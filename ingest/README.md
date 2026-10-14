# ingest/

Collectors for the university pages that allow it. What each source allows, and why some aren't
collected, is in [docs/sources/](../docs/sources/).

| File | What it does |
| --- | --- |
| `fetch.py` | Polite fetching: reads robots.txt first, honours crawl delays, identifies the project, stops at bot challenges, saves raw copies |
| `parsers/fresno.py` | Fresno State engineering clubs, Industry Expo, academic calendar (this year and next) |
| `parsers/berkeley.py` | Berkeley Engineering student groups |
| `tagging.py` | Club tags from words in each club's own name (used to match clubs to majors and goals) |
| `store.py` | Writes to the database: new items wait for review, approved items update in place, nothing is deleted |
| `sync.py` | Runs every source and writes a plain-language report |

## Run it

```bash
DATABASE_URL=... COLLECTOR_CONTACT_EMAIL=... uv run python -m bts_ingest.sync
```

It runs weekly in GitHub Actions ([.github/workflows/sync.yml](../.github/workflows/sync.yml)),
which opens an issue when a page fails or something needs your review.

## Rules

- Never collect a page robots.txt disallows, never log in, never get around a bot challenge.
- Collected text is untrusted data. It's stored as data and never placed in the agent's
  instructions.
- Contact emails on club pages are not stored; students get a link to the club's page instead.
- Parser tests run against saved copies of the real pages in `tests/fixtures/`.
