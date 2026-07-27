#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审计 zh_patch.py 源文件里"硬写进源码"的 JA2ZH 条目：
  - 与 _manual_zh.json（用户经 _translated_texts 注入）对比，找出"只有源文件里有、
    未被用户覆盖层覆盖"的条目 = 真正会渲染出来的硬编码译文。
  - 同时列出源文件中含签名(评论)的硬编码条目。
"""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "zh_patch.py"
JSON = ROOT / "tools" / "_manual_zh.json"

# --- 1) 从源码 AST 抽出 JA2ZH 原始字面量（不触发 merge） ---
src = SRC.read_text(encoding="utf-8")
tree = ast.parse(src)
src_ja2zh = None
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        t = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if isinstance(t, ast.Name) and t.id == "JA2ZH":
            src_ja2zh = ast.literal_eval(node.value)
            break
    if src_ja2zh is not None:
        break

assert src_ja2zh is not None, "找不到 JA2ZH"

# --- 2) 加载用户覆盖层 ---
manual = {}
if JSON.is_file():
    manual = json.loads(JSON.read_text(encoding="utf-8"))

src_keys = set(src_ja2zh.keys())
manual_keys = set(manual.keys())

overridden = src_keys & manual_keys          # 源码有、用户也填了同key -> 用户覆盖
src_only = src_keys - manual_keys            # 源码有、用户没覆盖 -> 真正渲染的硬编码
json_only = manual_keys - src_keys           # 用户填的、源码没有的

SIG_RE = re.compile(r"--\s*\[[^\]]*\]")

def is_comment(k):
    return bool(SIG_RE.search(k))

# 源文件里硬编码的"评论类"条目（带签名），无论是否被覆盖
src_comment_keys = [k for k in src_keys if is_comment(k)]
src_comment_only = [k for k in src_only if is_comment(k)]

OUT = ROOT / "tools" / "_audit_hardcoded_out.txt"
lines = []
lines.append("=" * 70)
lines.append("JA2ZH SOURCE HARDCODED vs USER _manual_zh.json OVERLAY")
lines.append("=" * 70)
lines.append(f"source JA2ZH total entries        : {len(src_keys)}")
lines.append(f"user _manual_zh.json entries      : {len(manual_keys)}")
lines.append(f"  - overridden by user (same key) : {len(overridden)}")
lines.append(f"  - source-only (live hardcoded)  : {len(src_only)}")
lines.append(f"  - user-only (not in source)     : {len(json_only)}")
lines.append("")
lines.append(f"source hardcoded [comment] entries (with --[sig]) total : {len(src_comment_keys)}")
lines.append(f"  of which still live (not overridden)                    : {len(src_comment_only)}")
lines.append("")
# 分类：源码里硬编码的非评论长句 / 术语 / 样板
src_only_noncomment = [k for k in src_only if not is_comment(k)]
src_only_comment = src_only_comment = [k for k in src_only if is_comment(k)]
lines.append(f"source-only live entries breakdown:")
lines.append(f"  - comment-type (with sig)        : {len(src_only_comment)}")
lines.append(f"  - non-comment (term/sample/body) : {len(src_only_noncomment)}")

# 写完整清单供人工核对（带 BOM 以便 Windows 记事本/任何读者正确识别 UTF-8）
dump = []
dump.append("=== SOURCE-ONLY (LIVE HARDCODED, not overridden by user) ===")
for k in sorted(src_only):
    v = src_ja2zh[k]
    tag = "[COMMENT]" if is_comment(k) else "[TERM/BODY]"
    dump.append(f"{tag}")
    dump.append(f"  JA: {k}")
    dump.append(f"  ZH: {v}")
    dump.append("")

# 风险分层：非评论里"长句"（JA 正文>40 字符）是最可能串台/错译的部分
LONG = 40
live_long = [k for k in src_only_noncomment if len(k) > LONG]
lines.append("")
lines.append(f"  - of non-comment live, JA body length > {LONG} chars (long-sentence risk): {len(live_long)}")

# 聚焦文件：仅导出 10979 条 live 评论（最高风险长文），供逐条核对
CMT_OUT = ROOT / "tools" / "_audit_hardcoded_live_comments.txt"
cmt = []
cmt.append("=== LIVE HARDCODED COMMENT ENTRIES (source-only, not in _translated_texts) ===")
cmt.append(f"total: {len(src_only_comment)}")
for k in sorted(src_only_comment):
    cmt.append(f"JA: {k}")
    cmt.append(f"ZH: {src_ja2zh[k]}")
    cmt.append("")
CMT_OUT.write_text("\ufeff" + "\n".join(cmt), encoding="utf-8")

OUT.write_text("\ufeff" + "\n".join(lines) + "\n\n" + "\n".join(dump), encoding="utf-8")
# 只把 ASCII 摘要打印到 stdout，避免日文经 GBK 控制台乱码
print("SUMMARY:")
for ln in lines:
    print(ln)
print(f"[files] full list -> {OUT.name}; live comments -> {CMT_OUT.name}")
