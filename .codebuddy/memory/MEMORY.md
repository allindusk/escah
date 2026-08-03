# MEMORY — ESCH 超昂大战 WIKI 中日双语镜像站

> 长期记忆（就地更新，保持精简）。逐日过程细节见 `YYYY-MM-DD.md`，此处只留跨会话仍有效的结论。
> 末次整理：2026-08-01（合并去重）。

## 用户偏好（最高优先级）
- ⚠️⚠️⚠️ **每次推送（git push）前，助手必须同步更新「版本更新文档」**：升 `SITE_VERSION`（`site/.vitepress/theme/components/SiteAccessSwitch.vue` 的 `const SITE_VERSION`）+ 在 `site/.vitepress/theme/changelog.json` 顶部加该版本的 `date`/`changes`。**版本号更新与 changelog 是 AI 助手的职责，不是用户的事**——绝不允许把"该写版本更新文档"推给用户。两者必须保持一致、与当次改动匹配。
- ⚠️⚠️ **推送 GitHub（git push）须经用户当次明确指令，且只覆盖该次；绝不因"之前那次说过 push"就自行连续推送**。用户的"commit+push"只授权当次那一个动作，后续修复/重构若还要 push，必须再次征求确认。本地可自由 commit / build 验证，但 push 一律等指令。
- **回收站约定**：过期/无用文件移 `recycle_bin/`，**绝不 git rm/永久删**。
- 后台运维纪律：①启动前 `Get-Process -Name python` 查重；②后台任务须有进度日志（`_bg.py`+锁+`[DONE]/[FAIL]`）；③能自行判断 bug/卡住。
- 助手不翻译成人正文。
- PowerShell 下勿用 `python -c`（Start-Process 会拆分号），改写脚本文件执行。

## 项目概况
- 镜像 escalationheroines.wikiru.jp（PukiWiki）→ 本地构建 ja/zh 双语静态站；GitHub Pages（base `/escah/`）+ Cloudflare Pages（`/`，BASE=/）。
- 架构：Python 流水线 `pipeline/escah_pipeline`（discover/fetch/parse/assets/i18n/chara/sync-site）+ VitePress `site/`（MPA，ja/zh 双 locale），层间以文件为契约。
- **部署：push 到 main 即触发** `.github/workflows/deploy.yml`（parse→sync-site→build→deploy）。本地只需 commit+push，勿手推 dist。
- 数据：`data/raw`（快照，git+LFS）+ `data/manifest.json`；`data/parsed/{ja,zh,characters}`、`site/public`、`site/*.md`、`site/.vitepress/frag` 均由流水线重建，**不入库**（`data/parsed/*` 忽略，仅 `!data/parsed/i18n/` 例外）；`data/assets/img`（2386 图）LFS 入库。
- ⚠️ **`data/parsed/i18n/` 是人工译文唯一真值，必须入库**——CI 构建 zh 站直接读它（不跑 i18n build/extract/fill）。改译文后须 commit，否则部署不生效。
- 硬件 16 线程；不可并行：fetch / sync_site / build.mjs。`vite preview`(sirv) 不能验证搜索，搜索只能对部署站实测。
- 运行顺序：`python -m escah_pipeline.cli sync-site` → `cd site && node build.mjs build`。

## 翻译工作流（key 化 i18n）
- 流程：`i18n build` → `extract`（`new_translation_<date>.txt`+`_translated.txt`）→ 译 → `fill` → `char-fill` → `sync-site` → build。中日同形算有效翻译。
- ⚠️ **子页待译分类**：`tools/extract_subpages.py` 把 4 类（b-universe/equipment/main-quest/raid）子页待译写到 `tools/_todo_translate/<cat>/`（含 `new_translation_<date>.txt` 待译原文 + 空白 `_translated.txt`）。**归档清理铁律**：翻译回填后，待译原文 → `tools/_texts_for_translation/<cat>/`，已译译文（.bak）→ `tools/_translated_texts/<cat>/`，最后**清空** `tools/_todo_translate/`。**绝不可整树塞进 `tools/_translated_texts/_todo_translate/`**（那是整体挪动、违反分类规则，且移动时易丢待译原文）。待译原文若丢失，重跑 `extract_subpages.py`（改其 TODO_ROOT）确定性补回，不丢数据。
- ⚠️ **`fill` 按 `[N]` 位置序号回填（非按 ja 内容）**：extract 与 fill 之间未译集合若变动会整体错位。损坏判别：某 key 的 ja 像标题但 zh 是长段落。修复=直改 `data/parsed/i18n/<slug>.json`。
- ⚠️ **`i18n build` 不套词表**（i18n.py 817-818，专名替换推迟到 `render_locale`），只做「记忆回贴」`zh = memory[norm(ja)]`，memory 取自跑之前的该 JSON 自身。故**先烘焙后 build，修正原样保住，不会被错误覆盖**。唯一例外：某分段 ja 切分粒度变了→memory 查不到→`zh=""`（漏译，非错译）。
  - 早前笔记「build 套 names/skills.yaml 产生 31 条漂移（歼忍 影→歼忍歼忍影影）」对当前代码**不成立**（旧版行为或渲染期差异），已作废勿再引用。

