from unittest.mock import patch

from trading_bot.agents import LLMAgent
from trading_bot.pipeline import Pipeline


def test_pipeline_returns_only_llmagent_reports():
    agents = [LLMAgent(), LLMAgent()]
    with patch.object(
        LLMAgent,
        "analyze",
        side_effect=lambda symbol: {
            "agent": "LLMAgent",
            "symbol": symbol,
            "summary": "stub",
            "raw_response": "raw",
        },
    ) as mock_analyze:
        pipeline = Pipeline(agents)
        result = pipeline.run("TSLA")
        assert mock_analyze.call_count == 2

    assert result["symbol"] == "TSLA"
    assert len(result["reports"]) == 2
    assert all(report["agent"] == "LLMAgent" for report in result["reports"])
