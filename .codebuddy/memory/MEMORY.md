# MEMORY — ESCH 超昂大战 WIKI 中日双语镜像站

> 长期记忆（就地更新，保持精简）。逐日过程细节见 `YYYY-MM-DD.md`，此处只留跨会话仍有效的结论。
> 末次整理：2026-08-14（压缩超链接/浮窗铁律，新增"持久删除页面块"铁律）。

## 用户偏好（最高优先级）
- ⚠️⚠️⚠️ **每次 push 前必须升版本 + 写 changelog**：`SiteAccessSwitch.vue` `const SITE_VERSION`（当前 **1.2.4**）+ `changelog.json` 顶部加该版本 `date`/`changes`。AI 职责，绝不许推给用户；两者须一致、与当次改动匹配。
  - ⚠️⚠️ **changelog 面向用户**：只写用户能感知的变化（修了什么 bug、补了什么页面/板块）。**严禁**提函数名/脚本名/文件名、根因、内部重构、构建流程。
- ⚠️⚠️ **push 须经用户当次明确指令**：只看当次消息有无明确 push 字样；对话总结里"已提交推送"≠用户授权。绝不顺延。
- **回收站约定**：过期/无用文件移 `recycle_bin/`（`.gitignore` 已忽略，物理保留），**绝不 git rm/永久删**。
- 后台运维：①启动前 `Get-Process -Name python` 查重；②后台任务须有进度日志（`_bg.py`+锁+`[DONE]/[FAIL]`）。
- 助手不翻译成人正文。PowerShell 下勿用 `python -c`（拆号），改写脚本执行。
- ⚠️ **临时文件用完即删（用户 2026-08-14 明确）**：调试/一次性脚本（`_tmp_*.py` 等）执行完**必须立即删除**，绝不残留让用户看到。⚠️ 注意：用户**从未**说过"对删除临时文件敏感/不希望删"，此前任何"用户不愿删临时文件"的记录均为误记——正确偏好是**不留临时文件**。⚠️ **删除操作直接静默执行，绝不弹需要用户点确认的命令**（2026-08-14 用户不在电脑前导致删除命令超时失败）；临时文件删除属安全清理，直接 `delete_file` 工具删，不必走 `execute_command` 等审批路径。
- ⚠️ **"项目设计"类结论必须先查 git 再下**：别把工作区未提交误改当设计甩锅。
- ⚠️⚠️ **AI 不得自创用户偏好/铁律**：任何"用户要求的设计约束"须能在对话记录或既有 MEMORY 找到出处；来源不明只能作待确认假设提问，**绝不允许**擅自执行+写进 MEMORY+自称"铁律/用户说过"（2026-08-12 曾把脑补的"角色浮窗纯预览不跳转"当铁律删 fullpage 链接被用户驳回撤回）。

## 项目概况
- 镜像 escalationheroines.wikiru.jp（PukiWiki）→ 本地构建 ja/zh 双语静态站；GitHub Pages（base `/escah/`）+ Cloudflare Pages（`/`，BASE=/）。push main 触发 `.github/workflows/deploy.yml`（parse→sync-site→build→deploy）。
- 架构：Python 流水线 `pipeline/escah_pipeline` + VitePress `site/`（MPA，ja/zh 双 locale）。
- 数据真值：`data/parsed/i18n/`（人工译文唯一真值，入库）、`glossary/`（names/terms/skills/link_terms 词表，render-time 最高优先级覆盖，入库）；`data/parsed/{ja,zh,characters}`、`site/public`、`site/*.md`、`site/.vitepress/frag` 由流水线重建不入库。`data/assets/img`（2386 图）LFS 入库。
- 运行顺序：`python -m escah_pipeline.cli sync-site` → `cd site && node build.mjs build`（`NODE_OPTIONS=--max-old-space-size=8192`）。⚠️ 改 i18n.py/模板/词表后**必须 sync-site + build**，只 build 用旧 frag 缓存。
- ⚠️ **dev base 铁律**：`config.ts` 默认 `base:'/escah/'`；dev 地址 `http://localhost:5173/escah/`。
- 不可并行：fetch / sync_site / build.mjs。搜索只能对**部署站**实测（`vite preview` 不能验证搜索）。