## 词表 glossary（render-time 最高优先级覆盖，仅 zh）
- 三份手工词表（不被 build 覆盖）：`terms.yaml`（page_titles/char_sections/labels/values/inline_terms）、`names.yaml`（~700 专名，**翻译绝对权威**）、`skills.yaml`（必杀技/固有效果 JA→ZH，~2900 条）。加词只改 yaml → `sync-site`+build 生效，无需重建 i18n JSON；ja 站不受影响。
- **`skills.yaml` 应用点**：`char_fill_all`（写 parsed→public/data/char，供浮窗）与 `render_locale`（整页）都走 `_name_override`。源 JA 与线上 JA 常有空白/换行漂移，故用 `_norm_ns`（去全部空白）二级索引，覆盖 2700/2700=100%。（曾报的「46% 死」是诊断脚本误用 NFKC 的假警报，勿信。）
- **`_correct_text` 覆盖顺序**：`_NAME_RE` → `_CORR_RE`（names 全量 + high_freq `_precise` 子集，带 `_split_name_suffix` 后缀健壮化）→ `_high_freq_override` → `_term_sub_override`。
- `_precise` 白名单在 `high_freq.yaml` 末段；其中非纯片假名条目做句中子串纠正（`_high_freq_precise_sub`，**仅节点级 zh，不对整段 html**——否则误改 `data-char` 属性致浮窗失效）。
- ⚠️ **渲染期覆盖救不了「想破→破念」这类错译（铁律）**：`_HF_ALL_NORM` 只保留 `k!=v`，**同形词（`想破:想破`）被整体跳过**；且子串替换要求 zh 含正确或日文形态，"破念"两者都不含。→ **同形词/错译必须烘焙进 i18n JSON 源头**。
- ⚠️ **改专名译名（如 honey 系「甜心→哈尼」）的改动盲区（铁律，2026-08-02 实战）**：只改 yaml + 烘焙 i18n 不够，渲染期 `_name_override` 会整句命中 `skills.yaml` 长键、且多处独立字段覆盖回旧译。必须同步改：①`skills.yaml` 长键 zh 里的专名子串（如「『甜心打火机』」）；②`data/parsed/characters/*.json` 的 `zh` 字段**及顶层 `name_zh` 字段**（脚本遍历易漏 name_zh）；③`site/.vitepress/theme/charRefs.json` 的「中文名→id」反向映射；④`llm_reco` 手写 `site/{zh,ja}/llm-recommend.md`。验证以 `grep 旧译 site/.vitepress/dist` 为准（含 zh/ja/char json/theme chunk）。
- **烘焙脚本 `tools/_apply_glossary_to_i18n.py`**（ja 驱动，把 high_freq+names+skills 写进 `data/parsed/i18n/**`）：
  - 规则0（最高优先）：整条 ja 精确命中词表（含 strip/去空白容错）→ 直接设 zh，不看现值。
  - 规则1：分词对齐——ja/zh 按「CJK/字母数字段 + 分隔符段」切分，段数相等时对应段强制设词表值；段数不等则跳过（安全，绝不瞎猜）。
  - ⚠️ **全角标点（）必须归分隔符段**，否则 ja 半角 () 切 4 段、zh 全角（）切 1 段 → 段数不等被跳过（初版踩过）。
  - 历史执行：9433ecd（416 文件/10646 条，"破念"清零）、fbdb94c（规则0 补强，408 文件/3911 条）。
- 精炼技能译已注入 `data/parsed/i18n/characters/<stem>.json`（345 角色/1216 单元格）。⚠️ `i18n build/extract/fill` 会覆盖该目录，须重跑注入脚本（`tools/_gen_skill_glossary.py`）。
- `レガリアの神騎` 系列读音用户拍板 **米加尔/玛雅尔**（非梅加艾尔/玛雅艾尔）；旧读音靠 `_READING_CORR` + render_locale 末尾 zh html 子串收口。
- 男主 戦部トキサダ（战部时贞）称呼变体已加；不翻译名单（FM77 等）`name_zh` 留空。
- ⚠️ 改 names.yaml 读音后须 `extract_all_characters(force=True)` 重生成角色 JSON（sync-site 只复制不重建）。

