"""Next-term schedule: check the sections a student is considering against their week.

Class times can't be collected from either school, so the student adds the sections they're
considering from their student portal. This module:

* finds clashes between sections, and between sections and work shifts or other fixed time;
* checks each course's prerequisites for that term;
* picks the best clash-free combination when the student lists several sections per course.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time

from .models import Catalog, GradeBand, Section, StudentRecord, Term, TimeBlock
from .rules import RuleContext, Status, best_records, evaluate


@dataclass(frozen=True)
class Clash:
    first: str
    second: str
    message: str


@dataclass
class ScheduleCheck:
    clashes: list[Clash] = field(default_factory=list)
    prerequisite_problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    units: float = 0.0

    @property
    def passed(self) -> bool:
        return not self.clashes and not self.prerequisite_problems


def _label(section: Section) -> str:
    return f"{section.course} ({section.code})"


def _block_label(block: TimeBlock) -> str:
    return f"{block.kind} {block.day.value.title()} {block.start:%H:%M}-{block.end:%H:%M}"


def check_sections(
    sections: list[Section],
    blocks: list[TimeBlock],
    term: str,
    catalog: Catalog,
    record: StudentRecord,
    units_max: float | None = None,
    standing: str | None = None,
) -> ScheduleCheck:
    out = ScheduleCheck()
    for i, a in enumerate(sections):
        for b in sections[i + 1 :]:
            if any(ma.overlaps(mb) for ma in a.meetings for mb in b.meetings):
                out.clashes.append(
                    Clash(_label(a), _label(b), f"{_label(a)} and {_label(b)} overlap")
                )
        for block in blocks:
            if any(m.overlaps(block.as_meeting()) for m in a.meetings):
                out.clashes.append(
                    Clash(
                        _label(a),
                        _block_label(block),
                        f"{_label(a)} overlaps your {_block_label(block)}",
                    )
                )

    best = best_records(record, catalog)
    in_progress = {k for k, r in best.items() if r.grade == GradeBand.IN_PROGRESS}
    same = frozenset(catalog.canonical(s.course) for s in sections)
    ctx = RuleContext(
        catalog=catalog,
        finished=best,
        finished_before=frozenset(in_progress),
        same_term=same,
        standing=standing,
        milestones_met=frozenset(record.milestones_met),
    )
    when = Term.parse(term)
    for section in sections:
        course = catalog.courses.get(section.course)
        if course is None:
            out.warnings.append(f"{section.course} isn't in our course list; check it yourself")
            out.units += section.units or 0
            continue
        out.units += section.units if section.units is not None else course.units
        result = evaluate(course.prereq_rule, ctx)
        if result.status == Status.NOT_MET:
            out.prerequisite_problems.append(f"{section.course}: " + "; ".join(result.reasons))
        elif result.status == Status.NEEDS_ACTION:
            out.warnings.extend(f"{section.course}: {r}" for r in result.reasons)
        out.warnings.extend(f"{section.course}: {a}" for a in result.assumes)
        if course.offered_in(when) is False:
            out.warnings.append(
                f"{section.course} is usually offered in {course.offered.value} only"
            )
    if units_max is not None and out.units > units_max:
        out.warnings.append(f"{out.units:g} units is over your limit of {units_max:g}")
    return out


@dataclass(frozen=True)
class TimePreferences:
    avoid_before: time | None = None
    avoid_after: time | None = None


def best_combination(
    options: dict[str, list[Section]],
    blocks: list[TimeBlock],
    preferences: TimePreferences | None = None,
) -> tuple[list[Section], list[str]]:
    """Choose one section per course with no clashes, fitting as many courses as possible.

    Ties go to the combination with the fewest meetings outside the preferred hours. Returns the
    chosen sections and the courses that couldn't fit.
    """
    prefs = preferences or TimePreferences()
    courses = sorted(options, key=lambda c: (len(options[c]), c))
    blocked = [b.as_meeting() for b in blocks]

    def fits(section: Section, chosen: list[Section]) -> bool:
        for m in section.meetings:
            if any(m.overlaps(b) for b in blocked):
                return False
            if any(m.overlaps(o) for s in chosen for o in s.meetings):
                return False
        return True

    def penalty(section: Section) -> int:
        count = 0
        for m in section.meetings:
            if prefs.avoid_before and m.start < prefs.avoid_before:
                count += len(m.days)
            if prefs.avoid_after and m.end > prefs.avoid_after:
                count += len(m.days)
        return count

    best: tuple[int, int, list[Section]] = (-1, 0, [])

    def search(index: int, chosen: list[Section], cost: int) -> None:
        nonlocal best
        if index == len(courses):
            score = (len(chosen), -cost)
            if score > (best[0], -best[1]):
                best = (len(chosen), cost, list(chosen))
            return
        # Upper bound: even taking every remaining course can't beat the best.
        if len(chosen) + (len(courses) - index) < best[0]:
            return
        for section in sorted(options[courses[index]], key=lambda s: (penalty(s), s.code)):
            if fits(section, chosen):
                chosen.append(section)
                search(index + 1, chosen, cost + penalty(section))
                chosen.pop()
        search(index + 1, chosen, cost)  # skip this course

    search(0, [], 0)
    chosen = best[2]
    placed = {s.course for s in chosen}
    return chosen, [c for c in sorted(options) if c not in placed]
