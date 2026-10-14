"""Parsers against saved copies of the real pages (fetched 2026-10-14; see docs/sources/)."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from bts_ingest.parsers import berkeley, fresno

FIXTURES = Path(__file__).parent / "fixtures"


def page(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_fresno_engineering_clubs() -> None:
    result = fresno.parse_engineering_clubs(page("fresno_engineering_clubs.html"))
    assert result.flagged == []
    assert len(result.items) == 34
    by_abbr = {c.abbreviation: c for c in result.items if c.abbreviation}
    assert by_abbr["ASME"].name == "American Society of Mechanical Engineers"
    assert by_abbr["ASME"].majors == ("mechanical",)
    assert by_abbr["IEEE"].majors == ("electrical",)
    assert by_abbr["ASCE"].majors == ("civil",)
    assert by_abbr["SHPE"].kind == "both" and "community" in by_abbr["SHPE"].tags
    # Contact emails are never stored.
    assert all("@" not in (c.description or "") for c in result.items)


def test_fresno_expo() -> None:
    result = fresno.parse_expo(page("fresno_expo.html"))
    assert result.flagged == []
    (expo,) = result.items
    assert expo.title == "Welcome Back BBQ & Industry Expo"
    assert expo.starts_at.replace(tzinfo=None) == datetime(2026, 9, 23, 10, 0)
    assert expo.ends_at is not None and expo.ends_at.hour == 14
    assert expo.location == "Engineering East (South Lawn)"


def test_fresno_expo_with_a_wrong_weekday_is_flagged_not_stored() -> None:
    broken = page("fresno_expo.html").replace("Wednesday, Sept. 23", "Friday, Sept. 23")
    result = fresno.parse_expo(broken)
    assert result.items == [] and "weekday doesn't match" in result.flagged[0]
    assert fresno.parse_expo("<p>nothing here</p>").flagged


def test_fresno_academic_calendar() -> None:
    result = fresno.parse_academic_calendar(page("fresno_calendar_current.html"))
    assert result.flagged == []
    fall, spring = result.items
    assert (fall.code, fall.starts_on, fall.ends_on) == (
        "2026FA",
        date(2026, 8, 19),
        date(2026, 12, 23),
    )
    assert (spring.code, spring.starts_on, spring.ends_on) == (
        "2027SP",
        date(2027, 1, 19),
        date(2027, 5, 26),
    )
    labels = {e.label: e for e in fall.entries}
    assert labels["Thanksgiving Break"].ends_on == date(2026, 11, 27)
    assert labels["Final Examination Days"].kind == "finals"
    assert not fall.tentative


def test_fresno_next_year_is_tentative() -> None:
    result = fresno.parse_academic_calendar(page("fresno_calendar_next.html"), tentative=True)
    assert [t.code for t in result.items] == ["2027FA", "2028SP"]
    assert all(t.tentative for t in result.items)


def test_calendar_rows_with_a_wrong_weekday_are_flagged() -> None:
    gap = "\n                                 \n                                 "
    broken = page("fresno_calendar_current.html").replace(
        f"<td>Wednesday</td>{gap}<td>August 19</td>", "<td>Friday</td><td>August 19</td>"
    )
    result = fresno.parse_academic_calendar(broken)
    assert any("Friday" in f and "Wednesday" in f for f in result.flagged)
    assert fresno.parse_academic_calendar("<table><caption>Other</caption></table>").flagged


def test_berkeley_engineering_groups() -> None:
    result = berkeley.parse_engineering_groups(page("berkeley_engineering_groups.html"))
    assert result.flagged == []
    assert len(result.items) == 46
    by_name = {g.name: g for g in result.items}
    asce = by_name["American Society of Civil Engineers"]
    assert (asce.abbreviation, asce.kind, asce.majors) == ("ASCE", "professional", ("civil",))
    chi = by_name["Chi Epsilon"]
    assert chi.description == "Civil Engineering Honor Society" and chi.abbreviation == "XE"
    assert "honors" in chi.tags
    assert by_name["Steel Bridge Competition Team"].kind == "both"
    assert by_name["IEEE Student Branch"].url == "http://ieee.berkeley.edu/"
    assert berkeley.parse_engineering_groups("<h3>Nothing</h3>").flagged
