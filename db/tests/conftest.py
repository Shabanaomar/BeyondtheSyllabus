"""Fixtures for database tests.

Each test session creates a fresh database, applies the Supabase stand-in and every migration in
order, and drops the database afterwards. Each test runs inside a transaction that is rolled
back, so tests can't affect each other.

Set DATABASE_URL to a Postgres 15+ server you can create databases on, for example
postgresql://postgres@localhost:5432/postgres. Without it the tests are skipped, unless
REQUIRE_DB_TESTS=1 (as in CI), in which case they fail.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

DB_DIR = Path(__file__).resolve().parents[1]
MIGRATIONS = sorted((DB_DIR / "migrations").glob("*.sql"))
STUB = DB_DIR / "tests" / "supabase_stub.sql"


def _server_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        if os.environ.get("REQUIRE_DB_TESTS") == "1":
            pytest.fail("DATABASE_URL is not set but REQUIRE_DB_TESTS=1")
        pytest.skip("DATABASE_URL not set; database tests skipped")
    return url


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    server = _server_url()
    name = f"bts_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(server, autocommit=True) as admin:
        admin.execute(sql.SQL("create database {}").format(sql.Identifier(name)))
    params = conninfo_to_dict(server)
    params["dbname"] = name
    url = make_conninfo(**params)
    try:
        with psycopg.connect(url, autocommit=True) as conn:
            for path in [STUB, *MIGRATIONS]:
                conn.execute(path.read_text())  # type: ignore[arg-type]
        yield url
    finally:
        with psycopg.connect(server, autocommit=True) as admin:
            admin.execute(
                sql.SQL("drop database if exists {} with (force)").format(sql.Identifier(name))
            )


@pytest.fixture
def db(database_url: str) -> Iterator[Db]:
    with psycopg.connect(database_url) as conn:
        yield Db(conn)
        conn.rollback()


class Db:
    """A connection with helpers to act as the superuser, a signed-in student, or signed-out."""

    def __init__(self, conn: psycopg.Connection[Any]) -> None:
        self.conn = conn

    def as_superuser(self) -> None:
        self.conn.execute("reset role")
        self.conn.execute("select set_config('request.jwt.claims', '', true)")

    def as_user(self, user_id: uuid.UUID) -> None:
        self.as_superuser()
        self.conn.execute("set local role authenticated")
        self.conn.execute(
            "select set_config('request.jwt.claims', %s, true)",
            [json.dumps({"sub": str(user_id)})],
        )

    def as_anon(self) -> None:
        self.as_superuser()
        self.conn.execute("set local role anon")

    def one(self, query: str, params: Any = None) -> Any:
        row = self.conn.execute(query, params).fetchone()
        assert row is not None
        return row[0]

    def all(self, query: str, params: Any = None) -> list[Any]:
        return [r[0] for r in self.conn.execute(query, params).fetchall()]

    def savepoint_error(self, query: str, params: Any = None) -> psycopg.Error:
        """Run a statement that must fail, and return the error without aborting the test."""
        with pytest.raises(psycopg.Error) as info, self.conn.transaction():
            self.conn.execute(query, params)
        return info.value

    def new_user(self) -> uuid.UUID:
        """Create an auth user as the superuser; leaves the role as superuser."""
        self.as_superuser()
        user_id = uuid.uuid4()
        self.conn.execute(
            "insert into auth.users (id, email) values (%s, %s)",
            [user_id, f"{user_id.hex[:8]}@example.edu"],
        )
        return user_id


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