## 翻译工作流（key 化 i18n）
- 流程：`i18n build` → `extract` → 译 → `fill` → `char-fill` → `sync-site` → build。中日同形算有效翻译。
- ⚠️ **`fill` 按 `[N]` 位置序号回填（非 ja 内容）**：extract→fill 间未译集合变动会整体错位；损坏判别=某 key 的 ja 像标题但 zh 是长段落，修复=直改 `data/parsed/i18n/<slug>.json`。
- ⚠️ **fill 与 extract 的 `allow_ui_fragments` 模式必须对称**：若 extract 对某页传 `allow_ui_fragments=True`（如 official-help 含 UI 碎片），fill 的 `_untranslated_items(slug)` 也必须对同页传 `True`，否则 items 集合不含碎片 → `[N]` 整体错位 → 0 回填。`i18n.py` 的 `fill_todo()` 已对 `slug=="official-help"` 对称处理。
- ⚠️ **translated 文件须保留 `===X===` 段分隔符**：`i18n fill` 靠 `===A===`/`===B===` 分组（`_parse_labeled_sections`），翻译者交付 `_translated.txt` 时若删掉 `===X===` 头 → `sections` 为空 → 0 回填。若发现 0 回填先查 translated 是否缺 `===X===`（可补回 `===A===` 包裹）。
- ⚠️ **`i18n build` 不套词表**（只做记忆回贴），专名替换推迟到 `render_locale`。分段 ja 粒度变了→memory 查不到→`zh=""`（漏译）。
- ⚠️ **烘焙脚本 `tools/_apply_glossary_to_i18n.py` 有段重复 bug（2026-08-13）**：分词对齐会产生错误重复（`圆香·突击·突击`等），**暂勿依赖**。改专名译名走「names.yaml + 整串文本替换 i18n/characters JSON + sync-site 重生 charRefs」。
- ⚠️ **子页待译分类**：`extract_subpages.py` 把 b-universe/equipment/main-quest/raid 子页待译写到 `tools/_todo_translate/<cat>/`；回填后待译原文→`_texts_for_translation/`、已译(.bak)→`_translated_texts/`、**清空** `_todo_translate/`。
- ⚠️ **持久删除页面块铁律（2026-08-14 确立）**：`i18n build` 从 `data/parsed/ja/<slug>.html`（源 raw 重生成）重建 template+JSON，**手动删 template/JSON 会被 build 复活**。要永久隐藏某块（如 official-help 页末ライセンス 模块）必须在 `build_page()` 渲染期（sanitized→frag 后、`_wrap_runs` 前）按文本从 frag 删除该节点及其后续兄弟，使其不再生成 key。不要改 template/JSON 做"删除"。

## 词表 glossary（render-time 覆盖，仅 zh）
- 三份词表：`terms.yaml`（标题/章节/标签/值/内联）、`names.yaml`（~700 专名，**翻译绝对权威**）、`skills.yaml`（必杀/固有效果 ~2900 条）；加词只改 yaml→sync-site+build 生效，ja 站不受影响。
- ⚠️ **改专名译名盲区**：只改 yaml 不够，须同步改 ①`skills.yaml` 长键 zh 内专名子串 ②角色 JSON `zh`+顶层 `name_zh` ③`charRefs.json`（sync-site 重生）。验证 `grep 旧译 site/.vitepress/dist`。
- ⚠️ **同形词/错译必须烘焙进 i18n JSON 源头**：渲染期 `_HF_ALL_NORM` 只保留 `k!=v`，同形词被整体跳过。
- ⚠️ **`_learn_corrections` 全局纠错污染铁律**：某节点 `norm(ja)` 命中 glossary 专名且 `zh!=规范值` 会学出全局 corr 污染无关页（`i18n.py` 已加安全阀 `set(zh)&set(canonical)` 为空即跳过）。真错译源节点必须回修 JSON。
- 渲染期块级回退（`render_locale`）：节点级全齐备→`continue`；含 img/table→`continue` 保留结构；含 `<a>` 且块级译文完整→保链、绝不回退日文；无链接纯文本块→`el.text=blk_zh`。
- ⚠️⚠️ **排版换行铁律（2026-08-13 用户拍板）**：**不为 blk.zh 人工加换行**。`\x01`（`_BR_PH`，渲染期还原 `<br>`）只许保留 PukiWiki 提取期带来的**句子间/段落间**合法换行。**严禁**为「序号点 `N.`」「`※` 标记」后人工注入 `\x01`。`_auto_br.py` 已废弃勿跑。校验：dist 不应出现 `※<br>`/`N.<br>`/`数字<br>%`。
- ⚠️⚠️ **blk.zh 必须与 ja 对齐、不可截断/双换行（2026-08-14 事故补丁）**：批量直译 blk 时若 zh 出现 `\x01\x01`（连续双换行→dist 里 `<br><br>` 撑长一倍页面）或 zh 比 ja 少段（截断→块级回退日文），须用 `keys` 列表逐段取各 key.zh、按 ja 的 `\x01` 位置 `BR.join(segs)` **重建 blk.zh**。任何 blk.zh 写入后须校验 `zh.count(\x01)==ja.count(\x01)` 且无连续 `\x01\x01`。中文换行点必须=日文换行点。

