#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 glossary 词表（high_freq + names + skills，JA->ZH）烘焙进 i18n JSON 的 zh。

背景：
  - 渲染期覆盖（render_locale 的 _correct_text / _name_override）只能做「子串替换」，
    要求 zh 里已含正确/日文形态才能替换。但 LLM 把「想破」误译成「破念」时，
    zh 根本不含「想破」，子串替换无从下手；且同形词（想破:想破，ja==zh）在
    _load_high_freq_glossary 里被 k!=v 过滤掉，渲染期完全不生效。
  - 因此必须把词表「执行到 i18n 源头」：直接修正 i18n JSON 的 zh。

做法（分词对齐，安全）：
  - 把 ja / zh 都按「CJK/字母数字 段」与「其余分隔符段（括号/空格/标点）」切分。
  - 仅当 ja 段数 == zh 段数（可对齐）时，逐段比对：若某 ja 段精确等于词表键 K，
    且对应 zh 段 != V，则把该 zh 段强制设为 V。
  - 段数不对齐 → 跳过该条（绝不瞎猜），保证不破坏结构。
  - 只改对齐上的对应段，不影响其它内容；幂等（再跑不产生变化）。

用法：
  python tools/_apply_glossary_to_i18n.py            # 默认执行并改动
  python tools/_apply_glossary_to_i18n.py --dry      # 仅统计，不写文件
