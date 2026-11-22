-- ============================================================================
-- Holavon — Astroloğa Sor (tek soruluk danışmanlık)
--
-- Kullanım: Supabase Dashboard > SQL Editor > bu dosyayı çalıştır.
-- Idempotenttir: tekrar çalıştırmak güvenlidir.
--
-- Faz 1 (tek astrolog):
--   * public.astrologers içinde TEK satır bulunur (siz).
--   * public.astro_questions her soruyu tutar; astrolog_id şimdiden var,
--     böylece ikinci fazda yeni astrologlar eklenirken şema değişmez.
--   * Ödeme henüz bağlı değil: status='pending_payment' ile başlar,
--     ödeme doğrulanınca sunucu (service_role) 'open' yapar.
--   * Astrolog cevabı service_role ile yazılır; kullanıcı yalnızca kendi
--     sorusunu görür ve puan verebilir (RPC).
-- ============================================================================

-- ── Astrologlar ─────────────────────────────────────────────────────────────
create table if not exists public.astrologers (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid unique references auth.users(id) on delete set null,
  display_name  text not null,
  headline      text,
  bio           text,
  photo_url     text,
  tier          text not null default 'mentor'
                check (tier in ('student', 'approved', 'mentor')),
  status        text not null default 'active'
                check (status in ('active', 'paused', 'closed')),
  langs         text[] not null default '{tr}',
  topics        text[] not null default '{}',
  max_open      int not null default 5,
  rating        numeric(3, 2),
  answer_count  int not null default 0,
  sort_order    int not null default 0,
  created_at    timestamptz not null default now()
);

create index if not exists idx_astrologers_active
  on public.astrologers (status, sort_order);

alter table public.astrologers enable row level security;

-- Herkes yalnızca aktif astrologları listeleyebilir.
drop policy if exists astrologers_select on public.astrologers;
create policy astrologers_select on public.astrologers for select
  using (status = 'active');

-- Yazma yalnızca service_role (panel/sunucu) üzerinden yapılır.

-- ── Sorular ─────────────────────────────────────────────────────────────────
create table if not exists public.astro_questions (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  astrologer_id uuid references public.astrologers(id) on delete set null,
  topic         text not null default 'other',
  question      text not null check (char_length(question) between 20 and 2000),
  lang          text not null default 'tr',
  price_try     numeric(10, 2) not null,
  product_id    text,
  status        text not null default 'pending_payment'
                check (status in ('pending_payment', 'open', 'answered',
                                  'closed', 'refunded', 'expired')),
  payment_ref   text,
  deadline_at   timestamptz,
  answer_text   text,
  answered_at   timestamptz,
  rating        int check (rating between 1 and 5),
  rating_note   text,
  rated_at      timestamptz,
  created_at    timestamptz not null default now()
);

create index if not exists idx_astro_questions_user
  on public.astro_questions (user_id, created_at desc);
create index if not exists idx_astro_questions_status
  on public.astro_questions (status, deadline_at);
create index if not exists idx_astro_questions_astrologer
  on public.astro_questions (astrologer_id, status);

alter table public.astro_questions enable row level security;

-- Kullanıcı yalnızca kendi sorularını görür.
drop policy if exists astro_questions_select on public.astro_questions;
create policy astro_questions_select on public.astro_questions for select
  to authenticated
  using (auth.uid() = user_id);

-- Kullanıcı yalnızca kendi adına ve ÖDENMEMİŞ soru oluşturabilir.
-- Cevap/ücret alanları istemciden yazılamaz.
drop policy if exists astro_questions_insert on public.astro_questions;
create policy astro_questions_insert on public.astro_questions for insert
  to authenticated
  with check (
    auth.uid() = user_id
    and status = 'pending_payment'
    and answer_text is null
    and answered_at is null
  );

-- Güncelleme politikası YOK: cevap ve durum değişikliği sunucudan
-- (service_role) yapılır. Puanlama aşağıdaki RPC ile verilir.

-- ── Puanlama RPC ────────────────────────────────────────────────────────────
create or replace function public.rate_astro_question(
  p_id      uuid,
  p_rating  int,
  p_note    text default null
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.uid() is null then
    raise exception 'not_authenticated';
  end if;
  if p_rating is null or p_rating < 1 or p_rating > 5 then
    raise exception 'invalid_rating';
  end if;

  update public.astro_questions
     set rating      = p_rating,
         rating_note = nullif(trim(coalesce(p_note, '')), ''),
         rated_at    = now()
   where id = p_id
     and user_id = auth.uid()
     and status = 'answered'
     and rating is null;

  if not found then
    raise exception 'not_rateable';
  end if;
end;
$$;

grant execute on function public.rate_astro_question(uuid, int, text) to authenticated;

-- ── Tek astrolog kaydı (kendiniz) ───────────────────────────────────────────
-- Aşağıdaki bloğu BİR KEZ çalıştırın; e-posta adresinizi yazın.
-- Fotoğraf için Storage'da public bir bucket (ör. 'astrologers') açıp
-- photo_url alanına yazabilirsiniz; şimdilik boş bırakmak yeterli.
--
-- do $$
-- declare v_uid uuid;
-- begin
--   select id into v_uid from auth.users where email = 'BURAYA_EMAIL';
--   if v_uid is null then
--     raise notice 'Kullanici bulunamadi: BURAYA_EMAIL';
--     return;
--   end if;
--   insert into public.astrologers
--     (user_id, display_name, headline, tier, status, langs, topics,
--      max_open, sort_order)
--   values
--     (v_uid, 'Fatih Asartepe',
--      'Karma Astrolog · Horary ve Sinastri',
--      'mentor', 'active', '{tr,en,es}',
--      '{love,career,family,lost,health,other}', 5, 0)
--   on conflict (user_id) do update
--     set display_name = excluded.display_name,
--         headline     = excluded.headline,
--         tier         = excluded.tier,
--         status       = excluded.status;
-- end $$;
