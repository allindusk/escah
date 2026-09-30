# -*- coding: utf-8 -*-
"""机翻留档与后续精翻（mt = machine translation）。

## 为什么要有这一层

`tools/_todo_translate/` 是**过程目录**：待译清单与 `*_translated.txt` 都是中间产物，
被 .gitignore 忽略、CI 跑完随 runner 消失。于是「这条译文是谷歌机翻的、值得回头精翻」
这个信息**留不下来** —— 机翻结果一旦 `i18n fill` 进真值，就和人工译文混在一起，
事后无从分辨哪些该重译。

本模块把机翻产物单独落档到 **`data/mt/`（入库，随 CI 提交）**：

    data/mt/<slug>.json
    {
      "slug": "main-quest",
      "engine": "gtrans",
      "updated": "2026-09-27",
      "entries": {
        "blk12#3": {"ja": "原文…", "zh": "机翻译文…", "mt_at": "2026-09-27",
                    "applied": true}
      }
    }

每条同时存 **待译文本（ja）** 与 **机翻译文（zh）** —— 正是精翻时需要的上下文。

## 精翻闭环（命令一览）

    python -m escah_pipeline.cli mt record          # CI/本地：机翻落库后留档
    python -m escah_pipeline.cli mt export          # 导出精翻清单 → tools/_mt_refine/
    #   ↑ 把该目录交给别的方式（LLM / 人工）逐条精翻，保持 `[id] 译文` 结构与行数
    python -m escah_pipeline.cli mt apply tools/_mt_refine --write
    #   ↑ 把精翻结果写回 i18n 真值，并把已精翻条目从留档中**销账**
    python -m escah_pipeline.cli mt status          # 还剩多少条待精翻

销账规则（`record` 与 `apply` 两个方向都会检查）：留档条目的 zh 若与真值里的 zh
不再一致（说明被人工/LLM 改过，或又被重译过），就从留档中移除 —— 留档里**永远只剩
还没精翻的机翻内容**，可以直接当作待办列表看。
"""
from __future__ import annotations

import json
import re
from datetime import date as _date
from pathlib import Path

import yaml

from . import config
from .i18n import (
    _blocks_of, _keys_of, _norm, _save_entries, has_i18n, load_entries,
)

MT_DIR = config.DATA_DIR / "mt"
TODO_DIR = config.ROOT / "tools" / "_todo_translate"
DEFAULT_EXPORT_DIR = config.ROOT / "tools" / "_mt_refine"
ENGINE = "gtrans"
BR = "\x01"

# `<slug>_<YYYYMMDD>[_A]_translated.txt`（拆分卷带字母后缀，见 gtrans 的分片输出）
_VOLUME_RE = re.compile(r"^(?P<slug>.+?)_(?P<date>\d{8})(?:_(?P<part>[A-Z]))?_translated\.txt$")
# 清单行：`[key12] 译文` / `[blk12#3] 译文`（段级 id 带 #n）
_ENTRY_LINE = re.compile(r"^\[([A-Za-z]+\d+(?:#\d+)?)\]\s?(.*)$")


# ------------------------------------------------------------------ 工具 ----

def _today() -> str:
    return _date.today().strftime("%Y%m%d")


def _volumes(date: str | None = None) -> "list[tuple[str, str, Path]]":
    """扫描译文卷 → [(slug, date, path)]。date 给定时只取该日期。"""
    out = []
    if not TODO_DIR.exists():
        return out
    for f in sorted(TODO_DIR.glob("*_translated.txt")):
        m = _VOLUME_RE.match(f.name)
        if not m:
            continue
        if date and m.group("date") != date:
            continue
        # 文件名里 slug 的分隔符是 `__`（页名内的 `/` 不能进文件名）
        slug = m.group("slug").replace("__", "/")
        out.append((slug, m.group("date"), f))
    return out


def _parse_entries(text: str) -> "dict[str, str]":
    """解析 `[id] 译文` 清单（剔除 `#` 注释行、容忍条目跨行）。"""
    out: "dict[str, str]" = {}
    cur: "str | None" = None
    buf: "list[str]" = []
    for line in text.splitlines():
        m = _ENTRY_LINE.match(line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1), [m.group(2)]
            continue
        if cur is not None and not line.lstrip().startswith("#"):
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf).strip()
    return out