### 词表注入逻辑：`render_locale` 块级回退（2026-08-03 增强，未提交）
> 节点级译文由 `_sub` 走 `_term_override → _name_override → _high_freq_* → _correct_text`（见上）。
> 块级（整句 blkN）缺译时走 `render_locale` 的「块级回退」分支，本次改动在此分支：
> - 入口：`if _BLK_ATTR in tpl` → 遍历 `@data-blkN` 元素，取 `blocks[bid]`。
> - **全节点级已译** → `continue`（保留行内结构，不整块换）。
> - **含 img/table** → `continue`（保留结构，交由顶层 `_sub` 节点级回退；铁律：块级整段换会丢图/丢表）。
> - **含 `<a>` 链接且块级译文完整但部分子 key 缺译** → 新增 `_fill_block_keep_links(el, blk, keys, blk_zh, locale)`：
>   - 不整块换成纯文本（会丢 `<a>` 跳转），也不 `continue`（会露日文）。
>   - 做法：按各 key 的 ja 长度比例，把完整块级 zh 连续切分成与各 key 对应的中文区间；遍历块内文本节点与 `<a>` 文本，把缺译 key 的 `{{keyN}}` 占位符就地替换为对应片段；`<a>` 结构原样保留。
>   - blk_zh 在 zh locale 下先过 `_name_override`（命中则替换）/否则 `_correct_text`（错译/子串纠正）。
> - **无链接的纯文本块** → 删子元素、`el.text = blk_zh`（原逻辑，整块换纯文本 zh）。
> - 上下文：新增函数 `_fill_block_keep_links`（i18n.py ~1345）；改动在 `render_locale`（~1406）块级回退分支。喂数来自 `data/parsed/i18n/<slug>.json` 的 blocks/keys。
> - 验证：含链接的整句块（如某页内带跳转链接的长段落）在 zh 站应既保链接又无日文露底；`grep 日文 site/.vitepress/dist/<页>` 不应再出现该块漏译。
> - ⚠️ 此改动**未 commit**，仅工作区；切换大模型或部署前须先 commit `pipeline/escah_pipeline/i18n.py` + `glossary/names.yaml` + 重生成的 `data/parsed/i18n/*.template.html`。

## 关键架构
- 原文 HTML → `sitegen._sanitize_html` → `site/.vitepress/frag/<slug>.{ja,zh}.json`；md 里 `import frag` + `MirrorContent.vue` `v-html`（**不可 ?raw**）。`site/*.md`/sidebar 由 sync-site 重生成，勿手改。图片走 `withBase('/img/')`。
- 角色 JSON `data/parsed/characters/<safe_id>.json`（name/name_zh/rarity/icon/sections）→ 复制到 `site/public/data/char/`。`CharHoverModal.displayName`：zh 站为 `name_zh（日文名）`。
- sitegen 特设页「日中用語対照表」slug 必须为 `term-map`，**不可用 glossary**（会覆盖 WIKI 用語集镜像页）。
- z-index 自顶向下：lightbox 300 > char-modal 271 / mask 270 > char-hover 260 > 表格全屏 `.escah-tbl-fs` 250 > VPNav 100。

## 新增/更新页面工作流（大模型接手必读，细化到文件与接口）
> 所有命令经 `python -m escah_pipeline.cli <cmd>` 在仓库根目录执行。管线以「文件为契约」：
> `data/raw`（LFS 快照）→ `data/manifest.json` → `data/parsed/{ja,zh,characters}` → `site/public`+`site/*.md`+`site/.vitepress/frag`（均不入库，CI 重建）。

### A. 镜像「原站已有、但本站还没镜像」的新页面
1. **发现**：`cli discover`
   - 调 `registry.discover()`：两阶段爬 MenuBar → 观察页、キャラクター一覧 → 角色详情页，写 `data/mirror_plan.yaml`（planned/mirrored）。
   - 调 `plan.sync_plan()`：把已爬到的 URL 落成 `mirrored` 条目。
2. **抓取**：`cli fetch [--pages 名1 名2] [--force]`
   - 调 `fetcher.fetch_registered_pages()`：按 mirror_plan 注册表抓 HTML 快照到 `data/raw/`（断点续抓，哈希去重；`--force` 全量重抓；`--mode all/watch/static`）。
3. **解析**：`cli parse [--pages ...] [--force]`
   - 调 `parser_puki.parse_all()`：快照 → `data/parsed/ja/<slug>.md`（日文 Markdown）。
   - 调 `chara.extract_all_characters(force=)`：角色页 → `data/parsed/characters/<safe_id>.json`（name/name_zh/rarity/icon/sections）。**改 names.yaml 读音后必须 `force=True` 重跑**（sync-site 只复制不重建）。
4. **资源**：`cli assets [--force]`
   - 调 `assets.download_assets()`：下页面引用图，哈希命名入 `data/assets/img/`（LFS）。
