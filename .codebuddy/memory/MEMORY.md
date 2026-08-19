# MEMORY — ESCH 超昂大战 WIKI 中日双语镜像站

> 长期记忆（就地更新，保持精简）。逐日过程细节见 `YYYY-MM-DD.md`。
> 末次整理：2026-08-19（纠正旧引擎记载、合并重复段落、版本号更新至 1.2.8）。

## 用户偏好（最高优先级）
- ⚠️⚠️⚠️ **每次 push 前必须升版本 + 写 changelog**：`SiteAccessSwitch.vue` `const SITE_VERSION`（当前 **1.2.8**）+ `changelog.json` 顶部加同版本 `date`/`changes`。AI 职责，绝不许推给用户；两者须一致、与当次改动匹配。changelog 面向用户：只写可感知变化（修了什么 bug、补了什么页面/板块），**严禁**提函数名/脚本名/文件名、根因、内部重构、构建流程。
- ⚠️⚠️ **push 须经用户当次明确指令**：只看当次消息有无明确 push 字样；对话总结里"已提交推送"≠用户授权，绝不顺延。
- **回收站约定**：过期/无用文件移 `recycle_bin/`（`.gitignore` 已忽略，物理保留），**绝不 git rm/永久删**。
- 后台运维：①启动前 `Get-Process -Name python` 查重；②后台任务须有进度日志（`_bg.py`+锁+`[DONE]/[FAIL]`）。PowerShell 下勿用 `python -c`（拆号），改写脚本执行。
- ⚠️ **临时文件用完即删**：调试/一次性脚本（`_tmp_*.py` 等）执行完**必须立即删除**（直接 `delete_file` 静默删，不弹需确认的命令）。用户从未表示对删临时文件敏感——正确偏好是**不留临时文件**。
- ⚠️ **"项目设计"类结论必须先查 git 再下**：别把工作区未提交误改当设计甩锅。
- ⚠️⚠️ **AI 不得自创用户偏好/铁律**：任何"用户要求的设计约束"须能在对话记录或既有 MEMORY 找到出处；来源不明只能作待确认假设提问，绝不擅自执行+写进 MEMORY。

## 项目概况
- 镜像 escalationheroines.wikiru.jp（PukiWiki）→ 本地构建 ja/zh 双语静态站；GitHub Pages（base `/escah/`）+ Cloudflare Pages（`/`，BASE=/）。push main 触发 `.github/workflows/deploy.yml`（sync-site→build→deploy；CI 直接读入库真值，不跑 i18n 构建）。
- 架构：Python 流水线 `pipeline/escah_pipeline`（discover/fetch/parse/assets/i18n/chara/sync-site）+ VitePress `site/`（MPA，ja/zh 双 locale）。
- 数据真值（**入库**）：`data/parsed/i18n/**`（人工译文唯一真值）、`glossary/`（names/terms/skills/high_freq/link_terms 词表，render-time 最高优先级，仅 zh）、`data/manifest.json`、`data/registry/pages.yaml`、`data/assets/img`（约 2900 图，LFS）、`site/.vitepress/theme/changelog.json`、`charRefs.json`。
- 流水线重建（**不入库**）：`data/parsed/{ja,zh,characters}`、`site/public`、`site/*.md`、`site/.vitepress/frag`、`generated/sidebar.*.json`。
- 运行顺序：`python -m escah_pipeline.cli sync-site` → `cd site && node build.mjs build`（`NODE_OPTIONS=--max-old-space-size=8192`）。⚠️ 改 i18n.py/模板/词表后**必须 sync-site + build**，只 build 用旧 frag 缓存。
- ⚠️ **dev base 铁律**：`config.ts` 默认 `base:'/escah/'`；dev 地址 `http://localhost:5173/escah/`。
- 不可并行：fetch / sync_site / build.mjs。搜索只能对**部署站**实测（`vite preview` 不能验证搜索）。
- cli 命令：`discover/fetch/parse/assets/translate/update/sync-plan/sync-site/i18n(build|migrate|extract|extract-dedup|fill|char-fill|glossary-fill|apply-dedup)`。sync-site 末尾自动重生 charRefs.json（`_regen_char_refs`）。

