"""将 4 类子页面的待译文本按 category 归类写入 tools/_todo_translate/<category>/
每个文件夹一份完整、可独立 fill 的 new_translation_<date>.txt（+ 空白 _translated.txt）。
格式与 i18n.extract_todo 完全一致：指令 + # MAP + ===X=== 分段 + [N] 日文。

用法：python tools/extract_subpages.py
回填：翻译各文件夹的 new_translation_<date>_translated.txt 后，逐文件夹运行
      python -m escah_pipeline.cli i18n fill <category>/new_translation_<date>.txt
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))
from escah_pipeline import i18n as I
from escah_pipeline.registry import load_registry

TODO_ROOT = ROOT / "tools" / "_todo_translate"
DATE = date.today().strftime("%Y%m%d")

def main():
    reg = load_registry()
    groups: dict[str, list] = {}
    for e in reg:
        if e.get("category") != "subpage":
            continue
        groups.setdefault(e.get("subgroup", "other"), []).append(e["slug"])

    total_files = 0
    for grp, slugs in groups.items():
        sections: list[str] = []
        map_pairs: list[str] = []
        idx = 0
        for slug in slugs:
            if not I.has_i18n(slug):
                continue
            items = I._untranslated_items(slug)
            if not items:
                continue
            label = I._label(idx)
            idx += 1
            lines = [f"[{i+1}] {I._one_line(it['ja'])}" for i, it in enumerate(items)]
            sections.append(f"\n==={label}===\n" + "\n".join(lines) + "\n")
            map_pairs.append(f"{label}={slug}")
        if not sections:
            print(f"[skip] {grp}: 无待译")
            continue
        folder = TODO_ROOT / grp
        folder.mkdir(parents=True, exist_ok=True)
        todo_path = folder / f"new_translation_{DATE}.txt"
        header = I._TODO_INSTRUCTION + "# MAP " + " ".join(map_pairs) + "\n"
        todo_path.write_text(header + "".join(sections), encoding="utf-8")
        (folder / f"new_translation_{DATE}_translated.txt").touch()
        print(f"[ok] {grp}: {idx} 页 -> {todo_path.name}")
        total_files += 1
    print(f"\n完成：{total_files} 个分类文件夹写入 tools/_todo_translate/")

if __name__ == "__main__":
    main()
