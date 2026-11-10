-- ============================================================================
-- FAST/Holavon — FAZ 0: Ölçek ve Güvenlik Geçişi
--
-- Supabase SQL Editor'da TEK SEFERDE çalıştırın. Idempotenttir
-- (create ... if not exists + drop policy if exists) — güvenle tekrar çalıştırılabilir.
--
-- Bu dosya şunları yapar:
--   1) Hikâyeler için PRIVATE 'stories' bucket'ı + RLS (süresi dolmamış hikâye
--      dosyaları sadece oturum açmış kullanıcılar imzalı URL ile okuyabilir).
--   2) stories.media_path kolonu (storage yolu) — imzalı URL üretmek için.
--   3) Engelleme artık mesajlaşmayı da keser (messages politikaları).
--   4) blocks tablosu: engellenen de "beni engellemiş" bilgisini görebilir
--      (aksi halde RLS mesaj göndermeyi engelleyemez).
--   5) pg_cron ile süresi dolan hikâye satırlarının otomatik temizliği.
--   6) Arama için trigram index (büyük tabloda ilike taraması pahalı).
--
-- NOT: Storage DOSYALARININ silinmesi için ayrıca Edge Function gerekir:
--   supabase/functions/cleanup-stories/index.ts  (Dashboard > Edge Functions)
--   Dosyalar silinmeden satırlar silinir; erişim yine de kesilir çünkü
--   imzalı URL'ler 2 saatte bir yenilenir ve bucket private'tır.
-- ============================================================================

create extension if not exists "pgcrypto";

-- ── 1) stories.media_path kolonu ─────────────────────────────────────────────
alter table public.stories add column if not exists media_path text;
create index if not exists idx_stories_media_path on public.stories (media_path);

-- Eski hikâyeler (public bucket'ta, media_path boş) artık erişilemeyecek:
-- satırları temizle, dosyalar cleanup-stories Edge Function'ına bırakılır.
delete from public.stories where media_path is null;

-- ── 2) PRIVATE 'stories' bucket ─────────────────────────────────────────────
insert into storage.buckets (id, name, public)
values ('stories', 'stories', false)
on conflict (id) do nothing;

-- Hikâye sahibi yükleyebilir (kendi klasörüne).
drop policy if exists stories_write on storage.objects;
create policy stories_write on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'stories'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

-- Hikâye sahibi silebilir.
drop policy if exists stories_delete on storage.objects;
create policy stories_delete on storage.objects
  for delete to authenticated
  using (
    bucket_id = 'stories'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

-- Okuma: YALNIZCA süresi dolmamış bir hikâyeye ait dosya. Böylece imzalı URL
-- 24 saatlik hikâye ömrü boyunca çalışır, sonra erişim kesilir.
drop policy if exists stories_read on storage.objects;
create policy stories_read on storage.objects
  for select to authenticated
  using (
    bucket_id = 'stories'
    and exists (
      select 1 from public.stories s
      where s.media_path = name
        and s.expires_at > now()
    )
  );

-- ── 3) Engelleme → mesajlaşma da kesilir ────────────────────────────────────
-- blocks: engelleyen kendi kaydını görür; ENGELLENEN de "beni engellemiş"
-- bilgisini görebilir (aksi halde RLS, karşı tarafın bizi engellediğini
-- tespit edemez ve mesaj engellenemez).
alter table public.blocks drop constraint if exists blocks_not_self;
alter table public.blocks add constraint blocks_not_self check (blocker_id <> blocked_id);

drop policy if exists bl_all on public.blocks;
drop policy if exists bl_select on public.blocks;
create policy bl_select on public.blocks
  for select to authenticated
  using (auth.uid() = blocker_id or auth.uid() = blocked_id);

drop policy if exists bl_insert on public.blocks;
create policy bl_insert on public.blocks
  for insert to authenticated
  with check (auth.uid() = blocker_id);

drop policy if exists bl_delete on public.blocks;
create policy bl_delete on public.blocks
  for delete to authenticated
  using (auth.uid() = blocker_id);

-- messages: engellenen iki taraf arasında mesaj gönderilemez / okunamaz.
-- "other party" = satırın karşı tarafı (auth.uid() hangisi ise diğeri).
-- Kural: auth.uid() ile karşı taraf arasında HER YÖNDE engel varsa engellenir.
drop policy if exists msg_select on public.messages;
create policy msg_select on public.messages
  for select to authenticated
  using (
    (auth.uid() = sender_id or auth.uid() = recipient_id)
    and not exists (
      select 1 from public.blocks b
      where (b.blocker_id = auth.uid() and b.blocked_id in (sender_id, recipient_id))
         or (b.blocked_id = auth.uid() and b.blocker_id in (sender_id, recipient_id))
    )
  );

drop policy if exists msg_insert on public.messages;
create policy msg_insert on public.messages
  for insert to authenticated
  with check (
    auth.uid() = sender_id
    and recipient_id <> auth.uid()
    and not exists (
      select 1 from public.blocks b
      where (b.blocker_id = auth.uid() and b.blocked_id = recipient_id)
         or (b.blocker_id = recipient_id and b.blocked_id = auth.uid())
    )
  );

drop policy if exists msg_update on public.messages;
create policy msg_update on public.messages
  for update to authenticated
  using (
    auth.uid() = recipient_id
    and not exists (
      select 1 from public.blocks b
      where (b.blocker_id = auth.uid() and b.blocked_id = sender_id)
         or (b.blocker_id = sender_id and b.blocked_id = auth.uid())
    )
  )
  with check (auth.uid() = recipient_id);

drop policy if exists msg_delete on public.messages;
create policy msg_delete on public.messages
  for delete to authenticated
  using (
    auth.uid() = sender_id
    and not exists (
      select 1 from public.blocks b
      where (b.blocker_id = auth.uid() and b.blocked_id = recipient_id)
         or (b.blocker_id = recipient_id and b.blocked_id = auth.uid())
    )
  );

-- ── 4) pg_cron: süresi dolan hikâye satırlarını saatlik temizle ─────────────
-- Storage DOSYALARI Edge Function ile silinir; burada satırlar temizlenir
-- (story_mentions / story_views CASCADE ile silinir).
do $$
begin
  create extension if not exists pg_cron;
exception
  when others then null;  -- pg_cron kapalıysa sessizce geç
end $$;

do $$
begin
  perform cron.unschedule(jobid)
    from cron.job where jobname = 'cleanup-stories-hourly';
exception
  when others then null;
end $$;

do $$
begin
  perform cron.schedule(
    'cleanup-stories-hourly',
    '11 * * * *',
    'delete from public.stories where expires_at < now();'
  );
exception
  when others then null;  -- yetki yoksa kullanıcı Edge Function'ı elle kurar
end $$;

-- ── 5) Arama için trigram index (büyük tabloda ilike taraması pahalı) ───────
do $$
begin
  -- Supabase security lint: extensions belong in their own schema, not public.
  create schema if not exists extensions;
  create extension if not exists pg_trgm with schema extensions;
exception
  when others then null;
end $$;

do $$
begin
  create index if not exists idx_social_profiles_username_trgm
    on public.social_profiles using gin (lower(username) extensions.gin_trgm_ops);
exception
  when others then null;
end $$;

-- ── 6) Sıralama index'leri (feed keyset sayfalama için hazırlık) ───────────
create index if not exists idx_posts_created_id on public.posts (created_at desc, id desc);
create index if not exists idx_stories_expires_created on public.stories (expires_at, created_at desc);
