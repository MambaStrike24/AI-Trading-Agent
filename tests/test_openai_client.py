from unittest.mock import MagicMock, patch
import types
import sys

from trading_bot import openai_client


def test_call_llm_uses_loaded_generator(monkeypatch):
    fake_gen = MagicMock(return_value="output")
    monkeypatch.setattr(openai_client, "_load_generator", lambda: fake_gen)

    result = openai_client.call_llm("prompt", temperature=0.2)

    assert result == "output"
    fake_gen.assert_called_once_with("prompt", temperature=0.2)


def test_call_llm_falls_back_when_transformers_missing():
    dummy_module = types.SimpleNamespace(pipeline=MagicMock(side_effect=Exception("boom")))
    with patch.dict(sys.modules, {"transformers": dummy_module}):
        openai_client._GENERATOR = None
        result = openai_client.call_llm("hi")
    assert result == "hi"

