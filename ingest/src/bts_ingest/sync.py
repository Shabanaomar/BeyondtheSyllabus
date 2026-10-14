"""Weekly data sync: fetch every allowed source, parse it, and store the results.

Run by .github/workflows/sync.yml, or by hand:

    DATABASE_URL=... COLLECTOR_CONTACT_EMAIL=... uv run python -m bts_ingest.sync

Each source is stored in its own transaction, so one broken page never blocks the others and
never leaves partial data behind. The run writes a plain-language report (sync-report.md); the
workflow opens a GitHub issue when anything failed or needs review.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg

from . import store
from .fetch import CollectionError, Fetcher, Page
from .parsers import berkeley, fresno
from .records import ParseResult


@dataclass(frozen=True)
class School:
    slug: str
    name: str
    college: str


FRESNO = School("fresno-state", "Fresno State", "Lyles College of Engineering")
BERKELEY = School("uc-berkeley", "UC Berkeley", "College of Engineering")

StoreFn = Callable[[psycopg.Connection[Any], int, Any, int, store.Report], None]


@dataclass(frozen=True)
class Source:
    school: School
    name: str
    url: str
    parse: Callable[[str], ParseResult[Any]]
    save: StoreFn


SOURCES: list[Source] = [
    Source(
        FRESNO,
        "Engineering clubs",
        fresno.CLUBS_URL,
        fresno.parse_engineering_clubs,
        store.store_organizations,
    ),
    Source(FRESNO, "Industry Expo", fresno.EXPO_URL, fresno.parse_expo, store.store_events),
    Source(
        FRESNO,
        "Academic calendar (this year)",
        fresno.CALENDAR_CURRENT_URL,
        fresno.parse_academic_calendar,
        store.store_terms,
    ),
    Source(
        FRESNO,
        "Academic calendar (next year, tentative)",
        fresno.CALENDAR_NEXT_URL,
        lambda text: fresno.parse_academic_calendar(text, tentative=True),
        store.store_terms,
    ),
    Source(
        BERKELEY,
        "Engineering student groups",
        berkeley.GROUPS_URL,
        berkeley.parse_engineering_groups,
        store.store_organizations,
    ),
]


def run(conn: psycopg.Connection[Any], fetcher: Fetcher, sources: list[Source]) -> tuple[str, bool]:
    """Returns (markdown report, whether every source succeeded)."""
    sections: list[str] = []
    ok = True
    school_ids: dict[str, int] = {}
    for source in sources:
        title = f"### {source.school.name}: {source.name}"
        report = store.Report()
        try:
            page: Page = fetcher.fetch(source.url)
        except CollectionError as error:
            ok = False
            sections.append(f"{title}\n\nFailed: {error}. The last good data is still in use.\n")
            continue
        try:
            with conn.transaction():
                if source.school.slug not in school_ids:
                    school_ids[source.school.slug] = store.ensure_school(
                        conn, source.school.slug, source.school.name, source.school.college
                    )
                school_id = school_ids[source.school.slug]
                source_id = store.record_page(conn, page)
                parsed = source.parse(page.text)
                for problem in parsed.flagged:
                    store.flag(conn, report, source_id, source.url, problem)
                if parsed.items:
                    source.save(conn, school_id, parsed.items, source_id, report)
        except Exception as error:  # report any failure and keep the other sources going
            ok = False
            sections.append(
                f"{title}\n\nFailed while saving: {type(error).__name__}: {error}. "
                "Nothing from this page was saved.\n"
            )
            continue
        details = "\n".join(f"- {line}" for line in report.lines) or "- No changes"
        sections.append(f"{title}\n\n{report.summary()}.\n\n{details}\n")
        if report.flagged:
            ok = False
    header = "## Data sync report\n\n" + (
        "Everything collected cleanly.\n" if ok else "Some sources need attention (see below).\n"
    )
    return header + "\n" + "\n".join(sections), ok


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2
    raw_dir = Path(os.environ.get("RAW_DIR", "ingest/raw"))
    fetcher = Fetcher(raw_dir=raw_dir)
    with psycopg.connect(url, autocommit=True) as conn:
        markdown, ok = run(conn, fetcher, SOURCES)
    Path(os.environ.get("REPORT_PATH", "sync-report.md")).write_text(markdown)
    print(markdown)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
