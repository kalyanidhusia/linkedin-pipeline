# LinkedIn Zero-Friction Content Pipeline

Weekly LinkedIn posts in your voice (proteomics, multi-omics, ML), drafted by an LLM and shipped via GitHub Actions. You approve, you post.

## What it does

Every Sunday morning, a GitHub Action:
1. Pulls fresh items from bioRxiv (proteomics + multi-omics + ML), GitHub trending repos, and your idea bank
2. Picks one of three post types (round-robin with light variation)
3. Generates a draft post in your voice using Claude / Gemini / OpenAI
4. For Type 3 (visual), also generates a do/don't card image with your photo
5. Opens a Pull Request with the draft for you to review, edit, and merge

You read the PR on your phone, tweak if needed, and paste to LinkedIn. Total time: ~5 minutes per week.

## The three post types

| Type | What | Example trigger |
|------|------|-----------------|
| 1. Update | Recent paper / news in proteomics-multi-omics-ML, explained simply | New bioRxiv preprint |
| 2. Tip | Practical bioinformatics gotcha for students | Item from `tips.md` |
| 3. Visual | Do/don't card with your photo + punchy caption | Item from `dos_donts.md` |

## Quick start

```bash
# 1. Clone this repo to your own GitHub (private)
# 2. Add a headshot to templates/headshot.png
# 3. Add an LLM API key as a GitHub secret (one of):
#    - ANTHROPIC_API_KEY
#    - GEMINI_API_KEY
#    - OPENAI_API_KEY
# 4. Edit author profile in scripts/config.py
# 5. Edit voice examples in prompts/voice_examples.md
# 6. Run locally to test: python scripts/generate_post.py
# 7. Push. The weekly schedule kicks in.
```

## Cost

$0 if you use Gemini's free tier or stay under Anthropic's free credits. GitHub Actions free tier covers this with thousands of minutes to spare.

## Files

```
scripts/
  config.py              # Your profile, API keys, schedule
  fetch_sources.py       # bioRxiv RSS, GitHub trending, idea bank
  generate_post.py       # Picks type, calls LLM, saves draft
  make_image.py          # Pillow renders Type 3 visual card
  llm_client.py          # Wraps Anthropic/Gemini/OpenAI
prompts/
  voice_examples.md      # Your past posts as style reference
  type1_update.md        # Prompt for news/paper posts
  type2_tip.md           # Prompt for tutorial posts
  type3_visual.md        # Prompt for do/don't visual posts
sources/
  idea_bank.md           # Free-form post ideas you jot down
  tips.md                # Recurring undergrad mistakes
  dos_donts.md           # Do/don't pairs for Type 3
templates/
  headshot.png           # Your photo (transparent background ideal)
drafts/
  YYYY-MM-DD_typeN.md    # Generated drafts, one per week
.github/workflows/
  weekly.yml             # Sunday cron, opens PR with draft
```