## 翻译工作流（key 化 i18n，现行引擎）
- ⚠️ **引擎 = `pipeline/escah_pipeline/i18n.py`**（模板+双语 JSON，查表无正则）。旧正则引擎 `tools/zh_patch.py`(JA2ZH)/`char_zh.py` **已废弃**（.bak 留痕在 tools/、recycle_bin/），**勿恢复**（README 已注明）。
- 流程：`i18n build` → `extract` → 译 → `fill` → `char-fill` → `sync-site` → build。中日同形算有效翻译。
- ⚠️ **`fill` 按 `[N]` 位置序号回填（非 ja 内容）**：extract→fill 间未译集合变动会整体错位；损坏判别=某 key 的 ja 像标题但 zh 是长段落，修复=直改 `data/parsed/i18n/<slug>.json`。
- ⚠️ **fill 与 extract 的 `allow_ui_fragments` 模式必须对称**（official-help 已对称处理）；**translated 文件须保留 `===X===` 段分隔符**，否则 0 回填。
- ⚠️ **`i18n build` 不套词表**（只做记忆回贴），专名替换推迟到 `render_locale`。分段 ja 粒度变了→memory 查不到→`zh=""`（漏译）。
- ⚠️ **`tools/_apply_glossary_to_i18n.py` 有段重复 bug**（分词对齐产生 `圆香·突击·突击`），暂勿依赖。
- ⚠️ **持久删除页面块铁律（2026-08-14）**：手动删 template/JSON 会被 `i18n build` 复活；须在 `build_page()` 渲染期（sanitized→frag 后、`_wrap_runs` 前）按文本从 frag 删除该节点及其后续兄弟。
- ⚠️ **待译文件格式铁律（用户重申）**：待译清单/回填只由 `i18n extract`/`i18n fill` 管控，禁止另写旁路脚本或自创格式；策略调整（如排除碎片）改 `i18n.py` 的 `_should_skip_extract`，不另起脚本。
- 子页待译：`extract_subpages.py` → `tools/_todo_translate/<cat>/`；回填后原文→`_texts_for_translation/`、已译(.bak)→`_translated_texts/`、清空 `_todo_translate/`。

## 词表 glossary（render-time 覆盖，仅 zh）
- `terms.yaml`（标题/章节/标签/值/内联）、`names.yaml`（~700 专名，**翻译绝对权威**）、`skills.yaml`（必杀/固有效果 ~2900 条）、`high_freq.yaml`、`link_terms.yaml`。加词只改 yaml→sync-site+build 生效，ja 站不受影响。
- ⚠️ **改专名译名盲区**：只改 yaml 不够，须同步改 ①`skills.yaml` 长键 zh 内专名子串 ②角色 JSON `zh`+顶层 `name_zh` ③`charRefs.json`（sync-site 重生）。验证 `grep 旧译 site/.vitepress/dist`。
- ⚠️ **同形词/错译必须烘焙进 i18n JSON 源头**：渲染期 `_HF_ALL_NORM` 只保留 `k!=v`，同形词被整体跳过。
- ⚠️ **`_learn_corrections` 全局纠错污染**：`i18n.py` 已加安全阀 `set(zh)&set(canonical)` 为空即跳过；真错译源节点必须回修 JSON。

