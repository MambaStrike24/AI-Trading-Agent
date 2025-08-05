"""Market scanner agent for basic market metrics.

This agent fetches recent price data via :mod:`yfinance` and extracts a
handful of metrics that are typically used to gauge the current market
environment for a given symbol.  The implementation is intentionally
lightweight but follows the structured output format described in the project
specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf


@dataclass
class MarketScannerAgent:
    """Collect basic market data such as price, volume and volatility."""

    data_source: str = "Yahoo Finance"

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """Return market metrics for ``symbol``.

        The method downloads roughly one month of daily data and reports the
        latest values for price, volume, VWAP, 14-day ATR and realised
        volatility.
        """

        df = yf.download(symbol, period="1mo", interval="1d", progress=False)
        if df.empty:
            raise ValueError(f"No data returned for symbol {symbol}")

        close = df["Close"]
        volume = df["Volume"]
        high = df["High"]
        low = df["Low"]

        # VWAP using the typical price approximation.
        typical = (high + low + close) / 3
        vwap = float((typical * volume).sum() / volume.sum())

        # Average True Range (ATR) over 14 periods
        hl = high - low
        hc = (high - close.shift()).abs()
        lc = (low - close.shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        atr14 = float(tr.rolling(14).mean().iloc[-1])

        # Realised volatility as standard deviation of log returns
        returns = close.pct_change().dropna()
        volatility = float(returns.std() * (len(returns) ** 0.5))

        results = {
            "price": float(close.iloc[-1]),
            "volume": float(volume.iloc[-1]),
            "vwap": vwap,
            "atr_14": atr14,
            "volatility": volatility,
        }

        return {
            "agent": "MarketScannerAgent",
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics_used": list(results.keys()),
            "results": results,
            "summary": "Market metrics collected.",
            "data_source": self.data_source,
        }


__all__: List[str] = ["MarketScannerAgent"]

