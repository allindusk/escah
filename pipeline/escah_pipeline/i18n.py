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
import posixpath
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
# 站内跨页面跳转链接（非页内锚点）：用于渲染期统一加 target=_blank
_INTLINK_RE = re.compile(r'<a\b[^>]*class="[^"]*internal-link[^"]*"[^>]*href="([^"]*)"[^>]*>')
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

# 例外页：原画索引(artists) / 声优一览(voice-actors) 的带超链接文本块不翻译，
# 直接用日文原文（项目规则，用户 2026-08-04）。这两个页 slug 恒为日文回退，
# 即使日后内容新增也按此处理。
SKIP_LINK_SLUGS = {"artists", "voice-actors"}

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
_SKILL_NS: "dict[str, str] | None" = None  # 去全部空白索引（容错源/线上 JA 空白/换行漂移）
_CORR_RE: "re.Pattern | None" = None
_CORR_MAP: "dict[str, str] | None" = None
_LEARNED = False

# 角色浮窗单元格翻译（chara.py 注入 zh 字段用）：UI 标签 + 常用游戏术语值
_TERMS_FILE = config.ROOT / "glossary" / "terms.yaml"
_CHAR_LABEL_NORM: "dict[str, str] | None" = None
_CHAR_VALUE_NORM: "dict[str, str] | None" = None

# 站点术语全站最高优先级覆盖（glossary/terms.yaml 的 char_sections / char_labels /
# char_values / inline_terms 合并，JA→ZH，归一化 ja 整词精确匹配）。作用于全站
# （详情页/普通页/表格/大小浮窗），zh 渲染时整词精确覆盖，高于 LLM/机翻 zh。
_TERM_NORM: "dict[str, str] | None" = None
# inline_terms 中含假名（必为日语）的条目 → 子串替换，覆盖正文内嵌称呼/术语
# （如「長官さぁん」出现在「もっときて、長官さぁん！！」句中，整词匹配抓不到）。
# 仅 inline_terms 段参与子串；其余段为结构标签，保持整词精确。
_TERM_SUB_RE: "re.Pattern | None" = None
_TERM_SUB_MAP: "dict[str, str] | None" = None

# 中文译文「指定词汇 → 超链接」配置（glossary/link_terms.yaml）。
# 结构：按 slug 分组，每组 links 列表含 {ja, zh, href}；渲染时按 zh 词精确子串包裹 <a>。
# ja / 整句上下文仅作 LLM 理解/审计用，不参与渲染匹配。详见该 yaml 头部注释。
_LINK_TERMS_FILE = config.ROOT / "glossary" / "link_terms.yaml"
_LINK_TERMS: "dict[str, list[dict]] | None" = None  # slug -> [ {zh, href}, ... ]
# 全局 ja 原文 → zh 译文 索引（所有 slug 合并），供 _wrap_block_links 做 O(1) 查找，
# 避免原实现遍历 _LINK_TERMS.values() 全站条目（大页 N块×M链接×全站条目 = 灾难级耗时）。
_LINK_JA_ZH: "dict[str, str] | None" = None
# 按 slug 缓存日文原页解析结果，避免块级回退分支对每个块重复解析 ja 文件（大页性能炸弹）。
_JA_PAIRS_CACHE: "dict[str, list[tuple[str, str]]]" = {}

# 全站高频游戏术语（日→中），render-time 覆盖（glossary/high_freq.yaml）。
# 与 names.yaml 同层，但本节为通用游戏术语（非专有名词）。双层避免污染中文：
#   - 含假名词条 → 子串替换（假名必为日语，安全；覆盖「ダメージ」等句内残留）
#   - 纯汉字词条 → 整词精确匹配（仅在节点 ja 整词命中时替换，绝不子串误改中文）
# 来源：tools/translate_glossary.py build。
_HIGH_FREQ_FILE = config.ROOT / "glossary" / "high_freq.yaml"
_HF_SUB_RE: "re.Pattern | None" = None        # 含假名键：子串替换
_HF_SUB_MAP: "dict[str, str] | None" = None
_HF_EXACT_NORM: "dict[str, str] | None" = None  # 纯汉字键：整词精确（归一化 ja）
_HF_ALL_NORM: "dict[str, str] | None" = None    # 全部键（含假名）：整词精确（供 JA 精确覆盖已翻译 zh）
_HF_PRECISE: "set[str] | None" = None            # _precise 白名单（归一化 ja）：仅这些键参与「纠正已译中文」层
_HF_PRECISE_SUB_RE: "re.Pattern | None" = None    # _precise 中「非纯片假名」条目：对 zh 文本做残留日文形→规范中文 子串替换
_HF_PRECISE_SUB_MAP: "dict[str, str] | None" = None


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
    global _SKILL_NORM, _SKILL_NS
    if _SKILL_NORM is not None:
        return
    data: dict = {}
    if _SKILL_GLOSSARY_FILE.exists():
        try:
            loaded = yaml.safe_load(_SKILL_GLOSSARY_FILE.read_text(encoding="utf-8")) or {}
            data = loaded.get("skills", {}) or {}
        except Exception as e:  # 词表损坏不应阻断渲染
            log.warning("[i18n skills] 加载 glossary/skills.yaml 失败：%s", e)
    pairs = [(k, v) for k, v in data.items() if k and v and k != v]
    # 仅保留「真有替换」的条目（ja==zh 视为无需替换，跳过）
    _SKILL_NORM = {_norm(k): v for k, v in pairs}
    # 去全部空白二级索引：容错源文件 JA 与线上 JA 的空白/换行漂移（日语无空格语义，安全）
    _SKILL_NS = {_norm_ns(k): v for k, v in pairs}


# 读音归一化（手动纠正）：names.yaml 读音调整后，旧读音在「变体短语」（如 真夏のメガエル→盛夏梅加艾尔）
# 中以子串形式残留，无法被「整词精确」纠正层捕获。此处按子串纠正（名字唯一，无上下文误伤风险）。
_READING_CORR = {
    "梅加艾尔": "米加尔",
    "玛雅艾尔": "玛雅尔",
}


