# -*- coding: utf-8 -*-
"""谷歌免费翻译引擎（解耦模块）。

两种用法：
  1) 库调用（供 i18n / cli 使用）：
       from .gtrans import translate_text, translate_lines, translate_todo_file
  2) 命令行手动翻译待译文件（不依赖项目流水线，可单独执行）：
       python -m escah_pipeline.gtrans <待译文件.txt> [更多文件...]
       python -m escah_pipeline.gtrans tools/_todo_translate/faq_20260826.txt
     产物：同目录同 stem + `_translated.txt`（正是 `i18n fill --per-page` 期望的文件名）。

走谷歌网页版内部接口 translate-pa.googleapis.com（非官方、免费），
只依赖 requests（无则回退 urllib，CI 免装依赖）。

待译文件格式约定（与 `i18n extract` 严格对称，勿另创格式）：
  - 首行起若干 `#` 注释行 / 提示词行 → 原样保留，不翻译
  - 条目行 `[keyN] 日文` 或 `[blkN] 日文` 或 `[12] 日文` → 只翻译方括号后的正文
  - 段分隔符 `===A===` → 原样保留（fill 依赖它，丢了就 0 回填）
  - 可见换行标记 `⏎` 在翻译前替换为安全占位，翻译后还原（谷歌会吃掉该字符）
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import yaml
from html import unescape
from pathlib import Path
from typing import Iterable, Sequence

# ---------------------------------------------------------------------------
# 谷歌内部接口配置
# ---------------------------------------------------------------------------
GOOGLE_URL = "https://translate-pa.googleapis.com/v1/translateHtml"
GOOGLE_API_KEY = "AIzaSyATBXajvzQLTDHEQbcpq0Ihe0vWDHmO520"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
)

LANG_MAP = {
    "zh": "zh-CN", "zh-cn": "zh-CN", "zh-tw": "zh-TW", "cht": "zh-TW",
    "jp": "ja", "jpx": "ja",
}

# ---------------------------------------------------------------------------
# 谷歌免费接口限制（实测 + 官方文档，2026-08-26 核实）
# ---------------------------------------------------------------------------
# 接口：translate-pa.googleapis.com/v1/translateHtml（即网页版「wt_lib」内部接口，免密钥/免费）。
# 权威限制（Google Cloud Translation 文档，最后更新 2026-08-11）：
#   ① 单请求最大 **100,000 字节**（超出 → 400 INVALID_ARGUMENT）；官方另建议「每请求 ≤ 5K 字符」以免高延迟。
#   ② 每日字符配额 = 无限（按项目），无单日封顶。
#   ③ 速率：每项目每分钟 **300,000 次请求**（v2）；超量 403 Daily/Rate Limit。
#   ④ 该免费端点按客户端 IP 计用户级限额，过快/过猛会被临时限流（返回 429/403），故必须主动限速。
# 因此唯一会直接导致 400 失败的硬约束是「单请求体积」，本模块据此设定以下保守上限：
MAX_REQ_BYTES = 4000     # 单次请求 payload 的 UTF-8 字节预算（远低于 100K 字节硬上限，亦满足 ≤5K 字符建议）
# 单条文本字节上限：必须**显著小于** MAX_REQ_BYTES，不能与它相等。
#  payload 有约 30 字节的 JSON 外壳（[[[""],"ja","zh-CN"],"wt_lib"]），单条文本里的
#  引号/反斜杠在 json.dumps 时还会再膨胀。若两者取相同值，单条字节数落在
#  (MAX_REQ_BYTES-30, MAX_REQ_BYTES] 时会出现「整批超限 → 拆成单条 → 仍然超限」
#  的无限递归（RecursionError）。而 _chunk_item 用 3 字节汉字贪心填充，切出的块
#  几乎必然是 3999/4000 字节，正好落在该区间（实测 7 个超长条目全部命中）。
MAX_ITEM_BYTES = MAX_REQ_BYTES - 64   # 3936：30 字节外壳 + 34 字节转义余量
BATCH_SIZE = 20          # 单次请求最多条数
MAX_RETRY = 4            # 单批最大重试次数
RETRY_BASE_SLEEP = 1.5   # 指数退避基数（秒）

# —— 限速（2026-09-26 调参 + 自适应）——
# 实测背景：74 卷实跑时死过 1 卷，但**真因不是间隔太小**，而是 `requests.post` 的
# 传输异常没被包成 GTransError，穿透了重试层直接冒到 translate_todo_dir（整卷判死）。
# 不过间隔确实偏激进：原 0.15s ≈ 6.7 批/秒，而这个免费端点按**客户端 IP**计用户级限额，
# 短时间突发容易被 429/403。故默认放宽到 0.5s（≈2 批/秒），并加自适应节流：
# 撞限流翻倍退避（上限 MAX_INTERVAL），连续成功再回落（下限 = 基准间隔）。
# 均可用环境变量覆盖，命令行 --interval/--rate 优先级更高。
REQ_INTERVAL = float(os.environ.get("ESCAH_GTRANS_INTERVAL", "0.5"))   # 批间最小间隔（秒）
MAX_INTERVAL = float(os.environ.get("ESCAH_GTRANS_MAX_INTERVAL", "5.0"))  # 自适应退避上限
# 速率护栏：单进程每分钟最多发多少请求，远低于 300K/min 项目上限，避免被 IP 级限流
RATE_PER_MIN = int(os.environ.get("ESCAH_GTRANS_RATE_PER_MIN", "120"))  # ≈2 req/s
FILE_RETRY = int(os.environ.get("ESCAH_GTRANS_FILE_RETRY", "3"))        # 单卷失败重试次数
_RATE_WIN = 60.0

# 轻量运行统计（收尾打印，便于判断是否被限流/是否需要调参）
_STATS: "dict[str, float]" = {"req": 0, "limited": 0, "retry": 0, "rc": 0}

# 可见换行标记：extract 导出的 ⏎（i18n._BR_EXPORT）。
# 谷歌会合并/丢弃换行，故按 ⏎ 拆片段分别翻译再回拼（见 translate_lines 文档）。
BR_EXPORT = "⏎"

# 支持段级 id（[blk12#1]）—— 多行块按段拆分后，每行仍是独立翻译单元，id 原样带 #n。
_ENTRY_RE = re.compile(r"^\[([A-Za-z]*\d+(?:#\d+)?)\]\s?(.*)$")
_SEP_RE = re.compile(r"^===\s*[A-Za-z]+\s*===$")
_KANA_RE = re.compile(r"[ぁ-んァ-ヶ]")


class GTransError(RuntimeError):
    """谷歌翻译调用失败。"""


class GTransRateLimited(GTransError):
    """被限流（HTTP 429/403 或 5xx）：可重试，且尽量遵守 Retry-After。

    单独成类的原因：它需要**不同的处理策略**（拉长批间间隔 + 等待 Retry-After），
    而不是普通错误那种固定指数退避。父类捕获顺序上必须排在 GTransError 之前。
    """

    def __init__(self, msg: str, retry_after: "float | None" = None):
        super().__init__(msg)
        self.retry_after = retry_after


class GTransDataError(GTransError):
    """结构/数据校验失败（确定性错误）。

    重试没有意义（同样的输入必然得到同样的不一致），所以目录模式**不再重试**它，
    避免白白多打几轮请求；直接把该卷记入失败清单。
    """


def norm_lang(code: str) -> str:
    if not code:
        return ""
    c = code.strip().lower()
    return LANG_MAP.get(c, c)


# ---------------------------------------------------------------------------
# 底层 HTTP
# ---------------------------------------------------------------------------
def _post(payload: str) -> str:
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json+protobuf",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "User-Agent": USER_AGENT,
    }
    try:
        import requests  # 优先 requests（本地一般已装）
    except ImportError:
        requests = None

    if requests is not None:
        resp = _session_post(requests, payload, headers)
        _check_status(resp.status_code, resp.text, resp.headers.get("Retry-After"))
        return resp.text

    # 回退 urllib：CI 上无需额外依赖
    import urllib.error
    import urllib.request
    req = urllib.request.Request(GOOGLE_URL, data=payload.encode("utf-8"),
                                headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            _STATS["req"] += 1
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        _STATS["req"] += 1
        body = e.read().decode("utf-8", "replace")[:300]
        _check_status(e.code, body, e.headers.get("Retry-After") if e.headers else None)
        raise GTransError(f"HTTP {e.code}: {body!r}") from e
    except Exception as e:  # noqa: BLE001
        # 传输层异常（超时/连接重置/DNS）必须归类为可重试错误，否则会穿透重试层
        raise GTransError(f"请求失败: {type(e).__name__}: {e}") from e


_SESSION = None


def _session_post(requests_mod, payload: str, headers: "dict[str, str]"):
    """用**复用的 Session** 发请求（keep-alive）。

    两个作用：① 省掉每请求新建 TCP/TLS 的开销（实测批量时占大头）；
    ② 连接复用更贴近真实浏览器行为，比每请求新连接更不容易被判定为异常流量。
    """
    global _SESSION
    if _SESSION is None:
        _SESSION = requests_mod.Session()
    _STATS["req"] += 1
    if not _STATS.get("t0"):
        _STATS["t0"] = time.monotonic()      # 首次请求时刻，用于算总耗时/均速
    try:
        return _SESSION.post(GOOGLE_URL, headers=headers,
                             data=payload.encode("utf-8"), timeout=30)
    except Exception as e:  # noqa: BLE001
        # ⚠️ 历史 bug：这里原来没包异常，requests 的 ConnectionError/Timeout 会**穿透**
        #     `_translate_units` 的 except GTransError，一路冒到 translate_todo_dir，
        #     「整卷失败」被当成不可恢复（实测 74 卷死 1 卷，重跑即通过 = 典型瞬时错误）。
        raise GTransError(f"请求失败: {type(e).__name__}: {e}") from e


def _check_status(code: int, body: str, retry_after: "str | None") -> None:
    """按状态码分类抛错：限流/服务端错误 → 可重试；其余非 200 → 普通失败。

    429/403 与 5xx 归为 GTransRateLimited（可等待后重试），并把响应头 Retry-After
    透传给上层（谷歌偶尔会给，尊重它能显著减少无效重试）。
    """
    if code == 200:
        return
    ra: "float | None" = None
    if retry_after:
        try:
            ra = float(retry_after)
        except (TypeError, ValueError):
            ra = None
    if code in (429, 403) or code >= 500:
        _STATS["limited"] += 1
        raise GTransRateLimited(f"HTTP {code}: {body[:200]}", ra)
    raise GTransError(f"HTTP {code}: {body[:300]}")


def _translate_batch(texts: Sequence[str], src: str, tgt: str, _depth: int = 0) -> list[str]:
    """一次请求翻译多条。返回等长列表；失败抛 GTransError。

    硬性体积护栏：若整批 payload 字节数超过 MAX_REQ_BYTES（理论上 batching 已保证），
    则回退为逐条翻译，逐条时超 MAX_ITEM_BYTES 的单条再切分——绝不直接打出超限请求。

    ⚠️ 防无限递归（历史 bug）：只有在「还能继续拆条」时才递归。若已只剩单条、
    或递归层数过深，说明单条虽 ≤ MAX_ITEM_BYTES 但加上 JSON 外壳仍超限
    （配置不当，或文本含大量需转义字符）→ 改为切分文本本身，绝不再次调用自身；
    切分也压不下去时（极端转义膨胀）直接回退原文，放弃该批机翻而不崩任务。
    """
    if not texts:
        return []
    pay = json.dumps([[list(texts), src, tgt], "wt_lib"], ensure_ascii=False)
    if _byte_len(pay) > MAX_REQ_BYTES:
        if len(texts) == 1 or _depth >= 2:
            if _depth >= 6:  # 兜底：切分也压不下去 → 回退原文，绝不无限递归
                return list(texts)
            out: list[str] = []
            for one in texts:
                out.extend(_translate_chunked(one, src, tgt, _depth + 1))
            return out
        out = []
        for one in texts:
            out.extend(_translate_batch([one], src, tgt, _depth + 1) if _byte_len(one) <= MAX_ITEM_BYTES
                       else _translate_chunked(one, src, tgt, _depth + 1))
        return out
    raw = _post(pay)
    try:
        data = json.loads(raw)
        res = data[0]
        if isinstance(res, str):
            res = [res]
        result = [unescape(x) if isinstance(x, str) else "" for x in res]
    except Exception as e:  # noqa: BLE001
        raise GTransError(f"返回解析失败: {e} / {raw[:300]}") from e
    if len(result) != len(texts):
        raise GTransError(f"条数不匹配: 请求 {len(texts)} 返回 {len(result)}")
    return result


def _translate_chunked(text: str, src: str, tgt: str, _depth: int = 0) -> list[str]:
    """超长单条：按字节切分后逐段翻译，再把译文用原文同款连接符拼回（不引入换行）。

    `_depth` 必须向下传递，否则会与 _translate_batch 形成相互递归（切分后体积仍
    超限 → 又来切分 → 无限循环）。
    """
    chunks = _chunk_item(text, MAX_ITEM_BYTES)
    parts = []
    for c in chunks:
        try:
            parts.append(_translate_batch([c], src, tgt, _depth + 1)[0])
        except (GTransError, RecursionError):
            parts.append(c)
    return ["".join(parts)]


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------
def translate_text(text: str, src: str = "ja", tgt: str = "zh-CN") -> str:
    """翻译单条文本。空串直接返回。"""
    if not text or not text.strip():
        return text or ""
    return translate_lines([text], src=src, tgt=tgt)[0]


def _byte_len(s: str) -> int:
    return len(s.encode("utf-8"))


def _chunk_item(text: str, limit: int) -> list[str]:
    """把超长单条按字节切分（不破坏日文字节序），每段 ≤ limit 字节。"""
    if _byte_len(text) <= limit:
        return [text]
    out: list[str] = []
    cur = ""
    for ch in text:
        if _byte_len(cur) + _byte_len(ch) > limit and cur:
            out.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


class _RateLimiter:
    """滑动窗口限速：每 RATE_PER_MIN/分钟 最多放行 RATE_PER_MIN 次请求。"""

    def __init__(self, per_min: int, window: float = _RATE_WIN):
        self.per_min = per_min
        self.window = window
        self._ts: list[float] = []

    def wait(self) -> None:
        now = time.monotonic()
        cutoff = now - self.window
        self._ts = [t for t in self._ts if t > cutoff]
        if len(self._ts) >= self.per_min:
            sleep_for = self._ts[0] + self.window - now
            if sleep_for > 0:
                time.sleep(min(sleep_for, self.window))
            now = time.monotonic()
            self._ts = [t for t in self._ts if t > now - self.window]
        self._ts.append(now)


_RATELIMITER = _RateLimiter(RATE_PER_MIN)


class _Throttle:
    """自适应批间间隔。

    固定间隔的两难：定太小容易撞限流，定太大又拖慢总量。做法是「基准 + 自适应」：
      · 正常情况用基准间隔（默认 0.5s）；
      · 一旦撞限流（GTransRateLimited）：间隔翻倍，上限 MAX_INTERVAL（默认 5s）；
      · 连续成功若干批后：间隔按 0.8 慢速回落，**不低于基准**（避免振荡回激进值）。
    这样既能立刻从限流里恢复，又不会长期停留在慢速上。
    """

    def __init__(self, base: float):
        self.base = max(0.0, base)
        self.cur = self.base
        self._ok = 0

    def on_limited(self) -> None:
        self._ok = 0
        self.cur = min(MAX_INTERVAL, max(self.cur * 2, 0.5))

    def on_success(self) -> None:
        self._ok += 1
        if self._ok >= 5 and self.cur > self.base:
            self.cur = max(self.base, self.cur * 0.8)
            self._ok = 0

    def sleep(self) -> None:
        if self.cur > 0:
            time.sleep(self.cur)


_THROTTLE = _Throttle(REQ_INTERVAL)


def _translate_units(units: Sequence[str], src: str, tgt: str,
                    progress: bool = False, label: str = "") -> list[str]:
    """翻译「不含 ⏎ 的原子片段」列表，返回等长结果。失败条目回退原文。

    约束：每批 payload UTF-8 字节数 ≤ MAX_REQ_BYTES（远低于谷歌 100K 字节硬上限），
    条数 ≤ BATCH_SIZE；单条超 MAX_ITEM_BYTES 先内部切分。整批受 _RATELIMITER 节流，
    绝不逼近 300K 次/分钟的官方速率上限。
    """
    out: list[str] = list(units)
    todo = [i for i, x in enumerate(units) if x and x.strip()]
    if not todo:
        return out

    # 拆出超长单条（不可能，因 units 已是 ⏎ 切出的短片段，仍保留防御）
    batches: list[list[int]] = [[]]
    cur = 0
    for i in todo:
        b = _byte_len(units[i])
        if batches[-1] and (len(batches[-1]) >= BATCH_SIZE or cur + b > MAX_REQ_BYTES):
            batches.append([])
            cur = 0
        batches[-1].append(i)
        cur += b

    done = 0
    for bi, idxs in enumerate(batches):
        if not idxs:
            continue
        src_texts = [units[i] for i in idxs]
        got: list[str] | None = None
        for attempt in range(MAX_RETRY):
            try:
                _RATELIMITER.wait()
                got = _translate_batch(src_texts, src, tgt)
                _THROTTLE.on_success()
                break
            except GTransRateLimited as e:
                # ⚠️ 必须排在 except GTransError 之前（子类）：限流要「拉长间隔 + 听 Retry-After」，
                #    而不是普通错误的固定退避，否则会一直用同样的节奏去撞同一堵墙。
                _STATS["retry"] += 1
                _THROTTLE.on_limited()
                wait = e.retry_after if e.retry_after else RETRY_BASE_SLEEP * (2 ** attempt)
                print(f"[gtrans] 批 {bi + 1} 被限流（{e}）；间隔→{_THROTTLE.cur:.1f}s，"
                      f"等待 {wait:.1f}s 后重试", file=sys.stderr)
                time.sleep(wait)
            except GTransError as e:
                _STATS["retry"] += 1
                if attempt == MAX_RETRY - 1:
                    print(f"[gtrans] 批 {bi + 1} 重试耗尽，降级逐条：{e}", file=sys.stderr)
                else:
                    time.sleep(RETRY_BASE_SLEEP * (2 ** attempt))
        if got is None:
            got = []
            for one in src_texts:
                try:
                    _RATELIMITER.wait()
                    got.append(_translate_batch([one], src, tgt)[0])
                    _THROTTLE.on_success()
                except GTransError:
                    got.append(one)
                _THROTTLE.sleep()
        for i, zh in zip(idxs, got):
            out[i] = zh or units[i]
        done += len(idxs)
        if progress:
            print(f"[gtrans] {label}{done}/{len(todo)} 片段完成（批 {bi + 1}/{len(batches)}）")
        _THROTTLE.sleep()
    return out


def translate_lines(lines: Sequence[str], src: str = "ja", tgt: str = "zh-CN",
                    progress: bool = False) -> list[str]:
    """批量翻译，返回与输入等长的列表（顺序严格对应）。

    ⚠️ 换行对齐铁律：条目内的 `⏎`（extract 导出的 `_BR_PH`）数量必须与原文完全一致，
    否则回填后 zh 与 ja 段数不符，渲染期会整段回退日文。谷歌翻译会合并/丢弃句子，
    无法保证 `<br/>` 哨兵存活，故这里**按 `⏎` 拆成原子片段分别翻译，再用原文的
    `⏎` 位置重新拼接**——数量天然守恒，不依赖谷歌行为。
    """
    s = norm_lang(src) or "auto"
    t = norm_lang(tgt) or "zh-CN"

    # 拆分：记录每条由哪些片段组成（owner[i] = 原条目下标）
    units: list[str] = []
    owner: list[int] = []
    seg_counts: list[int] = []
    for li, ln in enumerate(lines):
        segs = (ln or "").split(BR_EXPORT)
        seg_counts.append(len(segs))
        for sgm in segs:
            units.append(sgm)
            owner.append(li)

    zh_units = _translate_units(units, s, t, progress=progress)

    # 冗余层1：片段总数必须守恒，否则整体放弃机翻回退原文（绝不写出错位数据）
    if len(zh_units) != len(units):
        print(f"[gtrans] 致命：片段数不守恒（{len(units)}→{len(zh_units)}），"
              f"本批全部回退原文以保护格式", file=sys.stderr)
        return list(lines)

    # 按原 ⏎ 位置重组，数量严格守恒
    out: list[str] = []
    pos = 0
    for li, cnt in enumerate(seg_counts):
        segs = zh_units[pos:pos + cnt]
        pos += cnt
        # 冗余层2：单片段内绝不允许残留任何换行/⏎，否则会凭空多出段落（断句）
        clean: list[str] = []
        for sgm in segs:
            sgm = sgm.replace("\r", " ").replace("\n", " ")
            if BR_EXPORT in sgm:            # 谷歌把哨兵吐回来的极端情况
                sgm = sgm.replace(BR_EXPORT, " ")
            clean.append(sgm)
        joined = BR_EXPORT.join(clean)

        # 冗余层3：逐条校验 ⏎ 数量；不等则该条回退原文（宁可不译，绝不断句）
        src_line = lines[li] or ""
        if joined.count(BR_EXPORT) != src_line.count(BR_EXPORT):
            print(f"[gtrans] 第 {li + 1} 条换行数不符"
                  f"（{src_line.count(BR_EXPORT)}→{joined.count(BR_EXPORT)}），该条回退原文",
                  file=sys.stderr)
            joined = src_line
        out.append(joined)
    return out


# ---------------------------------------------------------------------------
# 翻译前词表预替换（解耦的核心环节）
# ---------------------------------------------------------------------------
# 设计要点（与用户确认）：
#   在「送翻之前」把日文原文里的固定译法术语替换成中文，谷歌/大模型翻译时
#   会把中文段原样保留、只翻剩余日文 → 译文天然统一、零残留日文、还能消除
#   整句漏翻。这是比「翻译后回填」更优的方案（实测验证）。
# 预替换词表来源 = names.yaml(专名, 整词精确) ∪ high_freq.yaml(含假名子串层)。
# 两者都只针对「日文术语」，原文预替时不存在「误改已译中文」问题（原文是纯日文），
# 比 render-time 子串替换更安全。纯汉字/整词层(high_freq 死条目)不纳入，避免误替。
# 只替换正文内容，绝不触碰 `[id]` 标记与可见换行标记 `⏎`（对齐铁律不受影响）。
_PRESUB_NAME_MAP: "dict[str, str] | None" = None
_PRESUB_NAME_RE: "re.Pattern | None" = None
_PRESUB_HF_MAP: "dict[str, str] | None" = None
_PRESUB_HF_RE: "re.Pattern | None" = None
_PRESUB_R18_MAP: "dict[str, str] | None" = None
_PRESUB_R18_RE: "re.Pattern | None" = None
# 纯汉字术语层（high_freq 里「不含假名」的条目）。**只用于送翻前预替换**：
# 渲染期不能用（会把中文里的同形汉字误改），但送翻前原文是纯日文，替换是安全的。
# 漏掉这层会怎样（实测）：`下位層のページがありません` 里 `ページ/ありません` 被替换、
# 而 `下位層` 没替换 → 送翻文本半中半日 → 谷歌翻不干净 → 该条被判「未译」留空。
_PRESUB_KANJI_MAP: "dict[str, str] | None" = None
_PRESUB_KANJI_RE: "re.Pattern | None" = None


def _load_presub() -> None:
    from . import i18n as _i18n
    from . import config as _cfg
    global _PRESUB_NAME_MAP, _PRESUB_NAME_RE, _PRESUB_HF_MAP, _PRESUB_HF_RE
    global _PRESUB_R18_MAP, _PRESUB_R18_RE, _PRESUB_KANJI_MAP, _PRESUB_KANJI_RE
    if _PRESUB_NAME_MAP is not None:
        return
    _i18n._load_name_glossary()
    _i18n._load_high_freq_glossary()
    _PRESUB_NAME_MAP = _i18n._GLOSSARY_NORM or {}
    _PRESUB_NAME_RE = _i18n._NAME_RE
    _PRESUB_HF_MAP = getattr(_i18n, "_HF_SUB_MAP", None) or {}
    _PRESUB_HF_RE = getattr(_i18n, "_HF_SUB_RE", None)
    # 纯汉字术语层（见 _PRESUB_KANJI_MAP 注释）：直接从 high_freq.yaml 取「不含任何假名」的条目。
    # i18n 侧的子串层刻意不含它们（渲染期会误改中文），这里单独建一份只给送翻用。
    try:
        hfp = _cfg.ROOT / "glossary" / "high_freq.yaml"
        if hfp.exists():
            hfd = (yaml.safe_load(hfp.read_text(encoding="utf-8")) or {}).get("high_freq") or {}
            KANA_ANY = re.compile(r"[\u3041-\u309f\u30a1-\u30fa\u30fc\uff66-\uff9f]")
            kj = {k: v for k, v in hfd.items()
                  if isinstance(k, str) and isinstance(v, str) and k and k != v
                  and not KANA_ANY.search(k)
                  # ⚠️ 必须排除**单字**键：high_freq 里有 217 个单字条目（面→表面、表→表格、
                  #    話→剧情、乳→乳房…），它们是分词碎片，做子串替换会命中任何含该字的词
                  #    ——实测 `ページ`→`页面` 之后，单字 `面` 又把「页面」改成「页表面」。
                  #    i18n 侧的渲染子串层同样刻意不含纯汉字/碎片键，这里保持一致（≥2 字）。
                  and len(k) >= 2}
            if kj:
                _PRESUB_KANJI_MAP = kj
                _PRESUB_KANJI_RE = re.compile(
                    "|".join(re.escape(k) for k in sorted(kj, key=len, reverse=True)))
    except Exception as e:
        print(f"[gtrans] 加载汉字术语层失败：{e}", file=sys.stderr)
    # R18 专用词表（glossary/r18.yaml）并入预替换子串层：R18 术语预替换，
    # 正常文本不含 R18 词（longest-match 安全），故不影响全站。
    r18p = _cfg.ROOT / "glossary" / "r18.yaml"
    if r18p.exists():
        try:
            r18 = yaml.safe_load(r18p.read_text(encoding="utf-8")) or {}
            r18d = r18.get("r18", {}) or {}
            r18_items = [(k, v) for k, v in r18d.items() if k and v and k != v]
            if r18_items:
                # ⚠️ 必须取 key 字符串列表：r18_items 是 (key, value) 元组列表，
                # 直接 sorted 得到的是元组列表，re.escape(tuple) 会抛
                # 「decoding to str: need a bytes-like object, tuple found」，
                # 被外层 except 吞掉后 R18 预替换静默失效（历史 bug）。
                r18_keys = sorted((k for k, _ in r18_items), key=len, reverse=True)
                _PRESUB_R18_MAP = dict(r18_items)
                _PRESUB_R18_RE = re.compile("|".join(re.escape(k) for k in r18_keys))
        except Exception as e:
            print(f"[gtrans] 加载 r18.yaml 失败：{e}", file=sys.stderr)


def pre_substitute(ja: str) -> str:
    """翻译前：把日文原文里的固定译法术语替换成中文（names 专名 + high_freq 子串层 + r18 专用层）。

    三步：① names.yaml 专名整词精确替换（如 トキサダ→时贞）；
         ② high_freq.yaml 含假名子串替换（如 レイド→突袭战）；
         ③ r18.yaml R18 术语子串替换（如 乳首→乳头）。
    只替换正文内容，不影响 `[id]` 标记与 `⏎` 换行标记。无术语时原样返回。
    """
    from . import i18n as _i18n
    _load_presub()
    if _PRESUB_NAME_RE is not None and _PRESUB_NAME_MAP:
        ja = _PRESUB_NAME_RE.sub(
            lambda m: _PRESUB_NAME_MAP.get(_i18n._norm(m.group(0)), m.group(0)), ja)
    if _PRESUB_KANJI_RE is not None and _PRESUB_KANJI_MAP:
        # 汉字术语层**必须最先跑**（专名之后、其它层之前）：它替换的键是纯汉字，
        # 若放在 HF/R18 层之后，就可能改到前面刚生成的中文（实测单字 `面` 把
        # 「页面」改成「页表面」）。在纯日文原文上做子串替换才是安全的。
        ja = _PRESUB_KANJI_RE.sub(
            lambda m: _PRESUB_KANJI_MAP.get(m.group(0), m.group(0)), ja)
    if _PRESUB_HF_RE is not None and _PRESUB_HF_MAP:
        ja = _PRESUB_HF_RE.sub(
            lambda m: _sub_word_bounded(m, _PRESUB_HF_MAP), ja)
    if _PRESUB_R18_RE is not None and _PRESUB_R18_MAP:
        ja = _PRESUB_R18_RE.sub(
            lambda m: _sub_word_bounded(m, _PRESUB_R18_MAP), ja)
    return ja


# 片假名（含半角）字符类 —— 用于「片假名词整词命中」判定
_KATA_CH = r"\u30a1-\u30fa\u30fc\uff66-\uff9f"
_KATA_RE = re.compile(f"[{_KATA_CH}]")


def _sub_word_bounded(m, mp: "dict[str, str]") -> str:
    """子串层替换：**片假名键必须整词命中**，否则原样返回。

    为什么（实测事故）：high_freq 的子串层里有一批短片假名词（ネット→网络、ガール…），
    它们会命中在**专名内部**，把没登记的新角色名撕成垃圾，再喂给谷歌就会翻出更离谱的东西：

        'コメント/ビートマジカル・マジック/' → '评论/彼特真的カル・真的ック/'   ← 名字被拆烂
        'コメント/閃忍ホーネット/'          → '评论/閃忍ホー网络/'           ← ホーネット 里的 ネット 被替
        'コメント/バニーガールゲッカ/'       → '评论/兔女郎ガール月华/'

    规则：键以片假名开头时，若其**紧邻字符也是片假名**，说明它只是某个片假名串的一部分
    （日语里片假名词通常被非片假名字符包围），此时不替换 —— 让整串交给谷歌/专名表处理。
    非片假名键（汉字/平假名词，如 攻撃→攻击、レイド 除外）行为不变。
    """
    key = m.group(0)
    if _KATA_RE.match(key[0]):
        s = m.string
        i, j = m.start(), m.end()
        if i > 0 and _KATA_RE.match(s[i - 1]):
            return key
        if j < len(s) and _KATA_RE.match(s[j]):
            return key
    return mp.get(key, key)


def translate_todo_file(path: str | Path, src: str = "ja", tgt: str = "zh-CN",
                        out_path: str | Path | None = None,
                        progress: bool = True,
                        pre_substitute_terms: bool = True) -> Path:
    """翻译一个待译清单文件，产出 `<stem>_translated.txt`。

    严格保留非条目行（`#` 注释 / 提示词 / `===A===` 分隔符），
    只翻译 `[id] 正文` 的正文部分并原样回写 `[id] 译文`。
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"待译文件不存在：{p}")
    if out_path is None:
        stem = p.stem
        if stem.endswith("_translated"):
            raise ValueError(f"这已经是译文文件，拒绝重复翻译：{p.name}")
        out = p.with_name(f"{stem}_translated.txt")
    else:
        out = Path(out_path)

    raw_lines = p.read_text(encoding="utf-8").splitlines()
    tags: list[str | None] = []
    payload: list[str] = []
    for ln in raw_lines:
        m = _ENTRY_RE.match(ln)
        if m and not _SEP_RE.match(ln):
            tags.append(m.group(1))
            payload.append(m.group(2))
        else:
            tags.append(None)
            payload.append(ln)

    idxs = [i for i, tg in enumerate(tags) if tg is not None]
    if not idxs:
        print(f"[gtrans] {p.name}：无 [id] 条目行，跳过")
        out.write_text("\n".join(raw_lines) + "\n", encoding="utf-8")
        return out

    if progress:
        chars = sum(len(payload[i]) for i in idxs)
        print(f"[gtrans] {p.name}：{len(idxs)} 条 / {chars} 字符 → 谷歌翻译")

    # 翻译前处理（2026-09-27 调优：默认改为**占位符保护** ✓）
    # 旧做法 pre_substitute 把术语**就地换成中文** ✗ → 送进谷歌的是中日混合语，据此乱翻 ✗✗：
    #     掩护が发动不コンテンツなので… → 「由于封面未激活，唯一可行的做法是避免闪光灯并降低价格」✗✗
    #     眩晕抗性降低 一覧        → 「抗眩光低血糖症列表」✗✗
    # 新做法：把专名/术语挖成 `[[i]]`（日文保持完整 ✓）→ 翻译 → 还原成词表中文 ✓。
    # 金标准实测（tools/_dev/mt_tune.py，368 条人工精校译文）：术语命中 34.1% → **97.6%** ✓、
    # chrF3 0.212 → **0.253** ✓。仍保留 `ESCAH_GTRANS_PRESUB=1` 可切回旧行为以便回退 ✓。
    # 仅影响送翻内容，不改 [id] 标记与 ⏎；回填仍用原始日文对齐，铁律不受影响。
    tables = None
    if pre_substitute_terms and os.environ.get("ESCAH_GTRANS_PRESUB", "0") != "1":
        try:
            ja_src, tables = [], []
            for i in idxs:
                p, spans = protect_ja(payload[i])
                ja_src.append(p)
                tables.append(spans)
        except Exception as e:  # noqa: BLE001 保护失败则退回旧路径，绝不阻断翻译
            print(f"[gtrans] 占位符保护失败，退回预替换：{e}", file=sys.stderr)
            ja_src, tables = [pre_substitute(payload[i]) for i in idxs], None
    elif pre_substitute_terms:
        ja_src = [pre_substitute(payload[i]) for i in idxs]
    else:
        ja_src = [payload[i] for i in idxs]
    zh_list = translate_lines(ja_src, src=src, tgt=tgt, progress=progress)
    if tables:
        zh_list = [restore_zh(z, sp)[0] for z, sp in zip(zh_list, tables)]

    # 冗余层4：条数必须与请求完全一致，否则拒绝写出（防止错位回填污染真值）
    if len(zh_list) != len(idxs):
        raise GTransDataError(
            f"{p.name}：译文条数 {len(zh_list)} != 待译条数 {len(idxs)}，拒绝写出")

    # 失败报告必须记录「未经词表预替换」的原文：ja_src 里的专名已被换成中文，
    # 直接拿它生成报告会得到中日混合体，人工据此补译会被误导。
    ja_orig = {i: payload[i] for i in idxs}

    fallback = 0
    failed: list[tuple[str, str]] = []  # (id, 原文ja) 翻译失败的条目
    empty_ids: set[str] = set()         # 译文被留空的条目 id（结构校验时豁免 ⏎ 数量）
    for i, ja, zh in zip(idxs, ja_src, zh_list):
        # 空译文/纯空白/译文仍含日文（机翻失败把原文退回）→ 视为翻译失败：
        # 不再静默写回日文原文（否则 fill 会把日文当译文污染 i18n 真值），
        # 而是留空（fill 跳过空 zh），并记录到失败报告。
        if not zh or not zh.strip() or _KANA_RE.search(zh):
            tid = tags[i] if tags[i] is not None else f"#{i}"
            failed.append((tid, ja_orig[i]))
            payload[i] = ""      # 留空，不写日文原文
            empty_ids.add(tid)
            fallback += 1
        else:
            payload[i] = zh

    result: list[str] = []
    for tg, body in zip(tags, payload):
        result.append(f"[{tg}] {body}" if tg is not None else body)

    # 冗余层5：写出前整体自检——行数、每行标签、⏎ 数量三项必须与原文严格一致
    # 传入 empty_ids：翻译失败而留空的行豁免 ⏎ 数量校验，否则全卷会被连带丢弃。
    errs = _validate_pair(raw_lines, result, allow_empty=empty_ids)
    if errs:
        for msg in errs[:10]:
            print(f"[gtrans] 校验失败：{msg}", file=sys.stderr)
        raise GTransDataError(
            f"{p.name}：译文与待译文件结构不一致（{len(errs)} 处），已拒绝写出，原文件未受影响")

    out.write_text("\n".join(result) + "\n", encoding="utf-8")

    # 翻译失败必须显式报告，绝不静默吞掉：
    if failed:
        rep = out.with_name(out.stem.replace("_translated", "") + "_translate_failed.txt")
        with rep.open("w", encoding="utf-8") as rf:
            rf.write(f"# 翻译失败报告（{out.name}）：共 {len(failed)} 条未译出\n")
            rf.write("# 这些条目译文留空，fill 会跳过；请人工补译或重跑 gtrans\n")
            for tid, ja in failed:
                rf.write(f"[{tid}] {ja}\n")
        print(f"[gtrans][警告] {out.name} 有 {len(failed)} 条翻译失败，已写出报告：{rep.name}",
              file=sys.stderr)

    remain = sum(1 for i in idxs if _KANA_RE.search(payload[i]))
    extra = f"，失败 {fallback} 条（见报告）" if fallback else ""
    print(f"[gtrans] 写出 {out.name}（{len(idxs)} 条，残留假名 {remain} 条{extra}）"
          f" [结构校验通过]")
    return out


