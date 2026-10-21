# -*- coding: utf-8 -*-
"""图片「可读名 ↔ 磁盘名」对照表（旁路索引，不动任何图片文件）。

为什么要有这个（2026-10-20 用户要求）：
  data/assets/img 里全是 `<sha256(源URL)[:16]>.webp`，找图时看名字认不出是什么图。
  真改名要动 3129 个文件 + 全部引用（虽然引用都在可重建产物里），用户不想冒这个变更；
  于是改成**旁路对照表**：文件名一个不动，只用一张表把「原站可读名」和「磁盘哈希名」对起来，
  Ctrl+F 搜可读名 → 同行就是它的磁盘文件名。

信息来源：**完全自动生成**，不要手工编辑本表
  · 名字来源 = data/pending_assets.json 里的源 URL（源站把文件名编成了 UTF-8 十六进制，
    见 readable_name；解不出来的条目退回 basename，再不行退回哈希原样）
  · 磁盘用量 = 实际 stat

产物（data/assets 下，**入库**，不进 LFS —— .gitattributes 只跟踪 img/*）：
  img_index.json  机器可读（含源 URL，脚本用途）
  img_index.md    人读表（可读名 / 磁盘名 / 体积），直接打开 Ctrl+F 即可
"""
from __future__ import annotations

import binascii
import collections
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .logutil import get_logger

log = get_logger()

CANONICAL_EXT = "webp"
_HEX_SEG = re.compile(r"^[0-9A-Fa-f]+$")
# Windows / URL 双重限制：文件名非法字符 + 控制字符
_BAD = re.compile(r'[\\/:*?"<>|\x00-\x1f\x7f]')
# 源文件名自带的扩展名（它可能连 '.' 一起被编进十六进制，解出来要再剥一层）
_SRC_EXT = re.compile(r"\.(pngv2|png|jpe?g|gif|webp)$", re.I)
MAX_STEM = 90

INDEX_JSON = "img_index.json"
INDEX_MD = "img_index.md"

# GitHub **仓库文件页**（blob）：点开是 GitHub 的图片预览界面 ✓ —— 这是对照表里要用的地址。
#
# 顺带记一笔三个端点的差别（2026-10-20 实测，别再试错）：
#   github.com/<…>/blob/<branch>/…            200 + text/html，GitHub 渲染出图片预览页 ✓ 用它
#   raw.githubusercontent.com/<…>/…           对 LFS 文件只返回**指针文本**
#                                             （version https://git-lfs.github.com/spec/v1
#                                               + oid/size），不是图 ✗
#   media.githubusercontent.com/media/<…>/…   200 + image/webp，直接是二进制 ✓
#                                             —— 需要"直接拿到图片字节"时才用它
_BLOB_TMPL = "https://github.com/{owner}/{repo}/blob/{branch}/data/assets/img/"
_REMOTE_RE = re.compile(
    r"(?:https://github\.com/|git@github\.com:)(?P<owner>[\w.\-]+)/(?P<repo>[\w.\-]+?)(?:\.git)?/?$")


def github_base() -> dict[str, str] | None:
    """当前仓库在 GitHub 上的图片 URL 前缀（media / blob 两个端点）。

    从 `git remote` + 当前分支推导，不写死 owner/repo —— 换远端地址也不会失效。
    """
    try:
        import subprocess

        def git(*args: str) -> str:
            out = subprocess.run(["git", *args], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=15)
            return out.stdout.strip()

        remote = git("remote", "get-url", "origin")
        branch = git("rev-parse", "--abbrev-ref", "HEAD")
    except Exception:  # noqa: BLE001  没有 git / 超时都当作拿不到
        return None
    m = _REMOTE_RE.match(remote)
    if not m or not branch:
        return None
    owner, repo = m.group("owner"), m.group("repo")
    return {"blob": _BLOB_TMPL.format(owner=owner, repo=repo, branch=branch)}


def _unhex_seg(seg: str) -> str | None:
    """单段十六进制 → UTF-8 文本；解不出返回 None（宁可保留哈希，也不要乱码名）。"""
    if not seg or len(seg) % 2 or not _HEX_SEG.match(seg):
        return None
    try:
        raw = binascii.unhexlify(seg)
    except (binascii.Error, ValueError):
        return None
    try:
        name = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in name):
        return None
    return name


