"""真实连通测试 —— 验证豆包密钥配好了、能调通。

对应教学第 1 节课「把 LLM 叫起来」。需要先在 .env 填好密钥，然后：

    uv run python scripts/check_llm.py

它会问豆包一个简单问题并打印回复。如果密钥没配，会给出友好提示。
（这个脚本不在 pytest 里跑，因为它要真实联网 + 花钱。）
"""

from novelreel.core.config import LLMConfig
from novelreel.core.llm import LLMClient, LLMError


def main() -> None:
    config = LLMConfig.from_env()
    print(f"接入地址：{config.base_url}")
    print(f"使用模型：{config.model}")
    print(f"密钥状态：{'已配置 ✓' if config.is_ready else '未配置 ✗'}\n")

    if not config.is_ready:
        print("请先复制 .env.example 为 .env，填入 NOVELREEL_LLM_API_KEY 再运行。")
        return

    client = LLMClient(config)
    try:
        print("→ 正在向豆包提问：用一句话介绍你自己\n")
        reply = client.chat("用一句话介绍你自己")
        print(f"← 豆包回复：{reply}\n")

        print("→ 测试结构化输出：返回一个含 name 和 mood 字段的 JSON\n")
        data = client.chat_json('返回一个 JSON，包含 name="测试" 和 mood="开心" 两个字段')
        print(f"← 解析结果：{data}\n")
        print("✅ 连通正常，可以开始用了。")
    except LLMError as e:
        print(f"❌ 调用失败：{e}")


if __name__ == "__main__":
    main()