def _split_id(tid: str) -> "tuple[str, int | None]":
    """`blk12#3` → ("blk12", 3)；`key12` → ("key12", None)。"""
    if "#" in tid:
        base, seg = tid.split("#", 1)
        try:
            return base, int(seg)
        except ValueError:
            return base, None
    return tid, None


def _ja_of(keys: dict, blocks: dict, tid: str) -> str:
    """取条目的日文原文：段级 id 取**该段**，否则取整条。"""
    base, seg = _split_id(tid)
    ent = keys.get(tid) or blocks.get(tid) or keys.get(base) or blocks.get(base) or {}
    if seg is not None:
        segs = (blocks.get(base) or {}).get("ja") or ""
        parts = segs.split(BR)
        return parts[seg - 1] if 0 < seg <= len(parts) else ""
    return ent.get("ja") or ""


def _zh_of(keys: dict, blocks: dict, tid: str) -> str:
    """取真值里该条目的中文（段级 id 取该段）。"""
    base, seg = _split_id(tid)
    if seg is not None:
        parts = ((blocks.get(base) or {}).get("zh") or "").split(BR)
        return parts[seg - 1] if 0 < seg <= len(parts) else ""
    ent = keys.get(tid) or blocks.get(tid) or {}
    return ent.get("zh") or ""


def _load_record(slug: str) -> dict:
    p = MT_DIR / f"{slug.replace('/', '__')}.json"
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save_record(slug: str, rec: dict) -> Path:
    MT_DIR.mkdir(parents=True, exist_ok=True)
    p = MT_DIR / f"{slug.replace('/', '__')}.json"
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                 encoding="utf-8")
    return p


# ---------------------------------------------------------------- record ----

def record(date: str | None = None, verbose: bool = True) -> dict:
    """把译文卷里的机翻内容留档到 data/mt/，并把已精翻的条目销账。

    幂等：同一批卷重复跑不会重复记账；真值被改过的条目会被自动移除（视为已精翻）。
    """
    stats = {"volumes": 0, "recorded": 0, "refined": 0, "pages": 0, "skipped": 0,
             "not_applied": 0}
    # slug → {id: {ja, zh, mt_at, applied}}
    fresh: "dict[str, dict[str, dict]]" = {}
    for slug, vdate, path in _volumes(date):
        if not has_i18n(slug):
            stats["skipped"] += 1
            continue
        stats["volumes"] += 1
        entries = load_entries(slug)
        keys, blocks = _keys_of(entries), _blocks_of(entries)
        got = _parse_entries(path.read_text(encoding="utf-8"))
        bucket = fresh.setdefault(slug, {})
        for tid, zh in got.items():
            if not zh:
                continue                      # 机翻失败留空 → 不算留档内容
            ja = _ja_of(keys, blocks, tid)
            if not ja.strip():
                continue                      # 段不存在（页面改版）→ 跳过
            live = _zh_of(keys, blocks, tid)
            applied = _norm(live) == _norm(zh)
            if not applied:
                # ⚠️ 只留档**真正落库**的机翻（真值 == 机翻译文）。
                #    原因：块内某段为空时整块会被重导出（我的完整性规则），卷里因此夹带着
                #    "早已有旧译文"的段 —— 那些旧译文不是机翻产物，记进来只会污染精翻待办。
                stats["not_applied"] += 1
                continue
            bucket[tid] = {
                "ja": ja,
                "zh": zh,
                "mt_at": vdate,
                "applied": True,
            }

    for slug, new in fresh.items():
        rec = _load_record(slug)
        old = rec.get("entries") or {}
        entries = load_entries(slug)
        keys, blocks = _keys_of(entries), _blocks_of(entries)
        merged = dict(old)
        # ① 销账：老记录里真值已与机翻不同 → 已精翻
        for tid, item in old.items():
            live = _zh_of(keys, blocks, tid)
            if not (item.get("zh") or "").strip():
                merged.pop(tid, None)
                continue
            if (live or "").strip() and _norm(live) != _norm(item.get("zh", "")):
                merged.pop(tid, None)
                stats["refined"] += 1
        # ② 入账：本次机翻内容（新条目，或同一 id 被重译后的新译文）
        for tid, item in new.items():
            prev = merged.get(tid)
            if prev and _norm(prev.get("zh", "")) == _norm(item["zh"]):
                merged[tid] = item           # 内容没变，仅刷新 applied/日期
            else:
                merged[tid] = item
                stats["recorded"] += 1
        if merged:
            rec = {"slug": slug, "engine": ENGINE,
                   "updated": (date or _today()), "entries": merged}
            _save_record(slug, rec)
        elif rec:
            p = MT_DIR / f"{slug.replace('/', '__')}.json"
            if p.exists():
                p.unlink()                   # 全部精翻完 → 移除空文件
        stats["pages"] += 1

    if verbose:
        print(f"[mt] 留档完成：新增/更新 {stats['recorded']} 条，销账（已精翻）"
              f" {stats['refined']} 条，涉及 {stats['pages']} 页"
              f"（扫描译文卷 {stats['volumes']} 个，跳过 {stats['skipped']} 个；"
              f"机翻未落库、不计入留档 {stats['not_applied']} 条）")
        st = status(verbose=False)
        print(f"[mt] 留档总量：{st['pages']} 页 / {st['entries']} 条待精翻"
              f"（其中已落库 {st['applied']} 条、未落库 {st['entries'] - st['applied']} 条）")
    return stats


