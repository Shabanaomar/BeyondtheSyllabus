from __future__ import annotations

import pytest
from sample import sample_catalog

from bts_engine.models import (
    CourseRecord,
    GradeBand,
    PatternOption,
    RecordSource,
    StudentRecord,
    Term,
    course_key,
    number_value,
)
from bts_engine.rules import (
    RuleContext,
    Status,
    best_records,
    courses_in_rule,
    evaluate,
    grade_meets,
)

G = GradeBand


@pytest.mark.parametrize(
    ("grade", "minimum", "ok"),
    [
        (G.C_OR_BETTER, None, True),
        (G.PASSED_BELOW_C, None, True),
        (G.PASS_NO_PASS, None, True),
        (G.IN_PROGRESS, None, False),
        (G.C_OR_BETTER, G.C_OR_BETTER, True),
        (G.PASSED_BELOW_C, G.C_OR_BETTER, False),
        (G.PASS_NO_PASS, G.C_OR_BETTER, False),
        (G.PASSED_BELOW_C, G.PASSED_BELOW_C, True),
        (G.PASS_NO_PASS, G.PASSED_BELOW_C, False),
        (G.PASS_NO_PASS, G.PASS_NO_PASS, True),
    ],
)
def test_grade_bands(grade: GradeBand, minimum: GradeBand | None, ok: bool) -> None:
    assert grade_meets(grade, minimum) is ok


def ctx(records: list[CourseRecord], **kw: object) -> RuleContext:
    catalog = sample_catalog()
    record = StudentRecord(courses=records)
    return RuleContext(catalog=catalog, finished=best_records(record, catalog), **kw)  # type: ignore[arg-type]


ME112 = sample_catalog().courses["ME 112"].prereq_rule


def test_no_rule_is_met() -> None:
    assert evaluate(None, ctx([])).status == Status.MET


def test_all_and_any_with_inherited_minimum_grade() -> None:
    records = [
        CourseRecord("MATH 76", G.C_OR_BETTER),
        CourseRecord("PHYS 4AL", G.C_OR_BETTER),
        CourseRecord("ME 26", G.C_OR_BETTER),
    ]
    assert evaluate(ME112, ctx(records)).status == Status.MET
    # PHYS 4AL with C- fails the C minimum inherited from the "any" node.
    records[1] = CourseRecord("PHYS 4AL", G.PASSED_BELOW_C)
    result = evaluate(ME112, ctx(records))
    assert result.status == Status.NOT_MET
    assert result.missing_courses == ["PHYS 4A"]


def test_concurrent_course_counts_only_in_the_same_term() -> None:
    records = [CourseRecord("MATH 76", G.C_OR_BETTER), CourseRecord("PHYS 4A", G.C_OR_BETTER)]
    assert evaluate(ME112, ctx(records)).status == Status.NOT_MET
    result = evaluate(ME112, ctx(records, same_term=frozenset({"ME 20"})))
    # ME 20 is the old number of ME 26, so taking it the same term counts.
    assert result.status == Status.MET
    assert any("same term" in a for a in result.assumes)


def test_course_finished_before_the_term_is_an_assumption() -> None:
    records = [CourseRecord("MATH 75", G.IN_PROGRESS)]
    rule = {"course": "MATH 75", "min_grade_band": "c_or_better"}
    assert evaluate(rule, ctx(records)).status == Status.NOT_MET
    result = evaluate(rule, ctx(records, finished_before=frozenset({"MATH 75"})))
    assert result.status == Status.MET
    assert result.assumes == ["Assumes you pass MATH 75"]


def test_credit_is_counted_but_flagged() -> None:
    records = [CourseRecord("MATH 75", G.PASS_NO_PASS, RecordSource.CREDIT)]
    result = evaluate({"course": "MATH 75"}, ctx(records))
    assert result.status == Status.MET
    assert "confirm this credit" in result.assumes[0]


def test_permission_and_unparsed_text_need_action() -> None:
    assert evaluate({"permission": "instructor"}, ctx([])).status == Status.NEEDS_ACTION
    result = evaluate({"text": "consent of the chair"}, ctx([]))
    assert result.status == Status.NEEDS_ACTION
    assert "advisor" in result.reasons[0]


@pytest.mark.parametrize(
    ("have", "status"),
    [("senior", Status.MET), ("sophomore", Status.NOT_MET), (None, Status.NEEDS_ACTION)],
)
def test_standing(have: str | None, status: Status) -> None:
    assert evaluate({"standing": "junior"}, ctx([], standing=have)).status == status


def test_milestone_rule() -> None:
    assert evaluate({"milestone": "X"}, ctx([])).status == Status.NOT_MET
    assert evaluate({"milestone": "X"}, ctx([], milestones_met=frozenset({"X"}))).status == (
        Status.MET
    )


def test_any_prefers_options_without_assumptions_and_needs_action_over_not_met() -> None:
    records = [
        CourseRecord("PHYS 4A", G.C_OR_BETTER, RecordSource.CREDIT),
        CourseRecord("PHYS 4AL", G.C_OR_BETTER),
    ]
    result = evaluate({"any": [{"course": "PHYS 4A"}, {"course": "PHYS 4AL"}]}, ctx(records))
    assert result.status == Status.MET and result.assumes == []
    either = {"any": [{"course": "MATH 99"}, {"permission": "department"}]}
    assert evaluate(either, ctx([])).status == Status.NEEDS_ACTION


def test_any_suggests_the_cheapest_missing_option() -> None:
    rule = {
        "any": [
            {"all": [{"course": "MATH 76"}, {"course": "MATH 77"}]},
            {"course": "PHYS 4B"},
        ]
    }
    result = evaluate(rule, ctx([]))
    assert result.status == Status.NOT_MET
    assert result.missing_courses == ["PHYS 4B"]


def test_failing_grade_gets_a_specific_reason() -> None:
    result = evaluate(
        {"course": "MATH 75", "min_grade_band": "c_or_better"},
        ctx([CourseRecord("MATH 75", G.PASSED_BELOW_C)]),
    )
    assert "needs a C or better" in result.reasons[0]


def test_best_record_wins_across_equivalents() -> None:
    catalog = sample_catalog()
    record = StudentRecord(
        courses=[CourseRecord("ME 20", G.PASSED_BELOW_C), CourseRecord("ME 26", G.C_OR_BETTER)]
    )
    best = best_records(record, catalog)
    assert list(best) == ["ME 20"]  # canonical key is the alphabetically first of the pair
    assert best["ME 20"].grade == G.C_OR_BETTER


def test_courses_in_rule() -> None:
    assert courses_in_rule(ME112) == {"MATH 76", "PHYS 4A", "PHYS 4AL", "ME 26"}
    assert courses_in_rule(None) == set()


def test_terms_parse_order_and_advance() -> None:
    assert Term.parse("2027SP") < Term.parse("2027FA") < Term.parse("2028SP")
    assert Term.parse("2026FA").next_regular().code == "2027SP"
    assert Term.parse("2027SP").next_regular().code == "2027FA"
    assert str(Term.parse("2027SU")) == "Summer 2027"
    with pytest.raises(ValueError, match="Not a term code"):
        Term.parse("Spring 2027")


def test_course_keys_and_patterns() -> None:
    assert course_key(" mec eng ", "c85") == "MEC ENG C85"
    assert number_value("C100") == 100
    assert number_value("W") is None
    pattern = PatternOption("ME", 140, 199, frozenset({"ME 180"}))
    assert pattern.matches("ME 156")
    assert not pattern.matches("ME 180")
    assert not pattern.matches("ME 112")
    assert not pattern.matches("CE 156")
