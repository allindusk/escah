"""把 data/assets/img 里的存量图片（png/gif/jpg/pngv2）迁移成 WebP，并同步改写全站引用。

一次性迁移脚本，幂等：已存在同名 .webp 的目标会跳过；原文件移到 data/assets/img_orig/ 备份。

改写范围（只动「图片文件名」，不碰任何正文/译文）：
- data/pending_assets.json        URL → 文件名（裸文件名值）
- data/parsed/ja|zh/*.html        /img/<hash>.<ext>
- data/parsed/characters/*.json   img/<hash>.<ext>（icon 字段）
- data/parsed/i18n/*              /img/<hash>.<ext>（模板）

用法:
  python -u tools/migrate_img_webp.py --dry-run          # 只看统计，不动文件
  python -u tools/migrate_img_webp.py --jobs 6           # 正式迁移（先备份原图）
  python -u tools/migrate_img_webp.py --rewrite-only     # 只重跑引用改写（用已有映射）
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "data" / "assets" / "img"
BACKUP = ROOT / "data" / "assets" / "img_orig"
MAP_FILE = ROOT / "tools" / "_dev" / "_img_webp_map.json"
SRC_EXTS = {".png", ".gif", ".jpg", ".jpeg", ".pngv2", ".bmp"}

sys.path.insert(0, str(ROOT / "pipeline"))
from escah_pipeline import imgx  # noqa: E402

# 引用改写：三种上下文（frag/parsed 的 /img/、characters 的 img/、pending_assets 的裸文件名）
PATH_RE = re.compile(r"(/?img/)([0-9a-f]{8,64}\.(?:pngv2|png|gif|jpe?g|webp))")
BARE_RE = re.compile(r"\"([0-9a-f]{8,64}\.(?:pngv2|png|gif|jpe?g|webp))\"")


def plan() -> tuple[list[tuple[Path, Path]], list[dict]]:
    """返回 (待转换 [(src, dst)], 冲突/跳过说明)。"""
    todo: list[tuple[Path, Path]] = []
    notes: list[dict] = []
    for p in sorted(IMG.iterdir()):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in SRC_EXTS:
            continue
        dst = p.with_suffix("." + imgx.CANONICAL_EXT)
        if dst.exists():
            same = False
            try:
                same = imgx.convert_bytes(p.read_bytes()) == dst.read_bytes()
            except Exception:  # noqa: BLE001
                same = False
            if same:
                notes.append({"file": p.name, "action": "skip-identical"})
                continue
            dst = p.with_name(f"{p.stem}-{ext.lstrip('.')}.{imgx.CANONICAL_EXT}")
            notes.append({"file": p.name, "action": "renamed-avoid-clash", "to": dst.name})
        todo.append((p, dst))
    return todo, notes


def convert_one(src: Path, dst: Path) -> dict:
    raw = src.read_bytes()
    t0 = time.time()
    try:
        out = imgx.convert_bytes(raw)
    except Exception as e:  # noqa: BLE001
        return {"file": src.name, "ok": False, "err": str(e)[:120]}
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(out)
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(BACKUP / src.name))
    return {
        "file": src.name,
        "to": dst.name,
        "ok": True,
        "old": len(raw),
        "new": len(out),
        "ms": int((time.time() - t0) * 1000),
    }


def rewrite_refs(mapping: dict[str, str]) -> list[tuple[str, int]]:
    """把全站引用里的旧文件名换成新文件名。返回 [(相对路径, 替换次数)]。"""
    targets: list[Path] = []
    pending = ROOT / "data" / "pending_assets.json"
    if pending.exists():
        targets.append(pending)
    parsed = ROOT / "data" / "parsed"
    for pat in ("*.html", "*.json", "*.template.html"):
        targets.extend(sorted(parsed.rglob(pat)))
    targets.extend(sorted((ROOT / "data" / "assets").glob("*.json")))

    touched: list[tuple[str, int]] = []
    for f in targets:
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        cnt = 0

        def sub_path(m: re.Match) -> str:
            nonlocal cnt
            new = mapping.get(m.group(2))
            if not new:
                return m.group(0)
            cnt += 1
            return m.group(1) + new

        def sub_bare(m: re.Match) -> str:
            nonlocal cnt
            new = mapping.get(m.group(1))
            if not new:
                return m.group(0)
            cnt += 1
            return f'"{new}"'

        new_text = PATH_RE.sub(sub_path, text)
        new_text = BARE_RE.sub(sub_bare, new_text)
        if cnt and new_text != text:
            f.write_text(new_text, encoding="utf-8")
            touched.append((str(f.relative_to(ROOT)), cnt))
    return touched


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--rewrite-only", action="store_true")
    args = ap.parse_args()

    if args.rewrite_only:
        mapping = json.loads(MAP_FILE.read_text(encoding="utf-8"))
        touched = rewrite_refs(mapping)
        for name, cnt in touched:
            print(f"  改写 {name}: {cnt} 处")
        print(f"引用改写完成：{len(touched)} 个文件")
        return

    todo, notes = plan()
    if args.limit:
        todo = todo[: args.limit]
    print(f"待转换 {len(todo)} 张（另有 {len(notes)} 条跳过/改名）")
    for n in notes[:10]:
        print("  ·", n)
    if args.dry_run:
        # 试转 3 张估算收益
        sample = todo[:3]
        for src, dst in sample:
            raw = src.read_bytes()
            out = imgx.convert_bytes(raw)
            print(f"  试转 {src.name}: {len(raw) / 1024:.1f}KB -> {len(out) / 1024:.1f}KB")
        print("dry-run 结束，未改动任何文件")
        return

    mapping: dict[str, str] = {}
    total_old = total_new = 0
    failed: list[dict] = []
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(convert_one, src, dst): (src, dst) for src, dst in todo}
        for fut in as_completed(futs):
            r = fut.result()
            done += 1
            if not r["ok"]:
                failed.append(r)
                print(f"  ✗ 转换失败 {r['file']}: {r['err']}")
                continue
            mapping[r["file"]] = r["to"]
            total_old += r["old"]
            total_new += r["new"]
            if done % 100 == 0 or done == len(todo):
                el = time.time() - t0
                print(f"  {done}/{len(todo)}  {total_old / 1048576:.0f}MB -> {total_new / 1048576:.0f}MB"
                      f"  已用 {el / 60:.1f} 分钟")

    MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    MAP_FILE.write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n转换完成：{len(mapping)} 张，{total_old / 1048576:.0f}MB -> {total_new / 1048576:.0f}MB"
          f"（{(total_new / total_old * 100) if total_old else 0:.1f}%），失败 {len(failed)} 张")
    print(f"原图备份在 {BACKUP}，映射表 {MAP_FILE}")

    touched = rewrite_refs(mapping)
    for name, cnt in touched:
        print(f"  改写 {name}: {cnt} 处")
    print(f"引用改写完成：{len(touched)} 个文件")


if __name__ == "__main__":
    main()
