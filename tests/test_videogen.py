"""视频生成客户端单测 —— 验证降级 + 异步成功路径，不调真接口。"""

import shutil
from unittest.mock import MagicMock, patch

from PIL import Image

from novelreel.core.config import MediaConfig
from novelreel.core.videogen import VideoClient


def _cfg(key=""):
    return MediaConfig(base_url="http://x", api_key=key, image_model="m", video_model="v")


def _make_frame(tmp_path):
    f = tmp_path / "frame.png"
    Image.new("RGB", (64, 64), (10, 20, 30)).save(f)
    return f


def test_placeholder_without_key(tmp_path):
    """没密钥 → 占位视频（有 ffmpeg 出 mp4，否则 png 占位），文件存在。"""
    client = VideoClient(_cfg(""))
    frame = _make_frame(tmp_path)
    out = tmp_path / "clip.mp4"
    path = client.generate("一段视频", out, first_frame=frame, duration=2)
    from pathlib import Path
    assert Path(path).exists()
    # 有 ffmpeg → mp4；没有 → 退化成 png 占位
    assert path.endswith(".mp4") or path.endswith(".png")


def test_real_async_success(tmp_path):
    """有密钥 + mock 异步任务（提交→succeeded→下载）→ 写出视频字节。"""
    client = VideoClient(_cfg("fake-key"), poll_interval=0.01, max_wait=1)
    frame = _make_frame(tmp_path)
    out = tmp_path / "clip.mp4"

    submit_resp = MagicMock(); submit_resp.json.return_value = {"id": "task-1"}; submit_resp.raise_for_status = lambda: None
    query_resp = MagicMock(); query_resp.json.return_value = {"status": "succeeded", "content": {"video_url": "http://v/clip.mp4"}}; query_resp.raise_for_status = lambda: None
    dl_resp = MagicMock(); dl_resp.content = b"FAKEVIDEO"

    with patch("novelreel.core.videogen.httpx") as hx:
        hx.post.return_value = submit_resp
        # 第一次 get 是轮询、第二次 get 是下载
        hx.get.side_effect = [query_resp, dl_resp]
        path = client.generate("视频", out, first_frame=frame)

    assert out.read_bytes() == b"FAKEVIDEO"


def test_failed_task_falls_back(tmp_path):
    """任务 failed → 降级占位，不抛异常。"""
    client = VideoClient(_cfg("fake-key"), poll_interval=0.01, max_wait=1)
    frame = _make_frame(tmp_path)
    out = tmp_path / "clip.mp4"

    submit_resp = MagicMock(); submit_resp.json.return_value = {"id": "t"}; submit_resp.raise_for_status = lambda: None
    query_resp = MagicMock(); query_resp.json.return_value = {"status": "failed"}; query_resp.raise_for_status = lambda: None
    with patch("novelreel.core.videogen.httpx") as hx:
        hx.post.return_value = submit_resp
        hx.get.return_value = query_resp
        path = client.generate("视频", out, first_frame=frame, duration=2)

    from pathlib import Path
    assert Path(path).exists()  # 降级产物存在
