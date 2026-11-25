#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""为站点图片生成轻量变体（手机/慢网省流量），可反复增量运行：
 1. 动图（动画 WebP，≥120KB）：抽第一帧做「海报图」，右下角烧一个 ▶ 角标。
    默认只加载海报（10~30KB），鼠标设备进视口自动换动图，触屏点按才播。
 2. 静态大图（宽 ≥1100 且 ≥100KB）：生成 480w / 1200w 两档，供 HTML srcset 使用。

增量语义（关键）：
  · 用源文件的 sha256[:16] 判断「新增 / 更新」。源图内容变了（同名文件被原站换图）
    就重建变体，**变体文件名自带这个哈希**，所以 URL 跟着变 → 不会吃 30 天浏览器缓存；
  · 源图没变就直接复用已有变体，不重编码（构建时可无脑每次调用）；
  · 清单里已不存在 / 变体不再被引用的文件会被清理（img_opt 是纯派生产物）。

产物：data/assets/img_opt/（gitignore，CI 用 LFS 清单做键缓存）
清单：site/.vitepress/img-variants.json（由 .vitepress/postprocess-media.mjs 读取并改写正文）

用法（仓库根目录）：
  python tools/gen_img_variants.py            # 增量生成（已是最新则几乎瞬时）
  python tools/gen_img_variants.py --force    # 全部重建
  python tools/gen_img_variants.py --dry      # 只统计
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
# 真图字节在 data/assets/img（Git LFS），site/public/img 每次 sync-site 都会从它重建，
# 所以直接读 LFS 目录，本地/CI 都不依赖 sync-site 是否已经跑过。
IMG_DIR = ROOT / "data" / "assets" / "img"
# 变体统一放这个独立目录（site/public 每次 sync-site 都会重建，且被 .gitignore 忽略；
# 这里由 build.mjs 在收尾阶段整目录拷进 dist/img，站点 URL 仍用 /img/ 前缀）。
OUT_DIR = ROOT / "data" / "assets" / "img_opt"
MANIFEST = ROOT / "site" / ".vitepress" / "img-variants.json"

ANIM_MIN_BYTES = 120_000          # 动图 ≥120KB 才做海报
ANIM_POSTER_QUALITY = 78
STATIC_MIN_BYTES = 100_000        # 静态图 ≥100KB
STATIC_MIN_WIDTH = 1100           # 且宽 ≥1100 才做多尺寸
VARIANT_WIDTHS = (480, 1200)
STATIC_QUALITY = 80

DRY = "--dry" in sys.argv
FORCE = "--force" in sys.argv
QUIET = "--quiet" in sys.argv


def log(msg: str) -> None:
    if not QUIET:
        print(msg, flush=True)


def url_of(p: Path) -> str:
    """站点 URL 统一用 /img/<文件名>：
    正文是 v-html 注入的，MirrorContent 只会把 /img/ 前缀补成带 base 的地址
    （见 theme/components/MirrorContent.vue），换别的目录前缀会 404。"""
    return "/img/" + p.name


def sha16(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def draw_badge(im: Image.Image) -> Image.Image:
    """在海报右下角画一个半透明 ▶ 圆角角标，提示「点按播放动画」。"""
    w, h = im.size
    r = max(11, min(20, int(w * 0.055)))
    pad = max(6, int(r * 0.36))
    cx, cy = w - pad - r, h - pad - r

    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(24, 20, 28, 168))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 96), width=1)
    s = r * 0.86
    d.polygon(
        [(cx - s * 0.42, cy - s * 0.62), (cx - s * 0.42, cy + s * 0.62), (cx + s * 0.62, cy)],
        fill=(255, 255, 255, 232),
    )
    return Image.alpha_composite(im.convert("RGBA"), overlay)


def outputs_of(entry: dict) -> list[Path]:
    """清单条目对应的变体文件列表"""
    out: list[Path] = []
    if entry.get("poster"):
        out.append(OUT_DIR / Path(entry["poster"]).name)
    for url, _w in entry.get("srcset") or []:
        out.append(OUT_DIR / Path(url).name)
    return out


