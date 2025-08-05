"""Wrapper around OpenAI's ChatCompletion API."""

from __future__ import annotations

import os
from typing import Any

import openai
from openai.error import OpenAIError, RateLimitError


def call_openai(prompt: str) -> str:
    """Send ``prompt`` to OpenAI and return the model's reply.

    Parameters
    ----------
    prompt:
        Text prompt to send to the model.

    Returns
    -------
    str
        The text of the model's response.

    Raises
    ------
    ValueError
        If ``OPENAI_API_KEY`` is not set in the environment.
    RuntimeError
        If the OpenAI API returns an error.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    openai.api_key = api_key

    try:
        response: Any = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
    except RateLimitError as exc:
        raise RuntimeError("OpenAI API rate limit exceeded") from exc
    except OpenAIError as exc:
        raise RuntimeError(f"OpenAI API error: {exc}") from exc

    return response.choices[0].message["content"].strip()


__all__ = ["call_openai"]
