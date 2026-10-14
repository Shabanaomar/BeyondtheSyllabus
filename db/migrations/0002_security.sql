-- Beyond the Syllabus: row-level security and table privileges.
--
-- Rules (from db/DATA_MODEL.md):
--   * Every table has row-level security switched on. A test fails if one doesn't.
--   * Catalog data: signed-in users read only 'live' rows; admins read everything and edit it.
--     Collectors write with the service role, which bypasses RLS and never reaches the browser.
--   * Student data: a student can read and change only their own rows.
--   * ai_usage: students can read their own counter but never change it (only the server can).
--   * answer_feedback: students can add a rating; only admins can read ratings.
--   * Anonymous (signed-out) visitors can read nothing.

-- ---------------------------------------------------------------------------------------------
-- Admin check
-- ---------------------------------------------------------------------------------------------

-- security definer so the check works even though app_admin itself is protected by RLS.
create function public.is_admin() returns boolean
language sql stable security definer
set search_path = ''
as $$
  select exists (select 1 from public.app_admin where user_id = auth.uid())
$$;

revoke all on function public.is_admin() from public;
grant execute on function public.is_admin() to authenticated, service_role;

-- ---------------------------------------------------------------------------------------------
-- Privileges. RLS decides which rows; these grants decide which actions are possible at all.
-- ---------------------------------------------------------------------------------------------

revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;

grant select on all tables in schema public to authenticated;
grant all on all tables in schema public to service_role;
grant usage on all sequences in schema public to authenticated, service_role;

-- Catalog editing by admins (RLS limits these to admins).
grant insert, update, delete on
  school, source_page, program, course, course_version, course_equivalent, milestone,
  milestone_course, requirement_group, requirement_option, term, section, section_meeting,
  organization, career_event, flagged_rule
to authenticated;

-- Students' own data.
grant insert, update, delete on
  student_profile, completed_course, student_credit, time_block, plan, plan_item
to authenticated;

-- Feedback: insert only (reading is limited to admins by RLS).
grant insert on answer_feedback to authenticated;

-- ai_usage and app_admin: select only for signed-in users (already granted above).

-- ---------------------------------------------------------------------------------------------
-- Switch on RLS everywhere
-- ---------------------------------------------------------------------------------------------

do $$
declare
  t record;
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format('alter table public.%I enable row level security', t.tablename);
  end loop;
end
$$;

-- ---------------------------------------------------------------------------------------------
-- Catalog policies
-- ---------------------------------------------------------------------------------------------

-- Tables with a review gate: students see live rows, admins see all.
do $$
declare
  t text;
begin
  foreach t in array array[
    'program', 'course_version', 'course_equivalent', 'milestone', 'requirement_group',
    'organization', 'career_event'
  ] loop
    execute format(
      'create policy read_live on public.%I for select to authenticated
         using (review_status = ''live'' or public.is_admin())', t);
  end loop;
end
$$;

-- Tables without their own review gate: facts (schools, terms, sections) and identities.
do $$
declare
  t text;
begin
  foreach t in array array[
    'school', 'source_page', 'course', 'term', 'section', 'section_meeting', 'milestone_course'
  ] loop
    execute format(
      'create policy read_all on public.%I for select to authenticated using (true)', t);
  end loop;
end
$$;

-- Options follow their group: visible only when the group is visible (RLS on the group applies
-- inside the subquery).
create policy read_with_group on requirement_option for select to authenticated
  using (exists (select 1 from requirement_group g where g.id = group_id));

-- Admin editing of every catalog table, and the review queue.
do $$
declare
  t text;
begin
  foreach t in array array[
    'school', 'source_page', 'program', 'course', 'course_version', 'course_equivalent',
    'milestone', 'milestone_course', 'requirement_group', 'requirement_option', 'term',
    'section', 'section_meeting', 'organization', 'career_event', 'flagged_rule'
  ] loop
    execute format(
      'create policy admin_insert on public.%I for insert to authenticated
         with check (public.is_admin())', t);
    execute format(
      'create policy admin_update on public.%I for update to authenticated
         using (public.is_admin()) with check (public.is_admin())', t);
    execute format(
      'create policy admin_delete on public.%I for delete to authenticated
         using (public.is_admin())', t);
  end loop;
end
$$;

create policy admin_read on flagged_rule for select to authenticated
  using (public.is_admin());

-- A signed-in user can see whether they themselves are an admin; nothing else.
create policy read_own on app_admin for select to authenticated
  using (user_id = auth.uid());

-- ---------------------------------------------------------------------------------------------
-- Student policies: own rows only
-- ---------------------------------------------------------------------------------------------

do $$
declare
  t text;
begin
  foreach t in array array[
    'student_profile', 'completed_course', 'student_credit', 'time_block', 'plan'
  ] loop
    execute format(
      'create policy own_rows on public.%I for all to authenticated
         using (user_id = auth.uid()) with check (user_id = auth.uid())', t);
  end loop;
end
$$;

create policy own_rows on plan_item for all to authenticated
  using (exists (select 1 from plan p where p.id = plan_id and p.user_id = auth.uid()))
  with check (exists (select 1 from plan p where p.id = plan_id and p.user_id = auth.uid()));

create policy read_own on ai_usage for select to authenticated
  using (user_id = auth.uid());

create policy add_rating on answer_feedback for insert to authenticated
  with check (true);
create policy admin_read on answer_feedback for select to authenticated
  using (public.is_admin());

-- Tables added by later migrations must not be readable by signed-out visitors by default.
alter default privileges in schema public revoke all on tables from anon;
alter default privileges in schema public revoke all on sequences from anon;
