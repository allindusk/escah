#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""移除 JA2ZH 后的冒烟测试（调试版）。"""
import importlib.util
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("zh_patch_smoke", TOOLS / "zh_patch.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print("JA2ZH 源字面量(merge前应为空) 实际 len:", len(m.JA2ZH), "= merge 后的手工译文数")
print("_JA2ZH_ORDERED 条数:", len(m._JA2ZH_ORDERED))
print("REGEX_RULES:", len(m.REGEX_RULES), " GENERIC:", len(m.GENERIC))

# 调试最长那条为何不匹配
ja, zh = m._JA2ZH_ORDERED[0]
out = m.patch(ja)
print("\n[最长条] patch == zh ?", out == zh)
if out != zh:
    # 找第一个不同字符
    for i in range(min(len(out), len(zh))):
        if out[i] != zh[i]:
            print("  首差异@%d: out=%r zh=%r" % (i, out[max(0,i-10):i+10], zh[max(0,i-10):i+10]))
            break
    else:
        print("  长度不同 out=%d zh=%d" % (len(out), len(zh)))

# 找一个短的手工条目(含常见词)测试
short = next(((j, z) for j, z in m._JA2ZH_ORDERED if 5 <= len(j) <= 25 and "実装" not in j), None)
if short:
    sja, szj = short
    sout = m.patch(sja)
    print("\n[短条] JA=%r" % sja[:25])
    print("       ZH=%r" % szj[:25])
    print("       patch命中?", sout == szj)
else:
    print("\n[短条] 未找到合适样例")

# REGEX 公式仍生效
print("\nREGEX 样例 敵全体に100ダメージを与える ->", m.patch("敵全体に100ダメージを与える"))
print("GENERIC 样例 覚醒 ->", m.patch("覚醒"))
print("SMOKE DONE")
