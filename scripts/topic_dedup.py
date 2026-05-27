"""
Topic deduplication: scan drafts/posted/ for previously-used topics so the LLM
can avoid repeating them.

Strategy:
- For each post type, gather the 'topic' (and 'title' / 'dont' for visual cards)
  from meta.json files in drafts/posted/
- Pass these as a 'recently_covered' list into the LLM prompt
- LLM is told to avoid these topics
- If the source pool is smaller than the recent list, we don't enforce hard
  exhaustion - the LLM can pick whatever fits best given the constraint

Functions:
  get_recent_topics(post_type, limit=12) -> list[str]
      Returns the most recent N topics used for this post type.
  format_avoid_list(topics) -> str
      Format as a string for prompt injection.
"""
import json
from pathlib import Path


def _drafts_dir() -> Path:
    """Locate drafts/ relative to this script."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "drafts",
        script_dir / "drafts",
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    # Fallback: try current working directory
    cwd_drafts = Path.cwd() / "drafts"
    if cwd_drafts.exists():
        return cwd_drafts
    return script_dir.parent / "drafts"


def _extract_topic_from_meta(meta: dict) -> str | None:
    """Extract the canonical topic string from a meta.json dict.

    Priority order:
    1. 'topic' (Type 3, Type 4, and any Type 1/2 with topic written)
    2. 'title' (Type 4)
    3. 'dont' (Type 3 fallback)
    4. First 80 chars of body text if all else fails (legacy posts)
    """
    topic = (meta.get("topic") or "").strip()
    if topic:
        return topic

    title = (meta.get("title") or "").strip()
    if title:
        return title

    dont = (meta.get("dont") or "").strip()
    if dont:
        return f"Don't: {dont}"

    return None


def get_recent_topics(post_type: str, limit: int = 12) -> list[str]:
    """Return up to `limit` most recent topics used for `post_type`.

    Looks in drafts/posted/<date>_<type>/meta.json. Returns most recent first.
    If post_type is None or 'all', returns topics across all types.
    """
    drafts = _drafts_dir()
    posted = drafts / "posted"
    if not posted.exists() or not posted.is_dir():
        return []

    # Collect (date, type, topic) tuples
    entries = []
    for folder in posted.iterdir():
        if not folder.is_dir():
            continue
        meta_path = folder / "meta.json"
        if not meta_path.exists():
            continue

        # Parse folder name: YYYY-MM-DD_typeN_label
        name = folder.name
        parts = name.split("_", 1)
        if len(parts) != 2:
            continue
        date_str, type_label = parts[0], parts[1]

        try:
            meta = json.loads(meta_path.read_text())
        except Exception:
            continue

        # Filter by type
        if post_type and post_type != "all":
            meta_type = (meta.get("type") or "").strip()
            if meta_type != post_type:
                continue

        topic = _extract_topic_from_meta(meta)
        if topic:
            entries.append((date_str, type_label, topic))

    # Sort by date descending (most recent first), then truncate
    entries.sort(key=lambda e: e[0], reverse=True)
    return [topic for _, _, topic in entries[:limit]]


def format_avoid_list(topics: list[str]) -> str:
    """Format topics as a bullet list for prompt injection.
    Returns empty string if no topics."""
    if not topics:
        return ""
    lines = ["RECENTLY COVERED (avoid these specific topics):"]
    for t in topics:
        lines.append(f"- {t}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Diagnostic: show what's been posted by type
    print("=== Posted history by type ===\n")
    for ptype in ("type1_update", "type2_tip", "type3_visual", "type4_koshish"):
        topics = get_recent_topics(ptype, limit=20)
        print(f"{ptype}: {len(topics)} posts")
        for t in topics:
            print(f"  - {t}")
        print()
