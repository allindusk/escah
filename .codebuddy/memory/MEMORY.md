# MEMORY — ESCH 超昂大战 WIKI 中日双语镜像站

## 项目概况
- 镜像 escalationheroines.wikiru.jp(PukiWiki)→本地构建 ja/zh 双语静态站,部署 GitHub Pages(base `/escah/`)。
- 架构:Python 流水线 `pipeline/escah_pipeline`(discover/fetch/parse/assets/i18n/chara/sync-site)+ VitePress 站点 `site/`(MPA,ja/zh 双 locale),层间以文件为契约。
- 数据:`data/raw`(快照,已 git)+`data/manifest.json`+`data/parsed/{ja,zh,characters,i18n}`(可重跑,不入库)+`data/assets/img`(2386 图,LFS)+`data/registry/{pages.yaml(~418页),mirror_plan.yaml}`。
- 部署:无 CI。本地 `python -m escah_pipeline.cli update`→`cd site && node build.mjs build`→手动 push dist 到 gh-pages。双部署 GH Pages(`/escah/`)+ Cloudflare Pages(`/`,CF 控制台设 `BASE=/`+`VITE_GHPAGES_URL`/`VITE_CF_URL`)。
- 硬件 16 线程;并行上限 round(cpu*0.8)。不可并行:fetch/sync_site(顺序)/build.mjs(detached)。
- ⚠️ 本地 `vite preview`(sirv)不能验证搜索(@localSearchIndex 分块 ~20MB 有坑);搜索只能对部署站实测。搜索索引懒加载,勿随意瘦身/改 load 机制(只加进度提示 `SearchLoading.vue`)。