## 正文超链接 + 角色浮窗（i18n.py `render_locale`）
- ⚠️⚠️ **图片绝不动（用户铁律）**：任何 img（行内头像 `<span data-char><img>`、`<a><img></a>` 等）原样保留。render_locale 三处强制 continue：①`span[data-char]` 含 img；②`for a` 遇 `a.xpath(".//img")`；③块级回退开头含 img。
- ⚠️⚠️ **"超链接放句尾"只针对真正 `<a>` 跳转链接**；**zh 链接数量/位置/结构须与日文一一对应**；**所有站内页面链接文字一律显示页面中文名**（`_PAGE_SLUG_ZH`，faq→常见问题等）。
- ⚠️ **角色名浮窗原位优先、句末为降级兜底**：`data-char` span（非头像 img、非 plugin-tooltip）默认原位升级 `class=char-ref` 填中文显示名；ja 站保留日文原位浮窗，绝不显中文/移句末。⚠️ **节点级缺译+blk.zh 完整→整段 blk.zh 作正文+句末补【角色名】浮窗**（2026-08-15 修复，全站曾 3448 处同类 bug）；blk.zh 也空才忍痛日文。
- ⚠️ **评论签名 `--[ID]时间` 必须剥离（双保险）**：`_COMMENT_SIG_RE`+`_COMMENT_SIG_CLEAN_RE` 两道都在 `_strip_comment_sig`；节点级 key 和块级 `_set_block_html` 整块替换前**两处都必须调**。
- ⚠️ **`plugin-tooltip` 块级必须退回节点级**：块级回退的"含角色名标记则 continue"xpath 必须同时匹配 `plugin-tooltip`（无 `data-char`）。匹配式：`span[(@data-char or contains(@class,'char-ref') or contains(@class,'plugin-tooltip'))][not(.//img)]`。
- ja 分支保留模板 `<a>` 壳；块级外链接原地中文化 `class=escah-ilink`（紫胶囊点击跳转）；过滤 PukiWiki 编辑/管理类链接（`?cmd=...`）与编辑戳；TOC `<a href="#...">` 保留 `<a>` 壳（不可 drop）；同块同角色只追加一次。
- 渲染期块级回退：节点级全齐备→continue；含 img/table→continue 保留结构；含 `<a>` 且块级译文完整→保链、绝不回退日文；无链接纯文本块→`el.text=blk_zh`。
- ⚠️⚠️ **排版换行铁律（2026-08-13 用户拍板）**：**不为 blk.zh 人工加换行**。`\x01`（`_BR_PH`→`<br>`）只许保留提取期句子/段落间合法换行，**严禁**为「序号点 `N.`」「`※`」后注入。校验：dist 不应出现 `※<br>`/`N.<br>`/`数字<br>%`。
- ⚠️⚠️ **blk.zh 必须与 ja 对齐**：zh 不得出现连续 `\x01\x01`（`<br><br>` 撑长页面）或比 ja 少段（截断→块级回退日文）；须用 keys 逐段取 zh、按 ja 的 `\x01` 位置 `BR.join(segs)` 重建；写入后校验 `zh.count(\x01)==ja.count(\x01)`。
- ⚠️ **验证**：`dist/zh` 全站 grep `escah-ilink`/`char-ref` + TOC 含 `<a href="#` + 无双追加 + 无 `--[` 签名。

## 关键架构
- 原文 HTML → `sitegen._sanitize_html` → `site/.vitepress/frag/<slug>.{ja,zh}.json`；md `import frag` + `MirrorContent.vue` `v-html`（不可 ?raw）。`site/*.md`/sidebar 由 sync-site 重生成，勿手改。图片 `withBase('/img/')`。
- 角色 JSON `data/parsed/characters/<safe_id>.json`（name/name_zh/rarity/icon/release_date/sections）→ 复制到 `site/public/data/char/`。`CharHoverModal.displayName`：zh 站为 `name_zh（日文名）`。`release_date` 由 chara.py `_extract_release_dates()` 从 `data/parsed/ja/characters.html` 提取（浮窗"实装日期"行）。
- z-index：lightbox 300 > char-modal 271/mask 270 > char-hover 260 > 表格全屏 250 > VPNav 100。
- 正文超链接子页面（b-universe/equipment/raid/main-quest 子页）：仅由正文超链接进入、不进导航栏；链接改写（原站 `?页名`→`/zh/<slug>.html`）是 deferred 任务未做。`artists.html`=原画索引、`voice-actors.html`=声优一览。
- sitegen 特设页「日中用語対照表」slug 必须 `term-map`，不可用 `glossary`（会覆盖 WIKI 用語集镜像页 md）。
- 改某页"原网页链接(sourceUrl)"：`data/registry/pages.yaml` 该条目加 `url:` 字段（sitegen 已做 registry>manifest>SOURCE_BASE 优先级）。
- ⚠️⚠️ **新增页面正规流程铁律**：绝不在根目录甩 md / 手写 `site/*.md`。唯一路径：①`data/raw/<snapshot.page_filename() 的 URL 编码>.html` ②`data/registry/pages.yaml` 追加 `{name,slug,category,mode}` ③`parse`→`data/parsed/ja/<slug>.html`+`.chunks.json` ④`i18n build --pages <slug>` ⑤`i18n extract --pages <slug>`→`tools/_todo_translate/new_translation_<日期>.txt`，用户翻后 `_translated.txt`→`i18n fill` ⑥`sync-site`→`site/<ja|zh>/<slug>.md`；`config.ts` nav 挂 `/<locale>/<slug>.html`。

