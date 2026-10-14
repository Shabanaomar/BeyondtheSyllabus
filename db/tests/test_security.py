"""Proves the privacy and access rules in db/DATA_MODEL.md hold in the real database."""

from __future__ import annotations

import uuid

import pytest

from .conftest import Db

STUDENT_TABLES = [
    "student_profile",
    "completed_course",
    "student_credit",
    "time_block",
    "plan",
    "plan_item",
    "ai_usage",
]


def _fill_student(db: Db, catalog: dict[str, int], user: uuid.UUID) -> None:
    """Give a student one row in every student table, as the superuser."""
    db.as_superuser()
    db.conn.execute(
        "insert into student_profile (user_id, school_id, program_id, start_term) "
        "values (%s, %s, %s, '2025FA')",
        [user, catalog["school"], catalog["program_live"]],
    )
    db.conn.execute(
        "insert into completed_course (user_id, course_id, grade_band, source) "
        "values (%s, %s, 'c_or_better', 'manual')",
        [user, catalog["course"]],
    )
    db.conn.execute(
        "insert into student_credit (user_id, requirement_group_id, note) "
        "values (%s, %s, 'AP Calculus BC')",
        [user, catalog["group_live"]],
    )
    db.conn.execute(
        "insert into time_block (user_id, day, start_time, end_time, kind) "
        "values (%s, 'mon', '09:00', '13:00', 'work')",
        [user],
    )
    plan_id = db.one(
        "insert into plan (user_id, kind, engine_version, check_passed) "
        "values (%s, 'long_term', '0.1.0', true) returning id",
        [user],
    )
    db.conn.execute(
        "insert into plan_item (plan_id, term_code, course_id) values (%s, '2027SP', %s)",
        [plan_id, catalog["course2"]],
    )
    db.conn.execute(
        "insert into ai_usage (user_id, day, requests) values (%s, current_date, 3)", [user]
    )


def test_every_table_has_row_level_security(db: Db) -> None:
    db.as_superuser()
    missing = db.all(
        "select tablename from pg_tables where schemaname = 'public' and not rowsecurity"
    )
    assert missing == []


def test_every_table_has_at_least_one_policy(db: Db) -> None:
    db.as_superuser()
    without = db.all(
        "select t.tablename from pg_tables t where t.schemaname = 'public' and not exists "
        "(select 1 from pg_policies p where p.schemaname = 'public' and p.tablename = t.tablename)"
    )
    assert without == []


@pytest.mark.parametrize("table", STUDENT_TABLES)
def test_student_sees_only_their_own_rows(db: Db, catalog: dict[str, int], table: str) -> None:
    alice, bob = db.new_user(), db.new_user()
    _fill_student(db, catalog, alice)
    _fill_student(db, catalog, bob)

    db.as_user(alice)
    assert db.one(f"select count(*) from {table}") == 1  # noqa: S608 (fixed table names)
    if table != "plan_item":
        assert db.all(f"select distinct user_id from {table}") == [alice]  # noqa: S608


@pytest.mark.parametrize(
    "table", ["student_profile", "completed_course", "student_credit", "time_block", "plan"]
)
def test_student_cannot_change_or_delete_someone_elses_rows(
    db: Db, catalog: dict[str, int], table: str
) -> None:
    alice, bob = db.new_user(), db.new_user()
    _fill_student(db, catalog, bob)

    db.as_user(alice)
    # RLS hides Bob's rows, so updates and deletes silently touch nothing.
    assert db.conn.execute(f"delete from {table}").rowcount == 0  # noqa: S608
    db.as_superuser()
    assert db.one(f"select count(*) from {table} where user_id = %s", [bob]) == 1  # noqa: S608


def test_student_cannot_write_rows_for_someone_else(db: Db, catalog: dict[str, int]) -> None:
    alice, bob = db.new_user(), db.new_user()
    db.as_user(alice)
    error = db.savepoint_error(
        "insert into time_block (user_id, day, start_time, end_time, kind) "
        "values (%s, 'tue', '10:00', '12:00', 'work')",
        [bob],
    )
    assert "row-level security" in str(error)


def test_student_cannot_add_items_to_someone_elses_plan(db: Db, catalog: dict[str, int]) -> None:
    alice, bob = db.new_user(), db.new_user()
    _fill_student(db, catalog, bob)
    bobs_plan = db.one("select id from plan where user_id = %s", [bob])

    db.as_user(alice)
    error = db.savepoint_error(
        "insert into plan_item (plan_id, term_code, course_id) values (%s, '2027FA', %s)",
        [bobs_plan, catalog["course"]],
    )
    assert "row-level security" in str(error)


def test_student_cannot_change_their_ai_usage_counter(db: Db, catalog: dict[str, int]) -> None:
    alice = db.new_user()
    _fill_student(db, catalog, alice)

    db.as_user(alice)
    assert db.one("select requests from ai_usage") == 3
    error = db.savepoint_error("update ai_usage set requests = 0")
    assert "permission denied" in str(error)
    error = db.savepoint_error("delete from ai_usage")
    assert "permission denied" in str(error)


