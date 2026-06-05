"""演示服务器 —— 用假 LLM 启动，无需豆包密钥也能端到端跑通前端。

仅用于本地演示 / 前端联调 / 课堂第一次看效果。它把 LLM 换成返回固定假数据，
所以提取资产和生成分镜会立刻返回（不联网、不花钱）。

启动：
    uv run python scripts/serve_demo.py
然后浏览器打开 http://127.0.0.1:8000

真实使用请配好 .env 的豆包密钥，用：
    uv run uvicorn novelreel.api:app --reload
"""

import time
from unittest.mock import MagicMock

import uvicorn

import novelreel.agents.extract_assets as ea
import novelreel.agents.generate_script as gs

_ASSETS = {
    "characters": [
        {"name": "沈师傅", "aliases": ["沈修表"], "appearance": "六十多岁，背微驼，圆框老花镜，靛蓝粗布褂子", "personality": "沉默寡言、专注、藏着旧情", "role": "主角"},
        {"name": "林小满", "aliases": ["小满"], "appearance": "二十出头，花店学徒，撑伞少女", "personality": "真诚、念旧、情绪外露", "role": "配角"},
        {"name": "云", "aliases": [], "appearance": "仅在表背刻字中出现，未正面描写", "personality": "沈师傅年轻时的定情之人", "role": "回忆人物"},
    ],
    "scenes": [
        {"name": "残灯巷旧钟表铺", "description": "巷尾旧铺，褪色齿轮招牌，昏黄台灯", "mood": "安静、怀旧"},
        {"name": "雨夜青石板巷", "description": "小雨，青石板泛水光，铺外的夜色", "mood": "湿润、克制的伤感"},
    ],
    "props": [
        {"name": "黄铜怀表", "description": "缠枝莲表壳，背刻「赠阿沈，民国廿三年，云」", "significance": "串起两代人的定情信物"},
        {"name": "修表工具", "description": "镊子、放大镜、极细钢丝、台灯", "significance": "承载「修复」这一核心动作"},
    ],
}
_SHOTS = {"shots": [
    {"index": 1, "shot_type": "全景", "visual_description": "雨夜，残灯巷尽头的旧钟表铺亮着一盏昏黄台灯，镜头缓缓推近店门。", "characters_present": ["沈师傅"], "dialogue": "", "caption": "残灯巷尽头，有一家修表三十年的铺子", "mood": "怀旧", "duration_hint": 4},
    {"index": 2, "shot_type": "中景", "visual_description": "林小满撑伞冲进铺子，紧攥着一只停摆的黄铜怀表，神情焦急。", "characters_present": ["林小满"], "dialogue": "师傅，这表……能修好吗？", "caption": "奶奶留下的唯一念想", "mood": "急切", "duration_hint": 3},
    {"index": 3, "shot_type": "特写", "visual_description": "台灯下，沈师傅用镊子撬开怀表后盖，放大镜里游丝纤细。", "characters_present": ["沈师傅"], "dialogue": "", "caption": "再坏的表，到他手里都能复活", "mood": "专注", "duration_hint": 5},
    {"index": 4, "shot_type": "近景", "visual_description": "怀表重新滴答走动，沈师傅的目光落在表背刻字上，手微微颤抖。", "characters_present": ["沈师傅", "林小满"], "dialogue": "赠阿沈，民国廿三年，云。", "caption": "那行字，他等了三十年", "mood": "动容", "duration_hint": 4},
    {"index": 5, "shot_type": "全景", "visual_description": "雨停了，镜头拉远，老人与少女的身影定格在昏黄灯光中。", "characters_present": ["沈师傅", "林小满"], "dialogue": "", "caption": "有些等待，本身就是答案", "mood": "释然", "duration_hint": 5},
]}


def _fake_llm():
    llm = MagicMock()

    def _slow_json(*a, **k):
        time.sleep(1.5)  # 模拟真实调用耗时，方便看到「处理中」动画
        text = a[0] if a else ""
        return _SHOTS if "分镜" in text else _ASSETS

    llm.chat_json.side_effect = _slow_json
    return llm


# 把两个 Subagent 里 new LLMClient 的地方换成假的
_fake = _fake_llm()
ea.LLMClient = lambda *a, **k: _fake
gs.LLMClient = lambda *a, **k: _fake

# 必须在打补丁之后再导入 app（api 不直接 new LLMClient，但保险起见放后面）
from novelreel.api import app  # noqa: E402

if __name__ == "__main__":
    print("演示模式启动（假 LLM，无需密钥）→ http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