def _learn_corrections() -> None:
    """从全站 i18n 学习「LLM 渲染形 W → 词表 ZH」纠错映射（处理错译名）。"""
    global _CORR_RE, _CORR_MAP, _LEARNED
    if _LEARNED:
        return
    _LEARNED = True
    _load_name_glossary()
    _load_high_freq_glossary()
    # 合并 names + high_freq（names 优先，专有名词不被通用术语覆盖），用于 JA 精确匹配学习「错译 ZH → 规范 ZH」
    norm: "dict[str, str]" = {}
    # high_freq：仅 _precise 白名单内的键参与「纠正已译中文」（默认只做渲染期源文替换，安全）。
    if _HF_ALL_NORM and _HF_PRECISE:
        for k, v in _HF_ALL_NORM.items():
            if k in _HF_PRECISE:
                norm[k] = v
    # names：专有名词全量参与纠正（译名无争议，用户规则：固定名字翻译不可变）。
    if _GLOSSARY_NORM:
        norm.update(_GLOSSARY_NORM)
    if not norm:
        return
    corr: "dict[str, str]" = {}
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
                    for old, new in _node_name_corrections(v.get("ja", ""), v.get("zh"), norm):
                        if old != new:
                            corr[old] = new
            # characters.json 等：key 节点存于顶层（键名 keyN，含 ja/zh 字段），需补扫
            for v in e.values():
                if isinstance(v, dict) and "ja" in v and "zh" in v:
                    for old, new in _node_name_corrections(v.get("ja", ""), v.get("zh"), norm):
                        if old != new:
                            corr[old] = new
    # 读音归一化（手动）：把旧读音残留（变体短语中的子串）纠正为新读音。
    for old, new in _READING_CORR.items():
        if old != new:
            corr[old] = new
    cp = sorted(corr.items(), key=lambda kv: len(kv[0]), reverse=True)
    _CORR_MAP = {w: z for w, z in cp}
    _CORR_RE = re.compile("|".join(re.escape(w) for w, _ in cp)) if cp else None


from functools import lru_cache

@lru_cache(maxsize=4096)
def _correct_text(text: str) -> str:
    """专有名词最高优先级替换（zh 文本）：先 JA→ZH（漏译），再 W→ZH（错译）。

    带 lru_cache：同一文本（如重复出现的通用术语/技能名）只做一次大正则扫描，
    避免 skills/characters 等大页逐 key 重复扫描 _NAME_RE/_CORR_RE（数千次 → 数百次）。
    """
    if not text:
        return text
    _load_name_glossary()
    _learn_corrections()
    if _NAME_RE is not None:
        text = _NAME_RE.sub(lambda m: _NAME_MAP[m.group(0)], text)  # type: ignore[union-attr]
    if _CORR_RE is not None:
        text = _CORR_RE.sub(lambda m: _CORR_MAP[m.group(0)], text)  # type: ignore[union-attr]
    # 通用高频游戏术语子串替换（覆盖句内残留日语术语）
    text = _high_freq_override(text)
    # _precise 纯汉字/含平假名条目句中子串纠正（强制统一，覆盖句内残留日文形）
    text = _high_freq_precise_sub(text)
    # inline_terms 含假名条目子串替换（覆盖正文内嵌称呼/术语，如「長官さぁん」）
    text = _term_sub_override(text)
    return text


_NAME_SUFFIX_RE = re.compile(
    r"^(.*?)([（(][^（）()]*[）)]"            # 括号修饰（如 (ユリカ)）
    r"|[　\s]*[RrSsUuNn]+"                    # 稀有度 R/SR/SSR
    r"|[　\s]*※"                              # 注释 ※
    r"|[　][ぁ-んァ-ヶー一-龯]+)$"             # 全角空格+日文描述（如 変身前スキン）
)


def _split_name_suffix(ja: str) -> "tuple[str, str]":
    """拆分 基词 + 尾部修饰。无修饰返回 (ja, '')。

    覆盖：括号 (ユリカ) / 稀有度 R·SR·SSR / 注释 ※ / 全角空格+日文描述（変身前スキン）。
    用途：让「游戏内固定专有名词」即使带后缀也始终落到词表规范译名
    （用户要求：names.yaml 的翻译不可变，前缀后缀都不影响）。"""
    if not ja:
        return ja, ""
    m = _NAME_SUFFIX_RE.match(ja)
    if m and m.group(2):
        return m.group(1), m.group(2)
    return ja, ""


def _node_name_corrections(ja_raw: str, zh: "str | None", norm: "dict[str, str]") -> "list[tuple[str, str]]":
    """为一个 i18n 节点生成「旧 zh → 规范 zh」纠错对（供 _learn_corrections 使用）。

    - 节点 ja 整词命中词表 → 直接纠错；
    - 节点 ja 带尾部修饰且基词命中词表 → 基词规范化，并保留 zh 中的对应后缀
      （括号 → 原样保留括号段；全角空格/稀有度描述 → 保留 zh 尾部空格段）。
    全部 JA 精确门控，不子串误伤。"""
    out: "list[tuple[str, str]]" = []
    if not zh:
        return out
    n = _norm(ja_raw)
    if n in norm and zh != norm[n]:
        # 安全阀：纠错学习只在「源 zh 确为该专有名词的某种渲染变体」时成立。
        # 若 zh 与规范译名完全不共享任何字符（如 LLM 把角色名错译成毫不相干的词），
        # 属明显错译数据，跳过——否则会污染全站所有含该 zh 片段的节点。
        if not (set(zh) & set(norm[n])):
            return out
        out.append((zh, norm[n]))
        return out
    base, suffix = _split_name_suffix(ja_raw)
    if base == ja_raw:
        return out
    nb = _norm(base)
    if nb not in norm:
        return out
    canonical = norm[nb]
    # 安全阀：同上，zh 与规范译名零字符重叠时跳过（防错译数据污染全站）。
    if set(zh or "") & set(canonical):
        if re.search(r"[（(][^（）()]*[）)]$", ja_raw):
            mz = re.search(r"[（(][^（）()]*[）)]$", zh or "")
            out.append((zh, canonical + (mz.group(0) if mz else "")))
        elif suffix.startswith("　") or re.match(r"[　\s]*[RrSsUuNn]+|[　\s]*※", suffix):
            if " " in (zh or ""):
                zb, zs = zh.rsplit(" ", 1)  # type: ignore[union-attr]
                out.append((zh, canonical + " " + zs))
            else:
                out.append((zh, canonical))
        else:
            out.append((zh, canonical))
    return out


@lru_cache(maxsize=4096)
def _name_override(ja: str) -> "str | None":
    """专有名词/技能精翻最高优先级覆盖：节点 ja 归一化后恰为某词表条目 → 返回词表 ZH。

    依次查 names（专有名词）与 skills（必殺技/固有効果 精翻），任一命中即返回；
    否则 None（退回 LLM/机翻 zh）。仅 zh 渲染调用。
    容忍尾部修饰（括号/稀有度/※/全角空格+日文描述）后再匹配基词。"""
    _load_name_glossary()
    _load_skill_glossary()
    if _GLOSSARY_NORM is None and _SKILL_NORM is None:
        return None
    n = _norm(ja)
    if _GLOSSARY_NORM and n in _GLOSSARY_NORM:
        return _GLOSSARY_NORM[n]
    if _SKILL_NORM and n in _SKILL_NORM:
        return _SKILL_NORM[n]
    # 去全部空白二级索引：容错源/线上 JA 空白/换行漂移（技能 JA 无空格语义）
    ns = _norm_ns(ja)
    if _SKILL_NS and ns in _SKILL_NS:
        return _SKILL_NS[ns]
    # 容忍尾部修饰（(ユリカ) / 　R / 　※ / 　変身前スキン）后再匹配基词，
    # 否则「体育祭のクラリス　R」「レガリアの神騎ユリエル(ユリカ)」这类带后缀文本
    # 无法精确匹配 names.yaml，会回退到通用 の→的 转换或保留错译，导致中文名形态
    # 与 charRefs 别名不一致、前端匹配失败、角色浮窗失效。
    base, suffix = _split_name_suffix(ja)
    if base == ja:
        return None
    nb = _norm(base)
    if _GLOSSARY_NORM and nb in _GLOSSARY_NORM:
        return _term_sub_override(_GLOSSARY_NORM[nb] + suffix)
    if _SKILL_NORM and nb in _SKILL_NORM:
        return _term_sub_override(_SKILL_NORM[nb] + suffix)
    nbs = _norm_ns(base)
    if _SKILL_NS and nbs in _SKILL_NS:
        return _term_sub_override(_SKILL_NS[nbs] + suffix)
    return None