## 正文超链接 + 角色浮窗（2026-08-12 淬炼）
- ⚠️⚠️ **图片绝不动（用户铁律）**：任何 img（行内头像 `<span data-char><img>`、`<a><img></a>` 等）原样保留，绝不可删/换字。i18n.py `render_locale` 三处强制：①`span[data-char]` 含 img 须 `continue`；②`for a` 遇 `a.xpath(".//img")` 须 `continue`；③块级回退开头 `if el.xpath(".//img"): continue`。
- ⚠️⚠️ **"超链接放句尾"只针对真正 `<a>` 跳转链接**，绝不扩展到头像 img/角色名浮窗。
- ⚠️⚠️ **中文链接必须照搬日文（用户三令五申）**：zh 正文超链接数量/位置/结构须与日文原页一一对应，绝不凭空多造/丢失。
- ⚠️⚠️ **所有站内页面链接文字一律显示页面中文名**（faq→常见问题、gacha→扭蛋等，非 characters 浮窗/外链/纯#锚点）。ja 站保留日文原貌。实现 `_page_name_for_href()`+`_disp_name(locale="zh")` 返回 `_PAGE_SLUG_ZH`。
- ⚠️ **角色名浮窗原位保留、绝不移到句末**：zh 引擎对 `data-char` span（非头像 img、非 plugin-tooltip）**原位升级 `class=char-ref`**（文本填中文显示名），绝收进句末【】。`<span class="char-ref" data-char="日文名">【中文名】</span>` 浅描边胶囊、虚线下划线、`font-size:1em`。ja 站保留原位日文角色名（plugin-tooltip 蓝气泡），绝不显中文/移句末（用户原话"日文镜像页你也用句尾加超链接方案还把日文名翻译成中文名，你有病吧"）。
- ⚠️ **评论签名 `--[ID]时间` 必须剥离（双保险，2026-08-14 加固）**：`_COMMENT_SIG_RE`+`_COMMENT_SIG_CLEAN_RE`（覆盖中文破折号后 `--[` 如 `——--[`）两道都在 `_strip_comment_sig`。**两处必须都调**：①节点级 key ②无链接块级块走 `_set_block_html` 整块替换**前也必须 `_strip_comment_sig`**（此前漏调 → 任何带签名无链接块级 blk 复发）。数据层残留用脚本遍历顶层 keyN/blkN 批量清（顶层非 `data["keys"]` 嵌套），搜 `--[` 0 匹配收尾。
- ⚠️ **`plugin-tooltip` 块级必须退回节点级（2026-08-14 铁律）**：块级回退的"含角色名标记则 continue 退回节点级"xpath **必须同时匹配 `plugin-tooltip`**（它无 `data-char`）——否则含 plugin-tooltip 的块走整块纯文本替换会**清空浮窗结构**导致浮窗失效。匹配式：`span[(@data-char or contains(@class,'char-ref') or contains(@class,'plugin-tooltip'))][not(.//img)]`。
- ja 分支（locale=="ja"）保留模板 `<a>` 壳；块级外链接原地中文化 `class=escah-ilink`（紫胶囊点击跳转），角色名降级 `data-char` 浮窗去 href；块内链接 drop 句中壳、块级回退优先原地包裹否则句末追加【名称】；显示名优先级 `_disp_name`：①`_CUR_JA_ZH` ②names→skills→terms→high_freq ③`_LINK_HREF_ZH` ④兜底日文（角色名必走 names.yaml）。
- ⚠️ 过滤 PukiWiki 编辑/管理类链接（`?cmd=edit|table_edit|backup|source|...`）；过滤编辑戳 `--[编辑者]YYYY-MM-DD(周X)HH:MM:SS`。
- ⚠️ **TOC 目录锚点不可 drop**：页内 `<a href="#...">` 保留 `<a>` 壳（只跳过作链接源 drop），否则目录变纯文本。`_relink_toc` 标题匹配需剥离 †。
- 去重：同块内同角色只追加一次。
- ⚠️ **验证**：`dist/zh` 全站 grep `escah-ilink`/`char-ref` + TOC 含 `<a href="#` + 无双追加；须遍历全站。

