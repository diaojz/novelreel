<div align="center">

# 🎬 NovelReel

**小说 → 分镜剧本 → 角色图 / 分镜图 → 视频片段 → 成片**
一条龙把一段小说自动变成推文短视频，对标剪映「小云雀」。

同时是一个**面向零基础学员的 AI 编排教学项目**——用**明文 Python** 复刻三层 Agent 编排范式，编排逻辑能逐行读懂，不藏在任何框架黑盒里。

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Tests](https://img.shields.io/badge/tests-44%20passed-2d8a56)
![License](https://img.shields.io/badge/License-MIT-orange)

</div>

---

## ✨ 它能做什么

输入一段中文小说（≤4000 字），自动产出：

| 阶段 | 产物 | 用的模型 |
|------|------|---------|
| **P0 文本闭环** | 角色 / 场景 / 道具 → 分镜剧本 JSON | 豆包 LLM |
| **P1 生图** | 每个角色的设计图 + 每个分镜的画面图（角色跨镜一致） | 豆包 Seedream |
| **P2 生视频** | 每个分镜的视频片段 → ffmpeg 合成一条成片 | 豆包 Seedance |

**没配密钥也能完整跑通**——生图/生视频会自动降级成占位图/占位视频，整条流水线照样从头跑到成片，方便先看效果、上课演示。配上火山引擎豆包密钥，出的就是真实画面。

---

## 🧠 核心范式：三层编排（明文 Python 状态机）

本项目借鉴开源项目 ArcReel 的「三层 Agent 编排」，但**不依赖任何 Agent 框架**（不用 Claude Agent SDK / LangGraph），整套编排就是一个你能逐行读懂的 Python 状态机。

```
┌──────────────────────────────────────────────┐
│  编排器 orchestrator（大脑，明文状态机 ~25 行）│
│  检测 project.json 状态 → 决定下一步 → 派 Subagent│
│  ★ 不读小说原文、不调模型，只做决策 ★          │
└──────┬───────────────────────────────────────┘
       │ dispatch（只传文件路径）
       ▼
  6 个单一职责 Subagent
   ① 提取资产   ② 生成剧本   ③ 画角色图
   ④ 画分镜图   ⑤ 生成视频   ⑥ 合成成片
       │ 调用
       ▼
  模型客户端层：LLM(豆包) / 图(Seedream) / 视频(Seedance)
       └── 没密钥自动降级占位，绝不中断流水线
```

**四条落地的设计原则：**

1. **重上下文任务隔离** — 啃小说原文的活在 Subagent 里，编排器只持有状态摘要，上下文永不爆。
2. **数据状态驱动** — 下一步做什么完全由 `project.json` 字段填没填决定，天然支持**断点续传**。
3. **决策与执行分离** — 编排器只决策，Subagent 只执行，可复用可测试。
4. **一致性靠数据结构** — 角色定义只存一处，画分镜图时把角色设计图作参考传入，保证同一角色跨镜一致。

---

## 🚀 快速开始

```bash
# 1. 安装依赖（需要 uv：https://docs.astral.sh/uv/）
uv sync --extra dev

# 2. 跑测试（纯本地 mock，不联网不花钱，秒过）
uv run pytest

# 3. 启动 —— 二选一

# 3a) 演示模式：假 LLM + 占位图，无需任何密钥，立刻看完整效果
uv run python scripts/serve_demo.py
#    → 浏览器打开 http://127.0.0.1:8000

# 3b) 真实模式：配好火山引擎豆包密钥
cp .env.example .env                        # 填入 NOVELREEL_LLM_API_KEY
uv run python scripts/check_llm.py          # 先验证密钥连通
uv run uvicorn novelreel.api:app --reload   # 启动
```

打开页面后：贴小说 → 点「开始处理」→ 审核角色/场景/道具（可改可跳过）→ 看分镜剧本 → 点「生成视频成片」→ 等成片播放。

> 需要 [ffmpeg](https://ffmpeg.org/)（P2 合成成片用）。macOS：`brew install ffmpeg`。

---

## 🛠 技术栈

- **Python 3.11+** · **FastAPI** — 后端与编排
- **OpenAI SDK** — 调豆包文本（火山引擎 OpenAI 兼容接口）
- **httpx** — 调 Seedream 生图 / Seedance 异步生视频
- **Pillow** — 占位图降级
- **ffmpeg** — 视频片段合成成片
- **Pydantic** — 数据模型与校验
- 纯 HTML + 原生 JS 单页前端（不上框架）

---

## 📁 目录结构

```
src/novelreel/
├── core/
│   ├── models.py          # Pydantic 数据模型（地基）
│   ├── project_manager.py # 项目目录与 project.json 读写
│   ├── config.py          # 模型接入配置（读 .env）
│   ├── llm.py             # 豆包文本客户端
│   ├── imagegen.py        # 豆包 Seedream 生图客户端（带占位降级）
│   ├── videogen.py        # 豆包 Seedance 生视频客户端（异步 + 降级）
│   ├── compose.py         # ffmpeg 合成
│   └── orchestrator.py    # ★ 编排器：明文 Python 状态机 ★
├── agents/                # 6 个单一职责 Subagent + prompts.py
└── api.py                 # FastAPI 接口
web/                       # 单页前端（index.html）+ 占位素材
scripts/                   # serve_demo / check_llm / seed_demo_projects
samples/ · tests/ · docs/  # 样例小说 / 测试 / 文档
```

---

## 📚 文档

| 文档 | 内容 |
|------|------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构讲解：三层编排、数据流时序图、文件地图、7 节课拆解 |
| [docs/PRD.md](docs/PRD.md) | 产品需求文档（功能分期、数据模型、验收标准） |
| [docs/DESIGN.md](docs/DESIGN.md) | 前端设计规范（小云雀同款工作台风） |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录 |

---

## 🎓 教学定位

这是一个「麻雀虽小五脏俱全」的真实 AI 工程项目，覆盖 LLM 调用、多 Agent 编排、数据状态管理、异步任务、API 设计、前端展示。课程沿「从最薄骨架、每节课加一层肉」推进，共 7 节，每节课结束学员都能跑出新功能看到效果（详见 ARCHITECTURE.md）。

**关键约束**：编排器保持明文极简（核心 ~25 行）、禁用 Agent 框架——因为编排不能是黑盒，学员要能逐行读懂、改得动。

---

## 📄 License

[MIT](LICENSE) —— 与参考项目 ArcReel（AGPL-3.0）**无任何代码继承关系**，全部为本项目自研实现。占位演示图来自 Unsplash（可商用）。
