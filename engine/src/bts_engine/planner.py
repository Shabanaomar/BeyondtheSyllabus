"""Long-term plan: every remaining course placed in a term, in an order that works.

1. Work out what's still needed from the audit: specific courses, plus picks for "choose"
   groups (courses whose prerequisites are already met and that match the student's interests
   come first).
2. Add any prerequisites the student hasn't taken, so the plan never assumes a course out of
   thin air.
3. Fill terms from the next one onward. Each term takes courses whose prerequisites will be done
   by then and that are offered that term, longest prerequisite chains first, up to the
   student's unit limit.

Every item carries a one-line reason, built from real data rather than written by an AI.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .audit import GroupAudit, GroupStatus, audit
from .models import (
    Catalog,
    CourseRecord,
    GradeBand,
    Program,
    RecordSource,
    RuleKind,
    StudentRecord,
    Term,
    number_value,
    split_key,
)
from .rules import RuleContext, Status, best_records, courses_in_rule, evaluate, needs_action

ENGINE_VERSION = "0.1.0"


@dataclass
class PlanItem:
    course: str
    title: str
    units: float
    reason: str
    groups: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    offering_unknown: bool = False


@dataclass
class PlannedTerm:
    term: str
    items: list[PlanItem] = field(default_factory=list)

    @property
    def units(self) -> float:
        return sum(i.units for i in self.items)


@dataclass
class Plan:
    terms: list[PlannedTerm]
    issues: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    relies_on_credit: bool = False
    engine_version: str = ENGINE_VERSION

    def placed(self) -> dict[str, str]:
        return {i.course: t.term for t in self.terms for i in t.items}


@dataclass
class PlanOptions:
    start_term: str
    units_min: float = 12
    units_max: float = 16
    max_terms: int = 10
    interests: tuple[str, ...] = ()
    standing: str | None = None


@dataclass
class _Need:
    course: str
    reasons: list[str]
    groups: list[str]


def build_plan(
    program: Program, catalog: Catalog, record: StudentRecord, options: PlanOptions
) -> Plan:
    result = audit(program, catalog, record)
    best = best_records(record, catalog)
    have = set(best)  # canonical keys finished or in progress
    in_progress = {k for k, r in best.items() if r.grade == GradeBand.IN_PROGRESS}

    needs: dict[str, _Need] = {}
    notes: list[str] = []
    issues: list[str] = []

    def add_need(course: str, reason: str, group: str | None = None) -> None:
        canon = catalog.canonical(course)
        if canon in have:
            return
        if course not in catalog.courses and canon not in catalog.courses:
            issues.append(f"{course} isn't in our course list yet; ask your advisor how to plan it")
            return
        key = course if course in catalog.courses else canon
        need = needs.setdefault(key, _Need(key, [], []))
        if reason not in need.reasons:
            need.reasons.append(reason)
        if group and group not in need.groups:
            need.groups.append(group)

    for group in result.flat():
        _collect_group_needs(group, catalog, options, needs, add_need, notes)

    # Prerequisite closure: keep adding missing prerequisites until nothing new appears.
    changed = True
    while changed:
        changed = False
        for key in list(needs):
            course = catalog.courses[key]
            ctx = RuleContext(
                catalog=catalog,
                finished=best,
                finished_before=frozenset(have | {catalog.canonical(k) for k in needs}),
                standing=options.standing,
                milestones_met=frozenset(record.milestones_met),
            )
            outcome = evaluate(course.prereq_rule, ctx)
            if outcome.status == Status.NOT_MET:
                for missing in outcome.missing_courses:
                    if catalog.canonical(missing) not in {catalog.canonical(k) for k in needs}:
                        add_need(missing, f"Prerequisite for {key}")
                        changed = True

    plan = _schedule(needs, catalog, best, in_progress, record, options, issues)
    plan.notes.extend(notes)
    plan.notes.extend(result.notes)
    plan.relies_on_credit = any(r.source == RecordSource.CREDIT for r in record.courses) or bool(
        record.credits
    )
    return plan


_AddNeed = Callable[[str, str, str | None], None]


def _collect_group_needs(
    group: GroupAudit,
    catalog: Catalog,
    options: PlanOptions,
    needs: dict[str, _Need],
    add_need: _AddNeed,
    notes: list[str],
) -> None:
    if group.status != GroupStatus.INCOMPLETE:
        return
    for course in group.still_needed:
        add_need(course, f"Required for {group.name}", group.name)
    for code in group.milestones_needed:
        milestone = catalog.milestones.get(code)
        if milestone is None:
            notes.append(f"{code}: see the catalog for how to meet this requirement")
            continue
        courses = sorted(k for k in milestone.satisfying_courses if k in catalog.courses)
        if courses:
            add_need(courses[0], f"Meets the {milestone.name} requirement", group.name)
        notes.append(f"{milestone.name}: {milestone.how_to_satisfy}")
    if group.rule == RuleKind.ALL_OF or group.remaining_count <= 0 or group.children:
        return
    picks, short = _pick_electives(group, catalog, options, needs)
    if group.rule == RuleKind.CHOOSE_UNITS:
        label = f"{group.remaining_count:g} more units needed"
    else:
        plural = "s" if group.remaining_count != 1 else ""
        label = f"{group.remaining_count:g} more course{plural} needed"
    for key in picks:
        add_need(key, f"Counts toward {group.name} ({label})", group.name)
    if short:
        notes.append(f"Not enough listed courses to finish {group.name}; ask your advisor")


def _pick_electives(
    group: GroupAudit, catalog: Catalog, options: PlanOptions, needs: dict[str, _Need]
) -> tuple[list[str], bool]:
    """Choose courses for what's left of a choose group. Returns (picks, still_short)."""
    interests = {w.lower() for w in options.interests}
    already = {catalog.canonical(k) for k in needs}

    def score(key: str) -> tuple[int, int, int, int, str]:
        course = catalog.courses[key]
        words = {w.lower().strip(",.:") for w in course.title.split()} | set(course.tags)
        matches_interest = bool(words & interests)
        prereqs = len(courses_in_rule(course.prereq_rule))
        reused = catalog.canonical(key) in already
        # Courses needing permission or special standing are picked only as a last resort.
        special = needs_action(course.prereq_rule)
        return (0 if reused else 1, int(special), 0 if matches_interest else 1, prereqs, key)

    picks: list[str] = []
    remaining = group.remaining_count
    for key in sorted(group.candidates, key=score):
        if remaining <= 0:
            break
        picks.append(key)
        remaining -= catalog.courses[key].units if group.rule == RuleKind.CHOOSE_UNITS else 1
    return picks, remaining > 0


