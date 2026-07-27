# MEMORY — ESCH 超昂大战 WIKI 中日双语镜像站

## 项目概况
- 镜像 escalationheroines.wikiru.jp（PukiWiki）→ 本地构建 ja/zh 双语静态站，部署 GitHub Pages（base `/escah/`）。
- 架构：Python 流水线 `pipeline/escah_pipeline`（discover/fetch/parse/assets/i18n/chara/sync-site）+ VitePress 站点 `site/`（MPA，ja/zh 双 locale），层间以文件为契约。
- 数据：`data/raw`(快照,已 git) + `data/manifest.json`(sha256) + `data/parsed/{ja,zh,characters,i18n}`(可重跑,不入库) + `data/assets/img`(2386 图,LFS) + `data/registry/{pages.yaml(真源~418页),mirror_plan.yaml}`。
- 部署：无 CI。本地 `python -m escah_pipeline.cli update` → `cd site && node build.mjs build` → 手动 push dist 到 gh-pages。
- 硬件 AMD Ryzen 7 8845HS（16 线程）；并行上限 round(cpu*0.8)，留 20% CPU。不可并行：fetch（单限速器）、sync_site（顺序）、build.mjs（detached 防 harness 杀）。

## 翻译工作流（2026-07-27 起 = key 化 i18n，方案固化，用户"暂不再改"）
- 助手不译正文（成人内容红线）。译者译文写 `new_translation_<YYYYMMDD>_translated.txt`；集中待译清单 `new_translation_<YYYYMMDD>.txt` 由 `i18n extract` 生成（`===X===` 字母标记分隔 + `# MAP A=<slug>` 映射 + `[N] 日文`；同时生成空白 `_translated.txt` 给译文）。
- 流程：`i18n build`(模板 {{keyN}}+双语 JSON) → `extract`(集中清单) → 译 → `fill`(按 #MAP+[N] 回填 zh，成功后 `_translated` 移 `_translated_texts/`、清单移 `_texts_for_translation/`) → `char-fill` → `sync-site`(渲染 frag) → build。一键 `cli translate`。全站 i18n 应用 ~30s。两级粒度：节点 keyN 保结构；整句块 blkN 回退纯文本。中日同形算有效翻译。
- 旧每页 `_texts_for_translation/*.txt` 是 i18n 重构前遗留，不覆盖细粒度键，仅归档，**勿当工作清单**。
- ja→zh 记忆按页复用；禁止旧全局 `_manual_zh.json` 迁移源。同一日文不同页译法不同属正常。
- 已废弃移 recycle_bin（勿重建）：`zh_patch.py`/`char_zh.py` 正则引擎、`inject_translations.py`、`_manual_zh.json`。

## 站点词汇表 / 专有名词 glossary（AI 维护，render-time 最高优先级覆盖）
- `glossary/terms.yaml`（入库）：`page_titles`(44 非角色页日文名→中文标题) + `char_sections`(6 浮窗分段标题)。`sitegen._page_title_ja2zh` 用于 md 标题/侧栏；`char_sections`→`site-terms.json`→`CharHoverModal.charSectionZh()`。特设对照表 slug 必须 `term-map`。
- `glossary/names.yaml`（入库，700 条 JA→ZH 名字：角色/NPC/支援者/道具/装备/宝箱/BOSS；来源 `name_glossary_20260727.txt`+`_translated.txt`，生成器 `tools/_gen_name_glossary.py`）。`i18n.render_locale` 仅 zh 三层：①独立名词(归一化 ja==名字)直接覆盖；②漏译 JA 子串→ZH；③错译名由 `_learn_corrections()` 扫描全站学 W→Z 整站替换。长词优先。`img alt/title` 与 `data-char` 保留日文（hover 键）。**也供 `chara.py` 注入角色 `name_zh` 字段**。
- `glossary/skills.yaml`（入库，2776 唯一归一化条目 JA→ZH，必殺技/固有効果 精翻；来源 `skill_unique_effects_20260727.txt`+`_translated.txt`，生成器 `tools/_gen_skill_glossary.py`）。`i18n.render_locale` 仅 zh 按归一化 ja 精确匹配最高优先级覆盖（`_name_override` 同时查 names+skills），防被其他翻译覆盖。注：这些条目此前已由 `tools/_fill_skills.py` 写入 i18n JSON（2881 条），skills.yaml 是额外保险（render-time，不破坏句级翻译）。
- 全部属 render-time overlay：当前+未来页面随 build 自动生效，ja 站不受影响。

## 关键架构
- 原文 HTML→`sitegen._sanitize_html`→`site/.vitepress/frag/<slug>.{ja,zh}.json`；md `import frag` + `MirrorContent.vue` `v-html`。**不可 `?raw`**；frag 按 locale 分文件。
- `site/*.md`/sidebar 由 `sync-site` 重生成**勿手改**；改 parser/图须 sync-site+ build。
- 图片：parse 扫 `#body` `<img>`→`data/pending_assets.json`→`data/assets/img`；`MirrorContent` 用 `withBase('/img/')`。所有资源/fetch 路径须带前导 `/`。
- `config.CHARLIST_PAGE` + `registry.extract_characters()` 是角色发现机制，勿删。
- `parser_puki._remove_rules_region` 删 PukiWiki 规则通知 `div.rgn-container`（按文案唯一标识）。
- 角色 JSON `data/parsed/characters/<safe_id>.json`：`name`(日文)/`name_zh`(查 names.yaml)/`rarity`/`icon`/`sections`；`sync-site` 复制到 `site/public/data/char/`。前端 `CharHoverModal` 用 `displayName`：zh 站显示 `name_zh（日文名）`，ja 站/未命中显示日文。

## 已修复阻断 bug
- `cleanUrls:false`，构建只产 `*.html`，内部链接务必带 `.html` 否则 404。
- VitePress 改 theme 后 JS 不刷新 → 删 `.vitepress/cache` 再 build。
- `CharHoverModal.isZh` 是函数须 `isZh()` 调用。
- 角色浮窗双模式：`charModalStore` `mode:'hover'|'pinned'` + `anchor`。hover 贴锚点小预览(pointer-events:none)；pinned 居中可拖动。`MirrorContent.onOver` 取 `[data-char]` rect `showHover`，`onClick` `store.pin(name)`。
- 全局搜索 `config.ts` `_render`+`_splitIntoSections`；TOC `sitegen._relink_toc` + `onAnchorClick` 平滑滚动。

## 前端功能（theme，简）
- `uiPrefs.ts`(ultraWide/navCollapsed/tocCollapsed,localStorage,`applyUiClasses`)；`ScrollButtons.vue`；`tableEnhancer.ts`(筛选/排序/全屏)；`Layout.vue` `nav-bar-content-after` 放宽度控件+`ScrollButtons`。

## 用户偏好（最高优先级）
- ⚠️ 后台运维纪律（用户"优先度高、别浪费我时间"）：①启动前 `Get-Process -Name python` 查重，绝不重复触发长任务；②每次后台任务须有进度日志（`_rebuild.bat` 或 `_bg.py start` 落 `tools/_logs/`+锁+`[DONE]/[FAIL]`）；③能判断 bug/卡住。
- ⚠️ 回收站约定：过期/无用文件移入根 `recycle_bin/`（tools//root 归类），**绝不 `git rm` 或永久删除**。
- LLM 翻译管线已弃用，代码 `recycle_bin/tools/`，勿重建。
- 本地开发 `start-dev.bat`(sync-site+`node build.mjs dev`:5173+`dev-watch.py`)/`stop-dev.bat`/`start-site.bat`(:4173)。
