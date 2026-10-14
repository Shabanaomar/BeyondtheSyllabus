# db/

Supabase Postgres schema, migrations and row-level security. The data model is in
[DATA_MODEL.md](DATA_MODEL.md); the migrations implement it.

| File                                 | What it does                                                        |
| ------------------------------------ | ------------------------------------------------------------------- |
| `migrations/0001_schema.sql`         | Every table, type and constraint                                    |
| `migrations/0002_security.sql`       | Row-level security and privileges                                   |
| `tests/supabase_stub.sql`            | Test-only stand-in for Supabase's auth system. Never apply to Supabase |
| `tests/test_security.py`             | Proves the privacy rules: own rows only, deletion, admin, signed out |
| `tests/test_constraints.py`          | Proves the database rejects data that would confuse the engine      |

## Run the tests

You need a Postgres 15+ server you can create databases on. The tests create a fresh database,
apply the stub and every migration, run, and drop it.

```bash
DATABASE_URL=postgresql://postgres@localhost:5432/postgres uv run pytest db/tests
```

Without `DATABASE_URL` the database tests are skipped locally. CI always runs them against a
Postgres 16 service.

## Apply to Supabase

Run the files in `migrations/` in order, once each, in the Supabase SQL editor (or with `psql`
against the project's connection string). Don't run anything from `tests/`.

## Adding a migration

- New file, next number: `0003_short_name.sql`. Never edit a migration that's been applied.
- Every new table needs row-level security and at least one policy; the tests fail otherwise.
- Every table with a `user_id` must reference `auth.users` with `on delete cascade`; the tests
  fail otherwise.
