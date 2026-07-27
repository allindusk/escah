#!/usr/bin/env python3
"""给存量 data/parsed/characters/*.json 补齐 name_zh 字段（查 glossary/names.yaml）。

chara.py 已在 extract_all_characters 写入 name_zh；本脚本仅针对已存在、缺该字段的
存量 JSON 一次性补写，不重解析 sections，避免破坏既有数据。sync-site 会随后复制到
site/public/data/char/。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from escah_pipeline import i18n as I  # noqa: E402

CHAR_DIR = ROOT / "data" / "parsed" / "characters"


def main() -> None:
    n = 0
    for p in sorted(CHAR_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "name_zh" in data:
            continue
        name = data.get("name")
        if not name:
            continue
        z = I.name_zh(name)
        if z is None:
            continue
        data["name_zh"] = z
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        n += 1
    print(f"补齐 name_zh 的角色 JSON 数：{n}")


if __name__ == "__main__":
    main()
