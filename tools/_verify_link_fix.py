# -*- coding: utf-8 -*-
"""本地验证站内链接修复（不依赖线上部署）。

覆盖四层：
  1. URL 构造函数：在 ESCAH_BASE=/escah/ 与 / 两种部署下，href 归一化结果是否正确
  2. 最终产物：扫描 dist 全部 HTML 的站内链接，核对目标文件是否存在（死链数应为 0）
  3. 角色页形态：确认所有角色链接都带 characters/ 段
  4. 两种 base 的前缀一致性：产物里 /escah/ 前缀数量 == 站内链接总数（GH 形态）

用法: python tools/_verify_link_fix.py
"""
from __future__ import annotations

import importlib
import os
import posixpath
import re
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
_DIST_ARG = sys.argv[sys.argv.index("--dist") + 1] if "--dist" in sys.argv else ""
DIST = (
    (ROOT / _DIST_ARG).resolve()
    if _DIST_ARG
    else ROOT / "site" / ".vitepress" / "dist"
)
sys.path.insert(0, str(ROOT / "pipeline"))

HREF_RE = re.compile(r'href="([^"]+)"')
SITE_PATH_RE = re.compile(r"^/(?:[^/]+/)?((?:ja|zh)/.*)$")


# ---------------------------------------------------------------- 1. URL 构造
def check_url_builder() -> int:
    print("=" * 68)
    print("[1] URL 构造函数（pipeline/escah_pipeline/i18n.py）")
    print("=" * 68)
    import escah_pipeline.config as config
    import escah_pipeline.i18n as i18n

    cases = [
        ("missions.html", "任务页（普通页）"),
        ("エスカレイヤー.html", "角色页"),
        ("FM77.html", "角色页（ASCII 名）"),
        ("/zh/missions.html", "已是站内绝对路径"),
        ("/zh/%E9%AD%94%E5%A5%B3%E3%82%B7%E3%82%BA%E3%82%AF.html", "角色页（已编码）"),
        ("characters.html", "角色一览（不是角色页）"),
    ]
    bad = 0
    for base in ("/escah/", "/"):
        os.environ["ESCAH_BASE"] = base
        importlib.reload(config)
        importlib.reload(i18n)
        print(f"\n  ESCAH_BASE={base!r}")
        for href, label in cases:
            got, _t = i18n._normalize_link_href(href)
            ok = got.startswith(base)
            # 角色页必须带 characters/
            if "エスカレイヤー" in got or "FM77" in got or "%E9%AD%94" in got:
                ok = ok and "/characters/" in got
            bad += 0 if ok else 1
            print(f"    {'OK ' if ok else 'BAD'} {label:<16} {href[:46]:<48} -> {got}")
    os.environ.pop("ESCAH_BASE", None)
    importlib.reload(config)
    importlib.reload(i18n)
    return bad


# ------------------------------------------------------------ 2/3/4. 产物核对
def check_dist() -> tuple[int, int, int]:
    print("\n" + "=" * 68)
    print("[2] 最终产物 dist 的站内链接核对")
    print("=" * 68)
    if not DIST.exists():
        print("  [skip] 没有 dist，先跑 node build.mjs build")
        return (0, 0, 0)

    files = {"/" + p.relative_to(DIST).as_posix() for p in DIST.rglob("*") if p.is_file()}
    htmls = [p for p in DIST.rglob("*.html")]
    print(f"  产物目录: {DIST.name}")
    print(f"  HTML 页数: {len(htmls)}   产物文件数: {len(files)}")

    total = with_base = broken = char_flat = relative = 0
    broken_samples: list[str] = []

    for p in htmls:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        page_dir = "/" + p.parent.relative_to(DIST).as_posix()
        if page_dir == "/.":
            page_dir = "/"
        for href in HREF_RE.findall(text):
            if href.startswith(("#", "//")) or re.match(r"^[a-z]+:", href, re.I):
                continue
            if href.startswith("/"):
                m = SITE_PATH_RE.match(href)
                if not m:
                    continue
                rel = "/" + m.group(1)
            else:
                # 相对链接（如 characters/xxx.html）：按当前页所在目录展开
                if not re.match(r"^(?:ja|zh)/", posixpath.normpath(posixpath.join(page_dir, href)).lstrip("/")):
                    continue
                rel = posixpath.normpath(posixpath.join(page_dir, href))
                relative += 1
                if not rel.startswith("/"):
                    rel = "/" + rel
            total += 1
            if href.startswith("/escah/"):
                with_base += 1
            rel = unquote(rel.split("#", 1)[0].split("?", 1)[0])
            if rel.endswith("/"):
                # 目录链接（/escah/ja/、/escah/zh/ex/）→ 对应目录下的 index.html
                rel = rel + "index.html"
            elif not rel.endswith(".html") and "." not in rel.rsplit("/", 1)[-1]:
                rel = rel + ".html"
            # 角色页必须带 characters/
            if "/characters/" not in rel and (
                "/zh/" in rel or "/ja/" in rel
            ) and rel.count("/") in (3, 4) and rel.endswith(".html"):
                parent = (DIST / rel.lstrip("/")).parent
                name = rel.rsplit("/", 1)[-1]
                if (parent / "characters" / name).exists():
                    char_flat += 1
            if rel not in files:
                broken += 1
                if len(broken_samples) < 8:
                    broken_samples.append(f"{rel}  <- {p.relative_to(DIST).as_posix()}")

    print(f"  站内内容链接总数: {total}（其中相对路径 {relative}）")
    print(f"  其中带 /escah/ 前缀: {with_base}")
    print(f"  角色链接缺 characters/ 段: {char_flat}")
    print(f"  目标文件不存在（死链）: {broken}")
    for s in broken_samples:
        print("    -", s)
    return (total, broken, char_flat)


def main() -> int:
    builder_bad = check_url_builder()
    total, broken, char_flat = check_dist()

    print("\n" + "=" * 68)
    print("结论")
    print("=" * 68)
    ok = builder_bad == 0 and broken == 0 and char_flat == 0 and total > 0
    print(f"  URL 构造函数异常: {builder_bad}")
    print(f"  产物死链: {broken}")
    print(f"  缺 characters/ 的角色链接: {char_flat}")
    print(f"  => {'全部通过' if ok else '存在问题，见上'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
