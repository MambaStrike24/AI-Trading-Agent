import pandas as pd
from unittest.mock import patch

from trading_bot.agents.technical_analysis import TechnicalAnalysisAgent


def test_analyze_returns_expected_structure():
    # Create deterministic price series so indicator values are stable
    close = pd.Series(range(1, 31), index=pd.date_range("2024-01-01", periods=30))
    df = pd.DataFrame({"Close": close})

    with patch("yfinance.download", return_value=df):
        agent = TechnicalAnalysisAgent()
        result = agent.analyze("TSLA")

    assert result["agent"] == "TechnicalAnalysisAgent"
    assert result["symbol"] == "TSLA"
    assert set(result["indicators_used"]) == {"ema_9", "rsi_14", "macd_hist"}
    assert {"ema_9", "rsi_14", "macd_hist"} <= result["results"].keys()
    assert result["trend_signal"] in {"bullish", "bearish"}
