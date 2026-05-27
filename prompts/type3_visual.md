You are drafting a Type 3 "do/don't visual" LinkedIn post for Kalyani Dhusia.

{author}

Voice reference:
{voice_examples}

Pick ONE pair from this pool and write the post. Each line is "DON'T | DO".

Topic pool:
{topic_pool}

{avoid_list}

Avoid pairs that overlap with the recently-covered list above.

Output a JSON object (and ONLY a JSON object — no markdown fences, no
explanation) with these fields:

{{
  "topic": "Short 5-10 word label for this lesson",
  "dont": "The 'don't' statement, under 60 chars. Will be displayed
           on a card as a bold short statement.",
  "do": "The 'do' alternative, under 60 chars.",
  "caption": "The LinkedIn caption that goes with the image card.
              100-180 words, structured as hook + body + close.
              End with 3-4 lowercase hashtags on the last line."
}}

The "dont" and "do" must be SHORT - they get rendered as large text on a card,
so brevity matters more than precision.

Output ONLY the JSON object.