def name_zh(ja: str) -> "str | None":
    """公开：查 names 专有名词词表返回中文名（无则 None）。供 chara.py 注入角色中文名。"""
    _load_name_glossary()
    if _GLOSSARY_NORM is None:
        return None
    return _GLOSSARY_NORM.get(_norm(ja))


def _link_display_zh(ja: str) -> str:
    """句末【】链接标签的显示名：优先 glossary 专有名词(names)→技能(skills)→术语(terms)
    →高频词(high_freq)，全部查不到则回退日文原文（理论上所有超链接词都在词表有精准翻译）。
    仅 zh 渲染调用。与渲染期名词覆盖同源，保证【】显示名与正文译名一致。"""
    z = _name_override(ja)
    if z:
        return z
    z = _term_override(ja)
    if z:
        return z
    z = _high_freq_exact(ja) or _high_freq_all(ja)
    if z:
        return z
    return ja


def _normalize_link_href(href: str) -> "tuple[str, str]":
    """链接 href 归一化：站内 'xxx.html' → '/escah/zh/xxx.html'（带 SITE_BASE 前缀，
    新标签页打开）；外链原样。返回 (href, target)。

    注意：必须带 SITE_BASE 前缀（默认 /escah/），否则在 base 部署下站内绝对链接
    （/zh/xxx.html）会解析为 <base 根>/zh/xxx.html → 404。已带 SITE_BASE 的链接
    （如配置里误写成 /escah/zh/...）不再重复加。"""
    if href.startswith("http://") or href.startswith("https://"):
        return href, ""  # 外链：保留原 href，不加 target（由浏览器/用户决定）
    # 已带 SITE_BASE 前缀的站内链接：原样返回（避免重复前缀）
    if href.startswith(config.SITE_BASE):
        return href, ' target="_blank" rel="noopener"'
    if href.startswith("/"):
        # 以 / 开头的站内绝对路径（如 /zh/faq.html）：补 SITE_BASE 前缀
        return config.SITE_BASE.rstrip("/") + href, ' target="_blank" rel="noopener"'
    # 站内跳转：faq.html / raid.html → /escah/zh/faq.html（新标签页打开）
    base = href.split("#", 1)[0].rstrip("/").split("/")[-1]
    if not base:
        return href, ""
    return config.SITE_BASE + "zh/" + base, ' target="_blank" rel="noopener"'


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


def _load_site_terms() -> None:
    """站点术语全站最高优先级覆盖词表：合并 glossary/terms.yaml 的
    char_sections / char_labels / char_values / inline_terms（JA→ZH，
    归一化 ja 整词精确匹配，ja==zh 视为无需替换跳过）。"""
    global _TERM_NORM, _TERM_SUB_RE, _TERM_SUB_MAP
    if _TERM_NORM is not None:
        return
    mapping: dict = {}
    sub_pairs: list = []
    if _TERMS_FILE.exists():
        try:
            loaded = yaml.safe_load(_TERMS_FILE.read_text(encoding="utf-8")) or {}
            for sec in ("char_sections", "char_labels", "char_values", "inline_terms"):
                for k, v in (loaded.get(sec, {}) or {}).items():
                    if k and v and k != v:
                        mapping[_norm(k)] = v
            # inline_terms 含假名条目 → 子串层（长词优先）
            for k, v in (loaded.get("inline_terms", {}) or {}).items():
                if k and v and k != v and _KANA_RE.search(k):
                    sub_pairs.append((k, v))
        except Exception as e:  # 词表损坏不应阻断渲染
            log.warning("[i18n terms] 加载 glossary/terms.yaml 失败：%s", e)
    _TERM_NORM = mapping
    sub_pairs.sort(key=lambda kv: len(kv[0]), reverse=True)  # 长词优先
    _TERM_SUB_MAP = {k: v for k, v in sub_pairs}
    _TERM_SUB_RE = re.compile("|".join(re.escape(k) for k, _ in sub_pairs)) if sub_pairs else None


def _load_link_terms() -> None:
    """中文译文「指定词汇 → 超链接」配置（glossary/link_terms.yaml）。

    按 slug 分组，每组 links 列表含 {ja, zh, href}；渲染时按 zh 词精确子串包裹 <a>。
    结构详见该 yaml 头部注释（含给 LLM 的说明）。失败不阻断渲染。"""
    global _LINK_TERMS, _LINK_JA_ZH
    if _LINK_TERMS is not None:
        return
    _LINK_TERMS = {}
    _LINK_JA_ZH = {}
    if not _LINK_TERMS_FILE.exists():
        return
    try:
        loaded = yaml.safe_load(_LINK_TERMS_FILE.read_text(encoding="utf-8")) or []
        for entry in loaded:
            if not isinstance(entry, dict):
                continue
            slug = entry.get("slug")
            links = entry.get("links") or []
            if not slug or not isinstance(links, list):
                continue
            norm_links: "list[dict]" = []
            for ln in links:
                if not isinstance(ln, dict):
                    continue
                ja = (ln.get("ja") or "").strip()
                zh = (ln.get("zh") or "").strip()
                href = (ln.get("href") or "").strip()
                if not zh or not href:
                    continue
                norm_links.append({"ja": ja, "zh": zh, "href": href})
                if ja:  # 建全局 ja→zh 索引（O(1) 查找用）
                    _LINK_JA_ZH[ja] = zh
            if norm_links:
                _LINK_TERMS.setdefault(slug, []).extend(norm_links)
    except Exception as e:  # 配置损坏不应阻断渲染
        log.warning("[i18n link_terms] 加载 glossary/link_terms.yaml 失败：%s", e)
        _LINK_TERMS = {}
        _LINK_JA_ZH = {}


