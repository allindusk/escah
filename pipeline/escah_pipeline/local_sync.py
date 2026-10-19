"""`local-sync`：**完全离线**的本地重建（原站 raw 已在库里 → 解析 → 翻译应用 → 站点）。

为什么要有这个命令（2026-10-19）：
  本机直连原站会被 Cloudflare 无感挑战挡住（记忆：本机 40 秒过不去，是出口 IP 层面），
  所以新的分工是：**CI 负责联网抓 raw**（`data/raw` 入库），**本地只负责镜像化**。
  原先的 `cli update` 把「检测变更（联网）→ 抓取（联网）→ 解析 → 翻译 → 建站」串在一起，
  在本地跑等于每次都要先撞一次挑战墙；本命令把其中的联网部分整段拿掉：

      git pull                 # 取回 CI 抓好的 raw / 图片 / 更新履歴存档
      escah-pipeline local-sync # ← 本命令：零网络请求地重建全部派生产物
      （人工翻译 → fill → 需要时再 local-sync --pages …）

与既有命令的关系（不要重复造）：
  · `parse`       —— 仍按 sha256 增量，本命令只是按需调用它（并传 pages 限定范围）；
  · `assets`      —— **不在**这里跑：图片由 CI 下载并转 WebP 入库（本地抓不到原站图）。
                     若 pending_assets 里还有本地也没有的图，报告里会列出来提醒。
  · `i18n build`  —— 只对「ja 片段比模板新 / 模板缺失」的页跑（mtime 判定），
                     避免全量重写 i18n JSON 造成入库文件的无谓 diff。
  · `sync-site`   —— 同 `cli sync-site`，产物（site/*.md、frag、public）本来就不入库。

「同页更新不丢译文」由 i18n.build_page 的**按 ja 文本内容回贴**保证（见该函数 docstring）；
本命令额外产出报告：本次 build 失效了多少条旧译文（data/upstream/build_report.json）。
"""
from __future__ import annotations

import json
from pathlib import Path

from . import config
from .logutil import get_logger
from .snapshot import Manifest, utcnow_iso

log = get_logger()

REPORT_FILE = config.DATA_DIR / "upstream" / "local_sync.json"
# 「本轮哪些页的 raw 与上次解析不一致」——**唯一判据就是 manifest 自己的两个字段**。
#   sha256         = 当前 raw 快照的哈希
#   parsed_sha256  = 本机上次成功解析这份 raw 时的哈希（`parse` 写入，见 parse --no-mark）
# 两者不等 = 这页 raw 变过或还没解析过 → 解析后 ja 内容变了 → 只有它需要重跑 i18n build。
#
# 为什么不用「ja 片段 mtime」或自建指纹索引：
#   · mtime：parse 会把内容没变的片段也重写一遍，实测 546/546 页被误判成需要 build；
#   · 自建索引（曾用 data/parsed/i18n_src_index.json）：索引文件**不入库**，一旦被
#     `git clean -xdf`／换机／删 data 目录清掉，就退化成「全站都没记录」→ 全量 build →
#     把库里那 633 条「节点级被块级整句覆盖」的脏数据扩散（2026-10-18 实测，见
#     tools/_dev/_diag_dirty_blockzh.py）。manifest 字段本身就在库里、随提交走，
#     不依赖任何本地产物，天然不会误触发全量。
#
# 什么情况**需要**全量 build：改了 i18n build 本身的规则（`_sanitize_html`／路由改写／
# key 化逻辑）—— 那是改代码的场景，显式用 `--rebuild-i18n`，不靠自动判定。


def _stale_page_names() -> set[str]:
    """raw 与本机上次解析不一致的页名集合（= parse 本轮会真正重解析的那些页）。"""
    from .snapshot import Manifest

    m = Manifest()
    out: set[str] = set()
    for name, e in (m.data.get("pages") or {}).items():
        if not isinstance(e, dict):
            continue
        if e.get("parsed_sha256") and e.get("parsed_sha256") == e.get("sha256"):
            continue
        out.add(name)
    return out


