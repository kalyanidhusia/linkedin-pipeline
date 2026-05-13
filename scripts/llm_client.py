"""
Thin wrapper around Anthropic / Gemini / OpenAI.
Auto-selects provider based on which API key is set.
"""

import os
from config import LLM_MODELS, LLM_PROVIDER


def _detect_provider() -> str:
    """Pick provider based on env vars, in priority order."""
    if LLM_PROVIDER != "auto":
        return LLM_PROVIDER
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    raise RuntimeError(
        "No LLM API key found. Set one of: ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY"
    )


def generate(prompt: str, system: str = "", max_tokens: int = 1500,
             json_mode: bool = False) -> str:
    """Send prompt, return text. Raises on error.

    json_mode=True asks the provider to return strictly valid JSON.
    Use this for Type 3 posts where we need parseable output.
    """
    provider = _detect_provider()
    model = LLM_MODELS[provider]

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        sys_msg = system or "You are a helpful assistant."
        if json_mode:
            sys_msg += "\n\nReturn ONLY a single valid JSON object. No markdown, no preamble."
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=sys_msg,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    if provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        config_kwargs = {
            "system_instruction": system or None,
            "max_output_tokens": max_tokens,
            "temperature": 0.7,
        }
        if json_mode:
            # Forces Gemini to return strictly valid JSON. Big reliability win.
            config_kwargs["response_mime_type"] = "application/json"
        config = types.GenerateContentConfig(**config_kwargs)
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            msg = str(e)
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "quota" in msg.lower():
                raise RuntimeError(
                    f"Gemini quota issue: '{model}' returned a quota error.\n"
                    f"  1. Switch model in config.py to 'gemini-2.5-flash'\n"
                    f"  2. Or use a key from a personal Gmail (not institutional)\n"
                    f"Raw: {msg[:300]}"
                ) from e
            raise

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    raise ValueError(f"Unknown provider: {provider}")


if __name__ == "__main__":
    out = generate("Say hello in one short sentence.", system="You are concise.")
    print(out)
