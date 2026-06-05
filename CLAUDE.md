# CLAUDE.md

本文件指导 Claude Code（claude.ai/code）在本仓库工作。

## 项目定位

NovelReel：把一段小说自动变成推文短视频（小说 → 分镜剧本 → 角色图/分镜图 → 视频片段 → 成片），对标剪映「小云雀」。

**同时是面向零基础学员的教学项目**——这一点决定了很多设计取舍：编排逻辑必须是**明文 Python**、能逐行讲，**禁止引入 Agent 框架**（LangGraph / Claude Agent SDK / CrewAI 等），因为框架内部调度对学员是黑盒。改代码时务必守住这条。

## 常用命令

```bash
uv sync --extra dev                          # 装依赖（含测试依赖）
uv run pytest                                # 全量测试（mock，不联网不花钱）
uv run pytest tests/test_orchestrator.py     # 跑单个测试文件
uv run pytest -k "draw_shots"                # 按名字跑某些测试
uv run python scripts/serve_demo.py          # 演示模式启动（假 LLM，无需密钥）→ :8000
uv run uvicorn novelreel.api:app --reload    # 真实模式启动（需 .env 配豆包密钥）
uv run python scripts/check_llm.py           # 验证豆包密钥连通
uv run python scripts/seed_demo_projects.py  # 生成演示项目
```

启动 dev server 后用 Chrome 打开 `http://127.0.0.1:8000/`。

## 架构（务必先理解再改）

三层编排，详见 `docs/ARCHITECTURE.md`：

```
orchestrator.py（编排器·明文状态机）  ← 只决策，不读原文不调模型
   └─ 6 个 Subagent（agents/）         ← 单一职责，自己读原文/调模型，返回 AgentResult
        └─ 模型客户端（core/llm|imagegen|videogen）← 无密钥自动降级占位
所有状态落盘在 projects/<id>/project.json，靠它驱动「下一步做什么」
```

**编排器 `advance()` 是整个项目的核心**：每个 `if` 判断「这一步产物有没有」，没有就派对应 Subagent。`run_all(target=script/storyboard/video)` 控制跑到哪个阶段（P0/P1/P2）。

## 关键约定（改代码时遵守）

- **数据状态驱动**：新增流程步骤 = 在 `models.py` 加状态/字段 + 在 `orchestrator.advance()` 加一个 `if` 判断。别在内存里维护流程指针。
- **决策与执行分离**：编排器不读小说原文、不直接调模型；这些活在 Subagent 里。Subagent 统一返回 `AgentResult(status, summary, detail)`，status ∈ DONE/BLOCKED/ERROR。
- **断点续传**：每个 Subagent 处理前先判断「已完成的跳过」（如已有 `character_sheet` 的角色不重画）。
- **优雅降级**：图片/视频客户端没配密钥或失败时必须降级（占位图/占位视频），绝不抛异常中断流水线。新增模型调用沿用这个模式。
- **提示词与逻辑分离**：所有 prompt 放 `agents/prompts.py`，不写死在业务代码里。
- **一致性靠数据结构**：角色/场景/道具完整定义只存 `project.json` 一处，剧本/分镜只引用名字。

## 测试约定

- 测试**不调真实 LLM/模型**：文本用 mock，图片/视频用「空密钥→降级占位」真实跑（快且免费）。
- 涉及 ffmpeg 的测试用 `pytest.mark.skipif(not has_ffmpeg())` 自动跳过。
- 改了任何核心模块，跑 `uv run pytest` 确认 44 测不回归。

## 前端

- `web/index.html` 单文件、原生 JS、内联 CSS，**不上框架、不加构建步骤**。
- 改前端后用浏览器自动化（agent-browser）真实点击验证交互，别只看代码。
- 视觉是小云雀同款工作台风（浅灰白底 + 左侧白圆角侧边栏 + 黑色主操作 + 真实图片，非 SVG 头像），见 `docs/DESIGN.md`。

## 不要做

- ❌ 引入 Agent 框架 / 把编排逻辑藏进黑盒
- ❌ 把 `.env`、`projects/`（运行时产物）提交进库（已在 .gitignore）
- ❌ 在代码里硬编码密钥
- ❌ 给前端加 React/Vue/构建工具
- ❌ 让某个模型调用失败时直接抛异常中断整条流水线（要降级）

## 提交规范

- 一个逻辑单元一个 commit，每次提交前跑通测试。
- commit message 用中文 `type(scope): 说明`，如 `feat(p1): ...` / `fix(web): ...`。