# ---------------------------------------------------------------- export ----

_EXPORT_HEADER = """\
# 机翻待精翻清单（由 `python -m escah_pipeline.cli mt export` 生成）
# 页：{slug}｜条数：{n}｜机翻引擎：{engine}｜导出日期：{today}
# 怎么用：
#   1) 逐条把 `[id]` 后面的机翻译文改写成精翻译文（**保持 [id] 与条目行结构不变**）；
#   2) 把整份/整目录交给别的方式（LLM、人工）处理都可以，`#` 开头的行会被忽略；
#   3) 改完运行：
#        python -m escah_pipeline.cli mt apply {outdir} --write
#      —— 会按 id 覆盖写回 i18n 真值，并把已精翻条目从留档中销账。
# `# ja:` 行是日文原文参考，保留或删除都不影响 apply。
"""


def export(out: "str | Path | None" = None, date: str | None = None,
           single: bool = False, verbose: bool = True) -> dict:
    """导出精翻清单：默认每页一份；`single=True` 额外合成一份总表。

    总表用 `=== <slug> ===` 分段，`mt apply` 能直接识别（一个文件即可整份交给
    别的方式精翻，不必来回切换 400+ 个小文件）。
    """
    outdir = Path(out) if out else DEFAULT_EXPORT_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    today = _today()
    files = entries = 0
    lines_manifest = [
        "# mt export 清单目录",
        f"# 生成于 {today}｜目录：{outdir}",
        "# 逐页精翻后运行： python -m escah_pipeline.cli mt apply "
        f"{outdir} --write",
        "",
    ]
    combined: "list[str]" = []
    for rec_file in sorted(MT_DIR.glob("*.json")):
        rec = _load_record(rec_file.stem.replace("__", "/"))
        items = rec.get("entries") or {}
        if not items:
            continue
        slug = rec.get("slug") or rec_file.stem.replace("__", "/")
        head = _EXPORT_HEADER.format(slug=slug, n=len(items),
                                     engine=rec.get("engine") or ENGINE,
                                     today=today, outdir=outdir)
        lines = []
        for tid, item in sorted(items.items()):
            lines.append(f"[{tid}] {item.get('zh', '')}")
            ja = (item.get("ja") or "").replace("\n", " ")
            lines.append(f"# ja: {ja}")
        target = outdir / f"{slug.replace('/', '__')}_{today}.txt"
        # 文件名沿用 `<slug>_<日期>.txt` 约定，apply 能直接从文件名还原 slug
        target.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
        combined.append(f"=== {slug} ===")
        combined.extend(lines)
        files += 1
        entries += len(items)
        lines_manifest.append(f"{slug}\t{len(items)} 条\t{target.name}")

    all_path = None
    if single and combined:
        all_path = outdir / f"_all_{today}.txt"
        all_path.write_text(
            "# 机翻待精翻**总表**（由 mt export --single 生成）\n"
            f"# 共 {files} 页 / {entries} 条｜导出日期 {today}\n"
            "# 结构：`=== <页 slug> ===` 分段，段内 `[id] 机翻译文` + `# ja: 原文`。\n"
            "# 精翻时保持 [id] 与 `=== ===` 分段不变；改完运行：\n"
            f"#   python -m escah_pipeline.cli mt apply {all_path} --write\n\n"
            + "\n".join(combined) + "\n", encoding="utf-8")
        lines_manifest.append(f"（总表）\t{entries} 条\t{all_path.name}")

    (outdir / "_manifest.txt").write_text("\n".join(lines_manifest) + "\n",
                                          encoding="utf-8")
    if verbose:
        print(f"[mt] 已导出精翻清单：{files} 页 / {entries} 条 → {outdir}")
        if all_path:
            print(f"[mt] 总表：{all_path}")
        print(f"[mt] 精翻完成后运行： python -m escah_pipeline.cli mt apply "
              f"{outdir} --write")
    return {"files": files, "entries": entries, "outdir": str(outdir),
            "single": str(all_path) if all_path else ""}


