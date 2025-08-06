"""Minimal wrapper around a local open-source language model.

The real project originally relied on the OpenAI API.  For the unit tests and
examples in this kata we instead use an entirely free approach based on the
`transformers` library.  The :func:`call_llm` function attempts to load a very
small model that ships with ``transformers`` and generates text locally.  If
``transformers`` (or its heavy dependencies such as ``torch``) are not
available, the function falls back to simply echoing the provided prompt.  This
keeps the project self-contained while still demonstrating how one might wire a
model into the rest of the system.
"""

from __future__ import annotations

from typing import Any, Callable
import warnings

_GENERATOR: Callable[[str], str] | None = None
_USING_ECHO = False


def _load_generator() -> Callable[[str], str]:
    """Load a tiny text generation pipeline.

    The function is separated out so tests can easily monkeypatch the loading
    mechanism.  ``transformers`` is imported lazily to avoid hard dependencies
    during module import.  If the library (or its required backend like
    ``torch``) is unavailable, a trivial echo generator is returned instead.
    """

    global _GENERATOR
    if _GENERATOR is not None:
        return _GENERATOR

    try:  # pragma: no cover - exercised in the import success path
        from transformers import pipeline  # type: ignore

        pipe = pipeline(
            "text-generation", model="hf-internal-testing/tiny-random-gpt2"
        )

        def _gen(prompt: str, *, temperature: float = 0.7, max_new_tokens: int = 32) -> str:
            result = pipe(
                prompt,
                do_sample=True,
                temperature=temperature,
                max_new_tokens=max_new_tokens,
            )
            return result[0]["generated_text"]

        _GENERATOR = _gen
    except Exception:  # pragma: no cover - fallback when transformers missing
        warnings.warn(
            "transformers not available, falling back to echo mode", RuntimeWarning
        )

        def _gen(prompt: str, **_: Any) -> str:
            return f"{prompt}"

        global _USING_ECHO
        _USING_ECHO = True
        _GENERATOR = _gen

    return _GENERATOR


def call_llm(prompt: str, *, temperature: float = 0.7) -> str:
    """Generate text using a local model.

    Parameters
    ----------
    prompt:
        The prompt to feed into the model.
    temperature:
        Sampling temperature used when generating text.

    Returns
    -------
    str
        The generated text.  If the model cannot be loaded, the prompt itself is
        echoed back.
    """

    generator = _load_generator()
    if _USING_ECHO:  # pragma: no cover - simple warning for echo mode
        warnings.warn("LLM dependencies missing, echoing prompt", RuntimeWarning)
    return generator(prompt, temperature=temperature)


__all__ = ["call_llm"]

