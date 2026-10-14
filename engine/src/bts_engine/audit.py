"""Degree audit: which requirements are met, which courses count where, and what's left.

How courses are assigned to requirements:

* Specific requirements are filled first ("all of" lists), then "choose N courses", then
  "choose N units", and within each kind the group with the fewest possible courses goes first.
  That keeps flexible elective groups from using up a course a required group needs.
* A course counts toward one group only, unless the overlap rules allow sharing: a group marked
  "shared", or two groups that list each other in may_share_with.
* Courses in progress count, but the group is reported as "in progress", not complete.
* Credit the student reports is counted and always flagged "confirm this credit appears on your
  record". GPA rules and other advisory checks are never marked met.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .models import (
    Catalog,
    CourseOption,
    CourseRecord,
    GradeBand,
    MilestoneOption,
    PatternOption,
    Program,
    RecordSource,
    RequirementGroup,
    RuleKind,
    StudentRecord,
)
from .rules import best_records, grade_meets


class GroupStatus(StrEnum):
    COMPLETE = "complete"
    IN_PROGRESS = "in_progress"
    INCOMPLETE = "incomplete"


@dataclass
class Applied:
    course: str
    units: float
    in_progress: bool = False
    credit: bool = False


@dataclass
class GroupAudit:
    id: str
    name: str
    rule: RuleKind
    status: GroupStatus
    applied: list[Applied] = field(default_factory=list)
    # all_of: the specific courses still needed.
    still_needed: list[str] = field(default_factory=list)
    # choose_courses: how many more courses; choose_units: how many more units.
    remaining_count: float = 0
    # Courses (from the catalog) that could fill what's left, for choose groups.
    candidates: list[str] = field(default_factory=list)
    milestones_needed: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    children: list[GroupAudit] = field(default_factory=list)
    source_url: str | None = None


@dataclass
class AuditResult:
    program: Program
    groups: list[GroupAudit]
    units_earned: float
    units_in_progress: float
    notes: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return all(g.status == GroupStatus.COMPLETE for g in self.groups)

    def flat(self) -> list[GroupAudit]:
        out: list[GroupAudit] = []
        stack = list(reversed(self.groups))
        while stack:
            g = stack.pop()
            out.append(g)
            stack.extend(reversed(g.children))
        return out

    def find(self, group_id: str) -> GroupAudit:
        for g in self.flat():
            if g.id == group_id:
                return g
        raise KeyError(group_id)


_RULE_ORDER = {RuleKind.ALL_OF: 0, RuleKind.CHOOSE_COURSES: 1, RuleKind.CHOOSE_UNITS: 2}


class _Allocator:
    def __init__(self, program: Program, catalog: Catalog, record: StudentRecord) -> None:
        self.program = program
        self.catalog = catalog
        self.record = record
        self.best = best_records(record, catalog)
        self.groups = {g.id: g for g in program.all_groups()}
        # canonical course key -> ids of groups it has been applied to
        self.used: dict[str, list[str]] = {}
        self.credited_groups = {c.group_id for c in record.credits if c.group_id}
        self.credited_milestones = {c.milestone for c in record.credits if c.milestone}

    # -- matching -------------------------------------------------------------------------------

    def option_matches(self, group: RequirementGroup, key: str) -> bool:
        canon = self.catalog.canonical(key)
        for option in group.options:
            if isinstance(option, CourseOption) and self.catalog.canonical(option.course) == canon:
                return True
            if isinstance(option, PatternOption) and (
                option.matches(key)
                or any(
                    option.matches(k)
                    for k in self.catalog.courses
                    if self.catalog.canonical(k) == canon
                )
            ):
                return True
        return False

    def can_use(self, group: RequirementGroup, canon: str) -> bool:
        for other_id in self.used.get(canon, []):
            other = self.groups[other_id]
            if group.overlap.default == "shared" or other.overlap.default == "shared":
                continue
            if other_id in group.overlap.may_share_with or group.id in other.overlap.may_share_with:
                continue
            return False
        return True

    def use(self, group: RequirementGroup, canon: str) -> None:
        self.used.setdefault(canon, []).append(group.id)

    def units_of(self, key: str) -> float:
        course = self.catalog.courses.get(key) or next(
            (c for k, c in self.catalog.courses.items() if self.catalog.same_course(k, key)), None
        )
        return course.units if course else 0.0

    def eligible(
        self, group: RequirementGroup, record: CourseRecord
    ) -> tuple[bool, bool, str | None]:
        """(counts, in_progress, note) for one record against one group's grade minimum."""
        if record.grade == GradeBand.IN_PROGRESS:
            return True, True, None
        if grade_meets(record.grade, group.min_grade):
            return True, False, None
        need = "a C or better" if group.min_grade == GradeBand.C_OR_BETTER else "a letter grade"
        return False, False, f"{record.course} doesn't count here: needs {need}"

    def catalog_candidates(self, group: RequirementGroup) -> list[str]:
        keys = [k for k in sorted(self.catalog.courses) if self.option_matches(group, k)]
        taken = set(self.best)
        return [k for k in keys if self.catalog.canonical(k) not in taken]

    # -- auditing -------------------------------------------------------------------------------

    def audit_leaf(self, group: RequirementGroup) -> GroupAudit:
        result = GroupAudit(
            group.id, group.name, group.rule, GroupStatus.INCOMPLETE, source_url=group.source_url
        )
        for check in group.advisory_checks:
            result.notes.append(_advisory_text(check))

        if group.id in self.credited_groups:
            note = next(c.note for c in self.record.credits if c.group_id == group.id)
            result.status = GroupStatus.COMPLETE
            result.notes.append(
                f"Counted from credit you reported{f' ({note})' if note else ''}: "
                "confirm this credit appears on your record"
            )
            return result

        if group.rule == RuleKind.ALL_OF:
            self._fill_all_of(group, result)
        else:
            self._fill_choose(group, result)

        if group.rule == RuleKind.ALL_OF:
            done = not result.still_needed and not result.milestones_needed
        else:
            done = result.remaining_count <= 0
        if done:
            any_progress = any(a.in_progress for a in result.applied)
            result.status = GroupStatus.IN_PROGRESS if any_progress else GroupStatus.COMPLETE
        if any(a.credit for a in result.applied):
            result.notes.append("Includes credit you reported: confirm it appears on your record")
        return result

    def _fill_all_of(self, group: RequirementGroup, result: GroupAudit) -> None:
        for option in group.options:
            if isinstance(option, MilestoneOption):
                if not self._milestone_met(option.milestone, result):
                    result.milestones_needed.append(option.milestone)
                continue
            if isinstance(option, PatternOption):
                # "All of" a pattern is unusual; treat it as one course from the pattern.
                matched = self._take_matching(group, result, limit_courses=1)
                if not matched:
                    result.still_needed.append(
                        f"{option.subject} {option.number_min}-{option.number_max}"
                    )
                continue
            canon = self.catalog.canonical(option.course)
            record = self.best.get(canon)
            if record is None:
                result.still_needed.append(option.course)
                continue
            counts, in_progress, note = self.eligible(group, record)
            if not counts:
                result.notes.append(note or "")
                result.still_needed.append(option.course)
                continue
            if not self.can_use(group, canon):
                result.notes.append(f"{option.course} already counts toward another requirement")
                result.still_needed.append(option.course)
                continue
            self.use(group, canon)
            result.applied.append(
                Applied(
                    option.course,
                    self.units_of(option.course),
                    in_progress,
                    record.source == RecordSource.CREDIT,
                )
            )

    def _fill_choose(self, group: RequirementGroup, result: GroupAudit) -> None:
        count = group.count or 0
        if group.rule == RuleKind.CHOOSE_COURSES:
            taken = self._take_matching(group, result, limit_courses=int(count))
            result.remaining_count = max(0.0, count - taken)
        else:
            units = self._take_matching(group, result, limit_units=count)
            result.remaining_count = max(0.0, count - units)
        for option in group.options:
            if isinstance(option, MilestoneOption) and self._milestone_met(
                option.milestone, result
            ):
                result.remaining_count = max(0.0, result.remaining_count - 1)
        if result.remaining_count > 0:
            result.candidates = self.catalog_candidates(group)

    def _take_matching(
        self,
        group: RequirementGroup,
        result: GroupAudit,
        limit_courses: int | None = None,
        limit_units: float | None = None,
    ) -> float:
        """Apply matching records; returns courses taken (count mode) or units (units mode)."""
        # Finished courses first, then in progress; alphabetical for stable results.
        ordered = sorted(
            self.best.items(), key=lambda kv: (kv[1].grade == GradeBand.IN_PROGRESS, kv[0])
        )
        taken_courses = 0
        taken_units = 0.0
        for canon, record in ordered:
            if limit_courses is not None and taken_courses >= limit_courses:
                break
            if limit_units is not None and taken_units >= limit_units:
                break
            if not self.option_matches(group, record.course):
                continue
            counts, in_progress, note = self.eligible(group, record)
            if not counts:
                if note:
                    result.notes.append(note)
                continue
            if not self.can_use(group, canon):
                continue
            self.use(group, canon)
            units = self.units_of(record.course)
            result.applied.append(
                Applied(record.course, units, in_progress, record.source == RecordSource.CREDIT)
            )
            taken_courses += 1
            taken_units += units
        return float(taken_courses) if limit_units is None else taken_units

    def _milestone_met(self, code: str, result: GroupAudit) -> bool:
        if code in self.record.milestones_met:
            return True
        if code in self.credited_milestones:
            result.notes.append(
                f"{code}: counted from credit you reported; confirm it on your record"
            )
            return True
        milestone = self.catalog.milestones.get(code)
        if milestone is None:
            return False
        for key in milestone.satisfying_courses:
            record = self.best.get(self.catalog.canonical(key))
            if record is None:
                continue
            if record.grade == GradeBand.IN_PROGRESS:
                # Counts, but the group can only be "in progress" until the course is done.
                result.applied.append(Applied(key, 0.0, in_progress=True))
                return True
            if grade_meets(record.grade, None):
                return True
        return False

    def audit_group(
        self, group: RequirementGroup, leaf_results: dict[str, GroupAudit]
    ) -> GroupAudit:
        if not group.children:
            return leaf_results[group.id]
        children = [self.audit_group(c, leaf_results) for c in group.children]
        own = leaf_results.get(group.id)
        result = own or GroupAudit(
            group.id, group.name, group.rule, GroupStatus.INCOMPLETE, source_url=group.source_url
        )
        result.children = children
        statuses = [c.status for c in children]
        if group.rule == RuleKind.ALL_OF:
            needed = len(children)
        else:
            needed = int(group.count or len(children))
        complete = sum(s == GroupStatus.COMPLETE for s in statuses)
        progressing = sum(s == GroupStatus.IN_PROGRESS for s in statuses)
        own_done = own is None or own.status != GroupStatus.INCOMPLETE
        if complete >= needed and own_done:
            result.status = GroupStatus.COMPLETE
        elif complete + progressing >= needed and own_done:
            result.status = GroupStatus.IN_PROGRESS
        else:
            result.status = GroupStatus.INCOMPLETE
            if group.rule != RuleKind.ALL_OF:
                result.remaining_count = max(0, needed - complete - progressing)
        return result


