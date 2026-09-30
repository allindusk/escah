# -*- coding: utf-8 -*-
"""盘点作者的 **PDF 发布稿**：页数、是否带图、每页开头文字、以及把若干页渲染成 PNG 供肉眼核对。

背景（2026-09-30 用户质问"你不看原PDF的吗？"✓）：我一直只解析 `recycle_bin/data/*.html`
（Google 表格的**网格导出** ✓），从没打开过同目录的 4 份 PDF ✗。PDF 才是作者的
**最终排版形态** ✓ —— 颜色、图表、只保留要给人看的工作表，都体现在这里 ✓。

用法：python tools/_dev/probe_pdfs.py [渲染页数上限]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "recycle_bin" / "data"
SHOTS = ROOT / "tools" / "_dev" / "shots"
SHOTS.mkdir(parents=True, exist_ok=True)


def images_on_page(page) -> int:
    """该页 XObject 里的图片数（图表/截图在这 ✓）。"""
    try:
        res = page.get("/Resources") or {}
        xo = res.get("/XObject")
        if xo is None:
            return 0
        xo = xo.get_object()
        return sum(1 for k in xo.keys() if xo[k].get_object().get("/Subtype") == "/Image")
    except Exception:  # noqa: BLE001
        return 0


def main() -> int:
    render_max = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    try:
        from pypdf import PdfReader
    except ImportError:
        print("需要 pypdf")
        return 2
    try:
        import pypdfium2 as pdfium
    except ImportError:
        pdfium = None
        print("（无 pypdfium2，跳过渲染）")

    for pdf in sorted(SRC.glob("*.pdf")):
        reader = PdfReader(str(pdf))
        n = len(reader.pages)
        imgs = [images_on_page(p) for p in reader.pages]
        print(f"\n===== {pdf.name}｜{n} 页｜带图页 {sum(1 for i in imgs if i)} 个"
              f"（图总数 {sum(imgs)}）｜{pdf.stat().st_size / 1024:.0f} KB")
        for i, page in enumerate(reader.pages[:4]):
            txt = " ".join((page.extract_text() or "").split())
            print(f"   p{i + 1}: {txt[:150]}")
        if pdfium is not None and n:
            doc = pdfium.PdfDocument(str(pdf))
            for i in range(min(render_max, n)):
                img = doc[i].render(scale=1.6).to_pil()
                out = SHOTS / f"pdf_{pdf.stem[:14]}_p{i + 1}.png"
                img.save(out)
                print(f"   已渲染 → {out.name} ({img.width}x{img.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
