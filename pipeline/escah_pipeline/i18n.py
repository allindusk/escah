"""key 化 i18n 引擎（2026-07-27 重构，取代 zh_patch/char_zh 正则替换）。

产物（data/parsed/i18n/）：
- <slug>.template.html : 净化+路由改写后的 HTML 模板，文本节点替换为 {{keyN}} 占位，
                         标签/链接/图片/表格结构原样保留；行内句子块带 data-i18n-blk 标记。
- <slug>.json          : 每页双语字典：
                         { "keyN": {"ja": "原文", "zh": "译文或空"},
                           "_blocks": { "blkN": {"keys": [...], "ja": 整句纯文本, "zh": ""} } }
                         key 为单纯序列递增（文档顺序），与模板同一次遍历产出。

两级粒度（渲染规则）：
- 文本节点级 keyN：结构（链接/加粗/图片）完整保留，逐节点查表替换。
- 行内句子块 blkN（块内全是行内标签且含 ≥2 个日文文本节点）：当块内任一 keyN 缺译
  而整句译文存在时，整块回退为 zh 纯文本（复用旧系统的整句译文，覆盖率不打折）；
  块内 keyN 全部有译时优先节点级（保留行内结构）。

命令（cli.py 的 i18n 子命令）：
- build   : parsed/ja/<slug>.html → 模板 + 双语 JSON（重跑按归一化 ja 文本回贴已有 zh）
- migrate : 按页配对旧 chunks.json 的 [N] 原文与 tools/_translated_texts/<slug>.txt
            的 [N] 译文，回填 zh（一次性存量迁移；禁止旧全局 _manual_zh.json）
- extract : 生成 tools/_todo_translate/new_translation_<YYYYMMDD>.txt（译者手持的待译清单，
            new_translation_ 表意「新增翻译」+ 紧凑 8 位日期，无中文、无连字符）。
            文件开头为翻译指令（用户给定提示词原样）；页面用不可翻译的字母标记
            「===A===」「===B===」… 分隔（A/B/C 纯 ASCII，不进翻译）；页面↔标记映射
            记在 ASCII 元数据行「# MAP A=<slug> …」。条目为「[N] 日文」（N 本页从 1 递增）；
            已译（JSON 有 zh）不出现，已列入的页面不重复追加。同时同目录生成空白
            new_translation_<YYYYMMDD>_translated.txt 供翻译模型产出译文。
- fill    : 从 new_translation_<YYYYMMDD>_translated.txt 取「[N] 中文」按页回填 i18n JSON
            （页面映射取自待译清单的 # MAP 行，[N] 序号与 extract 同源对齐）；
            旧版 _translated_texts/<slug>.txt 的纯数字 [N] 仍走 migrate 配对。
            取成功后把 new_translation_<YYYYMMDD>_translated.txt 移到 tools/_translated_texts/，
            并把待翻译文件 new_translation_<YYYYMMDD>.txt 移到 tools/_texts_for_translation/（保留原文+映射作审计留痕）。
            ⚠️ 译者把译文放进 new_translation_<YYYYMMDD>_translated.txt（沿用 ===X=== 分段与 [N] 序号），然后 fill。

渲染：render_locale(slug, locale) → 最终 HTML（查表替换，zh 缺失回退 ja，零正则扫描）。
"""
from __future__ import annotations

import html as _html
import json
import re
import unicodedata
import yaml
from pathlib import Path

from lxml import html as lxml_html

from . import config
from .logutil import get_logger

log = get_logger()

I18N_DIR = config.DATA_DIR / "parsed" / "i18n"
TOOLS_DIR = config.ROOT / "tools"
TRANSLATED_DIR = TOOLS_DIR / "_translated_texts"
TODO_DIR = TOOLS_DIR / "_todo_translate"
TEXTS_FOR_TRANS_DIR = TOOLS_DIR / "_texts_for_translation"

# 与 parser_puki 一致的日文判定
_JA_RE = re.compile(r"[ぁ-んァ-ヶ一-龯々〆ヵヶ]")
# 假名判定：译文与原文同形时，无假名（中日同形词如 物理/魔法）视为有效翻译
_KANA_RE = re.compile(r"[ぁ-んァ-ヶ]")
# 模板占位符
_KEY_RE = re.compile(r"\{\{key(\d+)\}\}")
# 待译/译文 txt 的 [N] / [keyN] / [blkN] 行（条目可跨行，直到下一个标记）
_ENTRY_RE = re.compile(r"^\[(key\d+|blk\d+|\d+)\]\s?", re.M)
# 这些标签内部不做 key 化（保持原样）
_SKIP_TAGS = {"script", "style", "pre", "code"}
# 行内标签集合（判定「句子块」用）
_INLINE_TAGS = {
    "a", "abbr", "b", "bdi", "bdo", "br", "cite", "data", "dfn",
    "em", "font", "i", "img", "ins", "kbd", "mark", "q", "rp", "rt", "ruby",
    "s", "samp", "small", "span", "strong", "sub", "sup", "time", "u",
    "var", "wbr", "del",
}
_BLK_ATTR = "data-i18n-blk"

# ---------------- 评论区（div.pcomment）专用规则 ----------------
# 评论日期 span（发送日期/时间元数据）：不进待译，照搬原文，仅星期按固定词表替换。
_DATE_SPAN_CLASS = "comment_date"
# 星期词表（沿用既有译文惯例：(月) → (周一)）
_WEEKDAY_JA2ZH = {"月": "周一", "火": "周二", "水": "周三", "木": "周四",
                  "金": "周五", "土": "周六", "日": "周日"}
_WEEKDAY_RE = re.compile(r"([（(])([月火水木金土日])([)）])")
# 评论正文末尾的发送 ID 签名「 -- [xxxx] 」：不进翻译，模板保留字面量
_SIG_TAIL_RE = re.compile(r"(\s*(?:--|――|——|—)\s*\[[^\[\]]{1,48}\]\s*)$")
# 旧版块条目尾巴「正文 -- [ID] 日期 (曜日) 时刻」：重建时剥尾入记忆，保住既有译文
_OLD_TAIL_JA_RE = re.compile(
    r"\s*--\s*\[[^\[\]]{1,48}\]\s*\d{4}-\d{2}-\d{2}\s*[（(][月火水木金土日][)）]\s*\d{1,2}:\d{2}(?::\d{2})?\s*$")
