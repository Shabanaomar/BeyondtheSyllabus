"""Tags for clubs, derived only from words in the club's own name.

The engine uses tags to match clubs to a student's major, career goal and interests. Tags come
from the name the university lists, never from guesses about what a club does. Every collected
club still goes to the review queue before students see it, so you can correct a tag.
"""

from __future__ import annotations

import re

# tag -> words or phrases that, when in a club's name, earn the tag (case-insensitive).
NAME_TAGS: dict[str, tuple[str, ...]] = {
    "civil": (
        "civil",
        "asce",
        "transportation",
        "water",
        "geotechnical",
        "public works",
        "chi epsilon",
        "steel bridge",
        "concrete canoe",
        "seismic",
        "geowall",
        "timber",
        "railway",
        "arema",
    ),
    "mechanical": (
        "mechanical",
        "asme",
        "ashrae",
        "aerospace",
        "aeronautics",
        "racing",
        "human powered",
        "mechatronics",
        "formula",
        "bike builders",
        "rocketry",
        "sae",
    ),
    "electrical": (
        "electrical",
        "ieee",
        "mechatronics",
        "eta kappa nu",
        "calsol",
        "formula electric",
    ),
    "computing": ("computer", "cybersecurity", "ai", "hack", "extended reality"),
    "robotics": ("robot", "mechatronics", "unmanned", "uav"),
    "aerospace": ("aerospace", "aeronautics", "space", "rocketry", "uav", "unmanned aerial"),
    "energy": ("energy", "solar", "calsol", "nuclear", "sustainab"),
    "environmental": ("environment", "water", "sustainab", "green"),
    "construction": ("construction", "contractors", "design build", "home builders"),
    "surveying": ("survey", "geomatics", "photogrammetry"),
    "honors": ("honor", "tau beta pi", "chi epsilon", "eta kappa nu", "lambda", "sigma lambda"),
    "competition": ("racing", "team", "competition", "canoe", "bridge", "human powered", "combat"),
    "community": (
        "black engineers",
        "black engineering",
        "hispanic",
        "latin",
        "women",
        "asian",
        "native american",
        "lgbt",
        "first generation",
        "out in science",
        "pilipinx",
        "filipino",
    ),
    "outreach": ("without borders", "outreach", "pioneers in engineering", "enabletech"),
    "leadership": ("council", "student board", "officers"),
}

# Tags that mean a club fits a particular major.
MAJOR_TAGS = {"civil": "civil", "mechanical": "mechanical", "electrical": "electrical"}


def _pattern(word: str) -> re.Pattern[str]:
    # Words match from a word boundary; short words (SAE, AI, UAV) must match whole.
    end = r"\b" if len(word) <= 3 else ""
    return re.compile(r"\b" + re.escape(word) + end)


_PATTERNS = {tag: [_pattern(w) for w in words] for tag, words in NAME_TAGS.items()}


def tags_for(name: str, extra_text: str = "") -> tuple[str, ...]:
    haystack = f"{name} {extra_text}".lower()
    found = {
        tag for tag, patterns in _PATTERNS.items() if any(p.search(haystack) for p in patterns)
    }
    return tuple(sorted(found))


def majors_for(tags: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({MAJOR_TAGS[t] for t in tags if t in MAJOR_TAGS}))


def abbreviation_in(name: str) -> tuple[str, str | None]:
    """'Society of Women Engineers (SWE)' -> ('Society of Women Engineers', 'SWE')."""
    match = re.match(r"^(.*?)\s*\(([^()]+)\)\s*$", name)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return name.strip(), None
