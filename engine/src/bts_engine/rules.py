"""Grade bands and prerequisite rules.

Prerequisite rules are small JSON trees stored next to the original catalog wording:

    {"all": [ ... ]}                       every child must be met
    {"any": [ ... ]}                       at least one child must be met
    {"course": "MATH 76",                  a course, optionally with a minimum grade band and
     "min_grade_band": "c_or_better",      "may be taken in the same term" (concurrent_ok)
     "concurrent_ok": true}
    {"permission": "instructor"}           can't be checked: the student must ask
    {"standing": "junior"}                 class standing
    {"milestone": "UC-ELWR"}               a non-course requirement

A "min_grade_band" on an all/any node applies to every course inside it that doesn't set its
own. Anything the engine can't verify comes back as NEEDS_ACTION with a plain-language reason,
never as met.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .models import Catalog, CourseRecord, GradeBand, RecordSource, StudentRecord

PASSING = (GradeBand.C_OR_BETTER, GradeBand.PASSED_BELOW_C, GradeBand.PASS_NO_PASS)
_BAND_RANK = {
    GradeBand.C_OR_BETTER: 3,
    GradeBand.PASSED_BELOW_C: 2,
    GradeBand.PASS_NO_PASS: 1,
    GradeBand.IN_PROGRESS: 0,
}
_STANDING_RANK = {"freshman": 1, "sophomore": 2, "junior": 3, "senior": 4}


def grade_meets(grade: GradeBand, minimum: GradeBand | None) -> bool:
    """Whether a finished course's grade band satisfies a minimum. In-progress never does."""
    if grade == GradeBand.IN_PROGRESS:
        return False
    if minimum is None or minimum == GradeBand.PASS_NO_PASS:
        return grade in PASSING
    if minimum == GradeBand.PASSED_BELOW_C:
        # A passing letter grade. Pass/no-pass doesn't show a letter, so it doesn't count.
        return grade in (GradeBand.C_OR_BETTER, GradeBand.PASSED_BELOW_C)
    return grade == GradeBand.C_OR_BETTER


def best_records(record: StudentRecord, catalog: Catalog) -> dict[str, CourseRecord]:
    """The best record per course, keyed by canonical course key (equivalents merged)."""
    best: dict[str, CourseRecord] = {}
    for entry in record.courses:
        key = catalog.canonical(entry.course)
        current = best.get(key)
        if current is None or _BAND_RANK[entry.grade] > _BAND_RANK[current.grade]:
            best[key] = entry
    return best


class Status(StrEnum):
    MET = "met"
    NOT_MET = "not_met"
    NEEDS_ACTION = "needs_action"


@dataclass
class RuleResult:
    status: Status
    # Plain-language notes, e.g. "Needs instructor permission: ask the department".
    reasons: list[str] = field(default_factory=list)
    # Courses that would satisfy what's missing (for planning).
    missing_courses: list[str] = field(default_factory=list)
    # True when the result relies on a course in progress or on reported credit.
    assumes: list[str] = field(default_factory=list)


@dataclass
class RuleContext:
    """Everything a prerequisite check needs to know about the student at a point in time."""

    catalog: Catalog
    # Finished courses (canonical key -> best record).
    finished: Mapping[str, CourseRecord]
    # Courses that will be finished before the term being checked: in progress now, or planned
    # in an earlier term. Assumed passed with a C or better, and flagged as an assumption.
    finished_before: frozenset[str] = frozenset()
    # Courses taken in the same term (for "may be taken concurrently").
    same_term: frozenset[str] = frozenset()
    standing: str | None = None
    milestones_met: frozenset[str] = frozenset()


def evaluate(rule: Mapping[str, Any] | None, ctx: RuleContext) -> RuleResult:
    """Check a prerequisite rule. No rule means nothing is required."""
    if not rule:
        return RuleResult(Status.MET)
    return _evaluate(rule, ctx, inherited_min=None)


