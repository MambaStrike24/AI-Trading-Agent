from unittest.mock import patch
import os
import types

import pytest
from openai import OpenAIError

from trading_bot import openai_client


def test_call_openai_success():
    fake_response = types.SimpleNamespace(
        choices=[
            types.SimpleNamespace(
                message=types.SimpleNamespace(content="hello world")
            )
        ]
    )
    with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True):
        with patch("trading_bot.openai_client.OpenAI") as MockOpenAI:
            mock_client = MockOpenAI.return_value
            mock_client.chat.completions.create.return_value = fake_response
            result = openai_client.call_openai("hi", temperature=0.2)
    assert result == "hello world"
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.2,
    )


def test_call_openai_raises_runtime_error_on_openaierror():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True):
        with patch("trading_bot.openai_client.OpenAI") as MockOpenAI:
            mock_client = MockOpenAI.return_value
            mock_client.chat.completions.create.side_effect = OpenAIError("boom")
            with pytest.raises(RuntimeError):
                openai_client.call_openai("hi")


def test_call_openai_raises_runtime_error_on_ratelimit():
    class DummyRateLimitError(Exception):
        pass

    with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True):
        with patch("trading_bot.openai_client.OpenAI") as MockOpenAI:
            mock_client = MockOpenAI.return_value
            mock_client.chat.completions.create.side_effect = DummyRateLimitError
            with patch("trading_bot.openai_client.RateLimitError", DummyRateLimitError):
                with pytest.raises(RuntimeError, match="rate limit"):
                    openai_client.call_openai("hi")
