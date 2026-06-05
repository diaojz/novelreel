"""图片生成客户端 —— 封装豆包 Seedream 文生图（P1）。

火山引擎方舟的文生图是 OpenAI 兼容的 /images/generations 接口：
    POST {base_url}/images/generations
    body: {model, prompt, size, response_format}
    返回: {data: [{url 或 b64_json}]}

**优雅降级**（教学友好 + 无密钥也能跑）：
没配密钥、或调用失败时，自动生成一张「占位图」（纯色底 + 文字），
保证整条生图流程不中断。配好密钥就是真图。

参考图：Seedream 支持传 image 参数做「图生图 / 多图参考」，
我们用它实现角色一致性 —— 分镜图生成时把角色 sheet 图作为参考传进去。
"""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from openai import OpenAI

from .config import MediaConfig

# 占位图的几种柔和底色（按 prompt 哈希挑一个，保证同内容同色）
_PLACEHOLDER_COLORS = [
    (124, 92, 167), (196, 98, 45), (37, 99, 168),
    (61, 122, 74), (176, 125, 24), (192, 57, 43),
]


class ImageClient:
    """豆包 Seedream 文生图客户端，带占位图降级。"""

    def __init__(self, config: MediaConfig | None = None) -> None:
        self.config = config or MediaConfig.from_env()
        self._client: OpenAI | None = None

    def _client_or_none(self) -> OpenAI | None:
        if not self.config.is_ready:
            return None
        if self._client is None:
            self._client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        return self._client

    def generate(
        self,
        prompt: str,
        out_path: str | Path,
        size: str = "1024x1024",
        reference_images: list[str] | None = None,
    ) -> str:
        """生成一张图，存到 out_path，返回该路径（字符串）。

        reference_images: 参考图的本地路径列表（用于角色一致性）。
        无密钥或失败 → 画占位图，绝不抛异常中断流程。
        """
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        client = self._client_or_none()
        if client is None:
            return self._placeholder(prompt, out, size)

        try:
            kwargs: dict = {
                "model": self.config.image_model,
                "prompt": prompt,
                "size": size,
                "response_format": "b64_json",
            }
            # 有参考图时传 image 参数（Seedream 图生图，保角色一致）
            if reference_images:
                imgs = [self._to_data_uri(p) for p in reference_images if Path(p).exists()]
                if imgs:
                    kwargs["image"] = imgs if len(imgs) > 1 else imgs[0]

            resp = client.images.generate(**kwargs)
            item = resp.data[0]
            if getattr(item, "b64_json", None):
                out.write_bytes(base64.b64decode(item.b64_json))
            elif getattr(item, "url", None):
                out.write_bytes(_download(item.url))
            else:
                return self._placeholder(prompt, out, size)
            return str(out)
        except Exception:
            # 真实调用失败 → 降级占位图，不让一张图失败拖垮整个项目
            return self._placeholder(prompt, out, size)

    # ---- 占位图 ----
    def _placeholder(self, prompt: str, out: Path, size: str) -> str:
        from PIL import Image, ImageDraw

        try:
            w, h = (int(x) for x in size.lower().split("x"))
        except Exception:
            w, h = 1024, 1024
        idx = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % len(_PLACEHOLDER_COLORS)
        color = _PLACEHOLDER_COLORS[idx]
        img = Image.new("RGB", (w, h), color)
        draw = ImageDraw.Draw(img)
        text = (prompt[:18] + "…") if len(prompt) > 18 else prompt
        draw.text((w // 2, h // 2), text, fill=(255, 255, 255), anchor="mm")
        draw.text((w // 2, h - 40), "占位图（未配生图密钥）", fill=(255, 255, 255), anchor="mm")
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out)
        return str(out)

    @staticmethod
    def _to_data_uri(path: str) -> str:
        data = Path(path).read_bytes()
        b64 = base64.b64encode(data).decode()
        return f"data:image/png;base64,{b64}"


def _download(url: str) -> bytes:
    import httpx

    return httpx.get(url, timeout=60).content
