"""Fixtures for database tests. The database itself comes from the root conftest.py."""

from __future__ import annotations

import pytest
from dbkit import Db


@pytest.fixture
def catalog(db: Db) -> dict[str, int]:
    """A small catalog: one school, one live and one pending program, courses, a term."""
    db.as_superuser()
    ids: dict[str, int] = {}
    ids["school"] = db.one(
        "insert into school (slug, name, college_name) "
        "values ('fresno-state', 'Fresno State', 'Lyles College of Engineering') returning id"
    )
    ids["program_live"] = db.one(
        "insert into program (school_id, major_code, name, catalog_year, review_status) "
        "values (%s, 'BS-ME', 'Mechanical Engineering', '2026-27', 'live') returning id",
        [ids["school"]],
    )
    ids["program_pending"] = db.one(
        "insert into program (school_id, major_code, name, catalog_year) "
        "values (%s, 'BS-CE', 'Civil Engineering', '2026-27') returning id",
        [ids["school"]],
    )
    ids["course"] = db.one(
        "insert into course (school_id, subject, number) values (%s, 'ME', '112') returning id",
        [ids["school"]],
    )
    ids["course2"] = db.one(
        "insert into course (school_id, subject, number) values (%s, 'MATH', '76') returning id",
        [ids["school"]],
    )
    ids["term"] = db.one(
        "insert into term (school_id, code, name, starts_on, ends_on) "
        "values (%s, '2027SP', 'Spring 2027', '2027-01-19', '2027-05-21') returning id",
        [ids["school"]],
    )
    ids["group_live"] = db.one(
        "insert into requirement_group (program_id, level, name, rule, review_status) "
        "values (%s, 'major', 'Major core', 'all_of', 'live') returning id",
        [ids["program_live"]],
    )
    ids["group_pending"] = db.one(
        "insert into requirement_group (program_id, level, name, rule, rule_count, review_status) "
        "values (%s, 'major', 'Electives', 'choose_units', 9, 'pending_review') returning id",
        [ids["program_live"]],
    )
    return ids