## 前端要点（site/.vitepress/theme）
- 组件（components/）：MirrorContent.vue（v-html+头像/浮窗处理）、CharHoverModal.vue（含実装日注入）、DocOutline.vue（自定义树状大纲，active 项自动滚入可视区，只滚目录栏不滚页面）、SiteAccessSwitch.vue（版本号 SITE_VERSION）、CategoryCards/MetaBar/MirrorChangelog/RecentUpdates/ScrollButtons/UpdateRecord/UpdatesLog/charModalStore.ts。
- Layout.vue 用 `#nav-bar-content-after` 挂自管 `VPNavBarSearch`（根 `.EscahNavSearch`），`custom.css` `.VPNavBarSearch{display:none!important}` 隐藏默认；`VPLocalSearchBox` 自包含、挂载即懒加载索引。`splitFragSections` 的 `titles` 末尾 `withPage()` 补页面标题。
- 表格：`.escah-tbl` 恒 `width:max-content!important; min-width:100%`；单元格只许 `overflow-wrap:break-word`，**禁 anywhere/break-all**；宽表 `.table-scroll` 横滚。`tableEnhancer.ts` 须选 `table.style_table`。
- `cleanUrls:false` → 内部链接须带 `.html`；改 theme 后删 `.vitepress/cache` 再 build；build EPERM：先 `Remove-Item .vitepress/.temp -Recurse -Force` 再 build。
- `config.ts` search.miniSearch 须自包含；preview rebuild 后须重启；`SearchLoading.vue` onClose 只复位视觉、mo 仅 onUnmounted 断 + 20s 硬超时。
- 侧边栏：sitegen `SIDEBAR_TREE` 生成 `generated/sidebar.{ja,zh}.json`，勿手改；分隔符 `__SB_DIV__` 必须用「真实页面+锚点」`/zh/characters.html#__SB_DIV__`（纯 hash 会被 VitePress 丢弃 DOM），text 用可见 `"—"` 再 CSS 隐藏；`character` 组不折叠、`guide/system/equipment/quest/misc` 默认折叠。
- ⚠️ 改 sidebar/config/词表后 **dev server 必须重启才生效**（config 不受 HMR）；验证侧边栏须 Edge 无头 `--dump-dom` 实测 dev，不能只读 generated json。
- 预览验证纪律：改完前端/sidebar 必须自己重启 preview 验证，绝不把验证成本推给用户；build 后 chunk hash 变，旧 preview(4173) serve 旧 HTML→旧 JS 404→整页前端失效，须杀旧 preview 干净重启。

## llm_reco 大模型推荐角色
- 目录 `llm_reco/`；已发布 `site/{zh,ja}/llm-recommend.md`。推理不得参考官方攻略/名单，须基于 `char_data.json`(370 角色)与机制事实自推。
- 量化模型 v0.8（`_char_score.py`）：固有效果才是区分度；降防 debuff >> 攻击 buff；觉醒（速度-2s扁平/必杀充能+6pt/攻魔+20%）、装备（火箭引擎/咆哮猛虎 速度-50%、冲击腰带 攻魔+50%）；maxDPS 6,595、TOP=レジェンド・ハルカ78.9。复用：补 `char_data.json`→重跑 `_char_score.py`。文档：reasoning-log §10/§11、reco-team §5、站点页第九节。

## 历史沿革（已归档，勿重建）
- ⚠️ **LLM 翻译方案早已弃用（非新任务）**：`_api_pipeline.py`/`_cmt_call.py`/`comment_translate.py`/`_llm_translations.json` 等已于 2026-07-24 判孤儿移 `recycle_bin/tools/`，活跃代码 0 引用。勿再生成"LLM 弃用重构"类 plan。
- 旧正则翻译引擎 `tools/zh_patch.py`(JA2ZH)/`char_zh.py` 已废弃，现行引擎=i18n.py（见「翻译工作流」）。`TRANSLATION_TODO.md`（批次 F+ 清单）仍是旧引擎时代的产物，勿按它执行。
- llm_reco v0.2~v0.7 被 v0.8 取代（属角色推荐，与翻译管线无关）。