## 关键架构
- 原文 HTML → `sitegen._sanitize_html` → `site/.vitepress/frag/<slug>.{ja,zh}.json`；md `import frag` + `MirrorContent.vue` `v-html`（不可 ?raw）。`site/*.md`/sidebar 由 sync-site 重生成，勿手改。图片 `withBase('/img/')`。
- 角色 JSON `data/parsed/characters/<safe_id>.json`（name/name_zh/rarity/icon/sections）→ 复制到 `site/public/data/char/`。`CharHoverModal.displayName`：zh 站为 `name_zh（日文名）`。
- sitegen 特设页「日中用語対照表」slug 必须 `term-map`，不可用 `glossary`。
- z-index：lightbox 300 > char-modal 271/mask 270 > char-hover 260 > 表格全屏 250 > VPNav 100。
- 入口 `cli.py`；`charRefs.json` 由 sync-site 末尾 `_regen_char_refs()` 重生。
- 正文超链接子页面（b-universe/equipment/raid/main-quest 子页）：仅由正文超链接进入、不进导航栏；链接改写（原站 `?页名`→`/zh/<slug>.html`）是 deferred 任务未做。`artists.html`=原画索引、`voice-actors.html`=声优一览。
- ⚠️⚠️ **新增页面正规流程铁律（2026-08-13 确立）**：绝不在根目录甩 md / 手写 `site/*.md`。唯一路径：`①data/raw/<snapshot.page_filename() 的 URL 编码>.html`（如 `公式ヘルプ`→`%E5%85%AC...html`）②`data/registry/pages.yaml` 追加 `{name,slug,category,mode}` ③`parse`→`data/parsed/ja/<slug>.html`+`.chunks.json` ④`i18n build --pages <slug>` ⑤`i18n extract --pages <slug>`→`tools/_todo_translate/new_translation_<日期>.txt`，用户翻后 `_translated.txt`→`i18n fill` ⑥`sync-site`→`site/<ja|zh>/<slug>.md`；`config.ts` nav 挂 `/<locale>/<slug>.html`。

## 已修复阻断 bug（铁律）
- `cleanUrls:false` → 内部链接须带 `.html`；改 theme 后删 `.vitepress/cache` 再 build。
- 表格：`.escah-tbl` 恒 `width:max-content!important; min-width:100%`；单元格只许 `overflow-wrap:break-word`，**禁 anywhere/break-all**；宽表 `.table-scroll` 横滚。`tableEnhancer.ts` 须选 `table.style_table`。
- `config.ts` search.miniSearch 须自包含；preview rebuild 后须重启。
- `SearchLoading.vue`：onClose 只复位视觉、mo 仅 onUnmounted 断 + 20s 硬超时。
- `#id` 锚点：`_strip_nav_links` 丢弃 `anchor_super` 时若带 `id` 须保留 `<span id>`；改后须重跑 `i18n build`。
- 角色浮窗对内联头像不触发：`avatarMap` 未命中时用 `alt/title` 经 `nameAliases` 回 key。
- 浮窗盖鼠标：`placeHover` 先选边→显式校验 `(mx,my)` 是否落浮窗矩形、命中则垂直推离。
- PukiWiki region 折叠块：`toggleRgn` 调 `_syncRgn` 统一同步；processEl 挂载时对所有 `.rgn-container` 调 `_syncRgn`。
- build EPERM：Windows 删 `.temp` 下日文文件名临时文件偶发 EPERM→先 `Remove-Item .vitepress/.temp -Recurse -Force` 再 build。

