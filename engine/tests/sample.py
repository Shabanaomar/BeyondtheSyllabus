"""A small, fictional catalog for engine tests ("Sample State"). Not real university data."""

from __future__ import annotations

from bts_engine.models import (
    Catalog,
    Course,
    CourseOption,
    GradeBand,
    Milestone,
    MilestoneOption,
    Offering,
    Overlap,
    PatternOption,
    Program,
    RequirementGroup,
    RuleKind,
)

C = GradeBand.C_OR_BETTER


def course(
    key: str,
    units: float = 3,
    prereq: dict[str, object] | None = None,
    offered: Offering = Offering.BOTH,
    title: str | None = None,
    coreq: dict[str, object] | None = None,
    tags: frozenset[str] = frozenset(),
) -> Course:
    return Course(
        key=key,
        title=title or key,
        units_min=units,
        units_max=units,
        prereq_rule=prereq,
        coreq_rule=coreq,
        offered=offered,
        tags=tags,
    )


def sample_catalog() -> Catalog:
    courses = [
        course("MATH 75", 4),
        course("MATH 76", 4, {"course": "MATH 75", "min_grade_band": "c_or_better"}),
        course("MATH 77", 4, {"course": "MATH 76"}),
        course("PHYS 4A", 4, {"course": "MATH 75", "concurrent_ok": True}),
        course("PHYS 4AL", 1, {"course": "MATH 75", "concurrent_ok": True}),
        course("PHYS 4B", 4, {"all": [{"course": "PHYS 4A"}, {"course": "MATH 76"}]}),
        course("ME 26", 3, offered=Offering.FALL, title="Engineering Graphics"),
        course("ME 30", 3, {"course": "MATH 75"}, title="Statics"),
        course(
            "ME 112",
            3,
            {
                "all": [
                    {"course": "MATH 76", "min_grade_band": "c_or_better"},
                    {
                        "any": [{"course": "PHYS 4A"}, {"course": "PHYS 4AL"}],
                        "min_grade_band": "c_or_better",
                    },
                    {"course": "ME 26", "concurrent_ok": True},
                ]
            },
            offered=Offering.SPRING,
            title="Thermodynamics",
        ),
        course("ME 120", 3, {"course": "ME 112"}, title="Heat Transfer"),
        course("ME 145", 3, {"course": "ME 112"}, title="Energy Conversion"),
        course(
            "ME 156",
            3,
            {"course": "ME 30"},
            title="Robotics and Automation",
            tags=frozenset({"robotics"}),
        ),
        course("ME 159", 3, title="Renewable Energy Systems", tags=frozenset({"energy"})),
        course("ME 180", 3, {"permission": "instructor"}, title="Special Topics"),
        course("ENGL 1", 3, title="Composition"),
        course("PHIL 1", 3, title="Critical Thinking"),
        course("ENGL 160W", 3, {"course": "ENGL 1"}, title="Technical Writing"),
        course("ME 20", 3, offered=Offering.FALL, title="Engineering Graphics (old number)"),
    ]
    return Catalog(
        courses={c.key: c for c in courses},
        milestones={
            "SS-UDW": Milestone(
                "SS-UDW",
                "Upper-division writing",
                "Pass ENGL 160W or the writing exam",
                frozenset({"ENGL 160W"}),
                can_be_met_by_exam=True,
            )
        },
        equivalents=[("ME 20", "ME 26")],
    )


def sample_program() -> Program:
    core = RequirementGroup(
        id="core",
        name="Major core",
        rule=RuleKind.ALL_OF,
        options=tuple(
            CourseOption(k) for k in ["MATH 75", "MATH 76", "PHYS 4A", "ME 26", "ME 112", "ME 120"]
        ),
        min_grade=C,
        advisory_checks=({"kind": "gpa", "value": 2.0, "scope": "major"},),
    )
    electives = RequirementGroup(
        id="electives",
        name="Technical electives",
        rule=RuleKind.CHOOSE_UNITS,
        count=6,
        options=(PatternOption("ME", 140, 199),),
    )
    writing = RequirementGroup(
        id="writing",
        name="Upper-division writing",
        rule=RuleKind.ALL_OF,
        options=(MilestoneOption("SS-UDW"),),
        level="university",
    )
    ge = RequirementGroup(
        id="ge",
        name="GE Critical thinking",
        rule=RuleKind.CHOOSE_COURSES,
        count=1,
        options=(CourseOption("ENGL 1"), CourseOption("PHIL 1")),
        overlap=Overlap(default="shared"),
        level="university",
    )
    return Program(
        school="sample-state",
        major_code="BS-ME",
        name="Mechanical Engineering",
        catalog_year="2026-27",
        total_units=None,
        groups=(core, electives, writing, ge),
    )
