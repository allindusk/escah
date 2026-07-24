# ESCH 续译任务清单（批次 F 起，可机械执行）

> 用途：下一次会话直接按本清单逐批执行，不中断。每批跑完即 sync-site + build 验证。
> 基线（2026-07-24 实测）：页面残留 782,489 假名（含 PROTECTED `bedroom-scenes.html` 94,705），
> 角色 JSON 残留 132,577。真正待译 ≈ 82 万字符。
> 已完成批次 A–E：评论规则样板、技能公式、角色页高频散文/机制句、glossary 词条。

## 执行协议（每批通用，必须按顺序）
1. 生成候选：
   - 单页：`python tools/_page_seg.py <页名>` → 生成 `tools/_seg_<页>.txt`（按频率排序句级候选）
   - 角色散文全局：`python tools/_freq_chars.py` → `tools/_seg_chars.txt`（按 频次×长度 排序）
2. 写注入脚本 `tools/_addchars_<X>.py`：从候选取高性价比条目（长句 + 通用短语）。
   注意：精确 key 必须匹配文件原文（含标签切分）；GENERIC 长键可能被 JA2ZH 短语拆散，公式类宜整句精确键或正则。
3. 跑翻译引擎：
   `python tools/zh_patch.py && python tools/char_zh.py`
4. 同步 + 构建：
   `python -m escah_pipeline.cli sync-site`
   `cd site && node build.mjs build`（用 Start-Process detached，约 22–45s）
5. 抽查 `site/.vitepress/dist` 确认新译流入；重跑统计确认降量。

## 批次（按性价比排序）
- **F — faq 整页**（~2.4万）：`python tools/_page_seg.py faq` 后注入常见问题/评论样板与高频段。
- **G — raid 系列**（~7.3万）：依次 `raid` / `raid-formations` / `raid-recommended` / `raid-buff-debuff`，
  每页 `_page_seg` 后注入；可合并为一个 `_addchars_g.py`。
- **H — glossary 用語集剩余**（~2.2万）：续批次 E 未覆盖段，再跑 `_page_seg.py glossary`。
- **I — characters 列表页 + annihilation**（~2.4万）
- **J — artists + voice-actors + character-exchange**（~2.6万）
- **K — scenario-order + treasure-box + release-history**（~2.5万）
- **L+ — 角色页散文长尾**：反复 `python tools/_freq_chars.py` 取全局 Top 注入，
  直到 freq≥2 段清空；再处理 freq=1 中长度≥阈值的高频段。每轮降量边际递减。
- **JSON**：随角色页词表增长自动受益，每批重跑 `char_zh` 即可，无需单独批次。

## 停止条件（避免无谓长尾）
- 角色页 freq=1 唯一文本（约 1.8 万条）逐条译收益极低，做到「集中页 + 高频段清零」即停，
  零星残留保留日文或转交人工 overrides/zh 目录。

## 不译（PROTECTED，勿动）
- `bedroom-scenes.html`（94,705 残留，项目规则刻意保留日文）

## 关键约束（来自 MEMORY.md）
- 站点特设页「日中用語対照表」slug 必须是 `term-map`，不可用 `glossary`（会覆盖 WIKI 用語集镜像页）。
- 所有 `site/*.md` 由 `sync-site` 用 `sitegen.py` 模板重新生成，勿手改。
- 翻译只走 `tools/zh_patch.py` 词表路径（无 LLM）；`char_zh.py` 复用其 patch()。
- 角色名 / 声优 / 画师名保留日文。
