-- Academic calendar dates within a term (holidays, finals, first and last day of instruction),
-- collected from each school's official calendar and used for the student's calendar export.

create table term_date (
  id bigint generated always as identity primary key,
  term_id bigint not null references term (id) on delete cascade,
  label text not null,
  kind text not null check (
    kind in (
      'term_start', 'term_end', 'instruction_start', 'instruction_end', 'holiday', 'finals',
      'registration', 'deadline', 'other'
    )
  ),
  starts_on date not null,
  ends_on date not null,
  source_page_id bigint references source_page (id),
  check (ends_on >= starts_on),
  unique (term_id, label, starts_on)
);

create index on term_date (term_id);

-- A term's dates may be a tentative draft (Fresno State publishes next year's calendar early).
alter table term add column tentative boolean not null default false;

alter table term_date enable row level security;
revoke all on term_date from anon;
grant select on term_date to authenticated;
grant insert, update, delete on term_date to authenticated;
grant all on term_date to service_role;

create policy read_all on term_date for select to authenticated using (true);
create policy admin_insert on term_date for insert to authenticated with check (public.is_admin());
create policy admin_update on term_date for update to authenticated
  using (public.is_admin()) with check (public.is_admin());
create policy admin_delete on term_date for delete to authenticated using (public.is_admin());
