"""Subagent ① 提取资产 —— 从小说里提取角色 / 场景 / 道具。

这是「单一职责 Subagent」的范例（来自 ArcReel 范式）：
- 输入：一个 Project（编排器只传项目，不传原文本体）
- 自己读原文：调 ProjectManager.read_novel，原文不经过编排器
- 调 LLM 结构化提取，写回 project
- 返回一个「结构化摘要」给编排器（DONE / 提取了几个角色 等）

教学第 3 节课内容。可单独运行：
    uv run python -m novelreel.agents.extract_assets <project_id>
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from ..core.llm import LLMClient, LLMError
from ..core.models import Character, Project, ProjectStatus, Prop, Scene
from ..core.project_manager import ProjectManager
from . import prompts


@dataclass
class AgentResult:
    """Subagent 的标准返回：状态 + 一句话摘要 + 细节。

    status 取值（仿 ArcReel）：DONE / BLOCKED / ERROR
    编排器拿到这个就能决定下一步，不需要看原文。
    """

    status: str
    summary: str
    detail: dict | None = None


def run(project: Project, pm: ProjectManager, llm: LLMClient | None = None) -> AgentResult:
    """对一个项目执行「提取资产」。"""
    llm = llm or LLMClient()

    # 1. 自己读原文（编排器没传原文，只传了 project）
    novel = pm.read_novel(project)
    if len(novel.strip()) < 50:
        return AgentResult("BLOCKED", "小说原文太短（少于 50 字），无法提取。")

    # 2. 调 LLM 结构化提取
    project.status = ProjectStatus.EXTRACTING
    pm.save(project)
    try:
        data = llm.chat_json(
            prompts.EXTRACT_ASSETS_PROMPT.format(novel=novel),
            system=prompts.EXTRACT_ASSETS_SYSTEM,
        )
    except LLMError as e:
        project.status = ProjectStatus.ERROR
        project.error_message = str(e)
        pm.save(project)
        return AgentResult("ERROR", f"提取资产失败：{e}")

    # 3. 把 LLM 返回的数据填进模型（Pydantic 会校验字段）
    project.characters = [Character(**c) for c in data.get("characters", [])]
    project.scenes = [Scene(**s) for s in data.get("scenes", [])]
    project.props = [Prop(**p) for p in data.get("props", [])]
    project.status = ProjectStatus.ASSETS_EXTRACTED
    project.error_message = ""
    pm.save(project)

    # 4. 返回结构化摘要
    nc, ns, np = len(project.characters), len(project.scenes), len(project.props)
    return AgentResult(
        "DONE",
        f"提取到 {nc} 个角色 · {ns} 个场景 · {np} 个道具",
        detail={"characters": nc, "scenes": ns, "props": np},
    )


def _main() -> None:
    """命令行入口：python -m novelreel.agents.extract_assets <project_id>"""
    if len(sys.argv) < 2:
        print("用法：python -m novelreel.agents.extract_assets <project_id>")
        sys.exit(1)
    pm = ProjectManager()
    project = pm.load(sys.argv[1])
    result = run(project, pm)
    print(f"[{result.status}] {result.summary}")
    for c in project.characters:
        print(f"  角色：{c.name}（{c.role}）— {c.appearance}")


if __name__ == "__main__":
    _main()
