"""提取资产 Subagent 单测 —— mock LLM，验证三条路径。"""

from unittest.mock import MagicMock

from novelreel.agents import extract_assets
from novelreel.core.llm import LLMError
from novelreel.core.models import ProjectStatus
from novelreel.core.project_manager import ProjectManager

# 一段够长的样例小说
NOVEL = "残灯巷尽头有一家旧钟表铺，主人姓沈。" * 5


def _fake_llm(return_value=None, raises=None):
    llm = MagicMock()
    if raises:
        llm.chat_json.side_effect = raises
    else:
        llm.chat_json.return_value = return_value
    return llm


def test_extract_success(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create(NOVEL, title="测试")
    llm = _fake_llm({
        "characters": [{"name": "沈师傅", "aliases": [], "appearance": "背微驼", "personality": "沉默", "role": "主角"}],
        "scenes": [{"name": "钟表铺", "description": "巷尾旧铺", "mood": "怀旧"}],
        "props": [{"name": "怀表", "description": "黄铜", "significance": "信物"}],
    })

    result = extract_assets.run(project, pm, llm)

    assert result.status == "DONE"
    assert result.detail == {"characters": 1, "scenes": 1, "props": 1}
    # 写回了 project 并落盘
    reloaded = pm.load(project.id)
    assert reloaded.status == ProjectStatus.ASSETS_EXTRACTED
    assert reloaded.characters[0].name == "沈师傅"
    assert reloaded.has_assets is True


def test_extract_too_short(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("太短了")
    result = extract_assets.run(project, pm, _fake_llm({}))
    assert result.status == "BLOCKED"


def test_extract_llm_error_sets_error_status(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create(NOVEL)
    llm = _fake_llm(raises=LLMError("模型抽风了"))
    result = extract_assets.run(project, pm, llm)
    assert result.status == "ERROR"
    reloaded = pm.load(project.id)
    assert reloaded.status == ProjectStatus.ERROR
    assert "抽风" in reloaded.error_message