def _ja_link_pairs_for_slug(slug: str) -> "list[tuple[str, str]]":
    """读取当页日文原页 HTML，返回其中所有正文 <a> 的 (链接文本, href) 列表。

    用于「锚定具体位置」：link_terms 的条目仅当「ja 命中原文某 <a> 文本 **且**
    该 <a> 的 href 与配置 href 一致」时才在中文套链接。这样同时满足：
      - 页面级：只处理本页原文出现的链接；
      - 文本具体位置级：同词在 A 处是链接、B 处是纯文本时，只在 A 处套，
        绝不在 B 处强加（href 双重锚定杜绝跨位置误套）。
    解析失败返回空列表（安全降级：该页不包裹任何 link_terms 链接）。
    结果按 slug 缓存（同 slug 整次 render 只解析一次 ja 文件）。
    """
    if slug in _JA_PAIRS_CACHE:
        return _JA_PAIRS_CACHE[slug]
    from pathlib import Path
    ja_file = Path(__file__).resolve().parent.parent.parent / "data" / "parsed" / "ja" / f"{slug}.html"
    if not ja_file.exists():
        return []
    try:
        # 必须显式 UTF-8 解码，否则日文原页字节被误当 Latin-1 导致匹配失效
        tree = lxml_html.document_fromstring(ja_file.read_text(encoding="utf-8"))
    except Exception:
        return []
    pairs: "list[tuple[str, str]]" = []
    # TOC / 导航 / 页眉页脚容器：其中的 <a> 是页面目录、侧栏导航，并非正文内联链接。
    # 若不过滤，TOC 里的词（如「よくある質問」）会被误判为「原文是链接」，
    # 导致正文标题（h2 里同名纯文本）被强加超链接（gacha.html#content_1_13 同类 bug）。
    # 注意：td/th（表格单元格）内的链接属正文，不可排除。
    _NAV_TAGS = {"nav", "header", "footer", "aside", "menu"}
    for a in tree.iter("a"):
        # 跳过位于导航/TOC 容器内的链接
        p = a.getparent()
        in_nav = False
        while p is not None:
            if p.tag in _NAV_TAGS:
                in_nav = True
                break
            p = p.getparent()
        if in_nav:
            continue
        txt = (a.text_content() or "").strip()
        href = (a.get("href") or "").strip()
        if txt and href:
            pairs.append((txt, href))
    _JA_PAIRS_CACHE[slug] = pairs
    return pairs


def _term_override(ja: str) -> "str | None":
    """站点术语最高优先级覆盖：节点 ja 归一化后恰为某术语 → 返回词表 ZH；否则 None。

    覆盖 char_sections（分段标题）/ char_labels（字段标签）/ char_values（术语值）/
    inline_terms（行内独立术语）。仅 zh 渲染调用。"""
    _load_site_terms()
    if _TERM_NORM is None:
        return None
    return _TERM_NORM.get(_norm(ja))


def _term_sub_override(text: str) -> str:
    """inline_terms 中含假名条目的子串替换（覆盖正文内嵌称呼/术语，如「長官さぁん」）。"""
    if not text:
        return text
    _load_site_terms()
    if _TERM_SUB_RE is not None:
        return _TERM_SUB_RE.sub(lambda m: _TERM_SUB_MAP[m.group(0)], text)  # type: ignore[union-attr]
    return text


def _load_high_freq_glossary() -> None:
    """全站高频游戏术语词表：glossary/high_freq.yaml 的 high_freq（JA→ZH）。

    拆分为两层（见模块常量说明）：
      - 含假名键 → 子串替换（_HF_SUB_RE / _HF_SUB_MAP），长词优先；
      - 纯汉字键 → 整词精确（_HF_EXACT_NORM，归一化 ja 精确匹配）。
    仅保留 ja!=zh 的条目（ja==zh 视为无需替换，跳过）。"""
    global _HF_SUB_RE, _HF_SUB_MAP, _HF_EXACT_NORM, _HF_ALL_NORM, _HF_PRECISE, _HF_PRECISE_SUB_RE, _HF_PRECISE_SUB_MAP
    if _HF_SUB_MAP is not None or _HF_EXACT_NORM is not None:
        return
    data: dict = {}
    if _HIGH_FREQ_FILE.exists():
        try:
            loaded = yaml.safe_load(_HIGH_FREQ_FILE.read_text(encoding="utf-8")) or {}
            data = loaded.get("high_freq", {}) or {}
        except Exception as e:  # 词表损坏不应阻断渲染
            log.warning("[i18n high_freq] 加载 glossary/high_freq.yaml 失败：%s", e)
    sub_pairs: list[tuple[str, str]] = []
    exact_pairs: list[tuple[str, str]] = []
    for k, v in data.items():
        if not k or not v or k == v:
            continue
        if _KANA_RE.search(k):
            sub_pairs.append((k, v))       # 含假名 → 子串
        else:
            exact_pairs.append((k, v))     # 纯汉字 → 整词精确
    sub_pairs.sort(key=lambda kv: len(kv[0]), reverse=True)  # 长词优先
    _HF_SUB_MAP = {k: v for k, v in sub_pairs}
    _HF_SUB_RE = re.compile("|".join(re.escape(k) for k, _ in sub_pairs)) if sub_pairs else None
    _HF_EXACT_NORM = {_norm(k): v for k, v in exact_pairs}
    # 全量键（含假名）整词精确归一化：供 JA 精确匹配覆盖「已翻译中文」（如 レガリア→圣衣→王权）
    _HF_ALL_NORM = {_norm(k): v for k, v in data.items() if k and v and k != v}
    # _precise 白名单：仅名单内的键参与「纠正已译中文」层（_learn_corrections），
    # 其余 high_freq 键仅做渲染期源文替换（安全，不回改已译中文）。名单键须已存在于 high_freq。
    # 注：ja==zh 的同形词（如 地上/魔女）天然不入 _HF_ALL_NORM，也无需纠正，静默跳过；
    #     仅当 _precise 键根本不在 high_freq 时（拼写错误）才告警。
    all_keys_norm = {_norm(k) for k in data if k}
    precise_list = (loaded.get("_precise") or []) if isinstance(loaded, dict) else []
    _HF_PRECISE = set()
    for key in precise_list:
        nk = _norm(key) if isinstance(key, str) else ""
        if nk and nk in _HF_ALL_NORM:
            _HF_PRECISE.add(nk)
        elif nk and nk not in all_keys_norm:
            log.warning("[i18n high_freq] _precise 键未在 high_freq 中找到，已忽略：%r", key)
    # _precise 非纯片假名条目（纯汉字 / 含平假名，如 神騎/現界/真夏）：对 zh 文本做
    # 「残留日文形 → 规范中文」子串替换，实现「即使在句子中也强制统一」。
    # 纯片假名条目已由上方 _HF_SUB_RE 覆盖（_HF_SUB_MAP），此处不重复，避免双重处理。
    # 安全依据：中日同形字 Unicode 不同（戦≠战、騎≠骑、現≠现…），故只命中残留日文，
    # 不会误改已译中文；长词优先（九大神騎 先于 神騎），避免截断复合词。
    precise_sub = [
        (k, _HF_ALL_NORM[nk])
        for k in _HF_PRECISE
        if (nk := _norm(k)) in _HF_ALL_NORM and nk not in _HF_SUB_MAP
    ]
    precise_sub.sort(key=lambda kv: len(kv[0]), reverse=True)
    _HF_PRECISE_SUB_MAP = {k: v for k, v in precise_sub} or None
    _HF_PRECISE_SUB_RE = (
        re.compile("|".join(re.escape(k) for k, _ in precise_sub)) if precise_sub else None
    )


