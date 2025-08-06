from unittest.mock import MagicMock, patch

from trading_bot.agents import LLMAgent


def test_llmagent_calls_openai_and_structures_output():
    response_text = "Bullish outlook on TSLA\nFurther details here"
    fake_call = MagicMock(return_value=response_text)
    with patch("trading_bot.openai_client.call_llm", fake_call):
        agent = LLMAgent()
        result = agent.analyze("TSLA")
        fake_call.assert_called_once()
        assert "TSLA" in fake_call.call_args[0][0]

    assert result["agent"] == "LLMAgent"
    assert result["symbol"] == "TSLA"
    assert result["summary"] == "Bullish outlook on TSLA"
    assert result["raw_response"] == response_text
