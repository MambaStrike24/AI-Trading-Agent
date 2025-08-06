"""Utilities for composing a daily trading strategy."""

from __future__ import annotations

from datetime import date
from typing import Dict, Any, Optional


def compose_strategy(
    symbol: str, agent_data: Dict[str, Dict[str, Any]], *, strategy_date: Optional[str] = None
) -> Dict[str, Any]:
    """Combine structured agent outputs into a simple action plan.

    Parameters
    ----------
    symbol:
        The ticker symbol the strategy applies to.
    agent_data:
        Mapping of agent name to the structured dictionary each agent produced.
    strategy_date:
        ISO formatted date for the strategy.  Defaults to today's date.
    """

    strategy_date = strategy_date or date.today().isoformat()
    summary = " ".join(v.get("summary", "") for v in agent_data.values()).strip()

    return {
        "symbol": symbol,
        "date": strategy_date,
        "summary": summary,
        "details": agent_data,
        "action": f"Review {symbol} with generated insights before trading.",
    }


__all__ = ["compose_strategy"]