5. **翻译（i18n 流水线，取代旧 zh_patch 正则）**：
   - `cli i18n build [--pages ...]`：调 `i18n.build_all()` → 生成 `data/parsed/i18n/<slug>.template.html` + `<slug>.json`（节点级 keyN / 整句块 blkN；`_norm`+`_norm_ns` 二级索引；中日同形算有效翻译）。**`data/parsed/i18n/` 是人工译文唯一真值，必须入库**（CI 直接读它，不跑 build/extract/fill）。
   - `cli i18n extract [--pages ...]`：调 `i18n.extract_todo()` → 写待译清单 `tools/_todo_translate/<cat>/new_translation_<日期>.txt`（待译原文）+ 空白 `<日期>_translated.txt`。
     - **4 类子页（b-universe/equipment/main-quest/raid）待译**由 `tools/extract_subpages.py` 分类写到 `tools/_todo_translate/<cat>/`（改其 TODO_ROOT 可确定性补回）。
   - 译：人工/LLM 把中文填进 `<日期>_translated.txt`。
   - `cli i18n fill [--todo 文件名] [--pages ...]`：调 `i18n.fill_latest_todo()`（或指定 `--todo`）→ 按 `[N]` 序号回填 JSON（**非按 ja 内容**，extract→fill 间未译集合变动会错位）。成功后待译原文 → `tools/_texts_for_translation/<cat>/`、已译 → `tools/_translated_texts/<cat>/`、清空 `_todo_translate/`。
   - `cli i18n char-fill`：调 `i18n.char_fill_all()` → 给角色 JSON 的 `zh` 字段（及顶层 `name_zh`）补写中文，取代旧 `char_zh.py`。
6. **生成站点**：`cli sync-site`
   - 调 `sitegen.sync_site()`：读 `data/parsed/{ja,zh}`+角色 JSON → 生成 `site/*.md`、sidebar、`site/.vitepress/frag/<slug>.{ja,zh}.json`（对 has_i18n 页用 render_locale 直落 frag）。
   - 自动调 `_regen_char_refs()`：重生成 `site/.vitepress/theme/charRefs.json`（中文名→id 反向映射，角色名一变就得重生成，否则中文页浮窗失效）。
7. **构建**：`cd site && node build.mjs build`（或 `dev` 预览）。改 theme 后删 `.vitepress/cache` 再 build。
8. **部署**：commit `data/parsed/i18n/*` + 源码改动 → `git push`（须用户当次指令）→ CI（`.github/workflows/deploy.yml`）跑 parse→sync-site→build→deploy。push 前升 `SITE_VERSION`+写 `changelog.json`（见用户偏好）。

### B. 自动同步原站更新（已有页内容变化）
- `cli update [--full] [--no-translate]`：调 `updater.run_update()` → 处理 planned + RSS 增量检测变更 → 自动重抓/重解析/重翻译。`--full` 全量逐页比对最后编辑时间；`--no-translate` 跳过 i18n 应用。
- 旧一键 `cli translate [--pages ...]`：调 `updater._run_zh_patch()`（旧 zh_patch 正则路径，仅兼容，新页面勿用）。

### C. 只改译名/专名（不新增页面）
- 改 `data/parsed/i18n/*.json` 源头（同形词/错译必须烘焙进 JSON，渲染期救不了）；
- 或改词表 `terms.yaml`/`names.yaml`/`skills.yaml` → `sync-site`+build 生效（ja 站不受影响）。
- 改专名译名须同步四处：①`skills.yaml` 长键 zh 内专名子串；②角色 JSON `zh` + 顶层 `name_zh`；③`charRefs.json`；④`llm_reco` 手写 md。验证 `grep 旧译 site/.vitepress/dist`。

### D. 关键文件/接口速查
- 入口：`pipeline/escah_pipeline/cli.py`（argparse，`build_parser` 定义全部子命令与参数）。
- 发现/注册：`registry.py`(`discover`)、`plan.py`(`sync_plan`)。
- 抓取：`fetcher.py`(`fetch_registered_pages`)。解析：`parser_puki.py`(`parse_all`)、`chara.py`(`extract_all_characters`)。
- 资源：`assets.py`(`download_assets`)。i18n：`i18n.py`(`build_all`/`extract_todo`/`fill_latest_todo`/`char_fill_all`/`migrate_all`)。
- 站点生成：`sitegen.py`(`sync_site`、`_sanitize_html`、`render_locale`、`_strip_nav_links`)。角色引用：`charRefs` 重生在 `cli.sync-site` 末尾 `_regen_char_refs()`。
- 前端渲染：`site/.vitepress/theme/components/MirrorContent.vue`（v-html 容器 + 交互）、`tableEnhancer.ts`、`custom.css`。

