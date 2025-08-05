from __future__ import annotations

"""Lightweight agent that queries an LLM for market commentary.

The agent relies on :mod:`trading_bot.openai_client` to interact with OpenAI's
API.  The text response from the model is wrapped into a small structured
dictionary so it fits the common interface used across the project.
"""

from typing import Dict


class LLMAgent:
    """Generate a brief analysis for a ticker symbol using a language model."""

    def analyze(self, symbol: str) -> Dict[str, str]:
        """Return an LLM-generated summary for ``symbol``.

        The method crafts a prompt referencing ``symbol`` and delegates the
        request to :func:`trading_bot.openai_client.call_openai`.  The raw text
        reply from the model is packaged into a simple dictionary alongside a
        one-line summary extracted from the response.
        """

        try:  # Import lazily so missing dependencies don't break module import.
            from trading_bot import openai_client
        except Exception as exc:  # pragma: no cover - exercised when dependency missing
            raise ImportError(
                "openai_client (and openai) must be available to use LLMAgent"
            ) from exc

        prompt = f"Provide a concise investment summary for the stock symbol {symbol}."
        raw_response = openai_client.call_openai(prompt)
        summary = raw_response.strip().splitlines()[0] if raw_response else ""

        return {
            "agent": "LLMAgent",
            "symbol": symbol,
            "summary": summary,
            "raw_response": raw_response,
        }


__all__ = ["LLMAgent"]
