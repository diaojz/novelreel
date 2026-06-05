"""视频生成客户端 —— 封装豆包 Seedance 文生视频 / 图生视频（P2）。

和生图不同，视频是**异步任务**，三步走：
  1. 提交任务：POST {base_url}/contents/generations/tasks → 返回 task id
  2. 轮询状态：GET {base_url}/contents/generations/tasks/{id} → status:
     queued / running / succeeded / failed
  3. 成功后从返回里取 video_url，下载到本地

**优雅降级**（无密钥 / 失败 / 没装 ffmpeg 时）：
把起始帧图片用 ffmpeg 转成一段几秒的静态视频当占位；连 ffmpeg 都没有时，
退一步复制图片为 .png 占位并返回路径。保证 P2 流程不中断。
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import httpx

from .config import MediaConfig


class VideoClient:
    """Seedance 视频客户端，带占位视频降级。"""

    def __init__(self, config: MediaConfig | None = None, poll_interval: float = 8.0,
                 max_wait: float = 300.0) -> None:
        self.config = config or MediaConfig.from_env()
        self.poll_interval = poll_interval
        self.max_wait = max_wait

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}

    def generate(
        self,
        prompt: str,
        out_path: str | Path,
        first_frame: str | Path | None = None,
        duration: int = 5,
    ) -> str:
        """生成一段视频，存 out_path，返回路径。

        first_frame: 起始帧图片路径（分镜图）。降级时也用它转占位视频。
        无密钥 / 失败 → 占位视频，绝不抛异常。
        """
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if not self.config.is_ready:
            return self._placeholder(first_frame, out, duration)

        try:
            video_url = self._run_task(prompt, first_frame, duration)
            if not video_url:
                return self._placeholder(first_frame, out, duration)
            out.write_bytes(httpx.get(video_url, timeout=120).content)
            return str(out)
        except Exception:
            return self._placeholder(first_frame, out, duration)

    # ---- 真实异步任务：提交 → 轮询 → 取 url ----
    def _run_task(self, prompt: str, first_frame, duration: int) -> str | None:
        base = self.config.base_url.rstrip("/")
        submit_url = f"{base}/contents/generations/tasks"

        content: list[dict] = [{"type": "text", "text": f"{prompt} --dur {duration}"}]
        if first_frame and Path(first_frame).exists():
            import base64 as _b64
            uri = "data:image/png;base64," + _b64.b64encode(Path(first_frame).read_bytes()).decode()
            content.append({"type": "image_url", "image_url": {"url": uri}})

        body = {"model": self.config.video_model, "content": content}
        r = httpx.post(submit_url, json=body, headers=self._headers(), timeout=60)
        r.raise_for_status()
        task_id = r.json().get("id")
        if not task_id:
            return None

        # 轮询
        query_url = f"{submit_url}/{task_id}"
        waited = 0.0
        while waited < self.max_wait:
            time.sleep(self.poll_interval)
            waited += self.poll_interval
            q = httpx.get(query_url, headers=self._headers(), timeout=60)
            q.raise_for_status()
            data = q.json()
            status = data.get("status")
            if status == "succeeded":
                content_out = data.get("content") or {}
                return content_out.get("video_url") or data.get("video_url")
            if status == "failed":
                return None
        return None  # 超时

    # ---- 占位视频 ----
    def _placeholder(self, first_frame, out: Path, duration: int) -> str:
        ffmpeg = shutil.which("ffmpeg")
        out = out.with_suffix(".mp4")
        if ffmpeg and first_frame and Path(first_frame).exists():
            try:
                subprocess.run(
                    [ffmpeg, "-y", "-loop", "1", "-i", str(first_frame),
                     "-t", str(duration), "-vf", "scale=768:1024,format=yuv420p",
                     "-r", "24", str(out)],
                    capture_output=True, timeout=60, check=True,
                )
                return str(out)
            except Exception:
                pass
        # 退而求其次：复制起始帧为 .png 占位（前端能显示，合成时会跳过）
        if first_frame and Path(first_frame).exists():
            placeholder_img = out.with_suffix(".png")
            shutil.copy(first_frame, placeholder_img)
            return str(placeholder_img)
        out.write_bytes(b"")  # 空占位
        return str(out)
