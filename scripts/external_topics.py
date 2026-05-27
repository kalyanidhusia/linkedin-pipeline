"""
External topic discovery from Biostars, Stack Overflow, and Medium RSS feeds.

Fetches recent bioinformatics topics from community sites, scores them by
recency + engagement + source weight, applies dedup against past posts,
and caches results to avoid hammering the feeds.

Public API:
    fetch_external_topics(limit=20, force_refresh=False) -> list[dict]
        Returns list of {title, link, source, score, date, snippet}, sorted
        by score descending.

Each call uses the disk cache if it's < CACHE_TTL_HOURS old, otherwise
re-fetches from all sources.

Network failures and feed parse errors are caught silently per-source: if
Medium is down, you still get Biostars + SO. If everything fails, you get
an empty list (caller should fall back to internal sources).
"""
import json
import time
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import feedparser
except ImportError as e:
    raise ImportError(
        "external_topics needs feedparser. Install with:\n"
        "  pip install feedparser"
    ) from e

import topic_dedup


# --- Configuration -----------------------------------------------------------

# RSS endpoints. If any of these break (site changes their feed structure),
# only that source fails - others continue.
SOURCES = {
    "biostars": {
        "url": "https://www.biostars.org/feeds/latest/",
        "weight": 1.0,
        "kind": "qa",  # questions = real problems
    },
    "stackoverflow": {
        "url": "https://stackoverflow.com/feeds/tag/bioinformatics",
        "weight": 1.0,
        "kind": "qa",
    },
    "medium": {
        "url": "https://medium.com/feed/tag/bioinformatics",
        "weight": 0.6,   # tertiary - lower quality, more noise
        "kind": "article",
    },
}

CACHE_DIR_NAME = "cache"
CACHE_FILE_NAME = "external_topics.json"
CACHE_TTL_HOURS = 24

# Per-request timeout in seconds. feedparser respects this.
FETCH_TIMEOUT = 15

# Min title length filter - drops things like "?" or single-word titles
MIN_TITLE_LEN = 12

# Score weights
RECENCY_BOOST_WEEK = 1.5     # < 7 days old
RECENCY_BOOST_MONTH = 1.0    # < 30 days
RECENCY_BOOST_OLDER = 0.5    # > 30 days
DEDUP_PENALTY = -10.0        # topic seen in our past posts -> effectively excluded

# Max topics per source to limit feed processing time
MAX_PER_SOURCE = 30


# --- Cache management --------------------------------------------------------

