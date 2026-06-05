"""Subagent ② 生成分镜剧本 —— 根据资产 + 原文，生成 shots[]。

同样是单一职责 Subagent：
- 输入：一个已提取资产的 Project
- 读原文 + project 里已有的角色/场景/道具
- 调 LLM 生成分镜列表，存成 Script，写回 project
- 返回结构化摘要

分镜数遵循 PRD 决策 Q3：用户填了 expected_shots 就按它，没填则 AI 自定。

教学第 4 节课内容。可单独运行：
    uv run python -m novelreel.agents.generate_script <project_id>
"""

from __future__ import annotations

import sys

from ..core.llm import LLMClient, LLMError
from ..core.models import Project, ProjectStatus, Script, Shot
from ..core.project_manager import ProjectManager
from . import prompts
from .extract_assets import AgentResult


def _format_assets(items, fields: list[str]) -> str:
    """把角色/场景/道具列表格式化成喂给 LLM 的简洁文本。"""
    if not items:
        return "（无）"
    lines = []
    for it in items:
        parts = [f"{getattr(it, 'name', '')}"]
        for f in fields:
            val = getattr(it, f, "")
            if val:
                parts.append(f"{f}={val}")
        lines.append("- " + "，".join(parts))
    return "\n".join(lines)


def run(project: Project, pm: ProjectManager, llm: LLMClient | None = None) -> AgentResult:
    """对一个项目执行「生成分镜剧本」。"""
    llm = llm or LLMClient()

    if not project.has_assets:
        return AgentResult("BLOCKED", "还没有提取资产，请先运行提取资产步骤。")

    novel = pm.read_novel(project)

    # 分镜数指令：用户指定 or AI 自定（PRD 决策 Q3）
    if project.expected_shots:
        shot_instruction = f"请生成恰好 {project.expected_shots} 个分镜。"
    else:
        shot_instruction = "请根据剧情自行决定合适的分镜数量（通常 4-8 个）。"

    project.status = ProjectStatus.GENERATING
    pm.save(project)

    try:
        data = llm.chat_json(
            prompts.GENERATE_SCRIPT_PROMPT.format(
                novel=novel,
                characters=_format_assets(project.characters, ["role", "appearance"]),
                scenes=_format_assets(project.scenes, ["description", "mood"]),
                props=_format_assets(project.props, ["description"]),
                shot_count_instruction=shot_instruction,
            ),
            system=prompts.GENERATE_SCRIPT_SYSTEM,
        )
    except LLMError as e:
        project.status = ProjectStatus.ERROR
        project.error_message = str(e)
        pm.save(project)
        return AgentResult("ERROR", f"生成分镜失败：{e}")

    raw_shots = data.get("shots", [])
    if not raw_shots:
        project.status = ProjectStatus.ERROR
        project.error_message = "模型没有返回任何分镜。"
        pm.save(project)
        return AgentResult("ERROR", "模型没有返回任何分镜。")

    # 填进 Shot 模型（重排序号，防 AI 乱编号）
    shots = []
    for i, s in enumerate(raw_shots, start=1):
        s["index"] = i
        shots.append(Shot(**s))

    script = Script(project_id=project.id, shots=shots)
    pm.save_script(project, script)
    project.status = ProjectStatus.SCRIPT_GENERATED
    project.error_message = ""
    pm.save(project)

    total = sum(sh.duration_hint for sh in shots)
    return AgentResult(
        "DONE",
        f"生成 {len(shots)} 个分镜，预计总时长约 {total} 秒",
        detail={"shots": len(shots), "duration": total},
    )


def _main() -> None:
    if len(sys.argv) < 2:
        print("用法：python -m novelreel.agents.generate_script <project_id>")
        sys.exit(1)
    pm = ProjectManager()
    project = pm.load(sys.argv[1])
    result = run(project, pm)
    print(f"[{result.status}] {result.summary}")
    if result.status == "DONE":
        script = pm.load_script(pm.load(project.id))
        for sh in script.shots:
            print(f"  #{sh.index:02d} [{sh.shot_type}] {sh.visual_description[:30]}…")


if __name__ == "__main__":
    _main()
