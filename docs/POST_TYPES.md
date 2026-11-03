# LinkedIn Pipeline — Post Types

Last updated: 2026-10-22

Four post types. Each one serves a different purpose. This file exists so you
remember what each one is for when you're deciding whether to force one with
`--type`.

---

## Type 1 — Update

**Full key:** `type1_update` · **CLI:** `--type 1` · **Weight:** 1.0

**What it is:** A "here's what's new" post. 100–200 words. Reports an event,
a finding, a release, or a signal from the field.

**Picks from:** `sources/idea_bank.md` + external topics (Biostars, SO, Medium)

**Pick this when:**
- A paper came out that's worth signaling
- You shipped a release (ProteoVar version, new MCP tool, Bio Arcade module)
- You hit a milestone worth marking (grant panel done, course launched)
- An industry trend intersects with your work

**Don't use for:**
- Opinion posts (use a manual post, not the pipeline)
- Personal reflections (use Type 4)
- Tutorial content (use Type 2)

**Length:** Short. The signal is the content, not the writing.

---

## Type 2 — Tip

**Full key:** `type2_tip` · **CLI:** `--type 2` · **Weight:** 1.4 (highest)

**What it is:** A short technical lesson. One concrete gotcha, one concrete
fix. Written as a story so people stop scrolling.

**Picks from:** `sources/tips.md`

**Pick this when:**
- You just debugged something non-obvious and want to save others the pain
- You want to show technical depth without self-promotion
- You want the highest-engagement post type (tips reliably outperform updates)
- The weekly post has no other obvious hook

**Example openings that work:**
- "I once spent a frustrating afternoon trying to figure out why..."
- "Here's a trap that costs people a day of debugging:"
- "If your [tool] is returning [weird thing], check [non-obvious cause]."

**Don't use for:**
- Tips without a specific lesson (dilutes future tip posts)
- Content that would work better as a tutorial or blog post

**Weight is 1.4** because tips are consistently your best-performing format
and the pool is deep.

---

## Type 3 — Visual (Do/Don't card)

**Full key:** `type3_visual` · **CLI:** `--type 3` · **Weight:** 1.0

**What it is:** A paired do/don't card with your headshot. Short caption,
image carries the message.

**Picks from:** `sources/dos_donts.md`

**Outputs:** `post.txt` + `card.png`

**Pick this when:**
- You want visual impact in the feed (images outperform text for stopping scroll)
- The lesson fits a strict do-vs-don't shape (not every lesson does)
- You want a post that works even if someone doesn't read the caption

**Don't use for:**
- Nuanced advice that needs "it depends" (the card format forces a binary)
- Topics where you're not sure the don't is actually wrong

**Known rough edges:**
- `card.png` on CI renders in fallback fonts (Caveat isn't installed on the
  Linux runner). Re-render locally before posting if the font matters.
- Needs `rembg` for headshot cutout — occasionally fails to install cleanly on
  CI. Skip the card on CI, generate it on Mac.

---

## Type 4 — Koshish (notebook card)

**Full key:** `type4_koshish` · **CLI:** `--type 4` · **Weight:** 1.2

**What it is:** The Koshish-branded notebook card. Handwritten-feel typography
on a lined-notebook backdrop with cliparts and a signature. Teaches one small
scientific concept the way you'd scribble it for a student.

**Picks from:** `sources/tips.md` (shared with Type 2 but formatted differently)

**Outputs:** `post.txt` + `card.png` (notebook-style)

**Pick this when:**
- The lesson has 3–5 clean steps that fit a numbered list
- You want to lean into the Koshish brand ("an attempt, an effort")
- The audience benefits from "this is how I'd teach it" framing
- You want the post to feel personal, not clinical

**Example topics that fit:**
- "The Silent Data Leak" (normalize before vs. after split)
- Bias–variance intuitions
- A single bioinformatics gotcha explained like a tutor would

**Don't use for:**
- Topics that need multiple images or a long walkthrough (use a blog post)
- Serious or difficult emotional subjects (the handwritten feel is wrong for those)

**Known rough edges:**
- Same font + rembg caveats as Type 3
- The clipart manifest must be in sync with `templates/cliparts/`

---

## How weights work (random mode)

When you run `python scripts/generate_post.py` without `--type`, it picks
weighted-at-random from `TYPE_WEIGHTS` in `scripts/config.py`:

| Type              | Weight | Relative frequency |
| ----------------- | -----: | -----------------: |
| `type1_update`    | 1.0    | ~21%               |
| `type2_tip`       | 1.4    | ~29%               |
| `type3_visual`    | 1.0    | ~21%               |
| `type4_koshish`   | 1.2    | ~25%               |

Totals 4.6; each type's share is its weight / 4.6.

The random path also respects `AVOID_REPEATS` — if last week was Type 4, Type 4
is excluded from the random pool this week. `--type 4` ignores this and gives
you Type 4 anyway.

---

## Which type should you force?

Decision shortcut:

- Just want a weekly post, nothing specific in mind → **random** (no `--type`)
- Something new happened in the field or your work → **Type 1**
- You debugged something interesting this week → **Type 2**
- You want visual impact and have a clean do/don't → **Type 3**
- You want to teach one small thing, Koshish-style → **Type 4**
- You're writing about a specific project → add `--project <name>` on top of
  whichever type fits (see `PROJECTS.md`)
