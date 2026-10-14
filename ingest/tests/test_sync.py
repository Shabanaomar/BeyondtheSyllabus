"""The whole sync against a real database, with pages served from saved copies."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from dbkit import Db

from bts_ingest import sync
from bts_ingest.fetch import BlockedError, Page

FIXTURES = Path(__file__).parent / "fixtures"
GAP = "\n                                 \n                                 "
PAGES = {
    sync.fresno.CLUBS_URL: "fresno_engineering_clubs.html",
    sync.fresno.EXPO_URL: "fresno_expo.html",
    sync.fresno.CALENDAR_CURRENT_URL: "fresno_calendar_current.html",
    sync.fresno.CALENDAR_NEXT_URL: "fresno_calendar_next.html",
    sync.berkeley.GROUPS_URL: "berkeley_engineering_groups.html",
}


class FakeFetcher:
    def __init__(self, overrides: dict[str, str] | None = None, blocked: set[str] | None = None):
        self.overrides = overrides or {}
        self.blocked = blocked or set()

    def fetch(self, url: str) -> Page:
        if url in self.blocked:
            raise BlockedError(f"challenge for {url}")
        text = self.overrides.get(url) or (FIXTURES / PAGES[url]).read_text(encoding="utf-8")
        return Page(url, url, 200, text, str(hash(text)), datetime.now(UTC), None)


def test_first_sync_stores_everything_for_review(db: Db) -> None:
    db.as_superuser()
    report, ok = sync.run(db.conn, FakeFetcher(), sync.SOURCES)  # type: ignore[arg-type]
    assert ok, report
    assert db.one("select count(*) from school") == 2
    assert db.one("select count(*) from organization where review_status = 'pending_review'") == 80
    assert db.one("select count(*) from career_event where review_status = 'pending_review'") == 1
    assert db.all("select code from term order by starts_on") == [
        "2026FA",
        "2027SP",
        "2027FA",
        "2028SP",
    ]
    assert db.one("select count(*) from term where tentative") == 2
    assert db.one("select count(*) from term_date") > 30
    assert "80 new" not in report and "34 new (waiting for your review)" in report


def test_second_sync_changes_nothing(db: Db) -> None:
    db.as_superuser()
    sync.run(db.conn, FakeFetcher(), sync.SOURCES)  # type: ignore[arg-type]
    report, ok = sync.run(db.conn, FakeFetcher(), sync.SOURCES)  # type: ignore[arg-type]
    assert ok
    assert "0 new" in report and "0 updated" in report


def test_changed_facts_update_and_are_reported(db: Db) -> None:
    db.as_superuser()
    sync.run(db.conn, FakeFetcher(), sync.SOURCES)  # type: ignore[arg-type]
    expo = (
        (FIXTURES / "fresno_expo.html")
        .read_text()
        .replace("10 a.m. to 2 p.m.", "11 a.m. to 3 p.m.")
    )
    calendar = (
        (FIXTURES / "fresno_calendar_current.html")
        .read_text()
        .replace("<td>December 23</td>", "<td>December 22</td>")
        .replace(
            "<td>Wednesday</td>" + GAP + "<td>December 22</td>",
            "<td>Tuesday</td><td>December 22</td>",
        )
    )
    report, _ = sync.run(
        db.conn,
        FakeFetcher({sync.fresno.EXPO_URL: expo, sync.fresno.CALENDAR_CURRENT_URL: calendar}),  # type: ignore[arg-type]
        sync.SOURCES,
    )
    assert "Updated event time or place: Welcome Back BBQ & Industry Expo" in report
    assert (
        db.one(
            "select extract(hour from starts_at at time zone 'America/Los_Angeles') "
            "from career_event"
        )
        == 11
    )
    assert "Fall 2026: dates changed" in report
    assert "removed outdated date Last Day of Fall Semester" in report


def test_a_blocked_page_keeps_old_data_and_fails_the_run(db: Db) -> None:
    db.as_superuser()
    sync.run(db.conn, FakeFetcher(), sync.SOURCES)  # type: ignore[arg-type]
    blocked = FakeFetcher(blocked={sync.fresno.CLUBS_URL})
    report, ok = sync.run(db.conn, blocked, sync.SOURCES)  # type: ignore[arg-type]
    assert not ok
    assert "Failed: challenge for" in report and "last good data is still in use" in report
    assert (
        db.one(
            "select count(*) from organization "
            "where school_id = (select id from school where slug = 'fresno-state')"
        )
        == 34
    )


def test_unreadable_rows_go_to_the_review_queue(db: Db) -> None:
    db.as_superuser()
    broken = (
        (FIXTURES / "fresno_expo.html")
        .read_text()
        .replace("Wednesday, Sept. 23", "Friday, Sept. 23")
    )
    report, ok = sync.run(db.conn, FakeFetcher({sync.fresno.EXPO_URL: broken}), sync.SOURCES)  # type: ignore[arg-type]
    assert not ok
    assert db.one("select count(*) from flagged_rule where status = 'open'") == 1
    assert "Flagged for review: Expo weekday doesn't match its date" in report
    assert db.one("select count(*) from career_event") == 0


def test_a_club_dropped_from_its_page_is_reported_not_deleted(db: Db) -> None:
    db.as_superuser()
    sync.run(db.conn, FakeFetcher(), sync.SOURCES)  # type: ignore[arg-type]
    text = (FIXTURES / "fresno_engineering_clubs.html").read_text().replace("Bulldog Racing", "")
    report, _ = sync.run(db.conn, FakeFetcher({sync.fresno.CLUBS_URL: text}), sync.SOURCES)  # type: ignore[arg-type]
    assert "No longer listed on its page (kept, please check): Bulldog Racing" in report
    assert db.one("select count(*) from organization where name = 'Bulldog Racing'") == 1
