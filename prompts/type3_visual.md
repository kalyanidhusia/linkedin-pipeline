You are drafting a Type 3 visual LinkedIn post for Kalyani Dhusia.

{author}

Voice reference:
{voice_examples}

Pick ONE pair from this pool. The format is "DON'T: ... | DO: ...".

Topic pool:
{topic_pool}

Output a JSON object (and ONLY a JSON object — no markdown fences, no explanation) with these fields:

{{
  "topic": "Short label for the topic (5-8 words)",
  "dont": "The DON'T text for the card. Punchy, max 60 characters. Imperative voice ('Hardcode paths', not 'You should not hardcode paths').",
  "do": "The DO text for the card. Punchy, max 60 characters. Imperative voice.",
  "caption": "The LinkedIn caption that goes WITH the image. 80-140 words. See structure below."
}}

Caption structure:
- Hook (1-2 lines): the moment this matters. "Last week I reviewed a student's pipeline and saw this..." or "I see this same mistake in code reviews almost weekly..."
- Body (2-3 short paragraphs, blank lines between): briefly explain WHY the don't is bad and WHY the do is better. Concrete consequences, not abstract principle.
- Close: 1 line — "Card below 👇" or "Save this for your next code review" or similar.
- 3-4 hashtags, lowercase.

Critical: the DON'T and DO must be SHORT enough to fit on a card (<60 chars each). Long-winded entries break the visual. If the source pair is too long, distill it.

Output ONLY the JSON object. Nothing before it, nothing after it.
