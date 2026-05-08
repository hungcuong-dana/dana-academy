"""Thin wrapper around the OpenAI SDK for one-shot prompt → text calls.

Used by the parent-portal weekly assessment job. Kept small and dependency-free
so it can be reused elsewhere if needed without dragging in the chatbot stack.
"""
from __future__ import annotations

from django.conf import settings


_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI

        api_key = getattr(settings, "OPENAI_API_KEY", None)
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set in local_settings.py — "
                "cannot call OpenAI."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def call_openai(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> dict:
    """Send a single user prompt, return the assistant text + usage stats.

    Returns: {'text': str, 'prompt_tokens': int, 'completion_tokens': int, 'model': str}
    """
    model = model or getattr(settings, "OPENAI_MODEL_PARENT", "gpt-4o-mini")
    resp = _get_client().chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return {
        "text": resp.choices[0].message.content or "",
        "prompt_tokens": resp.usage.prompt_tokens,
        "completion_tokens": resp.usage.completion_tokens,
        "model": model,
    }