def main() -> int:
    if not IMG_DIR.is_dir():
        print(f"[err] 找不到图片目录：{IMG_DIR}")
        return 2

    files = sorted(p for p in IMG_DIR.rglob("*.webp") if p.is_file())
    manifest: dict[str, dict] = {}
    if MANIFEST.exists() and not FORCE:
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    new_manifest: dict[str, dict] = {}
    keep: set[str] = set()
    n_new = n_reuse = 0
    bytes_before = bytes_after = 0

    for p in files:
        size = p.stat().st_size
        if size < STATIC_MIN_BYTES:      # 小图（头像/图标）无需变体
            continue
        key = url_of(p)
        src_sha = sha16(p)

        prev = manifest.get(key)
        if not FORCE and prev and prev.get("srcSha") == src_sha:
            outs = outputs_of(prev)
            if outs and all(o.exists() for o in outs):
                new_manifest[key] = prev
                keep.update(o.name for o in outs)
                n_reuse += 1
                continue

        try:
            with Image.open(p) as im:
                frames = getattr(im, "n_frames", 1)
                w, h = im.size
        except Exception as e:
            log(f"[warn] 读图失败 {p.name}: {e}")
            continue

        # ---- 动图 → 首帧海报 ----
        if frames > 1:
            if size < ANIM_MIN_BYTES:
                continue
            poster = OUT_DIR / f"{p.stem}.{src_sha[:8]}.poster.webp"
            if DRY:
                n_new += 1
                continue
            with Image.open(p) as im:
                frame = draw_badge(im.convert("RGBA"))
            frame.save(poster, "WEBP", quality=ANIM_POSTER_QUALITY, method=6)
            ps = poster.stat().st_size
            bytes_before += size
            bytes_after += ps
            new_manifest[key] = {
                "anim": True,
                "poster": url_of(poster),
                "w": w, "h": h,
                "srcSha": src_sha,
                "origKB": round(size / 1024),
                "posterKB": round(ps / 1024),
            }
            keep.add(poster.name)
            n_new += 1
            log(f"[poster] {p.name} {size // 1024}KB -> {ps // 1024}KB")
            continue

        # ---- 静态大图 → 480w / 1200w ----
        if w < STATIC_MIN_WIDTH:
            continue
        srcset = []
        for vw in VARIANT_WIDTHS:
            if vw >= w - 40:
                continue
            vp = OUT_DIR / f"{p.stem}.{src_sha[:8]}.w{vw}.webp"
            if not DRY and not vp.exists():
                vh = max(1, round(h * vw / w))
                with Image.open(p) as im:
                    mode = "RGBA" if (im.mode in ("RGBA", "LA", "P") or "transparency" in im.info) else "RGB"
                    im.convert(mode).resize((vw, vh), Image.LANCZOS).save(
                        vp, "WEBP", quality=STATIC_QUALITY, method=6
                    )
            srcset.append([url_of(vp), vw])
            keep.add(vp.name)
        if not srcset or DRY:
            continue
        bytes_before += size
        bytes_after += sum((OUT_DIR / Path(u).name).stat().st_size for u, _w in srcset)
        new_manifest[key] = {
            "anim": False, "srcset": srcset, "w": w, "h": h, "srcSha": src_sha,
            "origKB": round(size / 1024),
        }
        n_new += 1

    if DRY:
        log(f"[dry] 需重建 {n_new} 张，可复用 {n_reuse} 张")
        return 0

    # 清理不再被引用的旧变体（源图更新后旧哈希名的文件）
    pruned = 0
    for f in OUT_DIR.glob("*.webp"):
        if f.name not in keep:
            try:
                f.unlink()
                pruned += 1
            except OSError:
                pass

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(new_manifest, ensure_ascii=False, indent=0), encoding="utf-8")

    # 这三行不受 --quiet 影响：构建脚本会取它做一行摘要
    print(f"[media] 变体：重建 {n_new} 张 / 复用 {n_reuse} 张 / 清理 {pruned} 个，清单 {len(new_manifest)} 条", flush=True)
    if n_new:
        print(f"[media] 本次涉及源图 {bytes_before // 1024}KB -> 变体 {bytes_after // 1024}KB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
