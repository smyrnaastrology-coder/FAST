-- ============================================================================
-- Holavon - Social push notifications (likes / comments)
-- Run this once in the Supabase SQL Editor.
--
-- Flow:
--   likes/comments INSERT
--     -> trigger public.notify_social_push()
--     -> pg_net HTTP POST to fbst-api /api/push/social
--     -> fbst-api reads device_tokens (service_role) and sends FCM HTTP v1
--
-- Before running, replace CHANGE_ME below with the same secret you set as
-- HOLAVON_PUSH_SECRET on Render (fbst-api).
-- ============================================================================

-- pg_net is preinstalled on Supabase; this is a no-op if already enabled.
create extension if not exists pg_net with schema extensions;

-- ----------------------------------------------------------------------------
-- 1) Device tokens (one row per FCM token, owned by the last signed-in user)
-- ----------------------------------------------------------------------------
create table if not exists public.device_tokens (
  token       text primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  platform    text not null default 'android',
  lang        text not null default 'tr',
  app_version text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index if not exists idx_device_tokens_user on public.device_tokens (user_id);

alter table public.device_tokens enable row level security;

-- The app never writes the table directly; it calls the RPCs below.
-- No policies are needed (service_role bypasses RLS).

-- Register/refresh the current device for the signed-in user. Also takes over
-- a token that was left behind by a previous account on the same device.
create or replace function public.register_device_token(
  p_token       text,
  p_platform    text default 'android',
  p_lang        text default 'tr',
  p_app_version text default null
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
  if p_token is null or length(trim(p_token)) = 0 then
    raise exception 'token_required';
  end if;

  -- Free the token from any other account so a shared device does not leak
  -- notifications from a previous session.
  delete from public.device_tokens
   where token = p_token
     and user_id <> auth.uid();

  insert into public.device_tokens (token, user_id, platform, lang, app_version, updated_at)
  values (
    p_token,
    auth.uid(),
    coalesce(nullif(trim(p_platform), ''), 'android'),
    case when p_lang in ('tr', 'en', 'es') then p_lang else 'tr' end,
    nullif(trim(p_app_version), ''),
    now()
  )
  on conflict (token) do update
    set user_id     = excluded.user_id,
        platform    = excluded.platform,
        lang        = excluded.lang,
        app_version = excluded.app_version,
        updated_at  = now();
end;
$$;

-- Functions are executable by PUBLIC by default; close that before granting
-- only the signed-in role. Anonymous callers must never reach this RPC.
revoke all on function public.register_device_token(text, text, text, text) from public;
revoke all on function public.register_device_token(text, text, text, text) from anon;
grant execute on function public.register_device_token(text, text, text, text) to authenticated;

-- Remove this device when the user signs out (only their own row).
create or replace function public.unregister_device_token(p_token text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.uid() is null then
    return;
  end if;
  delete from public.device_tokens
   where token = p_token
     and user_id = auth.uid();
end;
$$;

revoke all on function public.unregister_device_token(text) from public;
revoke all on function public.unregister_device_token(text) from anon;
grant execute on function public.unregister_device_token(text) to authenticated;

-- ----------------------------------------------------------------------------
-- 2) Webhook configuration (single row)
-- ----------------------------------------------------------------------------
create table if not exists public.push_config (
  id       int primary key default 1,
  endpoint text not null,
  secret   text not null,
  enabled  boolean not null default true
);

alter table public.push_config enable row level security;
-- No policies: only the SECURITY DEFINER trigger below can read it.

insert into public.push_config (id, endpoint, secret, enabled)
values (
  1,
  'https://fbst-api-mzum.onrender.com/api/push/social',
  'CHANGE_ME',
  true
)
on conflict (id) do nothing;

-- ----------------------------------------------------------------------------
-- 3) Trigger -> fbst-api
-- ----------------------------------------------------------------------------
create or replace function public.notify_social_push()
returns trigger
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
  v_owner      uuid;
  v_actor_name text;
  v_endpoint   text;
  v_secret     text;
  v_payload    jsonb;
begin
  if tg_table_name = 'likes' then
    select p.user_id into v_owner
      from public.posts p
     where p.id = new.post_id;

    if v_owner is null or v_owner = new.user_id then
      return new;
    end if;

    select coalesce(nullif(trim(sp.display_name), ''), sp.username)
      into v_actor_name
      from public.social_profiles sp
     where sp.user_id = new.user_id;

    v_payload := jsonb_build_object(
      'type',       'like',
      'post_id',    new.post_id,
      'actor_id',   new.user_id,
      'owner_id',   v_owner,
      'actor_name', coalesce(v_actor_name, '')
    );

  elsif tg_table_name = 'comments' then
    select p.user_id into v_owner
      from public.posts p
     where p.id = new.post_id;

    if v_owner is null or v_owner = new.user_id then
      return new;
    end if;

    select coalesce(nullif(trim(sp.display_name), ''), sp.username)
      into v_actor_name
      from public.social_profiles sp
     where sp.user_id = new.user_id;

    v_payload := jsonb_build_object(
      'type',         'comment',
      'post_id',      new.post_id,
      'actor_id',     new.user_id,
      'owner_id',     v_owner,
      'actor_name',   coalesce(v_actor_name, ''),
      'comment_id',   new.id,
      'comment_text', left(coalesce(new.text, ''), 160)
    );
  else
    return new;
  end if;

  select endpoint, secret into v_endpoint, v_secret
    from public.push_config
   where id = 1 and enabled = true;

  if v_endpoint is null or v_secret is null or v_secret = 'CHANGE_ME' then
    return new;
  end if;

  perform net.http_post(
    url     := v_endpoint,
    body    := v_payload,
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'X-Holavon-Push-Secret', v_secret
    ),
    timeout_milliseconds := 5000
  );

  return new;
exception
  when others then
    -- Never block a like/comment because the notification failed.
    raise warning '[push] notify_social_push failed: %', sqlerrm;
    return new;
end;
$$;

-- Trigger-only function: no client role needs direct RPC access.
revoke all on function public.notify_social_push() from public;
revoke all on function public.notify_social_push() from anon;
revoke all on function public.notify_social_push() from authenticated;

drop trigger if exists trg_push_like on public.likes;
create trigger trg_push_like
  after insert on public.likes
  for each row execute function public.notify_social_push();

drop trigger if exists trg_push_comment on public.comments;
create trigger trg_push_comment
  after insert on public.comments
  for each row execute function public.notify_social_push();

-- ----------------------------------------------------------------------------
-- 4) Optional cleanup: tokens untouched for 180 days
-- ----------------------------------------------------------------------------
create or replace function public.prune_device_tokens()
returns void
language sql
security definer
set search_path = public
as $$
  delete from public.device_tokens where updated_at < now() - interval '180 days';
$$;

-- Maintenance function: callable by the owner/cron only, never by the API.
revoke all on function public.prune_device_tokens() from public;
revoke all on function public.prune_device_tokens() from anon;
revoke all on function public.prune_device_tokens() from authenticated;

-- To change the secret later:
--   update public.push_config set secret = 'NEW_SECRET' where id = 1;
