"""Subagent ⑤ 生成视频片段（P2）。

给剧本里每个分镜生成一段视频：
- 用分镜图（storyboard_image）作为起始帧
- prompt 取自画面描述
- 存进 videos/shot_NN.mp4，写回 shot.video_clip

可单独运行：
    uv run python -m novelreel.agents.make_clips <project_id>
"""

from __future__ import annotations

import sys

from ..core.models import Project, ProjectStatus
from ..core.project_manager import ProjectManager
from ..core.videogen import VideoClient
from .extract_assets import AgentResult


def run(project: Project, pm: ProjectManager, vid: VideoClient | None = None) -> AgentResult:
    """为剧本里每个缺视频的分镜生成片段。"""
    vid = vid or VideoClient()

    if not project.script_path:
        return AgentResult("BLOCKED", "还没有分镜剧本。")
    script = pm.load_script(project)
    if not script.shots:
        return AgentResult("BLOCKED", "剧本里没有分镜。")
    if not any(s.storyboard_image for s in script.shots):
        return AgentResult("BLOCKED", "还没有分镜图，请先生成分镜图。")

    pdir = pm.project_dir(project.id)
    project.status = ProjectStatus.GENERATING_VIDEO
    pm.save(project)

    made = 0
    for shot in script.shots:
        if shot.video_clip:
            continue  # 断点续传
        frame = pdir / shot.storyboard_image if shot.storyboard_image else None
        rel = f"videos/shot_{shot.index:02d}.mp4"
        actual = vid.generate(
            shot.visual_description, pdir / rel,
            first_frame=frame, duration=shot.duration_hint,
        )
        # videogen 降级时可能返回 .png；存相对路径
        shot.video_clip = str(actual).replace(str(pdir) + "/", "")
        made += 1

    pm.save_script(project, script)
    project.status = ProjectStatus.VIDEO_GENERATED
    project.error_message = ""
    pm.save(project)

    return AgentResult(
        "DONE",
        f"生成 {made} 段视频片段（共 {len(script.shots)} 个分镜）",
        detail={"made": made, "total": len(script.shots)},
    )


def _main() -> None:
    if len(sys.argv) < 2:
        print("用法：python -m novelreel.agents.make_clips <project_id>")
        sys.exit(1)
    pm = ProjectManager()
    project = pm.load(sys.argv[1])
    result = run(project, pm)
    print(f"[{result.status}] {result.summary}")


if __name__ == "__main__":
    _main()
