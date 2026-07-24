---
name: HY3 API 加速翻译（两阶段）
overview: 接入腾讯混元 HY3（OpenAI 兼容）把 ESCH 全站残留日文「一次性」翻译完：先用 tools/llm_patch.py 收集全站待译文本（标签间纯文本片段，去重、排除 PROTECTED 页与角色名/声优/画师行），批量调 HY3 翻译，译文落盘成 tools/_llm_translations.json（不注入词表）；后续再单独做注入 JA2ZH + char_zh.py + sync-site + build。
todos:
  - id: scaffold
    content: 新建 tools/llm_patch.py（硬编码 HY3 base_url/model、读 HY3_API_KEY、collect/translate/inject 三子命令与 call_hy3），并把 _llm_*.json 加入 .gitignore
    status: completed
  - id: collect
    content: 实现并运行 collect：扫描 ja HTML 与角色 JSON 残余片段去重，写 _llm_source.json（按频次降序）
    status: completed
    dependencies:
      - scaffold
  - id: translate-impl
    content: 实现 translate：分批调 HY3、JSON 解析、断点续译、重试退避，写 _llm_translations.json
    status: completed
    dependencies:
      - scaffold
  - id: translate-run
    content: 运行 translate 全量翻译落盘（不注入），核验覆盖率与抽样质量
    status: completed
    dependencies:
      - collect
      - translate-impl
---

## 用户需求

- 接入 HY3（腾讯混元 Hy3，OpenAI 兼容）API 加速 ESCH 站点日文→中文翻译。
- 本阶段只做“整理 + 翻译落盘”：收集全站待译日文片段，批量调 HY3 翻译，结果写入文件，**暂不注入** JA2ZH 词表。
- HY3 配置（base_url / model）硬编码；API Key 从环境变量 `HY3_API_KEY` 读取，不入库、不提交。

## 产品概述

ESCH 中日双语镜像站翻译工程的 API 加速前置环节：把站点全部残余日文（集中页 + 角色页散文长尾，预计 2–3 万条唯一文本）整理为去重清单，一次性喂给 HY3 翻译，产出可复用的译文字典文件，供后续注入与站点构建使用。

## 核心功能

- 收集：扫描 `data/parsed/ja/*.html`（跳过 PROTECTED 页）与 `data/parsed/characters/*.json`（跳过人名行），提取 `patch()` 后仍含假名的文本片段，去重并统计出现次数与出处。
- 翻译：分批调 HY3 `/v1/chat/completions`，将日文片段译为简体中文，支持断点续译与失败重试。
- 落盘：译文写入 `tools/_llm_translations.json`（含 ja/zh/ok/note），本阶段不写入 JA2ZH。

## 技术栈

- 语言：Python 3（仅标准库 `urllib` / `json` / `re` / `html` / `unicodedata` / `pathlib` / `argparse` / `time` / `sys`），**无新增依赖**。
- 复用现有：`tools/zh_patch.py` 的 `patch()`、`residual_kana()`、`PROTECTED` 判定残余片段；沿用 `_freq_chars.py` 的标签剥离与假名识别正则。
- HY3 接入：OpenAI 兼容 Chat Completions，base_url=`https://tokenhub.tencentmaas.com/v1`，model=`hy3`（或 `hy3-preview`），鉴权 `Authorization: Bearer <HY3_API_KEY>`。

## 实现方法

