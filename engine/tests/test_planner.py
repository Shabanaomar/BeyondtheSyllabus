from __future__ import annotations

from dataclasses import replace

from sample import sample_catalog, sample_program

from bts_engine.checker import ProblemKind, check_plan
from bts_engine.models import (
    CourseOption,
    CourseRecord,
    GradeBand,
    Program,
    RecordSource,
    RequirementGroup,
    RuleKind,
    StudentRecord,
)
from bts_engine.planner import PlanOptions, build_plan

G = GradeBand


def plan_for(records: list[CourseRecord], **kw: object):  # type: ignore[no-untyped-def]
    options = PlanOptions(start_term="2027SP", **kw)  # type: ignore[arg-type]
    return build_plan(sample_program(), sample_catalog(), StudentRecord(courses=records), options)


def as_terms(plan) -> list[tuple[str, list[str]]]:  # type: ignore[no-untyped-def]
    return [(t.term, [i.course for i in t.items]) for t in plan.terms]


def test_new_student_plan_respects_prerequisites_offerings_and_passes_the_checker() -> None:
    plan = plan_for([], units_max=12)
    placed = plan.placed()
    order = {t.term: n for n, t in enumerate(plan.terms)}
    # Prerequisite chains are in order.
    assert order[placed["MATH 75"]] < order[placed["MATH 76"]] < order[placed["ME 112"]]
    assert order[placed["ME 112"]] < order[placed["ME 120"]]
    # ME 26 is fall-only and ME 112 spring-only.
    assert placed["ME 26"].endswith("FA") and placed["ME 112"].endswith("SP")
    # Unit limit respected; nothing left over.
    assert all(t.units <= 12 for t in plan.terms)
    assert plan.issues == []
    # The writing milestone is met by planning its course (plus that course's prerequisite).
    assert placed["ENGL 1"] and placed["ENGL 160W"]
    assert any("Upper-division writing: Pass ENGL 160W" in n for n in plan.notes)
    # A course that needs instructor permission isn't auto-picked as an elective.
    assert "ME 180" not in placed
    check = check_plan(sample_program(), sample_catalog(), StudentRecord(), as_terms(plan), 12)
    assert check.passed, check.problems


def test_reasons_explain_each_course() -> None:
    plan = plan_for([])
    items = {i.course: i for t in plan.terms for i in t.items}
    assert items["MATH 76"].reason.startswith("Required for Major core; needed before")
    assert items["ME 145"].reason.startswith("Counts toward Technical electives")


def test_interests_steer_elective_picks_and_prerequisites_are_added() -> None:
    plan = plan_for([], interests=("robotics",))
    items = {i.course: i for t in plan.terms for i in t.items}
    assert "ME 156" in items
    # ME 156 needs ME 30, which isn't required, so the planner adds it.
    assert items["ME 30"].reason == "Prerequisite for ME 156"


def test_finished_and_in_progress_courses_are_not_planned_again() -> None:
    records = [
        CourseRecord("MATH 75", G.C_OR_BETTER),
        CourseRecord("MATH 76", G.IN_PROGRESS),
        CourseRecord("PHYS 4A", G.C_OR_BETTER, RecordSource.CREDIT),
    ]
    plan = plan_for(records)
    placed = plan.placed()
    assert "MATH 75" not in placed and "MATH 76" not in placed and "PHYS 4A" not in placed
    assert plan.relies_on_credit
    me112 = next(i for t in plan.terms for i in t.items if i.course == "ME 112")
    assert "Assumes you pass MATH 76" in me112.assumptions


def test_permission_courses_carry_the_warning() -> None:
    catalog = sample_catalog()
    group = RequirementGroup("x", "Topics", RuleKind.ALL_OF, options=(CourseOption("ME 180"),))
    program = Program("s", "X", "X", "2026-27", None, (group,))
    plan = build_plan(program, catalog, StudentRecord(), PlanOptions(start_term="2027SP"))
    item = plan.terms[0].items[0]
    assert "Needs instructor permission" in item.assumptions[0]


def test_impossible_courses_are_reported_not_silently_dropped() -> None:
    catalog = sample_catalog()
    group = RequirementGroup(
        "x", "Odd", RuleKind.ALL_OF, options=(CourseOption("ME 112"), CourseOption("NOPE 1"))
    )
    program = Program("s", "X", "X", "2026-27", None, (group,))
    plan = build_plan(
        program, catalog, StudentRecord(), PlanOptions(start_term="2027SP", max_terms=1)
    )
    assert any("NOPE 1 isn't in our course list" in i for i in plan.issues)
    assert any("Couldn't place ME 112" in i for i in plan.issues)


def test_light_terms_are_explained() -> None:
    plan = plan_for([], units_min=15, units_max=16)
    assert any("only" in n and "units fit" in n for n in plan.notes)


def test_checker_finds_each_kind_of_problem() -> None:
    catalog = sample_catalog()
    program = sample_program()
    record = StudentRecord(courses=[CourseRecord("MATH 75", G.C_OR_BETTER)])
    terms = [
        ("2027SP", ["ME 112", "ME 26", "MATH 75"]),  # ME 112 too early; ME 26 fall-only
        ("2027FA", ["MATH 76", "MATH 76", "PHYS 4A", "ME 120", "ME 145", "ME 159", "XYZ 1"]),
    ]
    result = check_plan(program, catalog, record, terms, units_max=12)
    kinds = {p.kind for p in result.problems}
    assert {
        ProblemKind.PREREQUISITE,
        ProblemKind.NOT_OFFERED,
        ProblemKind.ALREADY_TAKEN,
        ProblemKind.DUPLICATE,
        ProblemKind.OVER_UNITS,
        ProblemKind.UNKNOWN_COURSE,
        ProblemKind.UNFINISHED_REQUIREMENT,
    } <= kinds
    assert not result.passed


def test_checker_passes_a_complete_valid_plan_and_warns_on_unknowns() -> None:
    catalog = sample_catalog()
    catalog.courses["ME 159"] = replace(catalog.courses["ME 159"], offered="unknown")  # type: ignore[arg-type]
    record = StudentRecord(courses=[CourseRecord("ENGL 1", G.C_OR_BETTER)])
    terms = [
        ("2026FA", ["MATH 75", "ME 26", "ENGL 160W"]),
        ("2027SP", ["MATH 76", "PHYS 4A"]),
        ("2028SP", ["ME 112", "ME 159"]),
        ("2028FA", ["ME 120", "ME 145"]),
    ]
    result = check_plan(sample_program(), catalog, record, terms, units_max=16)
    assert result.passed, result.problems
    assert any("check it's offered" in w for w in result.warnings)
    assert any("GPA" in w for w in result.warnings)
