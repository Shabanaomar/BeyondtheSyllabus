"""Polite page fetching for the collectors.

Rules this module enforces (see docs/sources/):

* robots.txt is read for every host before anything else, and a disallowed URL is never fetched.
* The host's crawl-delay is honoured (at least 1 second between requests to the same host).
* Requests identify the project: "BeyondTheSyllabusBot/0.1 (+<repo URL>; <contact>)". The contact
  email comes from the COLLECTOR_CONTACT_EMAIL environment variable and is never written in code.
* A bot challenge (for example Amazon WAF's "x-amzn-waf-action: challenge") stops collection from
  that host. We never try to get around a challenge.
* Every response is saved raw with its fetch time, and a content hash is returned so callers can
  tell whether the page changed.
"""

from __future__ import annotations

import hashlib
import os
import time
import urllib.robotparser
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx

REPO_URL = "https://github.com/Shabanaomar/BeyondtheSyllabus"
BOT_NAME = "BeyondTheSyllabusBot"
MIN_DELAY_SECONDS = 1.0


def user_agent() -> str:
    contact = os.environ.get("COLLECTOR_CONTACT_EMAIL", "").strip()
    suffix = f"; {contact}" if contact else ""
    return f"{BOT_NAME}/0.1 (+{REPO_URL}{suffix})"


class CollectionError(Exception):
    """A page couldn't be collected. The message says why, in plain language."""


class DisallowedError(CollectionError):
    pass


class BlockedError(CollectionError):
    pass


@dataclass(frozen=True)
class Page:
    url: str
    final_url: str
    status: int
    text: str
    content_hash: str
    fetched_at: datetime
    raw_path: str | None


@dataclass
class Fetcher:
    """Fetches pages one at a time, respecting each host's robots.txt and crawl delay."""

    raw_dir: Path | None = None
    client: httpx.Client | None = None
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    _robots: dict[str, urllib.robotparser.RobotFileParser] = field(default_factory=dict)
    _last_request: dict[str, float] = field(default_factory=dict)
    _blocked_hosts: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = httpx.Client(
                headers={"User-Agent": user_agent()},
                follow_redirects=True,
                timeout=40.0,
            )

    # -- robots -------------------------------------------------------------------------------

    def _robots_for(self, url: str) -> urllib.robotparser.RobotFileParser:
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self._robots:
            parser = urllib.robotparser.RobotFileParser()
            response = self._get(f"{host}/robots.txt", host_key=parts.netloc)
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
            elif response.status_code in (401, 403):
                # A protected robots.txt means "don't crawl".
                parser.parse(["User-agent: *", "Disallow: /"])
            else:
                # No robots.txt (404 etc.) means no restrictions.
                parser.parse([])
            self._robots[host] = parser
        return self._robots[host]

    def allowed(self, url: str) -> bool:
        return self._robots_for(url).can_fetch(BOT_NAME, url)

    def _delay_for(self, netloc: str) -> float:
        parser = self._robots.get(f"https://{netloc}") or self._robots.get(f"http://{netloc}")
        delay = parser.crawl_delay(BOT_NAME) if parser else None
        return max(MIN_DELAY_SECONDS, float(delay or 0))

    # -- requests -----------------------------------------------------------------------------

    def _get(self, url: str, host_key: str) -> httpx.Response:
        if self.client is None:  # pragma: no cover (set in __post_init__)
            raise RuntimeError("Fetcher has no HTTP client")
        last = self._last_request.get(host_key)
        if last is not None:
            wait = self._delay_for(host_key) - (self.clock() - last)
            if wait > 0:
                self.sleep(wait)
        try:
            response = self.client.get(url)
        except httpx.HTTPError as error:
            raise CollectionError(f"Couldn't reach {url}: {error}") from error
        finally:
            self._last_request[host_key] = self.clock()
        return response

    def fetch(self, url: str) -> Page:
        netloc = urlsplit(url).netloc
        if netloc in self._blocked_hosts:
            raise BlockedError(f"{netloc} challenged us earlier in this run; skipping {url}")
        if not self.allowed(url):
            raise DisallowedError(f"robots.txt disallows {url}")
        response = self._get(url, host_key=netloc)
        if response.headers.get("x-amzn-waf-action") or response.status_code in (202, 429):
            self._blocked_hosts.add(netloc)
            raise BlockedError(
                f"{netloc} returned a bot challenge or rate limit (HTTP {response.status_code}) "
                f"for {url}. Not retrying."
            )
        if response.status_code != 200:
            raise CollectionError(f"{url} returned HTTP {response.status_code}")
        fetched_at = datetime.now(UTC)
        digest = hashlib.sha256(response.content).hexdigest()
        raw_path = self._save(url, fetched_at, response.content)
        return Page(
            url=url,
            final_url=str(response.url),
            status=response.status_code,
            text=response.text,
            content_hash=digest,
            fetched_at=fetched_at,
            raw_path=raw_path,
        )

    def _save(self, url: str, when: datetime, body: bytes) -> str | None:
        if self.raw_dir is None:
            return None
        parts = urlsplit(url)
        safe = (parts.netloc + parts.path).replace("/", "_").strip("_") or "index"
        path = self.raw_dir / when.strftime("%Y-%m-%d") / f"{safe[:150]}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return str(path)
