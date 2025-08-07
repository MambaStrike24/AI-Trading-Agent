"""Unified wrapper around a language model.

This wrapper supports both:
1. A local fallback model (based on Hugging Face transformers, e.g., for testing)
2. The OpenAI API (used in production for real completions)

To keep the project self-contained for examples and tests, a tiny model is loaded
locally unless the environment is configured with an OpenAI API key.

The core interface is `call_llm(prompt: str) -> str`
"""

from __future__ import annotations

from typing import Any, Callable
import warnings
import os

USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))

if USE_OPENAI:
    import openai
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    _GENERATOR: Callable[[str], str] | None = None
    _USING_ECHO = False


    def _load_generator() -> Callable[[str], str]:
        try:
            from transformers import pipeline  # type: ignore
            pipe = pipeline("text-generation", model="hf-internal-testing/tiny-random-gpt2")

            def _gen(prompt: str, *, temperature: float = 0.7, max_new_tokens: int = 32) -> str:
                result = pipe(
                    prompt,
                    do_sample=True,
                    temperature=temperature,
                    max_new_tokens=max_new_tokens,
                )
                return result[0]["generated_text"]

            return _gen
        except Exception:
            warnings.warn("transformers not available, falling back to echo mode", RuntimeWarning)

            def _gen(prompt: str, **_: Any) -> str:
                return prompt

            return _gen

    _GENERATOR = _load_generator()


def call_llm(prompt: str, *, temperature: float = 0.7) -> str:
    """Generate text using either OpenAI or a local fallback model."""
    if USE_OPENAI:
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a helpful financial analysis assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    else:
        return _GENERATOR(prompt, temperature=temperature)

__all__ = ["call_llm"]
