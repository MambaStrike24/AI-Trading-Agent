"""Specialised agents powered by a lightweight local language model.

Each agent issues a structured prompt instructing the model to return JSON with
the fields ``summary`` and ``reasoning`` plus a role specific field.  The JSON is
parsed and surfaced to the caller as a normal dictionary which makes downstream
processing straightforward.
"""

from __future__ import annotations

import json
from typing import Any, Dict


class _BaseAgent:
    """Common helper to query the LLM and parse JSON responses."""

    name: str
    prompt_template: str

    def _query(self, symbol: str, extra_fields: str) -> Dict[str, Any]:
        try:  # Import lazily so missing dependencies do not break imports.
            from trading_bot import openai_client
        except Exception as exc:  # pragma: no cover - exercised when dependency missing
            raise ImportError("openai_client must be available to use agents") from exc

        prompt = self.prompt_template.format(symbol=symbol)
        prompt += (
            " Respond in JSON with keys: summary, reasoning, " + extra_fields
        )
        raw = openai_client.call_llm(prompt)
        data = json.loads(raw)
        data["agent"] = self.name
        data["symbol"] = symbol
        return data


class MarketAnalystAgent(_BaseAgent):
    """Generate market analysis for a ticker symbol."""

    name = "MarketAnalystAgent"

    def __init__(self, prompt_template: str | None = None) -> None:
        self.prompt_template = (
            prompt_template or "Provide a market analysis for {symbol}."
        )

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """Return a structured market analysis."""

        return self._query(symbol, "market_trend")

    def respond(self, symbol: str, history: Any | None = None) -> Dict[str, Any]:
        return self.analyze(symbol)


class RiskAdvisorAgent(_BaseAgent):
    """Assess investment risks for a ticker symbol."""

    name = "RiskAdvisorAgent"

    def __init__(self, prompt_template: str | None = None) -> None:
        self.prompt_template = (
            prompt_template or "Offer an investment risk assessment for {symbol}."
        )

    def assess(self, symbol: str) -> Dict[str, Any]:
        """Return a structured risk assessment."""

        return self._query(symbol, "risk_level")

    def respond(self, symbol: str, history: Any | None = None) -> Dict[str, Any]:
        return self.assess(symbol)


class NewsSummarizerAgent(_BaseAgent):
    """Summarise recent news for a ticker symbol."""

    name = "NewsSummarizerAgent"

    def __init__(self, prompt_template: str | None = None) -> None:
        self.prompt_template = (
            prompt_template
            or "Summarise the latest financial news affecting {symbol}."
        )

    def summarize(self, symbol: str) -> Dict[str, Any]:
        """Return a structured news summary."""

        return self._query(symbol, "headlines")

    def respond(self, symbol: str, history: Any | None = None) -> Dict[str, Any]:
        return self.summarize(symbol)


__all__ = ["MarketAnalystAgent", "RiskAdvisorAgent", "NewsSummarizerAgent"]

