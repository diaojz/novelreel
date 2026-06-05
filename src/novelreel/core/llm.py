"""LLM 客户端 —— 把「调大模型」这件事封装成两个简单方法。

对接火山引擎豆包（OpenAI 兼容接口），用官方 openai SDK，只改 base_url 和 key。

提供两个方法：
- chat(): 返回纯文本回复（第 1 节课「把 LLM 叫起来」用这个）
- chat_json(): 强制返回 JSON 并解析成 dict（Subagent 提取角色/生成分镜用这个）

为什么要单独有个 chat_json：让 AI 返回结构化数据（而不是一段散文）是
做 Agent 的核心技巧。我们在 prompt 里要求「只返回 JSON」，再用 json.loads 解析，
解析失败就抛一个清晰的错误，方便定位是「AI 没按格式返回」还是「别的问题」。
"""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .config import LLMConfig


class LLMError(RuntimeError):
    """LLM 调用相关的错误（密钥没配、返回不是合法 JSON 等）。"""


class LLMClient:
    """豆包客户端的薄封装。"""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig.from_env()
        # 注意：这里不检查密钥，允许先创建客户端（方便测试 mock）；
        # 真正发请求时（_ensure_ready）才校验。
        self._client: OpenAI | None = None

    def _ensure_client(self) -> OpenAI:
        if not self.config.is_ready:
            raise LLMError(
                "未配置 LLM API Key。请复制 .env.example 为 .env 并填入 "
                "NOVELREEL_LLM_API_KEY（火山引擎控制台获取）。"
            )
        if self._client is None:
            self._client = OpenAI(
                api_key=self.config.api_key, base_url=self.config.base_url
            )
        return self._client

    def chat(self, prompt: str, system: str = "", temperature: float = 0.7) -> str:
        """发一条消息，返回模型的纯文本回复。"""
        client = self._ensure_client()
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = client.chat.completions.create(
            model=self.config.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    def chat_json(
        self, prompt: str, system: str = "", temperature: float = 0.4
    ) -> Any:
        """发一条消息，要求模型返回 JSON，解析后返回 Python 对象（dict/list）。

        用 response_format=json_object 让豆包走 JSON 模式；万一返回里仍夹带了
        ```json 代码块标记，也做一层兜底清洗再解析。
        """
        client = self._ensure_client()
        sys = (system or "你是一个严谨的助手。") + "\n请只返回合法的 JSON，不要任何额外解释或 markdown 代码块标记。"
        messages = [
            {"role": "system", "content": sys},
            {"role": "user", "content": prompt},
        ]

        resp = client.chat.completions.create(
            model=self.config.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        return _parse_json(raw)


def _parse_json(raw: str) -> Any:
    """解析模型返回的 JSON，带兜底清洗（去掉可能的 ```json 包裹）。"""
    text = raw.strip()
    # 兜底：剥掉 markdown 代码块围栏
    if text.startswith("```"):
        text = text.split("```", 2)[1] if text.count("```") >= 2 else text
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
        text = text.strip().strip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError(
            f"模型没有返回合法 JSON：{e}\n原始返回（前 300 字）：{raw[:300]}"
        ) from e
