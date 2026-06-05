"""Subagent ③ 生成角色设计图（P1）—— 一致性的基础。

给每个还没有设计图的角色，按「名字+外貌+性格」生成一张立绘，存进
characters/<安全文件名>.png，并写回 character.character_sheet。

为什么先画角色图：后面画分镜图时，会把出镜角色的这张设计图作为参考图传进去，
让同一个角色在所有分镜里长一样 —— 这就是 ArcReel「先固化角色 sheet 图、
处处引用」的一致性方案。

可单独运行：
    uv run python -m novelreel.agents.draw_characters <project_id>
"""

from __future__ import annotations

import re
import sys

from ..core.imagegen import ImageClient
from ..core.models import Project, ProjectStatus
from ..core.project_manager import ProjectManager
from . import prompts
from .extract_assets import AgentResult


def _safe_name(name: str) -> str:
    """把角色名转成安全的文件名（去掉特殊字符）。"""
    return re.sub(r"[^\w一-鿿-]", "_", name) or "char"


def run(project: Project, pm: ProjectManager, img: ImageClient | None = None) -> AgentResult:
    """为项目里所有缺设计图的角色生成立绘。"""
    img = img or ImageClient()

    if not project.characters:
        return AgentResult("BLOCKED", "还没有角色，请先提取资产。")

    project.status = ProjectStatus.DRAWING_CHARACTERS
    pm.save(project)

    pdir = pm.project_dir(project.id)
    drawn = 0
    for c in project.characters:
        if c.character_sheet:
            continue  # 已有图，跳过（断点续传）
        prompt = prompts.CHARACTER_SHEET_PROMPT.format(
            name=c.name, role=c.role, appearance=c.appearance or "未描述", personality=c.personality or "未描述"
        )
        rel = f"characters/{_safe_name(c.name)}.png"
        img.generate(prompt, pdir / rel, size="768x1024")  # 竖屏立绘
        c.character_sheet = rel
        drawn += 1

    project.status = ProjectStatus.CHARACTERS_DRAWN
    project.error_message = ""
    pm.save(project)

    return AgentResult(
        "DONE",
        f"生成 {drawn} 张角色设计图（共 {len(project.characters)} 个角色）",
        detail={"drawn": drawn, "total": len(project.characters)},
    )


def _main() -> None:
    if len(sys.argv) < 2:
        print("用法：python -m novelreel.agents.draw_characters <project_id>")
        sys.exit(1)
    pm = ProjectManager()
    project = pm.load(sys.argv[1])
    result = run(project, pm)
    print(f"[{result.status}] {result.summary}")
    for c in project.characters:
        print(f"  {c.name} → {c.character_sheet}")


if __name__ == "__main__":
    _main()
