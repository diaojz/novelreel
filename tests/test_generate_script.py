"""生成分镜剧本 Subagent 单测 —— mock LLM。"""

from unittest.mock import MagicMock

from novelreel.agents import generate_script
from novelreel.core.models import Character, ProjectStatus, Scene
from novelreel.core.project_manager import ProjectManager

NOVEL = "残灯巷尽头有一家旧钟表铺，主人姓沈。" * 5


def _project_with_assets(pm, expected_shots=None):
    project = pm.create(NOVEL, expected_shots=expected_shots)
    project.characters = [Character(name="沈师傅", role="主角")]
    project.scenes = [Scene(name="钟表铺", mood="怀旧")]
    project.status = ProjectStatus.ASSETS_EXTRACTED
    pm.save(project)
    return project


def _fake_llm(shots):
    llm = MagicMock()
    llm.chat_json.return_value = {"shots": shots}
    return llm


def test_generate_success_and_reindex(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = _project_with_assets(pm)
    # 故意给乱序号，验证会被重排成 1,2
    llm = _fake_llm([
        {"index": 9, "shot_type": "全景", "visual_description": "雨夜钟表铺", "characters_present": ["沈师傅"], "duration_hint": 4},
        {"index": 3, "shot_type": "特写", "visual_description": "修表的手", "duration_hint": 5},
    ])

    result = generate_script.run(project, pm, llm)

    assert result.status == "DONE"
    assert result.detail == {"shots": 2, "duration": 9}
    reloaded = pm.load(project.id)
    assert reloaded.status == ProjectStatus.SCRIPT_GENERATED
    script = pm.load_script(reloaded)
    assert [s.index for s in script.shots] == [1, 2]  # 重排成功


def test_generate_blocked_without_assets(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create(NOVEL)  # 没有资产
    result = generate_script.run(project, pm, _fake_llm([]))
    assert result.status == "BLOCKED"


def test_generate_empty_shots_is_error(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = _project_with_assets(pm)
    result = generate_script.run(project, pm, _fake_llm([]))
    assert result.status == "ERROR"
    assert pm.load(project.id).status == ProjectStatus.ERROR


def test_expected_shots_passed_to_prompt(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = _project_with_assets(pm, expected_shots=3)
    llm = _fake_llm([
        {"index": 1, "shot_type": "全景", "visual_description": "x", "duration_hint": 4},
    ])
    generate_script.run(project, pm, llm)
    # 验证 prompt 里带了「恰好 3 个分镜」的指令
    called_prompt = llm.chat_json.call_args[0][0]
    assert "3 个分镜" in called_prompt
