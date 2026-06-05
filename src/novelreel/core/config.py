"""配置加载 —— 从环境变量 / .env 读取 LLM 接入信息。

为什么单独抽一个文件：PRD 的「模型可替换」原则要求 —— 切换模型只改配置，
不改代码。所有跟「接哪个模型」相关的东西集中在这里。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# 自动加载项目根目录的 .env（如果存在）。
# 真实密钥放 .env（已被 .gitignore 忽略），不会进版本库。
load_dotenv()


@dataclass
class LLMConfig:
    """LLM 接入配置。默认值对接火山引擎豆包（OpenAI 兼容接口）。"""

    base_url: str
    api_key: str
    model: str

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """从环境变量读取配置。

        三个变量：
        - NOVELREEL_LLM_BASE_URL（默认豆包地址）
        - NOVELREEL_LLM_API_KEY（必填，没填会在真正调用时报错）
        - NOVELREEL_LLM_MODEL（默认 doubao-seed-1-6）
        """
        return cls(
            base_url=os.getenv(
                "NOVELREEL_LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
            ),
            api_key=os.getenv("NOVELREEL_LLM_API_KEY", ""),
            model=os.getenv("NOVELREEL_LLM_MODEL", "doubao-seed-1-6-251015"),
        )

    @property
    def is_ready(self) -> bool:
        """密钥是否已配置。"""
        return bool(self.api_key)
