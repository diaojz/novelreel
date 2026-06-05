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

from ..agents import extract_assets, generate_script
from ..agents.extract_assets import AgentResult
from ..core.llm import LLMClient
from .models import Project, ProjectStatus
from .project_manager import ProjectManager


def advance(project: Project, pm: ProjectManager, llm: LLMClient | None = None) -> AgentResult:
    """推进项目一步：看现在在哪，决定下一步跑什么 Subagent。

    返回这一步的执行结果（AgentResult）。调用方拿到后可以决定是否继续推进。
    """
    status = project.status

    # 还没提取资产 → 跑提取资产 Subagent
    if not project.has_assets and status != ProjectStatus.ERROR:
        return extract_assets.run(project, pm, llm)

    # 已提取资产、还没生成剧本 → 跑生成分镜 Subagent
    if project.has_assets and not project.script_path:
        return generate_script.run(project, pm, llm)

    # 剧本已生成 → 标记完成
    if project.script_path:
        project.status = ProjectStatus.DONE
        pm.save(project)
        return AgentResult("DONE", "全流程已完成，分镜剧本已生成。")

    # 兜底（理论上不会走到）
    return AgentResult("BLOCKED", f"无法推进，当前状态：{status}")


def run_all(
    project: Project,
    pm: ProjectManager,
    llm: LLMClient | None = None,
    stop_for_review: bool = False,
) -> AgentResult:
    """一路推进到完成（或出错 / 停下等审核）。

    stop_for_review=True 时（PRD 决策 Q2：审核可选），提取完资产就停下，
    把控制权交还给用户审核；用户确认后再调一次 run_all 继续。
    """
    last = AgentResult("DONE", "无事可做")
    while True:
        last = advance(project, pm, llm)
        if last.status in ("ERROR", "BLOCKED"):
            return last
        if project.status == ProjectStatus.DONE:
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
