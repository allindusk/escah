"""`manifest merge`：合并 CI 抓取侧与本地重建侧写的同一批状态文件。

背景（2026-10-19 新分工）：
  CI 负责联网抓 `data/raw` + 图片 + manifest；本地负责解析/翻译/建站，也会写 manifest
  （`parsed_sha256`）与 `data/pending_assets.json`。两边都提交到同一个仓库，
  `data/manifest.json`（约 1.3 MB 单文件）**必然**在 pull 时冲突，且 1.3 MB 的
  JSON 手工解冲突没有意义 —— 所以本模块给出确定性的合并规则。

规则（都取「信息更多」的一侧，绝不丢数据）：
  pages  · `wiki_last_modified` / `sha256` / `status`：取**更新的一方**
          —— 判据是 fetched_at 新者胜；相同则以 `ok` 优于非 `ok`（挑战页/缺失页
          不该覆盖一份好快照）。
  pages  · `parsed_sha256`：**只信本地**（`_prefer` 里的 `local_only`）。
          这是本项目最关键的一条：CI 跑 `parse --no-mark` 不会写它，而万一哪次
          写了，采信它会让本地把旧解析结果误判成「已解析」→ 站点静默用旧内容。
  assets · 取并集（两边各自新增的图记录都要留）。
  其它顶层键 · 取较新的 `last_update_run`；未知键以 ours/theirs 中存在者为准。

用法（冲突解完后跑一次即可，不需要手工编辑）：
    git checkout --theirs data/manifest.json        # 或 --ours，随意
    python -m escah_pipeline.cli manifest merge
"""
from __future__ import annotations

import json
from pathlib import Path

from . import config
from .logutil import get_logger
from .snapshot import utcnow_iso

log = get_logger()

PENDING_ASSETS = config.DATA_DIR / "pending_assets.json"
RECENT_STATE = config.DATA_DIR / "recent_state.json"
PARSED_DIR = config.PARSED_JA_DIR
MERGE_MARK = config.DATA_DIR / "manifest_merge_note.json"


def _ts(entry: dict | None) -> str:
    return ((entry or {}).get("fetched_at") or "") or ""


def _better(a: dict | None, b: dict | None) -> dict | None:
    """两侧取其一：fetched_at 新者胜；同刻则 ok 优于 missing/challenged/error。"""
    a, b = a or {}, b or {}
    if not a:
        return b or None
    if not b:
        return a
    if _ts(b) > _ts(a):
        return b
    if _ts(b) == _ts(a) and (b.get("status") == "ok") != (a.get("status") == "ok"):
        return b if b.get("status") == "ok" else a
    return a


def merge_manifests(ours_path: Path | None = None,
                    theirs_path: Path | None = None) -> dict:
    """合并两个 manifest 文件。默认 ours=工作区当前文件，theirs=`.merge-theirs`。

    返回合并结果（**不写盘**，由调用方/CLI 决定）。
    """
    ours_p = ours_path or config.MANIFEST_FILE
    theirs_p = theirs_path or config.MANIFEST_FILE.with_name("manifest.merge-theirs.json")
    ours = json.loads(ours_p.read_text(encoding="utf-8")) if ours_p.exists() else {}
    theirs = json.loads(theirs_p.read_text(encoding="utf-8")) if theirs_p.exists() else {}
    if not theirs:
        raise SystemExit(f"[manifest merge] 找不到待合并文件：{theirs_p}")

    pages: dict[str, dict] = {}
    names = set(ours.get("pages") or {}) | set(theirs.get("pages") or {})
    for n in names:
        a, b = (ours.get("pages") or {}).get(n), (theirs.get("pages") or {}).get(n)
        win = _better(a, b) or {}
        merged = dict(win)
        # parsed_sha256 只信本地侧（CI 不得推进本机解析进度标记）
        local_mark = ((ours.get("pages") or {}).get(n) or {}).get("parsed_sha256")
        if local_mark is not None:
            merged["parsed_sha256"] = local_mark
        elif not ((theirs.get("pages") or {}).get(n) or {}).get("parsed_sha256"):
            merged.pop("parsed_sha256", None)
        pages[n] = merged

    assets = dict(ours.get("assets") or {})
    assets.update(theirs.get("assets") or {})

    out = dict(ours)
    out.update({k: v for k, v in theirs.items()
                if k not in ("pages", "assets", "last_update_run")})
    out["pages"] = pages
    out["assets"] = assets
    runs = [r for r in ((ours.get("last_update_run") or ""), (theirs.get("last_update_run") or "")) if r]
    out["last_update_run"] = max(runs) if runs else None
    return out


