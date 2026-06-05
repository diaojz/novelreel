"""API 测试 —— FastAPI TestClient + mock LLM，验证 HTTP 全流程。

注意：BackgroundTasks 在 TestClient 里是同步执行的（请求返回前跑完），
所以建项目后直接查状态就能拿到结果，不用真的等待轮询。
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from novelreel import api

NOVEL = "残灯巷尽头有一家旧钟表铺，主人姓沈，街坊都叫他沈师傅，修表三十年。" * 3

ASSETS = {
    "characters": [{"name": "沈师傅", "aliases": [], "appearance": "背微驼", "personality": "沉默", "role": "主角"}],
    "scenes": [{"name": "钟表铺", "description": "巷尾", "mood": "怀旧"}],
    "props": [{"name": "怀表", "description": "黄铜", "significance": "信物"}],
}
SHOTS = {"shots": [
    {"index": 1, "shot_type": "全景", "visual_description": "雨夜钟表铺", "characters_present": ["沈师傅"], "duration_hint": 4},
]}


@pytest.fixture
def client(tmp_path, monkeypatch):
    # 把 API 用的项目根指向临时目录，避免污染真实 projects/
    from novelreel.core.project_manager import ProjectManager
    monkeypatch.setattr(api, "pm", ProjectManager(root=tmp_path / "projects"))

    # mock 掉编排器里 new 出来的 LLMClient：让两个 Subagent 拿到假返回
    fake_llm = MagicMock()
    fake_llm.chat_json.side_effect = [ASSETS, SHOTS] * 10  # 够多次调用
    monkeypatch.setattr("novelreel.agents.extract_assets.LLMClient", lambda *a, **k: fake_llm)
    monkeypatch.setattr("novelreel.agents.generate_script.LLMClient", lambda *a, **k: fake_llm)
    return TestClient(api.app)


def test_health(client):
    assert client.get("/health").json() == {"ok": True}


def test_create_too_short(client):
    r = client.post("/api/projects", json={"novel_text": "短", "auto_run": False})
    assert r.status_code == 400


def test_full_flow(client):
    # 1. 建项目（auto_run 默认 True → 后台跑提取，停在审核）
    r = client.post("/api/projects", json={"novel_text": NOVEL, "title": "API测试"})
    assert r.status_code == 200
    pid = r.json()["id"]

    # 2. 查状态：应已提取出资产
    r = client.get(f"/api/projects/{pid}")
    body = r.json()
    assert body["status"] == "assets_extracted"
    assert len(body["characters"]) == 1
    assert body["characters"][0]["name"] == "沈师傅"
    assert body["has_script"] is False

    # 3. 确认资产，继续生成分镜
    r = client.post(f"/api/projects/{pid}/run", json={"stop_for_review": False})
    assert r.status_code == 200

    # 4. 查状态：应已完成
    body = client.get(f"/api/projects/{pid}").json()
    assert body["status"] == "done"
    assert body["has_script"] is True

    # 5. 取剧本
    script = client.get(f"/api/projects/{pid}/script").json()
    assert len(script["shots"]) == 1
    assert script["shots"][0]["shot_type"] == "全景"


def test_get_missing_project(client):
    assert client.get("/api/projects/nope").status_code == 404
