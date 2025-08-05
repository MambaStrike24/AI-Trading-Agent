"""Minimal backtesting utility.

This is **not** a full featured backtesting engine but rather a lightweight
implementation that mirrors the structure described in the project
specification.  It performs a buy-and-hold simulation over the supplied date
range using data retrieved from :mod:`yfinance`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd


@dataclass
class Backtester:
    """Run a naive buy-and-hold simulation for a strategy."""

    data_source: str = "Yahoo Finance"

    def backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        strategy_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            import yfinance as yf  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "yfinance is required for backtesting. Install it with 'pip install yfinance'."
            ) from exc

        df = yf.download(
            symbol,
            start=start_date,
            end=end_date,
            interval="1d",
            progress=False,
        )
        if df.empty:
            raise ValueError("No data for backtest")

        prices = df["Close"]
        net_return = float(prices.iloc[-1] / prices.iloc[0] - 1)

        roll_max = prices.cummax()
        drawdown = (prices - roll_max) / roll_max
        max_drawdown = float(drawdown.min())

        trade_log = [
            {
                "entry_time": prices.index[0].isoformat(),
                "entry_price": float(prices.iloc[0]),
                "exit_time": prices.index[-1].isoformat(),
                "exit_price": float(prices.iloc[-1]),
                "pnl": float(prices.iloc[-1] - prices.iloc[0]),
            }
        ]

        return {
            "symbol": symbol,
            "date_range": [start_date, end_date],
            "net_return": net_return,
            "max_drawdown": max_drawdown,
            "trade_log": trade_log,
            "equity_curve": [float(p) for p in prices],
            "strategy_applied": strategy_dict,
            "agent_inputs": {},
            "data_source": self.data_source,
        }


__all__: List[str] = ["Backtester"]

