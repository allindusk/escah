---
name: esca-translation-finish
overview: 按 .codebuddy/memory/TRANSLATION_TODO.md 从批次 H 起连续推进剩余镜像页与角色页散文的 zh 词表翻译，并覆盖原清单「停止条件」中保留的零星残留（你要求全部译完、不留人工 overrides）。每批注入 tools/zh_patch.py 词表后自动 sync-site + 构建验证，不中途停下，目标全站零残留（仅 PROTECTED 页与角色名/声优/画师名除外）。
todos:
  - id: verify-fg
    content: 运行 sync-site 与 node build.mjs build 验证已完成的 F/G 批次注入
    status: pending
  - id: batch-h
    content: 续译 glossary 用語集剩余段并 sync-site + build 验证
    status: pending
    dependencies:
      - verify-fg
  - id: batch-i
    content: 补译 characters 列表页与 annihilation 页并构建验证
    status: pending
    dependencies:
      - batch-h
  - id: batch-j
    content: 补译 artists/voice-actors/character-exchange 并构建验证
    status: pending
    dependencies:
      - batch-i
  - id: batch-k
    content: 补译 scenario-order/treasure-box/release-history 并构建验证
    status: pending
    dependencies:
      - batch-j
  - id: batch-l-tail
    content: 反复取角色页长尾 Top 逐批清零直至零残留
    status: pending
    dependencies:
      - batch-k
  - id: finalize
    content: 统计全站残留并同步构建收尾，更新任务清单
    status: pending
    dependencies:
      - batch-l-tail
---

## 用户需求

- 按 `.codebuddy/memory/TRANSLATION_TODO.md` 任务清单从批次 H 起连续推进翻译，**不中途停下确认**。
- 推翻原「停止条件」：用户明确要求「不需要留作零星残留或人工 overrides，全部翻译完」，即角色页 freq=1 独有长尾也须逐批处理，直至全站零残留。
- 每批向 `tools/zh_patch.py` 的 JA2ZH/REGEX_RULES/GENERIC 写入译文后，运行 sync-site + build 验证。
- 目标全站零残留；**PROTECTED 页**（bedroom-scenes 等）与**角色名/声优/画师名**按约定保留日文，不译。

## 产品概述

ESCH 中日双语镜像站的翻译补全工程：把站点剩余日文（集中页 + 角色页独有散文）全部译为中文，词表引擎确定性、可复跑。

## 核心功能

- 续译集中页：glossary 用語集剩余、characters、annihilation、artists、voice-actors、character-exchange、scenario-order、treasure-box、release-history。
- 清零角色页散文长尾（freq=1 约 1.8 万条唯一文本），逐批处理不残留。
- 角色 JSON 的 zh 字段随词表增长自动受益（每批重跑 `char_zh.py`）。
- 每批执行 sync-site + `node build.mjs build` 验证新译流入。

## 技术栈

- 现有 Python 词表替换引擎 `tools/zh_patch.py`（JA2ZH 精确串 + REGEX_RULES 正则 + GENERIC 通用），无新增依赖。
- 辅助工具：`tools/_freq_chars.py`（全局长尾排序）、`tools/_page_seg.py <页>`（单页候选）、`tools/_addchars_*.py`（批次注入）。
- 构建/同步：`cd site && node build.mjs build`（detached，22–45s）、`python -m escah_pipeline.cli sync-site`。

## 实现方法

- **精确 key 替换**：`JA2ZH` 为精确串字典；`patch()` 经 `_JA2ZH_ORDERED` 按 key 长度降序匹配，长整句 key 自动优先、不被术语子串拆散——这是逐句译长散文可行的关键。
- **注入脚本模式**：用 `ast` 解析 `zh_patch.py` 提取已有 JA2ZH key 去重；`BATCH` 列表过滤已存在项后，插入锚点 `JA2ZH: dict[str, str] = {` 之后。
- **长尾清零策略**：对 freq=1 独有散文，反复运行 `_freq_chars.py` 取全局 Top（频次×长度），并新增辅助脚本按长度阈值批量产出候选；整句 key 优先替换，逐批写入直至零残留。
- **角色 JSON**：`char_zh.py` 复用 `patch()` 给 tr 单元格补 zh 字段，每批重跑即全站同步。

## 实现注意事项

- 精确 key 须匹配文件原文（含标签切分）；公式类宜整句精确键或正则，避免 GENERIC 长键被 JA2ZH 短语拆散。
- 勿手改 `site/*.md`（sync-site 用 sitegen 模板重生成）；特设页对照表 slug 必须用 `term-map`，不可叫 `glossary`。
- PROTECTED 页与角色名/声优/画师名保留日文，不译。
- 词表增大后 `zh_patch.py` 全量重跑成本上升，需关注执行时间；build 约 22–45s。

## 架构设计

翻译层（`zh_patch` 词表）与站点层（`sync-site` 生成 md → `build.mjs` 构建 dist）以文件为契约，逐批重跑即全站同步生效，无需改动架构。批次 H–K 处理集中页，批次 L+ 循环清空角色页长尾，最终 Z 收尾统计与构建。

## 目录结构

- `tools/_addchars_h.py` [NEW] glossary 用語集剩余段注入
- `tools/_addchars_i.py` [NEW] characters 列表页 + annihilation 注入
- `tools/_addchars_j.py` [NEW] artists + voice-actors + character-exchange 注入
- `tools/_addchars_k.py` [NEW] scenario-order + treasure-box + release-history 注入
- `tools/_addchars_l1.py` … `_addchars_lN.py` [NEW] 角色页长尾多批（反复生成，直至零残留）
- `tools/_seg_chars.txt` [MODIFY] 反复重生成的角色页长尾候选
- `tools/_seg_*.txt` [EXIST] 各集中页候选（已生成，供 H–K 取用）
- `.codebuddy/memory/TRANSLATION_TODO.md` [MODIFY] 更新进度、厘清停止条件（覆盖原"留零星残留"表述）

## 关键代码结构

注入脚本标准模式（沿用既有 `_addchars_f.py`/`_addchars_g.py`）：

- `ast.parse` 遍历 `JA2ZH` 节点收集已有 key 入 `existing` 集合去重。
- `BATCH` 为 `(ja, zh)` 元组列表；`new = [b for b in BATCH if b[0] not in existing]`。
- 锚点 `marker = "JA2ZH: dict[str, str] = {"`，在其后插入新条目块；因 `_JA2ZH_ORDERED` 按长度降序，长整句自动优先。