_OLD_TAIL_ZH_RE = re.compile(
    r"\s*(?:--|――|——|—)\s*\[[^\[\]]{1,48}\]\s*\d{4}-\d{2}-\d{2}\s*[（(][^（()）]{1,4}[)）]\s*\d{1,2}:\d{2}(?::\d{2})?\s*$")


def _date_span_zh(ja: str) -> str:
    """日期文本的 zh：原样照搬，仅 (曜日) 按词表换成 (周X)。"""
    return _WEEKDAY_RE.sub(
        lambda m: m.group(1) + _WEEKDAY_JA2ZH[m.group(2)] + m.group(3), ja)


def _is_date_span(el) -> bool:
    return (isinstance(el.tag, str) and el.tag.lower() == "span"
            and _DATE_SPAN_CLASS in (el.get("class") or ""))


def _norm(t: str) -> str:
    """匹配用归一化：NFC + 折叠空白 + 去 PukiWiki 标题尾部 †。"""
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFC", t or "")).strip()
    return re.sub(r"\s*†\s*$", "", t)


def _norm_ns(t: str) -> str:
    """强归一化：在 _norm 基础上去掉全部空白。

    旧 chunks 文本来自 get_text(\" \")（行内标签边界被插空格），
    新模板块文本来自 text_content()（无插空格），日文本身无空格语义，
    因此按「去全部空白」匹配是安全的二级索引。"""
    return re.sub(r"\s+", "", _norm(t))


# ------------------------------------------------- 专有名词（名字）最高优先级替换 ----
# 词表来源：glossary/names.yaml（JA→ZH，由 tools/_todo_translate/name_glossary_20260727.txt
# (+ 同名 _translated.txt) 配对生成）。渲染 zh 时按本表对专有名词做最高优先级替换，
# 覆盖 LLM/机翻的不一致译名；适用于当前与未来所有页面（随 build/渲染自动生效，重建不丢失）。
#
# 三级策略（仅 zh 生效）：
#   1) 独立名词：节点 ja 归一化后恰好等于某名字 → 直接用词表 ZH 覆盖（无视已有 zh）。
#   2) 嵌入式/残留日文：zh 文本中仍含日文名字（LLM 漏译）→ JA→ZH 子串替换。
#   3) 错译名：LLM 把名字翻成了别的汉字（如 艾丝卡蕾雅 vs 艾斯卡蕾雅）→ 从全站 i18n
#      学习「LLM 渲染形 W → 词表 ZH」的纠错映射（W→Z）后整站替换。
_NAME_GLOSSARY_FILE = config.ROOT / "glossary" / "names.yaml"
_SKILL_GLOSSARY_FILE = config.ROOT / "glossary" / "skills.yaml"
_NAME_RE: "re.Pattern | None" = None
_NAME_MAP: "dict[str, str] | None" = None
_GLOSSARY_NORM: "dict[str, str] | None" = None
_SKILL_NORM: "dict[str, str] | None" = None
_CORR_RE: "re.Pattern | None" = None
_CORR_MAP: "dict[str, str] | None" = None
_LEARNED = False

# 角色浮窗单元格翻译（chara.py 注入 zh 字段用）：UI 标签 + 常用游戏术语值
_TERMS_FILE = config.ROOT / "glossary" / "terms.yaml"
_CHAR_LABEL_NORM: "dict[str, str] | None" = None
_CHAR_VALUE_NORM: "dict[str, str] | None" = None


def _load_name_glossary() -> None:
    global _NAME_RE, _NAME_MAP, _GLOSSARY_NORM
    if _NAME_MAP is not None:
        return
    data: dict = {}
    if _NAME_GLOSSARY_FILE.exists():
        try:
            loaded = yaml.safe_load(_NAME_GLOSSARY_FILE.read_text(encoding="utf-8")) or {}
            data = loaded.get("names", {}) or {}
        except Exception as e:  # 词表损坏不应阻断渲染
            log.warning("[i18n names] 加载 glossary/names.yaml 失败：%s", e)
    # 仅保留「真有替换」的条目（ja==zh 视为无需替换，跳过）
    pairs = [(k, v) for k, v in data.items() if k and v and k != v]
    pairs.sort(key=lambda kv: len(kv[0]), reverse=True)  # 长词优先
    _NAME_MAP = {k: v for k, v in pairs}
    _NAME_RE = re.compile("|".join(re.escape(k) for k, _ in pairs)) if pairs else None
    _GLOSSARY_NORM = {_norm(k): v for k, v in pairs}


def _load_skill_glossary() -> None:
    """必殺技/固有効果 精翻词表（glossary/skills.yaml，JA→ZH，归一化 ja 精确匹配）。"""
    global _SKILL_NORM
    if _SKILL_NORM is not None:
        return
    data: dict = {}
    if _SKILL_GLOSSARY_FILE.exists():
        try:
            loaded = yaml.safe_load(_SKILL_GLOSSARY_FILE.read_text(encoding="utf-8")) or {}
            data = loaded.get("skills", {}) or {}
        except Exception as e:  # 词表损坏不应阻断渲染
            log.warning("[i18n skills] 加载 glossary/skills.yaml 失败：%s", e)
    # 仅保留「真有替换」的条目（ja==zh 视为无需替换，跳过）
    _SKILL_NORM = {
        _norm(k): v for k, v in data.items() if k and v and k != v
    }


def _learn_corrections() -> None:
    """从全站 i18n 学习「LLM 渲染形 W → 词表 ZH」纠错映射（处理错译名）。"""
    global _CORR_RE, _CORR_MAP, _LEARNED
    if _LEARNED:
        return
    _LEARNED = True
    _load_name_glossary()
    if not _GLOSSARY_NORM:
        return
    from collections import Counter, defaultdict
    wc: "dict[str, Counter]" = defaultdict(Counter)
    if I18N_DIR.exists():
        for p in I18N_DIR.glob("*.json"):
            try:
                e = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            for sec in (e.get("_keys") or {}, e.get("_blocks") or {}):
                for v in sec.values():
                    if not isinstance(v, dict):
                        continue
                    ja = _norm(v.get("ja", ""))
                    zh = v.get("zh")
                    if ja in _GLOSSARY_NORM and zh and zh != _GLOSSARY_NORM[ja]:
                        wc[ja][zh] += 1
    corr: "dict[str, str]" = {}
    for ja, counter in wc.items():
        z = _GLOSSARY_NORM[ja]
        for w in counter:
            if w != z:
                corr[w] = z
    cp = sorted(corr.items(), key=lambda kv: len(kv[0]), reverse=True)
    _CORR_MAP = {w: z for w, z in cp}
    _CORR_RE = re.compile("|".join(re.escape(w) for w, _ in cp)) if cp else None


