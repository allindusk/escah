# MEMORY — ESCH 超昂大战 WIKI 中日双语镜像站

> 长期记忆（就地更新，保持精简）。逐日过程细节见 `YYYY-MM-DD.md`，此处只留跨会话仍有效的结论。
> 末次整理：2026-08-05（压缩合并重复铁律，更新版本号）。

## 用户偏好（最高优先级）
- ⚠️⚠️⚠️ **每次 push 前必须升版本 + 写 changelog**：`SiteAccessSwitch.vue` 的 `const SITE_VERSION`（当前 **1.2.4**）+ `changelog.json` 顶部加该版本 `date`/`changes`。这是 AI 职责，绝不许推给用户；两者须一致、与当次改动匹配。
  - ⚠️⚠️ **changelog 是给「使用站点的用户」看的更新日志，不是开发笔记**：条目只写用户能感知的内容——修了什么看得见的 bug、新增/补全了什么页面或功能、翻译补全了哪些板块。**严禁写入开发细节**：不许提函数名/脚本名/文件名（如 i18n.py、pipeline、sync-site、link_terms.yaml、blk.zh、recycle_bin、git 操作等）、不许写根因分析、内部重构、构建流程。用户不需要也不关心这些。写之前自问：「普通访客读完这条知道网站哪里变好了吗？」写不出来的就别写。
- ⚠️⚠️ **push 须经用户当次明确指令，只覆盖该次**；绝不因"之前说过 push"连续推送。本地可自由 commit/build，push 一律等指令。
- **回收站约定**：过期/无用文件移 `recycle_bin/`（已被 `.gitignore` 忽略，物理保留），**绝不 git rm/永久删**。被 git 跟踪的临时脚本也应尽早移回收站，否则 `git add -A` 会把几百个调试文件带进提交。
- 后台运维纪律：①启动前 `Get-Process -Name python` 查重；②后台任务须有进度日志（`_bg.py`+锁+`[DONE]/[FAIL]`）。
- 助手不翻译成人正文。PowerShell 下勿用 `python -c`（Start-Process 拆号），改写脚本执行。
- ⚠️ **「这是项目设计」类结论必须先查 git 再下**：看到代码某逻辑，先用 `git diff`/`git log -p` 确认它是否在提交里，别把"工作区未提交误改"当项目设计甩锅。

## 项目概况
- 镜像 escalationheroines.wikiru.jp（PukiWiki）→ 本地构建 ja/zh 双语静态站；GitHub Pages（base `/escah/`）+ Cloudflare Pages（`/`，BASE=/）。push main 即触发 `.github/workflows/deploy.yml`（parse→sync-site→build→deploy）。
- 架构：Python 流水线 `pipeline/escah_pipeline` + VitePress `site/`（MPA，ja/zh 双 locale），层间以文件为契约。
- 数据真值：`data/parsed/i18n/`（人工译文唯一真值，**必须入库**，CI 直接读，不跑 i18n build/extract/fill）、`glossary/`（names/terms/skills/link_terms 词表，render-time 最高优先级覆盖，CI 直接读）；`data/parsed/{ja,zh,characters}`、`site/public`、`site/*.md`、`site/.vitepress/frag` 由流水线重建，**不入库**。`data/assets/img`（2386 图）LFS 入库。
- 运行顺序：`python -m escah_pipeline.cli sync-site` → `cd site && node build.mjs build`。⚠️ 改 i18n.py/模板/link_terms/词表后**必须 sync-site + build**，只 build 用旧 frag 缓存。
- ⚠️ **dev base 铁律**：`config.ts` 默认 `base:'/escah/'`；`build.mjs` dev 分支**不得**强制 `BASE='/'`；dev 地址 `http://localhost:5173/escah/`。
- 硬件 16 线程；不可并行：fetch / sync_site / build.mjs。搜索只能对部署站实测（`vite preview` 不能验证）。

## 翻译工作流（key 化 i18n）
- 流程：`i18n build` → `extract` → 译 → `fill` → `char-fill` → `sync-site` → build。中日同形算有效翻译。
- ⚠️ **`fill` 按 `[N]` 位置序号回填（非按 ja 内容）**：extract→fill 间未译集合变动会整体错位。损坏判别：某 key 的 ja 像标题但 zh 是长段落。修复=直改 `data/parsed/i18n/<slug>.json`。
- ⚠️ **`i18n build` 不套词表**（只做「记忆回贴」`zh=memory[norm(ja)]`），专名替换推迟到 `render_locale`。先烘焙后 build，修正原样保住。分段 ja 粒度变了→memory 查不到→`zh=""`（漏译）。
- ⚠️ **子页待译分类**：`extract_subpages.py` 把 b-universe/equipment/main-quest/raid 子页待译写到 `tools/_todo_translate/<cat>/`。回填后：待译原文→`tools/_texts_for_translation/`、已译(.bak)→`tools/_translated_texts/`、**清空** `_todo_translate/`。绝不可整树挪进 `_translated_texts/_todo_translate/`。