def _needs_i18n(slug: str, stale_names: "set[str] | None" = None,
                name: "str | None" = None) -> bool:
    """该页是否需要重跑 i18n build。

    需要 = ① ja 片段缺失（本地派生产物被清空）｜② 模板/字典缺失｜③ raw 变过（stale）。
    不需要 = 其余情况（原文句子没变 → 现有 JSON 就是对的，重建毫无意义且有污染风险）。
    """
    from .i18n import _tpl_path

    ja = config.PARSED_JA_DIR / f"{slug}.html"
    if not ja.exists():
        return False                      # 没 ja 源，build_page 也做不了
    if not _tpl_path(slug).exists():
        return True
    if stale_names is None:
        return False                     # 调用方没给 stale 集合时 = 不动（保守）
    return bool(name) and name in stale_names


def run_local_sync(
    pages: "list[str] | None" = None,
    force_parse: bool = False,
    translate: bool = True,
    char_fill: bool = True,
    extract: bool = True,
    site: bool = True,
    fresh: bool = False,
    rebuild_i18n: bool = False,
    dry_run: bool = False,
) -> dict:
    """离线重建。返回报告 dict（同时写 data/upstream/local_sync.json）。

    参数开关（默认路径 = 一次「pull 之后的标准重建」）：
      pages        只处理指定页（页名或 slug 都可）；缺省 = registry 全部
      force_parse  强制重解析（默认按 sha256 增量）
      rebuild_i18n 忽略内容指纹，**强制**重跑 i18n build（仍按 ja 文本回贴译文，不丢）
      translate    False = 跳过 i18n build/char-fill
      char_fill    False = 跳过角色 JSON 的 zh 回填
      extract      False = 不生成待译清单
      site         False = 不跑 sync-site
      fresh        True = build 不回贴旧译文（全量重翻，慎用）
      dry_run      只报告将要做什么，不写任何盘
    """
    from .chara import extract_all_characters
    from .i18n import (
        build_page,
        char_fill_all,
        extract_todo_per_page,
        has_i18n,
    )
    from .parser_puki import parse_all
    from .registry import load_registry

    config.ensure_dirs()
    entries = load_registry()
    if not entries:
        raise SystemExit("[local-sync] 注册表为空：先跑 discover / fetch（或从 CI 取回 raw）")
    name_by_slug = {e["slug"]: e["name"] for e in entries}
    slugs = [e["slug"] for e in entries]
    if pages:
        want = set(pages)
        slugs = [s for s in slugs if s in want or s.split("/")[-1] in want]
        if not slugs:
            raise SystemExit(f"[local-sync] --pages 未匹配到任何页：{pages}")

    report: dict = {
        "generated_at": utcnow_iso(),
        "pages_in_scope": len(slugs),
        "pages": pages,
        "dry_run": dry_run,
        "parsed": [],
        "i18n_built": [],
        "todo_files": [],
        "lost_translations": {},
        "pending_assets_missing": [],
        "sync_site": False,
    }

    # ---- ① 解析（增量；CI 抓来的新 raw 会自动进本轮）----
    # stale 必须在 parse **之前**取：parse 成功后会推进 parsed_sha256，之后差集就空了。
    stale = _stale_page_names()
    page_names = [name_by_slug[s] for s in slugs]
    if dry_run:
        log.info("[local-sync][dry-run] 将解析：%s", "、".join(page_names[:8]) or "（全部）")
    else:
        parse_all(pages=page_names, force=force_parse)
        extract_all_characters()
    report["parsed"] = page_names if force_parse else [n for n in page_names if n in stale]

    # ---- ② 只对本轮 ja 真的变了的页跑 i18n build ----
    force_all = fresh or rebuild_i18n
    targets = slugs if force_all else [
        s for s in slugs if _needs_i18n(s, stale, name_by_slug.get(s))
    ]
    log.info("[local-sync] i18n build 目标 %d 页（%s）", len(targets),
             "全量重建" if force_all else "raw 变过 → ja 变了的页")
    lost: dict[str, int] = {}
    lost_samples: dict[str, list] = {}
    if translate:
        if dry_run:
            report["i18n_built"] = targets
        else:
            for i, slug in enumerate(targets, 1):
                r = build_page(slug, fresh=fresh)
                if r is None:
                    log.warning("[local-sync] %s 无 ja 源，跳过", slug)
                    continue
                report["i18n_built"].append(slug)
                if r.get("lost"):
                    lost[slug] = r["lost"]
                    lost_samples[slug] = r.get("lost_samples", [])
                    for smp in r.get("lost_samples", [])[:2]:
                        log.warning("[local-sync] %s 失效条目：ja=%s｜旧译=%s",
                                    slug, smp.get("ja", "")[:40], smp.get("zh", "")[:40])
                if i % 50 == 0 or i == len(targets):
                    log.info("[local-sync] i18n build %d/%d", i, len(targets))
            report["lost_translations"] = lost
            if lost:
                log.warning("[local-sync] ⚠️ 本轮共 %d 条旧译文失效，明细见 "
                            "data/upstream/build_report.json", sum(lost.values()))
            # 失效明细（与 `i18n build` 写同一份文件，入库留痕）
            BR = config.DATA_DIR / "upstream" / "build_report.json"
            BR.parent.mkdir(parents=True, exist_ok=True)
            BR.write_text(json.dumps({
                "generated_at": utcnow_iso(),
                "source": "local-sync" + (" --rebuild-i18n" if rebuild_i18n else ""),
                "pages_built": len(report["i18n_built"]),
                "lost_total": sum(lost.values()),
                "note": "lost = 旧译文因原站改文/删段而失效；samples 带**旧译文**，重译时据此改",
                "lost_pages": sorted(
                    ({"slug": k, "lost": v, "samples": lost_samples.get(k, [])}
                     for k, v in lost.items()),
                    key=lambda d: -d["lost"])[:50],
            }, ensure_ascii=False, indent=1), encoding="utf-8")
        if char_fill and not dry_run:
            char_fill_all()

    # ---- ③ 待译清单（只针对本轮 build 过的页）----
    if extract and not dry_run:
        todo_slugs = [s for s in report["i18n_built"] if has_i18n(s)]
        if todo_slugs:
            report["todo_files"] = extract_todo_per_page(slugs=todo_slugs)
            log.info("[local-sync] 待译清单 %d 个 → tools/_todo_translate/", len(report["todo_files"]))

    # ---- ④ 图片：本地抓不到原站，缺图只能靠 CI；这里只报缺哪些 ----
    pending_path = config.DATA_DIR / "pending_assets.json"
    if pending_path.exists():
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
        missing = [u for u, fn in pending.items()
                   if not (config.ASSETS_IMG_DIR / fn).exists()]
        report["pending_assets_missing"] = missing
        if missing:
            log.warning("[local-sync] ⚠️ %d 张图本地没有（需 CI 跑 assets，或有网时手动 "
                        "`cli assets`）：%s", len(missing), "、".join(missing[:3]))

    # ---- ⑤ 站点内容 ----
    if site and not dry_run:
        from .sitegen import sync_site

        sync_site()
        report["sync_site"] = True

    # ---- ⑥ 落报告（入库留痕，便于事后对照）----
    manifest = Manifest()
    report["raw_pages"] = len(manifest.data.get("pages", {}))
    if not dry_run:
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                               encoding="utf-8")
        from .cli import _regen_char_refs

        if report["sync_site"]:
            _regen_char_refs()

    log.info("[local-sync] 完成：解析 %d 页｜i18n build %d 页｜待译清单 %d 个｜"
             "旧译文失效 %d 条｜缺图 %d 张｜站点%s",
             len(report["parsed"]), len(report["i18n_built"]),
             len(report["todo_files"]), sum(lost.values()),
             len(report["pending_assets_missing"]),
             "已生成" if report["sync_site"] else "未生成（--skip-site）")
    return report


def cmd_local_sync(args) -> int:
    run_local_sync(
        pages=args.pages,
        force_parse=args.force,
        translate=not args.no_translate,
        char_fill=not args.no_char_fill,
        extract=not args.no_extract,
        site=not args.no_site,
        fresh=args.fresh,
        rebuild_i18n=getattr(args, "rebuild_i18n", False),
        dry_run=args.dry_run,
    )
    return 0
