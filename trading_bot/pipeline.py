"""Minimal pipeline orchestrating LLMAgents.

The pipeline accepts a sequence of :class:`~trading_bot.agents.LLMAgent`
instances. When run for a symbol it executes each agent and aggregates their
responses into a single dictionary.

This stripped down version intentionally focuses on LLM driven analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from .agents import LLMAgent


@dataclass
class Pipeline:
    """Run all configured LLM agents for a given symbol."""

    agents: Sequence[LLMAgent]

    def run(self, symbol: str) -> Dict[str, Any]:
        """Execute each agent and collect their outputs."""
        reports: List[Dict[str, Any]] = [agent.analyze(symbol) for agent in self.agents]
        return {"symbol": symbol, "reports": reports}


__all__ = ["Pipeline"]
