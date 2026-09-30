# -*- coding: utf-8 -*-
"""机翻方案调优台：用**真实日文句子 + 金标准译文**客观对比几种送翻方案。

为什么可信（2026-09-27）：
  金标准不是机器评的，而是**我逐条人工精校过的译文**（`tools/_mt_refine/_jamap__*.txt`，
  形如 `原文<TAB>我的译文`）。于是可以直接量化"某方案离人工译文有多近" ✓，
  而不是靠主观印象说"这个方案更好" ✗。

被评测的方案（同一批句子，同一引擎，同一限速）：
  S0 raw        ：原文直接送翻（无任何术语处理）
  S1 pre        ：现状路径 —— `pre_substitute` 就地替换成中文后再送翻（**中日混合**✗）
  S2 protect    ：占位符保护（专名/术语挖成 `[[i]]`，日文完整）→ 翻译 → 还原
  S3 protect+ctx：S2 之上把**同一块的多行合成一次请求**（用换行分隔，给谷歌上文）

评分指标（每条都能定位到具体样本，便于复核）：
  · chrF3   ：与金标准的字符 3-gram F1（0–1，越高越像人工译文）—— 主指标
  · 术语命中 ：金标准里出现的词表术语，有多少在方案输出里也出现
  · 数字守恒 ：原文数字在输出里保留的比例
  · 未还原   ：占位符没能还原的条数（越低越好）
  · 假名残留 ：输出里仍含假名的条数（越低越好）

用法：
  python tools/_dev/mt_tune.py                 # 全量对比
  python tools/_dev/mt_tune.py --limit 150     # 只用前 150 条（快速迭代）
  python tools/_dev/mt_tune.py --dump 12       # 额外打印最优/最差样本对照
"""

from __future__ import annotations

import collections
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline import gtrans  # noqa: E402

KANA_RE = re.compile(r"[\u3041-\u3096\u30a1-\u30fa\u30fd-\u30ff]")
NUM_RE = re.compile(r"\d+(?:\.\d+)?%?％?")
SENT_RE = re.compile(r"\[\[\s*(\d+)\s*\]\]")


