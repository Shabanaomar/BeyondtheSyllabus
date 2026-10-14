from __future__ import annotations

from datetime import time

from sample import sample_catalog

from bts_engine.models import (
    CourseRecord,
    GradeBand,
    Meeting,
    Section,
    StudentRecord,
    TimeBlock,
    Weekday,
)
from bts_engine.schedule import TimePreferences, best_combination, check_sections

MW = frozenset({Weekday.MON, Weekday.WED})
TTH = frozenset({Weekday.TUE, Weekday.THU})


def sec(course: str, code: str, days: frozenset[Weekday], start: int, end: int) -> Section:
    return Section(course, code, (Meeting(days, time(start), time(end)),))


WORK = [TimeBlock(Weekday.MON, time(13), time(17)), TimeBlock(Weekday.WED, time(13), time(17))]
DONE = StudentRecord(courses=[CourseRecord("MATH 75", GradeBand.C_OR_BETTER)])


def test_clashes_with_work_and_between_sections() -> None:
    sections = [
        sec("MATH 76", "01", MW, 14, 15),  # during work
        sec("PHYS 4A", "01", TTH, 9, 11),
        sec("ME 30", "02", TTH, 10, 12),  # overlaps PHYS 4A
    ]
    result = check_sections(sections, WORK, "2027SP", sample_catalog(), DONE)
    messages = [c.message for c in result.clashes]
    assert "MATH 76 (01) overlaps your work Mon 13:00-17:00" in messages
    assert "PHYS 4A (01) and ME 30 (02) overlap" in messages
    assert not result.passed
    assert result.units == 11


def test_prerequisites_offerings_and_unknown_courses() -> None:
    sections = [
        sec("ME 112", "01", MW, 9, 10),  # missing MATH 76 etc., and spring-only
        sec("ME 26", "01", TTH, 9, 10),  # fall-only
        sec("ART 1", "01", TTH, 15, 16),
    ]
    result = check_sections(sections, [], "2027FA", sample_catalog(), DONE, units_max=5)
    assert any(p.startswith("ME 112: ") for p in result.prerequisite_problems)
    assert any("ME 112 is usually offered in spring only" in w for w in result.warnings)
    assert any("ART 1 isn't in our course list" in w for w in result.warnings)
    assert any("6 units is over your limit of 5" in w for w in result.warnings)


def test_in_progress_and_permission_show_as_warnings() -> None:
    record = StudentRecord(courses=[CourseRecord("MATH 75", GradeBand.IN_PROGRESS)])
    sections = [sec("MATH 76", "01", MW, 9, 10), sec("ME 180", "01", TTH, 9, 10)]
    result = check_sections(sections, [], "2027SP", sample_catalog(), record)
    assert result.passed
    assert "MATH 76: Assumes you pass MATH 75" in result.warnings
    assert any("Needs instructor permission" in w for w in result.warnings)


def test_best_combination_avoids_clashes_and_prefers_preferred_hours() -> None:
    options = {
        "MATH 76": [
            sec("MATH 76", "early", MW, 8, 9),
            sec("MATH 76", "work", MW, 14, 15),
            sec("MATH 76", "late", MW, 10, 11),
        ],
        "PHYS 4A": [sec("PHYS 4A", "a", TTH, 10, 12)],
        "ME 30": [sec("ME 30", "a", TTH, 11, 12)],  # always clashes with PHYS 4A
    }
    chosen, left_out = best_combination(options, WORK, TimePreferences(avoid_before=time(9)))
    codes = {(s.course, s.code) for s in chosen}
    assert ("MATH 76", "late") in codes
    assert len(chosen) == 2
    assert len(left_out) == 1 and left_out[0] in {"PHYS 4A", "ME 30"}


def test_best_combination_with_nothing_fitting() -> None:
    options = {"MATH 76": [sec("MATH 76", "w", MW, 14, 15)]}
    chosen, left_out = best_combination(options, WORK)
    assert chosen == [] and left_out == ["MATH 76"]


def test_avoid_after_preference() -> None:
    options = {"MATH 76": [sec("MATH 76", "eve", TTH, 18, 20), sec("MATH 76", "day", TTH, 9, 10)]}
    chosen, _ = best_combination(options, [], TimePreferences(avoid_after=time(17)))
    assert chosen[0].code == "day"
