"""Small, dependency-free helpers for reading HTML with the standard library."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser

_SPACE = re.compile(r"\s+")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def clean(text: str) -> str:
    """Unescape entities and collapse whitespace."""
    return _SPACE.sub(" ", html.unescape(text)).strip()


def strip_emails(text: str) -> str:
    """Remove email addresses: we link to clubs' pages instead of storing contact details."""
    text = clean(_EMAIL.sub("", text).replace("\u200b", ""))
    text = re.sub(r"\s*\b(or\s+)?(please\s+)?contact\s*[:.]?\s*$", "", text, flags=re.I)
    return text.strip(" :;,.")


class TableReader(HTMLParser):
    """Collects every <table> as (caption, rows of cell text)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[tuple[str, list[list[str]]]] = []
        self._in_table = 0
        self._caption: list[str] | None = None
        self._rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._caption_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._in_table += 1
            self._rows, self._caption_text = [], ""
        elif tag == "caption" and self._in_table:
            self._caption = []
        elif tag == "tr" and self._in_table:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "caption" and self._caption is not None:
            self._caption_text = clean("".join(self._caption))
            self._caption = None
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(clean("".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self._rows.append(self._row)
            self._row = None
        elif tag == "table" and self._in_table:
            self._in_table -= 1
            self.tables.append((self._caption_text, self._rows))

    def handle_data(self, data: str) -> None:
        if self._caption is not None:
            self._caption.append(data)
        if self._cell is not None:
            self._cell.append(data)


def read_tables(markup: str) -> list[tuple[str, list[list[str]]]]:
    reader = TableReader()
    reader.feed(markup)
    return reader.tables


def visible_text(markup: str) -> str:
    """Page text without scripts, styles and navigation, one block per line."""
    markup = re.sub(r"(?is)<(script|style|nav|header|footer)\b[^>]*>.*?</\1>", " ", markup)
    text = html.unescape(re.sub(r"<[^>]+>", "\n", markup))
    lines = (_SPACE.sub(" ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)
