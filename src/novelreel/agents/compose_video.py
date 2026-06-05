"""Subagent ⑥ 合成成片（P2 最后一步）。

把所有分镜的 video_clip 按顺序用 ffmpeg 拼成一条完整短视频，存 output/final.mp4，
写回 project.final_video，项目状态置 DONE。

可单独运行：
    uv run python -m novelreel.agents.compose_video <project_id>
"""

from __future__ import annotations

import sys

from ..core.compose import compose, has_ffmpeg
from ..core.models import Project, ProjectStatus
from ..core.project_manager import ProjectManager
from .extract_assets import AgentResult


def run(project: Project, pm: ProjectManager) -> AgentResult:
    if not project.script_path:
        return AgentResult("BLOCKED", "还没有分镜剧本。")
    script = pm.load_script(project)
    clips = [(s.video_clip, s.duration_hint) for s in script.shots if s.video_clip]
    if not clips:
        return AgentResult("BLOCKED", "还没有视频片段，请先生成视频。")

    if not has_ffmpeg():
        return AgentResult("BLOCKED", "未检测到 ffmpeg，无法合成。请先安装 ffmpeg。")

    pdir = pm.project_dir(project.id)
    project.status = ProjectStatus.COMPOSING
    pm.save(project)

    # 片段是相对路径，转绝对路径给 ffmpeg
    abs_clips = [(str(pdir / path), dur) for path, dur in clips]
    out_rel = "output/final.mp4"
    result_path = compose(abs_clips, pdir / out_rel)

    if not result_path:
        project.status = ProjectStatus.ERROR
        project.error_message = "ffmpeg 合成失败。"
        pm.save(project)
        return AgentResult("ERROR", "ffmpeg 合成失败。")

    project.final_video = out_rel
    project.status = ProjectStatus.DONE
    project.error_message = ""
    pm.save(project)

    total = sum(d for _, d in clips)
    return AgentResult(
        "DONE",
        f"合成完成：{len(clips)} 个片段，约 {total} 秒 → {out_rel}",
        detail={"clips": len(clips), "duration": total},
    )


def _main() -> None:
    if len(sys.argv) < 2:
        print("用法：python -m novelreel.agents.compose_video <project_id>")
        sys.exit(1)
    pm = ProjectManager()
    project = pm.load(sys.argv[1])
    result = run(project, pm)
    print(f"[{result.status}] {result.summary}")


if __name__ == "__main__":
    _main()
