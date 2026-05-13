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


def generate(prompt: str, system: str = "", max_tokens: int = 1500) -> str:
    """Send prompt, return text. Raises on error."""
    provider = _detect_provider()
    model = LLM_MODELS[provider]

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    if provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model_obj = genai.GenerativeModel(
            model_name=model,
            system_instruction=system or None,
        )
        response = model_obj.generate_content(
            prompt,
            generation_config={"max_output_tokens": max_tokens, "temperature": 0.7},
        )
        return response.text

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    raise ValueError(f"Unknown provider: {provider}")


if __name__ == "__main__":
    # Smoke test
    out = generate("Say hello in one short sentence.", system="You are concise.")
    print(out)