- **残余识别**：HTML 用 `tag.sub("\n", text)` 去标签后按行切分（`_freq_chars.py` 同款），JSON 取 tr 单元格 `t` 字段；对每段先 `patch()` 再 `residual_kana()`，仍含假名且非 PROTECTED/非人名行则收集。因片段为标签间纯文本，作为 JA2ZH 精确 key 时 `patch()` 的 `text.replace(ja,zh)` 能命中，故**无需 API 保留标签**。
- **收集去重**：以片段原文为 key，累计 `count`（全站出现次数）与 `where`（出处文件），按 `count` 降序排序，使高频样板句优先翻译、最大化覆盖率；输出 `tools/_llm_source.json`。
- **批量翻译**：每批 N 条（默认 20）拼成一个编号列表，要求模型按序返回 JSON 数组；用 `temperature=0` 保证确定性，system 提示约束游戏/wiki 文本翻译规则（仅输出译文、保留「」『』（）与数字、术语一致）。解析失败则按整批重试一次，仍失败则跳过该批（不落盘，留待续跑）。
- **断点续译**：`translate` 加载已有 `_llm_translations.json`（字典，key=ja），跳过已译条目；每批成功后增量写盘，中断重跑只补未完成项，成本可控。
- **阶段二分留接口**：`inject` 子命令预留，后续复用 `_addchars_*.py` 的 `ast` 去重 + 锚点插入模式写入 JA2ZH，并校验标签完整性；本阶段不实现、不调用。

## 实现注意事项

- **秘钥安全**：`HY3_API_KEY` 仅从环境变量读取，绝不写入任何文件或提交；`_llm_source.json` / `_llm_translations.json` 为中间产物，加入 `.gitignore` 避免仓库膨胀与误提交。
- **性能**：2–3 万唯一片段 ÷ 批 20 ≈ 1000–1500 次请求；采用顺序批处理 + 指数退避（429/5xx），吞吐约 1–3s/批，预计 30–75 分钟跑完；续译机制保证中断不丢进度。
- **质量兜底**：翻译仅落盘不注入，后续人工/自动核对后再入库；高频优先排序确保即便中途停止也先覆盖最大收益片段。
- **运行前置**：PowerShell 下先 `$env:HY3_API_KEY="..."` 再运行 `translate`。

## 架构设计

新增独立工具 `tools/llm_patch.py`，与 `zh_patch.py` / `_addchars_*.py` 并列，本阶段**不修改** `zh_patch.py`。数据契约：扫描产物 → `_llm_source.json` → HY3 → `_llm_translations.json`，后续 `inject` 再并入词表，保持现有“词表为确定性单一真源”的架构不变。

## 目录结构

- `tools/llm_patch.py` [NEW] 翻译加速工具。实现 `HY3_BASE_URL`/`HY3_MODEL` 常量、`call_hy3()`、`cmd_collect()`（扫 ja HTML+角色JSON 残余片段去重→`_llm_source.json`）、`cmd_translate()`（分批调 HY3、JSON 解析、断点续译、重试退避→`_llm_translations.json`）、`cmd_inject()`（阶段二预留，复用 `_addchars` 模式）。Key 从 `HY3_API_KEY` 读取。
- `tools/_llm_source.json` [NEW, 生成] 去重待译清单：条目含 `ja`/`count`/`where`，按 count 降序。加入 `.gitignore`。
- `tools/_llm_translations.json` [NEW, 生成] 译文库：`{ja: {zh, ok, note}}`，支持续译。加入 `.gitignore`。
- `.gitignore` [MODIFY] 追加 `tools/_llm_source.json` 与 `tools/_llm_translations.json`，避免提交中间产物与误带秘钥。

## 关键代码结构

```python
# tools/llm_patch.py
HY3_BASE_URL = "https://tokenhub.tencentmaas.com/v1"
HY3_MODEL = "hy3"                      # 或 "hy3-preview"
HY3_CHAT = HY3_BASE_URL + "/chat/completions"

def call_hy3(items: list[str], api_key: str) -> list[str] | None:
    """批量翻译；返回与 items 等长的译文列表，失败返回 None。"""

def cmd_collect() -> None:  ...   # 扫 ja HTML + 角色 JSON 残余片段去重 → _llm_source.json
def cmd_translate() -> None: ...  # 分批调 HY3、断点续译、重试退避 → _llm_translations.json
def cmd_inject() -> None:  ...    # 阶段二：复用 _addchars 模式注入 JA2ZH（本阶段不调用）
```