def _validate_pair(src_lines: Sequence[str], dst_lines: Sequence[str],
                   allow_empty: "set[str] | None" = None) -> list[str]:
    """校验译文文件与待译文件结构严格一致，返回问题描述列表（空=通过）。

    检查三项（任一不符都会导致 fill 错位或渲染断句）：
      ① 总行数一致；
      ② 每行「是否条目行 + 条目 id」一致，非条目行（`#`/提示词/`===X===`）内容原样；
      ③ 条目行内 `⏎` 数量一致（换行对齐铁律）。

    `allow_empty`：翻译失败、译文被有意留空的条目 id 集合，这些行豁免第 ③ 项。
    留空是刻意为之（避免把日文原文当译文写回而污染 i18n 真值），但留空会让该行
    ⏎ 数从 N 变成 0；若因此判为结构不一致，会 raise 并**连同失败报告一起丢弃整卷**
    ——即卷内 1 条失败导致成百上千条成功译文全部作废（历史 bug）。
    """
    allow_empty = allow_empty or set()
    errs: list[str] = []
    if len(src_lines) != len(dst_lines):
        errs.append(f"行数不一致 {len(src_lines)} → {len(dst_lines)}")
        return errs
    for n, (a, b) in enumerate(zip(src_lines, dst_lines), 1):
        ma, mb = _ENTRY_RE.match(a), _ENTRY_RE.match(b)
        sa = bool(ma) and not _SEP_RE.match(a)
        sb = bool(mb) and not _SEP_RE.match(b)
        if sa != sb:
            errs.append(f"第{n}行条目属性不一致（{'条目' if sa else '非条目'}→"
                        f"{'条目' if sb else '非条目'}）")
            continue
        if not sa:
            if a != b:
                errs.append(f"第{n}行非条目行被改写：{a[:30]!r} → {b[:30]!r}")
            continue
        if ma.group(1) != mb.group(1):
            errs.append(f"第{n}行 id 不一致 [{ma.group(1)}] → [{mb.group(1)}]")
            continue
        # 翻译失败留空行：⏎ 数量必然为 0，属预期行为，豁免校验（否则整卷被丢弃）。
        if ma.group(1) in allow_empty and not mb.group(2).strip():
            continue
        ca, cb = ma.group(2).count(BR_EXPORT), mb.group(2).count(BR_EXPORT)
        if ca != cb:
            errs.append(f"第{n}行[{ma.group(1)}] 换行数 {ca} → {cb}")
    return errs


