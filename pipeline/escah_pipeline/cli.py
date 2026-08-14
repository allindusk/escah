"""命令行入口：discover / fetch / parse / assets / translate / update / sync-plan / sync-site。"""
from __future__ import annotations

import argparse

from .logutil import get_logger

log = get_logger()


def _regen_char_refs() -> None:
    """重生成前端角色引用表 charRefs.json（供 sync-site 调用）。

    角色中文名 name_zh 一旦变更就必须重生成该文件，否则中文页角色名无法映射回
    日文 key，导致悬停浮窗失效（日文页不受影响）。旧流程需手动跑
    tools/gen_char_refs.py，易漏；这里在 sync-site 末尾自动重跑。
    """
    import importlib.util
    import os

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    script = os.path.join(root, 'tools', 'gen_char_refs.py')
    try:
        spec = importlib.util.spec_from_file_location('gen_char_refs', script)
        if spec is None or spec.loader is None:
            raise FileNotFoundError(script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
        log.info('[cli] 已重生成 charRefs.json（角色浮窗引用表）')
    except Exception as e:  # 失败不应阻断站点生成
        log.warning('[cli] 重生成 charRefs.json 失败（不影响站点内容）：%s', e)


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

    pt = sub.add_parser("translate", help="应用翻译（key 化 i18n：build→fill→char-fill，查表无正则）")
    pt.add_argument("--pages", nargs="*", help="只处理指定 slug（缺省全部）")

    pu = sub.add_parser("update", help="自动更新：处理 planned + 检测变更 → 重抓/重解析/重翻译")
    pu.add_argument("--no-translate", action="store_true", help="跳过 i18n 翻译应用")
    pu.add_argument("--full", action="store_true", help="全量逐页比对最后编辑时间（默认 RSS 增量）")

    sub.add_parser("sync-plan", help="重建 mirror_plan.yaml 的 mirrored（planned 保留）")
    sub.add_parser("sync-site", help="生成 VitePress 站点内容（ja/zh）")

    pi = sub.add_parser("i18n", help="key 化 i18n：模板+双语 JSON（取代 zh_patch 正则替换）")
    pi.add_argument("action", choices=["build", "migrate", "extract", "extract-dedup",
                                        "fill", "char-fill", "glossary-fill", "apply-dedup"],
                    help="build=生成模板+JSON；migrate=旧[N]译文按页迁移；extract=生成按页待译清单；"
                         "extract-dedup=生成跨页去重待译清单(每句只译一次)；fill=从<日期>_translated.txt回填；"
                         "char-fill=角色JSON补zh；glossary-fill=把词汇表已覆盖的词一次性填进各页i18n(真值)；"
                         "apply-dedup=把去重译文按出现位置写回所有页")
    pi.add_argument("--pages", nargs="*", help="只处理指定 slug（缺省全部）")
    pi.add_argument("--todo", help="fill 时指定待译清单文件名（默认用 _todo_translate/ 下最新一份 <日期>.txt）")
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
        _run_zh_patch(pages=args.pages)
    elif args.cmd == "update":
        from .updater import run_update
        run_update(no_translate=args.no_translate, full=args.full)
    elif args.cmd == "sync-plan":
        from .plan import sync_plan
        sync_plan()
    elif args.cmd == "sync-site":
        from .sitegen import sync_site
        sync_site()
        # 重生成前端角色引用表 charRefs.json：角色中文名（name_zh）一变就必须重生成，
        # 否则中文页的角色名无法映射回日文 key → 悬停浮窗失效（日文页正常）。
        # 旧流程需手动跑 tools/gen_char_refs.py，容易漏；这里接入自动重生成。
        _regen_char_refs()
    elif args.cmd == "i18n":
        from . import i18n
        if args.action == "build":
            i18n.build_all(slugs=args.pages)
        elif args.action == "migrate":
            i18n.migrate_all(slugs=args.pages)
        elif args.action == "extract":
            i18n.extract_todo(slugs=args.pages)
        elif args.action == "char-fill":
            i18n.char_fill_all()
        elif args.action == "fill":
            if args.todo:
                i18n.fill_todo(args.todo, slugs=args.pages)
            else:
                i18n.fill_latest_todo(slugs=args.pages)
        elif args.action == "glossary-fill":
            i18n.cmd_glossary_fill(args)
        elif args.action == "extract-dedup":
            i18n.cmd_extract_dedup(args)
        elif args.action == "apply-dedup":
            i18n.cmd_apply_dedup(args)


if __name__ == "__main__":
    main()
