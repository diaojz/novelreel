"""图片生成客户端单测 —— 验证降级 + 成功路径，不调真实接口。"""

import base64
from unittest.mock import MagicMock

from PIL import Image

from novelreel.core.config import MediaConfig
from novelreel.core.imagegen import ImageClient


def _cfg(key=""):
    return MediaConfig(base_url="http://x", api_key=key, image_model="m", video_model="v")


def test_placeholder_when_no_key(tmp_path):
    """没配密钥 → 生成占位图，文件真实存在且是合法图片。"""
    client = ImageClient(_cfg(""))
    out = tmp_path / "a.png"
    path = client.generate("一只猫站在屋顶", out, size="256x256")
    assert out.exists()
    img = Image.open(path)
    assert img.size == (256, 256)


def test_real_success_b64(tmp_path):
    """有密钥 + mock 返回 b64 → 写出真实图片字节。"""
    client = ImageClient(_cfg("fake-key"))
    # 造一张 1x1 png 的 b64
    buf = tmp_path / "src.png"
    Image.new("RGB", (1, 1), (10, 20, 30)).save(buf)
    b64 = base64.b64encode(buf.read_bytes()).decode()

    fake = MagicMock()
    item = MagicMock(); item.b64_json = b64; item.url = None
    fake.images.generate.return_value = MagicMock(data=[item])
    client._client = fake  # 直接塞入 mock client

    out = tmp_path / "out.png"
    client.generate("测试", out)
    assert out.exists()
    assert Image.open(out).size == (1, 1)


def test_falls_back_on_api_error(tmp_path):
    """真实调用抛错 → 降级占位图，不抛异常。"""
    client = ImageClient(_cfg("fake-key"))
    fake = MagicMock()
    fake.images.generate.side_effect = RuntimeError("接口炸了")
    client._client = fake

    out = tmp_path / "out.png"
    path = client.generate("测试", out, size="128x128")
    assert out.exists()
    assert Image.open(path).size == (128, 128)
