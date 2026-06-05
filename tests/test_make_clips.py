"""生成视频片段 Subagent 单测 —— mock VideoClient。"""

from unittest.mock import MagicMock

from novelreel.agents import make_clips
from novelreel.core.models import ProjectStatus, Script, Shot
from novelreel.core.project_manager import ProjectManager


def _vid(returns="videos/shot.mp4"):
    v = MagicMock()
    v.generate.side_effect = lambda prompt, out, **k: str(out)
    return v


def _project_with_storyboards(pm):
    project = pm.create("原文")
    script = Script(project_id=project.id, shots=[
        Shot(index=1, visual_description="夜景", storyboard_image="storyboards/shot_01.png"),
        Shot(index=2, visual_description="特写", storyboard_image="storyboards/shot_02.png"),
    ])
    pm.save_script(project, script)
    pm.save(project)
    return project


def test_make_all_clips(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = _project_with_storyboards(pm)
    result = make_clips.run(project, pm, _vid())

    assert result.status == "DONE"
    assert result.detail == {"made": 2, "total": 2}
    reloaded = pm.load(project.id)
    assert reloaded.status == ProjectStatus.VIDEO_GENERATED
    script = pm.load_script(reloaded)
    assert all(s.video_clip for s in script.shots)


def test_resume_skips_made(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = _project_with_storyboards(pm)
    make_clips.run(project, pm, _vid())
    project = pm.load(project.id)
    result = make_clips.run(project, pm, _vid())
    assert result.detail["made"] == 0


def test_blocked_without_storyboards(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("原文")
    script = Script(project_id=project.id, shots=[Shot(index=1, visual_description="x")])
    pm.save_script(project, script)
    pm.save(project)
    result = make_clips.run(project, pm, _vid())
    assert result.status == "BLOCKED"
