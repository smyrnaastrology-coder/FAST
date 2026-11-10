-- ============================================================================
-- Holavon Pro rozeti — sosyal profildeki altın tik
-- Supabase SQL Editor'de bir kez çalıştırın (idempotent, tekrar çalıştırmak zararsız).
--
-- Nasıl çalışır:
--   • Uygulama, RevenueCat'te aktif abonelik varsa kendi satırına is_pro=true
--     yazar (social_profiles RLS: sahibi güncelleyebilir).
--   • pro_since, bayrak false→true olduğunda otomatik damgalanır; bayrak
--     kapanınca temizlenir. İstemcinin tarih göndermesi gerekmez.
--
-- Güvenlik notu: is_pro yalnızca görsel bir göstergedir; satır sahibi kendi
-- bayrağını değiştirebilir. Sunucu tarafı doğrulama (RevenueCat webhook'u,
-- service_role ile yazma) eklendiğinde istemci yazımı kaldırılıp bu kolon
-- yalnızca service_role tarafından güncellenmeli.
-- ============================================================================

alter table public.social_profiles
  add column if not exists is_pro boolean not null default false;

alter table public.social_profiles
  add column if not exists pro_since timestamptz;

create index if not exists idx_social_profiles_pro
  on public.social_profiles (is_pro) where is_pro;

create or replace function public.tg_social_profiles_pro_stamp()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
begin
  if tg_op = 'INSERT' then
    if coalesce(new.is_pro, false) then
      new.pro_since := coalesce(new.pro_since, now());
    else
      new.pro_since := null;
    end if;
    return new;
  end if;

  if coalesce(new.is_pro, false) then
    -- Yalnızca ilk Pro geçişinde damgala; sonraki güncellemeler tarihi korur.
    if old.is_pro is distinct from true then
      new.pro_since := now();
    else
      new.pro_since := coalesce(old.pro_since, now());
    end if;
  else
    new.pro_since := null;
  end if;
  return new;
end;
$$;

drop trigger if exists social_profiles_pro_stamp on public.social_profiles;
create trigger social_profiles_pro_stamp
  before insert or update of is_pro on public.social_profiles
  for each row execute function public.tg_social_profiles_pro_stamp();

comment on column public.social_profiles.is_pro is
  'Holavon Pro abonelik rozeti (profillerde altın tik). Uygulama RevenueCat durumundan senkronlar.';

-- PostgREST şema önbelleğini hemen tazele.
notify pgrst, 'reload schema';
