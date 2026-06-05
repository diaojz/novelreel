"""项目管理 —— 负责项目目录的创建，以及 project.json 的读写。

每个项目是 projects/<id>/ 下的一个文件夹：

    projects/<id>/
    ├── project.json     # 核心状态文件（角色/场景/道具/状态）
    ├── source/
    │   └── novel.txt     # 小说原文
    └── scripts/
        └── <id>.json     # 分镜剧本（生成后才有）

所有「读项目 / 存项目」都走这个类，别的模块不直接碰文件，
这样数据落盘的细节集中在一处，好讲也好维护。
"""

from __future__ import annotations

from pathlib import Path

from .models import Project, Script


class ProjectManager:
    """管理 projects/ 目录下的所有项目。"""

    def __init__(self, root: str | Path = "projects") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # ---- 路径辅助 ----
    def project_dir(self, project_id: str) -> Path:
        return self.root / project_id

    def _project_json(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "project.json"

    # ---- 创建 ----
    def create(self, novel_text: str, title: str = "", expected_shots: int | None = None) -> Project:
        """新建一个项目：建目录、写原文、存 project.json。"""
        project = Project(title=title or "未命名项目", expected_shots=expected_shots)

        pdir = self.project_dir(project.id)
        (pdir / "source").mkdir(parents=True, exist_ok=True)
        (pdir / "scripts").mkdir(parents=True, exist_ok=True)

        # 写小说原文
        novel_file = pdir / "source" / "novel.txt"
        novel_file.write_text(novel_text, encoding="utf-8")
        project.novel_path = "source/novel.txt"

        self.save(project)
        return project

    # ---- 读 / 写 ----
    def load(self, project_id: str) -> Project:
        """读取一个已存在的项目。"""
        path = self._project_json(project_id)
        if not path.exists():
            raise FileNotFoundError(f"项目不存在：{project_id}")
        return Project.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, project: Project) -> None:
        """把项目状态写回 project.json（每次改动后调用）。"""
        project.touch()
        path = self._project_json(project.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            project.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def exists(self, project_id: str) -> bool:
        return self._project_json(project_id).exists()

    # ---- 小说原文 ----
    def read_novel(self, project: Project) -> str:
        """读取项目的小说原文。

        关键：编排器不读原文，只把项目传给需要原文的 Subagent，
        由 Subagent 调这个方法自己读 —— 这样大段原文不会污染编排器的上下文。
        """
        novel_file = self.project_dir(project.id) / project.novel_path
        return novel_file.read_text(encoding="utf-8")

    # ---- 分镜剧本 ----
    def save_script(self, project: Project, script: Script) -> str:
        """保存分镜剧本，返回相对路径，并写回 project.script_path。"""
        rel = f"scripts/{project.id}.json"
        path = self.project_dir(project.id) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(script.model_dump_json(indent=2), encoding="utf-8")
        project.script_path = rel
        return rel

    def load_script(self, project: Project) -> Script:
        """读取分镜剧本。"""
        if not project.script_path:
            raise FileNotFoundError("该项目还没有生成分镜剧本")
        path = self.project_dir(project.id) / project.script_path
        return Script.model_validate_json(path.read_text(encoding="utf-8"))
