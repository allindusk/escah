"""命令行入口：discover / fetch / parse / assets / translate / update / sync-plan / sync-site。"""
from __future__ import annotations

import argparse

from .logutil import get_logger

log = get_logger()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="escah-pipeline",
        description="超昂大戦 WIKI 中日双语镜像数据流水线",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("discover", help="两阶段发现：MenuBar → 观察页；キャラクター一覧 → 角色详情页")

    pf = sub.add_parser("fetch", help="按注册表抓取页面（断点续抓）")
    pf.add_argument("--force", action="store_true", help="忽略已有快照全部重抓")
    pf.add_argument("--mode", choices=["all", "watch", "static"], default="all")
    pf.add_argument("--pages", nargs="*", help="只抓指定页面名")

    pp = sub.add_parser("parse", help="解析快照 → 日文 Markdown / 角色 JSON")
    pp.add_argument("--pages", nargs="*")
    pp.add_argument("--force", action="store_true")

    pa = sub.add_parser("assets", help="下载页面引用的图片资源（哈希命名去重）")
    pa.add_argument("--force", action="store_true")

    pt = sub.add_parser("translate", help="翻译日文 Markdown → 中文（词典引擎 tools/zh_patch.py，无 LLM）")
    pt.add_argument("--pages", nargs="*", help="保留参数兼容（zh_patch 统一处理全部页）")

    pu = sub.add_parser("update", help="自动更新：处理 planned + 检测变更 → 重抓/重解析/重翻译")
    pu.add_argument("--no-translate", action="store_true", help="跳过 zh_patch 翻译")
    pu.add_argument("--full", action="store_true", help="全量逐页比对最后编辑时间（默认 RSS 增量）")

    sub.add_parser("sync-plan", help="重建 mirror_plan.yaml 的 mirrored（planned 保留）")
    sub.add_parser("sync-site", help="生成 VitePress 站点内容（ja/zh）")
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.cmd == "discover":
        from .registry import discover
        discover()
        from .plan import sync_plan
        sync_plan()
    elif args.cmd == "fetch":
        from .fetcher import fetch_registered_pages
        fetch_registered_pages(force=args.force, mode=args.mode, only=args.pages)
    elif args.cmd == "parse":
        from .parser_puki import parse_all
        parse_all(pages=args.pages, force=args.force)
        from .chara import extract_all_characters
        extract_all_characters(force=args.force)
    elif args.cmd == "assets":
        from .assets import download_assets
        download_assets(force=args.force)
    elif args.cmd == "translate":
        from .updater import _run_zh_patch
        _run_zh_patch()
    elif args.cmd == "update":
        from .updater import run_update
        run_update(no_translate=args.no_translate, full=args.full)
    elif args.cmd == "sync-plan":
        from .plan import sync_plan
        sync_plan()
    elif args.cmd == "sync-site":
        from .sitegen import sync_site
        sync_site()


if __name__ == "__main__":
    main()
