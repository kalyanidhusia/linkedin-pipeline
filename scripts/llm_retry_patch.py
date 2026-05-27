"""
Patch instructions for scripts/llm_client.py to retry on 503 (UNAVAILABLE) errors.

Find this section in your current llm_client.py (around line 50-80 for the Gemini
branch where `client.models.generate_content` is called) and replace the single
generate_content call with a retry loop.

BEFORE:
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )

AFTER:
    response = _generate_with_retry(client, model_name, prompt, config)


Then add this helper function somewhere in the same file (top-level, before
the `generate` function):
"""

import time

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
