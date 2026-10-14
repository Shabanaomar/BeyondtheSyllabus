"""Helpers for database tests: act as the superuser, a signed-in student, or signed-out."""

from __future__ import annotations

import json
import uuid
from typing import Any

import psycopg
import pytest


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
