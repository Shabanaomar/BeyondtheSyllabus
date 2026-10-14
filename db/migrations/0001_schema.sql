-- Beyond the Syllabus: tables, types and constraints.
-- Implements db/DATA_MODEL.md. Row-level security lives in 0002_security.sql.
--
-- Two kinds of data, kept strictly apart:
--   * Catalog data: public facts collected from university pages. Every rule-bearing row has a
--     review_status, and only 'live' rows are ever shown to students or used by the engine.
--   * Student data: private. Every row belongs to one auth user and is deleted with them.

-- ---------------------------------------------------------------------------------------------
-- Types
-- ---------------------------------------------------------------------------------------------

create type review_status as enum ('pending_review', 'live', 'rejected');
create type requirement_level as enum ('university', 'college', 'major');
create type requirement_rule as enum ('all_of', 'choose_courses', 'choose_units');
create type option_type as enum ('course', 'course_pattern', 'milestone');
create type equivalent_kind as enum ('renumbered', 'cross_listed');
create type grade_band as enum ('c_or_better', 'passed_below_c', 'pass_no_pass', 'in_progress');
create type course_record_source as enum ('manual', 'report', 'credit');
create type weekday as enum ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun');
create type time_block_kind as enum ('work', 'commute', 'other');
create type plan_kind as enum ('long_term', 'term');
create type organization_kind as enum ('professional', 'social', 'both');
create type career_event_kind as enum ('fair', 'info_session', 'workshop');
create type flag_status as enum ('open', 'approved', 'corrected');
create type section_component as enum ('lecture', 'lab', 'discussion', 'other');
create type section_mode as enum ('in_person', 'online', 'hybrid');
create type section_status as enum ('open', 'closed', 'waitlist', 'unknown');
create type offering_pattern as enum ('fall', 'spring', 'both', 'summer', 'irregular', 'unknown');
create type course_grading as enum ('letter', 'credit_no_credit', 'either');
create type feedback_rating as enum ('up', 'down');

-- Keeps updated_at current on every update.
create function set_updated_at() returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

-- ---------------------------------------------------------------------------------------------
-- Catalog data
-- ---------------------------------------------------------------------------------------------

create table school (
  id bigint generated always as identity primary key,
  slug text not null unique check (slug ~ '^[a-z0-9-]+$'),
  name text not null,
  college_name text not null,
  term_system text not null default 'semester' check (term_system in ('semester', 'quarter'))
);

-- Every page a collector fetched. One row per distinct version of a page.
create table source_page (
  id bigint generated always as identity primary key,
  url text not null check (url ~ '^https?://'),
  fetched_at timestamptz not null,
  last_checked_at timestamptz not null,
  content_hash text not null,
  raw_path text,
  robots_ok boolean not null,
  unique (url, content_hash)
);

-- One major in one catalog year.
create table program (
  id bigint generated always as identity primary key,
  school_id bigint not null references school (id),
  major_code text not null,
  name text not null,
  catalog_year text not null check (catalog_year ~ '^[0-9]{4}-[0-9]{2}$'),
  total_units numeric(5, 1) check (total_units > 0),
  source_page_id bigint references source_page (id),
  review_status review_status not null default 'pending_review',
  unique (school_id, major_code, catalog_year),
  -- Lets student_profile check that its program belongs to its school.
  unique (id, school_id)
);

-- The stable identity of a course ("ME 112 at Fresno State"). Never deleted, only deactivated.
create table course (
  id bigint generated always as identity primary key,
  school_id bigint not null references school (id),
  subject text not null check (subject ~ '^[A-Z][A-Z &]*$'),
  number text not null check (number ~ '^[A-Z]{0,2}[0-9]+[A-Z]{0,3}$'),
  active boolean not null default true,
  unique (school_id, subject, number)
);

