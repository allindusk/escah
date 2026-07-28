# MEMORY — ESCH 超昂大战 WIKI 中日双语镜像站

## 项目概况
- 镜像 escalationheroines.wikiru.jp（PukiWiki）→ 本地构建 ja/zh 双语静态站，部署 GitHub Pages（base `/escah/`）。
- 架构：Python 流水线 `pipeline/escah_pipeline`（discover/fetch/parse/assets/i18n/chara/sync-site）+ VitePress 站点 `site/`（MPA，ja/zh 双 locale），层间以文件为契约。
- 数据：`data/raw`(快照,已 git) + `data/manifest.json`(sha256) + `data/parsed/{ja,zh,characters,i18n}`(可重跑,不入库) + `data/assets/img`(2386 图,LFS) + `data/registry/{pages.yaml(真源~418页),mirror_plan.yaml}`。
- 部署：无 CI。本地 `python -m escah_pipeline.cli update` → `cd site && node build.mjs build` → 手动 push dist 到 gh-pages。**双部署**：GitHub Pages(base `/escah/`、repo 名 `escah` 项目页) + Cloudflare Pages(base `/`，CF 控制台设构建环境变量 `BASE=/`)；顶部 `SiteAccessSwitch.vue` 下拉互切，域名配 `site/.env` 的 `VITE_GHPAGES_URL` / `VITE_CF_URL`（`.env` 被 gitignore，CF 构建须在控制台设这些 VITE_ 变量 + `BASE=/`）。
- 硬件 AMD Ryzen 7 8845HS（16 线程）；并行上限 round(cpu*0.8)，留 20% CPU。不可并行：fetch（单限速器）、sync_site（顺序）、build.mjs（detached 防 harness 杀）。
- ⚠️ **本地 `vite preview`(sirv) 不能验证搜索**：sirv 对 `@` 前缀的本地搜索索引分块（`@localSearchIndex<locale>.<hash>.js`，~20MB）MIME/serving 有坑，预览站搜索恒 0 结果、索引资源不出现；**搜索相关只能对部署站（GH Pages/CF）实测**。VitePress 本地搜索索引是懒加载——`VPLocalSearchBox` 的 `ln={root,zh}` 在**用户首次输入**时才 `import()` 该分块（`storePositions:true` 致 `index` 字段 ~19.9MB，整体分块 ~21MB）。modal 打开即渲染 input，结果等索引就绪。
- ⚠️ **搜索索引不要随意瘦身/改 load 机制**（用户 2026-07-28：搜索可用，只加进度提示即可）。若需优化体积，注意：自己 `fetch/import` 该索引分块 URL 会与 VitePress 同 URL 的 `import()` **争用并破坏搜索**，只能侦测 VitePress 自身加载完成（performance resource `responseEnd>0`）。进度 UI 组件：`site/.vitepress/theme/components/SearchLoading.vue`（侦测 `.VPLocalSearchBox input`，冷加载显示 1%–100% 进度卡片，`pointer-events:none` 不拦截输入框）。

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
- **新增角色词汇入表（用户前瞻要求，2026-07-27）**：今后新增角色页后，须把新角色名 + 必殺技名并入 glossary。工具 `tools/_check_glossary_coverage.py` 扫描全角色 JSON，列出「名字/技能名」未纳入 names.yaml/skills.yaml 的条目（已译为中文的纯汉字技能名不算缺失；仅含假名者算；ja==zh 回声条目算缺失），并生成 `tools/_glossary_pending.txt` 待译清单。译者填好后重跑 `_gen_name_glossary.py`/`_gen_skill_glossary.py` 并入。i18n 与覆盖检查口径一致：`k==v` 视为未真正翻译。
- **不翻译（保持原样）名单（用户指定，2026-07-27）**：`FM77`（源 wiki 页标题本就是代号，无日文名）、`女郎蜘蛛初音`、`女郎蜘蛛奏子`——用户明确"像这种不是日语的都不用翻译，用原来的就行"。已从 names.yaml 删除其 `ja==zh` 回声条目；`name_zh` 留空 → 浮窗显示原样。`tools/_check_glossary_coverage.py` 的 `_DO_NOT_TRANSLATE` 集合 + `_is_plain_code()`（纯字母数字代号自动识别）负责跳过它们，不再报缺译。
- **技能名待补译（2 个，2026-07-27）**：`ケイロン ステップ`/`+`（角色 ビートソニック・アキレス）仍含假名未入 skills.yaml，待译者补。
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
- ⚠️ `config.ts` search.miniSearch 里的函数（tokenize/processTerm 等）会被序列化后浏览器端 eval 重建，**闭包变量全丢** → 必须自包含（常量写函数体内），否则 ReferenceError、搜索 0 结果（2026-07-27 已修）。
- ⚠️ preview 服务器（sirv）启动时缓存文件清单：rebuild 后新 hash 资源 404、页面 JS 全挂 → rebuild 后必须重启 preview。
- ⚠️ 表格"一字一行"终极约定（2026-07-28，用户已濒临放弃勿再犯）：`.escah-tbl` 表格曾设 `width:auto !important` + 单元格 `overflow-wrap:anywhere` → 多列表被压进内容区时每列最小宽度=1 字符，数字 `8,500,000,000` 每个数字一行、中文一字一行（raid/raid-formations 等）。**铁律**：表格恒 `width:max-content!important; min-width:100%`（自然宽度绝不被压缩，宽表由 `.table-scroll` 横滚承接）；单元格只许 `overflow-wrap:break-word`（不参与最小宽度计算），**全站禁止对表格单元格用 `anywhere`/`break-all`**。custom.css 内 `.escah-tbl` 与 `.escah-tbl-fs-scroll` 两处均已改。
- tableEnhancer 结构安全约定（2026-07-27 大修）：表头块=开头连续全 th 行整块进 thead（rowspan 不能跨 thead/tbody）；筛选行插表头块后、用 headerGrid 算叶列数；数据区含合并单元格的表禁用排序/列筛选/删首列（bodyHasSpans 守卫）；markSpecialColumns 按单元格不按列索引。数据层 raw↔ja↔zh 表结构 416 页 0 差异，表格问题一律先查前端。
- 表格图片竖向堆叠（2026-07-27）：`applyImageStack()` 对“去掉所有 `<a>/<img>` 后剩余非空白文字为 0”的单元格加 `escah-img-stack`（纯图标列表 / 图标+名称竖向）；CSS `.escah-img-stack a{display:flex;align-items:center;gap:6px}`。含「+」组合、尾部说明、裸 `<img>xN` 因剩余文字≠0 保持横排。`.escah-img-col img{display:block}` 已存在但外层 `<a>` 须也变 flex 才生效。
- `CharHoverModal.isZh` 是函数须 `isZh()` 调用。
- 角色浮窗双模式：`charModalStore` `mode:'hover'|'pinned'` + `anchor`。hover 贴锚点小预览(pointer-events:none)；pinned 居中可拖动。`MirrorContent.onOver` 取 `[data-char]` rect `showHover`，`onClick` `store.pin(name)`。
- ⚠️ `charRefs.json` 头像映射生成 bug（2026-07-28 修复）：`tools/gen_char_refs.py` 原把角色 JSON 的 `icon` 字段(`img/<hash>.png` 本地路径)拼成 wiki URL 去 `data/pending_assets.json` 反查 → 永远 0 命中，导致**全站角色图像从不触发浮窗**。`tagAvatars` 需要 hash→名 直接映射，现已改为从 `icon` 取 `img/` 后文件名。每次新增/删除角色后须重跑 `python tools/gen_char_refs.py`（当前 370 名 + 370 头像映射）。浮窗标签三来源：`tagCharLinks`(指向 `/characters/NAME.html` 的链接) + `tagAvatars`(img hash→名) + `wrapPlainTextNames`(纯文本名，**含外链 `<a>` 内的名字**——2026-07-28 放宽，原会漏掉非 /characters/ 链接包裹的名字)。`charRefs.json` 由 build 直接 import，**改后必须 rebuild**。
- ⚠️ 浮窗与详情页翻译必须同源（2026-07-27 晚修复）：浮窗 JSON `zh` 由 `i18n.char_fill_all()` 从「该角色页 i18n 词典」(节点 keyN + 整句块 blkN) 回填；该函数已挂进 `sitegen.sync_site`（复制角色 JSON 前调用）。`chara.py` 的 `extract_all_characters` 只做 glossary 精确匹配（无块级回退），**不得单独作为浮窗翻译源**——否则浮窗比详情页少译技能/效果文本。详情页走 `render_locale` 同一词典，二者一致。若浮窗又出现"详情页译了浮窗没译"，先查 `char_fill_all` 是否在 sync-site 跑了（不要误判为词表缺口）。
- ⚠️ `render_locale` 块级回退丢图/表（2026-07-28 修复）：块 `<td data-i18n-blk>` 含 `<img>`/`<table>` 且块级 zh 缺译时，原逻辑 `remove` 全部子节点再写纯文本，**图片/表格被一起删**，留下空 `rgn-content`（全站所有含图/表的块都受害，如 raid 区域截图）。修复：块循环加 `if any(d.tag in ("img","table") for d in el.iter()): continue` 保留结构、节点级回退 ja。改 `i18n.py` 后须 `sync-site` 全站重渲染（frag img 数 0→156）。
- 全局搜索 `config.ts` `_render`+`_splitIntoSections`；TOC `sitegen._relink_toc` + `onAnchorClick` 平滑滚动。

