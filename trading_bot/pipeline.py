"""Pipeline executing agents over a date range and persisting results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
import warnings

import pandas as pd

from .coordinator import Coordinator
from .strategy import compose_strategy
from .storage import JSONStorage
from .backtest import Backtester
from .portfolio import Portfolio


@dataclass
class Pipeline:
    """Coordinate agents and optionally backtest their combined strategy."""

    coordinator: Coordinator
    storage: JSONStorage
    backtester: Optional[Backtester] = None
    portfolio: Optional[Portfolio] = None

    def _date_iter(self, start: str, end: str) -> Iterable[pd.Timestamp]:
        return pd.date_range(start, end, freq="D")

    def _load_prices(
        self, symbol: str, start: str, end: str, dates: List[pd.Timestamp]
    ) -> pd.Series:
        try:  # pragma: no cover - exercised when yfinance available
            import yfinance as yf  # type: ignore

            df = yf.download(
                symbol,
                start=start,
                end=(pd.to_datetime(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                interval="1d",
                progress=False,
            )
            if df.empty:
                raise ValueError
            prices = df["Close"]
            prices.index = pd.to_datetime(prices.index)
            return prices
        except Exception:  # pragma: no cover - fallback path
            warnings.warn(
                "yfinance unavailable or returned no data; using synthetic price 100.0",
                RuntimeWarning,
            )
            return pd.Series(100.0, index=dates)

    def run(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        today: str | None = None,
    ) -> Dict[str, Any]:
        """Run the pipeline for ``symbol``.

        If ``today`` is supplied only that date is processed and the composed
        strategy for the day is returned.  Otherwise the function iterates from
        ``start_date`` to ``end_date`` (inclusive), logging each day's
        conversation and strategy and optionally invoking a backtest across the
        whole range.
        """

        if today:
            dates = [pd.to_datetime(today)]
            price_series = self._load_prices(symbol, today, today, dates)
        else:
            if start_date is None or end_date is None:
                raise ValueError(
                    "start_date and end_date must be provided when today is not set"
                )
            dates = list(self._date_iter(start_date, end_date))
            price_series = self._load_prices(symbol, start_date, end_date, dates)

        day_results: List[Dict[str, Any]] = []

        for ts in dates:
            day_str = ts.strftime("%Y-%m-%d")
            convo = self.coordinator.run(symbol)
            convo_path = self.storage.save("conversation", symbol, day_str, convo)

            agent_map = {item["agent"]: item for item in convo["conversation"]}
            strategy = compose_strategy(symbol, agent_map, strategy_date=day_str)
            strat_path = self.storage.save("strategy", symbol, day_str, strategy)

            price = float(price_series.get(ts, price_series.iloc[0]))
            if self.portfolio is not None:
                pos = self.portfolio.open_position(
                    symbol,
                    size=1,
                    entry_price=price,
                    entry_time=datetime.fromisoformat(day_str + "T00:00:00"),
                    strategy_ref=day_str,
                )
                self.portfolio.close_position(
                    pos,
                    exit_price=price,
                    exit_time=datetime.fromisoformat(day_str + "T23:59:59"),
                )

            day_results.append(
                {
                    "date": day_str,
                    "conversation_path": str(convo_path),
                    "strategy_path": str(strat_path),
                    "strategy": strategy,
                }
            )

        if today:
            last = day_results[-1]
            return {
                "strategy": last["strategy"],
                "files": {
                    "conversation": last["conversation_path"],
                    "strategy": last["strategy_path"],
                },
            }

        files = {
            "conversations": [d["conversation_path"] for d in day_results],
            "strategies": [d["strategy_path"] for d in day_results],
        }

        backtest_result = None
        if self.backtester is not None:
            backtest_result = self.backtester.backtest(
                symbol,
                start_date=start_date or dates[0].strftime("%Y-%m-%d"),
                end_date=end_date or dates[-1].strftime("%Y-%m-%d"),
                strategy_dict={"strategies": [d["strategy"] for d in day_results]},
                portfolio=self.portfolio,
            )
            bt_path = self.storage.save(
                "backtest", symbol, dates[-1].strftime("%Y-%m-%d"), backtest_result
            )
            files["backtest"] = str(bt_path)

        return {"days": day_results, "backtest": backtest_result, "files": files}


__all__ = ["Pipeline"]