## 已修复阻断 bug（铁律）
- `cleanUrls:false` → 内部链接须带 `.html`；改 theme 后删 `.vitepress/cache` 再 build。
- 表格：`.escah-tbl` 恒 `width:max-content!important; min-width:100%`；单元格只许 `overflow-wrap:break-word`，**禁 anywhere/break-all**；宽表用 `.table-scroll` 横滚。
- `config.ts` 的 search.miniSearch 被序列化 eval 重建 → 闭包变量全丢，**必须自包含**；preview rebuild 后须重启。
- 浮窗与详情页翻译须同源（`char_fill_all` 已挂 sync-site）；`charRefs.json` 由 sync-site 自动重生成（旧手动易漏 → 中文页浮窗失效）。
- `SearchLoading.vue`：`onClose` 里 `mo.disconnect()` 在空查询时断 MO → 进度卡 99%。改为 onClose 只复位视觉，mo 仅 onUnmounted 断，并加 20s 硬超时。
- `render_locale` 块级回退含 img/table 时须 `continue` 保留结构。
- **正文 `#id` 锚点跳转**：`sitegen._strip_nav_links` 原把 PukiWiki `anchor_super`（`<a id="drop_list">†</a>`）整个 drop，而它正是 `#id` 链接的跳转目标 → `getElementById` 返回 null。修复=丢弃时若带 `id` 则保留占位 `<span id="...">`。改后须重跑 `i18n build` 重生成 `*.template.html`（417 文件）。
- **角色浮窗对内联头像不触发**：`tagAvatars` 原只靠 `avatarMap[src hash]`，而 `avatarHashes` 仅由角色 JSON `icon`（一览缩略图 hash）构建，wiki 正文内联头像是**另一个 hash**。修复=`avatarMap` 未命中时用 `alt`/`title`（形如 `花のチルカ_icon.png`）去 `_icon`+扩展名后经 `nameAliases` 回 key。影响面 838 img / 745 页，已一次性修（bc5b2ac）。⚠️ 内联头像 URL 的 bytehex 被截断，**不能靠 URL 反解补 avatarHashes**，只能靠 alt。
- **浮窗盖住鼠标（2026-08-01 根治）**：曾反复改不好，真因有二——① `placeHover` 只算水平方向，垂直是 `top=min(a.top,my)-4` 而浮窗 `max-height:94vh`，鼠标几乎必然落在纵向区间内，「不盖鼠标」只是分支顺序的副产物而非被校验的约束；② `mouseover` 只在进入元素时触发一次，大锚点（宽单元格/大图）内移动时 `mx/my` 过期。修复=`placeHover` 改「先选边→再**显式校验** `(mx,my)` 是否落在浮窗矩形内，命中则垂直推到鼠标上/下方，上下都不够才水平让开」；`MirrorContent` 加 document `mousemove` → `store.updateHoverPointer()` 换新 anchor 对象（已有 `watch(store.anchor)` 自动重跑定位）。**教训：几何约束应先写校验、再写启发式。**
- **表格增强选择器铁律（2026-08-02）**：`tableEnhancer.ts` 的 `enhanceTables` 必须选 `table.style_table`（PukiWiki 原始 HTML 自带的表格 class，全站一致），**绝不能写 `table.escah-tbl`**——真实表格从不会被加 `escah-tbl`，写成后者会导致全屏/重置/筛选/吸顶/列宽全部失效（本地"按钮消失"就是这原因）。`enhanceTable` 依赖 `table.parentElement` 是 `.table-scroll`（真实结构 `<div class="ie5"><div class="table-scroll"><table>` 满足）。表头吸顶靠 CSS `.table-scroll thead th { position:sticky }`，无需 JS。
- **本地/线上不一致根因（2026-08-02）**：theme 改动（tableEnhancer/custom.css/MirrorContent）若未 commit+push，线上（跑 main HEAD）永远看不到，本地（工作区）却能看到 → 必然脱节。改完前端必须提醒用户 commit+push。dev 端口冲突时 Vite 自动 +1（5173→5174），浏览器要访问实际监听端口，僵尸 node 进程不监听却占 PID 会误导排查。
- **PukiWiki region 折叠块「整块消失」bug（2026-08-03 修复）**：`MirrorContent.vue` 的 `toggleRgn` 原只切 `.rgn-content` 的 display、**从不切 `.rgn-description`**。但原站 region 分「默认折叠/默认展开」两种，默认展开块的初始 inline 是 `rgn-content=block / rgn-description=none`（写反的脏状态）。旧逻辑下：加载时 desc 隐藏、content 显示（用户看到"展开的内容"）→ 点击 toggle 加 expanded、content 维持 block、desc 永久不显示 → 再点 content=none 且 desc 仍 none → **整块空白消失**。修复：① 新增 `_syncRgn(container)` 按 `expanded` 类统一同步 desc/content/plus/minus 显隐；② `toggleRgn` 改调 `_syncRgn`；③ `processEl` 挂载时对所有 `.rgn-container` 调 `_syncRgn` 规整脏初始（无 expanded 类 → 强制折叠态，符合「默认折叠」规范）。全站扫描 6600 个 rgn-container，22 个页面各 1 个脏块（raid/events/annihilation/super-equipment 的 ja+zh），均随 _syncRgn 修复。验证用 jsdom 模拟点击（无 playwright 时）。

