"""Parsers for UC Berkeley pages that allow collection (see docs/sources/uc-berkeley.md)."""

from __future__ import annotations

from html.parser import HTMLParser

from ..html_tools import clean
from ..records import OrganizationRecord, ParseResult
from ..tagging import majors_for, tags_for

GROUPS_URL = "https://engineering.berkeley.edu/students/student-life/teams-and-organizations/"

# The page's own section headings decide what kind of club each one is.
CATEGORY_KIND = {
    "academic and professional": "professional",
    "honor societies": "professional",
    "competition teams": "both",
    "design, make, hack": "both",
    "project-based team": "both",
    "school, community and global outreach": "both",
    "social": "social",
}


class _Groups(HTMLParser):
    """Walks the page: an <h3> sets the category; each <li> with a link is one group."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.groups: list[tuple[str, str, str | None, str]] = []  # category, name, url, trailing
        self._category: str | None = None
        self._heading: list[str] | None = None
        self._li: list[str] | None = None
        self._link_text: list[str] | None = None
        self._link_url: str | None = None
        self._name: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h3":
            self._heading = []
        elif tag == "li" and self._category:
            self._li, self._name, self._link_url = [], None, None
        elif tag == "a" and self._li is not None and self._name is None:
            self._link_text = []
            self._link_url = dict(attrs).get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self._heading is not None:
            heading = clean("".join(self._heading)).lower()
            self._category = heading if heading in CATEGORY_KIND else None
            self._heading = None
        elif tag == "a" and self._link_text is not None:
            self._name = clean("".join(self._link_text))
            self._link_text = None
        elif tag == "li" and self._li is not None:
            if self._name and self._category:
                self.groups.append(
                    (self._category, self._name, self._link_url, clean("".join(self._li)))
                )
            self._li = None
        elif tag == "ul" and self._li is None:
            pass

    def handle_data(self, data: str) -> None:
        if self._heading is not None:
            self._heading.append(data)
        if self._link_text is not None:
            self._link_text.append(data)
        elif self._li is not None:
            self._li.append(data)


def parse_engineering_groups(markup: str) -> ParseResult[OrganizationRecord]:
    reader = _Groups()
    reader.feed(markup)
    result: ParseResult[OrganizationRecord] = ParseResult()
    for category, name, url, trailing in reader.groups:
        abbreviation = None
        note = trailing.strip(" \u2013-")
        if note.startswith("(") and note.endswith(")"):
            abbreviation, note = note[1:-1].strip(), ""
        elif note.endswith(")") and "(" in note:
            note, _, abbr = note.rpartition("(")
            abbreviation, note = abbr[:-1].strip(), note.strip(" \u2013-")
        tags = tags_for(name, note)
        result.items.append(
            OrganizationRecord(
                name=name,
                kind=CATEGORY_KIND[category],
                abbreviation=abbreviation,
                category=category.capitalize(),
                description=note or None,
                url=url if url and url.startswith("http") else GROUPS_URL,
                tags=tuple(sorted(set(tags) | ({"honors"} if "honor" in category else set()))),
                majors=majors_for(tags),
            )
        )
    if not result.items:
        result.flagged.append("No groups found: the page layout may have changed")
    return result
