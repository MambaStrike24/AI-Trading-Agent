"""Utilities for composing a daily trading strategy."""

from __future__ import annotations

from datetime import date
from typing import Dict, Any, Optional, List


def compose_strategy(
    symbol: str, agent_data: Dict[str, Dict[str, Any]], *, strategy_date: Optional[str] = None
) -> Dict[str, Any]:
    """Derive a trading signal from structured agent outputs.

    The function inspects the ``market_trend`` from the analyst and the
    ``risk_level`` from the risk advisor to produce a high level ``signal`` of
    ``buy``, ``sell`` or ``hold``.  A human readable ``rationale`` summarises the
    key factors.  If certain information is missing the function may include a
    ``follow_ups`` list indicating areas that require more research.
    """

    strategy_date = strategy_date or date.today().isoformat()
    summary = " ".join(v.get("summary", "") for v in agent_data.values()).strip()

    trend = str(agent_data.get("MarketAnalystAgent", {}).get("market_trend", "")).lower()
    # risk = str(agent_data.get("RiskAdvisorAgent", {}).get("risk_level", "")).lower()

    signal = "hold"
    rationale: List[str] = []
    follow_ups: List[str] = []

    if "bull" in trend and risk not in {"high", "elevated"}:
        signal = "buy"
        rationale.append("Analyst reports bullish trend with acceptable risk")
    elif "bear" in trend and risk in {"high", "elevated", "medium"}:
        signal = "sell"
        rationale.append("Bearish trend with noted risk")
    else:
        rationale.append("Mixed signals; hold position")

    if not agent_data.get("NewsSummarizerAgent", {}).get("headlines"):
        follow_ups.append("Review recent news for more context")

    result: Dict[str, Any] = {
        "symbol": symbol,
        "date": strategy_date,
        "summary": summary,
        "details": agent_data,
        "signal": signal,
        "rationale": " ".join(rationale),
    }
    if follow_ups:
        result["follow_ups"] = follow_ups
    return result


__all__ = ["compose_strategy"]