## 词表 glossary（render-time 覆盖，仅 zh）
- 三份手工词表（不被 build 覆盖）：`terms.yaml`（页面标题/章节/标签/值/内联）、`names.yaml`（~700 专名，**翻译绝对权威**）、`skills.yaml`（必杀/固有效果 ~2900 条）；加词只改 yaml→sync-site+build 生效，ja 站不受影响。
- `skills.yaml` 经 `_name_override`（用 `_norm_ns` 去空白二级索引，覆盖 100%）。
- ⚠️ **改专名译名（如 honey「甜心→哈尼」）盲区**：只改 yaml+烘焙不够，须同步改 ①`skills.yaml` 长键 zh 内专名子串 ②角色 JSON `zh`+顶层 `name_zh` ③`charRefs.json` ④`llm_reco` 手写 md。验证 `grep 旧译 site/.vitepress/dist`。
- ⚠️ **同形词/错译必须烘焙进 i18n JSON 源头**：渲染期 `_HF_ALL_NORM` 只保留 `k!=v`，同形词被整体跳过；子串替换要求 zh 含正确/日文形态。例：「想破→破念」救不了。
- ⚠️ **`_learn_corrections` 全局纠错污染（铁律）**：扫描全站 i18n JSON，某节点 `norm(ja)` 命中 glossary 专名且 `zh!=规范值` 会学出全局 corr 污染无关页。单节点 ja/zh 错位会把常见中文词改写成角色名（如「宝箱」→「昂扬花苞」）。`i18n.py` 已加安全阀（`set(zh)&set(canonical)` 为空即跳过）。真错译源节点必须回修 JSON。
- **烘焙脚本 `tools/_apply_glossary_to_i18n.py`**（ja 驱动，必跑）：规则0（整条 ja 精确命中→直接设 zh，不看现值）+ 规则1（分词对齐，段数相等对应段强制设词表值，不等则跳过）。⚠️ **全角标点（）必须归分隔符段**（否则段数不等被跳过）。规则2'（连续专名段匹配，修正 LLM 幻觉名/空格）+ 空保护。必须作为「fill 之后、sync-site 之前」的必跑步骤，否则每次翻译更新角色名退化为译法、浮窗失效。
- **渲染期块级回退（`render_locale`）**：节点级全齐备→`continue`；含 img/table→`continue` 保留结构；含 `<a>` 且块级译文完整→`_fill_block_keep_links`（保链、绝不回退日文）；无链接纯文本块→`el.text=blk_zh`。

## 正文超链接方案（句末【】标签，2026-08-11 重构，现行）
- ⚠️ **现行方案**：zh 镜像站正文链接**不再在句子中间切割注入**（旧 link_terms.yaml 的 zh 精确匹配脆弱，译名不一致即丢链/错乱）。改为渲染时读取**日文原页正文 `<a>`**（href + 日文文本），在每个中文句子/段落**末尾追加** `翻译文本【名称1】【名称2】` 标签，跳转绑定**原日文 href**（不依赖中文名匹配 → 译名不准也不丢跳转）。
- 显示名取 glossary 中文译名：`_link_display_zh(ja)` 优先级 names→skills→terms→high_freq，全部查不到兜底日文原文（理论上超链接词都应有翻译）。
- **表格特例**：单元格纯文本恰为单链接词（原文就只有这个词）→ 直接 `【名称】`（不重复显示译文）；单元格是句子 → `翻译文本【名称】`。
- 实现位置 `pipeline/escah_pipeline/i18n.py` 的 `render_locale`：渲染前解析模板收集正文 `<a>`（按 `_BLK_ATTR` 祖先归属 `block_links[bid]`，不在块的进 `top_links`），`drop_tag()` 去掉所有 `<a>` 壳；块级回退用 `block_links[bid]` 在 blk_zh 末追加 `【名称】`（class=`escah-ilink`），节点级 `_sub` 对 `top_links` 匹配 key["ja"] 追加；例外页(artists/voice-actors) 日文原文+句末【日文名】。前端 `custom.css` 样式 `.mirror-content a.escah-ilink`（紫色小角标）。
- 旧 `_apply_config_links`/`_wrap_block_links`/`_fill_block_keep_links`/`_fill_block_ja_links` 已不被主线调用（保留未删）；`glossary/link_terms.yaml` 仍被 `tools/_extract_link_todo.py` 离线工具用，但**渲染层不再依赖**（CI 不读它的链接匹配）。
- 验证：`dist/zh` 全站 grep `escap-ilink` + 检查无残留 `{{key}}`/空 `<a>` 壳。build 需 `NODE_OPTIONS=--max-old-space-size=8192`（全站打包 OOM）。

