"""提取角色页「必殺技 / 固有効果」文本，供人工精翻后再回填 i18n。

用法：
    python tools/_dev/skill_i18n.py stats            # 统计（不写文件）
    python tools/_dev/skill_i18n.py extract          # 生成待精翻清单
    python tools/_dev/skill_i18n.py apply <清单文件>  # 回填（--dry 只报告）

清单格式（只改 ZH 行；JA 行与 [N] 编号不要动；<br> 是分段标记，需保留同等数量）：
    [1] 必杀技·名称  （1 处）
    JA: ネイルアート･インフィニティ
    ZH: 美甲艺术·无限

同一日文原文只在首次出现处列出一次（跨角色去重），译文回填到所有出现位置。
回填同时写 key 与 blk 两套节点（渲染优先用 blk）；若该原文已被
glossary/phrases_manual.yaml（渲染最高优先级）覆盖，则同步改写该手工表。

LLM 精翻流程（2026-10-18 起）：
  1) 我按批次整句翻译，产物写 tools/_todo_translate/skills_llm/batch_NN.txt
     （格式 [N] + JA: + ZH:，ZH 里的 <br> 按中文语境重新断行，数量不必与原文一致）。
  2) python tools/_dev/skill_i18n.py pending tools/_todo_translate/skills_llm
     python tools/_dev/skill_i18n.py merge   tools/_todo_translate/skills_llm
  3) python tools/_dev/skill_i18n.py apply tools/_todo_translate/skills_<日期>_final.txt
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date as _date
from pathlib import Path

from lxml import html as LH

ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "data" / "parsed" / "i18n" / "characters"
OUT_DIR = ROOT / "tools" / "_todo_translate"
MANUAL_YAML = ROOT / "glossary" / "phrases_manual.yaml"
GEN_YAML = ROOT / "glossary" / "phrases.yaml"

KEY_RE = re.compile(r"\{\{(key\d+)\}\}")
BR = "\x01"          # i18n 内部换行占位符
BR_TXT = "<br>"      # 清单里给人看的分段标记
HEADS = ("必殺技", "固有効果")
SUBTABLE = ("名称", "効果")


def _norm(s: str) -> str:
    """与 i18n._norm 一致：NFC + 折叠空白 + 去尾部 †。"""
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "")).strip()
    return re.sub(r"\s*†\s*$", "", t)


def _br_in(s: str) -> str:
    return (s or "").replace("{br}", BR).replace("{BR}", BR).replace("⏎", BR)


def _br_out(s: str) -> str:
    return (s or "").replace(BR, "{br}")


def _key(ja: str) -> str:
    """块内换行统一成内部占位符后的归一化键（与 i18n 的匹配口径一致）。"""
    return _norm(_br_in(ja))


def _cell_keys(cell) -> list[str]:
    return KEY_RE.findall(LH.tostring(cell, encoding="unicode"))


def iter_skill_rows(tpl_path: Path, keys: dict):
    """产出 (区块名, 行序, 名称单元格, 效果单元格)。"""
    doc = LH.fromstring(tpl_path.read_text(encoding="utf-8"))
    for tbl in doc.iter("table"):
        rows = tbl.findall(".//tr")
        if len(rows) < 2:
            continue
        head_ja = re.sub(r"\s+", "", "".join(keys.get(k, "") for k in _cell_keys(rows[0])))
        if head_ja not in HEADS:
            continue
        sub_ja = re.sub(r"\s+", "", "".join(keys.get(k, "") for k in _cell_keys(rows[1])))
        body = rows[2:] if sub_ja in ("名称効果", "効果名称") else rows[1:]
        for idx, tr in enumerate(body):
            cells = [c for c in tr if c.tag in ("td", "th")]
            if len(cells) < 2:
                continue
            yield head_ja, idx, cells[0], cells[-1]


def collect() -> list[dict]:
    """按文档顺序收集条目（已按 ja 去重，记录所有出现位置）。"""
    sections: list[dict] = []
    by_ja: dict[str, dict] = {}
    for tp in sorted(I18N.glob("*.template.html")):
        slug = tp.name[: -len(".template.html")]
        jp = I18N / f"{slug}.json"
        if not jp.exists():
            continue
        data = json.loads(jp.read_text(encoding="utf-8"))
        keys = {k: v.get("ja", "") for k, v in data.items() if k.startswith("key")}
        blocks = data.get("_blocks") or {}
        cur: dict | None = None
        for head, _idx, c1, c2 in iter_skill_rows(tp, keys):
            if cur is None or cur["sec"] != head:
                cur = {"sec": head, "slug": slug, "items": []}
                sections.append(cur)
            for k in _cell_keys(c1):
                ja = keys.get(k, "").strip()
                if not ja:
                    continue
                ent = by_ja.setdefault(_key(ja), {"ja": ja, "kind": "name",
                                                  "locs": [], "members": []})
                ent["locs"].append({"slug": slug, "kind": "key", "id": k})
                cur["items"].append(ent)
            bid = c2.get("data-i18n-blk")
            blk = blocks.get(bid) if bid else None
            ks = _cell_keys(c2)
            if blk and blk.get("ja"):
                ja = blk["ja"]
                loc = {"slug": slug, "kind": "blk", "id": bid}
            elif ks:
                ja = BR.join(keys.get(k, "") for k in ks)
                loc = {"slug": slug, "kind": "blk", "id": None}
            else:
                continue
            ent = by_ja.setdefault(_key(ja), {"ja": ja, "kind": "skill",
                                              "locs": [], "members": []})
            ent["locs"].append(loc)
            for k in ks:
                ent["locs"].append({"slug": slug, "kind": "key", "id": k})
                ent["members"].append({"slug": slug, "kind": "key", "id": k,
                                       "ja": keys.get(k, "")})
            cur["items"].append(ent)
    return sections


def _load_yaml_map(path: Path) -> dict:
    try:
        import yaml
    except Exception:
        return {}
    if not path.exists():
        return {}
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    m = (d.get("phrases") or {}) if isinstance(d, dict) else {}
    return {k: v for k, v in m.items() if isinstance(k, str) and isinstance(v, str)}


def _maps() -> tuple[dict, dict]:
    manual = {_key(k): _br_in(v) for k, v in _load_yaml_map(MANUAL_YAML).items()}
    gen = {_key(k): _br_in(v) for k, v in _load_yaml_map(GEN_YAML).items()}
    return manual, gen


def _cur_zh(ent: dict, manual: dict, gen: dict, cache: dict) -> str:
    """当前实际渲染出的译文（复刻渲染优先级）。"""
    k = _key(ent["ja"])
    if manual.get(k):
        return manual[k]
    for loc in ent["locs"]:
        if loc["kind"] != "blk" or not loc.get("id"):
            continue
        e = cache.get((loc["slug"], loc["id"]))
        if e and e.get("zh"):
            return e["zh"]
    if ent["kind"] != "skill":
        for loc in ent["locs"]:
            if loc["kind"] != "key":
                continue
            e = cache.get((loc["slug"], loc["id"]))
            if e and e.get("zh"):
                return e["zh"]
    if gen.get(k):
        return gen[k]
    # 末路：用成员 key 的译文拼接
    if ent["kind"] == "skill" and ent["members"]:
        parts = []
        for m in ent["members"]:
            e = cache.get((m["slug"], m["id"]))
            z = (e or {}).get("zh") or ""
            parts.append(z or m["ja"])
        return BR.join(parts)
    return ""


def _load_cache() -> dict:
    cache: dict = {}
    for jp in I18N.glob("*.json"):
        slug = jp.stem
        data = json.loads(jp.read_text(encoding="utf-8"))
        for k, v in data.items():
            if k.startswith("key") and isinstance(v, dict):
                cache[(slug, k)] = v
        for k, v in (data.get("_blocks") or {}).items():
            cache[(slug, k)] = v
    return cache


def _stamp() -> str:
    return _date.today().strftime("%Y%m%d")


def cmd_stats() -> int:
    secs = collect()
    seen = {}
    for s in secs:
        for e in s["items"]:
            seen[_key(e["ja"])] = e
    manual, gen = _maps()
    hit_m = sum(1 for k in seen if manual.get(k))
    hit_g = sum(1 for k in seen if gen.get(k) and not manual.get(k))
    names = sum(1 for k, e in seen.items() if e["kind"] == "name")
    print(f"角色页（含技能表）：{len({s['slug'] for s in secs})}")
    print(f"唯一文本：{len(seen)}（名称 {names} / 效果 {len(seen) - names}）")
    print(f"已由 phrases_manual 覆盖：{hit_m}   phrases.yaml（生成表）覆盖：{hit_g}")
    cache = _load_cache()
    kana = re.compile(r"[ぁ-んァ-ヶ]")
    empty = kana_hit = 0
    for k, e in seen.items():
        zh = _cur_zh(e, manual, gen, cache)
        if not zh.strip():
            empty += 1
        elif kana.search(zh):
            kana_hit += 1
    print(f"当前译文：空 {empty} 条 / 仍含假名 {kana_hit} 条")
    return 0


def cmd_extract() -> int:
    secs = collect()
    manual, gen = _maps()
    cache = _load_cache()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _stamp()
    txt = OUT_DIR / f"skills_{stamp}.txt"
    idx = OUT_DIR / f"skills_{stamp}.index.json"

    lines = [
        "# 角色「必杀技 / 固有效果」精翻清单",
        "# 只改 ZH: 行；JA: 行与 [N] 编号保持原样。",
        "# <br> 是分段标记（对应页面上的换行），译文请保留同等数量的 <br>。",
        "# 同一日文原文只列一次（跨角色去重），回填时会写回所有出现位置。",
        "# ZH 行 = 当前实际显示的译文，可直接在其上修改。",
        "",
    ]
    index: dict[str, dict] = {}
    n = 0
    done: set[str] = set()
    for sec in secs:
        buf: list[str] = []
        for ent in sec["items"]:
            k = _key(ent["ja"])
            if k in done:
                continue
            done.add(k)
            n += 1
            no = str(n)
            tag = "名称" if ent["kind"] == "name" else "效果"
            ja = ent["ja"].replace(BR, BR_TXT)
            zh = _cur_zh(ent, manual, gen, cache).replace(BR, BR_TXT)
            buf.append(f"[{no}] {sec['sec']}·{tag}  （{len(ent['locs'])} 处）")
            buf.append(f"JA: {ja}")
            buf.append(f"ZH: {zh}")
            index[no] = {
                "ja": ent["ja"],
                "kind": ent["kind"],
                "manual": bool(manual.get(k)),
                "locs": ent["locs"],
                "members": ent["members"],
            }
        if buf:
            lines.append(f"=== {sec['slug']} / {sec['sec']} ===")
            lines.extend(buf)
            lines.append("")
    txt.write_text("\n".join(lines), encoding="utf-8")
    idx.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"提取 {n} 条唯一文本 -> {txt}")
    print(f"索引 -> {idx}")
    return 0


_ENTRY_RE = re.compile(r"^\[(\d+)\]")
_JA_RE = re.compile(r"^JA:\s?(.*)$")
_ZH_RE = re.compile(r"^ZH:\s?(.*)$")


def parse_list(path: Path) -> dict[str, str]:
    """解析清单：N -> 新译文（<br> 保留，回填时转内部占位符）。"""
    out: dict[str, str] = {}
    cur: str | None = None
    buf: list[str] = []
    state = ""

    def flush() -> None:
        if cur is not None:
            # 译文若被手动折行，直接拼回一行（i18n 的 zh 里不应出现裸换行）
            out[cur] = "".join(buf).strip()

    for raw in path.read_text(encoding="utf-8").splitlines():
        m = _ENTRY_RE.match(raw)
        if m:
            flush()
            cur, buf, state = m.group(1), [], ""
            continue
        if raw.startswith("===") or not raw.strip():
            if raw.startswith("==="):
                flush()
                cur, buf, state = None, [], ""
                continue
            if state == "zh":
                buf.append("")
            continue
        m = _JA_RE.match(raw)
        if m:
            state = "ja"
            continue
        m = _ZH_RE.match(raw)
        if m:
            state = "zh"
            buf = [m.group(1)]
            continue
        if state == "zh":
            buf.append(raw)
    flush()
    return {k: v for k, v in out.items() if v}


def _patch_yaml_manual(pairs: dict[str, str]) -> int:
    """把 {ja: zh} 同步进 phrases_manual.yaml（文本级：只替换已存在键的值）。"""
    if not pairs:
        return 0
    text = MANUAL_YAML.read_text(encoding="utf-8")
    n = 0
    for ja, zh in pairs.items():
        # 键在 yaml 里可能是纯文本或单/双引号包裹；值同理。
        pat = re.compile(
            r"^(?P<ind>\s+)(?P<k>" + re.escape(ja) + r"|'" + re.escape(ja.replace("'", "''"))
            + r"'|\"" + re.escape(ja) + r"\"):\s*(?P<v>[^\n]*)$", re.M)
        m = pat.search(text)
        if not m:
            continue
        q = "'" if zh.startswith(("'", '"', "?", "-", "#", "@", "`")) or ": " in zh else ""
        val = f"'{zh.replace(chr(39), chr(39) * 2)}'" if q else zh
        text = text[:m.start("v")] + val + text[m.end("v"):]
        n += 1
    if n:
        MANUAL_YAML.write_text(text, encoding="utf-8")
    return n


def cmd_apply(list_path: Path, dry: bool = False) -> int:
    m = re.search(r"skills_(\d{8})", list_path.stem)
    if not m:
        print(f"文件名需含 skills_<YYYYMMDD>：{list_path.name}")
        return 1
    idx_path = list_path.with_name(f"skills_{m.group(1)}.index.json")
    if not idx_path.exists():
        print(f"缺少索引文件：{idx_path}")
        return 1
    index = json.loads(idx_path.read_text(encoding="utf-8"))
    trans = parse_list(list_path)

    # 校验 JA 未被动过（防止错位）
    ja_lines = {}
    cur = None
    for raw in list_path.read_text(encoding="utf-8").splitlines():
        m = _ENTRY_RE.match(raw)
        if m:
            cur = m.group(1)
        elif cur and raw.startswith("JA:"):
            ja_lines[cur] = raw[3:].strip()
            cur = None
    bad = []
    for no, zh in trans.items():
        ent = index.get(no)
        if not ent:
            bad.append(f"[{no}] 不在索引里")
            continue
        if ja_lines.get(no) and _key(ja_lines[no].replace(BR_TXT, BR)) != _key(ent["ja"]):
            bad.append(f"[{no}] JA 行与索引不一致")
    if bad:
        print("校验失败，未写入：")
        for b in bad[:20]:
            print("   ", b)
        return 1

    # 按页聚合
    per_page: dict[str, dict[str, str]] = {}
    per_page_blk: dict[str, dict[str, str]] = {}
    manual_pairs: dict[str, str] = {}
    skipped: list[str] = []
    for no, zh in trans.items():
        ent = index[no]
        zh_in = zh.replace(BR_TXT, BR)
        # <br> 数差异只记录不拦截：LLM 精翻按中文语境重新断行，分段数与原文不同
        # 是预期行为（分段仅影响排版分行，不影响内容）。仅当译文完全不含任何
        # 分段而原文是多行块时提示（那种通常是漏改）。
        n_zh = zh_in.count(BR)
        n_ja = ent["ja"].count(BR)
        if n_ja and not n_zh:
            skipped.append(f"[{no}] 译文无 <br> 而原文有 {n_ja} 处分行，已按整段写入")
        if ent.get("manual"):
            manual_pairs[_br_out(ent["ja"])] = _br_out(zh_in)
        for loc in ent["locs"]:
            if loc["kind"] == "key" and loc.get("id"):
                per_page.setdefault(loc["slug"], {})[loc["id"]] = zh_in
            elif loc["kind"] == "blk" and loc.get("id"):
                per_page_blk.setdefault(loc["slug"], {})[loc["id"]] = zh_in
        # 成员 key 拆分（仅当整块恰好是成员拼接时）
        if ent["kind"] == "skill" and ent["members"]:
            segs = zh_in.split(BR)
            by_slug: dict[str, list[dict]] = {}
            for m in ent["members"]:
                by_slug.setdefault(m["slug"], []).append(m)
            for slug, ms in by_slug.items():
                joined = BR.join(m["ja"] for m in ms)
                if _key(joined) != _key(ent["ja"]) or len(segs) != len(ms):
                    continue
                for seg, m in zip(segs, ms):
                    per_page.setdefault(slug, {})[m["id"]] = seg

    filled = 0
    pages: set[str] = set()
    for jp in I18N.glob("*.json"):
        slug = jp.stem
        ks = per_page.get(slug) or {}
        bs = per_page_blk.get(slug) or {}
        if not ks and not bs:
            continue
        data = json.loads(jp.read_text(encoding="utf-8"))
        changed = False
        for k, v in ks.items():
            if k in data and isinstance(data[k], dict):
                if data[k].get("zh") != v:
                    data[k]["zh"] = v
                    filled += 1
                    changed = True
        blocks = data.get("_blocks") or {}
        for k, v in bs.items():
            if k in blocks:
                if blocks[k].get("zh") != v:
                    blocks[k]["zh"] = v
                    filled += 1
                    changed = True
        if changed:
            if not dry:
                # 与 i18n._save_entries 完全一致的格式（indent=1，无尾换行），避免整文件 diff
                jp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            pages.add(slug)

    n_man = 0 if dry else _patch_yaml_manual(manual_pairs)
    print(f"译文条数：{len(trans)}；写入节点：{filled}；涉及页：{len(pages)}；"
          f"phrases_manual 更新：{n_man}")
    for s in skipped[:20]:
        print("   ！", s)
    if dry:
        print("（dry-run，未写入任何文件）")
    return 0


def _latest_list(exclude_final: bool = True) -> Path:
    cands = sorted(OUT_DIR.glob("skills_*.txt"))
    if exclude_final:
        cands = [c for c in cands if not c.stem.endswith("_final")]
    return cands[-1]


def cmd_merge(batch_dir: Path) -> int:
    """把 batch_*.txt 的译文合并进原清单，输出 skills_<date>_final.txt。"""
    if not batch_dir.is_dir():
        print(f"目录不存在：{batch_dir}")
        return 1
    orig = _latest_list()
    if not orig:
        print("未找到 skills_<date>.txt 原清单")
        return 1
    stamp = re.search(r"skills_(\d{8})", orig.stem).group(1)
    trans: dict[str, str] = {}
    for bp in sorted(batch_dir.glob("batch_*.txt")):
        trans.update(parse_list(bp))
    out = orig.with_name(f"skills_{stamp}_final.txt")
    lines = orig.read_text(encoding="utf-8").splitlines()
    cur: str | None = None
    n_done = 0
    for i, ln in enumerate(lines):
        m = _ENTRY_RE.match(ln)
        if m:
            cur = m.group(1)
            continue
        if ln.startswith("ZH:") and cur and cur in trans:
            lines[i] = f"ZH: {trans[cur]}"
            n_done += 1
            cur = None
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"合并 {len(trans)} 条译文（覆盖 {n_done} 行）-> {out}")
    return 0


def cmd_pending(batch_dir: Path) -> int:
    """列出还没翻的条目编号。"""
    orig = _latest_list()
    if not orig:
        print("未找到 skills_<date>.txt 原清单")
        return 1
    have: set[str] = set()
    if batch_dir.is_dir():
        for bp in sorted(batch_dir.glob("batch_*.txt")):
            have.update(parse_list(bp))
    total = 0
    missing: list[str] = []
    for ln in orig.read_text(encoding="utf-8").splitlines():
        m = _ENTRY_RE.match(ln)
        if m:
            total += 1
            if m.group(1) not in have:
                missing.append(m.group(1))
    print(f"总数 {total}，已翻 {total - len(missing)}，待翻 {len(missing)}")
    if missing:
        print("待翻编号：" + " ".join(missing[:200]) + (" …" if len(missing) > 200 else ""))
    return 0


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] == "extract":
        return cmd_extract()
    if argv[0] == "stats":
        return cmd_stats()
    if argv[0] == "apply":
        args = [a for a in argv[1:] if not a.startswith("--")]
        if not args:
            print("用法：apply <清单文件> [--dry]")
            return 1
        return cmd_apply(Path(args[0]), dry="--dry" in argv)
    if argv[0] == "merge":
        return cmd_merge(Path(argv[1]))
    if argv[0] == "pending":
        return cmd_pending(Path(argv[1]))
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