# ----------------------------------------------------------------- apply ----

def _iter_input_files(path: Path):
    if path.is_dir():
        for f in sorted(path.glob("*.txt")):
            if f.name.startswith("_"):
                continue
            yield f
    elif path.is_file():
        yield path


# 总表分段标记：`=== <slug> ===`（export --single 产物）
_SECTION_RE = re.compile(r"^===\s*(.+?)\s*===\s*$")


def _iter_sections(text: str) -> "list[tuple[str | None, str]]":
    """把文件按 `=== <slug> ===` 拆成 [(slug, 正文)]。

    没有分段标记时返回 `[(None, 全文)]` —— 调用方据此回退到"按文件名取 slug"。
    """
    parts: "list[tuple[str | None, str]]" = []
    cur: "str | None" = None
    buf: "list[str]" = []
    for line in text.splitlines():
        m = _SECTION_RE.match(line)
        if m:
            if cur is not None:
                parts.append((cur, "\n".join(buf)))
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        parts.append((cur, "\n".join(buf)))
    return parts or [(None, text)]


def apply(path: "str | Path", write: bool = False, verbose: bool = True) -> dict:
    """把精翻清单写回 i18n 真值，并把已精翻条目从留档中销账。

    支持两种输入：
      · **分页文件** `<slug>_<日期>.txt`（`mt export` 的默认产物，或目录）；
      · **总表** `_all_<日期>.txt`（`mt export --single`），按 `=== <slug> ===` 分段识别。

    默认 dry-run（只报告将改哪些条），加 `--write` 才落盘 —— 与项目里
    `phrase-fill` / `retain-scan` 等命令的约定一致。
    """
    src = Path(path)
    if not src.exists():
        raise SystemExit(f"[mt] 路径不存在：{src}")
    stats = {"files": 0, "applied": 0, "refined": 0, "unknown": 0, "empty": 0,
             "unchanged": 0}
    def _apply_page(slug: str, text: str) -> None:
        """把一份单页清单写回真值，并对该页留档销账。"""
        if not has_i18n(slug):
            if verbose:
                print(f"[mt] 跳过（无 i18n）：{slug}")
            return
        stats["files"] += 1
        rec = _load_record(slug)
        recorded = rec.get("entries") or {}
        entries = load_entries(slug)
        keys, blocks = _keys_of(entries), _blocks_of(entries)
        got = _parse_entries(text)
        page_changed = 0
        for tid, zh in got.items():
            if not zh.strip():
                stats["empty"] += 1
                continue
            ja = _ja_of(keys, blocks, tid)
            if not ja.strip():
                stats["unknown"] += 1
                if verbose:
                    print(f"   ! {slug}[{tid}] 真值里找不到该条目，跳过")
                continue
            live = _zh_of(keys, blocks, tid)
            if live and _norm(live) == _norm(zh):
                # 与真值相同：本份清单里这条没被精翻 —— 不算"写回"，也不写盘
                stats["unchanged"] += 1
                continue
            # 只有**真正改了内容**（含与留档机翻不同）才计入写回与销账，
            # 否则「apply 一整份清单」会把 7000 多条没动的条目也算成已精翻（口径失真且白写盘）
            if recorded.get(tid) and _norm(zh) != _norm(recorded[tid].get("zh", "")):
                stats["refined"] += 1
            base, seg = _split_id(tid)
            if seg is not None:
                blk = blocks.get(base)
                if blk is None:
                    stats["unknown"] += 1
                    continue
                parts = (blk.get("zh") or "").split(BR)
                # 段数不足则**补齐空段**再写（2026-09-27 修）。
                # 原先要求 `seg <= len(parts)`，于是 zh 里尚未出现的空段落永远写不进去 ✗：
                # 实测每个角色页的「角色背景文本」块（blk2 等）都有若干段是空的，
                # 精校时改不动它们（mt apply 报「异常跳过」），页面上整句因此只剩日文碎片 ✗✗。
                # 段数只由 ja 决定，补空段不会破坏既有译文（未赋值的段保持空串）。
                ja_parts = (blk.get("ja") or "").split(BR)
                if seg > len(parts):
                    if seg > len(ja_parts):
                        stats["unknown"] += 1
                        continue
                    parts += [""] * (seg - len(parts))
                parts[seg - 1] = zh
                if write:
                    blk["zh"] = BR.join(parts)
            else:
                ent = keys.get(tid) or blocks.get(tid)
                if ent is None:
                    stats["unknown"] += 1
                    continue
                if write:
                    ent["zh"] = zh
            page_changed += 1
        if write and page_changed:
            _save_entries(slug, entries)
        stats["applied"] += page_changed
        # 销账：留档里该页已精翻的条目移除
        if write and recorded:
            for tid in list(recorded):
                live = _zh_of(keys, blocks, tid)
                if not (live or "").strip():
                    continue
                if _norm(live) != _norm(recorded[tid].get("zh", "")):
                    recorded.pop(tid, None)
            if recorded:
                rec["entries"] = recorded
                rec["updated"] = _today()
                _save_record(slug, rec)
            else:
                p = MT_DIR / f"{slug.replace('/', '__')}.json"
                if p.exists():
                    p.unlink()
    for f in _iter_input_files(src):
        text = f.read_text(encoding="utf-8")
        sections = _iter_sections(text)
        if len(sections) == 1 and sections[0][0] is None:
            # 单页文件：slug 从文件名还原（`<slug>_<日期>.txt`，页名里的 `/` 写作 `__`）
            m = re.match(r"^(?P<slug>.+?)_(\d{8})\.txt$", f.name)
            if not m:
                if verbose:
                    print(f"[mt] 跳过（文件名不符合 <slug>_<日期>.txt，"
                          f"且内部无 === 分段）：{f.name}")
                continue
            sections = [(m.group("slug").replace("__", "/"), sections[0][1])]
        for slug, body in sections:
            _apply_page(slug, body)

    verb = "已写回" if write else "将写回"
    if verbose:
        print(f"[mt] {verb} {stats['applied']} 条（{stats['files']} 页）｜"
              f"其中留档内已精翻 {stats['refined']} 条｜未变 {stats['unchanged']}｜"
              f"异常跳过 {stats['unknown']}｜空译文 {stats['empty']}")
        if not write:
            print("[mt] dry-run：加 --write 真正写盘")
    return stats


