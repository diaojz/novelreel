"""FastAPI 接口 —— 把编排器包装成 HTTP API，供前端调用。

设计（DESIGN.md）：保持最少原则，核心就 4 个接口 + 轮询：
- POST /api/projects          创建项目（贴小说）
- POST /api/projects/{id}/run 触发编排（后台异步跑）
- GET  /api/projects/{id}     查项目状态（前端每 2 秒轮询这个）
- GET  /api/projects/{id}/script  取分镜剧本

为什么用后台任务：提取资产 / 生成分镜要调 LLM，耗时几十秒。
如果同步等，HTTP 请求会卡住。所以「触发」立刻返回，真正的活在后台跑，
前端靠轮询 status 知道进度 —— 这正是 ArcReel「数据状态驱动」的好处：
状态写在 project.json，前端读它就知道进行到哪了。

教学第 6 节课内容。启动：
    uv run uvicorn novelreel.api:app --reload
"""

from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .core.orchestrator import run_all
from .core.project_manager import ProjectManager

app = FastAPI(title="NovelReel API", version="0.1.0")
pm = ProjectManager()

# 前端静态文件目录（web/）
WEB_DIR = Path(__file__).resolve().parents[2] / "web"


# ---- 请求体 ----
class CreateProjectBody(BaseModel):
    novel_text: str
    title: str = ""
    expected_shots: int | None = None
    auto_run: bool = True  # 创建后是否立刻开跑


class RunBody(BaseModel):
    stop_for_review: bool = False  # True=提取完资产停下等审核
    target: str = "script"          # script(P0) / storyboard(P1) / video(P2)


# ---- 后台任务 ----
def _background_run(project_id: str, stop_for_review: bool, target: str = "script") -> None:
    """后台执行编排（在 BackgroundTasks 里跑，不阻塞 HTTP）。"""
    project = pm.load(project_id)
    run_all(project, pm, stop_for_review=stop_for_review, target=target)


# ---- 接口 ----
@app.post("/api/projects")
def create_project(body: CreateProjectBody, bg: BackgroundTasks) -> dict:
    """创建项目。auto_run=True 时立刻在后台开始提取资产。"""
    text = body.novel_text.strip()
    if len(text) < 50:
        raise HTTPException(400, "小说文本太短，请粘贴至少 50 字的完整段落。")
    if len(text) > 4000:
        raise HTTPException(400, "超出 4000 字上限，请精简后重试。")

    project = pm.create(text, title=body.title, expected_shots=body.expected_shots)
    if body.auto_run:
        # 创建即跑：提取资产后停下等审核（PRD 决策 Q2）
        bg.add_task(_background_run, project.id, True)
    return {"id": project.id, "status": project.status.value}


@app.post("/api/projects/{project_id}/run")
def run_project(project_id: str, body: RunBody, bg: BackgroundTasks) -> dict:
    """触发编排继续推进（如：用户确认资产后继续生成分镜）。"""
    if not pm.exists(project_id):
        raise HTTPException(404, "项目不存在")
    bg.add_task(_background_run, project_id, body.stop_for_review, body.target)
    return {"id": project_id, "started": True, "target": body.target}


@app.get("/api/projects")
def list_projects() -> list[dict]:
    """列出所有项目（前端「我的项目」用）。返回概要，按更新时间倒序。"""
    out = []
    for p in pm.list_all():
        shot_count = 0
        if p.script_path:
            try:
                shot_count = len(pm.load_script(p).shots)
            except Exception:
                shot_count = 0
        out.append({
            "id": p.id,
            "title": p.title,
            "status": p.status.value,
            "shot_count": shot_count,
            "char_count": len(p.characters),
            "updated_at": p.updated_at,
        })
    return out


@app.get("/api/projects/{project_id}")
def get_project(project_id: str) -> dict:
    """查项目状态（前端每 2 秒轮询）。返回状态 + 已提取的资产。"""
    if not pm.exists(project_id):
        raise HTTPException(404, "项目不存在")
    project = pm.load(project_id)
    return {
        "id": project.id,
        "title": project.title,
        "status": project.status.value,
        "error_message": project.error_message,
        "characters": [c.model_dump() for c in project.characters],
        "scenes": [s.model_dump() for s in project.scenes],
        "props": [p.model_dump() for p in project.props],
        "has_script": bool(project.script_path),
        "final_video": f"/media/{project.id}/{project.final_video}" if project.final_video else "",
    }


@app.get("/api/projects/{project_id}/script")
def get_script(project_id: str) -> dict:
    """取分镜剧本（生成完成后调）。"""
    if not pm.exists(project_id):
        raise HTTPException(404, "项目不存在")
    project = pm.load(project_id)
    if not project.script_path:
        raise HTTPException(409, "分镜剧本还没生成")
    return pm.load_script(project).model_dump()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


# ---- 生成产物静态托管 ----
# 把 projects/ 挂到 /media，前端用 /media/<项目id>/storyboards/shot_01.png 加载生成的图。
# 必须在挂载 web 之前（catch-all 的 / 会吞掉后面的路由）。
pm.root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=pm.root), name="media")

# ---- 前端静态托管 ----
# 把 web/ 挂到根路径，访问 http://127.0.0.1:8000/ 直接是前端页面。
if WEB_DIR.exists():
    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    app.mount("/", StaticFiles(directory=WEB_DIR), name="web")