## 本地搜索架构（VitePress LocalSearch）
- 结果主标题空白：`splitFragSections` 对每个 yield 的 `titles` 末尾 `withPage()` 补页面标题。
- 搜索框覆盖：`Layout.vue` 用 `#nav-bar-content-after` 挂自管 `VPNavBarSearch`（根 `.EscahNavSearch`），`custom.css` `.VPNavBarSearch{display:none!important}` 隐藏默认；`VPLocalSearchBox` 自包含、去自动 debounce、挂载即懒加载索引。

## 前端版本号
- `SITE_VERSION`（三位数：大版本/新增功能/修改）当前 **1.2.4**（2026-08-05）。
- 版本日志源 `theme/changelog.json`（入库）。升版本+维护 changelog 由 AI 在每次 push 前主动完成。

## 侧边栏生成（sitegen.py SIDEBAR_TREE）
- `SIDEBAR_TREE` + `_sb_node()` + `_write_sidebars()` 生成 `site/.vitepress/generated/sidebar.{ja,zh}.json`，被 `config.ts` import，勿手改。
- 分隔符 `__SB_DIV__`：必须用「真实页面+锚点」`/zh/characters.html#__SB_DIV__`（纯 hash 链接会被 VitePress 客户端丢弃 DOM），text 用可见 `"—"` 再 CSS 隐藏。
- 顶层组 `collapsed`：`character` 组不折叠；`guide/system/equipment/quest/misc` 五个板块默认折叠。

## 预览验证纪律
- 改完前端/sidebar 必须自己重启 preview 验证、绝不把验证成本推给用户（绝不说"你硬刷新看看"）。
- build 后 chunk hash 变，旧 preview(4173) serve 旧 HTML→旧 JS 404→整页前端失效，须杀旧 preview 干净重启。`vite preview` 不能验证搜索。
- 自检 DOM：Edge 无头 `--dump-dom` 渲染后查 DOM，永远用 dump-dom 验证渲染、不只读内联 JSON 字符串。

## llm_reco 大模型推荐角色
- 目录 `llm_reco/`；已发布 `site/{zh,ja}/llm-recommend.md`。
- 推荐推理不得参考官方攻略/名单，须基于 `char_data.json`(370 角色)与机制事实自推。
- 量化模型 v0.8（`_char_score.py`）：固有效果才是区分度；降防 debuff >> 攻击 buff；不撤退在 raid 被稀释、在主线/EX 是神；BREAK>时停。觉醒(行动速度-2s扁平/必杀充能+6pt/攻魔+20%)、装备(火箭引擎/咆哮猛虎 速度-50%、冲击腰带 攻魔+50%)。maxDPS 6,595、TOP=レジェンド・ハルカ78.9。复用：补 `char_data.json`→重跑 `_char_score.py`。

## 历史沿革（已归档，勿重建）
- ⚠️ **LLM 翻译方案早已弃用（非新任务）**：`_api_pipeline.py`/`_cmt_call.py`/`comment_translate.py`/`_llm_translations.json` 等 LLM 脚本与产物已于 2026-07-24 判定为孤儿、移入 `recycle_bin/tools/`，活跃代码 0 引用。翻译引擎 = `zh_patch.py`(JA2ZH) + `char_zh.py`（活跃核心，勿当"旧引擎"弃用）。勿再生成"LLM 弃用重构"类 plan。
- llm_reco v0.2~v0.7 被 v0.8 取代（属角色推荐，与翻译管线无关）。