"""
import os
import re
import sys
import json
import yaml

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N_DIR = os.path.join(BASE, "data", "parsed", "i18n")
GLOSS_DIR = os.path.join(BASE, "glossary")

# 词段 = CJK（中日韩表意+扩展A）+ 假名 + 半角字母数字 + 【全角字母数字】；
# 其余（含全角标点 （）、，。 等）一律作为「分隔段」。
# 注意：不能把全角区 ＀-￯ 整体算进词段，否则全角括号（）会被并入词段，
# 而对应 ja 用半角()作分隔段 → 段数不等被跳过，想破这类修正失效。
SEG = re.compile(
    r"[一-鿿぀-ヿ㐀-䶿0-9A-Za-z０-９Ａ-Ｚａ-ｚ]+"
    r"|[^一-鿿぀-ヿ㐀-䶿0-9A-Za-z０-９Ａ-Ｚａ-ｚ]+"
)


def segs(t: str):
    return SEG.findall(t)


def load_glossary():
    gloss = {}

    def add(d, priority_note=""):
        if not isinstance(d, dict):
            return
        for k, v in d.items():
            if not isinstance(k, str) or not k:
                continue
            if isinstance(v, str):
                z = v
            elif isinstance(v, dict):
                z = v.get("name_zh") or ""
            else:
                continue
            if not z:
                continue
            if len(k) < 2:  # 单字风险高，跳过
                continue
            gloss[k] = z

    # 优先级：skills < high_freq < names（专名最高）
    with open(os.path.join(GLOSS_DIR, "skills.yaml"), encoding="utf-8") as f:
        add(yaml.safe_load(f).get("skills", {}))
    with open(os.path.join(GLOSS_DIR, "high_freq.yaml"), encoding="utf-8") as f:
        add(yaml.safe_load(f).get("high_freq", {}))
    with open(os.path.join(GLOSS_DIR, "names.yaml"), encoding="utf-8") as f:
        add(yaml.safe_load(f).get("names", {}))

    return gloss


_WS = re.compile(r"\s+")


def load_names():
    """仅取 names.yaml 专名（JA->ZH），按键长降序返回，供规则2前缀匹配。"""
    with open(os.path.join(GLOSS_DIR, "names.yaml"), encoding="utf-8") as f:
        d = yaml.safe_load(f).get("names", {})
    items = []
    for k, v in d.items():
        if not isinstance(k, str) or len(k) < 2:
            continue
        z = v if isinstance(v, str) else (v.get("name_zh") if isinstance(v, dict) else "")
        if z:
            items.append((k, z))
    items.sort(key=lambda kv: len(kv[0]), reverse=True)  # 长键优先，避免短名被前缀误命中
    return items


def fix_zh(ja: str, zh: str, gloss: dict, gloss_ns: dict, names_items: list):
    # 规则0（最高优先）：整条 ja 恰为词表键（含去空白容错）→ zh 直接设为词表值。
    # 以 ja 为唯一匹配依据，与 zh 现值无关，不需要分词对齐。
    v = gloss.get(ja) or gloss.get(ja.strip()) or gloss_ns.get(_WS.sub("", ja))
    if v is not None:
        return v
    # 规则2（整句前缀专名）：整句 ja 以某个专名键开头（专名 + 其后紧接分隔符），
    # 把 zh 开头「连续 CJK/假名专名段（允许中间空格，即吃掉 LLM 幻觉/多余空格）」
    # 整体替换为权威译名。覆盖「整句开头是角色名、但整句非精确键、分词段数不等」的盲区。
    # 例：ja=「翼竜剣聖アカネ 20秒…」 zh=「翼龙剑圣 朱音 20秒…」
    #     → 吃掉「翼龙剑圣 朱音」替换为「翼龙剑圣茜」 → 「翼龙剑圣茜 20秒…」 ✓
    # 作者原话块（名后接叙述）若 zh 开头已是正确专名则 no-op，不会误伤。
    for name_key, name_zh in names_items:
        if ja.startswith(name_key):
            rest = ja[len(name_key):]
            if rest and rest[0] not in " 　()（）,，.。;；:：":
                continue  # 名后不是分隔符，不算「专名+描述」结构，跳过
            m = re.match(
                r"^[\u4e00-\u9fff぀-ヿ㐀-䶿]+(?:[ 　]*[\u4e00-\u9fff぀-ヿ㐀-䶿]+)*", zh
            )
            if m:
                head = m.group(0)
                if head.replace(" ", "") != name_zh.replace(" ", "") or head != name_zh:
                    return name_zh + zh[m.end():]
            else:
                if zh != name_zh:
                    return name_zh
            break  # 最长匹配生效，不再试更短键
    # 规则1：ja 含词表键作子串 → 分词对齐后替换对应 zh 段（段数不等则跳过，安全）。
    js = segs(ja)
    zs = segs(zh)
    if len(js) != len(zs):
        return zh  # 段数不对齐，跳过（安全）
    out = list(zs)
    changed = False
    for i, (jseg, zseg) in enumerate(zip(js, zs)):
        v = gloss.get(jseg)
        if v is not None and v != zseg:
            out[i] = v
            changed = True
    return "".join(out) if changed else zh


def walk(o, gloss, gloss_ns, names_items, stats, samples, path):
    if isinstance(o, dict):
        if isinstance(o.get("ja"), str) and isinstance(o.get("zh"), str):
            # 空保护：blk.zh 为空表示原缺译。渲染层对空 blk.zh 保留日文原文，
            # 前端用 nameAliases（日文名→中文名）匹配出浮窗。一旦烘焙把空块填成
            # 错译中文，日文原文丢失、浮窗彻底失效。故空块绝不写入，保留原状。
            if not o["zh"].strip():
                return
            new = fix_zh(o["ja"], o["zh"], gloss, gloss_ns, names_items)
            if new != o["zh"]:
                stats["entries"] += 1
                o["zh"] = new
                if len(samples) < 20000:
                    samples.append((path, o["ja"], new))
        for v in o.values():
            walk(v, gloss, gloss_ns, names_items, stats, samples, path)
    elif isinstance(o, list):
        for v in o:
            walk(v, gloss, gloss_ns, names_items, stats, samples, path)


def main():
    dry = "--dry" in sys.argv
    gloss = load_glossary()
    gloss_ns = {_WS.sub("", k): v for k, v in gloss.items()}
    names_items = load_names()
    print(f"词表条目数: {len(gloss)}  专名条目数: {len(names_items)}")
    stats = {"files": 0, "entries": 0}
    samples = []
    changed_files = []

    for root, _dirs, files in os.walk(I18N_DIR):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, BASE)
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[SKIP] 解析失败 {rel}: {e}")
                continue
            before = json.dumps(data, ensure_ascii=False, sort_keys=True)
            walk(data, gloss, gloss_ns, names_items, stats, samples, rel)
            after = json.dumps(data, ensure_ascii=False, sort_keys=True)
            if before != after:
                stats["files"] += 1
                changed_files.append(rel)
                if not dry:
                    with open(fp, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
                        f.write("\n")

    print(f"改动文件数: {stats['files']}")
    print(f"改动条目数: {stats['entries']}")
    if changed_files:
        log_dir = os.path.join(BASE, "tools", "_logs")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "apply_glossary_i18n.log"), "w", encoding="utf-8") as f:
            f.write("CHANGED FILES:\n")
            for c in changed_files:
                f.write(f"  {c}\n")
            f.write("\nSAMPLES (ja -> zh):\n")
            for rel, ja, zh in samples:
                f.write(f"[{rel}]\n  ja: {ja}\n  zh: {zh}\n")
        print(f"样本与文件清单已写入 tools/_logs/apply_glossary_i18n.log")
        print("样本（前若干）:")
        for rel, ja, zh in samples[:30]:
            print(f"  [{rel}] {ja} -> {zh}")


if __name__ == "__main__":
    main()
