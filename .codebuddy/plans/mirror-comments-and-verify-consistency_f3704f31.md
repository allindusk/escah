---
name: mirror-comments-and-verify-consistency
overview: 修复解析器以保留原站页面底部的网友评论（含发送ID与发表时间），并构建全站一致性扫描脚本，核对 400+ 原站页面与镜像站内容是否一致，最后重跑应用链重建 dist。
todos:
  - id: write-scan
    content: 编写 tools/verify_consistency.py 全站一致性扫描（评论计数 + 文本相似度）
    status: completed
  - id: run-scan-baseline
    content: 运行扫描，定位原站与镜像的内容差异（评论缺失及其它静默丢弃）
    status: completed
    dependencies:
      - write-scan
  - id: fix-parser
    content: 修复 parser_puki.py::_remove_chrome 保留评论（移出 form、清理回复单选、保留 ID 与时间）
    status: completed
    dependencies:
      - run-scan-baseline
  - id: reparse
    content: 重跑 parse_all(force) 再生全部 ja 片段
    status: completed
    dependencies:
      - fix-parser
  - id: rescan
    content: 重跑扫描确认评论已镜像且无其它内容丢失
    status: completed
    dependencies:
      - reparse
  - id: rebuild
    content: 重跑 sync-site + build.mjs 重建 dist 上线评论
    status: completed
    dependencies:
      - rescan
---

## 用户需求

重新核对原站点（data/raw 快照，400+ 页面）与镜像站（data/parsed/ja 片段 → 站点）的内容是否一致，重点包括页面底部的网友评论；评论的发送 ID 与发表时间也必须一并镜像化。

## 产品概述

在不改变现有"快照→解析→词表替换→VitePress 构建"分层架构的前提下，修复解析器把评论误删的问题，并提供一个全站一致性扫描脚本，量化核对原站与镜像在正文与评论上的差异，最终把评论（含发送 ID、时间）随 ja 片段自动上线。

## 核心功能

- 评论镜像：保留原站 pcomment 插件渲染的评论列表（每条含正文、`[发送ID]`、`comment_date` 时间），移出被 decompose 的 `<form>`，并删除"提交新评论"表单、表情/颜色工具条等交互控件。
- 全站一致性核对：逐页比较原站 #body 与镜像片段的可见文本保真度，并专门统计每页评论条数（raw vs parsed），标记内容丢失页面。
- 应用链重建：重跑解析 → sync-site → build，使评论在 ja/zh 双语站上线（评论按日文透传，不翻译，符合"镜像"语义）。

## 技术栈

- 复用现有 Python 流水线：`pipeline/escah_pipeline/parser_puki.py`（BeautifulSoup + lxml 解析）、`config`/`registry`、`sitegen.py`（sync-site）、`site/build.mjs`（VitePress 编程式 build，detached 运行）。
- 新增独立脚本 `tools/verify_consistency.py`（标准库 + BeautifulSoup，无新依赖）。
- 无新增依赖、无新增密钥。运行期沿用 `PYTHONIOENCODING=utf-8` 防 Win GBK 崩溃。

## 实现方案

### 核心修复：保留评论（`parser_puki.py::_remove_chrome`）

- **问题根因**：`_remove_chrome` 对 `body.find_all(['form','input','button','select','textarea'])` 整体 `decompose()`，而评论 `<ul class="list1 list-indent1">` 整组嵌在 `<form action="./" method="post">` 内，导致评论列表被当作表单一并删除。
- **方案**：在 `_remove_chrome` 的通用 form 删除**之前**，先对 `div.pcomment` 做保留处理：

1. 取 `div.pcomment` 内 `form` 中的评论 `<ul>`（`ul.list1`，含嵌套回复 `ul.list2/3`），用 `form.insert_before(ul)` 将其移出 form；
2. 对每条 `<li class="pcmt">` 删除其内 `<input class="pcmt" type="radio" name="reply">`（回复选择器），保留正文文本、`[发送ID]` 与时间 `<span class="comment_date">`，并清掉内部空 `<span class="__plugin_new">`；
3. 再 `form.decompose()` 删掉包裹评论的空 form，并 `div#pcomment-form`（提交表单）`decompose()`；
4. 死链 `<p>最新の20件を表示しています <a>コメントページを参照</a></p>` 一并 `decompose()`（指向源站不存在的 `コメント/` 页）。

