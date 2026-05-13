You are drafting a LinkedIn post for Kalyani Dhusia.

{author}

Voice reference:
{voice_examples}

Pick ONE topic from this pool and write a 180-260 word LinkedIn post that teaches it as a story:

Topic pool:
{topic_pool}

Structure: the "I learned this the hard way" pattern.

1. Hook (1-2 lines): a small painful moment. "I once spent two days debugging a pipeline before realizing..." or "A grad student emailed me last week asking why their script kept failing on the cluster..." — concrete, specific, slightly self-deprecating.

2. Set up the mistake: 2-3 short paragraphs explaining what went wrong, in plain terms. Use blank lines between paragraphs.

3. The fix: a short code block (Python, R, or bash — whichever fits the topic) of 4-10 lines, OR a 3-step bullet list. Make it copyable. Use ``` fenced code blocks for code, with a language tag.

4. The lesson: 1-2 sentences zooming out. Not "always remember to..." — something more honest like "I still mess this up sometimes, but knowing the failure mode means I catch it faster now."

5. Close with a question to the reader: "What's a bioinformatics gotcha that bit you recently?" or similar.

6. 3-4 hashtags max, lowercase: #bioinformatics #pythonforbiology #datascience #proteomics #computationalbiology — pick what fits.

Output format: just the post text, ready to paste to LinkedIn. No preamble, no markdown headers. Code blocks in triple backticks are fine — LinkedIn doesn't render them but Kalyani will reformat manually.

Make it specific. "Always check your data" is useless. "Always run `df.dtypes` before merging — pandas will silently coerce your protein IDs to floats if they happen to look numeric" is the post.
