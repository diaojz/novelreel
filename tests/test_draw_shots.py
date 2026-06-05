"""生成分镜图 Subagent 单测 —— 降级模式真实出占位图。"""

from novelreel.agents import draw_shots
from novelreel.core.config import MediaConfig
from novelreel.core.imagegen import ImageClient
from novelreel.core.models import Character, ProjectStatus, Script, Shot
from novelreel.core.project_manager import ProjectManager


def _img():
    return ImageClient(MediaConfig(base_url="x", api_key="", image_model="m", video_model="v"))


def _project_with_script(pm):
    project = pm.create("原文")
    project.characters = [Character(name="沈师傅", role="主角", character_sheet="characters/沈师傅.png")]
    script = Script(project_id=project.id, shots=[
        Shot(index=1, visual_description="钟表铺夜景", characters_present=["沈师傅"], mood="怀旧"),
        Shot(index=2, visual_description="修表特写", characters_present=[], mood="专注"),
    ])
    pm.save_script(project, script)
    pm.save(project)
    return project


def test_draw_all_shots(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = _project_with_script(pm)
    result = draw_shots.run(project, pm, _img())

    assert result.status == "DONE"
    assert result.detail == {"drawn": 2, "total": 2}
    reloaded = pm.load(project.id)
    assert reloaded.status == ProjectStatus.SHOTS_DRAWN
    script = pm.load_script(reloaded)
    for s in script.shots:
        assert s.storyboard_image
        assert (pm.project_dir(project.id) / s.storyboard_image).exists()


def test_resume_skips_drawn(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = _project_with_script(pm)
    # 先全画一遍
    draw_shots.run(project, pm, _img())
    # 再跑：应该一张都不重画
    project = pm.load(project.id)
    result = draw_shots.run(project, pm, _img())
    assert result.detail["drawn"] == 0


def test_blocked_without_script(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("原文")
    result = draw_shots.run(project, pm, _img())
    assert result.status == "BLOCKED"
