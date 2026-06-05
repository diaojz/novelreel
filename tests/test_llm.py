"""LLM 客户端单测 —— 用 mock 验证逻辑，不调真实 API（跑得快、不花钱）。"""

from unittest.mock import MagicMock, patch

import pytest

from novelreel.core.config import LLMConfig
from novelreel.core.llm import LLMClient, LLMError, _parse_json


def test_parse_json_plain():
    assert _parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_strips_code_fence():
    # 模型有时会画蛇添足包一层 ```json
    raw = '```json\n{"name": "沈师傅"}\n```'
    assert _parse_json(raw) == {"name": "沈师傅"}


def test_parse_json_invalid_raises():
    with pytest.raises(LLMError):
        _parse_json("这不是 JSON")


def test_chat_without_key_raises():
    client = LLMClient(LLMConfig(base_url="x", api_key="", model="m"))
    with pytest.raises(LLMError, match="未配置 LLM API Key"):
        client.chat("你好")


def _fake_response(content: str):
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    return resp


def test_chat_returns_text():
    config = LLMConfig(base_url="http://x", api_key="fake-key", model="m")
    client = LLMClient(config)
    with patch.object(client, "_ensure_client") as ec:
        fake = MagicMock()
        fake.chat.completions.create.return_value = _fake_response("你好呀")
        ec.return_value = fake
        assert client.chat("hi") == "你好呀"


def test_chat_json_parses():
    config = LLMConfig(base_url="http://x", api_key="fake-key", model="m")
    client = LLMClient(config)
    with patch.object(client, "_ensure_client") as ec:
        fake = MagicMock()
        fake.chat.completions.create.return_value = _fake_response('{"shots": 3}')
        ec.return_value = fake
        assert client.chat_json("生成分镜") == {"shots": 3}
