# LinkedIn Pipeline — Project-Grounded Posts

Last updated: 2026-10-22

How `--project <name>` works and how to add a new project source.

---

## What it does

`--project pxenrich` tells the generator to pull source material from
`sources/projects/pxenrich.md` instead of (or alongside) the broad pools in
`sources/tips.md` and `sources/idea_bank.md`.

Result: the post is grounded in specific, real work on that project — real
numbers, real failure modes, real decisions — instead of generic tips.

---

## Current project files

```
sources/projects/
└── pxenrich.md
```

More to add as projects mature:
- `cardio-pxenrich.md` — cardiovascular counterpart (planned)
- `proteovar.md` — pipeline work
- `bio-arcade.md` — teaching artifact
- `reviewer-analytics.md` — the service portfolio project

---

## File format — the "beat" pattern

Each line is one beat, tagged with a short all-caps label:

```markdown
# pxEnrich series

- ORIGIN | ProteomeXchange 2026 made me ask whether FAIR and public proteomics data are actually biologically reusable. Published anchor: 64,330 submitted datasets; 47% submitted in the previous three years.

- METADATA GAP | Preliminary scan of 962 human breast-cancer PRIDE datasets: molecular subtype was recoverable from free text in 32.4%, but structurally exposed in only 0.3%. Message: the metadata often exists, but machines cannot reliably see it.

- FIRST BENCHMARK | 18-dataset proof of concept. Regex precision 0.78, recall 0.70, correct abstention 0.88. Initial LLM precision 0.71, recall 0.50, correct abstention 0.75. Do not frame as universal model performance.

- ERBETA TRAP | PXD000499 discussed ERβ/ESR2. An off-the-shelf LLM inferred clinical ER-positive disease with confidence 1.0. Biological lesson: ERβ/ESR2 is not equivalent to clinical ERα/ESR1 receptor status.
```

Each beat should be:
- **Self-contained** — makes sense without the beats around it
- **Specific** — real numbers, real identifiers, real quotes
- **One idea** — if it has two, split into two beats
- **Postable on its own** — any beat should be enough material for a Type 1 or
  Type 2 post about this project

---

## Writing good beat tags

The tag is the hook. Keep it short, specific, and memorable:

Good tags: `ORIGIN`, `METADATA GAP`, `FIRST BENCHMARK`, `ERBETA TRAP`,
`STUDENT HANDOFF`, `MCP SERVER`, `18-DATASET PROOF`

Weak tags: `NOTES`, `MISC`, `THOUGHTS`, `UPDATE 1`, `TODO`

The tag doubles as a mental index — a year from now when you're skimming the
file to remember what happened, the tags are what you'll read first.

---

## Adding a new project

Three steps:

### 1. Create the file

```bash
cd ~/Desktop/PROJECTS/linkedin-pipeline
touch sources/projects/<slug>.md
```

Use kebab-case for the slug (matches the `--project` flag value).

### 2. Fill in beats

Open the file and add the "beat" lines as above. Start with 3–5 beats; add
more as the project evolves. A project file with fewer than 3 beats won't give
the LLM enough to work with.

### 3. Verify

```bash
python scripts/generate_post.py --project <slug>
```

If the slug isn't found, the generator should say so. If it generates but the
post feels generic, add more specific beats.

---

## How to combine with --type

Project scoping + type forcing stack:

```bash
# Update post about pxEnrich
python scripts/generate_post.py --project pxenrich --type 1

# Tip-shaped lesson from pxEnrich work
python scripts/generate_post.py --project pxenrich --type 2

# Do/don't card from pxEnrich lessons
python scripts/generate_post.py --project pxenrich --type 3

# Koshish-style notebook from a pxEnrich moment
python scripts/generate_post.py --project pxenrich --type 4
```

Without `--type`, the random pick runs weighted-at-random as usual, and the
project constraint narrows which beats it draws from.

---

## When NOT to use --project

- You want to write about something cross-cutting, not one project
- The project doesn't have a `.md` file yet in `sources/projects/`
- You're writing a reflection post that touches multiple projects (use the
  broad pools; write manually if needed)
- The post is really about a trend, not your work on it

---

## Known rough edges

- No per-beat dedup against `drafts/posted/` yet. If you post the same beat
  twice, nothing stops you. Keep an eye on tags you've already posted.
- The generator doesn't currently show you which beat it picked. If you want
  that, add a `print(f"→ Beat: {beat_tag}")` in the project loader.
- If a project file is missing, the error message isn't super friendly yet.
  Falls back to broad sources with a warning.
