"""合成成片单测 —— 用真实 ffmpeg 把占位图合成 mp4（集成测试）。

如果机器没装 ffmpeg，这些用例自动跳过。
"""

import pytest
from PIL import Image

from novelreel.agents import compose_video
from novelreel.core.compose import has_ffmpeg
from novelreel.core.models import ProjectStatus, Script, Shot
from novelreel.core.project_manager import ProjectManager

pytestmark = pytest.mark.skipif(not has_ffmpeg(), reason="未装 ffmpeg")


def _project_with_clips(pm, as_image=True):
    project = pm.create("原文")
    pdir = pm.project_dir(project.id)
    (pdir / "videos").mkdir(parents=True, exist_ok=True)
    shots = []
    for i in (1, 2):
        # 用图片当占位片段（验证图片也能合成）
        img = pdir / "videos" / f"shot_{i:02d}.png"
        Image.new("RGB", (768, 1024), (30 * i, 60, 90)).save(img)
        shots.append(Shot(index=i, visual_description=f"分镜{i}",
                          video_clip=f"videos/shot_{i:02d}.png", duration_hint=2))
    script = Script(project_id=project.id, shots=shots)
    pm.save_script(project, script)
    pm.save(project)
    return project


def test_compose_from_images(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = _project_with_clips(pm)
    result = compose_video.run(project, pm)

    assert result.status == "DONE"
    assert result.detail == {"clips": 2, "duration": 4}
    reloaded = pm.load(project.id)
    assert reloaded.status == ProjectStatus.DONE
    final = pm.project_dir(project.id) / reloaded.final_video
    assert final.exists()
    assert final.stat().st_size > 0  # 真的合出了一条非空视频


def test_blocked_without_clips(tmp_path):
    pm = ProjectManager(root=tmp_path / "projects")
    project = pm.create("原文")
    script = Script(project_id=project.id, shots=[Shot(index=1, visual_description="x")])
    pm.save_script(project, script)
    pm.save(project)
    result = compose_video.run(project, pm)
    assert result.status == "BLOCKED"
