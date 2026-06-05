"""数据模型 + 项目管理的单元测试。

这些测试不调用 LLM，纯本地，跑得飞快。
教学意义：让学员看到「测试」是怎么保证每一步都对的。
"""

from novelreel.core.models import (
    Character,
    ProjectStatus,
    Prop,
    Scene,
    Script,
    Shot,
)
from novelreel.core.project_manager import ProjectManager


def test_create_project_writes_files(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("从前有座山，山里有座庙。", title="测试小说", expected_shots=5)

    # 项目目录与原文文件都创建了
    pdir = pm.project_dir(project.id)
    assert pdir.exists()
    assert (pdir / "project.json").exists()
    assert (pdir / "source" / "novel.txt").exists()

    # 初始状态正确
    assert project.status == ProjectStatus.INITIALIZED
    assert project.expected_shots == 5
    assert project.has_assets is False


def test_load_roundtrip(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("原文内容", title="往返测试")

    # 改点数据再存
    project.characters.append(Character(name="沈师傅", role="主角", appearance="背微驼"))
    project.scenes.append(Scene(name="钟表铺", mood="怀旧"))
    project.props.append(Prop(name="黄铜怀表", description="缠枝莲表壳"))
    project.status = ProjectStatus.ASSETS_EXTRACTED
    pm.save(project)

    # 重新读出来，数据一致
    loaded = pm.load(project.id)
    assert loaded.id == project.id
    assert loaded.title == "往返测试"
    assert loaded.status == ProjectStatus.ASSETS_EXTRACTED
    assert loaded.characters[0].name == "沈师傅"
    assert loaded.has_assets is True


def test_read_novel(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    text = "这是一段会被 Subagent 读取的小说原文。"
    project = pm.create(text)
    assert pm.read_novel(project) == text


def test_save_and_load_script(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("原文")

    script = Script(
        project_id=project.id,
        shots=[
            Shot(index=1, shot_type="全景", visual_description="雨夜的钟表铺",
                 characters_present=["沈师傅"], caption="残灯巷尽头"),
            Shot(index=2, shot_type="特写", visual_description="修表的手"),
        ],
    )
    rel = pm.save_script(project, script)
    pm.save(project)

    assert rel == f"scripts/{project.id}.json"
    loaded = pm.load_script(pm.load(project.id))
    assert len(loaded.shots) == 2
    assert loaded.shots[0].characters_present == ["沈师傅"]


def test_load_missing_raises(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    try:
        pm.load("nonexistent")
        assert False, "应该抛 FileNotFoundError"
    except FileNotFoundError:
        pass