def _cache_dir() -> Path:
    """Locate the cache/ directory at project root, create if missing."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / CACHE_DIR_NAME,
        script_dir / CACHE_DIR_NAME,
    ]
    for p in candidates:
        if p.exists():
            return p
    # Create at project root (parent of scripts/)
    cache = script_dir.parent / CACHE_DIR_NAME
    cache.mkdir(exist_ok=True)
    return cache


def _cache_path() -> Path:
    return _cache_dir() / CACHE_FILE_NAME


def _cache_is_fresh() -> bool:
    """True if cache file exists and was written < CACHE_TTL_HOURS ago."""
    path = _cache_path()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text())
        fetched_at = datetime.fromisoformat(data["fetched_at"])
        age = datetime.now(timezone.utc) - fetched_at
        return age < timedelta(hours=CACHE_TTL_HOURS)
    except Exception:
        return False


def _load_cache() -> list[dict]:
    try:
        data = json.loads(_cache_path().read_text())
        return data.get("topics", [])
    except Exception:
        return []


def _save_cache(topics: list[dict]) -> None:
    try:
        payload = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "topics": topics,
        }
        _cache_path().write_text(json.dumps(payload, indent=2))
    except Exception as e:
        print(f"  ⚠ Could not write topic cache: {e}")


# --- Source-specific parsing -------------------------------------------------

def _parse_so_vote_count(title: str) -> tuple[str, int]:
    """Stack Overflow tag RSS prefixes titles with vote count like:
       '+5 How to parse a VCF in Python'.
    Returns (clean_title, votes). Votes defaults to 0 if no prefix."""
    m = re.match(r"^([+-]?\d+)\s+(.+)$", title.strip())
    if m:
        try:
            votes = int(m.group(1))
            return m.group(2).strip(), votes
        except ValueError:
            pass
    return title.strip(), 0


def _entry_date(entry) -> datetime:
    """Best-effort date extraction. Returns now() if nothing parseable."""
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return datetime.now(timezone.utc)


def _entry_snippet(entry, max_len: int = 200) -> str:
    """Get a short description from the entry summary, stripped of HTML."""
    summary = entry.get("summary", "") or entry.get("description", "")
    # Strip HTML tags crudely
    text = re.sub(r"<[^>]+>", " ", summary)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


# --- Scoring -----------------------------------------------------------------

def _recency_factor(post_date: datetime) -> float:
    """Boost recent posts. Returns multiplier on base score."""
    now = datetime.now(timezone.utc)
    age = now - post_date
    if age < timedelta(days=7):
        return RECENCY_BOOST_WEEK
    if age < timedelta(days=30):
        return RECENCY_BOOST_MONTH
    return RECENCY_BOOST_OLDER


def _engagement_factor(source_name: str, entry, votes: int) -> float:
    """Convert per-source engagement signals to a 0-2 multiplier."""
    if source_name == "stackoverflow":
        # Vote count - normalize. 0 votes = 0.5x, 1-5 = 1.0x, 6+ = 1.5x, 20+ = 2.0x
        if votes >= 20:
            return 2.0
        if votes >= 6:
            return 1.5
        if votes >= 1:
            return 1.0
        return 0.5
    if source_name == "biostars":
        # Biostars RSS doesn't expose votes reliably in standard feed.
        # Use comment/answer count if available, else neutral.
        # Most entries have 'updated' close to 'published' for new posts.
        return 1.0
    if source_name == "medium":
        # Medium has no reliable engagement signal in RSS. Trust the tag system.
        return 1.0
    return 1.0


def _topic_score(source_name: str, source_weight: float,
                 entry, post_date: datetime, votes: int) -> float:
    """Combine source weight, engagement, recency into a final score."""
    base = source_weight
    return base * _engagement_factor(source_name, entry, votes) * _recency_factor(post_date)


# --- Per-source fetchers -----------------------------------------------------

def _fetch_one_source(source_name: str, config: dict) -> list[dict]:
    """Fetch and normalize entries from one RSS source.

    Returns list of {title, link, source, score, date, snippet}.
    Returns [] on any failure (network, parse, empty feed).
    """
    url = config["url"]
    source_weight = config["weight"]

    try:
        # feedparser supports a request_headers arg in some versions; safest
        # is to just call with the URL. socket timeout is set globally below.
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"  ⚠ {source_name}: fetch failed - {e}")
        return []

    if feed.bozo and not feed.entries:
        # feedparser sets bozo=1 on malformed feeds. If we still got entries
        # we can use them; if not, skip this source.
        reason = getattr(feed, "bozo_exception", "unknown parse error")
        print(f"  ⚠ {source_name}: feed parse issue - {reason}")
        return []

    if not feed.entries:
        print(f"  ⚠ {source_name}: no entries returned")
        return []

    out = []
    for entry in feed.entries[:MAX_PER_SOURCE]:
        raw_title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not raw_title or not link:
            continue

        # Parse SO vote count out of title prefix
        if source_name == "stackoverflow":
            title, votes = _parse_so_vote_count(raw_title)
        else:
            title, votes = raw_title, 0

        if len(title) < MIN_TITLE_LEN:
            continue

        post_date = _entry_date(entry)
        snippet = _entry_snippet(entry)
        score = _topic_score(source_name, source_weight, entry, post_date, votes)

        out.append({
            "title": title,
            "link": link,
            "source": source_name,
            "score": round(score, 3),
            "date": post_date.date().isoformat(),
            "snippet": snippet,
            "votes": votes,
        })

    return out


# --- Public API --------------------------------------------------------------

def _apply_dedup_penalty(topics: list[dict]) -> list[dict]:
    """Penalize topics whose title resembles something we've already posted.
    Uses substring match (case-insensitive) — simple but works."""
    posted_topics = []
    for ptype in ("type1_update", "type2_tip", "type3_visual", "type4_koshish"):
        posted_topics.extend(topic_dedup.get_recent_topics(ptype, limit=30))

    if not posted_topics:
        return topics

    posted_lower = [t.lower() for t in posted_topics if t]

    for topic in topics:
        title_lower = topic["title"].lower()
        # Mark as already-covered if a past topic substring appears in this
        # title, or vice versa (one fully contains the other)
        for past in posted_lower:
            if len(past) > 15 and (past in title_lower or title_lower in past):
                topic["score"] += DEDUP_PENALTY
                topic["dedup_match"] = past
                break
    return topics


def fetch_external_topics(limit: int = 20, force_refresh: bool = False) -> list[dict]:
    """Return up to `limit` external topics, scored and dedup-penalized.

    Uses disk cache if it's < CACHE_TTL_HOURS old, unless force_refresh=True.
    Caching applies to the FETCH only — dedup re-runs every call so freshly
    posted topics are penalized immediately.
    """
    if not force_refresh and _cache_is_fresh():
        topics = _load_cache()
        print(f"  ⓘ Using cached external topics ({len(topics)} items)")
    else:
        # Set socket timeout for feedparser's underlying urllib request.
        # This is the only way to bound network time.
        import socket
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(FETCH_TIMEOUT)
        try:
            print(f"  → Fetching external topics from {len(SOURCES)} sources...")
            topics = []
            for source_name, config in SOURCES.items():
                source_topics = _fetch_one_source(source_name, config)
                print(f"    {source_name}: {len(source_topics)} items")
                topics.extend(source_topics)
        finally:
            socket.setdefaulttimeout(old_timeout)
        _save_cache(topics)

    # Always apply dedup fresh - past posts may have changed since cache
    topics = _apply_dedup_penalty(topics)
    # Sort by score descending
    topics.sort(key=lambda t: -t["score"])
    return topics[:limit]


def format_topics_for_prompt(topics: list[dict], max_count: int = 10) -> str:
    """Format topics as a bullet list for prompt injection.
    Caller decides how many to include - usually a subset of fetch result."""
    if not topics:
        return ""
    lines = ["EXTERNAL TOPIC SUGGESTIONS (from community sites):"]
    for t in topics[:max_count]:
        lines.append(f"- [{t['source']}] {t['title']}")
        if t.get("snippet"):
            lines.append(f"    {t['snippet'][:120]}...")
    return "\n".join(lines)


if __name__ == "__main__":
    # Diagnostic: fetch and print scored topics
    print("Fetching external topics...")
    topics = fetch_external_topics(limit=15, force_refresh=True)
    print(f"\nTop {len(topics)} topics by score:\n")
    for t in topics:
        flag = " [SEEN]" if "dedup_match" in t else ""
        print(f"  {t['score']:5.2f}  [{t['source']:13s}] {t['title'][:70]}{flag}")
        if t.get("snippet"):
            print(f"         {t['snippet'][:80]}...")