def readable_name(url: str) -> str:
    """源 URL → 想看的那个名字（不含 `.webp`）。

    `E382A2E382A4..._E58D98E799BA...png` → `アイテム一覧_単発ガチャケット`。
    解不出来时依次退回：URL 里原本可读的 basename → 哈希原名（保证不丢信息）。
    """
    basename = url.split("?")[0].rstrip("/").split("/")[-1]
    stem, dot, _ext = basename.rpartition(".")
    out: list[str] = []
    ok = bool(dot) and bool(stem)
    if ok:
        for seg in stem.split("_"):
            dec = _unhex_seg(seg)
            if dec is None:
                ok = False
                break
            out.append(dec)
    if ok:
        joined = _SRC_EXT.sub("", "_".join(out))
        if joined:
            return joined
    # 退回 basename 原名（help 图那类是形如 63_04.png 的原生可读名）
    raw_stem = basename.rpartition(".")[0]
    if raw_stem and not _BAD.search(raw_stem) and len(raw_stem) <= MAX_STEM:
        return raw_stem
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


_REF_RE = re.compile(r"img/([0-9a-f]{16}\.webp)")


def _scan_pages() -> dict[str, list[str]]:
    """反查每张图被哪些页面引用（数据来自 data/parsed/ja，可重建 → 缺了就跳过这列）。

    为什么要这列：有一批源站在大图就叫 `01_02`、`63_04` 这类编号，光看名字仍然不知道
    是什么；知道它出现在哪一页就能立刻定位（例：`01_02` 出现在「インストール」页）。
    """
    ja_dir = config.PARSED_JA_DIR
    if not ja_dir.exists():
        return {}
    try:
        from .registry import load_registry
        name_by_slug = {e["slug"]: e["name"] for e in load_registry()}
    except Exception:  # noqa: BLE001
        name_by_slug = {}

    refs: dict[str, set[str]] = collections.defaultdict(set)
    for p in ja_dir.glob("*.html"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits = _REF_RE.findall(text)
        if not hits:
            continue
        label = name_by_slug.get(p.stem, p.stem)
        for fname in hits:
            refs[fname].add(label)

    # 角色头像走的是另一条链（characters/*.json 的 icon 字段），正文 ja 里未必出现，
    # 不补这一段的话 `img_閃忍アキラ_icon` 这类图会是「无所在页」，最难认的那批恰恰没定位。
    char_dir = config.PARSED_CHAR_DIR
    if char_dir.exists():
        for cp in char_dir.glob("*.json"):
            try:
                data = json.loads(cp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            icon = (data or {}).get("icon") or ""
            m = _REF_RE.search(icon if isinstance(icon, str) else "")
            if m:
                refs[m.group(1)].add(data.get("name") or cp.stem)
    return {k: sorted(v) for k, v in refs.items()}


def build_index() -> dict:
    """返回索引 dict；同时把两个产物写到 data/assets/。"""
    assets_dir = config.DATA_DIR / "assets"
    img_dir = config.ASSETS_IMG_DIR
    pending_path = config.DATA_DIR / "pending_assets.json"

    pending: dict[str, str] = {}
    if pending_path.exists():
        pending = json.loads(pending_path.read_text(encoding="utf-8"))

    # 磁盘实况（含没进 pending 的孤儿图）
    on_disk: dict[str, int] = {}
    if img_dir.exists():
        for p in img_dir.iterdir():
            if p.is_file():
                on_disk[p.name] = p.stat().st_size

    gh = github_base()
    prefix = (gh or {}).get("blob", "")
    page_refs = _scan_pages()
    entries: list[dict] = []
    for url, local in pending.items():
        stem = readable_name(url)
        pages = page_refs.get(local, [])
        entries.append({
            "file": local,
            "name": stem,
            "url": url,
            "bytes": on_disk.get(local),
            "exists": local in on_disk,
            "pages": pages,
            # GitHub 仓库文件页：点开就是 GitHub 渲染好的图片预览
            "preview_url": (prefix + local) if prefix else None,
        })

    known_files = {e["file"] for e in entries}
    orphans = [
        {"file": name, "name": None, "url": None, "bytes": size, "exists": True}
        for name, size in sorted(on_disk.items())
        if name not in known_files
    ]

    entries.sort(key=lambda e: (e["name"] or "", e["file"]))
    total_bytes = sum(size for size in on_disk.values())

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": ("磁盘文件名是 sha256(源URL)[:16].webp，改动它有 404 风险，故不改名，"
                 "只用本表对照。本表自动生成（`cli assets --index-only`），勿手工编辑。"),
        "counts": {
            "pending": len(pending),
            "on_disk": len(on_disk),
            "mapped": len(entries),
            "orphan": len(orphans),
            "total_bytes": total_bytes,
            "with_page_refs": sum(1 for e in entries if e["pages"]),
        },
        "entries": entries,
        # 磁盘有、pending 无：多数是早期命名体系的遗留，**零引用**（见 tools/_dev/_img_refs_probe.py），
        # 不进对照表也无所谓；列出来是为了哪天想清理时有依据。
        "orphans": orphans,
    }

    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / INDEX_JSON).write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")

    (assets_dir / INDEX_MD).write_text(_to_markdown(index), encoding="utf-8")
    log.info("图片对照表已更新：%s / %s（%d 条对照，%d 张孤儿）",
             INDEX_JSON, INDEX_MD, len(entries), len(orphans))
    return index