def translate_todo_dir(directory: str | Path, pattern: str = "*.txt",
                       src: str = "ja", tgt: str = "zh-CN",
                       skip_existing: bool = True,
                       pre_substitute_terms: bool = True) -> list[Path]:
    """批量翻译目录下所有待译清单（跳过 `*_translated.txt` 与 `*_index.json`）。"""
    d = Path(directory)
    if not d.exists():
        print(f"[gtrans] 目录不存在，跳过：{d}")
        return []
    outs: list[Path] = []
    failed: list[str] = []
    for f in sorted(d.glob(pattern)):
        if f.stem.endswith("_translated"):
            continue
        # 失败报告不是待译清单：`--force` 曾把它当清单翻一遍，产出
        # `<stem>_translate_failed_translated.txt` 这种垃圾文件（实测）。
        if "_translate_failed" in f.stem or f.stem.endswith("_failed"):
            continue
        target = f.with_name(f"{f.stem}_translated.txt")
        # 上一轮**有失败条目**的卷必须重译，不能因为「已有译文文件」就跳过：
        # 失败条目在译文里是**空行**（gtrans 刻意不写日文原文，避免污染真值），
        # 若一刀切跳过，这些条目就永远补不上（实测：5 条 PukiWiki 提示语就这么卡住，
        # 必须人工删掉 <stem>_translated.txt 才会重试）。有失败报告 → 视为未完成。
        failed_report = f.with_name(f"{f.stem}_translate_failed.txt")
        if skip_existing and target.exists() and not failed_report.exists():
            print(f"[gtrans] 已有译文，跳过：{f.name}")
            outs.append(target)
            continue
        if skip_existing and target.exists() and failed_report.exists():
            print(f"[gtrans] 上轮有失败条目，重译：{f.name}")
        # 无 [id] 条目的文件直接跳过，不产出译文卷：目录里除清单外还放着**代码依赖的源文件**
        # （如 build_phrases.py 的 HF 词表输入 `_highfreq_20260903.txt`），原实现会照样写一份
        # `<stem>_translated.txt` 完整副本（纯垃圾，实测踩到）。
        if not any(_ENTRY_RE.match(ln) and not _SEP_RE.match(ln)
                   for ln in f.read_text(encoding="utf-8", errors="replace").splitlines()):
            print(f"[gtrans] 无 [id] 条目行，跳过（不产出译文卷）：{f.name}")
            continue
        # 单卷重试：瞬时错误（限流/连接重置）不该把整卷判死 —— 实测 74 卷里就死过 1 卷，
        # 手工重跑即通过。只有**确定性**的结构错误（GTransDataError）才立即放弃。
        for attempt in range(FILE_RETRY):
            try:
                outs.append(translate_todo_file(f, src=src, tgt=tgt,
                                                 pre_substitute_terms=pre_substitute_terms))
                break
            except GTransDataError as e:
                failed.append(f.name)
                print(f"[gtrans] 结构错误，放弃该卷 {f.name}：{e}", file=sys.stderr)
                break
            except Exception as e:  # noqa: BLE001
                if attempt < FILE_RETRY - 1:
                    wait = RETRY_BASE_SLEEP * (2 ** (attempt + 1))
                    print(f"[gtrans] {f.name} 第 {attempt + 1} 次失败（{e}）；"
                          f"{wait:.1f}s 后重试整卷", file=sys.stderr)
                    time.sleep(wait)
                else:
                    # 单卷失败不影响其它卷：该卷不产出译文文件，fill 阶段自然跳过
                    failed.append(f.name)
                    print(f"[gtrans] 翻译失败 {f.name}：{e}", file=sys.stderr)
    print(f"[gtrans] 目录完成：{len(outs)} 个译文文件"
          + (f"，失败 {len(failed)} 卷：{', '.join(failed)}" if failed else ""))
    print(_stats_line())
    return outs


