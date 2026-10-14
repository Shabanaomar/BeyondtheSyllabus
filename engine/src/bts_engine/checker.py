"""Independent check of a multi-term plan.

The planner builds plans; the checker verifies any plan, including one a student edited by hand.
A plan passes only when every course's prerequisites are met in time, no course is placed in a
term it isn't offered, no term goes over the unit limit, no course appears twice, and the plan
finishes every requirement. Anything the engine can't verify is a warning, not a failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .audit import GroupStatus, audit
from .models import (
    Catalog,
    CourseRecord,
    GradeBand,
    Program,
    RecordSource,
    StudentRecord,
    Term,
)
from .rules import RuleContext, Status, best_records, evaluate


class ProblemKind(StrEnum):
    UNKNOWN_COURSE = "unknown_course"
    PREREQUISITE = "prerequisite"
    COREQUISITE = "corequisite"
    NOT_OFFERED = "not_offered"
    OVER_UNITS = "over_units"
    DUPLICATE = "duplicate"
    ALREADY_TAKEN = "already_taken"
    UNFINISHED_REQUIREMENT = "unfinished_requirement"


@dataclass(frozen=True)
class Problem:
    kind: ProblemKind
    message: str
    term: str | None = None
    course: str | None = None


@dataclass
class CheckResult:
    problems: list[Problem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.problems


def check_plan(
    program: Program,
    catalog: Catalog,
    record: StudentRecord,
    terms: list[tuple[str, list[str]]],
    units_max: float,
    standing: str | None = None,
) -> CheckResult:
    """Check a plan given as [(term code, [course keys]), ...] in any order."""
    out = CheckResult()
    best = best_records(record, catalog)
    ordered = sorted(terms, key=lambda t: Term.parse(t[0]))
    done_before = {k for k, r in best.items() if r.grade == GradeBand.IN_PROGRESS}
    seen: dict[str, str] = {}

    for code, courses in ordered:
        term = Term.parse(code)
        same = {catalog.canonical(c) for c in courses}
        units = 0.0
        for key in courses:
            canon = catalog.canonical(key)
            course = catalog.courses.get(key)
            if course is None:
                out.problems.append(
                    Problem(ProblemKind.UNKNOWN_COURSE, f"{key} isn't in the catalog", code, key)
                )
                continue
            units += course.units
            if canon in seen:
                out.problems.append(
                    Problem(
                        ProblemKind.DUPLICATE,
                        f"{key} is planned twice ({seen[canon]} and {code})",
                        code,
                        key,
                    )
                )
            seen[canon] = code
            prior = best.get(canon)
            if prior is not None and prior.grade != GradeBand.PASSED_BELOW_C:
                out.problems.append(
                    Problem(ProblemKind.ALREADY_TAKEN, f"You already have {key}", code, key)
                )
            ctx = RuleContext(
                catalog=catalog,
                finished=best,
                finished_before=frozenset(done_before),
                same_term=frozenset(same),
                standing=standing,
                milestones_met=frozenset(record.milestones_met),
            )
            for rule, kind in (
                (course.prereq_rule, ProblemKind.PREREQUISITE),
                (course.coreq_rule, ProblemKind.COREQUISITE),
            ):
                result = evaluate(rule, ctx)
                if result.status == Status.NOT_MET:
                    out.problems.append(
                        Problem(kind, f"{key} in {term}: " + "; ".join(result.reasons), code, key)
                    )
                elif result.status == Status.NEEDS_ACTION:
                    out.warnings.extend(f"{key}: {r}" for r in result.reasons)
            offered = course.offered_in(term)
            if offered is False:
                out.problems.append(
                    Problem(
                        ProblemKind.NOT_OFFERED,
                        f"{key} is usually offered in {course.offered.value} only, not {term}",
                        code,
                        key,
                    )
                )
            elif offered is None:
                out.warnings.append(f"{key}: check it's offered in {term}")
        if units > units_max:
            out.problems.append(
                Problem(
                    ProblemKind.OVER_UNITS,
                    f"{term} has {units:g} units, over your limit of {units_max:g}",
                    code,
                )
            )
        done_before |= same

    # Does the plan finish the degree? Audit as if every planned course were in progress.
    planned_records = [
        CourseRecord(k, GradeBand.IN_PROGRESS, RecordSource.MANUAL, code)
        for code, courses in ordered
        for k in courses
        if k in catalog.courses
    ]
    future = StudentRecord(
        courses=[*record.courses, *planned_records],
        credits=record.credits,
        standing=record.standing,
        milestones_met=record.milestones_met,
    )
    final = audit(program, catalog, future)
    for group in final.flat():
        if group.children:
            continue
        if group.status == GroupStatus.INCOMPLETE:
            out.problems.append(
                Problem(
                    ProblemKind.UNFINISHED_REQUIREMENT,
                    f"The plan doesn't finish {group.name}",
                )
            )
        out.warnings.extend(n for n in group.notes if "advisor" in n or "confirm" in n)
    out.warnings = list(dict.fromkeys(out.warnings))
    return out
