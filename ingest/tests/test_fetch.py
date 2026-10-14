from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from bts_ingest.fetch import BlockedError, CollectionError, DisallowedError, Fetcher, user_agent


def make(
    routes: dict[str, httpx.Response], tmp_path: Path | None = None
) -> tuple[Fetcher, list[float], list[str]]:
    sleeps: list[float] = []
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        assert request.headers["user-agent"].startswith("BeyondTheSyllabusBot/0.1")
        return routes.get(str(request.url), httpx.Response(404))

    clock = iter(float(i) for i in range(1000))
    fetcher = Fetcher(
        raw_dir=tmp_path,
        client=httpx.Client(
            transport=httpx.MockTransport(handler), headers={"User-Agent": user_agent()}
        ),
        sleep=sleeps.append,
        clock=lambda: next(clock),
    )
    return fetcher, sleeps, seen


def test_robots_disallow_is_respected_and_nothing_else_is_requested() -> None:
    fetcher, _, seen = make(
        {"https://a.edu/robots.txt": httpx.Response(200, text="User-agent: *\nDisallow: /api/\n")}
    )
    with pytest.raises(DisallowedError):
        fetcher.fetch("https://a.edu/api/clubs")
    assert seen == ["https://a.edu/robots.txt"]


def test_crawl_delay_is_honoured_between_requests(tmp_path: Path) -> None:
    fetcher, sleeps, _ = make(
        {
            "https://a.edu/robots.txt": httpx.Response(
                200, text="User-agent: *\nCrawl-delay: 120\n"
            ),
            "https://a.edu/one": httpx.Response(200, text="one"),
            "https://a.edu/two": httpx.Response(200, text="two"),
        },
        tmp_path,
    )
    first = fetcher.fetch("https://a.edu/one")
    fetcher.fetch("https://a.edu/two")
    assert sleeps and all(s > 100 for s in sleeps)
    assert first.text == "one" and len(first.content_hash) == 64
    assert first.raw_path and Path(first.raw_path).read_text() == "one"


def test_missing_robots_means_allowed() -> None:
    fetcher, _, _ = make({"https://b.edu/page": httpx.Response(200, text="ok")})
    assert fetcher.fetch("https://b.edu/page").status == 200


def test_bot_challenge_stops_collection_from_that_host() -> None:
    fetcher, _, seen = make(
        {
            "https://c.edu/robots.txt": httpx.Response(200, text="User-agent: *\nDisallow:\n"),
            "https://c.edu/a": httpx.Response(202, headers={"x-amzn-waf-action": "challenge"}),
            "https://c.edu/b": httpx.Response(200, text="b"),
        }
    )
    with pytest.raises(BlockedError, match="bot challenge"):
        fetcher.fetch("https://c.edu/a")
    with pytest.raises(BlockedError, match="challenged us earlier"):
        fetcher.fetch("https://c.edu/b")
    assert "https://c.edu/b" not in seen


def test_errors_are_plain_language() -> None:
    fetcher, _, _ = make({"https://d.edu/robots.txt": httpx.Response(403)})
    with pytest.raises(DisallowedError):
        fetcher.fetch("https://d.edu/x")
    fetcher, _, _ = make({})
    with pytest.raises(CollectionError, match="HTTP 404"):
        fetcher.fetch("https://e.edu/missing")


def test_contact_email_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COLLECTOR_CONTACT_EMAIL", raising=False)
    assert (
        user_agent()
        == "BeyondTheSyllabusBot/0.1 (+https://github.com/Shabanaomar/BeyondtheSyllabus)"
    )
    monkeypatch.setenv("COLLECTOR_CONTACT_EMAIL", "team@example.org")
    assert user_agent().endswith("; team@example.org)")


def test_network_failures_become_collection_errors() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    fetcher = Fetcher(
        client=httpx.Client(transport=httpx.MockTransport(boom)), sleep=lambda s: None
    )
    with pytest.raises(CollectionError, match="Couldn't reach"):
        fetcher.fetch("https://f.edu/x")