def audit(program: Program, catalog: Catalog, record: StudentRecord) -> AuditResult:
    alloc = _Allocator(program, catalog, record)
    leaves = [g for g in program.all_groups() if g.options or not g.children]
    leaves.sort(
        key=lambda g: (
            _RULE_ORDER[g.rule],
            len(alloc.catalog_candidates(g)) if g.rule != RuleKind.ALL_OF else len(g.options),
            g.id,
        )
    )
    leaf_results = {g.id: alloc.audit_leaf(g) for g in leaves}
    top = [alloc.audit_group(g, leaf_results) for g in program.groups]

    earned = 0.0
    in_progress = 0.0
    for rec in alloc.best.values():
        units = alloc.units_of(rec.course)
        if rec.grade == GradeBand.IN_PROGRESS:
            in_progress += units
        elif grade_meets(rec.grade, None):
            earned += units
    notes: list[str] = []
    if program.total_units and earned + in_progress < program.total_units:
        left = program.total_units - earned - in_progress
        notes.append(f"{left:g} more units needed to reach the {program.total_units:g}-unit total")
    return AuditResult(program, top, earned, in_progress, notes)


def _advisory_text(check: dict[str, object]) -> str:
    if check.get("kind") == "gpa":
        scope = check.get("scope")
        where = f" in {scope} courses" if scope else ""
        return f"Requires a {check.get('value')} GPA{where}: check with your advisor"
    return f"Check with your advisor: {check.get('text', check.get('kind', 'additional rule'))}"
