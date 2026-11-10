-- ============================================================================
-- Supabase Security Advisor hardening (idempotent)
--
-- Fixes the remaining WARN lints:
--   1. function_search_path_mutable  -> tg_social_profiles_pro_stamp
--   2. extension_in_public           -> pg_trgm moved to extensions schema
--   3. anon/authenticated SECURITY DEFINER functions -> revoke direct RPC
--   4. leaked password protection    -> dashboard setting (see bottom)
--
-- Run once in the Supabase SQL Editor. Safe to run again.
-- ============================================================================

begin;

-- 1) Trigger function: pin search_path ---------------------------------------
alter function public.tg_social_profiles_pro_stamp()
  set search_path = public, pg_temp;

-- 2) pg_trgm belongs in the extensions schema --------------------------------
do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_trgm') then
    create schema if not exists extensions;
    alter extension pg_trgm set schema extensions;
  end if;
end $$;

-- 3) SECURITY DEFINER functions: remove PUBLIC/anon access -------------------
-- Trigger-only: no client role should call these through /rest/v1/rpc.
revoke all on function public.notify_social_push() from public;
revoke all on function public.notify_social_push() from anon;
revoke all on function public.notify_social_push() from authenticated;

revoke all on function public.prune_device_tokens() from public;
revoke all on function public.prune_device_tokens() from anon;
revoke all on function public.prune_device_tokens() from authenticated;

-- Device registration is intentionally callable by signed-in users only.
revoke all on function public.register_device_token(text, text, text, text) from public;
revoke all on function public.register_device_token(text, text, text, text) from anon;
grant execute on function public.register_device_token(text, text, text, text) to authenticated;

revoke all on function public.unregister_device_token(text) from public;
revoke all on function public.unregister_device_token(text) from anon;
grant execute on function public.unregister_device_token(text) to authenticated;

commit;

-- 4) Leaked password protection ----------------------------------------------
-- Dashboard -> Authentication -> Attack Protection (or Password Security):
-- enable "Leaked password protection" (HaveIBeenPwned check).
--
-- Verification:
--   select proname, proconfig
--   from pg_proc
--   where pronamespace = 'public'::regnamespace
--     and proname in ('tg_social_profiles_pro_stamp', 'notify_social_push',
--                     'prune_device_tokens', 'register_device_token',
--                     'unregister_device_token');
--
--   select extname, extnamespace::regnamespace
--   from pg_extension where extname = 'pg_trgm';
