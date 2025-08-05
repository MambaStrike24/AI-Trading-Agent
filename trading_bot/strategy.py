"""Strategy composer for combining agent outputs into an actionable plan."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional


def compose_strategy(
    symbol: str,
    *,
    technical: Optional[Dict[str, Any]] = None,
    news: Optional[Dict[str, Any]] = None,
    social: Optional[Dict[str, Any]] = None,
    macro: Optional[Dict[str, Any]] = None,
    strategy_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a strategy dictionary from agent insights.

    Parameters
    ----------
    symbol:
        Ticker symbol to which the strategy applies.
    technical, news, social, macro:
        Dictionaries produced by the corresponding agents.
    strategy_date:
        ISO formatted date.  Defaults to today if ``None``.
    """

    strategy_date = strategy_date or date.today().isoformat()
    technical = technical or {"summary": "", "details": {}}
    news = news or {"summary": "", "headlines": []}
    social = social or {"summary": "", "score": 0}
    macro = macro or {"summary": ""}

    entry_criteria = f"Enter long on {symbol} when technicals support bullish trend."
    position_sizing = "Risk 2% of capital per trade."
    risk_management = "Set stop-loss below recent swing low."
    exit_strategy = "Take profit at 2R or when momentum fades."
    trade_management = "Move stop to break-even after 1R gain."

    return {
        "symbol": symbol,
        "date": strategy_date,
        "entry_criteria": entry_criteria,
        "position_sizing": position_sizing,
        "risk_management": risk_management,
        "exit_strategy": exit_strategy,
        "trade_management": trade_management,
        "rationale": {
            "technical": {"summary": technical.get("summary", ""), "details": technical},
            "news": news,
            "social": social,
            "macro": macro,
        },
    }
