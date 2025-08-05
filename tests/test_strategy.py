from trading_bot.strategy import compose_strategy


def test_compose_strategy_structure():
    technical = {"summary": "Bullish"}
    news = {"summary": "", "headlines": []}
    social = {"summary": "", "score": 0}
    macro = {"summary": ""}
    strategy = compose_strategy(
        symbol="TSLA",
        technical=technical,
        news=news,
        social=social,
        macro=macro,
        strategy_date="2024-01-01",
    )

    assert strategy["symbol"] == "TSLA"
    for key in [
        "entry_criteria",
        "position_sizing",
        "risk_management",
        "exit_strategy",
        "trade_management",
    ]:
        assert key in strategy
    assert "rationale" in strategy and "technical" in strategy["rationale"]
