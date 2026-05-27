"""
Pick a post type, build the prompt, call the LLM, save the draft.

Output format per post (in drafts/YYYY-MM-DD_typeN/):
  post.txt   - exact text to paste to LinkedIn
  card.png   - image to attach (Type 3 only)
  meta.json  - type, source URLs, hashtags, generation timestamp
"""

import json
import random
import re
from datetime import datetime
from pathlib import Path

from config import AUTHOR, TYPE_WEIGHTS, AVOID_REPEATS, DRAFTS_DIR
from fetch_sources import gather_all
import llm_client
import make_image
import make_koshish_card
import topic_dedup

try:
    import external_topics
    EXTERNAL_TOPICS_AVAILABLE = True
except ImportError as e:
    print(f"  ⚠ external_topics unavailable ({e}). Skipping external sources.")
    external_topics = None
    EXTERNAL_TOPICS_AVAILABLE = False

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
DRAFTS = ROOT / DRAFTS_DIR


def _load(name: str) -> str:
    return (PROMPTS / name).read_text()


def _last_type() -> str | None:
    """Inspect drafts/ to see what was last drafted. Ignores posted/ and any
    non-draft folders."""
    if not DRAFTS.exists():
        return None
    # Only consider folders that look like YYYY-MM-DD_typeN
    candidates = []
    for d in DRAFTS.iterdir():
        if not d.is_dir():
            continue
        if d.name == "posted":
            continue
        parts = d.name.split("_", 1)
        if len(parts) != 2:
            continue
        # Must look like a date (rough check: starts with 4 digits)
        if not parts[0][:4].isdigit():
            continue
        candidates.append(d)
    dirs = sorted(candidates, reverse=True)
    if dirs:
        name = dirs[0].name
        parts = name.split("_", 1)
        return parts[1] if len(parts) > 1 else None
    # Legacy flat .md fallback
    files = sorted(DRAFTS.glob("20*.md"), reverse=True)
    if files:
        name = files[0].stem
        parts = name.split("_", 1)
        return parts[1] if len(parts) > 1 else None
    return None


def pick_type(forced: str | None = None) -> str:
    """Pick a post type. If `forced` is given, return it directly (overriding
    weights and the AVOID_REPEATS rule). Otherwise pick randomly by weight."""
    types = list(TYPE_WEIGHTS.keys())

    if forced:
        resolved = _resolve_type_name(forced, types)
        if resolved is None:
            raise SystemExit(
                f"Unknown type '{forced}'. Valid options:\n"
                + "\n".join(f"  {i + 1}  or  {t}" for i, t in enumerate(types))
            )
        return resolved

    weights = list(TYPE_WEIGHTS.values())
    if AVOID_REPEATS:
        last = _last_type()
        if last and last in types:
            i = types.index(last)
            weights[i] = 0
    return random.choices(types, weights=weights, k=1)[0]


def _resolve_type_name(value: str, types: list[str]) -> str | None:
    """Map a user-supplied type identifier to a full type key.
    Accepts: '4', 'type4', 'type4_koshish', 'koshish' (substring match)."""
    value = value.strip().lower()

    # Bare number: '4' -> types[3]
    if value.isdigit():
        idx = int(value) - 1
        if 0 <= idx < len(types):
            return types[idx]
        return None

    # Exact full match
    if value in types:
        return value

    # Prefix/substring match: 'type4', 'koshish', 'type4_koshish'
    matches = [t for t in types if value in t]
    if len(matches) == 1:
        return matches[0]
    return None


def _author_block() -> str:
    return (
        f"Author: {AUTHOR['name']}, {AUTHOR['title']} at {AUTHOR['affiliation']}.\n"
        f"Tagline: {AUTHOR['tagline']}\n"
        f"Expertise: {', '.join(AUTHOR['expertise'])}.\n"
        f"Audience: {AUTHOR['audience']}.\n"
        f"Voice traits:\n" + "\n".join(f"  - {t}" for t in AUTHOR["voice_traits"])
    )


def _safe_external_topics(limit: int = 10) -> list[dict]:
    """Fetch external topics, returning [] on any failure. Never blocks
    the pipeline if external sources are down."""
    if not EXTERNAL_TOPICS_AVAILABLE:
        return []
    try:
        return external_topics.fetch_external_topics(limit=limit)
    except Exception as e:
        print(f"  ⚠ External topic fetch failed: {e}. Continuing without.")
        return []


def _format_external_for_pool(topics: list[dict], max_items: int = 5) -> str:
    """Convert top external topics to bullet lines for prompt injection.
    Filters out anything with negative score (dedup-penalized below threshold)."""
    if not topics:
        return ""
    fresh = [t for t in topics if t["score"] > 0][:max_items]
    if not fresh:
        return ""
    lines = []
    for t in fresh:
        lines.append(f"- [{t['source']}] {t['title']}")
    return "\n".join(lines)