def _evaluate(
    node: Mapping[str, Any], ctx: RuleContext, inherited_min: GradeBand | None
) -> RuleResult:
    minimum = _band(node.get("min_grade_band")) or inherited_min
    if "all" in node:
        return _combine_all([_evaluate(child, ctx, minimum) for child in node["all"]])
    if "any" in node:
        return _combine_any([_evaluate(child, ctx, minimum) for child in node["any"]])
    if "course" in node:
        return _course(str(node["course"]), minimum, bool(node.get("concurrent_ok")), ctx)
    if "permission" in node:
        who = str(node["permission"])
        return RuleResult(
            Status.NEEDS_ACTION, [f"Needs {who} permission: ask the department before enrolling"]
        )
    if "standing" in node:
        return _standing(str(node["standing"]), ctx)
    if "milestone" in node:
        code = str(node["milestone"])
        if code in ctx.milestones_met:
            return RuleResult(Status.MET)
        return RuleResult(Status.NOT_MET, [f"Requires {code}"])
    text = str(node.get("text", "an unrecognised condition"))
    return RuleResult(Status.NEEDS_ACTION, [f"Check with your advisor: {text}"])


def _band(value: Any) -> GradeBand | None:
    return GradeBand(value) if value else None


def _course(
    raw_key: str, minimum: GradeBand | None, concurrent_ok: bool, ctx: RuleContext
) -> RuleResult:
    key = ctx.catalog.canonical(raw_key)
    record = ctx.finished.get(key)
    if record is not None and grade_meets(record.grade, minimum):
        assumes = (
            [f"{raw_key}: confirm this credit appears on your record"]
            if record.source == RecordSource.CREDIT
            else []
        )
        return RuleResult(Status.MET, assumes=assumes)
    if key in ctx.finished_before:
        return RuleResult(Status.MET, assumes=[f"Assumes you pass {raw_key}"])
    if concurrent_ok and key in ctx.same_term:
        return RuleResult(Status.MET, assumes=[f"Take {raw_key} in the same term"])
    if record is not None and record.grade != GradeBand.IN_PROGRESS:
        needed = "a C or better" if minimum == GradeBand.C_OR_BETTER else "a passing letter grade"
        return RuleResult(
            Status.NOT_MET,
            [f"{raw_key} needs {needed}; your recorded grade doesn't meet it"],
            missing_courses=[raw_key],
        )
    return RuleResult(Status.NOT_MET, [f"Requires {raw_key}"], missing_courses=[raw_key])


def _standing(required: str, ctx: RuleContext) -> RuleResult:
    need = _STANDING_RANK.get(required.lower())
    have = _STANDING_RANK.get((ctx.standing or "").lower())
    if need is None or have is None:
        return RuleResult(
            Status.NEEDS_ACTION, [f"Requires {required} standing: check your standing"]
        )
    if have >= need:
        return RuleResult(Status.MET)
    return RuleResult(Status.NOT_MET, [f"Requires {required} standing"])


def _combine_all(results: Iterable[RuleResult]) -> RuleResult:
    results = list(results)
    out = RuleResult(Status.MET)
    for r in results:
        out.reasons.extend(r.reasons)
        out.missing_courses.extend(r.missing_courses)
        out.assumes.extend(r.assumes)
    if any(r.status == Status.NOT_MET for r in results):
        out.status = Status.NOT_MET
    elif any(r.status == Status.NEEDS_ACTION for r in results):
        out.status = Status.NEEDS_ACTION
    return out


def _combine_any(results: Iterable[RuleResult]) -> RuleResult:
    results = list(results)
    met = [r for r in results if r.status == Status.MET]
    if met:
        # Prefer an option that needs no assumptions.
        return min(met, key=lambda r: len(r.assumes))
    action = [r for r in results if r.status == Status.NEEDS_ACTION]
    if action:
        return action[0]
    out = RuleResult(Status.NOT_MET)
    options = [r for r in results if r.missing_courses]
    if options:
        # Suggest the option that needs the fewest courses.
        cheapest = min(options, key=lambda r: len(r.missing_courses))
        out.missing_courses = list(cheapest.missing_courses)
    out.reasons = [
        "Requires one of: " + "; ".join(" and ".join(r.missing_courses) or "?" for r in results)
    ]
    return out


def courses_in_rule(rule: Mapping[str, Any] | None) -> set[str]:
    """Every course key mentioned anywhere in a rule (for ordering plans)."""
    found: set[str] = set()
    if not rule:
        return found
    if "course" in rule:
        found.add(str(rule["course"]))
    for key in ("all", "any"):
        for child in rule.get(key, []):
            found |= courses_in_rule(child)
    return found


def needs_action(rule: Mapping[str, Any] | None) -> bool:
    """Whether a rule contains anything the student must arrange themselves (permission,
    standing, or wording we couldn't turn into a rule)."""
    if not rule:
        return False
    if any(k in rule for k in ("permission", "standing", "text")):
        return True
    return any(needs_action(child) for k in ("all", "any") for child in rule.get(k, []))
