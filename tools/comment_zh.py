"""将已翻译的主页面评论译文应用到 zh 片段。

处理全部非 bedroom-scenes 页面（含角色页 characters/）的评论译文应用；
bedroom-scenes 属内容审核红线，保持日文原文不翻译。
按 data-comment-id 定位每条评论，替换其正文为 comment_zh.json 中的中文，保留 [发送ID]、
时间与嵌套回复。幂等：已应用则结果不变。

必须在 zh_patch 生成 zh 片段之后、sync-site 之前运行。
用法：python tools/comment_zh.py
"""
from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString
import yaml

ROOT = Path(__file__).resolve().parent.parent
PARSED_JA = ROOT / "data" / "parsed" / "ja"
PARSED_ZH = ROOT / "data" / "parsed" / "zh"
REGISTRY = ROOT / "data" / "registry" / "pages.yaml"
MAP = ROOT / "data" / "parsed" / "comment_zh.json"

# 受保护 / 不可翻译页：保持日文原文，直接从 ja 片段镜像到 zh（含评论），绝不注入中文译文。
_MIRROR_JA_TO_ZH = ("bedroom-scenes",)
# 受保护但已有中文真译文的页（如 daily-quest）：不可被 zh_patch 重生成（否则覆盖真译文），
# 但其 zh 片段的评论区为空，需从 ja 取评论块填入并应用中文译文（仅评论，不碰正文）。
_PROTECTED_MERGE = ("daily-quest",)

# 评论末尾的“ -- [发送ID]”标记（ID 可能与正文在同一文本节点，需只截取此部分）
# 评论末尾的发送 ID，格式如 " -- [/vx8jsxqZ4A]" 或 "名前[ID]"（名前直接接在括号前、无空格），
# 内容可能含任意非空白字符；取文本节点末尾最后的 [..] 即为发送 ID。
_ID_RE = re.compile(r"(?:--\s*)?\[[^\]]+\]\s*$")


def apply_zh_to_li(li, zh: str) -> bool:
    """把 li.pcmt 的正文替换为 zh，保留 [ID]、时间与嵌套回复。返回是否修改。"""
    date_span = li.find("span", class_="comment_date")
    children = list(li.children)
    # 嵌套回复 ul（list2/list3…）原样保留
    nested_uls = [c for c in children if getattr(c, "name", None) == "ul"]
    # [ID] 标记：date_span 之前最后一个含 '[' 的文本节点，仅截取末尾的“ -- [ID]”部分
    # （注意：该节点往往同时含正文，必须只取 ID 段，否则会把日文正文塞回）。
    id_text = None
    if date_span is not None and date_span in children:
        d_idx = children.index(date_span)
        for node in reversed(children[:d_idx]):
            if isinstance(node, NavigableString) and "[" in node:
                m = _ID_RE.search(str(node))
                if m:
                    id_text = m.group(0).strip()
                break
    li.clear()
    li.append(zh)
    if id_text is not None:
        li.append(" ")
        li.append(id_text)
    for ul in nested_uls:
        li.append(ul)
    if date_span is not None:
        li.append(date_span)
    return True


