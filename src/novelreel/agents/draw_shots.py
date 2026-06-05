"""Subagent ④ 生成分镜图（P1）—— 一致性的兑现。

给分镜剧本里每个分镜生成画面图：
- 按 画面描述 + 镜头 + 情绪 拼 prompt
- ★ 把出镜角色的设计图（character_sheet）作为参考图传进去 ★
  这样同一个角色在所有分镜里长一样

存进 storyboards/shot_NN.png，写回 shot.storyboard_image。

可单独运行：
    uv run python -m novelreel.agents.draw_shots <project_id>
"""

from __future__ import annotations

import sys

from ..core.imagegen import ImageClient
from ..core.models import Project, ProjectStatus
from ..core.project_manager import ProjectManager
from . import prompts
from .extract_assets import AgentResult


def run(project: Project, pm: ProjectManager, img: ImageClient | None = None) -> AgentResult:
    """为剧本里每个缺图的分镜生成画面图。"""
    img = img or ImageClient()

    if not project.script_path:
        return AgentResult("BLOCKED", "还没有分镜剧本，请先生成剧本。")

    script = pm.load_script(project)
    if not script.shots:
        return AgentResult("BLOCKED", "剧本里没有分镜。")

    # 角色名 → 设计图绝对路径（供参考）
    pdir = pm.project_dir(project.id)
    sheet_of = {
        c.name: str(pdir / c.character_sheet)
        for c in project.characters
        if c.character_sheet
    }

    project.status = ProjectStatus.DRAWING_SHOTS
    pm.save(project)

    drawn = 0
    for shot in script.shots:
        if shot.storyboard_image:
            continue  # 已有，跳过（断点续传）
        # 出镜角色的设计图作为参考，保一致
        refs = [sheet_of[n] for n in shot.characters_present if n in sheet_of]
        note = ("画面中的人物参考所给的角色设计图，保持外貌一致。" if refs else "")
        prompt = prompts.STORYBOARD_PROMPT.format(
            visual=shot.visual_description, shot_type=shot.shot_type,
            mood=shot.mood or "自然", character_note=note,
        )
        rel = f"storyboards/shot_{shot.index:02d}.png"
        img.generate(prompt, pdir / rel, size="768x1024", reference_images=refs or None)
        shot.storyboard_image = rel
        drawn += 1

    # 写回剧本 + 项目状态
    pm.save_script(project, script)
    project.status = ProjectStatus.SHOTS_DRAWN
    project.error_message = ""
    pm.save(project)

    return AgentResult(
        "DONE",
        f"生成 {drawn} 张分镜图（共 {len(script.shots)} 个分镜）",
        detail={"drawn": drawn, "total": len(script.shots)},
    )


def _main() -> None:
    if len(sys.argv) < 2:
        print("用法：python -m novelreel.agents.draw_shots <project_id>")
        sys.exit(1)
    pm = ProjectManager()
    project = pm.load(sys.argv[1])
    result = run(project, pm)
    print(f"[{result.status}] {result.summary}")


if __name__ == "__main__":
    _main()
