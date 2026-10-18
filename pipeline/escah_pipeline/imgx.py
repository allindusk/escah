"""图片转码：把源站下载来的 png/gif/jpg/pngv2 统一转成 WebP。

为什么统一成 WebP（2026-10-18 实测，`data/assets/img` 全量 2991 张 / 563MB）：
- PNG  → WebP(q88) 约原体积 **10%**（100×100 头像 42KB→4.5KB，989×508 大图 972KB→92KB）
- JPG  → WebP(q88) 约 35~45%
- GIF  → 动画 WebP 约 **32~59%**（31 帧 976KB→497KB）
合计从 563MB 降到约 145MB，站点首屏图片字节也同比例下降。

约定：站点里**只部署 WebP**，文件名主干仍是 `sha256(源URL)[:16]`（parser 生成），
扩展名固定为 `.webp` —— 与 `parser_puki._rewrite_images` / `registry._img_local_name`
两处命名保持完全一致，否则 frag 里的 `/img/x.webp` 会在磁盘上找不到。
"""
from __future__ import annotations

import io
from pathlib import Path

CANONICAL_EXT = "webp"
# 有损质量：小图（头像/图标/UI 截图）取高一点，大图（立绘/横幅）取 88 视觉上已无差异
QUALITY_SMALL = 90
QUALITY_LARGE = 88
QUALITY_ANIM = 80
METHOD = 6  # 0~6，越大越慢越小；6 对本站 3000 张量级可接受
SMALL_EDGE = 200  # 短边 ≤ 该值视为小图


def _pil():
    from PIL import Image, ImageOps  # 延迟导入：只有真正转码时才需要 Pillow

    return Image, ImageOps


def is_canonical(path: Path) -> bool:
    """已经是 .webp 就不必再转。"""
    return path.suffix.lower().lstrip(".") == CANONICAL_EXT


def convert_bytes(data: bytes, *, quality: int | None = None) -> bytes:
    """把任意支持的图片字节转成 WebP 字节。失败抛异常（调用方决定是否回退原图）。

    动图（多帧 gif/webp）逐帧转 RGBA 后用 save_all 保留动画、帧延时与循环次数。
    """
    Image, ImageOps = _pil()
    im = Image.open(io.BytesIO(data))
    frames = getattr(im, "n_frames", 1)
    buf = io.BytesIO()
    if frames > 1:
        seq = []
        durs = []
        for i in range(frames):
            im.seek(i)
            seq.append(im.convert("RGBA"))
            durs.append(im.info.get("duration", 100) or 100)
        seq[0].save(
            buf,
            "WEBP",
            save_all=True,
            append_images=seq[1:],
            duration=durs,
            loop=im.info.get("loop", 0) or 0,
            quality=quality or QUALITY_ANIM,
            method=METHOD,
        )
        return buf.getvalue()

    im = ImageOps.exif_transpose(im)  # 手机拍的 jpg 带方向标记
    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    q = quality or (QUALITY_SMALL if min(im.size) <= SMALL_EDGE else QUALITY_LARGE)
    im.convert("RGBA" if has_alpha else "RGB").save(
        buf, "WEBP", quality=q, method=METHOD, exact=not has_alpha
    )
    return buf.getvalue()


def convert_file(src: Path, dst: Path | None = None, *, quality: int | None = None) -> tuple[int, int]:
    """转换单个文件；dst 省略则改成同目录同名 .webp。返回 (原字节数, 新字节数)。"""
    dst = dst or src.with_suffix("." + CANONICAL_EXT)
    raw = src.read_bytes()
    out = convert_bytes(raw, quality=quality)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(out)
    return len(raw), len(out)


def download_and_convert(url_bytes: bytes, dst: Path, *, quality: int | None = None) -> tuple[int, int]:
    """下载后立即落地为 WebP（供 assets 流程调用）。返回 (原字节数, 新字节数)。"""
    out = convert_bytes(url_bytes, quality=quality)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(out)
    return len(url_bytes), len(out)
