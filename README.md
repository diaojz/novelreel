# NovelReel · 小说 → 推文短视频（教学版）

一个**面向零基础学员**的 AI 编排教学项目：把一本小说，自动拆成「角色 / 场景 / 道具 → 分镜剧本」，复刻字节剪映「小云雀」这类产品的核心工作流。

> 本项目用**明文 Python** 复刻开源项目 ArcReel 的三层 Agent 编排范式。
> 不依赖任何 Agent 框架（不用 Claude Agent SDK），编排逻辑就是你能逐行读懂的 Python——这是为了**讲课**：编排不能是黑盒。

## 核心范式：三层编排

```
主 Agent（编排器 orchestrator）  ← 明文 Python 状态机
  │  检测状态 → 决定下一步 → 调用对应 Subagent → 等结果
  │  ★ 小说原文不进编排器，只传文件路径 ★
  ├─→ Subagent: 提取资产    （读小说，提角色/场景/道具）
  └─→ Subagent: 生成分镜剧本（单集 → scenes[] JSON）
        │  调用
        └─→ LLM 客户端（豆包，OpenAI 兼容）
```

四条从 ArcReel 学来、本项目落地的设计原则：

1. **重上下文任务隔离**：啃小说原文的活在 Subagent 里，编排器只持有状态摘要。
2. **数据状态驱动**：用 `project.json` 里字段填没填来决定下一步，天然支持断点续传。
3. **决策与执行分离**：编排器只决策，Subagent 只执行。
4. **一致性靠数据结构**：角色/场景/道具定义只存一处，剧本里只引用名字。

## MVP 边界（当前阶段）

**小说 → 分镜剧本 JSON（文本闭环）**。先不接图片/视频模型，把编排骨架跑通、验证清楚，再迭代加生图、生视频。

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置豆包密钥
cp .env.example .env
# 编辑 .env 填入火山引擎 API Key

# 3. 跑测试
uv run pytest

# 4. 启动服务（后续步骤提供）
uv run uvicorn novelreel.api:app --reload
```

## 技术栈

- **Python 3.11+** + **FastAPI**：后端与编排
- **OpenAI SDK**：调豆包（火山引擎 OpenAI 兼容接口）
- **Pydantic**：数据模型与校验
- 纯 HTML/JS 单页：看效果

## 目录结构

```
src/novelreel/
├── core/         # 数据模型、项目管理、LLM 客户端、编排器
├── agents/       # 各 Subagent（提取资产、生成剧本）
└── api.py        # FastAPI 接口
web/              # 极简前端页面
samples/          # 样例小说
tests/            # 测试
docs/             # 教学文档与调研笔记
```

## 许可

MIT —— 与参考项目 ArcReel（AGPL-3.0）无代码继承关系，全部为本项目自研实现。