def _human(size: int | None) -> str:
    if size is None:
        return "-"
    return f"{size / 1024:.0f} KB" if size < 1024 * 1024 else f"{size / 1048576:.1f} MB"


def _to_markdown(index: dict) -> str:
    c = index["counts"]
    lines = [
        "# 图片对照表（自动生成，勿手工编辑）",
        "",
        f"生成时间：{index['generated_at']}　|　磁盘 {c['on_disk']} 张 / "
        f"{c['total_bytes'] / 1048576:.0f} MB　|　对照 {c['mapped']} 条"
        f"（其中 {c['with_page_refs']} 条标出了所在页）　|　孤儿 {c['orphan']} 张",
        "",
        index["note"],
        "",
        "**用法**：Ctrl+F 搜日文原图名（如 `単発ガチャケット`），同行第 2 列就是它的磁盘文件名，"
        "**点那个链接直接在 GitHub 文件页里预览这张图**"
        "（地址就是在仓库里点开这个文件那个页面）。"
        "名字是 `01_02` 这类编号的，看最后一列「所在页」定位。",
        "",
        "⚠️ **别照着这张表去改文件名**：文件名 `sha256(源URL)[:16]` 被 12284 处引用"
        "（i18n 模板 / 角色 JSON / registry），直接改名会让全站图片 404。改名的正确姿势见 TECHNICAL.md §14.4。",
        "",
        "| 可读名（源站原名） | 磁盘文件名 | 体积 | 所在页 |",
        "|---|---|---|---|",
    ]
    for e in index["entries"]:
        pages = e.get("pages") or []
        shown = "、".join(pages[:2])
        if len(pages) > 2:
            shown += f" 等 {len(pages)} 页"
        gh_url = e.get("preview_url")
        file_cell = f"[{e['file']}]({gh_url})" if gh_url else f"`{e['file']}`"
        lines.append(f"| {e['name']} | {file_cell} | {_human(e['bytes'])} | {shown or '-'} |")

    if index["orphans"]:
        lines += [
            "",
            "## 孤儿图（pending 里没有来源 URL，通常零引用）",
            "",
            "| 磁盘文件名 | 体积 |",
            "|---|---|",
        ]
        for o in index["orphans"]:
            lines.append(f"| `{o['file']}` | {_human(o['bytes'])} |")

    lines += [
        "",
        "## 重新生成",
        "",
        "```bash",
        "python -m escah_pipeline.cli assets --index-only",
        "```",
        "",
        "（每次 `cli assets` 下载完也会自动刷新这张表）",
        "",
    ]
    return "\n".join(lines)