-- What one catalog year says about a course.
create table course_version (
  id bigint generated always as identity primary key,
  course_id bigint not null references course (id),
  catalog_year text not null check (catalog_year ~ '^[0-9]{4}-[0-9]{2}$'),
  title text not null,
  units_min numeric(4, 1) not null check (units_min >= 0),
  units_max numeric(4, 1) not null,
  prereq_rule jsonb,
  coreq_rule jsonb,
  prereq_text text,
  typically_offered offering_pattern not null default 'unknown',
  grading course_grading not null default 'letter',
  source_page_id bigint references source_page (id),
  review_status review_status not null default 'pending_review',
  unique (course_id, catalog_year),
  check (units_max >= units_min)
);

-- Renumbered and cross-listed courses. The engine treats linked courses as one.
create table course_equivalent (
  id bigint generated always as identity primary key,
  course_id bigint not null references course (id),
  equivalent_course_id bigint not null references course (id),
  kind equivalent_kind not null,
  effective_catalog_year text check (effective_catalog_year ~ '^[0-9]{4}-[0-9]{2}$'),
  source_page_id bigint references source_page (id),
  review_status review_status not null default 'pending_review',
  check (course_id <> equivalent_course_id),
  unique (course_id, equivalent_course_id, kind)
);

-- Non-course requirements: writing requirements, American History & Institutions, etc.
create table milestone (
  id bigint generated always as identity primary key,
  school_id bigint not null references school (id),
  code text not null check (code ~ '^[A-Z0-9-]+$'),
  name text not null,
  how_to_satisfy text not null,
  can_be_met_by_exam boolean not null default false,
  source_page_id bigint references source_page (id),
  review_status review_status not null default 'pending_review',
  unique (school_id, code)
);

-- Courses that satisfy a milestone (a join table, so every link is a real foreign key).
create table milestone_course (
  milestone_id bigint not null references milestone (id) on delete cascade,
  course_id bigint not null references course (id),
  primary key (milestone_id, course_id)
);

-- A block of requirements. Groups nest via parent_group_id.
create table requirement_group (
  id bigint generated always as identity primary key,
  program_id bigint not null references program (id) on delete cascade,
  parent_group_id bigint references requirement_group (id) on delete cascade,
  level requirement_level not null,
  name text not null,
  rule requirement_rule not null,
  -- How many courses (choose_courses) or units (choose_units) are needed.
  rule_count numeric(5, 1) check (rule_count > 0),
  min_grade_band grade_band,
  -- {"default": "exclusive"|"shared", "may_share_with": [group ids], "max_shared_units": n}
  overlap_rule jsonb not null default '{"default": "exclusive"}'::jsonb,
  -- Rules the engine can't verify, e.g. [{"kind": "gpa", "value": 2.0, "scope": "major"}].
  -- Always shown as "check with your advisor", never as met.
  advisory_checks jsonb not null default '[]'::jsonb,
  notes text,
  sort_order integer not null default 0,
  source_page_id bigint references source_page (id),
  review_status review_status not null default 'pending_review',
  check (parent_group_id is null or parent_group_id <> id),
  check ((rule = 'all_of') = (rule_count is null)),
  check (min_grade_band is null or min_grade_band <> 'in_progress'),
  check (overlap_rule ? 'default' and overlap_rule ->> 'default' in ('exclusive', 'shared')),
  check (jsonb_typeof(advisory_checks) = 'array')
);

-- One way to satisfy a group: a course, a course pattern, or a milestone.
create table requirement_option (
  id bigint generated always as identity primary key,
  group_id bigint not null references requirement_group (id) on delete cascade,
  option_type option_type not null,
  course_id bigint references course (id),
  subject text check (subject ~ '^[A-Z][A-Z &]*$'),
  number_min integer check (number_min >= 0),
  number_max integer,
  exclusions jsonb not null default '[]'::jsonb,
  milestone_id bigint references milestone (id),
  check (jsonb_typeof(exclusions) = 'array'),
  check (
    (option_type = 'course'
      and course_id is not null and subject is null and number_min is null
      and number_max is null and milestone_id is null)
    or (option_type = 'course_pattern'
      and course_id is null and subject is not null and number_min is not null
      and number_max is not null and number_max >= number_min and milestone_id is null)
    or (option_type = 'milestone'
      and milestone_id is not null and course_id is null and subject is null
      and number_min is null and number_max is null)
  )
);