def _stats_line() -> str:
    """收尾统计：请求数 / 被限流次数 / 重试次数 / 当前批间间隔 / 均速。

    用途：一眼看出「是否需要调参」——
      · limited > 0 → 间隔仍偏激进，加大 --interval；
      · 均速远低于 1/interval → 瓶颈在网络往返而非限速，继续加大间隔没有收益。
    """
    req = int(_STATS["req"])
    t0 = _STATS.get("t0") or 0.0
    el = (time.monotonic() - t0) if t0 else 0.0
    rate = (req / el) if el > 0 else 0.0
    return (f"[gtrans] 统计：请求 {req} 次，被限流 {int(_STATS['limited'])} 次，"
            f"重试 {int(_STATS['retry'])} 次，耗时 {el:.1f}s（均速 {rate:.2f} req/s），"
            f"当前批间间隔 {_THROTTLE.cur:.2f}s（基准 {_THROTTLE.base:.2f}s）")


# ---------------------------------------------------------------------------
# 手动执行入口
# ---------------------------------------------------------------------------
def main(argv: Iterable[str] | None = None) -> int:
    import argparse
    # Windows 控制台 stdout/stderr 默认 GBK，遇到日文/中文会 UnicodeEncodeError。
    # 强制 UTF-8，避免翻译进度打印崩溃。
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        prog="python -m escah_pipeline.gtrans",
        description="谷歌免费翻译：把待译清单 <file>.txt 翻成 <file>_translated.txt")
    ap.add_argument("paths", nargs="+", help="待译文件或目录（目录则翻其下所有 *.txt）")
    ap.add_argument("--src", default="ja", help="源语言（默认 ja）")
    ap.add_argument("--tgt", default="zh-CN", help="目标语言（默认 zh-CN）")
    ap.add_argument("--force", action="store_true", help="目录模式下覆盖已有译文")
    ap.add_argument("--no-presub", dest="pre_substitute_terms", action="store_false",
                    help="关闭翻译前词表预替换（默认开启：送翻前把 names.yaml 专名术语替换为中文）")
    ap.add_argument("--text", action="store_true", help="把 paths 当作待翻译文本直接翻译并打印")
    ap.add_argument("--interval", type=float, default=None,
                    help=f"批间最小间隔（秒，默认 {REQ_INTERVAL:g}；环境变量 ESCAH_GTRANS_INTERVAL）")
    ap.add_argument("--rate", type=int, default=None,
                    help=f"每分钟最大请求数（默认 {RATE_PER_MIN}；被限流时优先加大间隔而非此值）")
    args = ap.parse_args(list(argv) if argv is not None else None)

    # 命令行 > 环境变量 > 代码默认。注意同时改「基准」与「当前」间隔，
    # 否则自适应回落会把 --interval 的设定慢慢拉回代码默认值。
    if args.interval is not None:
        _THROTTLE.base = _THROTTLE.cur = max(0.0, args.interval)
    if args.rate is not None:
        _RATELIMITER.per_min = max(1, args.rate)

    if args.text:
        for t in args.paths:
            print(translate_text(t, src=args.src, tgt=args.tgt))
        return 0

    fail = 0
    for raw in args.paths:
        p = Path(raw)
        if p.is_dir():
            translate_todo_dir(p, src=args.src, tgt=args.tgt,
                               skip_existing=not args.force,
                               pre_substitute_terms=args.pre_substitute_terms)
        elif p.exists():
            # 单文件同样给一次重试机会：瞬时错误（限流/连接重置）不该要求用户手工重跑。
            for attempt in range(FILE_RETRY):
                try:
                    translate_todo_file(p, src=args.src, tgt=args.tgt,
                                        pre_substitute_terms=args.pre_substitute_terms)
                    break
                except GTransDataError as e:
                    print(f"[gtrans] 结构错误 {p}：{e}", file=sys.stderr)
                    fail = 1
                    break
                except Exception as e:  # noqa: BLE001
                    if attempt < FILE_RETRY - 1:
                        wait = RETRY_BASE_SLEEP * (2 ** (attempt + 1))
                        print(f"[gtrans] {p.name} 第 {attempt + 1} 次失败（{e}）；"
                              f"{wait:.1f}s 后重试", file=sys.stderr)
                        time.sleep(wait)
                    else:
                        print(f"[gtrans] 失败 {p}：{e}", file=sys.stderr)
                        fail = 1
        else:
            print(f"[gtrans] 路径不存在：{p}", file=sys.stderr)
            fail = 1
    # 目录模式由 translate_todo_dir 收尾打印统计；这里只补「纯单文件」调用的情况，
    # 否则同一次运行会看到两行一模一样的统计（实测）。
    if not any(Path(raw).is_dir() for raw in args.paths):
        print(_stats_line())
    return fail