def build_type1(sources: dict) -> tuple[str, str, list[str]]:
    candidates = (sources["biorxiv"] or [])[:8] + (sources["github"] or [])[:4]

    # Add external community topics as additional candidates
    external = _safe_external_topics(limit=10)
    fresh_external = [t for t in external if t["score"] > 0][:5]
    for t in fresh_external:
        candidates.append({
            "source": t["source"],
            "title": t["title"],
            "summary": t.get("snippet", ""),
            "link": t["link"],
        })

    if not candidates:
        raise RuntimeError("No bioRxiv or GitHub items fetched. Try again later.")
    candidates_str = "\n\n".join(
        f"[{i + 1}] ({c['source']}) {c['title']}\n    {c.get('summary', '')[:300]}\n    {c['link']}"
        for i, c in enumerate(candidates)
    )
    voice = _load("voice_examples.md")
    template = _load("type1_update.md")
    avoid_list = topic_dedup.format_avoid_list(
        topic_dedup.get_recent_topics("type1_update", limit=12)
    )
    prompt = template.format(
        author=_author_block(),
        voice_examples=voice,
        candidates=candidates_str,
        avoid_list=avoid_list,
    )
    candidate_links = [c["link"] for c in candidates if c.get("link")]
    return prompt, "type1_update", candidate_links


def build_type2(sources: dict) -> tuple[str, str, list[str]]:
    tips = sources["tips"]
    ideas = sources["idea_bank"]
    if not tips and not ideas:
        raise RuntimeError("Add at least a few tips to sources/tips.md")
    pool = tips + [i["title"] for i in ideas]

    # Add external community topics - reframed as tip-candidates
    external = _safe_external_topics(limit=10)
    fresh = [t for t in external if t["score"] > 0][:5]
    pool.extend([f"{t['title']} (from {t['source']})" for t in fresh])

    pool_str = "\n".join(f"- {t}" for t in pool)
    voice = _load("voice_examples.md")
    template = _load("type2_tip.md")
    avoid_list = topic_dedup.format_avoid_list(
        topic_dedup.get_recent_topics("type2_tip", limit=12)
    )
    prompt = template.format(
        author=_author_block(),
        voice_examples=voice,
        topic_pool=pool_str,
        avoid_list=avoid_list,
    )
    return prompt, "type2_tip", []


def build_type3(sources: dict) -> tuple[str, str, list[str]]:
    pairs = sources["dos_donts"]
    if not pairs:
        raise RuntimeError("Add at least one pair to sources/dos_donts.md")
    pool_lines = [f"- {p['dont']} | {p['do']}" for p in pairs]

    # Add external community topics as raw inspiration (no DON'T|DO structure)
    # The LLM will reframe them into the do/don't format itself
    external = _safe_external_topics(limit=10)
    fresh = [t for t in external if t["score"] > 0][:4]
    if fresh:
        pool_lines.append("")  # blank separator
        pool_lines.append("# External community topics (reframe these into DON'T | DO):")
        for t in fresh:
            pool_lines.append(f"- inspiration: {t['title']} (from {t['source']})")

    pool_str = "\n".join(pool_lines)
    voice = _load("voice_examples.md")
    template = _load("type3_visual.md")
    avoid_list = topic_dedup.format_avoid_list(
        topic_dedup.get_recent_topics("type3_visual", limit=12)
    )
    prompt = template.format(
        author=_author_block(),
        voice_examples=voice,
        topic_pool=pool_str,
        avoid_list=avoid_list,
    )
    return prompt, "type3_visual", []


def build_type4(sources: dict) -> tuple[str, str, list[str]]:
    """Koshish notebook note. Draws from tips + idea_bank for source content
    (same pool as Type 2 — these are story-shaped lessons), and the LLM
    reformats them into title + sections + closing structure."""
    tips = sources["tips"]
    ideas = sources["idea_bank"]
    if not tips and not ideas:
        raise RuntimeError("Add at least a few tips to sources/tips.md")
    pool = tips + [i["title"] for i in ideas]

    # Add external community topics
    external = _safe_external_topics(limit=10)
    fresh = [t for t in external if t["score"] > 0][:5]
    pool.extend([f"{t['title']} (from {t['source']})" for t in fresh])

    pool_str = "\n".join(f"- {t}" for t in pool)
    voice = _load("voice_examples.md")
    template = _load("type4_koshish.md")
    avoid_list = topic_dedup.format_avoid_list(
        topic_dedup.get_recent_topics("type4_koshish", limit=12)
    )
    prompt = template.format(
        author=_author_block(),
        voice_examples=voice,
        topic_pool=pool_str,
        avoid_list=avoid_list,
    )
    return prompt, "type4_koshish", []


