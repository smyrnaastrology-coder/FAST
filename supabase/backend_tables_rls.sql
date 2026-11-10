-- ============================================================================
-- Backend-only tables: enable RLS and remove public API access
--
-- These tables are written by the Render backend through a direct
-- DATABASE_URL connection (table owner), not through PostgREST. Enabling RLS
-- without policies keeps anon/authenticated out while the backend keeps
-- working, because the owner bypasses RLS unless FORCE RLS is set.
--
-- Run once in the Supabase SQL Editor. Safe to run again.
-- ============================================================================

begin;

alter table if exists public.auth_profiles        enable row level security;
alter table if exists public.auth_people           enable row level security;
alter table if exists public.billing_subs          enable row level security;
alter table if exists public.billing_free          enable row level security;
alter table if exists public.billing_pdf_single    enable row level security;
alter table if exists public.billing_pdf_credits   enable row level security;
alter table if exists public.billing_pdf_txns      enable row level security;
alter table if exists public.analysis_sessions     enable row level security;

-- Defense in depth: even a future accidental policy will not expose these
-- tables to the public PostgREST roles.
revoke all on table public.auth_profiles       from anon, authenticated;
revoke all on table public.auth_people         from anon, authenticated;
revoke all on table public.billing_subs        from anon, authenticated;
revoke all on table public.billing_free        from anon, authenticated;
revoke all on table public.billing_pdf_single  from anon, authenticated;
revoke all on table public.billing_pdf_credits from anon, authenticated;
revoke all on table public.billing_pdf_txns    from anon, authenticated;
revoke all on table public.analysis_sessions   from anon, authenticated;

commit;

-- Verification: all rows must return rls_enabled = true.
--
-- select c.relname as table_name, c.relrowsecurity as rls_enabled
-- from pg_class c
-- join pg_namespace n on n.oid = c.relnamespace
-- where n.nspname = 'public'
--   and c.relname in (
--     'auth_profiles', 'auth_people',
--     'billing_subs', 'billing_free',
--     'billing_pdf_single', 'billing_pdf_credits', 'billing_pdf_txns',
--     'analysis_sessions'
--   )
-- order by c.relname;
