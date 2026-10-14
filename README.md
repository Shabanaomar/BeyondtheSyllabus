# Beyond the Syllabus

An AI counselor for engineering students. A student enters their school, major, progress, work
schedule and career goal, and gets a next-term schedule, a path to graduation, club picks, career
events and a one-click calendar export. Project rules live in [CLAUDE.md](CLAUDE.md).

## What's where

| Folder    | What it is                                                       | Language            |
| --------- | ---------------------------------------------------------------- | ------------------- |
| `ingest/` | Collectors and parsers for catalogs, schedules, clubs and events | Python              |
| `engine/` | Requirement audit, prerequisites, plan checker, term scheduler   | Python, FastAPI     |
| `agent/`  | Claude tool-use counselor; system prompt in `agent/prompt.md`    | Python (planned)    |
| `web/`    | The website                                                      | Next.js, TypeScript |
| `db/`     | Postgres schema, migrations, row-level security                  | SQL (Supabase)      |
| `evals/`  | Test students and expected answers for the agent                 | Python (planned)    |

## Run it locally

You need [uv](https://docs.astral.sh/uv/) (Python 3.12+) and Node.js 22+.

```bash
# Python: install, then lint, type check and test
uv sync
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run pytest --cov=bts_engine --cov-fail-under=90

# Engine API at http://localhost:8000/health
uv run fastapi dev engine/src/bts_engine/api.py

# Website at http://localhost:3000
cd web
npm install
npm run dev
npm run check      # lint + format + type check
npm run test:e2e   # Playwright + axe at phone and desktop widths
```

Copy `.env.example` to `.env` (and `web/.env.local`) when you need real keys. Never commit them.

## Checks that run on every pull request

See [.github/workflows/ci.yml](.github/workflows/ci.yml).

| Check                                           | Status                         |
| ----------------------------------------------- | ------------------------------ |
| Python: ruff, strict mypy, pytest               | On                             |
| Engine test coverage ≥ 90%                      | On                             |
| TypeScript: strict, ESLint, Prettier, typecheck | On                             |
| Playwright e2e at 375px and 1280px, with axe    | On (home page for now)         |
| Dependency audit (pip-audit, npm audit)         | On                             |
| Secret scan (gitleaks)                          | On                             |
| Lighthouse on landing and dashboard (≥ 90)      | Added with the landing page    |
| Agent evals                                     | Added with the agent (Phase 2) |

## Environments

Development (your laptop), preview (a Vercel deployment per pull request), production. Each has
its own Supabase project and keys. Hosting is set up in Phase 4.
