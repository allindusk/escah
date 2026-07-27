# ESCH 项目进度统筹 & TODO

> 生成时间：2026-07-25（深夜）。依据：README.md、.codebuddy/memory/（MEMORY.md / 2026-07-24.md / 2026-07-25.md / TRANSLATION_TODO.md）、.codebuddy/plans/*、实际文件核对。
> 原则：所有"无用文件"一律移入 `recycle_bin/`（仅回收、不永久删除），见 第 0 项。

---

## 第 0 项【最高优先级】回收站清理（已执行 2026-07-25）

- 在项目根新建 `recycle_bin/`，把**确定不再使用**的文件/目录全部移入（不 `git rm`、不永久删除，随时可恢复）。
- 适用对象：一次性注入脚本（`_addchars_*`、`_addbatch*`、`_addfaq*`、`_addglossary*`、`_addraid*`）、注入输入批次（`_batch_*.json`）、残存 grep/分段调试产物（`_rg_*.txt`、`_seg_*.txt`、`_seg_chars.txt`）、各类日志（`_api_*.log`、`_api_pipeline_run.log` 等）、大导出 `_for_api.txt`、调试/补丁脚本（`_debug_*.py`、`_check_*.py`、`_fix_*.py`、`_freq.py`、`_remain_segs.py`、`_stat_now.py`）、三个子目录 `_api_batches/`、`_api_results/`、`_untranslated/`、`__pycache__/`、根目录调试文件（`_check.txt`、`_debug_raw.txt`、`_prints.txt`、`_snap__api_out.log.txt`、`$null`）。
- **保留（活跃工具链，勿动）**：`zh_patch.py`、`char_zh.py`、`comment_zh.py`、`_freq_chars.py`、`_page_seg.py`、`_extract_texts.py`、`inject_translations.py`、`gen_char_refs.py`、备份 `zh_patch.bak.py`、`zh_patch.py.bak_rollback001`。
- **以后约定**：任何新发现的过期/无用文件，默认只移入 `recycle_bin/`，绝不直接永久删除。
- **2026-07-26 追加**：LLM 翻译已彻底弃用，全部 LLM 脚本/产物/日志（`_api_pipeline.py`、`_cmt_call.py`、`comment_translate.py`、`_translate_loop.py`、`_t_diag.py`、`_export_for_api.py`、`_split_for_api.py`、`_export_untranslated.py`、`_split_untranslated.py`、`_inject_batch.py`、`_api_batches/`、`_api_results/`、`_cmt_pages/` 及相关 log）已移入 `recycle_bin/tools/`。

---

## 一、已做（已逐项核对）

| # | 项目 | 状态 | 核对依据 |
|---|------|------|----------|
| 1 | Python 流水线 discover/fetch/parse/assets/sync-site | 完成 | 代码存在；data/registry/{pages,mirror_plan}.yaml 已生成 |
| 2 | VitePress 双语站点 + detached 构建 | 完成 | `site/.vitepress/dist` 含 423 zh + 423 ja HTML、2386 张图 |
| 3 | 图片 base 路径修复（withBase） | 完成 | dist/img 正常 |
| 4 | 镜像计划 plan.py + sync-plan + mirror_plan.yaml | 完成 | data/registry/mirror_plan.yaml 存在（planned 空、mirrored 分组填满）|
| 5 | updater 改为 zh_patch 确定性翻译 + RSS/--full 增量 | 完成 | 代码存在；CI 按决策**未**配置（见不准确项 2）|
| 6 | LLM API 翻译 8 批（001–008，glm-5.1/5.2）| 完成（**方式已弃用**，文件在 recycle_bin/tools/）| 历史批次译文已注入 JA2ZH，产物归档（**注：JA2ZH 硬编码词典已于 2026-07-26 整体移除，散文硬编码无实用价值，现仅以手工译文 _manual_zh.json 为准**）|
| 7 | 译文注入 JA2ZH 词表 | 完成 | 实为注入 `_manual_zh.json`（用户手工译文）；原 JA2ZH 硬编码词典 40,473 条已于 2026-07-26 移除，数据存 `recycle_bin/tools/zh_patch_ja2zh_removed_20260726.py` |
| 8 | 应用链跑通：zh_patch + char_zh + sync-site + build | 完成 | dist 已含最新译文 |
| 9 | 本地脚本多线程化（ProcessPool/ThreadPool）| 完成 | zh_patch/char_zh/_freq_chars/parser_puki/assets 已并行；fetch/sync_site 保持串行 |

---

## 二、未完成 / 待办（按优先级）

- ~~**P0 key 化 i18n 重构**~~ ✅ **已完成（2026-07-27）**：废弃 zh_patch/char_zh 正则替换，落地「模板 {{keyN}} 占位 + 每页双语 JSON」流程（`pipeline/escah_pipeline/i18n.py` + `cli i18n build/migrate/extract/fill/char-fill`）。全站 416 页迁移回填 82992 条；`list-ssr.txt` 两段错位（1497 漏译致前移/后移 1）已修复并重迁移（锚点校验 257/258）；dist 终验零占位残留。性能：i18n 应用全站 ~30 秒（旧正则 ~6 分钟）。旧引擎已移 `recycle_bin/tools/`。
- ✅ **专有名词 / 技能精翻 glossary 最高优先级覆盖（2026-07-27 末）**：`glossary/names.yaml`（700 条名字：角色/NPC/支援者/道具/装备/宝箱/BOSS）+ `glossary/skills.yaml`（2776 条必殺技/固有効果 精翻，由 translator 精译）纳入 glossary；`i18n.render_locale` 仅 zh 按归一化 ja 精确匹配**最高优先级覆盖**（防被其他翻译覆盖），当前+未来所有页面随 build 自动生效，ja 站不受影响。生成器 `tools/_gen_name_glossary.py` / `_gen_skill_glossary.py`。
- ✅ **角色浮窗中文名（2026-07-27 末）**：`chara.py` 提取时注入 `name_zh`（查 names.yaml，366/369 命中；3 个角色名未在 names.yaml 暂留日文）+ `sync-site` 复制到 `site/public/data/char/`；`CharHoverModal.vue` 新增 `displayName`，zh 站显示「中文名（日文名）」。存量 JSON 用 `tools/_backfill_char_name_zh.py` 补齐。
- **P1 部署 GitHub Pages（阻断"上线"）**：`site/.vitepress/dist` 已生成但未推送。需 `git add` dist 内容 → 推送 `gh-pages` 分支（或 Pages 指向该分支）。项目无 CI，需手动 commit+push。（README 第 4 节）
- **P1 清零残留翻译（长尾）**：全站残留真未译（raid/faq 集中页 + 角色页 freq=1 散文长尾）。**LLM 补译已弃用**，按新流程补译（`i18n extract` 汇总待译到 `tools/_todo_translate/new_translation_<YYYYMMDD>.txt` 并生成空白 `new_translation_<YYYYMMDD>_translated.txt` → 翻译模型把 [N]中文 写进 _translated → `i18n fill` 回填 zh → sync-site + build）。
- **P2 角色 JSON 残留**：`char_zh.py` 跑后仍有 **1,604 条**（2026-07-26 注入 9 页手工译文后已从 2,002 降）单元格未补 zh 字段，随手动译文注入后重跑即受益。
- **P2 过时计划文档归档**：`.codebuddy/plans/` 下两份 `(未完成)` 计划（修复图片路径、esca-translation-finish）已被 API 管线方式取代，建议合并/标记 stale，避免误导。
- **P3 文档准确性修订**（见第三节）。

---

## 三、已核对的不准确项（需修订）

1. **README `legacy/index.html` 引用（已作废，非错误）**：原独立 `index.html` 角色浮窗 demo 经用户确认**作废**（浮窗已成全页面功能，无需单独 demo 页），`legacy/` 不建；README 已修正该引用。
2. **GitHub Action（已作废，非矛盾）**：用户确认不配置 CI（GitHub 服务器环境复杂 + AI 无法为新增散文补译词表），更新由用户在项目内手动跑 `update` 后构建部署；计划文件 `add-github-action` 已改标 `cancelled`，与正文第四节决策一致。
3. **esca-translation-finish 计划未执行**：batches H–L 工作流从未跑；实际改由 `_api_pipeline.py` 完成 001–008 批。该计划"全站零残留"目标尚未达成（见 P1 残留）。
4. **修复图片路径计划残留 pending**：`translate-remaining` / `translate-characters` 标 pending，实际由 API 管线 + 词表注入完成，方式已变，计划状态未同步。

---

## 手动翻译工作流

> ⚠️ **2026-07-27 起**：旧「正则词表替换」工作流（`inject_translations.py` → `_manual_zh.json` → `zh_patch.py`/`char_zh.py`）**已废弃**，由 key 化 i18n 流程取代（见第二节 P0 与 README「翻译工作流（key 化 i18n）」）。`tools/_translated_texts/<slug>.txt`（`[N]` 旧版迁移遗留）仍由 `i18n migrate` 一次性回填，400+ 存量文件全程复用。

新流程（重构落地后）：
1. `parse`：产出每页模板 + 双语 JSON（ja 已填、zh 空）。
2. `i18n extract`：把空 zh 的条目汇总成**集中待译清单** `tools/_todo_translate/new_translation_<YYYYMMDD>.txt`（文件名 `new_translation_`+8 位日期，表意「新增翻译」无中文/无连字符）：开头固定翻译指令（用户提示词原样、无中文使用说明）+ 用不可翻译的 `===A===`/`===B===` 字母标记分段（页面↔标记映射记在 ASCII 行 `# MAP A=<slug> …`）+ 老格式 `[N] 日文`；已译不出现、已列入页面不重复追加；同时生成空白 `new_translation_<YYYYMMDD>_translated.txt`。
3. 翻译模型把 `[N] 中文` 写进 `new_translation_<YYYYMMDD>_translated.txt`（沿用同样 `===X===` 分段）→ `i18n fill` 从它取译文按页回填 `zh`（取成功后该文件移入 `_translated_texts/`，待译清单移入 `_texts_for_translation/`）。
4. `sync-site`（拆单语言 JSON + glossary 替换）→ `cd site && node build.mjs build`。

---

## 四、备注（非阻塞）

- 增量更新为本地手动命令（`python -m escah_pipeline.cli update`），由用户在对话中触发，不配 CI（决策：CI 内 AI 无法为新散文补译词表）。
- 备份文件 `zh_patch.bak.py` / `zh_patch.py.bak_rollback001` 保留作安全网，勿移入回收站。