# ---------------------------------------------------------------------------
# 占位符保护翻译（2026-09-27 新增；**默认不启用**，先用探针实测再决定）
# ---------------------------------------------------------------------------
# 为什么需要（实测证据）：
#   旧路径 `pre_substitute` 把术语**就地替换成中文** ✗，于是送进谷歌的是**中日混合语**：
#       20秒間、自軍フィールドの命中50アップ → 20秒間、我方场地の命中50提升 ✗
#   谷歌对混合输入会产出离谱译文 ✗✗：
#       掩护が发动不コンテンツなので闪避降低しか定位がなく… → 「由于封面未激活，唯一可行的
#       做法是避免闪光灯并降低价格…」✗✗  ／ 眩晕抗性降低 一覧 → 「抗眩光低血糖症列表」✗✗
#   本函数改为：**先用占位符把专名/术语挖走**（日文保持完整 ✓）→ 翻译 → 再把占位符还原成
#   词表中文 ✓。既强制了术语，又让谷歌看到可读日语。
_PROTECT_CACHE: "dict[str, str] | None" = None
_PROTECT_RE: "re.Pattern | None" = None
_SENT_RE = re.compile(r"\[\[\s*(\d+)\s*\]\]")
# 平假名：用来把「活用短语」（発動しない / させて）从保护名单里筛掉 ✗
_HIRA_RE = re.compile(r"[\u3041-\u3096]")


