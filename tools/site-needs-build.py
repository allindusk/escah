#!/usr/bin/env python3
"""判断站点产物（site/.vitepress/dist）是否需要重新构建 —— 供 start-site.bat 调用。

为什么要它（2026-09-27）：
  `start-site.bat` 原先只检查 `.vitepress\\dist\\index.html` **是否存在** ✗ →
  内容更新后不会重建，预览到的是旧站点 ✗（实测撞到：旧 dist 里还留着已被删除的两页）。
  改为按「内容源最新修改时间 vs 产物标记文件修改时间」判断，并把这套逻辑放在 Python 里
  （而不是 .bat 里塞一段 PowerShell 一行式）：可单测、可复用、退出码语义清晰。

判定规则：产物标记文件不存在 → 需要构建；任一内容源文件比产物标记**更新** → 需要构建。

退出码：
  0 = 需要构建
  1 = 无需构建（产物已是最新）

用法：python tools/site-needs-build.py [--verbose]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 产物标记：构建成功时会生成它（build.mjs build 还会写 .nojekyll）
MARKER = ROOT / "site" / ".vitepress" / "dist" / "index.html"

# 内容源 + 构建输入：这些目录下任一文件更新，就该重建站点
# ⚠️ 必须同时包含「sync-site 生成出来的站点内容」：sync-site 只重写 site/**（md / frag /
#    generated），**不碰 dist**。若只比 data/ 与 glossary/，会出现"data 变了 → sync-site 重写了
#    md/frag → dist 仍是旧的，但判定说最新"✗。
SOURCES = [
    ROOT / "data" / "parsed" / "i18n",        # 译文真值（*.json / *.template.html）
    ROOT / "data" / "parsed" / "ja",          # 正文片段
    ROOT / "data" / "parsed" / "characters",  # 角色数据
    ROOT / "data" / "registry",               # 页面集合（pages.yaml / mirror_plan.yaml）
    ROOT / "glossary",                        # 词表（terms / phrases_manual / names …）
    ROOT / "site" / "zh",                     # ↓ sync-site 的产物（等价于构建输入）
    ROOT / "site" / "ja",
    ROOT / "site" / ".vitepress" / "frag",
    ROOT / "site" / ".vitepress" / "generated",
]


def newest_source() -> "tuple[float, str]":
    """返回 (最新 mtime, 对应文件) —— 只统计内容源。"""
    newest, newest_path = 0.0, ""
    for root in SOURCES:
        if not root.exists():
            continue
        targets = [root] if root.is_file() else [
            os.path.join(dp, f) for dp, _dirs, files in os.walk(root) for f in files
        ]
        for p in targets:
            try:
                m = os.path.getmtime(p)
            except OSError:
                continue
            if m > newest:
                newest, newest_path = m, p
    return newest, newest_path


def main() -> int:
    verbose = "--verbose" in sys.argv

    def say(msg: str) -> None:
        if verbose:
            print(msg, flush=True)      # 默认安静：由 .bat 决定是否打印

    if not MARKER.exists():
        say(f"[site-needs-build] 产物缺失：{MARKER.relative_to(ROOT)} → 需要构建")
        return 0

    marker_m = MARKER.stat().st_mtime
    newest, newest_path = newest_source()
    if newest > marker_m:
        say(f"[site-needs-build] 内容源更新于产物之后（{Path(newest_path).relative_to(ROOT)}）"
            f" → 需要构建")
        return 0
    say("[site-needs-build] 产物已是最新 → 无需构建")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
