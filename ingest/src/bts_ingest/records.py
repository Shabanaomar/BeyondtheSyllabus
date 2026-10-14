"""What collectors produce. Plain data, written to the database by store.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class OrganizationRecord:
    name: str
    kind: str  # professional / social / both
    abbreviation: str | None = None
    category: str | None = None  # the heading the source page lists it under
    description: str | None = None
    url: str | None = None
    tags: tuple[str, ...] = ()
    majors: tuple[str, ...] = ()


@dataclass(frozen=True)
class EventRecord:
    title: str
    kind: str  # fair / info_session / workshop
    starts_at: datetime
    ends_at: datetime | None = None
    location: str | None = None
    url: str | None = None
    majors: tuple[str, ...] = ()


@dataclass(frozen=True)
class CalendarEntry:
    """One row of an academic calendar: a single day or a range of days."""

    term_code: str
    label: str
    starts_on: date
    ends_on: date
    kind: str  # term_start, term_end, instruction_start, instruction_end, holiday, finals, other


@dataclass(frozen=True)
class TermDates:
    code: str
    name: str
    starts_on: date
    ends_on: date
    tentative: bool = False
    entries: tuple[CalendarEntry, ...] = ()


@dataclass
class ParseResult[T]:
    items: list[T] = field(default_factory=list)
    # Rows the parser couldn't read confidently; they go to the review queue, never to students.
    flagged: list[str] = field(default_factory=list)
