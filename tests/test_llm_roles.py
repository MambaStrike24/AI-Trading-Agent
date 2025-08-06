import json
from unittest.mock import MagicMock, patch

from trading_bot.agents import (
    MarketAnalystAgent,
    RiskAdvisorAgent,
    NewsSummarizerAgent,
)


def test_market_analyst_agent_returns_structured_data():
    response = json.dumps(
        {"summary": "s", "reasoning": "r", "market_trend": "up"}
    )
    fake = MagicMock(return_value=response)
    with patch("trading_bot.openai_client.call_llm", fake):
        agent = MarketAnalystAgent()
        data = agent.analyze("AAPL")

    fake.assert_called_once()
    assert data["summary"] == "s"
    assert data["reasoning"] == "r"
    assert data["market_trend"] == "up"


def test_risk_advisor_agent_returns_structured_data():
    response = json.dumps(
        {"summary": "s", "reasoning": "r", "risk_level": "low"}
    )
    fake = MagicMock(return_value=response)
    with patch("trading_bot.openai_client.call_llm", fake):
        agent = RiskAdvisorAgent()
        data = agent.assess("TSLA")

    assert data["risk_level"] == "low"
    assert data["agent"] == "RiskAdvisorAgent"


def test_news_summarizer_agent_returns_structured_data():
    response = json.dumps(
        {"summary": "s", "reasoning": "r", "headlines": ["h1"]}
    )
    fake = MagicMock(return_value=response)
    with patch("trading_bot.openai_client.call_llm", fake):
        agent = NewsSummarizerAgent()
        data = agent.summarize("GOOG")

    assert data["headlines"] == ["h1"]
    assert data["agent"] == "NewsSummarizerAgent"


def test_agent_handles_malformed_json():
    fake = MagicMock(return_value="not json")
    with patch("trading_bot.openai_client.call_llm", fake):
        agent = MarketAnalystAgent()
        data = agent.analyze("MSFT")
    assert data["summary"] == ""
    assert "error" in data