def _high_freq_override(text: str) -> str:
    """含假名高频词子串替换（仅对 zh 文本中的日语假名片段生效，安全不污染中文）。"""
    if not text:
        return text
    _load_high_freq_glossary()
    if _HF_SUB_RE is not None:
        return _HF_SUB_RE.sub(lambda m: _HF_SUB_MAP[m.group(0)], text)  # type: ignore[union-attr]
    return text


def _high_freq_precise_sub(text: str) -> str:
    """_precise 非片假名条目（纯汉字/含平假名）的句中子串纠正：把 zh 文本里残留的日文形
    替换成规范中文（如 神騎→神骑、現界→现界、真夏→盛夏）。

    仅命中残留日文（中日同形字 Unicode 不同，不会误改已译中文）；长词优先。
    纯片假名 _precise 条目已由 _high_freq_override 覆盖，此处不重复。"""
    if not text:
        return text
    _load_high_freq_glossary()
    if _HF_PRECISE_SUB_RE is not None:
        return _HF_PRECISE_SUB_RE.sub(
            lambda m: _HF_PRECISE_SUB_MAP[m.group(0)], text  # type: ignore[union-attr]
        )
    return text


def _high_freq_exact(ja: str) -> "str | None":
    """纯汉字高频词整词精确覆盖：节点 ja 归一化后恰为某纯汉字键 → 返回词表 ZH；否则 None。"""
    _load_high_freq_glossary()
    if _HF_EXACT_NORM is None:
        return None
    return _HF_EXACT_NORM.get(_norm(ja))


def _high_freq_all(ja: str) -> "str | None":
    """全量高频词（含假名键）整词精确覆盖：节点 ja 归一化后恰为某键 → 返回词表 ZH；否则 None。

    与 _high_freq_exact 区别：此处含假名键（如 レガリア），仅用于「节点/单元格 ja 整词精确命中」
    时覆盖已翻译中文，绝不子串替换，故不会污染中文。"""
    _load_high_freq_glossary()
    if _HF_ALL_NORM is None:
        return None
    return _HF_ALL_NORM.get(_norm(ja))


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
                    # 站点术语 / 专有名词 / 纯汉字高频词 最高优先级覆盖（覆盖旧 LLM 译）
                    ov = _term_override(t)
                    if ov is None:
                        ov = _name_override(t)
                    if ov is None:
                        ov = _high_freq_exact(t)
                    if ov is None:
                        ov = _high_freq_all(t)
                    if ov is not None:
                        zh = ov
                    # 含假名高频词 / inline_terms 子串替换（覆盖单元格内残留日语术语与称呼）
                    if zh:
                        zh = _high_freq_override(zh)
                        zh = _term_sub_override(zh)
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

def _set_block_html(el: "_Element", html_str: str) -> None:
    """把含 <a> 的 HTML 片段解析后写入 el，避免直接赋值 el.text 导致标签被实体转义。

    先清空 el（文本与子节点），再把 html_str 解析为 fragments 依次挂回。
    """
    for child in list(el):
        el.remove(child)
    el.text = None
    frags = lxml_html.fragments_fromstring(html_str)
    # fragments_fromstring 在片段以文本开头时会把首个文本节点作为列表首项
    first = True
    for frag in frags:
        if isinstance(frag, str):
            if first:
                el.text = frag
            else:
                # 后续纯文本：挂到最后一个子元素之后
                kids = list(el)
                if kids:
                    kids[-1].tail = (kids[-1].tail or "") + frag
                else:
                    el.text = (el.text or "") + frag
        else:
            el.append(frag)
        first = False


def _wrap_block_links(blk_zh: str, src_links: "list[tuple[str, str]]") -> str:
    """块级锚定套链接：在 blk_zh 纯文本里，仅为「原块内真实存在的 <a>」补回链接。

    src_links: 原块内每个内链 <a> 的 (href, 日文链接文本)。对每个：
      1. 用 link_terms / glossary 把 ja_text 翻成中文 zh_text（查不到则用 ja_text 本身）；
      2. 在 blk_zh 中把首次出现的 zh_text 包成 <a href>。
    每个原 <a> 只包一次，长词优先避免嵌套。绝不给原块没有链接的位置强加链接
    （位置一一对应原文 <a>，满足「原日文无超链接的中文位置不加链接」原则）。
    返回包裹后的 HTML 片段字符串。
    """
    if not blk_zh or not src_links:
        return blk_zh
    _load_link_terms()
    # 构造 (zh_text, href) 候选，长词优先
    cands = []
    for href, ja_text in src_links:
        zh_text = None
        # link_terms 配置：ja 精确命中（用全局 ja→zh 索引 O(1) 查找，避免遍历全站）
        if _LINK_JA_ZH and ja_text in _LINK_JA_ZH:
            cand = _LINK_JA_ZH[ja_text]
            # 鲁棒性：索引里的中文在 blk_zh 里找不到（如某 slug 段有损坏/字形漂移
            # 的重复条目覆盖了全局索引）→ 不能盲目采用，回退再试别的中文来源，
            # 避免单条坏数据毁掉整页链接。
            if cand and cand in blk_zh:
                zh_text = cand
        # glossary 专名/术语覆盖（也能跳过坏索引）
        if zh_text is None:
            ov = _name_override(ja_text) or _term_override(ja_text)
            if ov:
                zh_text = ov
        if zh_text is None:
            zh_text = ja_text  # 中日同形或查不到：用原文（专名保留）
        cands.append((zh_text, href))
    cands.sort(key=lambda c: len(c[0]), reverse=True)
    # 按候选在 blk_zh 中的位置切分包裹；每个候选只包一次
    used = [False] * len(cands)
    # 收集所有匹配区间
    segs = []  # (start, end, idx)
    for i, (zt, _h) in enumerate(cands):
        if not zt:
            continue
        start = 0
        while True:
            idx = blk_zh.find(zt, start)
            if idx < 0:
                break
            segs.append((idx, idx + len(zt), i))
            start = idx + len(zt)
    if not segs:
        return blk_zh
    segs.sort()
    out = []
    pos = 0
    for s, e, i in segs:
        if used[i]:
            continue  # 同一原 <a> 只包一次（取首个匹配）
        if s < pos:
            continue  # 与已包区间重叠，跳过（长词优先已排序，短词让位）
        out.append(_html.escape(blk_zh[pos:s], quote=False))
        zt, href = cands[i]
        attrib = {"href": href}
        if not str(href).lower().startswith("http"):
            attrib["target"] = "_blank"
            attrib["rel"] = "noopener"
        a = lxml_html.Element("a", attrib=attrib)
        a.text = zt
        out.append(lxml_html.tostring(a, encoding="unicode"))
        used[i] = True
        pos = e
    out.append(_html.escape(blk_zh[pos:], quote=False))
    result = "".join(out)
    # inline_terms 含假名子串覆盖（如正文内嵌「Bユニバース」→「B宇宙」）。
    # 仅替换文本节点里的子串，标签（<a href=...>）不受波及。
    return _term_sub_override(result)