# ---------------------------------------------------------------- status ----

def status(verbose: bool = True) -> dict:
    """留档概览：多少页、多少条待精翻、多少已落库、分布前几页。"""
    files = sorted(MT_DIR.glob("*.json")) if MT_DIR.exists() else []
    n_entries = n_applied = 0
    per_page: "list[tuple[str, int]]" = []
    oldest = newest = ""
    for p in files:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = rec.get("entries") or {}
        if not items:
            continue
        n_entries += len(items)
        n_applied += sum(1 for it in items.values() if it.get("applied"))
        per_page.append((rec.get("slug") or p.stem.replace("__", "/"), len(items)))
        d = rec.get("updated") or ""
        if d:
            oldest = min(oldest, d) if oldest else d
            newest = max(newest, d) if newest else d
    out = {"pages": len(per_page), "entries": n_entries, "applied": n_applied,
           "oldest": oldest, "newest": newest}
    if verbose:
        print(f"[mt] 留档：{out['pages']} 页 / {n_entries} 条机翻待精翻"
              f"（已落库 {n_applied}，未落库 {n_entries - n_applied}）")
        if oldest:
            print(f"[mt] 记录日期范围：{oldest} ~ {newest}")
        for slug, n in sorted(per_page, key=lambda x: -x[1])[:10]:
            print(f"     {n:5d}  {slug}")
        if not files:
            print("[mt] 尚无留档 —— 先运行 `mt record`（机翻落库后执行）")
    return out
