-- ============================================================================
--  user_charts: Haritalar modulu icin kullanici harita kayitlari (bulut)
--  Supabase SQL Editor'da bir kez calistirin. Idempotent: tekrar calistirilabilir.
--
--  - Her satir bir kullaniciya aittir; RLS ile yalnizca sahibi erisir.
--  - chart_data: /api/charts/natal yanitinin tamami (jsonb).
--  - Ayni kullanici ayni dogum bilgisi + isimle tekrar kaydederse upsert edilir.
-- ============================================================================

create table if not exists public.user_charts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null default '',
  chart_data jsonb not null,
  house_system text not null default 'P',
  birth_date text,
  birth_time text,
  lat double precision,
  lon double precision,
  tz double precision,
  place text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.user_charts is 'Haritalar modulu: kullanicinin kaydettigi natal/donus haritalari';
comment on column public.user_charts.chart_data is 'POST /api/charts/natal yanitinin tam JSON govdesi';
comment on column public.user_charts.name is 'Kullanici gorunen adi (bos olabilir)';

create index if not exists idx_user_charts_user
  on public.user_charts (user_id, updated_at desc);

create unique index if not exists uq_user_charts_identity
  on public.user_charts (user_id, name, birth_date, birth_time);

alter table public.user_charts enable row level security;

drop policy if exists uc_select on public.user_charts;
create policy uc_select on public.user_charts
  for select to authenticated using (auth.uid() = user_id);

drop policy if exists uc_insert on public.user_charts;
create policy uc_insert on public.user_charts
  for insert to authenticated with check (auth.uid() = user_id);

drop policy if exists uc_update on public.user_charts;
create policy uc_update on public.user_charts
  for update to authenticated using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists uc_delete on public.user_charts;
create policy uc_delete on public.user_charts
  for delete to authenticated using (auth.uid() = user_id);

create or replace function public.tg_user_charts_touch()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists trg_user_charts_touch on public.user_charts;
create trigger trg_user_charts_touch
before update on public.user_charts
for each row execute function public.tg_user_charts_touch();
