from trading_bot.strategy import compose_strategy


def test_compose_strategy_generates_signal_and_followups():
    agents = {
        "MarketAnalystAgent": {
            "summary": "bullish outlook",
            "reasoning": "",
            "market_trend": "bullish",
        },
        "RiskAdvisorAgent": {
            "summary": "low risk",
            "reasoning": "",
            "risk_level": "low",
        },
        "NewsSummarizerAgent": {
            "summary": "",
            "reasoning": "",
            "headlines": [],
        },
    }

    strat = compose_strategy("TSLA", agents, strategy_date="2024-01-01")
    assert strat["signal"] == "buy"
    assert "bullish" in strat["rationale"].lower()
    assert strat.get("follow_ups")
