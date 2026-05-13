"""
Fetch candidate items from bioRxiv RSS, GitHub trending, and your idea bank.
Returns a dict the prompt builder can plug into.
"""

import re
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config import BIORXIV_FEEDS, GITHUB_TRENDING_URL, MAX_CANDIDATES_PER_SOURCE

ROOT = Path(__file__).resolve().parent.parent


def fetch_biorxiv() -> list[dict[str, Any]]:
    """Pull recent preprints from bioRxiv subject feeds."""
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    for url in BIORXIV_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[: MAX_CANDIDATES_PER_SOURCE]:
                pub = entry.get("published_parsed")
                if pub:
                    pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue
                items.append({
                    "title": entry.get("title", "").strip(),
                    "summary": _clean(entry.get("summary", "")),
                    "link": entry.get("link", ""),
                    "source": "bioRxiv",
                })
        except Exception as e:
            print(f"[fetch_biorxiv] {url} failed: {e}")
    return items


def fetch_github_trending() -> list[dict[str, Any]]:
    """Scrape GitHub trending Python repos (no API key needed)."""
    try:
        resp = requests.get(GITHUB_TRENDING_URL, timeout=10,
                            headers={"User-Agent": "linkedin-pipeline/1.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"[fetch_github_trending] failed: {e}")
        return []

    # Crude scrape - we don't need a parser library.
    items = []
    pattern = re.compile(
        r'<h2 class="h3 lh-condensed">.*?href="/([^/]+/[^"]+)".*?</h2>(.*?)<p class="col-9 color-fg-muted my-1 pr-4">([^<]*)',
        re.DOTALL,
    )
    matches = list(pattern.finditer(resp.text))[:MAX_CANDIDATES_PER_SOURCE]
    for match in matches:
        repo, _middle, desc = match.groups()
        items.append({
            "title": repo.strip(),
            "summary": desc.strip(),
            "link": f"https://github.com/{repo.strip()}",
            "source": "GitHub trending",
        })
    return items


def load_idea_bank() -> list[dict[str, Any]]:
    """Read sources/idea_bank.md - one idea per bullet."""
    path = ROOT / "sources" / "idea_bank.md"
    if not path.exists():
        return []
    items = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ")):
            items.append({
                "title": line[2:].strip(),
                "summary": "",
                "link": "",
                "source": "idea bank",
            })
    return items[:MAX_CANDIDATES_PER_SOURCE]


def load_tips() -> list[str]:
    """Read sources/tips.md - one tip per bullet."""
    return _load_bullets(ROOT / "sources" / "tips.md")


def load_dos_donts() -> list[dict[str, str]]:
    """Read sources/dos_donts.md - format: 'DON'T: ... | DO: ...' per line."""
    path = ROOT / "sources" / "dos_donts.md"
    if not path.exists():
        return []
    pairs = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        # Only real bullet lines, not headers or format docs
        if not stripped.startswith(("- ", "* ")):
            continue
        body = stripped[2:].strip()
        if "|" not in body or "DON'T:" not in body.upper():
            continue
        # Skip placeholder template lines like "DON'T: <pithy 1-liner>"
        if "<" in body and ">" in body:
            continue
        parts = body.split("|", 1)
        dont = parts[0].split(":", 1)[-1].strip()
        do = parts[1].split(":", 1)[-1].strip() if len(parts) > 1 else ""
        if dont and do:
            pairs.append({"dont": dont, "do": do})
    return pairs


def _load_bullets(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()[2:].strip()
        for line in path.read_text().splitlines()
        if line.strip().startswith(("- ", "* "))
    ]


def _clean(html: str) -> str:
    """Strip tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()[:500]


def gather_all() -> dict[str, Any]:
    """One-shot collector for the generate script."""
    return {
        "biorxiv": fetch_biorxiv(),
        "github": fetch_github_trending(),
        "idea_bank": load_idea_bank(),
        "tips": load_tips(),
        "dos_donts": load_dos_donts(),
    }


if __name__ == "__main__":
    import json
    data = gather_all()
    print(json.dumps({k: len(v) for k, v in data.items()}, indent=2))
