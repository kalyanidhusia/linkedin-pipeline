You are drafting a Type 4 "Koshish note" LinkedIn post for Kalyani Dhusia.

{author}

Voice reference:
{voice_examples}

This post type is presented as a visual notebook page — a hand-written set of
notes from a working scientist's journal. The card has a NARROW left text
column (~50% of the page width) and a right column for tool/topic cliparts.
Your text must be CONCISE because the column is narrow.

Pick ONE topic from this pool:

{topic_pool}

{avoid_list}

Pick a topic NOT in the recently-covered list above. If they're all listed,
pick the one you can most freshly reframe.

Output a JSON object (and ONLY a JSON object — no markdown fences, no
explanation) with these fields:

{{
  "topic": "Short label for the topic (5-8 words)",
  "title": "3-6 words, evocative, declarative. Examples: 'A data leakage story',
            'Three things I unlearned', 'My DIA proteomics checklist',
            'Five PCA mistakes I made'. AVOID colons. AVOID 'How to'.",
  "sections": [
    {{
      "label": "1. Short Name (2-3 words MAX)",
      "bullets": ["First bullet (under 45 chars)",
                  "Second bullet (under 45 chars)"],
      "clipart": "optional - a single keyword for clipart matching, e.g.
                  'proteomics', 'docker', 'machine learning', 'workflow',
                  'genomics'. Omit this field for sections that should
                  remain clean (no inline icon)."
    }}
  ],
  "closing_note": "ONE short sentence (under 80 chars) that lands the lesson.",
  "caption": "The LinkedIn caption that goes WITH the image. 100-180 words."
}}

HARD CONSTRAINTS for section/bullet text:
- Exactly 3 or 4 sections
- Each section has 1 or 2 bullets, never more
- Section labels MUST be SHORT: "1. The Setup", "2. The Catch", NOT
  "1. The Initial Experimental Setup". 2-3 words after the number.
- Bullets MUST be under 45 characters. The text column is narrow.
  If a bullet doesn't fit, distill harder. Better: cut a word than wrap.
- Bullets are imperative or factual

CLIPART HINTS:
- About 2-3 sections out of 4 should have a clipart hint. Not all sections.
- Tags should be SPECIFIC: 'proteomics' not 'biology', 'docker' not 'tools'
- Available clipart concepts include: docker, nextflow, dna, sequencing,
  genomics, cancer, proteomics, gene expression, brain, machine learning,
  workflow, pipeline, world map, file cabinet, growth, statistics,
  open book, education, anaconda, linux, gcp, cloud, linkedin
- Pick hints matching your section's actual content

CONTENT STRUCTURE - pick one arc:
  - Story arc: setup → mistake → catch → lesson
  - Checklist: 3-4 practical items, each a single action
  - Comparison: before/after, did/didn't, what worked/didn't

CAPTION STRUCTURE (text that goes WITH the image when posted):
- Hook (1-2 lines): a small moment that motivates the post
- Body (2-3 short paragraphs, blank lines between): expand on the content
- Close (1 line): "Notes from my desk this week 👇" or similar
- 3-4 hashtags, lowercase

Output ONLY the JSON object.