def _load_protect_terms() -> None:
    global _PROTECT_CACHE, _PROTECT_RE
    if _PROTECT_CACHE is not None:
        return
    terms: "dict[str, str]" = {}
    import yaml as _yaml
    from . import config as _cfg          # 模块内其它函数也是函数内导入（避免别名作用域问题）
    # ⚠️ 只取**词汇级**词表（专名 + 术语）。high_freq.yaml 整体纳入会把句子切碎 ✗ ——
    #    它含大量**活用短语/从句**（`発動しない`、`させて`…），挖成占位符后实测整句退化成
    #    「由于 掩护 是 发动不 内容，因此只有 闪避降低 定位…」✗。
    #    2026-09-27 调优：改为**按形态过滤后纳入** —— 只保护「不含平假名的词汇项」
    #    （片假名/汉字名词 ✓，如 `ダウン`、`コンテンツ`），活用形含平假名必被排除 ✗。
    #    实测（mt_tune.py）：术语命中率与 chrF3 显著提升，且不再切碎句子 ✓。
    for rel in ("names.yaml", "terms.yaml"):
        p = _cfg.ROOT / "glossary" / rel
        if not p.exists():
            continue
        try:
            data = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001 词表坏了不应阻断翻译
            continue
        stack = [data]
        flat: "dict[str, str]" = {}
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                for k, v in cur.items():
                    if isinstance(v, dict):
                        stack.append(v)
                    elif isinstance(v, str):
                        flat[str(k)] = v
        for ja, zh in flat.items():
            ja_s, zh_s = ja.strip(), zh.strip()
            if len(ja_s) >= 2 and zh_s and ja_s != zh_s:
                terms.setdefault(ja_s, zh_s)
    # high_freq.yaml：**只取不含平假名的词汇项**（排除活用短语，见上方注释）。
    # 默认**关闭** ✗ —— 200 条金标准样本 A/B（mt_tune.py）三种口径实测：
    #     仅 names+terms      chrF3 0.234 ｜术语命中 88.8%   ← 既定默认（无可见劣化 ✓）
    #     + HF（≥2 字）        chrF3 0.232 ｜术语命中 92.3%   ← 术语略好，但短片段会被译坏 ✗✗
    #     + HF（≥4 字）        chrF3 0.229 ｜术语命中 86.7%   ← 两项都更差 ✗
    # 关键反例：保护 `ダメージ` 后，`敵一列に魔法4倍ダメージ` → 「对一排敌人**施放 4 号法术**倍伤害」✗✗
    # —— 标记过密时谷歌会把占位符当成专名来猜 ✗。**可见的劣化比术语一致更严重**，故默认关 ✓。
    # 需要时可用 `ESCAH_GTRANS_PROTECT_HF=1` 开启复测；机制术语（场地/命中/眩晕…）请**逐条**
    # 补进 terms.yaml: inline_terms（受控 ✓），而不是整层纳入 ✗。
    hf_path = _cfg.ROOT / "glossary" / "high_freq.yaml"
    if os.environ.get("ESCAH_GTRANS_PROTECT_HF", "0") == "1" and hf_path.exists():
        try:
            hf_data = _yaml.safe_load(hf_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            hf_data = {}
        for ja, zh in (hf_data.get("high_freq") or {}).items():
            ja_s, zh_s = str(ja).strip(), str(zh).strip()
            # 长度门槛 ≥4（2026-09-27 调优）：2 字词被挖成标记后，谷歌会在**短片段**上瞎猜
            # —— 实测 `敵一列に魔法4倍ダメージ` 因 `魔法` 被保护而译成
            # 「对一排敌人**施放 4 号法术**倍伤害」✗✗。≥4 字多为真正的术语（フィールド 等）✓。
            if (4 <= len(ja_s) <= 16 and zh_s and ja_s != zh_s
                    and not _HIRA_RE.search(ja_s)):
                terms.setdefault(ja_s, zh_s)
    keys = sorted(terms, key=len, reverse=True)
    _PROTECT_CACHE = {k: terms[k] for k in keys}
    _PROTECT_RE = re.compile("|".join(re.escape(k) for k in keys)) if keys else None


def protect_ja(ja: str) -> "tuple[str, list[str]]":
    """把专名/术语换成 `[[i]]` 占位符，返回 (待翻文本, 还原表)。"""
    _load_protect_terms()
    if not _PROTECT_RE or not _PROTECT_CACHE:
        return ja, []
    spans: "list[str]" = []

    def _rep(m):
        zh = _PROTECT_CACHE.get(m.group(0))
        if not zh:
            return m.group(0)
        spans.append(zh)
        return f"[[{len(spans) - 1}]]"

    return _PROTECT_RE.sub(_rep, ja), spans


def restore_zh(zh: str, spans: "list[str]") -> "tuple[str, int]":
    """把占位符还原成词表中文；返回 (结果, 未还原的占位符数)。

    容错与整形（2026-09-27 调优）：
      · 谷歌会把标记挪动/加空格（`[[ 0 ]]`）、偶尔转成全角（`［［0］］`）→ 一并容忍 ✓
      · 还原后**吞掉紧邻的空格**（仅当两侧都是中日字符时）—— 否则中文里会出现
        `则不会 触发 技能` 这类空格 ✗（实测「如果目标中存在类似的 效果，则会复制 效果。」✗）
    """
    if not spans:
        return zh, 0
    missing = 0
    for i, target in enumerate(spans):
        num = r"[\[［]\s*[\[［]\s*%d\s*[\]］]\s*[\]］]" % i
        pat = re.compile(num)
        if not pat.search(zh):
            missing += 1
            continue
        cjk = r"[\u3000-\u9fff\uff00-\uffef]"
        tight = re.compile(r"(%s)?\s*(%s)\s*(%s)?" % (cjk, num, cjk))

        def _rep(m):
            return (m.group(1) or "") + target + (m.group(3) or "")

        zh = tight.sub(_rep, zh)
        zh = pat.sub(lambda _m: target, zh)      # 兜底：行首/行尾等无邻字符的情况
    return zh, missing


def translate_text_protected(ja: str, src: str = "ja", tgt: str = "zh-CN") -> str:
    """占位符保护版单条翻译（供探针/后续切换使用）。"""
    protected, spans = protect_ja(ja)
    out = translate_text(protected, src=src, tgt=tgt)
    out, _missing = restore_zh(out, spans)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
