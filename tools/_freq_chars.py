"""全局频率分析：369 个角色页 ja 源里 patch 后仍含假名的文本节点，按 (次数×长度) 收益排序。
输出 tools/_seg_chars.txt：freq TAB len TAB 原文。跨页高频样板句优先补词收益最大。
"""
import html
import os
import pathlib
import re
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from zh_patch import patch  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
JA = ROOT / "data" / "parsed" / "ja" / "characters"

ka = re.compile(r"[぀-ゟ゠-ヺ]")
tag = re.compile(r"<[^>]+>")


def _freq_file(f: pathlib.Path) -> dict[str, int]:
    """单文件统计 patch 后仍含假名的节点（可在独立进程运行，无共享状态）。"""
    text = f.read_text(encoding="utf-8")
    local: dict[str, int] = {}
    for line in html.unescape(tag.sub("\n", text)).split("\n"):
        line = line.strip()
        if not line or len(line) < 2 or len(line) > 300 or not ka.search(line):
            continue
        out = patch(line)
        if not ka.search(out):
            continue  # 已可译净
        local[line] = local.get(line, 0) + 1
    return local


def main() -> None:
    files = sorted(JA.glob("*.html"))
    workers = max(1, round((os.cpu_count() or 4) * 0.8))  # 留约 20% CPU 不占满
    counts: dict[str, int] = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for local in ex.map(_freq_file, files):
            for s, c in local.items():
                counts[s] = counts.get(s, 0) + c
    rows = sorted(counts.items(), key=lambda x: (-x[1] * len(x[0]),))
    out_lines = [f"{c}\t{len(s)}\t{s}" for s, c in rows[:400]]
    pathlib.Path(ROOT / "tools" / "_seg_chars.txt").write_text("\n".join(out_lines), encoding="utf-8")
    total = sum(c * len(s) for s, c in counts.items())
    print(f"未译净节点：唯一 {len(counts)} 条，总收益字符 {total}；Top400 → tools/_seg_chars.txt（进程池 workers={workers}）")


if __name__ == "__main__":
    main()
