"""命令行入口：discover / fetch / parse / assets / translate / update / sync-plan / sync-site。"""
from __future__ import annotations

import argparse
import os

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
    pp.add_argument("--no-mark", dest="mark", action="store_false", default=True,
                    help="**不**写 manifest 的 parsed_sha256 解析进度标记。"
                         "CI 专用：它跑 parse 只是为了产出 pending_assets.json（下载图片用），"
                         "若写标记会让本地 pull 后误判「已解析」而跳过重解析 → 站点用旧内容且无报错")

    pa = sub.add_parser("assets", help="下载页面引用的图片资源（哈希命名去重）")
    pa.add_argument("--force", action="store_true")

    pt = sub.add_parser("translate", help="应用翻译（key 化 i18n：build→fill→char-fill，查表无正则）")
    pt.add_argument("--pages", nargs="*", help="只处理指定 slug（缺省全部）")

    pu = sub.add_parser("update", help="自动更新：处理 planned + 检测变更 → 重抓/重解析/词表注入")
    pu.add_argument("--no-translate", action="store_true", help="跳过 i18n 翻译应用")
    # ⚠️ 2026-09-28 方针变更（用户决定）：**默认不再调用谷歌机翻** ✓ ——
    #   免费端点质量不可控（实测旧"预替换"路径 chrF3 仅 0.175、术语命中 37.8%，且会产出
    #   「抗眩光低血糖症列表」这类乱译 ✗✗），改为人工/自然语言精翻。
    #   要与 CI 一致（CI 已停用机翻，见 .github/workflows/sync-cron.yml），故默认关闭 ✓。
    #   需要临时开启：`update --gtrans`（仍只翻本次变更页产出的待译清单，不扫整目录 ✓）。
    pu.add_argument("--gtrans", action="store_true",
                    help="启用谷歌机翻（**默认关闭**：只翻本次变更页产出的待译清单再 fill 回填）")
    pu.add_argument("--full", action="store_true", help="全量逐页比对最后编辑时间（默认 RSS 增量）")

    ps = sub.add_parser("sync-stale",
                        help="并行比对原站「最終更新日時」，只把**变更页**的快照落盘"
                             "（= update --full 的快版：后者走串行礼貌抓取，675 页要 30+ 分钟）")
    ps.add_argument("--dry-run", action="store_true", help="只报告哪些页需要更新，不写盘")
    ps.add_argument("--workers", type=int, default=13, help="并发线程数（默认 13）")

    # 更新履歴驱动的增量通道：1 次请求拿到「最新 100 条（日期+页面名）」→ 只探候选页。
    # 与 sync-stale 是**互补**关系（廉价日常 / 权威兜底），见 updater.sync_recent_pages 的
    # 高可用设计说明（窗口饱和回退、盲区可观测、--verify 交叉校验）。
    pr = sub.add_parser("sync-recent",
                        help="读原站「更新履歴ページ」缩小候选集，只对候选页比对「最終更新日時」"
                             "（1 次请求；窗口覆盖不足时自动回退 sync-stale 全量）")
    pr.add_argument("--dry-run", action="store_true", help="只报告哪些页需要更新，不写盘")
    pr.add_argument("--workers", type=int, default=13, help="并发线程数（默认 13）")
    pr.add_argument("--no-fallback", action="store_true",
                    help="窗口饱和/解析失败时**不**回退全量比对（只报告，用于观测）")
    pr.add_argument("--verify", action="store_true",
                    help="交叉校验：本次额外跑一遍全量比对，报告两条通道的变更集差异")
    pr.add_argument("--margin-days", type=int, default=1,
                    help="窗口余量：更新履歴最旧日期须比上次同步再早这么多天，否则回退（默认 1）")

    # 原站「更新履歴ページ」周存档（2026-10-19 起 CI 只做这一件事）：
    # 1 次请求拿最新 100 条 → 与 registry/manifest 对照 → 落 data/upstream/ 入库。
    # 本地更新前拉 latest.json 就知道哪些页是新增、哪些需重抓，不必全量爬取比对。
    pc = sub.add_parser("changelog",
                        help="原站「更新履歴ページ」周存档：fetch=抓取落盘；show=摘要；names=待处理页面名")
    pc.add_argument("action", nargs="?", default="fetch", choices=["fetch", "show", "names"],
                    help="fetch=抓取并写 data/upstream/（latest.json + weekly/<周>.json/.md）；"
                         "show=打印最新存档摘要；names=只打印需要处理（new/update）的页面名")
    pc.add_argument("--all", action="store_true",
                    help="names 专用：连 unchanged/excluded/frozen 一起输出")
    pc.add_argument("--html",
                    help="fetch 专用：解析本地 HTML 而不联网（原站对本机直连会返回"
                         "「少々お待ちください…」等待页，可在浏览器另存该页后用此参数）")
    pc.add_argument("--cookie",
                    help="fetch 专用：附加 Cookie（可填浏览器里的 cf_clearance 以通过 "
                         "Cloudflare 验证；也可用环境变量 WIKIRU_COOKIE 注入）")
    pc.add_argument("--browser", action="store_true",
                    help="fetch 专用：HTTP 被验证页拦截时，改用真实浏览器(playwright+chromium)"
                         "重试——能执行 JS，Cloudflare 的无感挑战通常会在 reload 后放行")

    # go/no-go 探针：只抓一页，判定「HTTP/浏览器通道能不能拿到正文」。
    # 新分工（CI 抓 raw / 本地离线镜像化）能否成立全看这一条 —— 本机被 Cloudflare
    # 挑战挡住，而 Actions 出口同样是数据中心 IP，必须先实测。
    pprobe = sub.add_parser("probe", help="只抓一页并判定是否拿到正文（不写盘，CI go/no-go 用）")
    pprobe.add_argument("--page", default="キャラクター一覧", help="探针页面名（默认角色一览）")
    pprobe.add_argument("--cookie", help="附加 Cookie（cf_clearance）；也可用 WIKIRU_COOKIE")
    pprobe.add_argument("--browser", action="store_true", help="HTTP 失败后改用真实浏览器重试")
    pprobe.add_argument("--attempts", type=int, default=3, help="HTTP 重试次数（默认 3，退避 6s×n）")

    sub.add_parser("sync-plan", help="重建 mirror_plan.yaml 的 mirrored（planned 保留）")
    sub.add_parser("sync-site", help="生成 VitePress 站点内容（ja/zh）")

    # 2026-10-19 新分工下的**本地**主命令：零网络请求，从已入库的 data/raw 重建一切。
    # 起因是本机直连原站会被 Cloudflare 无感挑战挡住 → 抓取交给 CI（见 sync-fetch.yml），
    # 本地只做镜像化。详见 local_sync.py 顶部说明。
    pls = sub.add_parser("local-sync",
                         help="离线本地重建：parse → i18n build（仅落后的页）→ char-fill → "
                              "待译清单 → sync-site。**全程不联网**（raw 由 CI 抓好入库）")
    pls.add_argument("--pages", nargs="*", help="只处理指定页（页名或 slug 均可）")
    pls.add_argument("--force", action="store_true", help="强制重解析（默认按 sha256 增量）")
    pls.add_argument("--rebuild-i18n", action="store_true",
                     help="忽略内容指纹，强制重跑 i18n build（仍按 ja 文本回贴，不丢译文）")
    pls.add_argument("--fresh", action="store_true",
                     help="i18n build 不回贴旧译文（全量重翻，慎用）")
    pls.add_argument("--no-translate", action="store_true", help="跳过 i18n build / char-fill")
    pls.add_argument("--no-char-fill", action="store_true", help="跳过角色 JSON 的 zh 回填")
    pls.add_argument("--no-extract", action="store_true", help="不生成待译清单")
    pls.add_argument("--no-site", action="store_true", help="不跑 sync-site")
    pls.add_argument("--dry-run", action="store_true", help="只报告将要做什么，不写盘")

    pm2 = sub.add_parser("manifest",
                         help="合并 CI 抓取侧与本地重建侧写的 manifest.json / pending_assets.json")
    pm2.add_argument("action", choices=["merge", "status"],
                     help="merge=合并（另一侧先改名成 *.merge-theirs.json）；status=概览")
    pm2.add_argument("--dry-run", action="store_true", help="merge 专用：只报告差异，不写盘")

    pi = sub.add_parser("i18n", help="key 化 i18n：模板+双语 JSON（取代 zh_patch 正则替换）")
    pi.add_argument("action", choices=["build", "migrate", "extract", "extract-dedup", "verify-links",
                                        "fill", "char-fill", "glossary-fill", "apply-dedup",
                                        "repair-glossary", "fix-br", "phrase-fill", "retain-scan"],
                    help="build=生成模板+JSON；migrate=旧[N]译文按页迁移；extract=生成按页待译清单；"
                         "extract-dedup=生成跨页去重待译清单(每句只译一次)；fill=从<日期>_translated.txt回填；"
                         "char-fill=角色JSON补zh；glossary-fill=把词汇表已覆盖的词一次性填进各页i18n(真值)；"
                         "apply-dedup=把去重译文按出现位置写回所有页；"
                         "phrase-fill=把 glossary/phrases.yaml 的整块/整句译文注入各页 i18n(默认 dry-run)；"
                         "retain-scan=结构化抽取人名等「保留原文」名单 → glossary/retain_ja.yaml(默认 dry-run)")
    pi.add_argument("--pages", nargs="*", help="只处理指定 slug（缺省全部）")
    pi.add_argument("--apply", action="store_true",
                    help="repair-glossary / phrase-fill / retain-scan 专用：真正写盘"
                         "（默认 dry-run，只打印将要改的内容）")
    pi.add_argument("--revert", action="store_true",
                    help="phrase-fill 专用：反向操作——把 zh 恰好等于 phrases.yaml 译文的条目清空"
                         "（用于回退误注入，不碰其它译文）")
    pi.add_argument("--fresh", action="store_true",
                    help="build 专用：全量重翻，不回贴旧译文（zh 全空）。"
                         "默认按 ja 文本内容回贴，句子没变的保住译文、变了的留空进待译")
    pi.add_argument("--todo", help="fill 时指定待译清单文件名；"
                                   "注意：该参数隐含旧的位置序号 [N] 模式，见 --no-per-page 的风险说明")
    pi.add_argument("--per-page", action=argparse.BooleanOptionalAction, default=True,
                    help="v2 按页_日期生成/回填（条目 [keyN]/[blkN] 直接对应 i18n id，按 id 精确写回）。"
                         "【默认开启】extract 生成 <slug>_YYYYMMDD.txt + _index.json；fill 按 id 回填。"
                         "用 --no-per-page 可退回旧的位置序号 [N] 模式——不推荐：fill 会重新计算"
                         "待译集合并按序号对齐，extract→fill 之间集合一旦变动（如跑了 glossary-fill、"
                         "apply-dedup 或部分条目已被译）就会整体错位，且不会报错。")
    pi.add_argument("--pages-file", help="v2 extract 用的 diff 清单（.workbuddy/diff_pages.json），"
                                         "action 自动同步时传入本次新增/更新页")
    pi.add_argument("--date", help="v2 日期标签 YYYYMMDD（缺省当天），用于命名 <slug>_YYYYMMDD.txt")

    pg = sub.add_parser("gtrans",
                        help="谷歌免费翻译：把 _todo_translate/ 下待译清单翻成 *_translated.txt")
    pg.add_argument("paths", nargs="*",
                    help="待译文件或目录（缺省=tools/_todo_translate/ 全部未译清单）")
    pg.add_argument("--src", default="ja", help="源语言（默认 ja）")
    pg.add_argument("--tgt", default="zh-CN", help="目标语言（默认 zh-CN）")
    pg.add_argument("--force", action="store_true", help="覆盖已存在的 *_translated.txt")

    pm = sub.add_parser("mt", help="机翻留档与后续精翻：record/export/apply/status")
    pm.add_argument("action", choices=["record", "export", "apply", "status"],
                    help="record=把机翻产物按页留档到 data/mt/（入库，供后续精翻）；"
                         "export=导出精翻清单到 tools/_mt_refine/；"
                         "apply=把精翻结果按 id 写回 i18n 真值并销账（默认 dry-run）；"
                         "status=留档概览（还剩多少条待精翻）")
    pm.add_argument("path", nargs="?", help="apply 专用：精翻清单文件或目录")
    pm.add_argument("--out", help="export 专用：输出目录（缺省 tools/_mt_refine/）")
    pm.add_argument("--single", action="store_true",
                    help="export 专用：额外合成一份总表 _all_<日期>.txt"
                         "（按 `=== <页> ===` 分段，便于整份交给 LLM/人工精翻，"
                         "apply 可直接识别）")
    pm.add_argument("--date", help="记录/导出用的日期标签 YYYYMMDD（缺省=全部译文卷）")
    pm.add_argument("--write", action="store_true",
                    help="apply 专用：真正写盘（默认只报告将要改哪些条目）")
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
        parse_all(pages=args.pages, force=args.force, mark=args.mark)
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
        # 机翻默认关闭（2026-09-28 方针）；`--gtrans` 才开启。
        run_update(no_translate=args.no_translate, full=args.full,
                   no_gtrans=not args.gtrans)
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
    elif args.cmd == "local-sync":
        from .local_sync import cmd_local_sync
        cmd_local_sync(args)
    elif args.cmd == "probe":
        from .probe import cmd_probe
        raise SystemExit(cmd_probe(args))
    elif args.cmd == "manifest":
        from .manifest_merge import cmd_manifest
        cmd_manifest(args)
    elif args.cmd == "i18n":
        from . import i18n
        if args.action == "build":
            # 默认按 ja 文本回贴旧译文（原站增删段落时不会整页丢译文）；
            # 仅在显式 --fresh 时才全量重翻。
            i18n.build_all(slugs=args.pages, fresh=getattr(args, "fresh", False))
        elif args.action == "migrate":
            i18n.migrate_all(slugs=args.pages)
        elif args.action == "extract":
            if getattr(args, "per_page", True):
                i18n.extract_todo_per_page(date=getattr(args, "date", None),
                                           slugs=args.pages,
                                           pages_file=getattr(args, "pages_file", None))
            else:
                log.warning("[i18n extract] 使用旧的位置序号模式（--no-per-page），"
                            "回填时存在错位风险，建议改用默认 --per-page")
                i18n.extract_todo(slugs=args.pages)
        elif args.action == "char-fill":
            i18n.char_fill_all()
        elif args.action == "fill":
            if getattr(args, "per_page", True):
                i18n.fill_todo_per_page(date=getattr(args, "date", None), slugs=args.pages)
            elif args.todo:
                log.warning("[i18n fill] 使用旧的位置序号模式（--no-per-page），"
                            "待译集合若已变动会整体错位，建议改用默认 --per-page")
                i18n.fill_todo(args.todo, slugs=args.pages)
            else:
                log.warning("[i18n fill] 使用旧的位置序号模式（--no-per-page），"
                            "待译集合若已变动会整体错位，建议改用默认 --per-page")
                i18n.fill_latest_todo(slugs=args.pages)
        elif args.action == "verify-links":
            i18n.verify_link_parity()
        elif args.action == "glossary-fill":
            i18n.cmd_glossary_fill(args)
        elif args.action == "phrase-fill":
            i18n.cmd_phrase_fill(args)
        elif args.action == "retain-scan":
            i18n.cmd_retain_scan(args)
        elif args.action == "extract-dedup":
            i18n.cmd_extract_dedup(args)
        elif args.action == "apply-dedup":
            i18n.cmd_apply_dedup(args)
        elif args.action == "repair-glossary":
            # 把词表回补到「已译但残留日文术语」的译文上，消除这部分条目的反复重译。
            # 默认 dry-run，需 --apply 才写盘。
            i18n.repair_glossary_residue(apply=getattr(args, "apply", False))
        elif args.action == "fix-br":
            # 一次性规范化：按 ja 的段落结构重建 zh 的换行，使全站段结构严格对齐。
            # 对齐后 build 回贴即纯文本匹配，不会再出现「越 build 越错位」的连锁问题。
            # 默认 dry-run，需 --apply 才写盘。
            i18n.fix_block_breaks(apply=getattr(args, "apply", False))
    elif args.cmd == "gtrans":
        from pathlib import Path

        from . import gtrans
        from .i18n import TODO_DIR
        paths = args.paths or [str(TODO_DIR)]
        for raw in paths:
            p = Path(raw)
            if p.is_dir():
                gtrans.translate_todo_dir(p, src=args.src, tgt=args.tgt,
                                          skip_existing=not args.force)
            elif p.exists():
                gtrans.translate_todo_file(p, src=args.src, tgt=args.tgt)
            else:
                log.warning("[gtrans] 路径不存在：%s", p)
    elif args.cmd == "sync-stale":
        from .updater import sync_stale_pages

        names = sync_stale_pages(dry_run=args.dry_run, workers=args.workers)
        log.info("[sync-stale] %s %d 页", "将更新" if args.dry_run else "已更新", len(names))
    elif args.cmd == "sync-recent":
        from .updater import sync_recent_pages, verify_recent_vs_stale

        rep = sync_recent_pages(
            dry_run=args.dry_run,
            workers=args.workers,
            fallback=not args.no_fallback,
            margin_days=args.margin_days,
        )
        log.info(
            "[sync-recent] 窗口 %s→%s｜条目 %d（触顶 %s）｜候选 %d｜变更 %d｜回退 %s%s",
            rep["window"][0], rep["window"][1], rep["entries"], rep["truncated"],
            rep["candidates"], len(rep["changed"]), rep["fell_back"],
            f"（{rep['reason']}）" if rep["reason"] else "",
        )
        if rep["unregistered"] or rep["known_nav"]:
            # 细节由 updater.sync_recent_pages 分别打日志：前者是"多为新增角色页"（允许自动登记
            # 的那类，实际由 discover Phase 2 登记），后者是"已知导航/系统页但我们有意不镜像"
            # （登记会进左侧导航栏，必须人工确认 —— 用户约束 2026-09-27）。
            log.info(
                "[sync-recent] 未登记：角色页候选 %d 个｜已知导航/系统页未镜像 %d 个"
                "（两侧都不会被本命令自动登记）",
                len(rep["unregistered"]), len(rep["known_nav"]),
            )
        if args.verify:
            out = verify_recent_vs_stale(workers=args.workers)
            log.info(
                "[verify] 更新履歴通道 %d 页 / 全量通道 %d 页｜"
                "**全量发现而履歴漏掉** %d 页｜履歴多出 %d 页",
                len(out["recent"]), len(out["stale"]),
                len(out["missed_by_recent"]), len(out["extra_by_recent"]),
            )
            for n in out["missed_by_recent"]:
                log.warning("[verify] 履歴漏检：%s", n)
    elif args.cmd == "changelog":
        import json

        from . import changelog

        if args.action == "fetch":
            html = Path(args.html).read_text(encoding="utf-8") if args.html else None
            cookie = args.cookie or os.environ.get("WIKIRU_COOKIE") or None
            snap = changelog.build(html=html, cookie=cookie, browser=args.browser)
            if not snap["items"]:
                # 原站返回等待页/结构变化时解析为 0 条 —— 若照写会用空存档覆盖上周的，
                # 那比"没有存档"更糟（本地据此以为原站啥也没动）。宁可失败保留旧档。
                raise SystemExit("[changelog] 解析到 0 条（疑似反爬等待页或页面结构变化），"
                                 "已放弃写入以保留上次存档")
            paths = changelog.save(snap)
            c = snap["counts"]
            log.info("[changelog] %s｜窗口 %s→%s｜新增 %d / 需更新 %d / 无变化 %d / 排除 %d / 冻结 %d",
                     snap["iso_week"], snap["window"][0], snap["window"][1],
                     c.get("new", 0), c.get("update", 0), c.get("unchanged", 0),
                     c.get("excluded", 0), c.get("frozen", 0))
            print(json.dumps(paths, ensure_ascii=False, indent=1))
        elif args.action == "show":
            snap = changelog.latest()
            if not snap:
                raise SystemExit("尚无存档，先跑：python -m escah_pipeline.cli changelog fetch")
            print(changelog._to_markdown(snap))
        else:
            snap = changelog.latest()
            if not snap:
                raise SystemExit("尚无存档，先跑：python -m escah_pipeline.cli changelog fetch")
            for n in changelog.actionable_names(
                snap, None if args.all else changelog.ACTIONABLE,
            ):
                print(n)
    elif args.cmd == "mt":
        # 机翻留档 → 精翻闭环（见 escah_pipeline/mt.py 顶部说明）
        from . import mt

        if args.action == "record":
            mt.record(date=args.date)
        elif args.action == "export":
            mt.export(out=args.out, date=args.date, single=args.single)
        elif args.action == "apply":
            if not args.path:
                raise SystemExit("mt apply 需要给出精翻清单路径："
                                 "mt apply tools/_mt_refine --write")
            mt.apply(args.path, write=args.write)
        else:
            mt.status()


if __name__ == "__main__":
    main()
