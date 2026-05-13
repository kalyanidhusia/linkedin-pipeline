"""
Pick a post type, build the prompt, call the LLM, save the draft.
This is what the GitHub Action runs every Sunday.
"""

import json
import random
from datetime import datetime
from pathlib import Path

from config import AUTHOR, TYPE_WEIGHTS, AVOID_REPEATS, DRAFTS_DIR
from fetch_sources import gather_all
import llm_client
import make_image

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
DRAFTS = ROOT / DRAFTS_DIR


def _load(name: str) -> str:
    return (PROMPTS / name).read_text()


def _last_type() -> str | None:
    """What type did we post last week? (so we can avoid repeating)"""
    if not DRAFTS.exists():
        return None
    files = sorted(DRAFTS.glob("*.md"), reverse=True)
    if not files:
        return None
    name = files[0].stem  # e.g. 2026-05-04_type2_tip
    parts = name.split("_", 1)
    return parts[1] if len(parts) > 1 else None


def pick_type() -> str:
    """Weighted random pick, optionally avoiding last week's type."""
    types = list(TYPE_WEIGHTS.keys())
    weights = list(TYPE_WEIGHTS.values())
    if AVOID_REPEATS:
        last = _last_type()
        if last and last in types:
            i = types.index(last)
            weights[i] = 0
    return random.choices(types, weights=weights, k=1)[0]


def _author_block() -> str:
    """Render the author profile for the system prompt."""
    return (
        f"Author: {AUTHOR['name']}, {AUTHOR['title']} at {AUTHOR['affiliation']}.\n"
        f"Tagline: {AUTHOR['tagline']}\n"
        f"Expertise: {', '.join(AUTHOR['expertise'])}.\n"
        f"Audience: {AUTHOR['audience']}.\n"
        f"Voice traits:\n" + "\n".join(f"  - {t}" for t in AUTHOR["voice_traits"])
    )


def build_type1(sources: dict) -> tuple[str, str]:
    """Type 1: news/paper update."""
    candidates = (sources["biorxiv"] or [])[:8] + (sources["github"] or [])[:4]
    if not candidates:
        raise RuntimeError("No bioRxiv or GitHub items fetched. Try again later.")
    candidates_str = "\n\n".join(
        f"[{i + 1}] ({c['source']}) {c['title']}\n    {c.get('summary', '')[:300]}\n    {c['link']}"
        for i, c in enumerate(candidates)
    )
    voice = _load("voice_examples.md")
    template = _load("type1_update.md")
    prompt = template.format(
        author=_author_block(),
        voice_examples=voice,
        candidates=candidates_str,
    )
    return prompt, "type1_update"


def build_type2(sources: dict) -> tuple[str, str]:
    """Type 2: practical tip for students."""
    tips = sources["tips"]
    ideas = sources["idea_bank"]
    if not tips and not ideas:
        raise RuntimeError("Add at least a few tips to sources/tips.md")
    pool = tips + [i["title"] for i in ideas]
    pool_str = "\n".join(f"- {t}" for t in pool)
    voice = _load("voice_examples.md")
    template = _load("type2_tip.md")
    prompt = template.format(
        author=_author_block(),
        voice_examples=voice,
        topic_pool=pool_str,
    )
    return prompt, "type2_tip"


def build_type3(sources: dict) -> tuple[str, str]:
    """Type 3: do/don't visual."""
    pairs = sources["dos_donts"]
    if not pairs:
        raise RuntimeError("Add at least one pair to sources/dos_donts.md")
    pool_str = "\n".join(
        f"- {p['dont']} | {p['do']}" for p in pairs
    )
    voice = _load("voice_examples.md")
    template = _load("type3_visual.md")
    prompt = template.format(
        author=_author_block(),
        voice_examples=voice,
        topic_pool=pool_str,
    )
    return prompt, "type3_visual"


BUILDERS = {
    "type1_update": build_type1,
    "type2_tip": build_type2,
    "type3_visual": build_type3,
}


def parse_visual_output(raw: str) -> dict:
    """Type 3 output is JSON with caption + dont + do."""
    # Strip markdown fences if the model added them
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


def run() -> None:
    DRAFTS.mkdir(exist_ok=True)
    post_type = pick_type()
    print(f"→ Picked: {post_type}")

    print("→ Fetching sources...")
    sources = gather_all()

    print("→ Building prompt...")
    prompt, type_label = BUILDERS[post_type](sources)

    print("→ Calling LLM...")
    output = llm_client.generate(
        prompt,
        system="You write LinkedIn posts in the author's voice. Output exactly what they should post, no preamble.",
        max_tokens=1500,
    )

    today = datetime.now().strftime("%Y-%m-%d")
    base = DRAFTS / f"{today}_{type_label}"

    if post_type == "type3_visual":
        try:
            data = parse_visual_output(output)
        except Exception as e:
            print(f"⚠ Could not parse JSON, saving raw: {e}")
            base.with_suffix(".md").write_text(output)
            return

        # Save the post text
        md = (
            f"# Type 3: Visual do/don't post\n\n"
            f"**Topic:** {data.get('topic', '')}\n\n"
            f"## LinkedIn caption\n\n{data['caption']}\n\n"
            f"## Card content\n\n"
            f"- DON'T: {data['dont']}\n"
            f"- DO: {data['do']}\n\n"
            f"![card](./{base.name}.png)\n"
        )
        base.with_suffix(".md").write_text(md)

        # Render the image
        img_path = base.with_suffix(".png")
        make_image.make_card(data["dont"], data["do"], img_path)
        print(f"✓ Wrote: {base.with_suffix('.md').name} + {img_path.name}")
    else:
        md = f"# {post_type}\n\n## LinkedIn post draft\n\n{output}\n"
        base.with_suffix(".md").write_text(md)
        print(f"✓ Wrote: {base.with_suffix('.md').name}")


if __name__ == "__main__":
    run()
