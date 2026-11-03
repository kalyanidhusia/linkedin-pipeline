# LinkedIn Pipeline — Command Reference

Last updated: 2026-10-22

Every CLI invocation for the pipeline, in one place. Written for your future
self at 11pm when you've forgotten what flags exist.

---

## Daily workflow

```bash
# 1. See what's available (fastest sanity check, no LLM call)
python scripts/generate_post.py --list-types

# 2. Generate a random weekly post (respects AVOID_REPEATS)
python scripts/generate_post.py

# 3. Open the draft, copy text, launch LinkedIn in browser
python scripts/post_now.py

# 4. After posting on LinkedIn in the browser, archive the draft
python scripts/post_now.py --archive
```

The `--archive` step is what tells `topic_dedup.py` "this topic is now covered,
don't suggest it again." Archive only after real posting, or dedup gets
miscalibrated.

---

## Forcing a specific post type

```bash
python scripts/generate_post.py --type 4              # by number
python scripts/generate_post.py --type koshish        # by keyword
python scripts/generate_post.py --type type4_koshish  # by full key
python scripts/generate_post.py -t 4                  # short flag
```

Type mapping:

| Flag value   | Full key          |
| ------------ | ----------------- |
| `1`          | `type1_update`    |
| `2`          | `type2_tip`       |
| `3`          | `type3_visual`    |
| `4`          | `type4_koshish`   |

See `POST_TYPES.md` for when to pick which.

Two behaviors to remember:
- `--type` **overrides `AVOID_REPEATS`**. If you ask for Type 4, you get Type 4
  even if last week was Type 4. Random path (no `--type`) still respects
  no-repeats.
- Bad input fails loudly. `--type 9`, `--type banana`, or `--type type`
  (ambiguous — matches all four) all print the valid options and exit without
  burning an LLM call.

---

## Project-grounded posts

```bash
python scripts/generate_post.py --project pxenrich
```

Scopes source material to beats inside `sources/projects/<name>.md` instead of
pulling broadly from `tips.md` / `idea_bank.md`. Pair with `--type` to control
both:

```bash
python scripts/generate_post.py --project pxenrich --type 1
```

Project files live in `sources/projects/`. Each is a markdown file of tagged
beats like:

```markdown
- ORIGIN | ProteomeXchange 2026 made me ask whether FAIR data is actually biologically reusable.
- METADATA GAP | 962 breast-cancer PRIDE datasets: subtype recoverable from free text in 32.4%, structurally exposed in 0.3%.
- FIRST BENCHMARK | 18-dataset proof: regex precision 0.78, LLM precision 0.71.
- ERBETA TRAP | PXD000499 — LLM inferred ER-positive from ERβ/ESR2 with confidence 1.0. ERβ ≠ ERα.
```

See `PROJECTS.md` for how to add a new one.

---

## Common one-liners

```bash
# Peek at available types + weights, no LLM call
python scripts/generate_post.py --list-types

# Force a tip-type post about pxEnrich
python scripts/generate_post.py --project pxenrich --type 2

# Random pick weighted by config
python scripts/generate_post.py

# After generating, open + archive together
python scripts/generate_post.py --type 4 && python scripts/post_now.py
# ...post it in the browser...
python scripts/post_now.py --archive
```

---

## Troubleshooting

### `anthropic.AuthenticationError: 401 - invalid x-api-key`
Your `ANTHROPIC_API_KEY` env var is unset, expired, or wrong. Check with
`echo $ANTHROPIC_API_KEY`. Regenerate at console.anthropic.com and update
your `~/.zshrc` or `.env`.

### `⚠ external_topics unavailable (No module named 'external_topics')`
Harmless — the module is optional and generation falls back to local sources.
If you want external topics (Biostars / StackOverflow / Medium), confirm
`scripts/external_topics.py` exists.

### `⚠ biostars: feed parse issue`
Biostars' RSS occasionally returns malformed XML. Wrapped in try/except on
purpose — ignore. StackOverflow and Medium feeds carry the load.

### `--list-types` shows only 3 types
`type4_koshish` is missing from `TYPE_WEIGHTS` in `scripts/config.py`. Add:
```python
TYPE_WEIGHTS = {
    "type1_update": 1.0,
    "type2_tip": 1.4,
    "type3_visual": 1.0,
    "type4_koshish": 1.2,
}
```

---

## What NOT to run

- Don't run `topic_dedup.py` or `external_topics.py` directly — they're
  imported modules, not standalone scripts.
- Don't re-run `--archive` on a draft that's already been archived. It won't
  break anything but it writes a confusing second log line.
- Don't push to `main` without `--list-types` passing locally first. CI is
  slow to catch config errors.
