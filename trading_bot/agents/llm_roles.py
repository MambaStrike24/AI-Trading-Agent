from __future__ import annotations

"""Specialized LLM-backed agents for different market research roles."""

from typing import Dict


class MarketAnalystAgent:
    """Generate market analysis for a ticker symbol."""

    def __init__(self, prompt_template: str = "Provide a market analysis for {symbol}.") -> None:
        self.prompt_template = prompt_template

    def analyze(self, symbol: str) -> Dict[str, str]:
        """Return a market analysis for ``symbol`` using an LLM."""
        try:  # Import lazily so missing dependencies don't break module import.
            from trading_bot import openai_client
        except Exception as exc:  # pragma: no cover - exercised when dependency missing
            raise ImportError(
                "openai_client (and openai) must be available to use MarketAnalystAgent"
            ) from exc

        prompt = self.prompt_template.format(symbol=symbol)
        raw_response = openai_client.call_openai(prompt)

        return {
            "agent": "MarketAnalystAgent",
            "symbol": symbol,
            "analysis": raw_response,
        }


class RiskAdvisorAgent:
    """Assess investment risks for a ticker symbol."""

    def __init__(
        self, prompt_template: str = "Offer an investment risk assessment for {symbol}."
    ) -> None:
        self.prompt_template = prompt_template

    def assess(self, symbol: str) -> Dict[str, str]:
        """Return a risk assessment for ``symbol`` using an LLM."""
        try:  # Import lazily so missing dependencies don't break module import.
            from trading_bot import openai_client
        except Exception as exc:  # pragma: no cover - exercised when dependency missing
            raise ImportError(
                "openai_client (and openai) must be available to use RiskAdvisorAgent"
            ) from exc

        prompt = self.prompt_template.format(symbol=symbol)
        raw_response = openai_client.call_openai(prompt)

        return {
            "agent": "RiskAdvisorAgent",
            "symbol": symbol,
            "assessment": raw_response,
        }


class NewsSummarizerAgent:
    """Summarize recent news for a ticker symbol."""

    def __init__(
        self, prompt_template: str = "Summarize the latest financial news affecting {symbol}."
    ) -> None:
        self.prompt_template = prompt_template

    def summarize(self, symbol: str) -> Dict[str, str]:
        """Return a news summary for ``symbol`` using an LLM."""
        try:  # Import lazily so missing dependencies don't break module import.
            from trading_bot import openai_client
        except Exception as exc:  # pragma: no cover - exercised when dependency missing
            raise ImportError(
                "openai_client (and openai) must be available to use NewsSummarizerAgent"
            ) from exc

        prompt = self.prompt_template.format(symbol=symbol)
        raw_response = openai_client.call_openai(prompt)

        return {
            "agent": "NewsSummarizerAgent",
            "symbol": symbol,
            "summary": raw_response,
        }


__all__ = ["MarketAnalystAgent", "RiskAdvisorAgent", "NewsSummarizerAgent"]