## 关键架构
- 原文 HTML → `sitegen._sanitize_html` → `site/.vitepress/frag/<slug>.{ja,zh}.json`；md 里 `import frag` + `MirrorContent.vue` `v-html`（不可 ?raw）。`site/*.md`/sidebar 由 sync-site 重生成，勿手改。图片走 `withBase('/img/')`。
- 角色 JSON `data/parsed/characters/<safe_id>.json`（name/name_zh/rarity/icon/sections）→ 复制到 `site/public/data/char/`。`CharHoverModal.displayName`：zh 站为 `name_zh（日文名）`。
- sitegen 特设页「日中用語対照表」slug 必须 `term-map`，不可用 `glossary`（会覆盖 WIKI 用語集镜像页）。
- z-index：lightbox 300 > char-modal 271/mask 270 > char-hover 260 > 表格全屏 250 > VPNav 100。
- 入口 `cli.py`；发现 `registry/plan`；抓取 `fetcher`；解析 `parser_puki/chara`；资源 `assets`；i18n `i18n.py`；站点生成 `sitegen.py`(`sync_site`/`_sanitize_html`/`render_locale`/`_strip_nav_links`)。`charRefs.json` 由 sync-site 末尾 `_regen_char_refs()` 自动重生。
- 正文超链接子页面（b-universe/equipment/raid/main-quest 子页）：仅由正文超链接进入、不进导航栏。`pages.yaml` 注册 `category:subpage`+ascii slug（`buniv-001` 等）。链接改写（原站 `?页名`→`/zh/<slug>.html`）是 deferred 任务，当前未做。

## 已修复阻断 bug（铁律）
- `cleanUrls:false` → 内部链接须带 `.html`；改 theme 后删 `.vitepress/cache` 再 build。
- 表格：`.escah-tbl` 恒 `width:max-content!important; min-width:100%`；单元格只许 `overflow-wrap:break-word`，**禁 anywhere/break-all**；宽表用 `.table-scroll` 横滚。`tableEnhancer.ts` 必须选 `table.style_table`（**绝不** `table.escah-tbl`）。
- `config.ts` search.miniSearch 被序列化 eval 重建→闭包丢失，**必须自包含**；preview rebuild 后须重启。
- `SearchLoading.vue`：`onClose` 里 `mo.disconnect()` 在空查询时断 MO→进度卡 99%，改为 onClose 只复位视觉、mo 仅 onUnmounted 断 + 20s 硬超时。
- 正文 `#id` 锚点：`_strip_nav_links` 丢弃 PukiWiki `anchor_super` 时若带 `id` 须保留占位 `<span id>`；改后须重跑 `i18n build` 重生成 template。
- 角色浮窗对内联头像不触发：`avatarMap` 未命中时用 `alt/title` 经 `nameAliases` 回 key（URL bytehex 截断不能反解，只能靠 alt）。
- 浮窗盖鼠标：`placeHover` 先选边→显式校验 `(mx,my)` 是否落浮窗矩形、命中则垂直推离；`MirrorContent` 加 document `mousemove`→`updateHoverPointer()`。
- PukiWiki region 折叠块消失：`toggleRgn` 改调 `_syncRgn` 按 `expanded` 类统一同步 desc/content/plus/minus；processEl 挂载时对所有 `.rgn-container` 调 `_syncRgn` 规整脏初始。
- build EPERM 环境坑：Windows 删 `.temp` 下含日文文件名临时文件偶发 EPERM→先 `Remove-Item .vitepress/.temp -Recurse -Force` 再 build。

## 本地搜索架构（VitePress LocalSearch）
- 结果主标题空白：`splitFragSections` 对每个 yield 的 `titles` 末尾 `withPage()` 补页面标题→结果主标题=页面名。
- 搜索框覆盖：`Layout.vue` 用 `#nav-bar-content-after` 插槽挂自管 `VPNavBarSearch`（根 `.EscahNavSearch`），`custom.css` 加 `.VPNavBarSearch{display:none!important}` 隐藏默认。`VPLocalSearchBox` 自包含（去 theme-default 内部 import，自写 `highlight()`）；去输入自动 debounce→点按钮/回车才 `runSearch()`；挂载即懒加载索引。