## llm_reco 大模型推荐角色（独立子项目）
- 目录 `llm_reco/`（reco-method / draft / reasoning-log / reco-team + `_signal_extract.py`/`_detail.py`/`_classify.py`/`_team_build.py`/`_char_score.py`）；已发布 `site/{zh,ja}/llm-recommend.md`。
- ⚠️ **用户硬要求：推荐推理不得参考官方攻略/推荐名单**，须基于 `llm_reco/char_data.json`（370 角色）与机制事实由大模型自推，思维过程入文件夹。耗时多久都行。
- **机制结论**（稳定）：数值无区分度、**固有效果才是区分度**；讨伐战体力 -2%/s（百分比，双防无效）→ 单队约 50s 退场 → **多队接力**；**降防 debuff >> 攻击 buff**（对 75% 减伤 BOSS 收益 3 倍；50% 上限只限「降低闪避」，正常降防可列到 100%）；不撤退在 raid 被稀释（raid 居座真解是「体力停止衰减」= 超昂奈理卡），在主线/EX 才是神；BREAK（确定点灯）> 时停。
- **稀缺度盘点**（12 职能标签）：复活 1（唯 O 闪忍奈理卡）/ 不撤退 8 / 解控 19 / 降防 46 / 增伤 54 / 减伤 60 / 免疫 62 / 治疗 99 / 充能 102 / 攻 buff 110 / 硬控 112 / 速度 126。**洞察：速度、充能虽被用户强调但持有量充足非瓶颈，真卡脖子是复活/不撤退/降防。** 铰链卡：小鬼の斗羽大洋（单卡顶 6 职）。
- **量化模型 v0.8（当前版，2026-07-30）**——RAID 专用真实频率公式，`_char_score.py`，输出 `_score_v08_out.txt`：
  - 觉醒（真实表）：行动速度 -0.1×20 = 最多 **-2 秒扁平**（下限 3s，基础 ≤3s 零收益）；必杀充能 +0.3×20 = 最多 **+6pt 上限 15%**；攻/魔 +20%。连击率 +20 **不采用**（50/70 档已达上限；0 档点了反拖慢）。
  - 装备（用户拍板，仅两件满级主装）：火箭引擎/咆哮猛虎 **行动速度 -50%**（乘法，先觉醒后装备）、冲击腰带 **攻魔 +50%**（与攻 buff 加算）。**副装贴片全删**（多变量）、**仁王纳豆删**（与部分角色技能冲突）；降防只剩角色 kit 自带（无 30% 打底）。
  - 常数：`AWK_SPEED_SEC=2` / `AWK_SPEED_FLOOR=3` / `AWK_CHARGE=6` / `AWK_CHARGE_CAP=15` / `AWK_ATK=0.20` / `EQ_ROCKET_SPEED=0.50` / `EQ_BELT_ATK=0.50` / `R_ref=0.50` / 连击阈值 60%。
  - 公式要点：`interval = max(速度-2, 3) × 0.5 / (1+自身速buff)`；`interval_ult = interval × (1+連撃率)`（连击拖慢节奏）；必杀 casts/s = (充填量%+15)/100/interval_ult；普攻含 combo_mult（decay 0.8/0.6/0.4/0.3，连击不暴击）；强度 = 0.70·DPS_norm + 0.30·UTIL_norm。
  - 结果：maxDPS **6,595**；TOP＝レジェンド・ハルカ 78.9（降防100%）> 幻忍コテツ 75.4 > 黒門天 73.0 > ブライド・スバル 61.3 > 真夏のハルカ 55.3。**删降防打底后 kit 自带降防价值暴涨**（100% vs 60% = 25% 伤害差，直接改写头名）。四队：D 暴力输出 42,281 > C 居座 16,529 > A 顶配 12,541 > B 新手 7,344。
  - 曾修 bug：连击率百分比/小数单位混用（1+30=31 倍减速塌缩）。「觉醒下限 3s 把基础 3~5s 拉平 → 基础速度快不再是护城河」。
  - 复用：新增角色补 `char_data.json` → 重跑 `_char_score.py`。文档 reasoning-log §10/§11、reco-team §5、站点页第九节均 v0.8。
- 待深化：弗栗多/乌塔尔「减速/全体异常清小猫」持有者需据 raid.md 减速表全量核实；速度/充能对 FEVER 分数的边际未量化；UTIL 稀缺度赋权与 0.70/0.30 权重为主观折中；队伍 fit_mult 为经验系数非严格推导。

