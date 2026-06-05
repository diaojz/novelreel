# Changelog

本项目所有重要变更都记录在此。
格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added — P2 生视频 + 合成
- 视频生成客户端 `videogen.py`：封装豆包 Seedance 异步任务（提交→轮询→取 url），无密钥/失败时用 ffmpeg 把分镜图转占位视频降级。
- Subagent⑤ `make_clips`：逐分镜用分镜图作起始帧生成视频片段。
- Subagent⑥ `compose_video` + `compose.py`：用 ffmpeg 把分镜片段合成 `output/final.mp4`（含图片占位也能合成幻灯片视频）。
- 前端：分镜结果页加「生成视频成片」按钮 + 成片 `<video>` 播放器。

### Added — P1 生图
- 数据模型扩展：`character_sheet` / `storyboard_image` / `video_clip` / `final_video` 字段，新增 `DRAWING_CHARACTERS … COMPOSING` 状态链。
- 图片生成客户端 `imagegen.py`：封装豆包 Seedream（`/images/generations`，OpenAI 兼容），支持参考图（角色一致性），无密钥/失败时用 Pillow 画占位图降级。
- `MediaConfig`：复用火山引擎账号，配置图片/视频模型名。
- Subagent③ `draw_characters`：为每个角色生成设计图（一致性基础）。
- Subagent④ `draw_shots`：为每个分镜生成画面图，把出镜角色的设计图作为参考传入，保证角色跨镜一致。

### Added — 编排打通 + 演示数据
- 编排器扩展到 6 个 Subagent，`run_all(target=script/storyboard/video)` 控制跑到哪一步（P0/P1/P2）。
- API：`run` 接口加 `target` 参数，`get_project` 暴露 `final_video`，挂载 `/media` 托管生成产物，新增 `GET /api/projects` 项目列表接口。
- 前端：「我的项目」接真实列表、点卡片打开对应项目分镜；覆盖所有 P1/P2 中间态。
- `scripts/seed_demo_projects.py`：一键生成 3 个推文爆款向演示项目。

### Fixed
- 修复「看着像按钮却点了没反应」的 4 处死交互（侧边栏「我的作品」、「全部›」、折叠原文条展开），全部补上真实功能。经浏览器真实点击全量验证。

## [0.1.0] — 2026-06-05 — P0 文本闭环 MVP

### Added
- 项目脚手架：`uv` 依赖管理、目录结构、教学版 README。
- 产品需求文档 PRD（功能分期 / 数据模型 / 7 节课教学拆解）。
- 设计规范 DESIGN.md + 高保真可交互原型（小云雀同款工作台风，真实图片非 SVG 头像）。
- 数据模型（Pydantic）+ 项目管理（`project.json` 读写，角色等定义只存一处）。
- 豆包文本客户端 `llm.py`：`chat()` 纯文本 + `chat_json()` 结构化 JSON（带 markdown 围栏兜底）。
- Subagent① `extract_assets`：从小说提取角色/场景/道具。
- Subagent② `generate_script`：单集 → 分镜剧本 `shots[]`，分镜数 AI 自定或用户指定。
- 编排器 `orchestrator.py`：明文 Python 状态机（核心 ~25 行），数据状态驱动 + 断点续传 + 决策/执行分离。
- FastAPI 接口（建项目/触发编排/查状态/取剧本）+ 单页前端（贴小说→轮询→看分镜→复制下载 JSON）。
- `scripts/serve_demo.py`：假 LLM 演示服务器，无密钥即可跑通。

[Unreleased]: https://github.com/diaojz/novelreel/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/diaojz/novelreel/releases/tag/v0.1.0