# ------------------------------------------------------------------ 金标准 ----
def load_gold(limit: int | None) -> "list[tuple[str, str, str]]":
    """返回 [(来源文件, ja, 人工译文)]。"""
    rows: "list[tuple[str, str, str]]" = []
    for p in sorted((ROOT / "tools" / "_mt_refine").glob("_jamap__*.txt")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#") or "\t" not in line:
                continue
            ja, zh = line.split("\t", 1)
            ja, zh = ja.strip(), zh.strip()
            if len(ja) < 6 or not zh or ja == zh:
                continue
            rows.append((p.name, ja, zh))
    seen = set()
    uniq = []
    for f, ja, zh in rows:
        if ja in seen:
            continue
        seen.add(ja)
        uniq.append((f, ja, zh))
    return uniq[:limit] if limit else uniq


# -------------------------------------------------------------------- 指标 ----
def chrf3(hyp: str, ref: str) -> float:
    """字符 3-gram F1（chrF 的简化版，足够做方案排序）。"""
    def grams(s: str):
        s = re.sub(r"\s+", "", s)
        return collections.Counter(s[i:i + 3] for i in range(max(0, len(s) - 2)))

    h, r = grams(hyp), grams(ref)
    if not h or not r:
        return 0.0
    inter = sum((h & r).values())
    if inter == 0:
        return 0.0
    prec, rec = inter / sum(h.values()), inter / sum(r.values())
    return 2 * prec * rec / (prec + rec)


def score(pairs: "list[tuple[str, str, str]]") -> dict:
    """pairs: [(ja, hyp, gold)]"""
    chrf = terms_hit = terms_tot = nums_ok = nums_tot = 0.0
    kana_left = unrestored = 0
    for ja, hyp, gold in pairs:
        chrf += chrf3(hyp, gold)
        for tja, tzh in gtrans_term_hits(ja):
            terms_tot += 1
            if tzh in hyp:
                terms_hit += 1
        for num in set(NUM_RE.findall(ja)):
            core = num.rstrip("%％")
            nums_tot += 1
            if core and core in hyp:
                nums_ok += 1
        if KANA_RE.search(hyp):
            kana_left += 1
        unrestored += len(SENT_RE.findall(hyp))
    n = max(1, len(pairs))
    return {
        "chrF3": chrf / n,
        "术语命中": terms_hit / terms_tot if terms_tot else 0.0,
        "数字守恒": nums_ok / nums_tot if nums_tot else 0.0,
        "未还原": unrestored,
        "假名残留": kana_left,
    }


_TERM_CACHE = None


def gtrans_term_hits(ja: str) -> "list[tuple[str, str]]":
    """术语命中检查用：**固定取 names.yaml + terms.yaml**（权威词表）。

    为什么固定 ✗ 不能用当前保护层的名单：名单会随方案变化（是否纳入 high_freq），
    分母一变，「术语命中率」就无法跨方案比较 ✗（实测出现 97.5% 与 79.8% 不可比）。
    固定成权威词表后，该指标恒等于「输出是否采用了站内权威译名」✓，方案间可比 ✓。
    """
    global _TERM_CACHE
    if _TERM_CACHE is None:
        import yaml as _yaml
        terms: "dict[str, str]" = {}
        for rel in ("names.yaml", "terms.yaml"):
            d = _yaml.safe_load((ROOT / "glossary" / rel).read_text(encoding="utf-8")) or {}
            stack = [d]
            while stack:
                cur = stack.pop()
                if isinstance(cur, dict):
                    for k, v in cur.items():
                        if isinstance(v, dict):
                            stack.append(v)
                        elif isinstance(v, str):
                            terms[str(k).strip()] = v.strip()
        _TERM_CACHE = terms
    out = []
    for k, v in _TERM_CACHE.items():
        if len(k) >= 2 and v and k in ja:
            out.append((k, v))
    return out[:6]


# ------------------------------------------------------------------ 方案 ------
LATIN_RUN_RE = re.compile(r"[A-Za-z]{4,}")

CACHE_PATH = ROOT / "tools" / "_dev" / "_mt_eval_cache.json"
_CACHE = None


def _cache() -> dict:
    global _CACHE
    if _CACHE is None:
        try:
            _CACHE = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 缓存损坏就当空
            _CACHE = {}
    return _CACHE


def _save_cache() -> None:
    try:
        CACHE_PATH.write_text(json.dumps(_CACHE or {}, ensure_ascii=False),
                              encoding="utf-8", newline="\n")
    except Exception as e:  # noqa: BLE001 缓存写失败不影响评测
        print(f"  (缓存写入失败：{e})")


def quality_score(ja: str, zh: str) -> float:
    """**无参考答案**的质量打分：用于多候选重排（线上没有金标准，只能靠这些信号 ✓）。

    信号都来自我们已验证过的错误形态 ✗：
      + 术语命中（词表权威译法出现 ✓，长术语权重更高 ✓）
      + 数字/百分数保留 ✓
      - 残留假名 ✗（未译干净）
      - 连续拉丁串（`Daibeet`/`Escalayer` 这类音译 ✗ —— 站内约定「人名/术语不音译」✓）
      - 长度比离群（机翻跑题常表现为过长/过短 ✗）
    权重是可调参数 ✓ —— 调参就靠 mt_tune.py 的金标准 chrF3 来定 ✓。
    """
    s = 0.0
    zh_nospace = re.sub(r"\s+", "", zh)
    for tja, tzh in gtrans_term_hits(ja):
        if tzh in zh:
            s += 1.0 + 0.2 * len(tzh)          # 长术语更有信息量
    for num in set(NUM_RE.findall(ja)):
        if num.rstrip("%％") and num.rstrip("%％") in zh:
            s += 1.0
    s -= 3.0 * len(KANA_RE.findall(zh))
    s -= 1.5 * len(LATIN_RUN_RE.findall(zh_nospace))
    ja_n = max(1, len(re.sub(r"\s+", "", ja)))
    ratio = len(zh_nospace) / ja_n
    if ratio < 0.25 or ratio > 2.5:
        s -= 2.0
    return s


def rerank(rows, candidates: "list[list[str]]"):
    """多候选重排：每条取 quality_score 最高者。candidates = [[候选A...], [候选B...], ...]"""
    out = []
    for idx, (_f, ja, _gold) in enumerate(rows):
        best, best_s = None, None
        for cand in candidates:
            z = cand[idx]
            sc = quality_score(ja, z)
            if best_s is None or sc > best_s:
                best, best_s = z, sc
        out.append((ja, best or "", _gold))
    return out


def run_scheme(name: str, rows, batch: int = 20):
    keys = [ja for _f, ja, _g in rows]
    if name == "S0 raw":
        inputs = keys
    elif name == "S1 pre":
        inputs = [gtrans.pre_substitute(k) for k in keys]
    else:
        inputs, tables = [], []
        for k in keys:
            p, spans = gtrans.protect_ja(k)
            inputs.append(p)
            tables.append(spans)
    # 缓存：key = **送翻文本**（与方案无关 ✓）→ 换评分权重/换样本量重跑时零请求 ✓，
    # 也让本脚本可以在后台跑（重复调参不再烧网络 ✓）。缓存文件随仓库放在 tools/_dev/。
    cache = _cache()
    outs = [cache.get(s, "") for s in inputs]
    todo = [i for i, s in enumerate(inputs) if not cache.get(s)]
    for i in range(0, len(todo), batch):
        idxs2 = todo[i:i + batch]
        chunk = [inputs[j] for j in idxs2]
        try:
            got = gtrans.translate_lines(chunk, src="ja", tgt="zh-CN")
        except Exception as e:  # noqa: BLE001
            print(f"  ! {name} 第 {i // batch + 1} 批失败：{e}")
            got = [""] * len(chunk)
        for j, z in zip(idxs2, got):
            outs[j] = z
            if z:
                cache[inputs[j]] = z
        _save_cache()
    print(f"  （{name}：命中缓存 {len(inputs) - len(todo)}/{len(inputs)}，"
          f"本次新请求 {len(todo)} 条）")
    if name.startswith("S2") or name.startswith("S3"):
        fixed = []
        for (ja, zh), spans in zip(zip(keys, outs), tables):
            z, _m = gtrans.restore_zh(zh, spans)
            fixed.append(z)
        outs = fixed
    return [(ja, zh, gold) for (_f, ja, gold), zh in zip(rows, outs)]


def load_block_gold(max_blocks: int | None, min_segs: int = 3):
    """块级金标准：取已精校页的块（ja 段拼起来 vs 我精校的 zh 段拼起来）。

    用途：验证「整块一次翻」是否比「按 ⏎ 拆成原子片段分别翻」更接近人工译文。
    注意取的是**已精校页**，其 zh 就是人工结果 ✓（未精校页的 zh 是机翻产物，不能当金标准 ✗）。
    """
    sys.path.insert(0, str(ROOT / "pipeline"))
    from escah_pipeline.i18n import _blocks_of, has_i18n, load_entries  # noqa: E402

    BR = "\x01"
    pages = ["characters/閃忍ホーネット", "characters/神騎ハウゼル", "characters/エスカ・セブン",
             "characters/真夏のキクリ", "characters/盛夏のエスカレイヤー"]
    out = []
    for slug in pages:
        if not has_i18n(slug):
            continue
        for bid, blk in _blocks_of(load_entries(slug)).items():
            ja_segs = [s.strip() for s in (blk.get("ja") or "").split(BR)]
            zh_segs = [s.strip() for s in (blk.get("zh") or "").split(BR)]
            pairs = [(j, z) for j, z in zip(ja_segs, zh_segs) if j and z and j != z]
            if len(pairs) < min_segs:
                continue
            out.append((f"{slug}:{bid}", [j for j, _z in pairs], [z for _j, z in pairs]))
    return out[:max_blocks] if max_blocks else out


def run_block_scheme(blocks, mode: str):
    """mode: 'seg' = 每段单独翻（现状口径）；'blk' = 整块一次翻（[[BR]] 保换行）。"""
    if mode == "seg":
        flat, tables = [], []
        for _k, jas, _z in blocks:
            for j in jas:
                p, spans = gtrans.protect_ja(j)
                flat.append(p)
                tables.append(spans)
        outs = []
        for i in range(0, len(flat), 20):
            outs.extend(gtrans.translate_lines(flat[i:i + 20], src="ja", tgt="zh-CN"))
        fixed = [gtrans.restore_zh(o, sp)[0] for o, sp in zip(outs, tables)]
        it = iter(fixed)
        return [[next(it) for _ in jas] for _k, jas, _z in blocks]
    # blk：整块 → 保护术语 → 换行写成 [[BR]] → 一次翻译 → 还原
    reqs, tables, brmaps = [], [], []
    for _k, jas, _z in blocks:
        joined = "[[BR]]".join(jas)
        p, spans = gtrans.protect_ja(joined)
        reqs.append(p)
        tables.append(spans)
    outs = []
    for i in range(0, len(reqs), 10):
        outs.extend(gtrans.translate_lines(reqs[i:i + 10], src="ja", tgt="zh-CN"))
    result = []
    for (k, jas, _z), o, sp in zip(blocks, outs, tables):
        z = gtrans.restore_zh(o, sp)[0]
        segs = re.split(r"\[\[\s*BR\s*\]\]", z, flags=re.I)
        segs = [s.strip() for s in segs if s.strip()]
        result.append(segs)
    return result


def main() -> int:
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    dump = 0
    if "--dump" in sys.argv:
        dump = int(sys.argv[sys.argv.index("--dump") + 1])

    # ---- 覆盖缺口：金标准日文里出现、但**词表没有**的片假名词（调优闭环的输入）----
    if "--gaps" in sys.argv:
        rows = load_gold(None)
        gtrans._load_protect_terms()
        have = gtrans._PROTECT_CACHE or {}
        runs: "collections.Counter[str]" = collections.Counter()
        example: "dict[str, tuple[str, str]]" = {}
        for _f, ja, gold in rows:
            for run in re.findall(r"[\u30a1-\u30fa\u30fc]{3,}", ja):
                if any(run in k for k in have):
                    continue          # 词表已覆盖（含作为长词一部分出现）
                runs[run] += 1
                example.setdefault(run, (ja, gold))
        print(f"金标准 {len(rows)} 条里，**词表未覆盖**的片假名词：{len(runs)} 种\n")
        print(f"{'次数':>4}  {'片假名词':<22}{'出处原文 / 人工译文'}")
        print("-" * 100)
        for run, n in runs.most_common(limit or 40):
            ja, gold = example[run]
            print(f"{n:>4}  {run:<22}{ja[:34]}  ⇒  {gold[:36]}")
        print("\n→ 把这些补进 names.yaml/terms.yaml（用 add_names_batch.py 或手工），再重跑评测即可量化提升 ✓")
        return 0

    if "--blocks" in sys.argv:
        nb = 12
        if "--limit" in sys.argv:
            nb = int(sys.argv[sys.argv.index("--limit") + 1])
        blocks = load_block_gold(nb)
        print(f"块级金标准 {len(blocks)} 块（已精校页的块，金标准 = 人工精校译文）\n")
        res = {}
        for mode, label in (("seg", "S2 分段翻（现状口径）"), ("blk", "S3 整块翻（[[BR]] 保换行）")):
            out = run_block_scheme(blocks, mode)
            chrf = terms_ok = terms_all = 0.0
            for (k, jas, golds), got in zip(blocks, out):
                chrf += chrf3(" ".join(got), " ".join(golds))
                for j, g in zip(jas, golds):
                    for tja, tzh in gtrans_term_hits(j):
                        terms_all += 1
                        if tzh in " ".join(got):
                            terms_ok += 1
            n = max(1, len(blocks))
            res[label] = (chrf / n, terms_ok / terms_all if terms_all else 0, out)
            print(f"  {label}: chrF3={chrf / n:.3f}  术语命中={terms_ok / max(1, terms_all):.1%}")
        best = max(res, key=lambda k: res[k][0])
        print(f"\n块级最优 = {best}")
        if dump:
            for (k, jas, golds), got in list(zip(blocks, res[best][2]))[:dump]:
                print(f"\n  {k}")
                print(f"    ja  : {'⏎'.join(jas)[:110]}")
                print(f"    金标: {'⏎'.join(golds)[:110]}")
                print(f"    方案: {'⏎'.join(got)[:110]}")
        return 0

    rows = load_gold(limit)
    print(f"金标准样本 {len(rows)} 条（来自 tools/_mt_refine/_jamap__*.txt 的人工精校译文）\n")

    results = {}
    for scheme in ["S0 raw", "S1 pre", "S2 protect"]:
        print(f"跑 {scheme} …")
        scored = run_scheme(scheme, rows)
        results[scheme] = (score(scored), scored)

    # ---- 第三候选：保护层含 high_freq 词汇（单项略差 ✗，但作为候选能补上被漏掉的术语 ✓）----
    os.environ["ESCAH_GTRANS_PROTECT_HF"] = "1"
    gtrans._PROTECT_CACHE = None
    gtrans._PROTECT_RE = None
    print("跑 S3 protect+HF …（第三个候选）")
    hf_scored = run_scheme("S3 protect+HF", rows)
    os.environ["ESCAH_GTRANS_PROTECT_HF"] = "0"
    gtrans._PROTECT_CACHE = None
    gtrans._PROTECT_RE = None

    # ---- S4：**多候选重排**（用无参考答案的质量分挑最优；候选都是现成的，零额外请求 ✓）----
    cands = [[zh for _ja, zh, _g in results[k][1]] for k in ("S0 raw", "S2 protect")]
    cands.append([zh for _ja, zh, _g in hf_scored])
    picked = rerank(rows, cands)
    results["S4 rerank"] = (score(picked), picked)

    print("\n" + "=" * 78)
    print(f"{'方案':<12}{'chrF3':>9}{'术语命中':>10}{'数字守恒':>10}{'未还原':>8}{'假名残留':>10}")
    print("-" * 78)
    for name, (sc, _rows) in results.items():
        print(f"{name:<12}{sc['chrF3']:>9.3f}{sc['术语命中']:>10.1%}"
              f"{sc['数字守恒']:>10.1%}{sc['未还原']:>8d}{sc['假名残留']:>10d}")
    print("=" * 78)

    if dump:
        best = max(results, key=lambda k: results[k][0]["chrF3"])
        print(f"\n最优方案 = {best}；按 chrF3 升序看最不像人工译文的样本：")
        samples = results[best][1]
        ranked = sorted(samples, key=lambda t: chrf3(t[1], t[2]))
        for ja, hyp, gold in ranked[:dump]:
            print(f"\n  差例 chrF3={chrf3(hyp, gold):.2f}")
            print(f"    ja  : {ja[:80]}")
            print(f"    金标: {gold[:80]}")
            print(f"    方案: {hyp[:80]}")
        print("\n  最接近人工译文的样本：")
        for ja, hyp, gold in ranked[-dump // 2:] if dump > 1 else []:
            print(f"\n  好例 chrF3={chrf3(hyp, gold):.2f}")
            print(f"    ja  : {ja[:80]}")
            print(f"    金标: {gold[:80]}")
            print(f"    方案: {hyp[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
