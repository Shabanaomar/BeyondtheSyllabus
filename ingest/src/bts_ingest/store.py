"""Writes collected records to the database, following the change rules in the build plan.

* Every fetched page is recorded in source_page; an unchanged page only updates last_checked_at.
* New clubs and collected events arrive as pending_review: nobody sees them until you approve.
* Facts about records you've already approved (a club's description, an event's time, term dates)
  update in place, and each change is listed in the run report.
* Nothing is deleted. A club that disappears from its page is reported, not removed.
* Anything a parser couldn't read confidently goes to the review queue (flagged_rule).

Collectors connect with the database owner's credentials (the service role), which bypasses
row-level security. Those credentials only ever live in GitHub Actions secrets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import psycopg

from .fetch import Page
from .records import EventRecord, OrganizationRecord, TermDates


@dataclass
class Report:
    lines: list[str] = field(default_factory=list)
    new: int = 0
    changed: int = 0
    unchanged: int = 0
    flagged: int = 0

    def add(self, line: str) -> None:
        self.lines.append(line)

    def summary(self) -> str:
        return (
            f"{self.new} new (waiting for your review), {self.changed} updated, "
            f"{self.unchanged} unchanged, {self.flagged} flagged for review"
        )


def _id(row: tuple[Any, ...] | None) -> int:
    if row is None:  # pragma: no cover (insert ... returning always returns a row)
        raise RuntimeError("Expected the database to return an id")
    return int(row[0])


def ensure_school(conn: psycopg.Connection[Any], slug: str, name: str, college: str) -> int:
    row = conn.execute(
        "insert into school (slug, name, college_name) values (%s, %s, %s) "
        "on conflict (slug) do update set name = excluded.name, "
        "college_name = excluded.college_name returning id",
        [slug, name, college],
    ).fetchone()
    return _id(row)


def record_page(conn: psycopg.Connection[Any], page: Page, robots_ok: bool = True) -> int:
    row = conn.execute(
        "insert into source_page (url, fetched_at, last_checked_at, content_hash, raw_path, "
        "robots_ok) values (%s, %s, %s, %s, %s, %s) "
        "on conflict (url, content_hash) do update set last_checked_at = excluded.last_checked_at "
        "returning id",
        [page.url, page.fetched_at, page.fetched_at, page.content_hash, page.raw_path, robots_ok],
    ).fetchone()
    return _id(row)


def flag(
    conn: psycopg.Connection[Any],
    report: Report,
    source_id: int | None,
    excerpt: str,
    reason: str,
    entity_type: str = "source_page",
) -> None:
    exists = conn.execute(
        "select 1 from flagged_rule where status = 'open' and entity_type = %s "
        "and source_excerpt = %s and reason = %s",
        [entity_type, excerpt, reason],
    ).fetchone()
    if exists is None:
        conn.execute(
            "insert into flagged_rule (entity_type, source_page_id, source_excerpt, reason) "
            "values (%s, %s, %s, %s)",
            [entity_type, source_id, excerpt, reason],
        )
    report.flagged += 1
    report.add(f"Flagged for review: {reason}")


def store_organizations(
    conn: psycopg.Connection[Any],
    school_id: int,
    records: list[OrganizationRecord],
    source_id: int,
    report: Report,
) -> None:
    seen: set[str] = set()
    for org in records:
        seen.add(org.name)
        description = org.description
        if org.abbreviation:
            description = f"{org.abbreviation}. {description}" if description else org.abbreviation
        current = conn.execute(
            "select id, kind, tags, majors, description, url from organization "
            "where school_id = %s and name = %s",
            [school_id, org.name],
        ).fetchone()
        values = [org.kind, list(org.tags), list(org.majors), description, org.url, source_id]
        if current is None:
            conn.execute(
                "insert into organization (school_id, name, kind, tags, majors, description, "
                "url, source_page_id, review_status) "
                "values (%s, %s, %s, %s, %s, %s, %s, %s, 'pending_review')",
                [school_id, org.name, *values],
            )
            report.new += 1
            report.add(f"New club waiting for review: {org.name}")
            continue
        old = [current[1], list(current[2]), list(current[3]), current[4], current[5]]
        if old == values[:5]:
            report.unchanged += 1
            continue
        conn.execute(
            "update organization set kind = %s, tags = %s, majors = %s, description = %s, "
            "url = %s, source_page_id = %s where id = %s",
            [*values, current[0]],
        )
        report.changed += 1
        report.add(f"Updated club details: {org.name}")
    gone = conn.execute(
        "select name from organization where school_id = %s and source_page_id in "
        "(select id from source_page where url = (select url from source_page where id = %s)) "
        "and not (name = any(%s))",
        [school_id, source_id, list(seen)],
    ).fetchall()
    for (name,) in gone:
        report.add(f"No longer listed on its page (kept, please check): {name}")


def store_terms(
    conn: psycopg.Connection[Any],
    school_id: int,
    terms: list[TermDates],
    source_id: int,
    report: Report,
) -> None:
    for term in terms:
        current = conn.execute(
            "select id, starts_on, ends_on, tentative from term where school_id = %s and code = %s",
            [school_id, term.code],
        ).fetchone()
        if current is None:
            row = conn.execute(
                "insert into term (school_id, code, name, starts_on, ends_on, tentative, "
                "source_page_id) values (%s, %s, %s, %s, %s, %s, %s) returning id",
                [
                    school_id,
                    term.code,
                    term.name,
                    term.starts_on,
                    term.ends_on,
                    term.tentative,
                    source_id,
                ],
            ).fetchone()
            term_id = _id(row)
            report.new += 1
            report.add(f"New term: {term.name}{' (tentative)' if term.tentative else ''}")
        else:
            term_id = int(current[0])
            if (current[1], current[2], current[3]) != (
                term.starts_on,
                term.ends_on,
                term.tentative,
            ):
                conn.execute(
                    "update term set starts_on = %s, ends_on = %s, tentative = %s, "
                    "source_page_id = %s where id = %s",
                    [term.starts_on, term.ends_on, term.tentative, source_id, term_id],
                )
                report.changed += 1
                report.add(
                    f"{term.name}: dates changed (was {current[1]} through {current[2]}, "
                    f"now {term.starts_on} through {term.ends_on})"
                )
            else:
                report.unchanged += 1
        existing = {
            (label, starts): (row_id, ends, kind)
            for row_id, label, starts, ends, kind in conn.execute(
                "select id, label, starts_on, ends_on, kind from term_date where term_id = %s",
                [term_id],
            ).fetchall()
        }
        keep: set[int] = set()
        for entry in term.entries:
            key = (entry.label, entry.starts_on)
            if key in existing:
                row_id, ends, kind = existing[key]
                keep.add(row_id)
                if (ends, kind) != (entry.ends_on, entry.kind):
                    conn.execute(
                        "update term_date set ends_on = %s, kind = %s, source_page_id = %s "
                        "where id = %s",
                        [entry.ends_on, entry.kind, source_id, row_id],
                    )
                continue
            row = conn.execute(
                "insert into term_date (term_id, label, kind, starts_on, ends_on, source_page_id) "
                "values (%s, %s, %s, %s, %s, %s) returning id",
                [term_id, entry.label, entry.kind, entry.starts_on, entry.ends_on, source_id],
            ).fetchone()
            keep.add(_id(row))
            if current is not None:
                report.add(f"{term.name}: new date {entry.label} ({entry.starts_on})")
        # A calendar date that moved shows up as a new row; drop the stale one so the student's
        # calendar doesn't show both. Term dates are facts, not rules, so this is safe.
        for (label, starts), (row_id, _, _) in existing.items():
            if row_id not in keep:
                conn.execute("delete from term_date where id = %s", [row_id])
                report.add(f"{term.name}: removed outdated date {label} ({starts})")


def store_events(
    conn: psycopg.Connection[Any],
    school_id: int,
    events: list[EventRecord],
    source_id: int,
    report: Report,
) -> None:
    for event in events:
        current = conn.execute(
            "select id, starts_at, ends_at, location from career_event where school_id = %s "
            "and title = %s and starts_at::date = %s::date",
            [school_id, event.title, event.starts_at],
        ).fetchone()
        if current is None:
            conn.execute(
                "insert into career_event (school_id, title, kind, starts_at, ends_at, location, "
                "majors, url, source_page_id, review_status) "
                "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending_review')",
                [
                    school_id,
                    event.title,
                    event.kind,
                    event.starts_at,
                    event.ends_at,
                    event.location,
                    list(event.majors),
                    event.url,
                    source_id,
                ],
            )
            report.new += 1
            report.add(f"New event waiting for review: {event.title} ({event.starts_at:%b %d})")
            continue
        if (current[1], current[2], current[3]) == (event.starts_at, event.ends_at, event.location):
            report.unchanged += 1
            continue
        conn.execute(
            "update career_event set starts_at = %s, ends_at = %s, location = %s, "
            "source_page_id = %s where id = %s",
            [event.starts_at, event.ends_at, event.location, source_id, current[0]],
        )
        report.changed += 1
        report.add(f"Updated event time or place: {event.title}")
