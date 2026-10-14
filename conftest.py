"""Shared test fixtures: a fresh Postgres database with every migration applied.

Set DATABASE_URL to a Postgres 15+ server you can create databases on, for example
postgresql://postgres@localhost:5432/postgres. Without it, database tests are skipped, unless
REQUIRE_DB_TESTS=1 (as in CI), in which case they fail. Each test runs inside a transaction that
is rolled back, so tests can't affect each other.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from dbkit import Db
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

DB_DIR = Path(__file__).resolve().parent / "db"
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
