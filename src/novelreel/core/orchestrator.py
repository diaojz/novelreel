"""编排器 —— 整个产品的「大脑」。

这就是 PRD 反复强调的「明文 Python 状态机」：它不藏在任何框架里，
每一行都能在课堂上指着讲。它做的事情极简：

    检测项目当前状态 → 决定下一步该做什么 → 调对应的 Subagent → 更新状态

核心思想（来自 ArcReel）：
- 「数据状态驱动」：下一步做什么，完全由 project.status 决定，不靠内存里的变量。
  所以任意一步崩溃后重新调 advance()，都能从断点续上。
- 「决策与执行分离」：编排器只决策（该跑哪个 Subagent），不碰原文、不调 LLM。
  真正的活由 Subagent 干。
- 「编排器不读原文」：它只把 project 传给 Subagent，原文由 Subagent 自己读。

教学第 5 节课内容。可单独运行：
    uv run python -m novelreel.core.orchestrator <project_id>
"""

from __future__ import annotations

import sys

from ..agents import (
    compose_video,
    draw_characters,
    draw_shots,
    extract_assets,
    generate_script,
    make_clips,
)
from ..agents.extract_assets import AgentResult
from ..core.llm import LLMClient
from .models import Project, ProjectStatus
from .project_manager import ProjectManager

# 目标阶段：跑到哪一步停。默认 script（P0 文本闭环），可要到 storyboard（P1）或 video（P2）
TARGET_SCRIPT = "script"        # 跑到分镜剧本（P0）
TARGET_STORYBOARD = "storyboard"  # 跑到分镜图（P1）
TARGET_VIDEO = "video"          # 跑到视频成片（P2）


def _reached_target(project: Project, pm: ProjectManager, target: str) -> bool:
    """判断是否已经达到目标阶段（达到就停，不继续往下烧钱）。"""
    if target == TARGET_SCRIPT:
        return bool(project.script_path)
    if target == TARGET_STORYBOARD:
        return _shots_drawn(project, pm)
    if target == TARGET_VIDEO:
        return bool(project.final_video)
    return bool(project.script_path)


def advance(project: Project, pm: ProjectManager, llm: LLMClient | None = None) -> AgentResult:
    """推进项目一步：看现在在哪，决定下一步跑什么 Subagent。

    返回这一步的执行结果（AgentResult）。调用方拿到后可以决定是否继续推进。

    这就是状态机的全部：每个 if 判断「这一步的产物有没有」，没有就跑对应
    Subagent。P0（文本）→ P1（生图）→ P2（生视频）层层递进，靠数据状态驱动。
    """
    # P0 ── 还没提取资产 → 提取
    if not project.has_assets and project.status != ProjectStatus.ERROR:
        return extract_assets.run(project, pm, llm)

    # P0 ── 已有资产、没剧本 → 生成分镜剧本
    if project.has_assets and not project.script_path:
        return generate_script.run(project, pm, llm)

    # P1 ── 有剧本、角色还没画设计图 → 画角色图
    if project.script_path and project.characters and not project.characters_drawn:
        return draw_characters.run(project, pm)

    # P1 ── 角色图好了、分镜还没画图 → 画分镜图
    if project.characters_drawn and not _shots_drawn(project, pm):
        return draw_shots.run(project, pm)

    # P2 ── 分镜图好了、还没生成视频片段 → 生成视频
    if _shots_drawn(project, pm) and not _clips_made(project, pm):
        return make_clips.run(project, pm)

    # P2 ── 视频片段好了、还没合成 → 合成成片
    if _clips_made(project, pm) and not project.final_video:
        return compose_video.run(project, pm)

    # 兜底：已经到能到的终点
    return AgentResult("DONE", "当前阶段已全部完成。")


def _shots_drawn(project: Project, pm: ProjectManager) -> bool:
    """剧本里所有分镜都有分镜图了吗？"""
    if not project.script_path:
        return False
    shots = pm.load_script(project).shots
    return bool(shots) and all(s.storyboard_image for s in shots)


def _clips_made(project: Project, pm: ProjectManager) -> bool:
    """剧本里所有分镜都有视频片段了吗？"""
    if not project.script_path:
        return False
    shots = pm.load_script(project).shots
    return bool(shots) and all(s.video_clip for s in shots)


def run_all(
    project: Project,
    pm: ProjectManager,
    llm: LLMClient | None = None,
    stop_for_review: bool = False,
    target: str = TARGET_SCRIPT,
) -> AgentResult:
    """一路推进到目标阶段（或出错 / 停下等审核）。

    target：跑到哪一步停。默认 TARGET_SCRIPT（P0 文本闭环），可要 TARGET_STORYBOARD
    （P1 生图）或 TARGET_VIDEO（P2 视频成片）。达到目标就把状态置 DONE 收尾。

    stop_for_review=True 时（PRD 决策 Q2：审核可选），提取完资产就停下等用户审核。
    """
    last = AgentResult("DONE", "无事可做")
    while True:
        # 已达目标阶段 → 收尾
        if _reached_target(project, pm, target):
            if project.status != ProjectStatus.DONE:
                project.status = ProjectStatus.DONE
                pm.save(project)
            return AgentResult("DONE", last.summary if last.detail else "已达到目标阶段。", last.detail)

        last = advance(project, pm, llm)
        if last.status in ("ERROR", "BLOCKED"):
            return last
        # 提取完资产、且要求停下审核 → 暂停
        if stop_for_review and project.status == ProjectStatus.ASSETS_EXTRACTED:
            return AgentResult("PAUSED_FOR_REVIEW", last.summary, last.detail)


def _main() -> None:
    if len(sys.argv) < 2:
        print("用法：python -m novelreel.core.orchestrator <project_id>")
        sys.exit(1)
    pm = ProjectManager()
    project = pm.load(sys.argv[1])
    print(f"项目：{project.title}（当前状态：{project.status.value}）\n")
    result = run_all(project, pm)
    print(f"\n[{result.status}] {result.summary}")
    print(f"最终状态：{pm.load(project.id).status.value}")


if __name__ == "__main__":
    _main()