## 翻译工作流(key 化 i18n,2026-07-27 起固化,用户"暂不再改")
- 流程:`i18n build`(模板 {{keyN}}+双语 JSON)→`extract`(集中清单 `new_translation_<date>.txt`+空白 `_translated.txt`)→译→`fill`(按 #MAP+[N] 回填 zh)→`char-fill`→`sync-site`(渲染 frag)→build。一键 `cli translate`。两级粒度:节点 keyN 保结构;整句块 blkN 回退纯文本。中日同形算有效翻译。
- 助手不译正文(成人内容红线)。ja→zh 记忆按页复用;旧每页 `_texts_for_translation` 仅归档,勿当清单。

## 站点词汇表 glossary(render-time 最高优先级覆盖,仅 zh 站)
- 三份入库词表(手工维护,不被 build 覆盖):`terms.yaml`(page_titles/char_sections/char_labels/char_values/inline_terms)、`names.yaml`(~700 名)、`skills.yaml`(~2776 技能)。加词只改 yaml→`sync-site`+`build` 全站生效,无需重建 i18n JSON。ja 站不受影响。
- **`_correct_text` 覆盖顺序**:①`_NAME_RE` 子串(长词优先,漏译 JA→ZH)②`_CORR_RE` 错译纠正(`_learn_corrections()`)③`_high_freq_override`(含假名→子串)④`_term_sub_override`(inline_terms 含假名→子串,如 長官さぁん→长官～)。
- ⚠️ **`_learn_corrections()` 局限**:仅当节点 `ja`(归一化)**恰好等于**某 glossary 键才学「错译 zh→正确 zh」;长节点(ja 含该名但≠键,如 bedroom-scenes 的「相手：トキサダ…」)漏学 → 此类错译(トキサダ 误读 時定→时定)只能**直接改 i18n 节点 zh**。
- **inline_terms 双层(2026-07-28)**:纯汉字/符号→`_term_override` 整词精确;含假名→`_term_sub_override` 子串(称呼内嵌句中)。已加 `長官さぁん/長官さ～ん→长官～`、`長官さん→长官`。
- `names.yaml` 已加 男主 戦部トキサダ(战部时贞)称呼变体:トキサダ/トキサダさん/くん/っ/さぁん/さ～ん、戦部さん/さぁん/さ～ん(长词优先子串)。
- 不翻译名单(非日语/代号,如 `FM77`/`女郎蜘蛛初音`/`女郎蜘蛛奏子`):勿写 glossary、`name_zh` 留空;新增追加 `tools/_check_glossary_coverage.py` 的 `_DO_NOT_TRANSLATE`。`k==v` 视为未真正翻译。
- high_freq 双层:`_high_freq_override`(含假名→子串)+`_high_freq_exact`(纯汉字→整词精确,防污染中文)。`translate_glossary.py` 操作 `_todo_translate`(template/merge/build/archive)。

## 关键架构
- 原文 HTML→`sitegen._sanitize_html`→`site/.vitepress/frag/<slug>.{ja,zh}.json`;md `import frag`+`MirrorContent.vue` `v-html`。**不可 `?raw`**;frag 按 locale 分文件。
- `site/*.md`/sidebar 由 `sync-site` 重生成**勿手改**。图片 `withBase('/img/')`,路径须带前导 `/`。
- 角色 JSON `data/parsed/characters/<safe_id>.json`:`name`(日文)/`name_zh`/`rarity`/`icon`/`sections`;复制到 `site/public/data/char/`。`CharHoverModal.displayName`:zh 站 `name_zh（日文名）`。

## 已修复阻断 bug(铁律/易犯)
- `cleanUrls:false`→内部链接务必带 `.html`。VitePress 改 theme 后删 `.vitepress/cache` 再 build。
- ⚠️ 表格铁律:`.escah-tbl` 恒 `width:max-content!important;min-width:100%`;单元格只许 `overflow-wrap:break-word`,**禁止 `anywhere`/`break-all`**(否则数字/中文一字一行)。宽表由 `.table-scroll` 横滚。
- ⚠️ `config.ts` search.miniSearch 函数被序列化 eval 重建,**闭包变量全丢**→须自包含。preview(sirv) rebuild 后须重启。
- ⚠️ 浮窗与详情页翻译须同源:`char_fill_all()`(i18n 词典回填浮窗 zh)已挂 `sync-site`;勿用 `extract_all_characters` 单独作浮窗源。`charRefs.json` 改后须 rebuild(每次增删角色重跑 `gen_char_refs.py`)。
- ⚠️ `render_locale` 块级回退含 img/table 时须 `continue` 保留结构(否则图/表被删)。

## 用户偏好(最高优先级)
- ⚠️ 后台运维纪律:①启动前 `Get-Process -Name python` 查重,绝不重复触发长任务;②后台任务须有进度日志(`_bg.py start` 落 `tools/_logs/`+锁+`[DONE]/[FAIL]`);③能判断 bug/卡住。
- ⚠️ 回收站约定:过期/无用文件移入根 `recycle_bin/`,**绝不 `git rm`/永久删**。
- LLM 翻译管线已弃用→`recycle_bin/tools/`,勿重建。
- ⚠️ **推送 GitHub 须经用户明确指令**:改动完成勿自行 commit+push,等用户说"推送"才做。本地可自由构建验证。

## 2026-07-28 工作记录
- **長官/男主 戦部トキサダ 译名统一**:① glossary 加 `長官さん→长官`(terms.yaml inline_terms)+ 男主称呼变体(names.yaml)。② 修复已译错译(词表子串无法回改,直改 i18n zh):`时定→时贞`(bedroom-scenes 等 25 文件 722 处,トキサダ 误读 時定)、`指挥官→长官` 仅限 ja 含 長官 的节点(避免误改 司令 来源的 指挥官)。验证:时定残留 0、称呼变体正文残留 0、司令节点未被误改。③ 遗留(未做,低可见度):角色链接 `title=`/`alt=` 属性仍显示日文名(悬浮提示/图 alt);main-story `<pre>` 章节标题(トキサダの力 等)未翻译。
