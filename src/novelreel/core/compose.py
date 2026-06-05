"""视频合成 —— 用 ffmpeg 把分镜片段拼成一条完整短视频（P2 最后一步）。

输入：每个分镜的 video_clip（可能是真 .mp4，也可能是降级的 .png 占位）。
策略：
- 全是 .mp4：用 ffmpeg concat 拼接。
- 含 .png 占位（没真视频）：把图片按时长转成片段再拼，做成「幻灯片视频」。
- 没装 ffmpeg：跳过，返回空（编排器会据此提示）。

输出：output/final.mp4
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def compose(clips: list[tuple[str, int]], out_path: str | Path) -> str | None:
    """把 (片段路径, 时长秒) 列表合成一条视频，返回成片路径；失败返回 None。

    片段路径可以是 .mp4（直接用）或图片（转成静态片段）。
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not clips:
        return None

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        norm_clips: list[Path] = []

        # 1. 把每个片段标准化成同规格的小 mp4（图片转视频 / 视频重编码）
        for i, (path, dur) in enumerate(clips):
            p = Path(path)
            seg = tmp / f"seg_{i:03d}.mp4"
            if not p.exists():
                continue
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                cmd = [ffmpeg, "-y", "-loop", "1", "-i", str(p), "-t", str(dur),
                       "-vf", "scale=768:1024,format=yuv420p", "-r", "24", str(seg)]
            else:
                cmd = [ffmpeg, "-y", "-i", str(p),
                       "-vf", "scale=768:1024,format=yuv420p", "-r", "24",
                       "-an", str(seg)]
            try:
                subprocess.run(cmd, capture_output=True, timeout=120, check=True)
                norm_clips.append(seg)
            except Exception:
                continue

        if not norm_clips:
            return None

        # 2. concat 列表文件
        listfile = tmp / "list.txt"
        listfile.write_text("".join(f"file '{c}'\n" for c in norm_clips), encoding="utf-8")

        # 3. 拼接
        try:
            subprocess.run(
                [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
                 "-c", "copy", str(out)],
                capture_output=True, timeout=180, check=True,
            )
            return str(out)
        except Exception:
            return None
