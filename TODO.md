# ESCH 项目进度统筹 & TODO

> 生成时间：2026-07-25（深夜）。依据：README.md、.codebuddy/memory/（MEMORY.md / 2026-07-24.md / 2026-07-25.md / TRANSLATION_TODO.md）、.codebuddy/plans/*、实际文件核对。
> 原则：所有"无用文件"一律移入 `recycle_bin/`（仅回收、不永久删除），见 第 0 项。

---

## 第 0 项【最高优先级】回收站清理（已执行 2026-07-25）

- 在项目根新建 `recycle_bin/`，把**确定不再使用**的文件/目录全部移入（不 `git rm`、不永久删除，随时可恢复）。
- 适用对象：一次性注入脚本（`_addchars_*`、`_addbatch*`、`_addfaq*`、`_addglossary*`、`_addraid*`）、注入输入批次（`_batch_*.json`）、残存 grep/分段调试产物（`_rg_*.txt`、`_seg_*.txt`、`_seg_chars.txt`）、各类日志（`_api_*.log`、`_api_pipeline_run.log` 等）、大导出 `_for_api.txt`、调试/补丁脚本（`_debug_*.py`、`_check_*.py`、`_fix_*.py`、`_freq.py`、`_remain_segs.py`、`_stat_now.py`）、三个子目录 `_api_batches/`、`_api_results/`、`_untranslated/`、`__pycache__/`、根目录调试文件（`_check.txt`、`_debug_raw.txt`、`_prints.txt`、`_snap__api_out.log.txt`、`$null`）。
- **保留（活跃工具链，勿动）**：`zh_patch.py`、`char_zh.py`、`_freq_chars.py`、`_page_seg.py`、`_inject_batch.py`、`_api_pipeline.py`、`_export_for_api.py`、`_split_for_api.py`、`_export_untranslated.py`、`_split_untranslated.py`、`gen_char_refs.py`、备份 `zh_patch.bak.py`、`zh_patch.py.bak_rollback001`。
- **以后约定**：任何新发现的过期/无用文件，默认只移入 `recycle_bin/`，绝不直接永久删除。

---

## 一、已做（已逐项核对）

| # | 项目 | 状态 | 核对依据 |
|---|------|------|----------|
| 1 | Python 流水线 discover/fetch/parse/assets/sync-site | 完成 | 代码存在；data/registry/{pages,mirror_plan}.yaml 已生成 |
| 2 | VitePress 双语站点 + detached 构建 | 完成 | `site/.vitepress/dist` 含 423 zh + 423 ja HTML、2386 张图 |
| 3 | 图片 base 路径修复（withBase） | 完成 | dist/img 正常 |
| 4 | 镜像计划 plan.py + sync-plan + mirror_plan.yaml | 完成 | data/registry/mirror_plan.yaml 存在（planned 空、mirrored 分组填满）|
| 5 | updater 改为 zh_patch 确定性翻译 + RSS/--full 增量 | 完成 | 代码存在；CI 按决策**未**配置（见不准确项 2）|
| 6 | LLM API 翻译 8 批（001–008，glm-5.1/5.2）| 完成 | `tools/_api_results/` 16 个结果文件齐全 |
| 7 | 译文注入 JA2ZH 词表 | 完成 | **实测 JA2ZH 词条 27,310 条**（文档记 ~26,752，基本一致）|
| 8 | 应用链跑通：zh_patch + char_zh + sync-site + build | 完成 | dist 已含最新译文 |
| 9 | 本地脚本多线程化（ProcessPool/ThreadPool）| 完成 | zh_patch/char_zh/_freq_chars/parser_puki/assets 已并行；fetch/sync_site 保持串行 |

---

## 二、未完成 / 待办（按优先级）

- **P1 部署 GitHub Pages（阻断"上线"）**：`site/.vitepress/dist` 已生成但未推送。需 `git add` dist 内容 → 推送 `gh-pages` 分支（或 Pages 指向该分支）。项目无 CI，需手动 commit+push。（README 第 4 节）
- **P1 清零残留翻译（长尾）**：全站残留 **306,600 字符 / 10,281 条**真未译（raid/faq 集中页 + 角色页 freq=1 散文长尾）。glm-5.1/5.2 各剩约 37 万 token，足够增量补译。esca-translation-finish 计划的"全站零残留"目标**未达成**。
- **P2 角色 JSON 残留**：`char_zh.py` 跑后仍有 **2,002 条**单元格未补 zh 字段，随词表增长重跑即受益。
- **P2 过时计划文档归档**：`.codebuddy/plans/` 下两份 `(未完成)` 计划（修复图片路径、esca-translation-finish）已被 API 管线方式取代，建议合并/标记 stale，避免误导。
- **P3 文档准确性修订**（见第三节）。

---

## 三、已核对的不准确项（需修订）

1. **README `legacy/index.html` 引用（已作废，非错误）**：原独立 `index.html` 角色浮窗 demo 经用户确认**作废**（浮窗已成全页面功能，无需单独 demo 页），`legacy/` 不建；README 已修正该引用。
2. **GitHub Action（已作废，非矛盾）**：用户确认不配置 CI（GitHub 服务器环境复杂 + AI 无法为新增散文补译词表），更新由用户在项目内手动跑 `update` 后构建部署；计划文件 `add-github-action` 已改标 `cancelled`，与正文第四节决策一致。
3. **esca-translation-finish 计划未执行**：batches H–L 工作流从未跑；实际改由 `_api_pipeline.py` 完成 001–008 批。该计划"全站零残留"目标尚未达成（见 P1 残留）。
4. **修复图片路径计划残留 pending**：`translate-remaining` / `translate-characters` 标 pending，实际由 API 管线 + 词表注入完成，方式已变，计划状态未同步。

---

## 四、备注（非阻塞）

- 增量更新为本地手动命令（`python -m escah_pipeline.cli update`），由用户在对话中触发，不配 CI（决策：CI 内 AI 无法为新散文补译词表）。
- 备份文件 `zh_patch.bak.py` / `zh_patch.py.bak_rollback001` 保留作安全网，勿移入回收站。