## 浮窗 / 链接验证铁律（2026-08-05 实战，重要）
- ⚠️ **`data-char` 是客户端运行时注入**：`MirrorContent.vue` 的 `onMounted→processEl→wrapPlainTextNames` 用 `charRefs.nameAliases` 对 `v-html` 文本节点匹配后 `setAttribute('data-char', 日文key)`。**静态 `dist/**/*.html` 里根本没有 `data-char`** → 验证浮窗**绝不** grep 静态 HTML（必得 0，误判"浮窗消失"）。正确：① Edge `--dump-dom` 实际渲染后查；② python 模拟 `wrapPlainTextNames` 估注入数。中文名浮窗天然已支持（nameAliases 含中文名→日文key，无需额外改动）。
- ⚠️ **全站校验不能只拿一页（b-universe）做样本**：验证"改动不破坏别的功能"必须遍历全站（所有 i18n JSON 或所有 dist 页）。

## 前端版本号
- `SITE_VERSION`（三位数：①大版本 ②新增功能 ③修改）当前 **1.2.4**（2026-08-05，b-universe 12 链接修复 + 工作区清理 + 累积译文/词表）。
- 版本日志源 `theme/changelog.json`（源码目录、入库，更新记录页按此渲染）。⚠️ 切勿放回 `.gen-data/`（sync-site 生成、被 gitignore，放进去 CI 报 'Could not resolve' 失败）。
- 升版本号+维护 changelog 由 AI 在每次 push 前主动完成。

## 侧边栏生成（sitegen.py SIDEBAR_TREE）
- 由 `SIDEBAR_TREE`(按 cat 分组) + `_sb_node()`(递归) + `_write_sidebars()`(顶层组循环读 `collapsed`) 生成 `site/.vitepress/generated/sidebar.{ja,zh}.json`，再被 `config.ts` import。勿手改。
- 分隔符 `__SB_DIV__`：必须用「真实页面+锚点」`/zh/characters.html#__SB_DIV__`（纯 hash 链接会被 VitePress 客户端丢弃 DOM），text 用可见 `"—"` 再 CSS 隐藏。
- `combined` 合并节点（如 `SSR | SR | R`）：`_sb_node()` 递归路径 和 `_write_sidebars()` 顶层路径都要识别并调 `_sb_combined_node()`。
- 顶层组 `collapsed`：`character` 组不折叠；`guide/system/equipment/quest/misc` 五个板块默认折叠。

## 预览验证纪律
- 改完前端/sidebar 必须自己重启 preview 验证、绝不把验证成本推给用户（绝不说"你硬刷新看看"）。
- build 后 chunk hash 变，旧 preview(端口4173) serve 旧 HTML→旧 JS 404→整页前端失效。须杀旧 preview 干净重启。`vite preview` 不能验证搜索。
- 自检 DOM：Edge 无头 `--dump-dom` 渲染后查 DOM，**永远用 dump-dom 验证渲染、不只读内联 JSON 字符串**（JSON 含数据≠DOM 渲染出来）。

## llm_reco 大模型推荐角色
- 目录 `llm_reco/`（reco-method/draft/reasoning-log/reco-team + 脚本）；已发布 `site/{zh,ja}/llm-recommend.md`。
- ⚠️ 推荐推理不得参考官方攻略/名单，须基于 `char_data.json`(370 角色)与机制事实自推，思维过程入文件夹。
- 机制结论：数值无区分度、**固有效果才是区分度**；体力 -2%/s→多队接力；**降防 debuff >> 攻击 buff**（75% 减伤 BOSS 收益 3 倍）；不撤退在 raid 被稀释、在主线/EX 才是神；BREAK>时停。
- 量化模型 v0.8（`_char_score.py`，输出 `_score_v08_out.txt`）：觉醒(行动速度-2s扁平下限3s/必杀充能+6pt上限15%/攻魔+20%)、装备(火箭引擎/咆哮猛虎 速度-50%、冲击腰带 攻魔+50%、副装贴片删、仁王纳豆删、降防仅 kit 自带)、maxDPS 6,595、TOP=レジェンド・ハルカ78.9。复用：补 `char_data.json`→重跑 `_char_score.py`。

## 历史沿革（已归档，勿重建）
- LLM 翻译管线(`llm_patch.py`等)与旧词表替换引擎(`zh_patch.py`/`char_zh.py`)弃用→`recycle_bin/tools/`。
- llm_reco v0.2~v0.7 被 v0.8 取代。

## 正文超链接子页面 slug 真值
- `artists.html`=原画索引（画师一览）；`voice-actors.html`=声优一览（角色声优）；`characters` 不是声优页。
