"""The database rejects data that would break the engine's assumptions."""

from __future__ import annotations

import pytest
from dbkit import Db


def test_profile_program_must_belong_to_profile_school(db: Db, catalog: dict[str, int]) -> None:
    other_school = db.one(
        "insert into school (slug, name, college_name) "
        "values ('uc-berkeley', 'UC Berkeley', 'College of Engineering') returning id"
    )
    user = db.new_user()
    error = db.savepoint_error(
        "insert into student_profile (user_id, school_id, program_id, start_term) "
        "values (%s, %s, %s, '2025FA')",
        [user, other_school, catalog["program_live"]],
    )
    assert "foreign key" in str(error)


def test_completed_course_needs_exactly_one_of_course_or_free_text(
    db: Db, catalog: dict[str, int]
) -> None:
    user = db.new_user()
    for course_id, free_text in [(None, None), (catalog["course"], "ME 112")]:
        error = db.savepoint_error(
            "insert into completed_course (user_id, course_id, free_text, grade_band, source) "
            "values (%s, %s, %s, 'c_or_better', 'manual')",
            [user, course_id, free_text],
        )
        assert "check constraint" in str(error)
    db.conn.execute(
        "insert into completed_course (user_id, free_text, grade_band, source) "
        "values (%s, 'ENGR 1 (transfer)', 'pass_no_pass', 'manual')",
        [user],
    )


def test_unknown_grade_band_is_rejected(db: Db, catalog: dict[str, int]) -> None:
    user = db.new_user()
    error = db.savepoint_error(
        "insert into completed_course (user_id, course_id, grade_band, source) "
        "values (%s, %s, 'A', 'manual')",
        [user, catalog["course"]],
    )
    assert "invalid input value for enum grade_band" in str(error)


def test_requirement_cannot_demand_in_progress_grade(db: Db, catalog: dict[str, int]) -> None:
    error = db.savepoint_error(
        "insert into requirement_group (program_id, level, name, rule, min_grade_band) "
        "values (%s, 'major', 'x', 'all_of', 'in_progress')",
        [catalog["program_live"]],
    )
    assert "check constraint" in str(error)


def test_time_block_must_end_after_it_starts(db: Db) -> None:
    user = db.new_user()
    error = db.savepoint_error(
        "insert into time_block (user_id, day, start_time, end_time, kind) "
        "values (%s, 'mon', '17:00', '09:00', 'work')",
        [user],
    )
    assert "check constraint" in str(error)


def test_credit_points_to_exactly_one_requirement_or_milestone(
    db: Db, catalog: dict[str, int]
) -> None:
    user = db.new_user()
    error = db.savepoint_error("insert into student_credit (user_id) values (%s)", [user])
    assert "check constraint" in str(error)


@pytest.mark.parametrize(
    ("option_type", "course", "subject", "low", "high", "ok"),
    [
        ("course", True, None, None, None, True),
        ("course", False, None, None, None, False),
        ("course_pattern", False, "ME", 100, 199, True),
        ("course_pattern", False, "ME", 199, 100, False),
        ("course_pattern", True, "ME", 100, 199, False),
        ("milestone", False, None, None, None, False),
    ],
)
def test_requirement_option_shapes(
    db: Db,
    catalog: dict[str, int],
    option_type: str,
    course: bool,
    subject: str | None,
    low: int | None,
    high: int | None,
    ok: bool,
) -> None:
    query = (
        "insert into requirement_option "
        "(group_id, option_type, course_id, subject, number_min, number_max) "
        "values (%s, %s, %s, %s, %s, %s)"
    )
    params = [
        catalog["group_live"],
        option_type,
        catalog["course"] if course else None,
        subject,
        low,
        high,
    ]
    if ok:
        db.conn.execute(query, params)
    else:
        db.savepoint_error(query, params)


def test_choose_rules_need_a_count_and_all_of_must_not_have_one(
    db: Db, catalog: dict[str, int]
) -> None:
    for rule, count in [("choose_units", None), ("all_of", 3)]:
        error = db.savepoint_error(
            "insert into requirement_group (program_id, level, name, rule, rule_count) "
            "values (%s, 'major', 'x', %s, %s)",
            [catalog["program_live"], rule, count],
        )
        assert "check constraint" in str(error)


@pytest.mark.parametrize("number", ["112", "1A", "C8", "W22", "R1B", "190L"])
def test_course_numbers_from_both_schools_are_accepted(
    db: Db, catalog: dict[str, int], number: str
) -> None:
    db.conn.execute(
        "insert into course (school_id, subject, number) values (%s, 'MEC ENG', %s)",
        [catalog["school"], number],
    )


def test_term_plan_needs_a_term_and_long_term_plan_must_not_have_one(
    db: Db, catalog: dict[str, int]
) -> None:
    user = db.new_user()
    for kind, term in [("term", None), ("long_term", catalog["term"])]:
        error = db.savepoint_error(
            "insert into plan (user_id, kind, term_id, engine_version, check_passed) "
            "values (%s, %s, %s, '0.1.0', true)",
            [user, kind, term],
        )
        assert "check constraint" in str(error)