## 前端功能（theme，简）
- `uiPrefs.ts`(ultraWide/navCollapsed/tocCollapsed,localStorage,`applyUiClasses`)；`ScrollButtons.vue`；`tableEnhancer.ts`(筛选/排序/全屏)；`Layout.vue` `nav-bar-content-after` 放宽度控件+`ScrollButtons`。

## 用户偏好（最高优先级）
- ⚠️ 后台运维纪律（用户"优先度高、别浪费我时间"）：①启动前 `Get-Process -Name python` 查重，绝不重复触发长任务；②每次后台任务须有进度日志（`_rebuild.bat` 或 `_bg.py start` 落 `tools/_logs/`+锁+`[DONE]/[FAIL]`）；③能判断 bug/卡住。
- ⚠️ 回收站约定：过期/无用文件移入根 `recycle_bin/`（tools//root 归类），**绝不 `git rm` 或永久删除**。
- LLM 翻译管线已弃用，代码 `recycle_bin/tools/`，勿重建。
- ⚠️ **非日语/代号类不翻译（用户 2026-07-27 指定）**：名字或术语若不是日语（代号、纯字母数字、或用户指定保持原样的，如 `FM77`/`女郎蜘蛛初音`/`女郎蜘蛛奏子`），**不要翻译，保留原样**：不写进 glossary（不造 `ja==zh` 回声），角色 `name_zh` 留空使浮窗显示原样。新增此类名字追加到 `tools/_check_glossary_coverage.py` 的 `_DO_NOT_TRANSLATE`，避免被报为缺译。
- 本地开发 `start-dev.bat`(sync-site+`node build.mjs dev`:5173+`dev-watch.py`)/`stop-dev.bat`/`start-site.bat`(:4173)。
- ⚠️ **推送 GitHub 须经用户明确指令（2026-07-28 指定）**：修复/改动完成后**不要自行决定提交并推送**；只能在做完改动、等用户说"推送/提交推送"时才 `git commit`+`git push`。本地可自由构建验证，但 push 一律等用户发话。
