"""一页的译文覆盖度与「渲染口径」日文残留度量（只输出数字，不输出正文）。

为什么看渲染口径：i18n JSON 里 zh 为空很常见（大量标签由词表在渲染期兜底），
**空译 ≠ 页面露日文**。所以要判断「这页还有多少日文」，必须看 render_locale 的产物。

用法：
  python tools/sop/coverage.py "characters/八爪妖蠱ハツネ"
  python tools/sop/coverage.py "characters/八爪妖蠱ハツネ" --list 10   # 另列空译 id（不含正文）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "data" / "parsed" / "i18n"
sys.path.insert(0, str(ROOT / "pipeline"))
from escah_pipeline import i18n  # noqa: E402

KANA = re.compile(r"[\u3041-\u3096\u30a1-\u30fa]")
TAG = re.compile(r"<[^>]+>")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    slug = args[0]
    topn = 10
    if "--list" in sys.argv:
        try:
            topn = int(sys.argv[sys.argv.index("--list") + 1])
        except (IndexError, ValueError):
            pass

    p = I18N / f"{slug}.json"
    if not p.exists():
        print(f"[SKIP] {slug} 没有 i18n")
        return 1
    e = i18n.load_entries(slug)
    keys = i18n._keys_of(e)
    blocks = i18n._blocks_of(e)
    b_ok = sum(1 for v in blocks.values() if (v.get("zh") or "").strip())
    k_ok = sum(1 for v in keys.values() if (v.get("zh") or "").strip())
    print(f"块级 blk: {b_ok}/{len(blocks)}｜节点 key: {k_ok}/{len(keys)}")

    zh = i18n.render_locale(slug, "zh")
    ja = i18n.render_locale(slug, "ja")
    if zh is None:
        print("[SKIP] 该页没有 i18n 模板")
        return 1
    zt, jt = TAG.sub(" ", zh), TAG.sub(" ", ja)
    zk, jk = len(KANA.findall(zt)), len(KANA.findall(jt))
    pct = zk / jk * 100 if jk else 0.0
    print(f"渲染 zh 假名字符: {zk}（原日文 {jk}，残留率 {pct:.2f}%）")

    if topn:
        empt = [(k, len(KANA.findall(v.get("ja") or "")))
                for k, v in keys.items()
                if not (v.get("zh") or "").strip() and KANA.search(v.get("ja") or "")]
        empt.sort(key=lambda x: -x[1])
        print(f"仍空译且含假名的节点: {len(empt)}（前 {min(topn, len(empt))} 个 id／假名字数）")
        for k, n in empt[:topn]:
            print(f"  {k}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
