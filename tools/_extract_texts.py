"""
_extract_texts.py - 从 data/parsed/ja/**/*.chunks.json 提取待翻译文本，
输出带 [N] key 的 .txt 文件 + 映射 JSON，供 LLM/人工翻译后回注。
回注方式：译文按相同 [N] 格式填入 tools/_translated_texts/ 同名文件，
经 tools/inject_translations.py 写入 tools/_manual_zh.json（zh_patch.py 加载时 merge 为唯一译文来源）。

扫描范围：data/parsed/ja/ 顶层页 + data/parsed/ja/characters/ 子目录。
输出：tools/_texts_for_translation/（顶层页）+ /characters/（角色页）。
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARSED_JA_DIR = ROOT / "data" / "parsed" / "ja"
OUTPUT_DIR = Path(__file__).resolve().parent / "_texts_for_translation"


def process_page(chunks_path: Path, out_dir: Path) -> dict:
    slug = chunks_path.stem.replace(".chunks", "")
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

    translatable = [c for c in chunks if c.get("translate", False)]
    if not translatable:
        return {"slug": slug, "total": len(chunks), "to_translate": 0}

    # TXT：每行 [N] origin_text（原文即回注锚点，无需额外 JSON 映射）
    lines = [f"[{i}] {c['text']}" for i, c in enumerate(translatable)]
    (out_dir / f"{slug}.txt").write_text("\n".join(lines), encoding="utf-8")

    return {"slug": slug, "total": len(chunks), "to_translate": len(translatable)}


def scan(scope_name: str, chunks_dir: Path, out_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(chunks_dir.glob("*.chunks.json"))
    print(f"[{scope_name}] 找到 {len(files)} 个 chunks.json")

    results = []
    with ThreadPoolExecutor(max_workers=max(1, round((os.cpu_count() or 4) * 0.8))) as ex:  # 留约 20% CPU 不占满
        futs = {ex.submit(process_page, f, out_dir): f.stem for f in files}
        for fut in futs:
            try:
                r = fut.result()
                results.append(r)
                if r["to_translate"]:
                    print(f"  {r['slug']}: {r['to_translate']}/{r['total']} 条")
            except Exception as e:
                print(f"  [ERROR] {futs[fut]}: {e}")
    return results


def main():
    all_results = []
    all_results += scan("顶层页", PARSED_JA_DIR, OUTPUT_DIR)
    all_results += scan("角色页", PARSED_JA_DIR / "characters", OUTPUT_DIR / "characters")

    total_all = sum(r["total"] for r in all_results)
    total_ja = sum(r["to_translate"] for r in all_results)
    pages = sum(1 for r in all_results if r["to_translate"] > 0)
    print(f"\n完成：{pages}/{len(all_results)} 页有日文，共 {total_ja}/{total_all} 条待翻译")
    print(f"输出：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
