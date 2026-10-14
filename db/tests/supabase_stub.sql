-- Test-only stand-in for the parts of Supabase our migrations rely on.
-- Real Supabase projects already have all of this; NEVER apply this file to Supabase.
--
-- It provides:
--   * the anon / authenticated / service_role roles
--   * an auth.users table
--   * auth.uid(), which returns the signed-in user's id from the request's JWT claims
--
-- Tests "sign in" as a user with:
--   set local role authenticated;
--   select set_config('request.jwt.claims', '{"sub": "<uuid>"}', true);

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin noinherit;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin noinherit;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then
    create role service_role nologin noinherit bypassrls;
  end if;
end
$$;

create schema if not exists auth;
grant usage on schema auth to anon, authenticated, service_role;

create table if not exists auth.users (
  id uuid primary key,
  email text unique,
  created_at timestamptz not null default now()
);

create or replace function auth.uid() returns uuid
language sql stable
as $$
  select nullif(
    coalesce(
      current_setting('request.jwt.claim.sub', true),
      (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
    ),
    ''
  )::uuid
$$;

grant execute on function auth.uid() to anon, authenticated, service_role;
grant usage on schema public to anon, authenticated, service_role;
