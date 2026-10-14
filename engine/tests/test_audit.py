from __future__ import annotations

from dataclasses import replace

from sample import sample_catalog, sample_program

from bts_engine.audit import GroupStatus, audit
from bts_engine.models import (
    CourseOption,
    CourseRecord,
    GradeBand,
    Overlap,
    PatternOption,
    Program,
    RecordSource,
    RequirementCredit,
    RequirementGroup,
    RuleKind,
    StudentRecord,
)

G = GradeBand
CORE = ["MATH 75", "MATH 76", "PHYS 4A", "ME 26", "ME 112", "ME 120"]


def rec(*keys: str, grade: GradeBand = G.C_OR_BETTER) -> list[CourseRecord]:
    return [CourseRecord(k, grade) for k in keys]


def run(records: list[CourseRecord], **kw: object):  # type: ignore[no-untyped-def]
    return audit(sample_program(), sample_catalog(), StudentRecord(courses=records, **kw))  # type: ignore[arg-type]


def test_new_student_needs_everything() -> None:
    result = run([])
    assert not result.complete
    core = result.find("core")
    assert core.status == GroupStatus.INCOMPLETE
    assert core.still_needed == CORE
    electives = result.find("electives")
    assert electives.remaining_count == 6
    assert "ME 156" in electives.candidates and "ME 112" not in electives.candidates
    assert result.find("writing").milestones_needed == ["SS-UDW"]
    assert "Requires a 2.0 GPA in major courses: check with your advisor" in core.notes


def test_complete_record_finishes_the_degree() -> None:
    result = run(rec(*CORE, "ME 145", "ME 159", "ENGL 1", "ENGL 160W"))
    assert result.complete
    assert result.units_earned == 33  # 21 core + 4 courses x 3


def test_minimum_grade_is_enforced_with_a_reason() -> None:
    records = rec(*CORE)
    records[1] = CourseRecord("MATH 76", G.PASSED_BELOW_C)
    core = run(records).find("core")
    assert core.status == GroupStatus.INCOMPLETE
    assert core.still_needed == ["MATH 76"]
    assert any("MATH 76 doesn't count here: needs a C or better" in n for n in core.notes)


def test_in_progress_courses_make_a_group_in_progress_not_complete() -> None:
    records = [*rec(*CORE[:-1]), CourseRecord("ME 120", G.IN_PROGRESS)]
    result = run(records)
    assert result.find("core").status == GroupStatus.IN_PROGRESS
    assert result.units_in_progress == 3


def test_equivalent_course_counts_for_its_new_number() -> None:
    records = rec("MATH 75", "MATH 76", "PHYS 4A", "ME 20", "ME 112", "ME 120")
    assert run(records).find("core").status == GroupStatus.COMPLETE


def test_course_counts_once_unless_overlap_allows() -> None:
    catalog = sample_catalog()
    a = RequirementGroup("a", "A", RuleKind.ALL_OF, options=(CourseOption("ME 159"),))
    b = RequirementGroup(
        "b", "B", RuleKind.CHOOSE_COURSES, 1, options=(PatternOption("ME", 150, 160),)
    )
    program = Program("s", "X", "X", "2026-27", None, (a, b))
    result = audit(program, catalog, StudentRecord(courses=rec("ME 159")))
    assert result.find("a").status == GroupStatus.COMPLETE
    assert result.find("b").status == GroupStatus.INCOMPLETE  # ME 159 already used by A

    shared = replace(b, overlap=Overlap(may_share_with=frozenset({"a"})))
    program = Program("s", "X", "X", "2026-27", None, (a, shared))
    result = audit(program, catalog, StudentRecord(courses=rec("ME 159")))
    assert result.find("b").status == GroupStatus.COMPLETE


def test_specific_requirements_are_filled_before_flexible_ones() -> None:
    catalog = sample_catalog()
    flexible = RequirementGroup(
        "flex", "Flex", RuleKind.CHOOSE_COURSES, 1, options=(PatternOption("ME", 100, 199),)
    )
    specific = RequirementGroup("spec", "Spec", RuleKind.ALL_OF, options=(CourseOption("ME 145"),))
    program = Program("s", "X", "X", "2026-27", None, (flexible, specific))
    result = audit(program, catalog, StudentRecord(courses=rec("ME 145", "ME 156")))
    assert result.complete


def test_reported_credit_completes_a_group_and_is_flagged() -> None:
    result = run([], credits=[RequirementCredit(group_id="ge", note="AP English")])
    ge = result.find("ge")
    assert ge.status == GroupStatus.COMPLETE
    assert "AP English" in ge.notes[0] and "confirm" in ge.notes[0]


def test_course_credit_is_flagged() -> None:
    records = [CourseRecord("ENGL 1", G.PASS_NO_PASS, RecordSource.CREDIT)]
    ge = run(records).find("ge")
    assert ge.status == GroupStatus.COMPLETE
    assert any("confirm" in n for n in ge.notes)


def test_milestones_by_course_by_record_and_by_credit() -> None:
    assert run(rec("ENGL 1", "ENGL 160W")).find("writing").status == GroupStatus.COMPLETE
    assert run([], milestones_met={"SS-UDW"}).find("writing").status == GroupStatus.COMPLETE
    by_credit = run([], credits=[RequirementCredit(milestone="SS-UDW")]).find("writing")
    assert by_credit.status == GroupStatus.COMPLETE
    assert any("confirm" in n for n in by_credit.notes)


def test_units_electives_and_total_units_note() -> None:
    result = run(rec("ME 145"))
    assert result.find("electives").remaining_count == 3
    program = replace(sample_program(), total_units=120)
    result = audit(program, sample_catalog(), StudentRecord(courses=rec("ME 145")))
    assert result.notes == ["117 more units needed to reach the 120-unit total"]


def test_nested_groups() -> None:
    catalog = sample_catalog()
    math = RequirementGroup("m", "Math", RuleKind.ALL_OF, options=(CourseOption("MATH 75"),))
    phil = RequirementGroup("p", "Phil", RuleKind.ALL_OF, options=(CourseOption("PHIL 1"),))
    either = RequirementGroup("e", "Either", RuleKind.CHOOSE_COURSES, 1, children=(math, phil))
    both = RequirementGroup("b", "Both", RuleKind.ALL_OF, children=(math, phil))
    program = Program("s", "X", "X", "2026-27", None, (either,))
    assert audit(program, catalog, StudentRecord(courses=rec("PHIL 1"))).complete
    program = Program("s", "X", "X", "2026-27", None, (both,))
    result = audit(program, catalog, StudentRecord(courses=rec("PHIL 1")))
    assert result.find("b").status == GroupStatus.INCOMPLETE
    program = Program("s", "X", "X", "2026-27", None, (either,))
    in_progress = audit(
        program, catalog, StudentRecord(courses=[CourseRecord("PHIL 1", G.IN_PROGRESS)])
    )
    assert in_progress.find("e").status == GroupStatus.IN_PROGRESS
    assert [g.id for g in in_progress.flat()] == ["e", "m", "p"]
