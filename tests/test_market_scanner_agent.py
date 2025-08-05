import pandas as pd
from unittest.mock import patch

from trading_bot.agents.market_scanner import MarketScannerAgent


def test_market_scanner_returns_expected_structure():
    dates = pd.date_range("2024-01-01", periods=30)
    df = pd.DataFrame(
        {
            "Close": pd.Series(range(1, 31), index=dates),
            "Volume": pd.Series(1000, index=dates),
            "High": pd.Series(range(2, 32), index=dates),
            "Low": pd.Series(range(0, 30), index=dates),
        }
    )

    with patch("yfinance.download", return_value=df):
        agent = MarketScannerAgent()
        result = agent.analyze("TSLA")

    assert result["agent"] == "MarketScannerAgent"
    assert result["symbol"] == "TSLA"
    assert {"price", "volume", "vwap", "atr_14", "volatility"} <= set(
        result["results"].keys()
    )
