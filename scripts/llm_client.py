import os
import random
import time

from google import genai
from google.genai import types
from google.genai.errors import APIError


# Only models currently intended for this $0 pipeline.
# Order = preference order.
MODEL_CANDIDATES = (
    "gemini-3.8-flash",
    "gemini-3.6-flash",
)


def _client() -> genai.Client:
    key = os.getenv("GEMINI_API_KEY")

    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    return genai.Client(api_key=key)


def _available_generate_models(client: genai.Client) -> set[str]:
    """
    Ask Gemini which models THIS API project can actually use
    with generateContent.
    """
    available = set()

    for model in client.models.list():
        actions = model.supported_actions or []

        if "generateContent" not in actions:
            continue

        name = model.name or ""

        # API normally returns models/gemini-x
        if name.startswith("models/"):
            name = name.removeprefix("models/")

        available.add(name)

    return available


def _select_model(client: genai.Client) -> str:
    available = _available_generate_models(client)

    for candidate in MODEL_CANDIDATES:
        if candidate in available:
            print(f"  ✓ Gemini model selected: {candidate}")
            return candidate

    relevant = sorted(
        name for name in available
        if name.startswith("gemini-")
    )

    raise RuntimeError(
        "None of the approved free-tier Gemini models are available "
        "to this API project.\n"
        f"Tried: {', '.join(MODEL_CANDIDATES)}\n"
        f"generateContent models visible to this key:\n"
        + "\n".join(f"  - {m}" for m in relevant)
    )


def _generate_with_retry(
    client: genai.Client,
    model: str,
    prompt: str,
    config: types.GenerateContentConfig,
    max_attempts: int = 5,
):
    """
    Retry only transient/quota errors.

    404 is NOT retried because it indicates an invalid/unavailable model.
    400 auth/request errors are NOT retried.
    """

    for attempt in range(1, max_attempts + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )

        except APIError as exc:
            code = getattr(exc, "code", None)

            retryable = code in (429, 500, 502, 503, 504)

            if not retryable:
                raise

            if attempt == max_attempts:
                raise RuntimeError(
                    f"Gemini failed after {max_attempts} attempts "
                    f"with model {model}: {exc}"
                ) from exc

            # 15, ~30, ~60, ~120 sec plus small jitter
            delay = 15 * (2 ** (attempt - 1))
            delay += random.uniform(0, 3)

            print(
                f"  ⚠ Gemini {code} on {model}; "
                f"retry {attempt}/{max_attempts} "
                f"in {delay:.1f}s"
            )

            time.sleep(delay)


def generate(
    prompt: str,
    system: str = "",
    max_tokens: int = 4000,
    json_mode: bool = False,
) -> str:

    client = _client()
    model = _select_model(client)

    kwargs = {
        "system_instruction": system or None,
        "max_output_tokens": max_tokens,
        "temperature": 0.7,
    }

    if json_mode:
        kwargs["response_mime_type"] = "application/json"

    config = types.GenerateContentConfig(**kwargs)

    response = _generate_with_retry(
        client=client,
        model=model,
        prompt=prompt,
        config=config,
    )

    if not response.text:
        raise RuntimeError(
            f"Gemini returned an empty response from {model}"
        )

    return response.text