def test_deleting_an_account_removes_all_student_data(db: Db, catalog: dict[str, int]) -> None:
    alice, bob = db.new_user(), db.new_user()
    _fill_student(db, catalog, alice)
    _fill_student(db, catalog, bob)
    db.as_superuser()
    db.conn.execute("insert into answer_feedback (rating) values ('up')")

    db.conn.execute("delete from auth.users where id = %s", [alice])

    for table in STUDENT_TABLES:
        if table == "plan_item":
            remaining = db.one(
                "select count(*) from plan_item i join plan p on p.id = i.plan_id "
                "where p.user_id = %s",
                [alice],
            )
        else:
            remaining = db.one(
                f"select count(*) from {table} where user_id = %s",  # noqa: S608
                [alice],
            )
        assert remaining == 0, f"{table} still has rows for the deleted user"
    # Bob is untouched, and the unlinked feedback rating stays (the privacy page says so).
    assert db.one("select count(*) from student_profile where user_id = %s", [bob]) == 1
    assert db.one("select count(*) from answer_feedback") == 1


def test_every_student_table_cascades_from_auth_users(db: Db) -> None:
    """Any table with a user_id column must be deleted along with the user."""
    db.as_superuser()
    not_cascading = db.all(
        """
        select c.table_name
        from information_schema.columns c
        where c.table_schema = 'public' and c.column_name = 'user_id'
          and not exists (
            select 1
            from pg_constraint k
            join pg_class t on t.oid = k.conrelid
            join pg_namespace n on n.oid = t.relnamespace
            where n.nspname = 'public' and t.relname = c.table_name and k.contype = 'f'
              and k.confrelid = 'auth.users'::regclass and k.confdeltype = 'c'
          )
        """
    )
    assert not_cascading == []


def test_students_see_only_live_catalog_rows(db: Db, catalog: dict[str, int]) -> None:
    alice = db.new_user()
    db.as_user(alice)
    assert db.all("select major_code from program") == ["BS-ME"]
    assert db.all("select name from requirement_group") == ["Major core"]


def test_options_of_hidden_groups_are_hidden(db: Db, catalog: dict[str, int]) -> None:
    db.as_superuser()
    db.conn.execute(
        "insert into requirement_option (group_id, option_type, course_id) "
        "values (%s, 'course', %s), (%s, 'course', %s)",
        [catalog["group_live"], catalog["course"], catalog["group_pending"], catalog["course2"]],
    )
    db.as_user(db.new_user())
    assert db.all("select course_id from requirement_option") == [catalog["course"]]


def test_students_cannot_edit_the_catalog(db: Db, catalog: dict[str, int]) -> None:
    db.as_user(db.new_user())
    error = db.savepoint_error(
        "insert into course (school_id, subject, number) values (%s, 'ME', '1')",
        [catalog["school"]],
    )
    assert "row-level security" in str(error)
    assert db.conn.execute("update program set name = 'x'").rowcount == 0
    assert db.conn.execute("delete from course").rowcount == 0


def test_students_cannot_see_the_review_queue(db: Db, catalog: dict[str, int]) -> None:
    db.as_superuser()
    db.conn.execute(
        "insert into flagged_rule (entity_type, source_excerpt, reason) "
        "values ('course_version', 'ME 112 prerequisite: ...', 'ambiguous')"
    )
    db.as_user(db.new_user())
    assert db.one("select count(*) from flagged_rule") == 0


def test_admin_sees_pending_rows_and_can_edit(db: Db, catalog: dict[str, int]) -> None:
    admin = db.new_user()
    db.conn.execute("insert into app_admin (user_id) values (%s)", [admin])
    db.conn.execute(
        "insert into flagged_rule (entity_type, source_excerpt, reason) "
        "values ('program', 'BS-CE requirements ...', 'new page version')"
    )

    db.as_user(admin)
    assert sorted(db.all("select major_code from program")) == ["BS-CE", "BS-ME"]
    assert db.one("select count(*) from flagged_rule") == 1
    updated = db.conn.execute(
        "update program set review_status = 'live' where id = %s", [catalog["program_pending"]]
    ).rowcount
    assert updated == 1


def test_students_cannot_make_themselves_admin(db: Db) -> None:
    alice = db.new_user()
    db.as_user(alice)
    error = db.savepoint_error("insert into app_admin (user_id) values (%s)", [alice])
    assert "permission denied" in str(error)
    assert db.one("select public.is_admin()") is False


def test_feedback_is_write_only_for_students(db: Db, catalog: dict[str, int]) -> None:
    db.as_user(db.new_user())
    db.conn.execute("insert into answer_feedback (rating) values ('down')")
    assert db.one("select count(*) from answer_feedback") == 0


def test_signed_out_visitors_can_read_nothing(db: Db, catalog: dict[str, int]) -> None:
    db.as_anon()
    for table in ["school", "program", "course", "organization", "student_profile"]:
        error = db.savepoint_error(f"select * from {table}")  # noqa: S608
        assert "permission denied" in str(error)