BUILDERS = {
    "type1_update": build_type1,
    "type2_tip": build_type2,
    "type3_visual": build_type3,
    "type4_koshish": build_type4,
}


def _extract_hashtags(text: str) -> tuple[str, list[str]]:
    """Pull hashtags off the end (last line). Returns (body, hashtag_list)."""
    lines = text.rstrip().split("\n")
    if not lines:
        return text, []
    last = lines[-1].strip()
    if last.startswith("#") and all(w.startswith("#") for w in last.split()):
        return "\n".join(lines[:-1]).rstrip(), last.split()
    return text, []


def _extract_topic_tag(text: str) -> tuple[str, str]:
    """Pull a TOPIC: <topic> line from the start of the LLM response.
    Returns (topic_string, body_without_topic_line). Topic is empty if missing.
    Looks at the first 3 non-empty lines to be robust to leading whitespace."""
    lines = text.split("\n")
    topic = ""
    drop_index = -1
    checked = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        checked += 1
        if checked > 3:
            break
        # Accept various forms: "TOPIC: foo", "**TOPIC:** foo", "[TOPIC] foo",
        # "Topic - foo". Strip leading markdown/bracket noise first.
        cleaned = re.sub(r"^[\[\*\s]+", "", stripped)
        m = re.match(r"^topic\]?\**\s*[:\-]?\s*(.+?)\**\s*$",
                     cleaned, flags=re.IGNORECASE)
        if m:
            topic = m.group(1).strip().rstrip(".")
            topic = topic.strip('"\'*[] ')
            drop_index = i
            break
    if drop_index >= 0:
        body = "\n".join(lines[:drop_index] + lines[drop_index + 1:]).strip()
        return topic, body
    return "", text