## 历史沿革（已归档，勿重建）
- LLM 翻译管线（`tools/llm_patch.py` 等）与旧词表替换引擎（`zh_patch.py`/`char_zh.py`）均已弃用 → `recycle_bin/tools/`。
- llm_reco v0.2/v0.3/v0.4/v0.6/v0.7 均被 v0.8 取代，过程见 `2026-07-29.md`/`2026-07-30.md`。

## 前端版本号铁律（2026-08-02 新增；强制触发条件见「用户偏好·最高优先级」）
- 站点右上角版本号：`site/.vitepress/theme/components/SiteAccessSwitch.vue` 的 `const SITE_VERSION`（三位数：①大版本 ②新增功能 ③修改）。当前 `1.2.1`。
- 版本日志数据源：`site/.vitepress/theme/changelog.json`（**源码目录、入库**，更新记录页「镜像站更新记录」区块按此渲染）。⚠️ 切勿放回 `.gen-data/`（那是 sync-site 生成的 `page-times.json`，被 gitignore，放进去会导致 CI 构建报 'Could not resolve' 失败）。
- ⚠️ **升版本号 + 维护 changelog 必须由 AI 助手在「每次 push 前」主动完成**（详见上方最高优先级铁律）：每次改动前端升 `SITE_VERSION` 时，助手自己同步在 `theme/changelog.json` 顶部加该版本 `date`/`changes`，并保持一致。改完前端 commit 后等用户确认再 push（见上方推送纪律）。

## 侧边栏生成（sitegen.py SIDEBAR_TREE）
- 侧边栏由 `pipeline/escah_pipeline/sitegen.py` 的 `SIDEBAR_TREE`（按分类 cat 分组）+ `_sb_node()`（递归展开节点为 VitePress sidebar item）+ `_write_sidebars()`（顶层组循环，读 `collapsed` 字段）生成到 `site/.vitepress/generated/sidebar.{ja,zh}.json`，再被 `config.ts` import 喂给 VitePress。**`site/*.md`/sidebar JSON 由 sync-site 重生成，勿手改。**
- 分隔符节点 `_SB_DIV = "__SB_DIV__"`：`_sb_node` 返回 `{"text":"—","link":f"/{locale}/characters.html#__SB_DIV__"}`，custom.css 用 `.VPSidebarItem a[href$="__SB_DIV__"]` 隐藏文字 + `border-top:1px solid` 画实线。
  - **致命根因（铁律）**：VitePress **客户端渲染时会直接丢弃「纯 hash 链接」`link:"#__SB_DIV__"` 的 sidebar item**（DOM 里 0 个 `<a>`，CSS 永远失效）。必须用「真实存在页面 + 锚点」`/zh/characters.html#__SB_DIV__`。空文本 `""` 也会被跳过，故 text 用可见的 `"—"`（再被 CSS 隐藏）。
- **`combined` 合并节点（可复用机制，2026-08-03 新增）**：把多个列表页合并成「一个文本节点内含多个链接」，例如 `SSR | SR | R`。节点写法 `{"slug":"rarity-links","combined":["list-ssr","list-sr","list-r"],"sep":" | "}`（置于某父节点的 `items` 内，如 `characters` 的 items）。`_sb_combined_node()` 生成 `{"text":'<a href="/{locale}/{s}.html">{label}</a>' 用 sep 连接, "collapsible":False}`。
  - **⚠️ 铁律：`combined` 必须两条路径都支持**：`_sb_node()` 递归（处理容器内子项，如 `characters.items`）**和** `_write_sidebars()` 顶层循环（处理组直接子项）都要识别 `combined` 并调 `_sb_combined_node()`。曾只在顶层循环处理 → 容器内子项的 combined 被 `_sb_node` 因无 `slug` 静默丢弃 → `items:[]`（SSR/SR/R 消失）。**改 SIDEBAR_TREE 加 combined 后，必须确认它处于哪一层、两条路径都覆盖。**
  - VitePress 1.6 的 `VPSidebarItem` 对 `text` 字段用 `v-html`（支持 HTML 标签），故 `<a>` 会被真实渲染成链接；但这是裸 `<a href>`，点击是**整页跳转**（非 SPA 客户端导航），功能正确、体验轻微。
- **顶层组 `collapsed` 默认折叠（2026-08-03 新增）**：`SIDEBAR_TREE` 顶层组可加 `"collapsed": True` → `_write_sidebars()` 读 `grp.get("collapsed", False)` 写进生成的 sidebar item。当前约定：`character` 组不折叠（保持展开）；`guide/system/equipment/quest/misc` 五个板块默认折叠，由用户点击展开。

