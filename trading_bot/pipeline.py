"""High level pipeline for running the trading workflow for one symbol.

This module ties together the various agents, strategy composer, backtester
and storage utilities to execute the full daily routine described in the
project specification.  The implementation is intentionally minimal but shows
how the pieces fit together and provides a convenient function for unit tests
or scripts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

from .agents import (
    TechnicalAnalysisAgent,
    MarketScannerAgent,
    SocialMediaAgent,
    NewsAnalyzerAgent,
)
from .strategy import compose_strategy
from .backtest import Backtester
from .storage import JSONStorage
from .portfolio import Portfolio


@dataclass
class Pipeline:
    """Run all agents, compose a strategy and backtest it."""

    storage: Optional[JSONStorage] = None
    portfolio: Optional[Portfolio] = None
    backtester: Backtester = Backtester()

    def run(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Execute the full pipeline for ``symbol``.

        Parameters
        ----------
        symbol:
            Ticker symbol to analyse.
        start_date, end_date:
            Date range for the backtest in ``YYYY-MM-DD`` format.
        """

        # Run agents ------------------------------------------------------
        technical = TechnicalAnalysisAgent().analyze(symbol)
        market = MarketScannerAgent().analyze(symbol)
        social = SocialMediaAgent().analyze(symbol)
        news = NewsAnalyzerAgent().analyze(symbol)

        # Compose strategy -------------------------------------------------
        strategy = compose_strategy(
            symbol,
            technical=technical,
            market=market,
            news=news,
            social=social,
        )

        # Backtest ---------------------------------------------------------
        bt_result = self.backtester.backtest(symbol, start_date, end_date, strategy)

        # Persist outputs --------------------------------------------------
        date_str = start_date
        if self.storage:
            self.storage.save("technical", symbol, date_str, technical)
            self.storage.save("market", symbol, date_str, market)
            self.storage.save("social", symbol, date_str, social)
            self.storage.save("news", symbol, date_str, news)
            self.storage.save("strategy", symbol, date_str, strategy)
            self.storage.save("backtest", symbol, date_str, bt_result)

        # Update portfolio -------------------------------------------------
        if self.portfolio:
            trade = bt_result["trade_log"][0]
            pos = self.portfolio.open_position(
                symbol,
                size=1,
                entry_price=trade["entry_price"],
                entry_time=datetime.fromisoformat(trade["entry_time"]),
                strategy_ref=date_str,
            )
            self.portfolio.close_position(
                pos,
                exit_price=trade["exit_price"],
                exit_time=datetime.fromisoformat(trade["exit_time"]),
            )

        return {
            "symbol": symbol,
            "technical": technical,
            "market": market,
            "social": social,
            "news": news,
            "strategy": strategy,
            "backtest": bt_result,
        }


__all__ = ["Pipeline"]