create table term (
  id bigint generated always as identity primary key,
  school_id bigint not null references school (id),
  code text not null check (code ~ '^[0-9]{4}(SP|SU|FA|WI)$'),
  name text not null,
  starts_on date not null,
  ends_on date not null,
  registration_opens_on date,
  add_deadline date,
  drop_deadline date,
  source_page_id bigint references source_page (id),
  unique (school_id, code),
  check (ends_on > starts_on)
);

create table section (
  id bigint generated always as identity primary key,
  term_id bigint not null references term (id) on delete cascade,
  course_id bigint not null references course (id),
  section_code text not null,
  class_number text,
  component section_component not null default 'lecture',
  -- A lecture that must be taken with one section from the same linked group (e.g. its labs).
  linked_section_group text,
  units numeric(4, 1) check (units >= 0),
  mode section_mode not null default 'in_person',
  status section_status not null default 'unknown',
  last_seen_at timestamptz not null default now(),
  source_page_id bigint references source_page (id),
  unique (term_id, course_id, section_code)
);

create table section_meeting (
  id bigint generated always as identity primary key,
  section_id bigint not null references section (id) on delete cascade,
  days weekday[] not null check (cardinality(days) > 0),
  start_time time not null,
  end_time time not null,
  location text,
  starts_on date,
  ends_on date,
  check (end_time > start_time)
);

create table organization (
  id bigint generated always as identity primary key,
  school_id bigint not null references school (id),
  name text not null,
  kind organization_kind not null,
  tags text[] not null default '{}',
  majors text[] not null default '{}',
  description text,
  meeting_info text,
  url text check (url ~ '^https?://'),
  source_page_id bigint references source_page (id),
  review_status review_status not null default 'pending_review',
  unique (school_id, name)
);

create table career_event (
  id bigint generated always as identity primary key,
  school_id bigint not null references school (id),
  term_id bigint references term (id),
  title text not null,
  kind career_event_kind not null,
  starts_at timestamptz not null,
  ends_at timestamptz,
  location text,
  majors text[] not null default '{}',
  goal_tags text[] not null default '{}',
  url text check (url ~ '^https?://'),
  source_page_id bigint references source_page (id),
  -- Events entered in the admin form go straight to live; collected ones wait for review.
  review_status review_status not null default 'pending_review',
  created_by uuid references auth.users (id) on delete set null,
  created_at timestamptz not null default now(),
  check (ends_at is null or ends_at > starts_at)
);

-- The data review queue.
create table flagged_rule (
  id bigint generated always as identity primary key,
  entity_type text not null,
  entity_id bigint,
  source_page_id bigint references source_page (id),
  source_excerpt text not null,
  proposed_value jsonb,
  reason text not null,
  status flag_status not null default 'open',
  resolved_by uuid references auth.users (id) on delete set null,
  resolved_at timestamptz,
  created_at timestamptz not null default now(),
  check ((status = 'open') = (resolved_at is null))
);

-- Who may edit catalog data and see the review queue. Rows are added by hand (service role).
create table app_admin (
  user_id uuid primary key references auth.users (id) on delete cascade
);

-- ---------------------------------------------------------------------------------------------
-- Student data (private). Every table cascades from auth.users, so deleting the account
-- deletes everything.
-- ---------------------------------------------------------------------------------------------

