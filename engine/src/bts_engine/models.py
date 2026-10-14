"""Plain data types the engine works with.

The engine never talks to the database directly: callers load live catalog rows and the
student's record into these types, so every rule can be tested without a database.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import time
from enum import StrEnum
from typing import Any


class GradeBand(StrEnum):
    C_OR_BETTER = "c_or_better"
    PASSED_BELOW_C = "passed_below_c"
    PASS_NO_PASS = "pass_no_pass"  # noqa: S105 (a grade band, not a password)
    IN_PROGRESS = "in_progress"


class RecordSource(StrEnum):
    MANUAL = "manual"
    REPORT = "report"
    CREDIT = "credit"


class Offering(StrEnum):
    FALL = "fall"
    SPRING = "spring"
    BOTH = "both"
    SUMMER = "summer"
    IRREGULAR = "irregular"
    UNKNOWN = "unknown"


class Season(StrEnum):
    FALL = "FA"
    SPRING = "SP"
    SUMMER = "SU"
    WINTER = "WI"


_TERM_RE = re.compile(r"^(?P<year>[0-9]{4})(?P<season>SP|SU|FA|WI)$")
_SEASON_ORDER = {Season.WINTER: 0, Season.SPRING: 1, Season.SUMMER: 2, Season.FALL: 3}


@dataclass(frozen=True, order=False)
class Term:
    """A term code such as 2027SP. Spring comes before Fall within a calendar year."""

    year: int
    season: Season

    @classmethod
    def parse(cls, code: str) -> Term:
        match = _TERM_RE.match(code)
        if not match:
            raise ValueError(f"Not a term code: {code!r} (expected e.g. 2027SP)")
        return cls(int(match["year"]), Season(match["season"]))

    @property
    def code(self) -> str:
        return f"{self.year}{self.season.value}"

    def sort_key(self) -> tuple[int, int]:
        return (self.year, _SEASON_ORDER[self.season])

    def __lt__(self, other: Term) -> bool:
        return self.sort_key() < other.sort_key()

    def __le__(self, other: Term) -> bool:
        return self.sort_key() <= other.sort_key()

    def next_regular(self) -> Term:
        """The next fall or spring term (summer and winter are optional extras)."""
        if self.season == Season.FALL:
            return Term(self.year + 1, Season.SPRING)
        return Term(self.year, Season.FALL)

    def __str__(self) -> str:
        names = {Season.FALL: "Fall", Season.SPRING: "Spring", Season.SUMMER: "Summer"}
        return f"{names.get(self.season, 'Winter')} {self.year}"


def course_key(subject: str, number: str) -> str:
    """The stable key the engine uses for a course, e.g. 'MEC ENG 40'."""
    return f"{subject.strip().upper()} {number.strip().upper()}"


def split_key(key: str) -> tuple[str, str]:
    subject, _, number = key.rpartition(" ")
    return subject, number


def number_value(number: str) -> int | None:
    """The numeric part of a course number: 'C100' -> 100, '61A' -> 61."""
    match = re.search(r"[0-9]+", number)
    return int(match.group()) if match else None


@dataclass(frozen=True)
class Course:
    key: str
    title: str
    units_min: float
    units_max: float
    prereq_rule: dict[str, Any] | None = None
    coreq_rule: dict[str, Any] | None = None
    offered: Offering = Offering.UNKNOWN
    source_url: str | None = None
    tags: frozenset[str] = frozenset()

    @property
    def units(self) -> float:
        """Units used for planning: the maximum, so plans never under-count load."""
        return self.units_max

    def offered_in(self, term: Term) -> bool | None:
        """True/False when known, None when the offering pattern is unknown or irregular."""
        if self.offered in (Offering.UNKNOWN, Offering.IRREGULAR):
            return None
        if self.offered == Offering.BOTH:
            return term.season in (Season.FALL, Season.SPRING)
        mapping = {Offering.FALL: Season.FALL, Offering.SPRING: Season.SPRING}
        season = mapping.get(self.offered, Season.SUMMER)
        return term.season == season


@dataclass(frozen=True)
class Milestone:
    code: str
    name: str
    how_to_satisfy: str
    satisfying_courses: frozenset[str] = frozenset()
    can_be_met_by_exam: bool = False
    source_url: str | None = None


class RuleKind(StrEnum):
    ALL_OF = "all_of"
    CHOOSE_COURSES = "choose_courses"
    CHOOSE_UNITS = "choose_units"


@dataclass(frozen=True)
class CourseOption:
    course: str


@dataclass(frozen=True)
class PatternOption:
    subject: str
    number_min: int
    number_max: int
    exclusions: frozenset[str] = frozenset()

    def matches(self, key: str) -> bool:
        subject, number = split_key(key)
        value = number_value(number)
        return (
            subject == self.subject.upper()
            and value is not None
            and self.number_min <= value <= self.number_max
            and key not in self.exclusions
        )


@dataclass(frozen=True)
class MilestoneOption:
    milestone: str


Option = CourseOption | PatternOption | MilestoneOption


@dataclass(frozen=True)
class Overlap:
    """Whether courses used here may also count toward other groups."""

    default: str = "exclusive"  # "exclusive" or "shared"
    may_share_with: frozenset[str] = frozenset()
    max_shared_units: float | None = None


@dataclass(frozen=True)
class RequirementGroup:
    id: str
    name: str
    rule: RuleKind
    count: float | None = None
    options: tuple[Option, ...] = ()
    children: tuple[RequirementGroup, ...] = ()
    min_grade: GradeBand | None = None
    overlap: Overlap = field(default_factory=Overlap)
    advisory_checks: tuple[dict[str, Any], ...] = ()
    source_url: str | None = None
    level: str = "major"

    def walk(self) -> list[RequirementGroup]:
        groups = [self]
        for child in self.children:
            groups.extend(child.walk())
        return groups


@dataclass(frozen=True)
class Program:
    school: str
    major_code: str
    name: str
    catalog_year: str
    total_units: float | None
    groups: tuple[RequirementGroup, ...]
    source_url: str | None = None

    def all_groups(self) -> list[RequirementGroup]:
        result: list[RequirementGroup] = []
        for group in self.groups:
            result.extend(group.walk())
        return result


@dataclass
class Catalog:
    """Live catalog data for one school and catalog year."""

    courses: dict[str, Course]
    milestones: dict[str, Milestone] = field(default_factory=dict)
    # Pairs of equivalent course keys (renumbered or cross-listed).
    equivalents: list[tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._canon: dict[str, str] = {}
        for a, b in self.equivalents:
            self._union(a, b)

    def _find(self, key: str) -> str:
        parent = self._canon.get(key, key)
        if parent == key:
            return key
        root = self._find(parent)
        self._canon[key] = root
        return root

    def _union(self, a: str, b: str) -> None:
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            # Deterministic: the alphabetically smaller key is the representative.
            low, high = sorted((ra, rb))
            self._canon[high] = low
            self._canon.setdefault(low, low)

    def canonical(self, key: str) -> str:
        return self._find(key)

    def same_course(self, a: str, b: str) -> bool:
        return self._find(a) == self._find(b)


@dataclass(frozen=True)
class CourseRecord:
    """One course the student has completed, is taking, or has credit for."""

    course: str
    grade: GradeBand
    source: RecordSource = RecordSource.MANUAL
    term: str | None = None


@dataclass(frozen=True)
class RequirementCredit:
    """'I have credit for this requirement' (e.g. AP credit covering a GE area)."""

    group_id: str | None = None
    milestone: str | None = None
    note: str | None = None


@dataclass
class StudentRecord:
    courses: list[CourseRecord] = field(default_factory=list)
    credits: list[RequirementCredit] = field(default_factory=list)
    standing: str | None = None  # e.g. "junior", when known
    milestones_met: set[str] = field(default_factory=set)


class Weekday(StrEnum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


@dataclass(frozen=True)
class Meeting:
    days: frozenset[Weekday]
    start: time
    end: time

    def overlaps(self, other: Meeting) -> bool:
        return bool(self.days & other.days) and self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class Section:
    """A section the student is considering, entered from their student portal."""

    course: str
    code: str
    meetings: tuple[Meeting, ...]
    units: float | None = None


@dataclass(frozen=True)
class TimeBlock:
    """Work shift, commute or other fixed time."""

    day: Weekday
    start: time
    end: time
    kind: str = "work"

    def as_meeting(self) -> Meeting:
        return Meeting(frozenset({self.day}), self.start, self.end)