def _correct_text(text: str) -> str:
    """专有名词最高优先级替换（zh 文本）：先 JA→ZH（漏译），再 W→ZH（错译）。"""
    if not text:
        return text
    _load_name_glossary()
    _learn_corrections()
    if _NAME_RE is not None:
        text = _NAME_RE.sub(lambda m: _NAME_MAP[m.group(0)], text)  # type: ignore[union-attr]
    if _CORR_RE is not None:
        text = _CORR_RE.sub(lambda m: _CORR_MAP[m.group(0)], text)  # type: ignore[union-attr]
    return text


def _name_override(ja: str) -> "str | None":
    """专有名词/技能精翻最高优先级覆盖：节点 ja 归一化后恰为某词表条目 → 返回词表 ZH。

    依次查 names（专有名词）与 skills（必殺技/固有効果 精翻），任一命中即返回；
    否则 None（退回 LLM/机翻 zh）。仅 zh 渲染调用。"""
    _load_name_glossary()
    _load_skill_glossary()
    if _GLOSSARY_NORM is None and _SKILL_NORM is None:
        return None
    n = _norm(ja)
    if _GLOSSARY_NORM and n in _GLOSSARY_NORM:
        return _GLOSSARY_NORM[n]
    if _SKILL_NORM and n in _SKILL_NORM:
        return _SKILL_NORM[n]
    return None


def name_zh(ja: str) -> "str | None":
    """公开：查 names 专有名词词表返回中文名（无则 None）。供 chara.py 注入角色中文名。"""
    _load_name_glossary()
    if _GLOSSARY_NORM is None:
        return None
    return _GLOSSARY_NORM.get(_norm(ja))


def _load_char_terms() -> None:
    """角色浮窗 UI 标签 / 常用游戏术语值的 zh 词表（glossary/terms.yaml 的
    char_labels / char_values，JA→ZH，归一化 ja 精确匹配）。"""
    global _CHAR_LABEL_NORM, _CHAR_VALUE_NORM
    if _CHAR_LABEL_NORM is not None:
        return
    labels: dict = {}
    values: dict = {}
    if _TERMS_FILE.exists():
        try:
            loaded = yaml.safe_load(_TERMS_FILE.read_text(encoding="utf-8")) or {}
            labels = loaded.get("char_labels", {}) or {}
            values = loaded.get("char_values", {}) or {}
        except Exception as e:  # 词表损坏不应阻断渲染
            log.warning("[i18n char] 加载 glossary/terms.yaml 失败：%s", e)
    # 仅保留「真有替换」的条目（ja==zh 视为无需替换，跳过）
    _CHAR_LABEL_NORM = {_norm(k): v for k, v in labels.items() if k and v and k != v}
    _CHAR_VALUE_NORM = {_norm(k): v for k, v in values.items() if k and v and k != v}


def char_cell_zh(ja: str) -> "str | None":
    """角色浮窗单元格翻译：先专有名词/技能精翻（名字、必殺技/固有効果 名称与效果），
    再 UI 标签（名前/本名/レアリティ…），最后常用游戏术语值（近距離攻撃(物理)…）。
    命中且 zh≠ja 返回中文，否则 None（保留日文）。供 chara.py 注入单元格 zh 字段。"""
    if not ja:
        return None
    ov = _name_override(ja)
    if ov:
        return ov
    _load_char_terms()
    n = _norm(ja)
    if _CHAR_LABEL_NORM and n in _CHAR_LABEL_NORM:
        return _CHAR_LABEL_NORM[n]
    if _CHAR_VALUE_NORM and n in _CHAR_VALUE_NORM:
        return _CHAR_VALUE_NORM[n]
    return None


def _tpl_path(slug: str) -> Path:
    return I18N_DIR / f"{slug}.template.html"


def _json_path(slug: str) -> Path:
    return I18N_DIR / f"{slug}.json"


def has_i18n(slug: str) -> bool:
    return _tpl_path(slug).exists() and _json_path(slug).exists()


