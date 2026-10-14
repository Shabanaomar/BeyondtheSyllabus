"""Parsers for Fresno State pages that allow collection (see docs/sources/fresno-state.md)."""

from __future__ import annotations

import re
from datetime import date, datetime
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

from ..html_tools import clean, read_tables, strip_emails, visible_text
from ..records import CalendarEntry, EventRecord, OrganizationRecord, ParseResult, TermDates
from ..tagging import abbreviation_in, majors_for, tags_for

PACIFIC = ZoneInfo("America/Los_Angeles")
CLUBS_URL = "https://engineering.fresnostate.edu/student-services/clubs-orgs.html"
EXPO_URL = "https://engineering.fresnostate.edu/student-services/expo.html"
CALENDAR_CURRENT_URL = "https://academics.fresnostate.edu/about/calendars/current.html"
CALENDAR_NEXT_URL = "https://academics.fresnostate.edu/about/calendars/next.html"

MONTHS = {
    m: i + 1
    for i, m in enumerate(
        [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
    )
}
MONTH_ABBR = {k[:3]: v for k, v in MONTHS.items()} | {"sept": 9}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


# --- Clubs -------------------------------------------------------------------------------------


class _Accordion(HTMLParser):
    """Reads the college's club accordion: each card's button is the name, its body the details."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[tuple[str, str]] = []
        self._button: list[str] | None = None
        self._body: list[str] | None = None
        self._body_depth = 0
        self._name = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = dict(attrs).get("class") or ""
        if tag == "button" and "accordion-trigger" in classes:
            self._button = []
        elif tag == "div" and self._body is not None:
            self._body_depth += 1
        elif tag == "div" and "card-body" in classes.split():
            self._body = []
            self._body_depth = 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self._button is not None:
            self._name = clean("".join(self._button))
            self._button = None
        elif tag == "div" and self._body is not None:
            self._body_depth -= 1
            if self._body_depth == 0:
                self.cards.append((self._name, clean(" ".join(self._body))))
                self._body = None

    def handle_data(self, data: str) -> None:
        if self._button is not None:
            self._button.append(data)
        elif self._body is not None:
            self._body.append(data)


def parse_engineering_clubs(markup: str) -> ParseResult[OrganizationRecord]:
    reader = _Accordion()
    reader.feed(markup)
    result: ParseResult[OrganizationRecord] = ParseResult()
    for raw_name, body in reader.cards:
        if not raw_name:
            continue
        name, abbreviation = abbreviation_in(raw_name)
        description: str | None = strip_emails(body)
        # Bodies that only said "For more information, contact <email>" carry nothing once the
        # email is removed.
        if description and re.fullmatch(
            r"(for more information,?\s*(please\s*)?contact)?", description, re.I
        ):
            description = None
        tags = tags_for(raw_name)
        if "leadership" in tags and "council" in name.lower():
            kind = "professional"
        elif {"community", "competition"} & set(tags):
            kind = "both"
        else:
            kind = "professional"
        result.items.append(
            OrganizationRecord(
                name=name,
                kind=kind,
                abbreviation=abbreviation,
                category="Lyles College of Engineering clubs",
                description=description,
                url=CLUBS_URL,
                tags=tags,
                majors=majors_for(tags),
            )
        )
    if not result.items:
        result.flagged.append("No clubs found: the page layout may have changed")
    return result


# --- Industry Expo -----------------------------------------------------------------------------

_EXPO_LINE = re.compile(
    r"(?P<weekday>[A-Za-z]+),\s+(?P<month>[A-Za-z]+)\.?\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})"
    r"\s*\|\s*(?P<start>[\d:]+\s*[ap]\.?m\.?)\s+to\s+(?P<end>[\d:]+\s*[ap]\.?m\.?)"
    r"\s*\|\s*(?P<location>[^\n]+)",
    re.IGNORECASE,
)


def _clock(text: str) -> tuple[int, int]:
    match = re.match(r"(\d{1,2})(?::(\d{2}))?\s*([ap])", text.strip().lower())
    if not match:
        raise ValueError(text)
    hour, minute, half = int(match[1]), int(match[2] or 0), match[3]
    if half == "p" and hour != 12:
        hour += 12
    if half == "a" and hour == 12:
        hour = 0
    return hour, minute


def parse_expo(markup: str) -> ParseResult[EventRecord]:
    text = visible_text(markup)
    result: ParseResult[EventRecord] = ParseResult()
    match = _EXPO_LINE.search(text)
    if not match:
        result.flagged.append("Couldn't find the Expo date line: the page layout may have changed")
        return result
    month = (
        MONTHS.get(match["month"].lower())
        or MONTH_ABBR.get(match["month"].lower()[:4])
        or (MONTH_ABBR.get(match["month"].lower()[:3]))
    )
    if month is None:
        result.flagged.append(f"Unrecognised month in Expo date: {match.group(0)}")
        return result
    day = date(int(match["year"]), month, int(match["day"]))
    if WEEKDAYS[day.weekday()] != match["weekday"].lower():
        result.flagged.append(f"Expo weekday doesn't match its date: {match.group(0)}")
        return result
    sh, sm = _clock(match["start"])
    eh, em = _clock(match["end"])
    title_match = re.search(r"Welcome Back BBQ (?:&|and) Industry Expo", text)
    result.items.append(
        EventRecord(
            title=title_match.group(0) if title_match else "Industry Expo",
            kind="fair",
            starts_at=datetime(day.year, day.month, day.day, sh, sm, tzinfo=PACIFIC),
            ends_at=datetime(day.year, day.month, day.day, eh, em, tzinfo=PACIFIC),
            location=clean(match["location"]),
            url=EXPO_URL,
            majors=("civil", "mechanical", "electrical"),
        )
    )
    return result


# --- Academic calendar -------------------------------------------------------------------------

_CAPTION = re.compile(r"^(?P<season>Fall|Spring|Summer|Winter)\s+(?P<year>\d{4})\b", re.I)
_DATES = re.compile(
    r"^(?P<m1>[A-Za-z]+)\s*(?P<d1>\d{1,2})"
    r"(?:\s*[-\u2013]\s*(?:(?P<m2>[A-Za-z]+)\s*)?(?P<d2>\d{1,2}))?$"
)
_SEASON_CODE = {"fall": "FA", "spring": "SP", "summer": "SU", "winter": "WI"}


def _entry_kind(label: str) -> str:
    low = label.lower()
    if low.startswith("first day of") and "semester" in low:
        return "term_start"
    if low.startswith("last day of") and "semester" in low:
        return "term_end"
    if low.startswith("first day of") and "instruction" in low:
        return "instruction_start"
    if low.startswith("last day of") and "instruction" in low:
        return "instruction_end"
    if "final exam" in low:
        return "finals"
    if low.startswith("holiday") or "break" in low:
        return "holiday"
    return "other"


def parse_academic_calendar(markup: str, tentative: bool = False) -> ParseResult[TermDates]:
    result: ParseResult[TermDates] = ParseResult()
    for caption, rows in read_tables(markup):
        head = _CAPTION.match(caption)
        if not head:
            continue
        season, year = head["season"].lower(), int(head["year"])
        code = f"{year}{_SEASON_CODE[season]}"
        entries: list[CalendarEntry] = []
        for row in rows:
            if len(row) != 3 or row[0].lower() == "description":
                continue
            label, weekdays, when = row
            parsed = _DATES.match(when.replace("\xa0", " ").strip())
            if not parsed:
                result.flagged.append(f"{caption}: couldn't read the date {when!r} for {label!r}")
                continue
            m1 = MONTHS.get(parsed["m1"].lower())
            m2 = MONTHS.get((parsed["m2"] or parsed["m1"]).lower())
            if m1 is None or m2 is None:
                result.flagged.append(f"{caption}: unknown month in {when!r}")
                continue
            start = date(year, m1, int(parsed["d1"]))
            end_year = year + 1 if m2 < m1 else year
            end = date(end_year, m2, int(parsed["d2"] or parsed["d1"]))
            first_day = weekdays.split("-")[0].strip().lower()
            if first_day in WEEKDAYS and WEEKDAYS[start.weekday()] != first_day:
                result.flagged.append(
                    f"{caption}: {label} is listed as {weekdays} but {when} {year} is a "
                    f"{WEEKDAYS[start.weekday()].title()}"
                )
                continue
            entries.append(CalendarEntry(code, label, start, end, _entry_kind(label)))
        starts = [e.starts_on for e in entries if e.kind == "term_start"]
        ends = [e.ends_on for e in entries if e.kind == "term_end"]
        if not starts or not ends:
            result.flagged.append(f"{caption}: missing the first or last day of the semester")
            continue
        result.items.append(
            TermDates(
                code=code,
                name=f"{head['season'].title()} {year}",
                starts_on=starts[0],
                ends_on=ends[0],
                tentative=tentative,
                entries=tuple(entries),
            )
        )
    if not result.items and not result.flagged:
        result.flagged.append("No calendar tables found: the page layout may have changed")
    return result
