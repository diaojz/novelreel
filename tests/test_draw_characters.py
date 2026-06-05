"""生成角色图 Subagent 单测 —— 用降级模式（占位图）真实跑，不调真接口。"""

from novelreel.agents import draw_characters
from novelreel.core.config import MediaConfig
from novelreel.core.imagegen import ImageClient
from novelreel.core.models import Character, ProjectStatus
from novelreel.core.project_manager import ProjectManager


def _img():
    # 空密钥 → 走占位图，真实生成 png 文件
    return ImageClient(MediaConfig(base_url="x", api_key="", image_model="m", video_model="v"))


def test_draw_all_characters(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("原文")
    project.characters = [
        Character(name="沈师傅", role="主角", appearance="背微驼"),
        Character(name="林小满", role="配角", appearance="撑伞少女"),
    ]
    pm.save(project)

    result = draw_characters.run(project, pm, _img())

    assert result.status == "DONE"
    assert result.detail == {"drawn": 2, "total": 2}
    reloaded = pm.load(project.id)
    assert reloaded.status == ProjectStatus.CHARACTERS_DRAWN
    assert reloaded.characters_drawn is True
    # 图文件真实存在
    for c in reloaded.characters:
        assert (pm.project_dir(project.id) / c.character_sheet).exists()


def test_resume_skips_drawn(tmp_path):
    """断点续传：已有 sheet 的角色不重画。"""
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("原文")
    project.characters = [
        Character(name="甲", role="主角", character_sheet="characters/甲.png"),  # 已画
        Character(name="乙", role="配角"),  # 没画
    ]
    pm.save(project)

    result = draw_characters.run(project, pm, _img())
    assert result.detail["drawn"] == 1  # 只画了乙


def test_blocked_without_characters(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("原文")
    result = draw_characters.run(project, pm, _img())
    assert result.status == "BLOCKED"