def _schedule(
    needs: dict[str, _Need],
    catalog: Catalog,
    best: dict[str, CourseRecord],
    in_progress: set[str],
    record: StudentRecord,
    options: PlanOptions,
    issues: list[str],
) -> Plan:
    finished = best
    done_before: set[str] = set(in_progress)
    remaining = dict(needs)
    depth = _chain_depth(remaining, catalog)
    plan = Plan(terms=[], issues=issues)
    term = Term.parse(options.start_term)

    for _ in range(options.max_terms):
        if not remaining:
            break
        planned = PlannedTerm(term.code)
        same: set[str] = set()
        progress = True
        while progress:
            progress = False
            for key in sorted(remaining, key=lambda k: (-depth.get(k, 0), _level(k), k)):
                course = catalog.courses[key]
                if planned.units + course.units > options.units_max:
                    continue
                offered = course.offered_in(term)
                if offered is False:
                    continue
                ctx = RuleContext(
                    catalog=catalog,
                    finished=finished,
                    finished_before=frozenset(done_before),
                    same_term=frozenset(same | {catalog.canonical(key)}),
                    standing=options.standing,
                    milestones_met=frozenset(record.milestones_met),
                )
                pre = evaluate(course.prereq_rule, ctx)
                co = evaluate(course.coreq_rule, ctx)
                if pre.status == Status.NOT_MET or co.status == Status.NOT_MET:
                    continue
                need = remaining.pop(key)
                assumptions = [a for a in pre.assumes + co.assumes if "same term" not in a]
                if pre.status == Status.NEEDS_ACTION:
                    assumptions.extend(pre.reasons)
                planned.items.append(
                    PlanItem(
                        course=key,
                        title=course.title,
                        units=course.units,
                        reason=_reason(need, remaining, catalog),
                        groups=need.groups,
                        assumptions=assumptions,
                        offering_unknown=offered is None,
                    )
                )
                same.add(catalog.canonical(key))
                progress = True
                break
        if planned.items:
            plan.terms.append(planned)
            if planned.units < options.units_min and remaining:
                plan.notes.append(
                    f"{term}: only {planned.units:g} units fit because of prerequisites or "
                    "course offerings"
                )
        done_before |= {catalog.canonical(i.course) for i in planned.items}
        term = term.next_regular()

    for key in sorted(remaining):
        plan.issues.append(
            f"Couldn't place {key} within {options.max_terms} terms: check its prerequisites "
            "and when it's offered with your advisor"
        )
    return plan


def _reason(need: _Need, remaining: dict[str, _Need], catalog: Catalog) -> str:
    text = need.reasons[0]
    unlocks = sorted(
        key
        for key in remaining
        if need.course
        in {catalog.canonical(c) for c in courses_in_rule(catalog.courses[key].prereq_rule)}
        or need.course in courses_in_rule(catalog.courses[key].prereq_rule)
    )
    if unlocks and not text.startswith("Prerequisite"):
        text += f"; needed before {', '.join(unlocks[:2])}"
    return text


def _chain_depth(needs: dict[str, _Need], catalog: Catalog) -> dict[str, int]:
    """How many planned courses depend on each course, directly or indirectly (longest chain)."""
    dependents: dict[str, set[str]] = {k: set() for k in needs}
    canon_to_key = {catalog.canonical(k): k for k in needs}
    for key in needs:
        for pre in courses_in_rule(catalog.courses[key].prereq_rule):
            pk = canon_to_key.get(catalog.canonical(pre))
            if pk and pk != key:
                dependents[pk].add(key)
    memo: dict[str, int] = {}

    def depth(key: str, seen: frozenset[str]) -> int:
        if key in memo:
            return memo[key]
        if key in seen:
            return 0
        value = max((1 + depth(d, seen | {key}) for d in dependents[key]), default=0)
        memo[key] = value
        return value

    return {k: depth(k, frozenset()) for k in needs}


def _level(key: str) -> int:
    return number_value(split_key(key)[1]) or 0
