"""
Thin wrapper around Anthropic / Gemini / OpenAI.
Auto-selects provider based on which API key is set.
"""
import time
import os
from config import LLM_MODELS, LLM_PROVIDER
from dotenv import ad_dotenv

load_dotenv()

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

def _generate_with_retry(client, model_name, prompt, config,
                         max_attempts: int = 4,
                         base_delay: float = 8.0):
    """Call client.models.generate_content with automatic retry on 503.

    Gemini's free tier returns 503 UNAVAILABLE during demand spikes. These are
    transient. We back off and retry up to `max_attempts` times.

    Delays: 8s, 16s, 32s (caps at ~1 minute total wait before giving up).

    Other errors (400 bad request, auth failures, etc.) raise immediately.
    """
    # Import here to keep this helper module-light. In the real file, import
    # at the top: from google.genai.errors import ServerError
    try:
        from google.genai.errors import ServerError
    except ImportError:
        ServerError = Exception  # fallback for older SDK

    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            return client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
        except ServerError as e:
            # Only retry on 503 - other server errors (500, 502) might be
            # something fundamentally broken; retry those once just in case
            code = getattr(e, "code", None) or getattr(e, "status_code", None)
            is_retryable = code in (500, 502, 503, 504) or "UNAVAILABLE" in str(e)
            if not is_retryable or attempt >= max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))  # 8, 16, 32
            print(f"  ⚠ Gemini {code or 'transient'} error (attempt {attempt}/{max_attempts}). "
                  f"Retrying in {delay:.0f}s...")
            time.sleep(delay)
            last_err = e
        except Exception:
            # Non-server errors: don't retry
            raise

    # Shouldn't reach here, but just in case
    if last_err:
        raise last_err



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
        #client = genai.Client(api_key=os.environ["AIzaSyB3tCgRjrdIMFzRt0Y5KLvKzBCReDKDNLE"])
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
            response = _generate_with_retry(client, model, prompt, config)
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
