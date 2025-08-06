from pathlib import Path
from pathlib import Path
from unittest.mock import MagicMock

from trading_bot.coordinator import Coordinator
from trading_bot.pipeline import Pipeline
from trading_bot.storage import JSONStorage
from trading_bot.backtest import Backtester
from trading_bot.portfolio import Portfolio


class DummyAgent:
    def __init__(self, name: str):
        self.name = name

    def respond(self, symbol, history):
        return {"summary": f"{self.name} for {symbol}"}


def test_coordinator_builds_strategy_summary():
    c = Coordinator([DummyAgent("A"), DummyAgent("B")])
    result = c.run("TSLA")
    assert result["strategy_summary"]["A"]["summary"] == "A for TSLA"
    assert result["strategy_summary"]["B"]["summary"] == "B for TSLA"
    assert len(result["conversation"]) == 2


def test_pipeline_runs_range_and_backtests(tmp_path, monkeypatch):
    coord = Coordinator([DummyAgent("A")])
    storage = JSONStorage(base_dir=tmp_path)
    backtester = Backtester()
    portfolio = Portfolio()
    pipeline = Pipeline(coord, storage=storage, backtester=backtester, portfolio=portfolio)

    backtester.backtest = MagicMock(return_value={"net_return": 1})

    import types
    import pandas as pd
    import sys

    def fake_download(symbol, start, end, interval, progress=False):
        idx = pd.date_range(start, end, freq="D")
        return pd.DataFrame({"Close": [100.0 for _ in idx]}, index=idx)

    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(download=fake_download))

    result = pipeline.run("TSLA", start_date="2024-01-01", end_date="2024-01-02")

    assert len(result["days"]) == 2
    assert Path(result["days"][0]["strategy_path"]).exists()
    backtester.backtest.assert_called_once()
    assert len(portfolio.closed_positions()) == 2


def test_pipeline_today_returns_paths(tmp_path, monkeypatch):
    coord = Coordinator([DummyAgent("A")])
    storage = JSONStorage(base_dir=tmp_path)
    pipeline = Pipeline(coord, storage=storage)

    import types
    import pandas as pd
    import sys

    def fake_download(symbol, start, end, interval, progress=False):
        idx = pd.date_range(start, end, freq="D")
        return pd.DataFrame({"Close": [100.0 for _ in idx]}, index=idx)

    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(download=fake_download))

    result = pipeline.run("TSLA", today="2024-01-01")

    assert "signal" in result["strategy"]
    assert Path(result["files"]["strategy"]).exists()