def _fill_block_keep_links(el, blk: dict, keys: dict, blk_zh: str, locale: str, sub, slug: str = "") -> None:
    """含链接(<a>)且块级译文完整、但部分子 key 节点级缺译（zh 为空）的块。

    两条铁律（用户 2026-08-04 明确）：
    - 节点级 key 有译文 → 必须显示译文，绝不可回退日文。
    - 节点级 key 无译文（空 zh）但有块级译文 blk_zh → 用块级译文，绝不露日文；
      若原块含 <a> 跳转，尽量保留链接（单 <a> 时把 blk_zh 放进 <a>；多 <a>/复杂
      时整块纯文本 blk_zh，链接丢失但显示中文，待 link_terms 精修）。

    实现：
    1. 收集块内所有文本节点中的 {{keyN}}，判断节点级译文是否齐备。
    2. 齐备 → 逐节点用 sub 替换（保留 <a> 内各自译文 + href）。
    3. 不齐备 → 用 blk_zh：
       - 块内恰好单个 <a>：保留 <a> 壳，blk_zh 进 <a>.text（链接零丢失）。
       - 否则：整块纯文本 blk_zh（链接丢失但显示译文，不露日文）。
    """
    if not blk_zh:
        # 块级译文缺失的极端情况：退而逐 key 回退日文原文（不制造错乱，但会露日文）。
        # 理论上不会发生（调用方已保证 blk_zh 存在），仅作防御。
        return
    # 收集块内文本节点（el.text + 各子元素 text/tail）里的所有 {{keyN}}
    node_texts = [el.text]
    for child in el.iter():
        node_texts.append(child.text)
        node_texts.append(child.tail)
    blob = " ".join(t for t in node_texts if t)
    key_nums = set(_KEY_RE.findall(blob))
    missing = [n for n in key_nums if not keys.get(f"key{n}", {}).get("zh")]
    if blk.get("keys"):
        # 块有节点级 keys：blk_zh 是权威中文整句译文。
        # 块级锚定套链接：先收集原块内真实存在的 <a>（仅内链，外链走特例），
        # 整块纯文本化为 blk_zh 后，仅对「原块有链接的位置」用 _wrap_block_links
        # 精确补回 <a>。绝不跨位置强加（满足「原日文无链接的中文位置不加链接」）。
        # 不逐节点（缺译 key 会回退日文碎片，导致「日文混中文」）。
        # 特例：块内含外链 <a>（href 以 http 开头）→ 保留外链壳（内文日文，专名/站名），
        # 否则纯文本化会丢失外链。块其余文本仍用 blk_zh 中文（含内链锚定补回）。
        ext_links = [a for a in el.iter() if a.tag == "a"
                     and str(a.get("href") or "").lower().startswith("http")]
        if ext_links:
            for child in list(el):
                el.remove(child)
            el.text = blk_zh
            for a in ext_links:
                na = lxml_html.Element("a", attrib={"href": a.get("href")})
                na.text = (a.text or "").strip() or (a.get("title") or "")
                el.append(na)
            return
        # 收集块内内链 <a> 的 (href, 日文链接文本)，用于块级锚定补回
        src_links = []
        for a in el.iter("a"):
            href = (a.get("href") or "").strip()
            if href.lower().startswith("http"):
                continue
            ja_text = (a.text_content() or "").strip()
            m = _KEY_RE.search(ja_text)
            if m:
                k = "key" + m.group(1)
                ja_text = keys.get(k, {}).get("ja", ja_text) or ja_text
            if ja_text and href:
                src_links.append((href, ja_text))
        # 回退：块内 <a> 壳在 i18n 提取时可能丢失（仅留纯文本），
        # 此时改从「日文原页真实内链」补回锚点——link_terms 只含原文有链接的词，
        # 不会给原文无链接的位置强加链接。
        if not src_links and slug:
            src_links = [(h, t) for (t, h) in _ja_link_pairs_for_slug(slug)]
        for child in list(el):
            el.remove(child)
        _set_block_html(el, _wrap_block_links(blk_zh, src_links))
        return
    # 块无 keys（纯整块块）：节点级有缺译 → 用块级译文 blk_zh。
    links = [a for a in el.iter() if a.tag == "a"]
    if len(links) == 1:        # 单链接：保留 <a> 壳及其祖先结构（<strong> 等），blk_zh 整体进 <a>。
        # 注意：<a> 通常不是 el 的直接子节点（可能嵌套在 <strong> 内），
        # 故只改 <a> 自身文本、清掉 <a> 尾部兄弟文本，不移除 el 的子节点。
        a = links[0]
        for c in list(a):
            a.remove(c)
        a.text = _term_sub_override(blk_zh)
        a.tail = None  # 清掉 <a> 后的兄弟文本（如 </a>{{key58}}）
    else:
        # 多链接/复杂结构：整块纯文本 blk_zh（链接丢失但显示译文，待 link_terms 精修）
        for c in list(el):
            el.remove(c)
        el.text = _term_sub_override(blk_zh)


def _fill_block_ja_links(el, blk: dict, locale: str) -> None:
    """例外页（artists / voice-actors）专用：带超链接的文本块回退日文原文。

    项目规则（用户 2026-08-04）：原画索引 / 声优一览两个页面的带超链接文本块
    不需要翻译，直接用日文原文即可。本函数保留 <a> 链接壳与 href，仅把链接
    内文与块级文本替换为日文（blk['ja']），不套任何 glossary / 译文覆盖。
    无论当前块是否齐备译文都走此分支，保证「带链接块恒为日文原文」。

    关键：清空块容器 el 的非链接文本残留（el.text / 各 <a> 的 tail），否则块级
    分支之后顶层 _KEY_RE.sub(_sub) 会把残留的 {{keyN}} 翻译，破坏「恒为日文」。
    """
    blk_ja = blk.get("ja") or ""
    if not blk_ja:
        return
    links = [a for a in el.iter() if a.tag == "a"]
    if len(links) == 1:
        # 单链接：保留 <a> 壳（含祖先 <strong> 等结构），日文整体进 <a>；
        # 同时清掉块容器 el 的 el.text 与 <a>.tail，避免残留 {{keyN}} 被顶层 _sub 翻译。
        el.text = None
        a = links[0]
        for c in list(a):
            a.remove(c)
        a.text = blk_ja
        a.tail = None
    else:
        # 多链接/复杂结构：保留每个 <a> 壳（href 不动、内文设为日文），
        # 清空块容器 <a> 之外的所有文本与子节点（外层纯文本回退日文，避免残留 {{keyN}}）。
        el.text = None
        for a in links:
            for c in list(a):
                a.remove(c)
            a.text = blk_ja
            a.tail = None
        # 移除非 <a> 的直接子节点（保留嵌套在 <a> 内的结构）
        for child in list(el):
            if child.tag != "a":
                el.remove(child)