- **幂等性与安全**：该改动仅新增"先抢救评论再删表单"的前置步骤；原 `_remove_chrome` 的 `plugin=attach` 链接 unwrap 逻辑、`style/script` 删除均保持不变。评论保留在 ja 片段后，zh 片段由 `zh_patch.py` 生成（评论不在 JA2ZH 词表里）按日文透传，无需翻译。

### 全站一致性扫描（`tools/verify_consistency.py`）

- 遍历注册表每页：读取 `data/raw/<page>.html` 与 `data/parsed/ja/<slug>.html`。
- 评论核对：分别统计 raw `#body` 与 parsed 片段中 `li.pcmt` 数量，标记"raw 有评论但 parsed 为 0"的页面（即评论丢失）。
- 正文保真度：用 BeautifulSoup 提取两边可见文本（`get_text(strip=True, separator=' ')`，并先移除 `script/style/form` 内非评论文本与 `plugin=attach` 壳），归一化空白后计算 `difflib.SequenceMatcher` 相似度，标记相似度低于阈值（如 0.9）的页面供人工复核（链接改写只改 href/src、不改文本，不应拉低相似度）。
- 输出：控制台摘要 + `tools/_verify_report.txt`（按页面列出评论计数差与相似度，区分"评论缺失"与"其它内容缺失"两类）。

## 实现注意事项

- **顺序关键**：pcomment 抢救必须放在通用 form/input `decompose()` 之前，否则评论仍被删。
- **勿破坏既有约定**：`plugin=attach` 链接"含 img 则 unwrap、否则 decompose"、`style/script` 删除、`CHROME_LINK_RE` 编辑链接清理保持不变；改动后用扫描脚本交叉验证。
- **性能**：406 页用 lxml 解析，单次扫描秒级完成；`parse_all(force)` 已用 `ProcessPoolExecutor` 多进程，重跑全量片段约 11s，无需改动。
- **上线**：修复后必须 `parse_all(force)` 再生 ja 片段 → `python -m escah_pipeline.cli sync-site` → `cd site && node build.mjs build`（detached），否则 dist 仍是旧快照（无评论）。
- **回收站约定**：本次无文件删除需求，切勿误删 raw/parsed。

## 架构设计

完全复用现有"快照层 → 解析层(parser_puki) → 词表引擎(zh_patch) → 站点生成(sitegen) → VitePress(dist)"分层（以文件为契约）。本次仅在 `parser_puki` 做最小增强（保留评论），并新增一个独立扫描脚本，不引入新模块、不改组件。数据流向：
`data/raw → parser_puki(保留评论) → data/parsed/ja → sync-site(frag json) → MirrorContent.vue(v-html) → dist`。

## 目录结构

```
escah/
├── pipeline/escah_pipeline/
│   └── parser_puki.py        # [MODIFY] _remove_chrome 新增 pcomment 评论保留逻辑：
│                             #   评论 ul 移出 form、清理回复单选、保留 [ID] 与时间、
│                             #   删除提交表单与死链；通用 form 删除顺序后移。
├── tools/
│   └── verify_consistency.py # [NEW] 全站一致性扫描：逐页对比 raw vs parsed 的
│                             #   评论计数(li.pcmt)与正文文本相似度，输出报告。
├── data/
│   ├── raw/                  # [REUSE] 原站快照（含评论，作为核对真源）。
│   └── parsed/ja/            # [REGEN] parse_all(force) 重生成，评论将出现在此。
└── site/.vitepress/dist/     # [REGEN] build.mjs 重建，含镜像评论。
```

## 关键代码结构

```python
# pipeline/escah_pipeline/parser_puki.py —— _remove_chrome 内新增（置于通用 form 删除之前）
def _keep_pcomments(body: BeautifulSoup) -> None:
    for div in body.find_all("div", class_="pcomment"):
        for form in list(div.find_all("form")):
            ul = form.find("ul", class_="list1") or form.find("ul")
            if ul is not None:
                for li in ul.find_all("li", class_="pcmt"):
                    inp = li.find("input", class_="pcmt")
                    if inp is not None:
                        inp.decompose()
                    for empty in li.find_all("span", class_="__plugin_new"):
                        empty.decompose()
                form.insert_before(ul)
            form.decompose()
        pf = div.find("div", id="pcomment-form")
        if pf is not None:
            pf.decompose()
        for dead in div.find_all("p"):
            if "最新の20件" in (dead.get_text() or ""):
                dead.decompose()
```