from __future__ import annotations

"""Technical analysis agent for computing basic indicators using yfinance.

The agent fetches recent daily price data for a symbol from Yahoo Finance and
computes a small selection of technical indicators.  Results are returned in a
structured dictionary which mirrors the specification described in the project
README.  This module is intentionally lightweight – it provides a minimal
implementation that can be expanded upon by future contributors.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf


@dataclass
class TechnicalAnalysisAgent:
    """Analyse a symbol using common technical indicators.

    Parameters
    ----------
    indicators:
        A list of indicator names that the agent should compute.  Supported
        values are ``ema_9``, ``rsi_14`` and ``macd``.  If ``None`` is supplied
        all indicators are calculated.
    """

    indicators: List[str] | None = None
    data_source: str = "Yahoo Finance"

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """Return indicator values for ``symbol``.

        The method downloads roughly one month of daily data for ``symbol`` and
        returns the last calculated value for each indicator.
        """

        indicators = self.indicators or ["ema_9", "rsi_14", "macd"]
        df = yf.download(symbol, period="1mo", interval="1d", progress=False)

        if df.empty:
            raise ValueError(f"No data returned for symbol {symbol}")

        results: Dict[str, float] = {}
        closes = df["Close"]

        if "ema_9" in indicators:
            results["ema_9"] = float(closes.ewm(span=9).mean().iloc[-1])
        if "rsi_14" in indicators:
            delta = closes.diff()
            up = delta.clip(lower=0).rolling(14).mean()
            down = -delta.clip(upper=0).rolling(14).mean()
            rs = up / down
            rsi = 100 - 100 / (1 + rs)
            results["rsi_14"] = float(rsi.iloc[-1])
        if "macd" in indicators:
            ema12 = closes.ewm(span=12).mean()
            ema26 = closes.ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal = macd_line.ewm(span=9).mean()
            results["macd_hist"] = float(macd_line.iloc[-1] - signal.iloc[-1])

        trend_signal = "bullish" if results.get("macd_hist", 0) > 0 else "bearish"

        return {
            "agent": "TechnicalAnalysisAgent",
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "indicators_used": list(results.keys()),
            "results": results,
            "summary": f"Trend is {trend_signal} based on MACD histogram.",
            "trend_signal": trend_signal,
            "data_source": self.data_source,
        }