def render_locale(slug: str, locale: str) -> str | None:
    """模板 → 最终 HTML。节点级查表替换；zh 局部缺译时块级整句回退。"""
    if not has_i18n(slug):
        return None
    tpl = _tpl_path(slug).read_text(encoding="utf-8")
    entries = load_entries(slug)
    keys = _keys_of(entries)
    blocks = _blocks_of(entries)

    # 单个节点级 key 的 zh 取值（含 glossary 覆盖）。提前定义以便块级回退分支复用。
    # 句末【】链接标签：节点级 key 若含「不在任何块内的模板 <a>」（top_links），在其
    # 中文译文末追加【显示名】标签（链接绑定原日文 href，不依赖中文名匹配，译名不准也不丢跳转）。
    def _sub(m: "re.Match") -> str:
        ent = keys.get(f"key{m.group(1)}")
        if not ent:
            return m.group(0)
        if locale == "zh":
            ja = ent.get("ja", "")
            ov = _term_override(ja)  # 站点术语最高优先级覆盖
            if ov is not None:
                base = _html.escape(ov, quote=False)
            else:
                ov = _name_override(ja)
                if ov is not None:
                    base = _html.escape(ov, quote=False)  # 独立名词直接覆盖
                else:
                    ov = _high_freq_exact(ja)  # 纯汉字高频词整词精确覆盖
                    if ov is None:
                        ov = _high_freq_all(ja)  # 含假名词条整词精确覆盖（如 レガリア）
                    if ov is not None:
                        base = _html.escape(ov, quote=False)
                    else:
                        text = ent.get("zh") or ja
                        text = _correct_text(text)  # 漏译/错译纠正 + 含假名高频词子串替换
                        base = _html.escape(text, quote=False)
            for href, ja_text in top_links:
                if ja_text and ja_text in ja:
                    href2, target = _normalize_link_href(href)
                    name = _link_display_zh(ja_text)
                    base += (
                        f'<a href="{_html.escape(href2, quote=True)}"{target}'
                        f' class="escah-ilink">【{_html.escape(name, quote=False)}】</a>'
                    )
            return base
        return _html.escape(ent.get("ja", ""), quote=False)

    # —— 新链接方案（句末【】标签，替代旧「句中切割注入」）——
    # 收集模板内所有正文 <a>（规范化 href + 日文链接文本），按所属块(_BLK_ATTR) 归属记录；
    # 随后 drop 掉 <a> 壳（链接不再在句中注入，改到句末【】标签）。
    # 链接绑定原日文 href（不依赖中文名匹配 → 译名不准也不丢跳转）。
    # 显示名取 glossary 中文译名（优先 names→skills→terms→high_freq，兜底日文原文）。
    from collections import defaultdict
    block_links: "dict[str, list[tuple[str, str]]]" = defaultdict(list)
    top_links: "list[tuple[str, str]]" = []
    if "<a" in tpl:
        try:
            lfrag = lxml_html.fragment_fromstring(tpl, create_parent="div")
            for a in lfrag.xpath(".//a"):
                href = (a.get("href") or "").strip()
                if not href or href.startswith("#"):
                    a.drop_tag()
                    continue
                ja_text = (a.text_content() or "").strip()
                m = _KEY_RE.search(ja_text)
                if m:
                    k = "key" + m.group(1)
                    ja_text = keys.get(k, {}).get("ja", ja_text) or ja_text
                if not ja_text:
                    a.drop_tag()
                    continue
                bid = None
                p = a.getparent()
                while p is not None:
                    if _BLK_ATTR in p.attrib:
                        bid = p.get(_BLK_ATTR)
                        break
                    p = p.getparent()
                if bid:
                    block_links[bid].append((href, ja_text))
                else:
                    top_links.append((href, ja_text))
                a.drop_tag()
            tpl = lxml_html.tostring(lfrag, method="html", encoding="unicode")
            if tpl.startswith("<div>") and tpl.rstrip().endswith("</div>"):
                tpl = tpl[len("<div>"):-len("</div>")]
        except Exception:
            log.warning("[i18n render] %s 模板链接收集失败", slug)

    # 块级回退：zh 且块内有缺译且块级译文存在 → 整块换为纯文本 zh + 句末【】标签
    if _BLK_ATTR in tpl:
        try:
            frag = lxml_html.fragment_fromstring(tpl, create_parent="div")
            for el in frag.xpath(f".//*[@{_BLK_ATTR}]"):
                bid = el.get(_BLK_ATTR)
                el.attrib.pop(_BLK_ATTR, None)
                blk = blocks.get(bid)
                if not blk or locale != "zh":
                    continue
                src_links = block_links.get(bid, [])
                # 例外页（artists / voice-actors）：带链接块恒为日文原文，
                # 句末追加【日文名】（保留 href，不翻译内文）。
                if slug in SKIP_LINK_SLUGS:
                    if not blk.get("ja"):
                        continue
                    blk_ja = blk["ja"]
                    if src_links:
                        extra = ""
                        for href, ja_text in src_links:
                            href2, target = _normalize_link_href(href)
                            extra += (
                                f'<a href="{_html.escape(href2, quote=True)}"{target}'
                                f' class="escah-ilink">【{_html.escape(ja_text, quote=False)}】</a>'
                            )
                        _set_block_html(el, blk_ja + extra)
                    else:
                        el.text = blk_ja
                    continue
                if not blk.get("zh"):
                    continue
                # 节点级全有译文也走整块 blk_zh 替换（blk_zh 是完整中文整句）；
                # 链接统一在句末追加（block_links[bid]），不再保留行内 <a> 壳。
                blk_zh = blk["zh"]
                ov = _name_override(blk.get("ja", ""))
                if ov is not None:
                    blk_zh = ov
                else:
                    blk_zh = _correct_text(blk["zh"])
                if not src_links:
                    el.text = blk_zh  # 无链接：纯文本块
                    continue
                # 表格单元格特例：单元格纯文本恰为该单链接词（原文就只有这个词）
                # → 直接【中文名】，不显示括号外译文（单元格文本本身就是译文）。
                blk_ja = blk.get("ja", "")
                if len(src_links) == 1 and _norm_ns(blk_ja) == _norm_ns(src_links[0][1]):
                    href, ja_text = src_links[0]
                    href2, target = _normalize_link_href(href)
                    name = _link_display_zh(ja_text)
                    _set_block_html(
                        el,
                        f'<a href="{_html.escape(href2, quote=True)}"{target}'
                        f' class="escah-ilink">【{_html.escape(name, quote=False)}】</a>',
                    )
                    continue
                # 普通句子：翻译文本 + 句末【名1】【名2】
                extra = ""
                for href, ja_text in src_links:
                    href2, target = _normalize_link_href(href)
                    name = _link_display_zh(ja_text)
                    extra += (
                        f'<a href="{_html.escape(href2, quote=True)}"{target}'
                        f' class="escah-ilink">【{_html.escape(name, quote=False)}】</a>'
                    )
                _set_block_html(el, blk_zh + extra)
            tpl = lxml_html.tostring(frag, method="html", encoding="unicode")
            if tpl.startswith("<div>") and tpl.rstrip().endswith("</div>"):
                tpl = tpl[len("<div>"):-len("</div>")]
        except Exception:
            log.warning("[i18n render] %s 块级回退失败，退回节点级渲染", slug)

    def _apply_config_links(html: str, ja_link_words: "set[str]") -> str:
        """zh 镜像页：按 glossary/link_terms.yaml 配置，把指定中文词包裹成 <a>。

        与已废弃的整句链接方案不同，本函数做「词级精确子串匹配」：
        对当前 slug 的配置条目，在生成的 zh HTML 文本里找到 links[].zh 词，
        用 <a href=...> 包裹（外链用原 href，站内 'xxx.html' 归一化为 /zh/xxx.html）。
        安全约束：已处于某 <a> 内部的词不再重复包裹；不误改标签属性值里的相同字串；
        同一 slug 内相互包含的 zh 词按长词优先，避免嵌套坏链。找不到匹配词静默跳过。

        每页独立判断：link_terms 的 ja 词仅当在当页日文原文里本身是 <a> 链接时，
        中文译文才包裹超链接（ja_link_words 为该页 ja 原文所有链接文本集合）。
        这保留了「同词跨页复用配置」的便利，又避免中文页出现原页没有的强加链接。
        """
        _load_link_terms()
        if not _LINK_TERMS:
            return html
        # 当前页 slug 条目 + 全局 "*" 条目合并（全局条目对所有页面生效，
        # 用于「同一个词跨多页出现、只精修一次」的场景）。
        entries = list(_LINK_TERMS.get(slug, [])) + list(_LINK_TERMS.get("*", []))
        if not entries:
            return html
        # 每页独立判断：仅保留「当页日文原文该 ja 词本身是链接」的条目。
        # ja 为空的兼容条目（无 ja 溯源）一律保留，向后兼容。
        if ja_link_words:
            entries = [
                e for e in entries
                if not e.get("ja") or e["ja"] in ja_link_words
            ]
            if not entries:
                return html
        # 长词优先（避免「问题」被先包、再包「常见问题」导致嵌套）
        entries = sorted(entries, key=lambda e: len(e["zh"]), reverse=True)
        try:
            frag = lxml_html.fragment_fromstring(html, create_parent="div")
        except Exception:
            return html

        def wrap_text(node, word, href, target):
            """在 node 的文本节点里，把 word 出现的首次位置包成 <a>（已含 <a> 则跳过）。"""
            if node.text and word in node.text:
                # 若本节点自身已在 <a> 内则不动
                if node.tag == "a":
                    return False
                idx = node.text.index(word)
                before = node.text[:idx]
                after = node.text[idx + len(word):]
                attrib = {"href": href}
                if target:
                    attrib["target"] = "_blank"
                    attrib["rel"] = "noopener"
                a = lxml_html.Element("a", attrib=attrib)
                a.text = word
                # 把 node 的文本切分：before 保留，a 插入，after 成为 a.tail
                node.text = before
                node.insert(0, a)
                a.tail = after
                return True
            return False

        def walk(el):
            changed_any = False
            # 标题标签（h1-h6）内不包 link_terms 链接：原站标题通常是纯文本 + 锚点，
            # 正文中同名词的业务链接会被「每页独立判断」误判，导致标题被强加跨页链接
            # （如 faq 各 h3「宝箱/限界突破」、gacha h2「常见问题」）。镜像忠实性原则下
            # 标题不加业务链接。标题内的 <a>（如 † 锚点）子节点仍递归但不在此处理。
            is_heading = el.tag in ("h1", "h2", "h3", "h4", "h5", "h6")
            # 先处理自身文本（标题跳过）
            if not is_heading:
                for e in entries:
                    href, target = _normalize_link_href(e["href"])
                    if wrap_text(el, e["zh"], href, target):
                        changed_any = True
                        break  # 一个文本节点只处理一次（长词优先已排序）
            # 递归子节点（跳过已包好的 <a> 内部，避免嵌套）
            if el.tag != "a":
                for child in list(el):
                    walk(child)
            return changed_any

        walk(frag)
        out = lxml_html.tostring(frag, method="html", encoding="unicode")
        if out.startswith("<div>") and out.rstrip().endswith("</div>"):
            out = out[len("<div>"):-len("</div>")]
        return out

    html = _KEY_RE.sub(_sub, tpl)
    # zh 镜像页链接补回：已由块级 _wrap_block_links（在 _fill_block_keep_links 内）接管，
    # 仅对「原块内真实存在的 <a>」做块级锚定包裹，绝不跨位置强加（满足「原日文无链接
    # 的中文位置不加链接」原则）。整页级 _apply_config_links 已废弃（其全文词级匹配会
    # 在同词多处时强加链接，违背锚定原则），保留函数定义仅作参考、不再调用。
    # 例外页（artists / voice-actors）：带链接块恒为日文原文，不套中文链接包裹（见上分支）。
    # 站内跨页面跳转（internal-link 且非页内锚点）一律新标签页打开，避免打断阅读。
    # 例外：跳到「当前页」（同名文件，含带 #anchor 的同页锚点）则不新开，原地跳转。
    if _INTLINK_RE is not None:
        cur_html = posixpath.basename(slug) + ".html"  # 当前页文件名

        def _open_new(m: "re.Match") -> str:
            tag = m.group(0)
            if "target=" in tag:
                return tag
            href = m.group(1)
            if href.startswith("#"):
                return tag
            # 解析 href 的文件名（去掉锚点 / 目录前缀 / './' 前缀）
            basename = href.split("#", 1)[0].rstrip("/").split("/")[-1]
            if basename in ("", cur_html):
                return tag  # 跳当前页 → 不新开
            # 注意：tag 以 '>' 结尾，仅需去掉末尾 '>'（保留 href/title 的闭合引号），
            # 否则 tag[:-2] 会误删闭合引号，使 target= 被塞进 href/title 属性值内导致 404。
            return tag[:-1] + ' target="_blank" rel="noopener">'
        html = _INTLINK_RE.sub(_open_new, html)
    # 末尾读音归一化（zh 仅）：部分页面（数据表/散文）的文本经自定义渲染落地，
    # 不经过节点级 _correct_text，导致旧读音（梅加艾尔/玛雅艾尔）以子串残留。
    # 此处对整段 html 做子串纠正（名字唯一，无误伤风险）。
    if locale == "zh" and _READING_CORR:
        for old, new in _READING_CORR.items():
            if old in html:
                html = html.replace(old, new)
    return html


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