def _salvage_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    def escape_newlines_in_strings(s: str) -> str:
        out, in_str, escape = [], False, False
        for ch in s:
            if escape: out.append(ch); escape = False
            elif ch == "\\": out.append(ch); escape = True
            elif ch == '"': out.append(ch); in_str = not in_str
            elif ch == "\n" and in_str: out.append("\\n")
            elif ch == "\r" and in_str: out.append("\\r")
            else: out.append(ch)
        return "".join(out)

    escaped = escape_newlines_in_strings(text)
    try:
        return json.loads(escaped)
    except json.JSONDecodeError:
        pass

    fields = {}
    for key in ("topic", "dont", "do", "caption"):
        m = re.search(rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"', escaped, flags=re.DOTALL)
        if m:
            try:
                fields[key] = m.group(1).encode().decode("unicode_escape", errors="ignore")
            except Exception:
                fields[key] = m.group(1)
    if "caption" not in fields:
        m = re.search(r'"caption"\s*:\s*"((?:[^"\\]|\\.)*)$', escaped, flags=re.DOTALL)
        if m:
            try:
                fields["caption"] = m.group(1).encode().decode("unicode_escape", errors="ignore")
            except Exception:
                fields["caption"] = m.group(1)
            fields["_caption_truncated"] = True
    if fields:
        return fields
    raise json.JSONDecodeError("Could not salvage", text, 0)


def _write_post(folder: Path, post_text: str, post_type: str, hashtags: list[str],
                source_links: list[str], extras: dict | None = None) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "post.txt").write_text(post_text.strip() + "\n")
    meta = {
        "type": post_type,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "hashtags": hashtags,
        "source_links": source_links,
    }
    if extras:
        meta.update(extras)
    (folder / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")


def run(forced_type: str | None = None) -> None:
    DRAFTS.mkdir(exist_ok=True)
    post_type = pick_type(forced_type)
    if forced_type:
        print(f"→ Type (forced): {post_type}")
    else:
        print(f"→ Picked: {post_type}")

    print("→ Fetching sources...")
    sources = gather_all()

    print("→ Building prompt...")
    prompt, type_label, source_links = BUILDERS[post_type](sources)

    print("→ Calling LLM...")
    json_mode = post_type in ("type3_visual", "type4_koshish")
    output = llm_client.generate(
        prompt,
        system="You write LinkedIn posts in the author's voice. Output exactly what they should post.",
        max_tokens=4000,
        json_mode=json_mode,
    )

    today = datetime.now().strftime("%Y-%m-%d")
    folder = DRAFTS / f"{today}_{type_label}"

    if post_type == "type3_visual":
        try:
            data = _salvage_json(output)
        except Exception as e:
            print(f"⚠ JSON salvage failed: {e}")
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "raw.txt").write_text(output)
            return

        missing = [k for k in ("dont", "do") if not data.get(k, "").strip()]
        if missing:
            print(f"⚠ Missing {missing}. Saving raw.")
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "raw.txt").write_text(output)
            return

        caption = data.get("caption", "").strip()
        truncated = data.get("_caption_truncated", False)
        if not caption:
            caption = "[CAPTION MISSING - please write before posting]"
        elif truncated:
            caption += "\n\n[CAPTION TRUNCATED - please complete the last sentence]"

        post_body, hashtags = _extract_hashtags(caption)
        full_post = post_body + ("\n\n" + " ".join(hashtags) if hashtags else "")
        _write_post(
            folder=folder,
            post_text=full_post,
            post_type=type_label,
            hashtags=hashtags,
            source_links=source_links,
            extras={
                "topic": data.get("topic", ""),
                "dont": data["dont"],
                "do": data["do"],
                "caption_truncated": truncated,
            },
        )

        img_path = folder / "card.png"
        make_image.make_card(data["dont"], data["do"], img_path)
        print(f"✓ Draft ready: {folder}")
        print(f"  post.txt + card.png written")
        if truncated:
            print(f"  ⚠ Caption truncated - check post.txt before posting")
    elif post_type == "type4_koshish":
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            # Fall back to salvage for robustness
            try:
                data = _salvage_json(output)
            except Exception as e:
                print(f"⚠ Type 4 JSON parse failed: {e}")
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "raw.txt").write_text(output)
                return

        # Validate required fields
        title = data.get("title", "").strip()
        sections = data.get("sections", [])
        if not title or not sections:
            print(f"⚠ Type 4 missing title or sections. Saving raw.")
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "raw.txt").write_text(output)
            return

        # Validate each section has label and bullets
        valid_sections = []
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            label = sec.get("label", "").strip()
            bullets = sec.get("bullets", [])
            if label and bullets:
                valid_sections.append({"label": label, "bullets": bullets})
        if not valid_sections:
            print(f"⚠ Type 4 no valid sections after filtering. Saving raw.")
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "raw.txt").write_text(output)
            return

        caption = data.get("caption", "").strip()
        if not caption:
            caption = "[CAPTION MISSING - please write before posting]"

        # Pull clipart hints from the LLM (may be missing on older prompts)
        clipart_hints = data.get("clipart_hints", []) or []
        if not isinstance(clipart_hints, list):
            clipart_hints = []

        post_body, hashtags = _extract_hashtags(caption)
        full_post = post_body + ("\n\n" + " ".join(hashtags) if hashtags else "")
        _write_post(
            folder=folder,
            post_text=full_post,
            post_type=type_label,
            hashtags=hashtags,
            source_links=source_links,
            extras={
                "topic": data.get("topic", ""),
                "title": title,
                "sections": valid_sections,
                "closing_note": data.get("closing_note", ""),
                "clipart_hints": clipart_hints,
            },
        )

        img_path = folder / "card.png"
        make_koshish_card.make_card(
            title=title,
            sections=valid_sections,
            output_path=img_path,
            closing_note=data.get("closing_note") or None,
            clipart_hints=clipart_hints,
        )
        print(f"✓ Draft ready: {folder}")
        print(f"  post.txt + card.png written")
    else:
        # Type 1 & Type 2: prose response. We ask the LLM to include a
        # TOPIC: line at the start which we strip out and save to meta.json
        # for future dedup.
        topic, body = _extract_topic_tag(output)
        post_body, hashtags = _extract_hashtags(body)
        full_post = post_body + ("\n\n" + " ".join(hashtags) if hashtags else "")
        extras = {"topic": topic} if topic else None
        _write_post(
            folder=folder,
            post_text=full_post,
            post_type=type_label,
            hashtags=hashtags,
            source_links=source_links,
            extras=extras,
        )
        print(f"✓ Draft ready: {folder}")
        print(f"  post.txt written")
        if topic:
            print(f"  topic: {topic}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a LinkedIn post draft.")
    parser.add_argument(
        "--type", "-t", dest="type", default=None,
        help="Force a post type. Accepts a number (1-4), the full key "
             "(e.g. type4_koshish), or a keyword (e.g. koshish). "
             "If omitted, a type is picked at random by weight.")
    parser.add_argument(
        "--list-types", action="store_true",
        help="List the available post types and exit.")
    args = parser.parse_args()

    if args.list_types:
        print("Available post types:")
        for i, t in enumerate(TYPE_WEIGHTS.keys()):
            print(f"  {i + 1}  {t}  (weight {TYPE_WEIGHTS[t]})")
        raise SystemExit(0)

    run(forced_type=args.type)