## 预览验证纪律（铁律，2026-08-03 用户重点强调）
- **改完前端/sidebar 这类有 UI 副作用的内容，助手必须自己重启 preview 并验证实际渲染，绝不把验证成本推给用户**。绝不允许对用户说"你硬刷新看看/你浏览器有缓存"——这是助手没自己验证好的借口。
- 根因背景：每次 `node build.mjs build` 后 chunk 文件名 hash 会变。若旧 preview 进程（端口 4173）还在 serve 上一次 build 的旧 HTML，旧 HTML 引用的旧 `app/theme.*.js` 会 404 → 整页前端 JS 没初始化 → 侧边栏点不开、右侧 DocOutline 不渲染。所以 **build 后必须杀掉旧 preview 进程、干净重启再验证**。
- **重启 preview 干净做法**：`Get-CimInstance Win32_Process -Filter "name='node.exe'" | Stop-Process -Force`（或精准杀 4173 占用 PID），再 `Start-Process node -ArgumentList "build.mjs","preview"`。`vite preview` 不能验证搜索；搜索只能对部署站实测。
- **自检 DOM 方法（无需让用户刷新）**：系统 Edge 无头 dump 渲染后 DOM 验证：`& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless --disable-gpu --no-sandbox --virtual-time-budget=8000 --dump-dom "http://localhost:4173/escah/zh/characters.html" | Out-File -Encoding utf8 _dom_dump.html`，再 `[regex]::Matches($dom,'<a[^>]*SB_DIV[^>]*>')` 看数量等。**永远用 dump-dom 实际验证渲染结果，不要只 grep 内联 JSON 字符串——JSON 含数据不代表 DOM 渲染出来。**

## 正文超链接子页面（body-linked subpages，2026-08-03 新增）
- 需求：装备/raid/b-universe/main-quest 的「子页面」（装备条目、raid 7 boss 事件页、b-universe 11 boss 页、main-quest 各 Area 页）**不进导航栏**，仅由别的页面正文超链接点击进入。译名用词汇表即可。
- **注册机制（已落地）**：在 `data/registry/pages.yaml` 新增条目 `category: subpage` + `subgroup: equipment|raid|b-universe|main-quest` + ascii slug（`equip-001`/`raid-001`/`buniv-001`/`mq-001`）。`sitegen._write_sidebars` 已把 `subpage` 与 `character-detail` 一起排除出导航（`slug_index` 构建 + flat 平铺分支两处都排除）。`parse_all`→`i18n build`→`sync-site` 正常处理它们（has_i18n 渲染 md），故子页面有 html 但不在侧边栏。
  - ⚠️ **slug 必须是 ascii**：原站页名含 `/`（如 `メインクエスト/第2部/Area1`）与全角 `（）＆` 等。name→slug 映射见 `tools/subpage_name_slug.json`（由 pages.yaml 重新生成，供后续链接改写使用）。
- **抓取**：`fetch`（无 `--force`）跳过已存在快照，只抓新增。⚠️ 长页名（如 `エスカレイヤー・リバース＆ハルカ・リバース（Bユニバース）`）编码后超 Windows MAX_PATH(260) → `snapshot.page_filename` 已加 sha1 短名回退（>180 字符用 `sha1[:16].html`），**确定性**，parse/i18n/sitegen 都用同一函数故不失配。当前有 2 个 raw 文件是 sha1 短名（功能正常，仅文件名不可读）。
- **⚠️ 已知 bug：`fetcher.fetch_registered_pages` 函数末尾无 `return`，返回 `None`**。调用方若 `fetched,skipped,missing = fetch_registered_pages(...)` 会 `TypeError: cannot unpack NoneType`。自己写后台调用时**勿解包返回值**（直接 try/except 包住、或该函数补 `return (ok,skipped,failed)`）。
- **待译文本归类**：`tools/extract_subpages.py` 把 4 类子页的未译文本按 `subgroup` 写入 `tools/_todo_translate/<equipment|raid|b-universe|main-quest>/new_translation_<date>.txt`（格式与 `i18n extract_todo` 一致：指令 + `# MAP A=<slug>` + `===A===` + `[N] 日文`）。每文件夹附空白 `_translated.txt` 占位。**回填：翻译后逐文件夹 `python -m escah_pipeline.cli i18n fill <category>/new_translation_<date>.txt`**（fill_todo 按 `# MAP` 标签 + `[N]` 顺序对齐，写回 i18n JSON）。
- **⚠️ 链接改写是后续任务（用户明确 deferred）**：现在其它页面正文里指向这些子页的 `?原站页名` 链接还是指向原 wiki。镜像站做好后，需按 `tools/subpage_name_slug.json` 把原站链接改写成 `/zh/<slug>.html`（注意 ja 站为 `/ja/<slug>.html`）。当前未做。
- 数量：equipment 112 / raid 7 / b-universe 11 / main-quest 116（实际 wiki 主线有 第一部46+第2部+第3部 >116，全部抓取）。
