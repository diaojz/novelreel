"""编排器单测 —— 用 mock LLM 跑真实的两个 Subagent，验证编排链路。

这是「集成测试」性质：不 mock Subagent，而是让编排器真的依次调用它们，
只把最底层的 LLM 换成假的。这样能验证「状态推进 + 断点续传」整条链路。
"""

from unittest.mock import MagicMock

from novelreel.core import orchestrator
from novelreel.core.models import ProjectStatus
from novelreel.core.project_manager import ProjectManager

NOVEL = "残灯巷尽头有一家旧钟表铺，主人姓沈，街坊都叫他沈师傅。" * 4

ASSETS = {
    "characters": [{"name": "沈师傅", "aliases": [], "appearance": "背微驼", "personality": "沉默", "role": "主角"}],
    "scenes": [{"name": "钟表铺", "description": "巷尾", "mood": "怀旧"}],
    "props": [{"name": "怀表", "description": "黄铜", "significance": "信物"}],
}
SHOTS = {"shots": [
    {"index": 1, "shot_type": "全景", "visual_description": "雨夜钟表铺", "characters_present": ["沈师傅"], "duration_hint": 4},
    {"index": 2, "shot_type": "特写", "visual_description": "修表的手", "duration_hint": 5},
]}


def _llm_returning(*json_returns):
    """每次 chat_json 依次返回给定的值（模拟两步不同输出）。"""
    llm = MagicMock()
    llm.chat_json.side_effect = list(json_returns)
    return llm


def test_run_all_end_to_end(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create(NOVEL, title="端到端")
    llm = _llm_returning(ASSETS, SHOTS)

    result = orchestrator.run_all(project, pm, llm)

    assert result.status == "DONE"
    final = pm.load(project.id)
    assert final.status == ProjectStatus.DONE
    assert final.has_assets
    assert final.script_path
    script = pm.load_script(final)
    assert len(script.shots) == 2


def test_run_all_stop_for_review(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create(NOVEL)
    llm = _llm_returning(ASSETS, SHOTS)

    # 第一次：停在审核
    result = orchestrator.run_all(project, pm, llm, stop_for_review=True)
    assert result.status == "PAUSED_FOR_REVIEW"
    assert pm.load(project.id).status == ProjectStatus.ASSETS_EXTRACTED

    # 用户确认后继续：跑完
    project = pm.load(project.id)
    result2 = orchestrator.run_all(project, pm, llm)
    assert result2.status == "DONE"
    assert pm.load(project.id).status == ProjectStatus.DONE


def test_resume_from_extracted(tmp_path):
    """断点续传：资产已提取，重新推进应直接跳到生成分镜。"""
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create(NOVEL)
    # 先只跑提取
    llm = _llm_returning(ASSETS, SHOTS)
    orchestrator.advance(project, pm, llm)  # 提取
    assert project.status == ProjectStatus.ASSETS_EXTRACTED

    # 模拟「崩溃后重新读项目继续」
    reloaded = pm.load(project.id)
    result = orchestrator.advance(reloaded, pm, llm)  # 应该跑生成分镜
    assert result.detail["shots"] == 2
    # chat_json 一共只被调了 2 次（提取 1 + 生成 1），没重复提取
    assert llm.chat_json.call_count == 2


def test_run_all_to_video_full_pipeline(tmp_path, monkeypatch):
    """P2 全链路：小说→资产→剧本→角色图→分镜图→视频片段→合成成片。

    LLM 用 mock；图/视频客户端无密钥 → 走占位图/占位视频（真实 ffmpeg 合成）。
    验证编排器能一路把 target=video 跑到 final_video。
    """
    import shutil
    if not shutil.which("ffmpeg"):
        import pytest
        pytest.skip("未装 ffmpeg")

    # 清空 media 密钥，强制走降级（占位图/占位视频），不联网不花钱
    monkeypatch.delenv("NOVELREEL_MEDIA_API_KEY", raising=False)
    monkeypatch.delenv("NOVELREEL_LLM_API_KEY", raising=False)

    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create(NOVEL, title="到视频")
    llm = _llm_returning(ASSETS, SHOTS)

    result = orchestrator.run_all(project, pm, llm, target=orchestrator.TARGET_VIDEO)

    assert result.status == "DONE", result.summary
    final = pm.load(project.id)
    assert final.status == ProjectStatus.DONE
    # 每个阶段的产物都在
    assert final.characters_drawn                       # 角色图
    script = pm.load_script(final)
    assert all(s.storyboard_image for s in script.shots)  # 分镜图
    assert all(s.video_clip for s in script.shots)        # 视频片段
    assert final.final_video                              # 成片
    assert (pm.project_dir(final.id) / final.final_video).exists()
