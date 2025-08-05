from unittest.mock import MagicMock, patch
import os
import types

import pytest
from openai import OpenAIError

from trading_bot import openai_client


def test_call_openai_success():
    fake_response = types.SimpleNamespace(
        choices=[types.SimpleNamespace(message={"content": "hello world"})]
    )
    with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True):
        with patch("openai.ChatCompletion.create", return_value=fake_response) as mock_create:
            result = openai_client.call_openai("hi", temperature=0.2)
    assert result == "hello world"
    mock_create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.2,
    )


def test_call_openai_raises_runtime_error_on_openaierror():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True):
        with patch("openai.ChatCompletion.create", side_effect=OpenAIError("boom")):
            with pytest.raises(RuntimeError):
                openai_client.call_openai("hi")
