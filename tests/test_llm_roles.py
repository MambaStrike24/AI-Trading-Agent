from unittest.mock import MagicMock, patch

from trading_bot.agents import (
    MarketAnalystAgent,
    NewsSummarizerAgent,
    RiskAdvisorAgent,
)


def test_market_analyst_agent_uses_prompt_template():
    response_text = "Analysis result"
    fake_call = MagicMock(return_value=response_text)
    with patch("trading_bot.openai_client.call_openai", fake_call):
        template = "Analyze the market for {symbol}"
        agent = MarketAnalystAgent(prompt_template=template)
        result = agent.analyze("AAPL")
        fake_call.assert_called_once_with("Analyze the market for AAPL")

    assert result["agent"] == "MarketAnalystAgent"
    assert result["symbol"] == "AAPL"
    assert result["analysis"] == response_text


def test_risk_advisor_agent_uses_prompt_template():
    response_text = "Risk assessment"
    fake_call = MagicMock(return_value=response_text)
    with patch("trading_bot.openai_client.call_openai", fake_call):
        template = "Assess risks for {symbol}"
        agent = RiskAdvisorAgent(prompt_template=template)
        result = agent.assess("TSLA")
        fake_call.assert_called_once_with("Assess risks for TSLA")

    assert result["agent"] == "RiskAdvisorAgent"
    assert result["symbol"] == "TSLA"
    assert result["assessment"] == response_text


def test_news_summarizer_agent_uses_prompt_template():
    response_text = "News summary"
    fake_call = MagicMock(return_value=response_text)
    with patch("trading_bot.openai_client.call_openai", fake_call):
        template = "Summarize news for {symbol}"
        agent = NewsSummarizerAgent(prompt_template=template)
        result = agent.summarize("GOOG")
        fake_call.assert_called_once_with("Summarize news for GOOG")

    assert result["agent"] == "NewsSummarizerAgent"
    assert result["symbol"] == "GOOG"
    assert result["summary"] == response_text