create table student_profile (
  user_id uuid primary key references auth.users (id) on delete cascade,
  school_id bigint not null references school (id),
  program_id bigint not null,
  start_term text not null check (start_term ~ '^[0-9]{4}(SP|SU|FA|WI)$'),
  units_per_term_min numeric(4, 1) not null default 12 check (units_per_term_min >= 0),
  units_per_term_max numeric(4, 1) not null default 16,
  graduation_target_term text check (graduation_target_term ~ '^[0-9]{4}(SP|SU|FA|WI)$'),
  career_goal text check (char_length(career_goal) <= 500),
  interests text[] not null default '{}',
  -- e.g. {"avoid_before": "09:00", "avoid_after": "18:00", "prefer_days": ["tue", "thu"]}
  preferred_times jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key (program_id, school_id) references program (id, school_id),
  check (units_per_term_max >= units_per_term_min),
  check (cardinality(interests) <= 20)
);

create trigger student_profile_updated_at
before update on student_profile
for each row execute function set_updated_at();

create table completed_course (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  course_id bigint references course (id),
  -- A course we don't have in our list yet; flagged for review by a background job.
  free_text text check (char_length(free_text) <= 120),
  grade_band grade_band not null,
  term_code text check (term_code ~ '^[0-9]{4}(SP|SU|FA|WI)$'),
  source course_record_source not null,
  created_at timestamptz not null default now(),
  check ((course_id is null) <> (free_text is null)),
  unique (user_id, course_id)
);

create table student_credit (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  requirement_group_id bigint references requirement_group (id) on delete cascade,
  milestone_id bigint references milestone (id) on delete cascade,
  note text check (char_length(note) <= 200),
  source course_record_source not null default 'credit' check (source = 'credit'),
  created_at timestamptz not null default now(),
  check ((requirement_group_id is null) <> (milestone_id is null))
);

create table time_block (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  -- Empty means "every term until I change it".
  term_id bigint references term (id) on delete cascade,
  day weekday not null,
  start_time time not null,
  end_time time not null,
  kind time_block_kind not null,
  check (end_time > start_time)
);

create table plan (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  kind plan_kind not null,
  term_id bigint references term (id),
  engine_version text not null,
  -- Which catalog data the plan was built from (catalog years, sync timestamps).
  catalog_snapshot jsonb not null default '{}'::jsonb,
  check_passed boolean not null,
  relies_on_credit boolean not null default false,
  created_at timestamptz not null default now(),
  check ((kind = 'term') = (term_id is not null))
);

create table plan_item (
  id bigint generated always as identity primary key,
  plan_id uuid not null references plan (id) on delete cascade,
  term_code text not null check (term_code ~ '^[0-9]{4}(SP|SU|FA|WI)$'),
  course_id bigint not null references course (id),
  section_id bigint references section (id) on delete set null,
  reason text check (char_length(reason) <= 300)
);

-- Daily counter used to cap AI spend per student. Written only by the server.
create table ai_usage (
  user_id uuid not null references auth.users (id) on delete cascade,
  day date not null,
  requests integer not null default 0 check (requests >= 0),
  tokens integer not null default 0 check (tokens >= 0),
  cost_cents integer not null default 0 check (cost_cents >= 0),
  primary key (user_id, day)
);

-- Thumbs up or down on an AI answer. Deliberately not linked to any user, so it can't be traced
-- to anyone and stays after account deletion (the privacy page says so).
create table answer_feedback (
  id bigint generated always as identity primary key,
  rating feedback_rating not null,
  school_id bigint references school (id),
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------------------------
-- Indexes for foreign keys and common lookups
-- ---------------------------------------------------------------------------------------------

create index on program (school_id);
create index on course_version (course_id);
create index on course_equivalent (equivalent_course_id);
create index on milestone_course (course_id);
create index on requirement_group (program_id);
create index on requirement_group (parent_group_id);
create index on requirement_option (group_id);
create index on requirement_option (course_id);
create index on requirement_option (milestone_id);
create index on term (school_id);
create index on section (term_id);
create index on section (course_id);
create index on section_meeting (section_id);
create index on organization (school_id);
create index on career_event (school_id, starts_at);
create index on flagged_rule (status);
create index on student_profile (program_id, school_id);
create index on completed_course (user_id);
create index on student_credit (user_id);
create index on time_block (user_id);
create index on plan (user_id);
create index on plan_item (plan_id);
