import pandas as pd
from unittest.mock import patch

from trading_bot.backtest import Backtester


def test_backtester_returns_structure():
    dates = pd.date_range("2024-01-01", periods=5)
    df = pd.DataFrame({"Close": pd.Series([1, 2, 3, 4, 5], index=dates)})

    with patch("yfinance.download", return_value=df):
        bt = Backtester()
        strategy = {"symbol": "TSLA"}
        result = bt.backtest("TSLA", "2024-01-01", "2024-01-05", strategy)

    assert result["symbol"] == "TSLA"
    assert "net_return" in result and result["net_return"] > 0
    assert result["trade_log"][0]["entry_price"] == 1