def merge_pending_assets() -> dict:
    """`data/pending_assets.json` 取并集（两边各自新增的图记录都要留）。"""
    if not PENDING_ASSETS.exists():
        return {}
    cur = json.loads(PENDING_ASSETS.read_text(encoding="utf-8"))
    other = PENDING_ASSETS.with_name("pending_assets.merge-theirs.json")
    if not other.exists():
        return cur
    inc = json.loads(other.read_text(encoding="utf-8"))
    before = len(cur)
    for k, v in inc.items():
        cur.setdefault(k, v)
    if len(cur) != before:
        log.info("[manifest merge] pending_assets 并入 %d 条（共 %d）", len(cur) - before, len(cur))
    return cur


def run_merge(write: bool = True) -> dict:
    """执行合并并（默认）写回 manifest + pending_assets。

    `write=False` 只报告差异量，供人工确认。
    """
    merged = merge_manifests()
    ours = json.loads(config.MANIFEST_FILE.read_text(encoding="utf-8")) \
        if config.MANIFEST_FILE.exists() else {}
    changed = [n for n, e in (merged.get("pages") or {}).items()
               if (ours.get("pages") or {}).get(n) != e]
    pend = merge_pending_assets()
    note = {
        "merged_at": utcnow_iso(),
        "pages_total": len(merged.get("pages") or {}),
        "pages_changed": len(changed),
        "pages_changed_sample": sorted(changed)[:10],
        "assets_total": len(merged.get("assets") or {}),
        "pending_assets_total": len(pend),
        "written": bool(write),
    }
    if write:
        config.MANIFEST_FILE.write_text(json.dumps(merged, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
        if pend:
            PENDING_ASSETS.write_text(json.dumps(pend, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
        MERGE_MARK.parent.mkdir(parents=True, exist_ok=True)
        MERGE_MARK.write_text(json.dumps(note, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("[manifest merge] %s：页 %d（变更 %d）｜资源 %d｜待下载图 %d",
             "已写盘" if write else "仅报告", note["pages_total"], note["pages_changed"],
             note["assets_total"], note["pending_assets_total"])
    return note


def cmd_manifest(args) -> int:
    if args.action == "merge":
        # 冲突解法：任意一侧落到工作区，另一侧改名让 merge 读得到即可。
        #   git checkout --ours   data/manifest.json   # 或 --theirs
        #   git mv data/manifest.json data/manifest.merge-theirs.json   # 另一侧改名
        #   python -m escah_pipeline.cli manifest merge
        run_merge(write=not getattr(args, "dry_run", False))
        return 0
    if args.action == "status":
        m = json.loads(config.MANIFEST_FILE.read_text(encoding="utf-8")) \
            if config.MANIFEST_FILE.exists() else {}
        pages = m.get("pages") or {}
        stats: dict[str, int] = {}
        for e in pages.values():
            stats[e.get("status") or "ok"] = stats.get(e.get("status") or "ok", 0) + 1
        print(json.dumps({"pages": len(pages), "by_status": stats,
                          "assets": len(m.get("assets") or {}),
                          "last_update_run": m.get("last_update_run")}, ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 1
