# -*- coding: utf-8 -*-
"""盘点作者在表格里用的**颜色**：来源（内联 style / class）、种类、各色对应的内容语义。

用户质问（2026-09-30）："原来的表格不是有样式的吗，作者给表格做了很好区分的颜色，为什么你不沿用" ✓
—— 事实是：
  · **原样镜像页**（mirror/*.html ✓）整块搬了原始 `<table>` ⇒ 内联样式原样保留 ✓；
  · **数据统计页**（stat-*.html ✓）走我的解析器 `parse_shiraberu.py` ✗ —— 它只存了
    文字 + colspan/rowspan + h（表头标记 ✓），**颜色/加粗全丢了** ✗✗。
作者用颜色做**语义编码**（例如"水色 = 需要你填写的单元格"✓，其说明文字就写着
"只填写浅蓝色背景的单元格" ✓）⇒ 丢掉颜色**等于把这条说明变成废话** ✗✗。

用法：python tools/_dev/probe_colors.py [包key] [sheet名前缀]
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_sheet_mirror import PKGS, RAW, extract_table  # noqa: E402

import lxml.html as LH  # noqa: E402

_BG_RE = re.compile(r"background-color:\s*([^;\"']+)", re.I)
_CLASS_BG_RE = re.compile(r"\.(s\d+)\s*\{[^}]*background-color:\s*([^;}]+)", re.I)


def main() -> int:
    key = sys.argv[1] if len(sys.argv) > 1 else "treasure-open"
    prefix = sys.argv[2] if len(sys.argv) > 2 else ""
    d = next((p for p in RAW.glob(PKGS[key] + "*") if p.is_dir()), None)
    if d is None:
        print("找不到包")
        return 1
    # ① 源文件里的 class 级样式表（Google 导出常把配色放在 <style> 的 .sN 里 ✗）
    f0 = sorted(d.glob("*.html"))[0]
    raw0 = f0.read_text(encoding="utf-8", errors="replace")
    cls_map = {m.group(1): m.group(2).strip() for m in _CLASS_BG_RE.finditer(raw0)}
    print(f"【样式来源】{f0.stem}: <style> 里的 .sN 配色 {len(cls_map)} 条；"
          f"内联 style= 出现 {raw0.count('style=')} 次")
    print(f"  样例 class 配色: {list(cls_map.items())[:6]}")
    # ② 逐 sheet 统计实际用到的颜色（内联 + class 两种来源都算 ✓）
    files = [f for f in sorted(d.glob("*.html")) if not prefix or f.stem.startswith(prefix)]
    for f in files[:6]:
        frag = extract_table(f)
        if not frag:
            continue
        root = LH.fragment_fromstring(frag, create_parent="div")
        cells = root.xpath("//td|//th")
        cnt: "collections.Counter[str]" = collections.Counter()
        samples: "dict[str, list[str]]" = collections.defaultdict(list)
        for c in cells:
            bg = ""
            m = _BG_RE.search(c.get("style") or "")
            if m:
                bg = m.group(1).strip()
            else:
                for cl in (c.get("class") or "").split():
                    if cl in cls_map:
                        bg = cls_map[cl]
                        break
            if not bg:
                continue
            key_c = bg.lower().replace(" ", "")
            cnt[key_c] += 1
            if len(samples[key_c]) < 3:
                t = " ".join((c.text_content() or "").split())[:22]
                if t:
                    samples[key_c].append(t)
        print(f"\n## {f.stem}（{len(cells)} 格）")
        for color, n in cnt.most_common(8):
            print(f"   {color:<22} {n:>4} 格   例: {samples[color]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