def main() -> int:
    if not MAP.exists():
        print("comment_zh.json 不存在（评论中文映射需人工提供）")
        return 1
    cmap: dict[str, dict[str, str]] = json.loads(MAP.read_text(encoding="utf-8"))
    reg = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))

    total = 0
    for entry in reg.get("pages", []):
        slug = entry.get("slug", "")
        if slug in _MIRROR_JA_TO_ZH:
            continue  # 受保护/不可翻译页：保持日文，下方单独从 ja 镜像
        if slug in _PROTECTED_MERGE:
            continue  # 受保护真译文页：评论块从 ja 填入并译，下方单独处理
        page_map = cmap.get(slug)
        if not page_map:
            continue
        path = PARSED_ZH / (slug + ".html")
        if not path.exists():
            continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
        changed = 0
        for li in soup.find_all("li", class_="pcmt"):
            cid = li.get("data-comment-id")
            zh = page_map.get(cid) if cid else None
            # 仅注入真正的 str 译文；int 0 / list 等无效值（多为未译出的原文）跳过，
            # 评论区保持 zh_patch 生成的日文原文，绝不注入非字符串导致 bs4 崩溃。
            if isinstance(zh, str) and zh:
                apply_zh_to_li(li, zh)
                changed += 1
        if changed:
            path.write_text(str(soup), encoding="utf-8")
            total += changed
            print(f"  {slug}: 应用 {changed} 条")
    print(f"主页面评论译文应用完成，共 {total} 条")

    # 受保护 / 不可翻译页（如 bedroom-scenes 含成人内容，内容审核红线）：
    # 直接用 ja 片段（含日文评论原文）覆盖 zh，确保评论（含 [发送ID] 与时间）随镜像上线，
    # 且绝不被注入中文译文。zh_patch 因 PROTECTED 跳过这些页，故在此补镜像。
    for slug in _MIRROR_JA_TO_ZH:
        ja_path = PARSED_JA / (slug + ".html")
        if not ja_path.exists():
            continue
        zh_path = PARSED_ZH / (slug + ".html")
        zh_path.parent.mkdir(parents=True, exist_ok=True)
        zh_path.write_text(ja_path.read_text(encoding="utf-8"), encoding="utf-8")
        n = len(BeautifulSoup(zh_path.read_text(encoding="utf-8"), "lxml").find_all("li", class_="pcmt"))
        print(f"  {slug}: 镜像 ja→zh（日文原文，评论 {n} 条，未翻译）")

    # 受保护但已有中文真译文的页（如 daily-quest）：其 zh 片段的评论区为空（zh_patch 因
    # PROTECTED 跳过重生成），需从 ja 取评论块填入 zh 的 pcomment 区并应用中文译文，
    # 仅处理评论，绝不覆盖正文真译文。
    for slug in _PROTECTED_MERGE:
        page_map = cmap.get(slug)
        if not page_map:
            continue
        m = merge_protected_comments(slug, page_map)
        if m:
            print(f"  {slug}: 受保护页评论注入 {m} 条（ja 块 + 中文译文）")
    return 0


# 受保护页评论块中仍残留的「嵌入式日文回复」（无独立 data-comment-id，cid 注入无法覆盖）：
# 这些多为简短致谢回复，按已知译文直接替换（按片段，兼容 <br> 拆分），重跑本脚本持续生效。
_PROTECTED_PHRASE_FIX = {
    "ありがとうございます": "谢谢，",
    "参考にさせていただきます": "我会作为参考。",
    "この動画ありがたいですね。皆が欲しいタイミングで先に検証してくれてるのは有能だわ":
        "这个视频真是帮大忙了。在大家都想要的时候提前帮忙验证，真是太靠谱了。",
}


def merge_protected_comments(slug: str, page_map: dict[str, str]) -> int:
    """受保护真译文页的评论注入：从 ja 片段取评论块填入 zh 的空 pcomment 区，按 cid 应用中文。

    不动 zh 正文（避免覆盖真译文）；仅克隆 ja 评论 ul、应用译文、保留 [发送ID] 与时间。
    """
    ja_path = PARSED_JA / (slug + ".html")
    zh_path = PARSED_ZH / (slug + ".html")
    if not (ja_path.exists() and zh_path.exists()):
        return 0
    ja = BeautifulSoup(ja_path.read_text(encoding="utf-8"), "lxml")
    zh = BeautifulSoup(zh_path.read_text(encoding="utf-8"), "lxml")
    ja_pc = ja.find("div", class_="pcomment")
    zh_pc = zh.find("div", class_="pcomment")
    if ja_pc is None or zh_pc is None:
        return 0
    # 用 ja 评论块（已清理过表单/死链）替换 zh 的空 pcomment 内容
    zh_pc.clear()
    for child in list(ja_pc.children):
        zh_pc.append(deepcopy(child))
    changed = 0
    for li in zh_pc.find_all("li", class_="pcmt"):
        cid = li.get("data-comment-id")
        zh_text = page_map.get(cid) if cid else None
        if isinstance(zh_text, str) and zh_text:
            apply_zh_to_li(li, zh_text)
            changed += 1
    # 兜底：嵌入式日文回复（无独立 cid）按已知译文片段替换
    pc_html = zh_pc.decode_contents()
    for jp, cn in _PROTECTED_PHRASE_FIX.items():
        if jp in pc_html:
            pc_html = pc_html.replace(jp, cn)
            changed += 1
    zh_pc.clear()
    zh_pc.append(BeautifulSoup(pc_html, "lxml"))
    zh_path.write_text(str(zh), encoding="utf-8")
    return changed


if __name__ == "__main__":
    sys.exit(main())
