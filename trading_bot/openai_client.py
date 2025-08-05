"""Lightweight wrapper around OpenAI's ChatCompletion API."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError, RateLimitError

def ensure_api_key() -> None:
    """Load ``OPENAI_API_KEY`` from ``.env`` or prompt the user."""
    # load_dotenv()
    
    # if not os.getenv("OPENAI_API_KEY"):
    #     os.environ["OPENAI_API_KEY"] = getpass("Enter OpenAI API key: ")

    # Dynamically find the root project directory and load .env
    project_root = Path(__file__).resolve().parent.parent  # adjust depth as needed
    dotenv_path = project_root / ".env"
    load_dotenv(dotenv_path=dotenv_path)

    # print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

def call_openai(prompt: str, *, temperature: float = 0.7) -> str:
    """Send ``prompt`` to OpenAI and return the model's reply.

    Parameters
    ----------
    prompt:
        Text prompt to send to the model.
    temperature:
        Sampling temperature to use for the completion.

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
    ensure_api_key()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
    except RateLimitError as exc:
        raise RuntimeError("OpenAI API rate limit exceeded") from exc
    except OpenAIError as exc:
        raise RuntimeError(f"OpenAI API error: {exc}") from exc

    return response.choices[0].message.content.strip()


__all__ = ["call_openai", "ensure_api_key"]
