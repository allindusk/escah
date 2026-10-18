"""扫描 characters 模板里的表格结构，统计「必殺技 / 固有効果」表的形态。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lxml import html as LH

ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "data" / "parsed" / "i18n" / "characters"

KEY_RE = re.compile(r"\{\{(key\d+)\}\}")


def texts(el) -> str:
    return "".join(el.itertext()).strip()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    heads: dict[str, int] = {}
    rowshapes: dict[str, int] = {}
    pages = 0
    no_table = []
    for tp in sorted(I18N.glob("*.template.html")):
        slug = tp.name[: -len(".template.html")]
        jp = I18N / f"{slug}.json"
        if not jp.exists():
            continue
        data = json.loads(jp.read_text(encoding="utf-8"))
        keys = {k: v.get("ja", "") for k, v in data.items() if k.startswith("key")}
        pages += 1
        doc = LH.fromstring(tp.read_text(encoding="utf-8"))
        found = False
        for tbl in doc.iter("table"):
            rows = tbl.findall(".//tr")
            if not rows:
                continue
            head = texts(rows[0])
            ids = KEY_RE.findall(rows[0].text_content()) or KEY_RE.findall(
                LH.tostring(rows[0], encoding="unicode"))
            ja_head = "".join(keys.get(i, "?") for i in ids)
            if ja_head in ("必殺技", "固有効果"):
                found = True
                heads[ja_head] = heads.get(ja_head, 0) + 1
                shape = []
                for tr in rows[1:]:
                    cells = tr.findall("th") + tr.findall("td")
                    shape.append(len(cells))
                sig = f"{ja_head}:rows={len(rows) - 1},cells={shape}"
                rowshapes[sig] = rowshapes.get(sig, 0) + 1
        if not found:
            no_table.append(slug)
    print("pages:", pages)
    print("heads:", heads)
    print("--- rowshapes ---")
    for k, v in sorted(rowshapes.items(), key=lambda kv: -kv[1]):
        print(f"{v:4d}  {k}")
    print("--- no table:", len(no_table))
    for s in no_table[:40]:
        print("   ", s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