def load_entries(slug: str) -> dict:
    p = _json_path(slug)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save_entries(slug: str, entries: dict) -> None:
    p = _json_path(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")


def _keys_of(entries: dict) -> dict:
    return {k: v for k, v in entries.items() if k.startswith("key") and isinstance(v, dict)}


def _blocks_of(entries: dict) -> dict:
    b = entries.get("_blocks")
    return b if isinstance(b, dict) else {}


# ---------------------------------------------------------------- build ----

_RUN_ATTR = "data-i18n-run"  # 预处理阶段的句子块候选标记（build 后即被替换/移除）


def _inline_only(el) -> bool:
    for d in el.iterdescendants():
        if isinstance(d.tag, str) and d.tag.lower() not in _INLINE_TAGS:
            return False
    return True


def _ja_node_count(el) -> int:
    n = 1 if (el.text and _JA_RE.search(el.text)) else 0
    for d in el.iterdescendants():
        if isinstance(d.tag, str) and d.text and _JA_RE.search(d.text):
            n += 1
        if d.tail and _JA_RE.search(d.tail):
            n += 1
    return n


def _wrap_element_runs(el) -> None:
    """把 el 直接内容中的「行内连续段」（inline run）圈成句子块候选。

    run 以非行内子元素（嵌套 ul 回复等）或评论日期 span 为边界切分；
    run 内含 ≥2 个日文文本节点才成块（单节点本身即完整句子，无需成块）。
    - run 覆盖 el 全部内容 → 直接在 el 打 _RUN_ATTR（与旧行为一致，不加包装）。
    - 否则用 <span data-i18n-run> 包住 run 部分 → 修复评论正文（后跟日期
      span/嵌套回复 ul）与任何「行内文本+块级子元素」混排被拆成孤key 的问题。
    """
    def _boundary(c) -> bool:
        return (not isinstance(c.tag, str) or c.tag.lower() not in _INLINE_TAGS
                or _is_date_span(c) or not _inline_only(c))

    runs: list[dict] = []
    cur = {"src": None, "kids": [], "ja": 1 if (el.text and _JA_RE.search(el.text)) else 0}

    def _flush():
        nonlocal cur
        if cur and cur["ja"] >= 2:
            runs.append(cur)
        cur = None

    for child in el:
        if _boundary(child):
            _flush()
            cur = {"src": child, "kids": [],
                   "ja": 1 if (child.tail and _JA_RE.search(child.tail)) else 0}
        else:
            cur["kids"].append(child)
            cur["ja"] += _ja_node_count(child)
            if child.tail and _JA_RE.search(child.tail):
                cur["ja"] += 1
    _flush()
    if not runs:
        return

    n_children = len(list(el))
    for run in runs:
        # 覆盖整个元素内容：等价旧的元素级块，直接打标
        if run["src"] is None and len(run["kids"]) == n_children:
            el.set(_RUN_ATTR, "1")
            continue
        w = el.makeelement("span", {_RUN_ATTR: "1"})
        if run["src"] is None:
            w.text = el.text
            el.text = None
            el.insert(0, w)
        else:
            prev = run["src"]
            w.text = prev.tail
            prev.tail = None
            el.insert(el.index(prev) + 1, w)
        for kid in run["kids"]:
            w.append(kid)  # 连同 tail 一起移入


def _wrap_runs(root) -> None:
    """遍历树对每个非行内元素做 run 圈块（跳过 _SKIP_TAGS 与已圈的 run 内部）。"""
    def process(el):
        if isinstance(el.tag, str) and el.tag.lower() in _SKIP_TAGS:
            return
        if (el is not root and isinstance(el.tag, str)
                and el.tag.lower() not in _INLINE_TAGS):
            _wrap_element_runs(el)
        if el.get(_RUN_ATTR) is not None:
            return  # run 内部全为行内内容，无需再处理
        for child in list(el):
            if isinstance(child.tag, str) and child.get(_RUN_ATTR) is None:
                process(child)
    process(root)


def build_page(slug: str) -> dict | None:
    """parsed/ja/<slug>.html → 模板 + 双语 JSON（净化/路由改写在此一次性完成）。"""
    from .sitegen import _localize_routes, _sanitize_html  # 延迟导入避免环

    src = config.PARSED_JA_DIR / f"{slug}.html"
    if not src.exists():
        return None
    raw = src.read_text(encoding="utf-8")
    sanitized = _sanitize_html(_localize_routes(raw, slug))

    # 页内翻译记忆：norm(ja) -> zh（节点级与块级共用）
    old = load_entries(slug)
    memory: dict[str, str] = {}
    for ent in _keys_of(old).values():
        if ent.get("zh"):
            memory.setdefault(_norm(ent.get("ja", "")), ent["zh"])
    for blk in _blocks_of(old).values():
        if not blk.get("zh"):
            continue
        ja_old, zh_old = blk.get("ja", ""), blk["zh"]
        memory.setdefault(_norm(ja_old), zh_old)
        # 旧块含「 -- [ID] 日期」尾巴：剥尾后再入一份记忆，衔接新的正文-only 块
        ja_strip = _OLD_TAIL_JA_RE.sub("", ja_old)
        if ja_strip != ja_old:
            memory.setdefault(_norm(ja_strip), _OLD_TAIL_ZH_RE.sub("", zh_old))
    ns_memory = {_norm_ns(k): v for k, v in memory.items()}

    def _mem(ja: str) -> str:
        return memory.get(_norm(ja)) or ns_memory.get(_norm_ns(ja), "")

    try:
        frag = lxml_html.fragment_fromstring(sanitized, create_parent="div")
    except Exception:
        frag = lxml_html.fromstring(f"<div>{sanitized}</div>")

    _wrap_runs(frag)  # 行内连续段预圈块（含评论正文，边界=日期 span/嵌套块级元素）

    entries: dict[str, dict] = {}
    blocks: dict[str, dict] = {}
    kseq = bseq = 0

    def _take(text: str, blk: dict | None, in_cmt: bool) -> str | None:
        """文本节点 → key 占位。评论正文末尾「 -- [ID] 」签名保留字面量不进翻译。"""
        nonlocal kseq
        if not text:
            return None
        body, lit_tail = text, ""
        if in_cmt:
            m = _SIG_TAIL_RE.search(text)
            if m:
                body, lit_tail = text[:m.start()], m.group(1)
        if not _JA_RE.search(body):
            if blk is not None:
                blk["parts"].append(body)  # 块内非日文片段也参与整句拼接
            return None
        kseq += 1
        k = f"key{kseq}"
        entries[k] = {"ja": body, "zh": _mem(body)}
        if blk is not None:
            blk["keys"].append(k)
            blk["parts"].append(body)
        return "{{" + k + "}}" + lit_tail

    def _walk(el, blk: dict | None, in_cmt: bool) -> None:
        nonlocal kseq, bseq
        if isinstance(el.tag, str) and el.tag.lower() in _SKIP_TAGS:
            return
        cls = el.get("class") or ""
        if "pcomment" in cls or "pcmt" in cls:
            in_cmt = True
        # 评论日期 span：不进待译，zh 照搬 + 星期词表替换（发送 ID/日期/时间元数据）
        if _is_date_span(el):
            if el.text and _JA_RE.search(el.text):
                kseq += 1
                k = f"key{kseq}"
                entries[k] = {"ja": el.text, "zh": _date_span_zh(el.text)}
                el.text = "{{" + k + "}}"
            return
        if not in_cmt and any(_is_date_span(c) for c in el):
            in_cmt = True  # 兜底：pcomment 之外的评论列表（含日期 span 即评论行）
        cur = blk
        if el.get(_RUN_ATTR) is not None:
            del el.attrib[_RUN_ATTR]
            if blk is None:
                bseq += 1
                bid = f"blk{bseq}"
                cur = {"id": bid, "keys": [], "parts": []}
                el.set(_BLK_ATTR, bid)
        ph = _take(el.text, cur, in_cmt)
        if ph is not None:
            el.text = ph
        for child in el:
            if isinstance(child.tag, str):
                _walk(child, cur, in_cmt)
            ph = _take(child.tail, cur, in_cmt)
            if ph is not None:
                child.tail = ph
        if cur is not None and cur is not blk:
            plain = _norm("".join(cur["parts"]))
            blocks[cur["id"]] = {"keys": cur["keys"], "ja": plain, "zh": _mem(plain)}

    _walk(frag, None, False)

    out = lxml_html.tostring(frag, method="html", encoding="unicode")
    if out.startswith("<div>") and out.rstrip().endswith("</div>"):
        out = out[len("<div>"):-len("</div>")]

    if blocks:
        entries["_blocks"] = blocks
    tpl = _tpl_path(slug)
    # 注：专有名词（名字）最高优先级替换在 render_locale 渲染期统一施加，
    # 不在此处改 JSON，以免破坏 LLM 句级翻译；随 build/渲染对所有页面自动生效。
    tpl.parent.mkdir(parents=True, exist_ok=True)
    tpl.write_text(out, encoding="utf-8")
    _save_entries(slug, entries)

    keys = _keys_of(entries)
    filled = sum(1 for e in keys.values() if e.get("zh"))
    return {"slug": slug, "keys": len(keys), "zh": filled, "blocks": len(blocks)}


def build_all(slugs: list[str] | None = None) -> None:
    from .registry import load_registry

    targets = [e["slug"] for e in load_registry()]
    if slugs:
        wanted = set(slugs)
        targets = [s for s in targets if s in wanted or s.split("/")[-1] in wanted]
    ok = miss = 0
    for i, slug in enumerate(targets, 1):
        r = build_page(slug)
        if r is None:
            miss += 1
        else:
            ok += 1
        if i % 50 == 0 or i == len(targets):
            log.info("[i18n build] %d/%d（成功 %d，无源 %d）", i, len(targets), ok, miss)
    log.info("i18n build 完成：%d 页模板+JSON，%d 页无 ja 源", ok, miss)


# -------------------------------------------------------------- migrate ----

def _parse_numbered(text: str) -> dict[str, str]:
    """解析 `[标记] 内容`（条目可跨行）→ {标记: 内容}。标记=N/keyN/blkN。

    内容中出现的 `#` 注释行（extract 生成的「# 原文：…」参考）会被剔除，
    以免被误当成译文。旧版 [N] 文件无此类注释行，行为不变。
    """
    out: dict[str, str] = {}
    matches = list(_ENTRY_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw = text[m.end():end]
        lines = [ln for ln in raw.split("\n") if not ln.lstrip().startswith("#")]
        out[m.group(1)] = "\n".join(lines).strip()
    return out


def _fill_from_page_map(slug: str, page_map: dict[str, str]) -> dict:
    """按「归一化 ja → zh」词典回填本页节点级与块级 zh（含去空白二级索引）。"""
    ns_map = {_norm_ns(k): v for k, v in page_map.items()}

    def _lookup(ja: str) -> str | None:
        return page_map.get(_norm(ja)) or ns_map.get(_norm_ns(ja))

    entries = load_entries(slug)
    filled = already = 0
    for ent in _keys_of(entries).values():
        if ent.get("zh"):
            already += 1
            continue
        zh = _lookup(ent.get("ja", ""))
        if zh:
            ent["zh"] = zh
            filled += 1
    for blk in _blocks_of(entries).values():
        if blk.get("zh"):
            continue
        zh = _lookup(blk.get("ja", ""))
        if zh:
            blk["zh"] = zh
            filled += 1
    _save_entries(slug, entries)
    empty = _count_untranslated(entries)
    return {"slug": slug, "filled": filled, "already": already,
            "empty": empty, "keys": len(_keys_of(entries))}


def _count_untranslated(entries: dict) -> int:
    """有效待译数：块内 keyN 若可被块级 zh 覆盖则不算缺。"""
    keys = _keys_of(entries)
    blocks = _blocks_of(entries)
    covered: set[str] = set()
    for blk in blocks.values():
        if blk.get("zh"):
            covered.update(blk.get("keys", []))
    n = sum(1 for k, e in keys.items() if not e.get("zh") and k not in covered)
    n += sum(
        1 for blk in blocks.values()
        if not blk.get("zh") and not all(keys.get(k, {}).get("zh") for k in blk.get("keys", []))
    )
    return n


def _read_translated_source(slug: str) -> str | None:
    """读取某页旧译文源文本：优先 <slug>.txt；不存在时合并 `<base>-N.txt` 拆分文件。

    仅匹配 `^<base>-(\\d+)\\.txt$`（纯数字后缀），避免误吞 `raid-formations-*`、
    `raid-recommended-*` 等独立 slug 的拆分文件；拆分文件 [N] 跨文件连续（0 起），
    按数字序拼接后与 chunks translatable 索引对齐。
    """
    exact = TRANSLATED_DIR / f"{slug}.txt"
    if exact.exists():
        return exact.read_text(encoding="utf-8", errors="replace")
    base = slug.rsplit("/", 1)[-1]
    pat = re.compile(rf"^{re.escape(base)}-(\d+)\.txt$")
    parts = sorted(
        (p for p in TRANSLATED_DIR.glob(f"{base}-*.txt") if pat.match(p.name)),
        key=lambda p: int(pat.match(p.name).group(1)),
    )
    if not parts:
        return None
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace") for p in parts
    )


def migrate_page(slug: str) -> dict | None:
    """一次性迁移：旧 chunks.json [N] 原文 × _translated_texts/<slug>.txt（或拆分 <slug>-N.txt）[N] 译文。

    ⚠️ 仅按页配对，禁止旧全局 _manual_zh.json（跨页塌缩 + 错位脏数据）。
    """
    chunks_path = config.PARSED_JA_DIR / f"{slug}.chunks.json"
    if not chunks_path.exists() or not has_i18n(slug):
        return None
    src = _read_translated_source(slug)
    if not src:
        return None
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    translatable = [c for c in chunks if c.get("translate")]
    raw_map = _parse_numbered(src)

    page_map: dict[str, str] = {}
    pairs = 0
    for n, chunk in enumerate(translatable):
        zh = raw_map.get(str(n), "").strip()
        ja = _norm(chunk.get("text", ""))
        zh = re.sub(r"\s*†\s*$", "", zh)
        if not zh or not ja:
            continue
        # 译文与原文同形：含假名 → 视为未译跳过；无假名（中日同形词）→ 有效翻译
        if zh == ja and _KANA_RE.search(ja):
            continue
        # 同页同文重复出现时首译优先（与旧 load_page_override 语义一致）
        page_map.setdefault(ja, zh)
        pairs += 1

    r = _fill_from_page_map(slug, page_map)
    r["pairs"] = pairs
    return r


def migrate_all(slugs: list[str] | None = None) -> None:
    from .registry import load_registry

    targets = [e["slug"] for e in load_registry()]
    if slugs:
        wanted = set(slugs)
        targets = [s for s in targets if s in wanted or s.split("/")[-1] in wanted]
    total_filled = total_empty = pages = 0
    for slug in targets:
        r = migrate_page(slug)
        if r is None:
            continue
        pages += 1
        total_filled += r["filled"]
        total_empty += r["empty"]
        log.info("[migrate] %s：配对 %d，回填 %d，已有 %d，有效待译 %d",
                 r["slug"], r["pairs"], r["filled"], r["already"], r["empty"])
    log.info("迁移完成：%d 页，累计回填 %d，有效待译 %d", pages, total_filled, total_empty)


# -------------------------------------------------------------- extract ----

# 待译清单：译者手持、按日期一份，文件名 new_translation_<YYYYMMDD>.txt
# （new_translation_ 表意「新增翻译」+ 紧凑 8 位日期，无中文、无连字符，不影响执行）
TODO_PREFIX = "new_translation_"
_DATE_RE = re.compile(r"^\d{8}$")                      # YYYYMMDD
_TODO_NAME_RE = re.compile(r"^new_translation_\d{8}$")  # 待译清单文件 stem（不含 _translated 后缀）
_SEP_RE = re.compile(r"^===\s*([A-Za-z]+)\s*===$", re.M)
_ENTRY_LINE_RE = re.compile(r"^\[(\d+)\]\s*(.*)$", re.M)
_MAP_RE = re.compile(r"^# MAP\s+(.*)$", re.M)

# 文件开头固定指令（用户给定提示词原样）。不再附带中文【使用说明】，避免污染翻译。
# 页面用不可翻译的字母标记 ===A===/===B=== 分隔；页面↔标记映射记在 ASCII 行 # MAP（不被翻译）。
_TODO_INSTRUCTION = (
    "你是一名专业的日语翻译简体中文的游戏本地化翻译员，负责游戏《超昂大战》（エスカレーション・ヒロインズ）WIKI 内容翻译。严格遵循：每行格式为 `[N] 日文`，你必须返回 `[N] 中文`，N 与输入完全一致，不得遗漏、合并、重排或增删任何行，翻译的时候需要结合整个文本的上下文翻译。\n"
)


def _label(idx: int) -> str:
    """序号 → 不可翻译的字母标记：0→A, 1→B, …, 25→Z, 26→AA, 27→AB …（纯 ASCII，不进翻译）。"""
    s = ""
    idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def _parse_map(text: str) -> dict[str, str]:
    """解析 `# MAP A=<slug> B=<slug> …` → {label: slug}。ASCII 元数据行，翻译模型不会改动。"""
    m = _MAP_RE.search(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for part in m.group(1).split():
        if "=" in part:
            lbl, slug = part.split("=", 1)
            out[lbl] = slug
    return out


def _today() -> str:
    import datetime
    return datetime.date.today().strftime("%Y%m%d")


def _one_line(ja: str) -> str:
    return (ja or "").replace("\r", "").replace("\n", " ").strip()


def _untranslated_items(slug: str) -> list[dict]:
    """本页有效待译条目（确定性顺序），用于生成/回填待译清单。

    先块级整句（blk，整体未译的整句），后独立节点（key，未被已译块覆盖）。
    返回 [{kind:'block'|'key', id, ja}, ...]，顺序即清单中的 [N] 序号（N=index+1）。
    """
    entries = load_entries(slug)
    keys = _keys_of(entries)
    blocks = _blocks_of(entries)
    covered: set[str] = set()
    items: list[dict] = []
    for bid, blk in blocks.items():
        members = blk.get("keys", [])
        if blk.get("zh") or all(keys.get(k, {}).get("zh") for k in members):
            covered.update(members)
            continue
        items.append({"kind": "block", "id": bid, "ja": blk.get("ja", "")})
        covered.update(members)
    for k, ent in keys.items():
        if ent.get("zh") or k in covered:
            continue
        items.append({"kind": "key", "id": k, "ja": ent.get("ja", "")})
    return items


def _todo_present_slugs(text: str) -> set[str]:
    """已出现在待译清单中的页面 slug 集合（合并时跳过已有页面，避免冲掉译文）。"""
    return set(_parse_map(text).values())


def extract_todo(slugs: list[str] | None = None, date: str | None = None) -> str:
    """生成/追加待译清单 tools/_todo_translate/new_translation_<YYYYMMDD>.txt，并在同目录生成空白 new_translation_<YYYYMMDD>_translated.txt。

    - 文件开头固定为翻译指令（用户给定提示词原样，无中文使用说明）。
    - 页面用不可翻译的字母标记分隔：`===A===` `===B===` …（纯 ASCII，不进翻译）。
      页面↔标记 的映射记在 ASCII 元数据行 `# MAP A=<slug> B=<slug> ...`（不会被翻译）。
    - 条目为老格式「[N] 日文」（N 本页从 1 递增）；已译（JSON 有 zh）不出现；
      已列入的页面不重复追加（合并时只追加尚未列入的页面整段，续接字母标记）。
    - 同时创建空白的 `<日期>_translated.txt`：翻译模型把「[N] 中文」写进该文件
      （沿用同样的 ===X=== 分段与 [N] 序号），fill 从中取译文。
    """
    from .registry import load_registry

    if date is None:
        date = _today()
    if not _DATE_RE.match(date):
        raise ValueError(f"日期格式应为 YYYYMMDD（8 位，如 20260727），收到：{date}")

    reg = load_registry()
    targets = [e["slug"] for e in reg]
    if slugs:
        wanted = set(slugs)
        targets = [s for s in targets if s in wanted or s.split("/")[-1] in wanted]

    todo_path = TODO_DIR / f"{TODO_PREFIX}{date}.txt"
    translated_path = TODO_DIR / f"{TODO_PREFIX}{date}_translated.txt"

    # 既有页面（含标记）映射，用于增量追加时续接字母标记、跳过已有页面
    existing_map: dict[str, str] = {}
    if todo_path.exists():
        existing_map = _parse_map(
            todo_path.read_text(encoding="utf-8", errors="replace"))
    present = set(existing_map.values())
    idx = len(existing_map)  # 续接字母：已用到第 idx 个

    new_sections: list[str] = []
    map_pairs: list[str] = []
    pages = total = 0
    for slug in targets:
        if slug in present or not has_i18n(slug):
            continue
        items = _untranslated_items(slug)
        if not items:
            continue
        label = _label(idx)
        idx += 1
        lines = [f"[{i + 1}] {_one_line(it['ja'])}" for i, it in enumerate(items)]
        new_sections.append(f"\n==={label}===\n" + "\n".join(lines) + "\n")
        map_pairs.append(f"{label}={slug}")
        pages += 1
        total += len(lines)

    TODO_DIR.mkdir(parents=True, exist_ok=True)
    translated_path.touch()  # 空白译文文件（翻译模型产出后由 fill 取用）

    if not new_sections:
        log.info("无新增待译页面（或均已列入）：%s", todo_path)
        return str(todo_path)

    if todo_path.exists():
        cur = todo_path.read_text(encoding="utf-8", errors="replace")
        if cur and not cur.endswith("\n"):
            cur += "\n"
        # 续接 # MAP 行（合并已有映射 + 新页面映射）
        combined = dict(existing_map)
        for p in map_pairs:
            l, s = p.split("=", 1)
            combined[l] = s
        new_map_line = "# MAP " + " ".join(f"{l}={s}" for l, s in combined.items())
        cur = _MAP_RE.sub(lambda m: new_map_line, cur, count=1)
        todo_path.write_text(cur + "".join(new_sections), encoding="utf-8")
    else:
        header = _TODO_INSTRUCTION + "# MAP " + " ".join(map_pairs) + "\n"
        todo_path.write_text(header + "".join(new_sections), encoding="utf-8")
    log.info("待译清单已生成/追加：%s（%d 页 %d 条）", todo_path, pages, total)
    return str(todo_path)


# ----------------------------------------------------------------- fill ----

def _parse_labeled_sections(text: str) -> dict[str, dict[int, list[str]]]:
    """解析 `===X===` 分段 → {label: {N: [行...]}}。

    用 finditer 定位分隔符，避免 re.split 捕获组把标记本身塞进结果。
    文件头的翻译指令与 `# MAP` 行不含 [N] 条目，不会误当译文。
    """
    matches = list(_SEP_RE.finditer(text))
    sections: dict[str, dict[int, list[str]]] = {}
    for i, m in enumerate(matches):
        label = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        nmap: dict[int, list[str]] = {}
        for mm in _ENTRY_LINE_RE.finditer(body):
            nmap.setdefault(int(mm.group(1)), []).append(mm.group(2))
        sections[label] = nmap
    return sections


def fill_todo(filename: str, slugs: list[str] | None = None) -> None:
    """从 new_translation_<YYYYMMDD>_translated.txt 取「[N] 中文」回填各页 i18n JSON；成功后把该文件移到 _translated_texts/。

    - filename 为待译清单（new_translation_<YYYYMMDD>.txt）；译文取自同目录同名 + _translated 的文件
      （里面是翻译模型产出的 ===X=== 分段 + [N] 中文）。
    - 页面↔标记 映射从待译清单的 `# MAP` 行读取（ASCII，不会被翻译）。
    - 每页按 _untranslated_items 顺序对齐 [N]（N=index+1）；同一 N 多行跳过与 ja 相同的行，取最后不同行。
    - 中日同形如仍含假名（=未译）跳过；译文写回 keyN.zh / blkN.zh。
    """
    path = Path(filename)
    if not path.is_absolute():
        path = TODO_DIR / filename
    if not path.exists():
        log.error("待译清单不存在：%s", path)
        return
    todo_text = path.read_text(encoding="utf-8", errors="replace")
    label_to_slug = _parse_map(todo_text)
    if not label_to_slug:
        log.error("待译清单缺少 # MAP 行，无法定位页面：%s", path)
        return

    translated_path = path.with_name(path.stem + "_translated" + path.suffix)
    if not translated_path.exists():
        log.error("译文文件不存在：%s（请先让翻译模型产出该文件）", translated_path)
        return
    sections = _parse_labeled_sections(
        translated_path.read_text(encoding="utf-8", errors="replace"))

    wanted = set(slugs) if slugs else None
    total_filled = 0
    for label, slug in label_to_slug.items():
        if wanted and slug not in wanted and slug.split("/")[-1] not in wanted:
            continue
        if not has_i18n(slug):
            log.warning("跳过（无 i18n 数据）：%s", slug)
            continue
        nmap = sections.get(label)
        if not nmap:
            continue
        items = _untranslated_items(slug)
        entries = load_entries(slug)
        keys = _keys_of(entries)
        blocks = _blocks_of(entries)
        filled = 0
        for i, it in enumerate(items):
            N = i + 1
            raws = nmap.get(N)
            if not raws:
                continue
            ja_norm = _norm(it["ja"])
            cands = [r for r in raws if _norm(r) != ja_norm]
            if not cands:
                continue
            zh = cands[-1].strip()
            if not zh:
                continue
            if zh == ja_norm and _KANA_RE.search(zh):
                continue  # 中日同形如仍含假名 → 视为未译
            target = blocks.get(it["id"]) if it["kind"] == "block" else keys.get(it["id"])
            if not target:
                continue
            target["zh"] = re.sub(r"\s*†\s*$", "", zh)
            filled += 1
        if filled:
            _save_entries(slug, entries)
            total_filled += filled
            log.info("[fill] %s：回填 %d", slug, filled)

    if total_filled:
        log.info("fill 完成：累计回填 %d 条（来源 %s）", total_filled, translated_path.name)
        # 取成功后把译文文件移到 _translated_texts（已消费，移出待译目录）
        dest = TRANSLATED_DIR / translated_path.name
        TRANSLATED_DIR.mkdir(parents=True, exist_ok=True)
        translated_path.replace(dest)
        log.info("译文文件已移至：%s", dest)
        # 待翻译文件（<日期>.txt，含 # MAP 与 ===X=== 原文）同样移出待译目录，
        # 归档到 _texts_for_translation（保留原文 + 页面映射，作审计留痕）
        TEXTS_FOR_TRANS_DIR.mkdir(parents=True, exist_ok=True)
        todo_dest = TEXTS_FOR_TRANS_DIR / path.name
        if path.exists():
            path.replace(todo_dest)
            log.info("待翻译文件已移至：%s", todo_dest)
    else:
        log.info("fill：未回填任何条目（来源 %s）", translated_path.name)


def fill_latest_todo(slugs: list[str] | None = None) -> None:
    """应用 _todo_translate/ 下最新一份 new_translation_<YYYYMMDD>.txt（供一键 translate 调用）。"""
    files = sorted(
        f for f in TODO_DIR.glob(f"{TODO_PREFIX}*.txt")
        if _TODO_NAME_RE.match(f.stem)
    )
    if not files:
        log.info("无待译清单可应用（_todo_translate/ 为空）")
        return
    fill_todo(files[-1].name, slugs)


# ------------------------------------------------------------ char-fill ----

# 值保留日文的表头（人名/声优/画师约定）
_KEEP_JA_HEADERS = {"名前", "CV", "イラスト", "本名"}


def _page_dict(slug: str) -> dict[str, str]:
    """本页 i18n JSON → 强归一化 ja → zh 词典（keys + blocks）。"""
    entries = load_entries(slug)
    d: dict[str, str] = {}
    for ent in _keys_of(entries).values():
        if ent.get("zh"):
            d.setdefault(_norm_ns(ent.get("ja", "")), ent["zh"])
    for blk in _blocks_of(entries).values():
        if blk.get("zh"):
            d.setdefault(_norm_ns(blk.get("ja", "")), blk["zh"])
    return d


def char_fill_all() -> None:
    """角色数据 JSON（data/parsed/characters/*.json，悬浮窗数据源）补 zh。

    取代 char_zh.py：用该角色自己页面的 i18n 词典查表（按页隔离，无跨页塌缩）。
    命中则写/覆盖 zh；未命中保留原有 zh（旧成果不丢）。
    """
    char_dir = config.DATA_DIR / "parsed" / "characters"
    total = hit = 0
    files = sorted(char_dir.glob("*.json"))
    for i, f in enumerate(files, 1):
        data = json.loads(f.read_text(encoding="utf-8"))
        name = data.get("name") or f.stem
        d = _page_dict(f"characters/{name}")
        if not d:
            continue
        changed = False
        for sec in (data.get("sections") or {}).values():
            for row in sec.get("rows", []):
                head = next((c.get("t", "").strip() for c in row if c.get("h")), "")
                for cell in row:
                    t = cell.get("t", "")
                    if not t or not _JA_RE.search(t):
                        continue
                    if not cell.get("h") and head in _KEEP_JA_HEADERS:
                        continue  # 人名/声优/画师值保留日文
                    total += 1
                    zh = d.get(_norm_ns(t))
                    if zh and zh != cell.get("zh"):
                        cell["zh"] = zh
                        cell["tr"] = True
                        changed = True
                        hit += 1
        if changed:
            # 与 chara.py 提取时的缩进保持一致（indent=1），避免每次回填都重排版全量文件
            f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        if i % 100 == 0 or i == len(files):
            log.info("[char-fill] %d/%d", i, len(files))
    log.info("char-fill 完成：%d 文件，命中更新 %d / 候选 %d", len(files), hit, total)


# --------------------------------------------------------------- render ----

def render_locale(slug: str, locale: str) -> str | None:
    """模板 → 最终 HTML。节点级查表替换；zh 局部缺译时块级整句回退。"""
    if not has_i18n(slug):
        return None
    tpl = _tpl_path(slug).read_text(encoding="utf-8")
    entries = load_entries(slug)
    keys = _keys_of(entries)
    blocks = _blocks_of(entries)

    # 块级回退：zh 且块内有缺译且块级译文存在 → 整块换为纯文本 zh
    if _BLK_ATTR in tpl:
        try:
            frag = lxml_html.fragment_fromstring(tpl, create_parent="div")
            for el in frag.xpath(f".//*[@{_BLK_ATTR}]"):
                bid = el.get(_BLK_ATTR)
                el.attrib.pop(_BLK_ATTR, None)
                blk = blocks.get(bid)
                if not blk or locale != "zh" or not blk.get("zh"):
                    continue
                if all(keys.get(k, {}).get("zh") for k in blk.get("keys", [])):
                    continue  # 节点级全有译文 → 保留行内结构
                # 含图片/表格的块：保留结构（避免丢图/丢表），节点级回退 ja
                if any(d.tag in ("img", "table") for d in el.iter()):
                    continue
                for child in list(el):
                    el.remove(child)
                if locale == "zh":
                    ov = _name_override(blk.get("ja", ""))
                    el.text = ov if ov is not None else _correct_text(blk["zh"])
                else:
                    el.text = blk["zh"]
            tpl = lxml_html.tostring(frag, method="html", encoding="unicode")
            if tpl.startswith("<div>") and tpl.rstrip().endswith("</div>"):
                tpl = tpl[len("<div>"):-len("</div>")]
        except Exception:
            log.warning("[i18n render] %s 块级回退失败，退回节点级渲染", slug)

    def _sub(m: re.Match) -> str:
        ent = keys.get(f"key{m.group(1)}")
        if not ent:
            return m.group(0)
        if locale == "zh":
            ov = _name_override(ent.get("ja", ""))
            if ov is not None:
                return _html.escape(ov, quote=False)  # 独立名词直接覆盖（最高优先级）
            text = ent.get("zh") or ent.get("ja", "")
            text = _correct_text(text)  # 漏译/错译纠正
            return _html.escape(text, quote=False)
        return _html.escape(ent.get("ja", ""), quote=False)

    return _KEY_RE.sub(_sub, tpl)


def zh_ratio(slug: str) -> float:
    """本页有效 zh 覆盖率（块级译文覆盖块内 key）。"""
    entries = load_entries(slug)
    keys = _keys_of(entries)
    if not keys:
        return 0.0
    covered: set[str] = set()
    for blk in _blocks_of(entries).values():
        if blk.get("zh"):
            covered.update(blk.get("keys", []))
    done = sum(1 for k, e in keys.items() if e.get("zh") or k in covered)
    return done / len(keys)
