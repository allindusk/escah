# MEMORY — ESCH 超昂大战 WIKI 中日双语镜像站

## 项目概况
- 镜像 escalationheroines.wikiru.jp(PukiWiki)→本地构建 ja/zh 双语静态站,部署 GitHub Pages(base `/escah/`)+ Cloudflare Pages(`/`,BASE=/)。
- 架构:Python 流水线 `pipeline/escah_pipeline`(discover/fetch/parse/assets/i18n/chara/sync-site)+ VitePress 站点 `site/`(MPA,ja/zh 双 locale),层间以文件为契约。
- **部署:GitHub Actions `.github/workflows/deploy.yml`,push 到 main 即触发**(parse→sync-site→build→deploy GH Pages;可选 CF)。本地只需 commit+push,勿手动推 dist。
- 数据:`data/raw`(快照,已 git+LFS)+`data/manifest.json`;`data/parsed/{ja,zh,characters}` 与 `site/public`/`site/*.md`/`site/.vitepress/frag` 由流水线从 data/raw+源码重建,**不入库**(`data/parsed/*` 忽略,仅 `!data/parsed/i18n/` 例外);`data/assets/img`(2386 图)LFS 入库。
- ⚠️ **`data/parsed/i18n/` 是人工译文词典(唯一真值),必须入库**——CI 构建 zh 站直接读它(不跑 i18n build/extract/fill)。改译文后须把改动 commit 进 i18n JSON,否则部署不生效。
- 硬件 16 线程;不可并行:fetch/sync_site(顺序)/build.mjs。`vite preview`(sirv)不能验证搜索,搜索只能对部署站实测。

## 翻译工作流(key 化 i18n,2026-07-27 起固化)
- 流程:`i18n build`→`extract`(清单 `new_translation_<date>.txt`+`_translated.txt`)→译→`fill`(按 [N] 序号回填,脆弱)→`char-fill`→`sync-site`→build。中日同形算有效翻译。助手不译成人正文。
- ⚠️ **`fill` 按 `[N]` 位置序号对齐回填(非按 ja 内容)**:extract 与 fill 间未译集合偏移会整体错位(标题/正文串位)。损坏判别:某 key 的 ja 像标题但 zh 是长段落。修复=直改 `data/parsed/i18n/<slug>.json` 错 key/blk(重建保留,因记忆来自该 JSON)。

## 站点词汇表 glossary(render-time 最高优先级覆盖,仅 zh)
- 三份手工词表(不被 build 覆盖):`terms.yaml`(page_titles/char_sections/labels/values/inline_terms)、`names.yaml`(~700 专名,**翻译绝对权威,天然全 precise**)、`skills.yaml`(必杀技/固有效果 JA→ZH,~2900 条)。加词只改 yaml→`sync-site`+`build` 生效,无需重建 i18n JSON。ja 站不受影响。
- **`skills.yaml` 应用点**:`char_fill_all`(写 parsed→public/data/char,供 CharHoverModal 小浮窗)与 `render_locale`(整页)都用 `_name_override` 最高优先级。**⚠️ 2026-07-29 修 `_SKILL_NS`**:源 JA 与线上 JA 常有空白/换行漂移,原 `_norm`(保留空白)漏匹配近半(2700 中 1340 不命中)。已加 `_norm_ns`(去全部空白)二级索引,`_name_override` 查它,覆盖 2700/2700=100%(日语无空格语义,安全)。**之前报的「46% 死」是诊断脚本错用 NFKC 归一化的假警报,勿信。**
- 精炼技能译已批量注入 `data/parsed/i18n/characters/<stem>.json`(按条目 ja 的 `_norm_ns` 匹配,覆盖 345 角色/1216 单元格),成可持久主源。⚠️ `i18n build/extract/fill` 会覆盖该目录,须重跑注入脚本(`tools/_gen_skill_glossary.py` 现指向 `skill_unique_effects_20260729_translated.txt`)。
- **`_correct_text` 覆盖顺序**:`_NAME_RE`(子串)→`_CORR_RE`(`_learn_corrections`,names 全量+high_freq `_precise` 子集,带后缀健壮化 `_split_name_suffix`)→`_high_freq_override`(含假名子串)→`_term_sub_override`(inline_terms 含假名子串)。
- **`_precise` 白名单(2026-07-29)**:`high_freq.yaml` 末 `_precise:` 段(纯片假名借词/专名)+取其中非纯片假名条目做「句中子串纠正」(`_high_freq_precise_sub`,仅节点级 zh,**不对整段 html**——否则误改 `data-char` 属性致浮窗失效)。用户 25 权威术语(アルカナ/フェス/レガリア/九大神騎/期間限定/神騎/魔女…)全站强制统一。
- **`レガリアの神騎` 系列**:names.yaml 已有整系列,读音由 梅加艾尔/玛雅艾尔→用户选 **米加尔/玛雅尔**(含超昂变体);旧读音残留靠 `_READING_CORR`+render_locale 末尾 zh html 子串收口归零。
- `names.yaml` 男主 戦部トキサダ(战部时贞)称呼变体已加;不翻译名单(FM77 等)`name_zh` 留空。
- ⚠️ 改 names.yaml 读音后须 `extract_all_characters(force=True)` 重生成角色 JSON(sync-site 只复制不重建);调用用脚本文件(`python script.py`,勿 `python -c` 在 PowerShell Start-Process 下分号会被拆)。

## 关键架构
- 原文 HTML→`sitegen._sanitize_html`→`site/.vitepress/frag/<slug>.{ja,zh}.json`;md `import frag`+`MirrorContent.vue` `v-html`(不可 ?raw)。`site/*.md`/sidebar 由 sync-site 重生成勿手改。图片 `withBase('/img/')`。
- 角色 JSON `data/parsed/characters/<safe_id>.json`:name/name_zh/rarity/icon/sections→复制 `site/public/data/char/`。CharHoverModal.displayName: zh 站 `name_zh（日文名）`。

## 已修复阻断 bug(铁律)
- `cleanUrls:false`→内部链接带 `.html`;改 theme 后删 `.vitepress/cache` 再 build。
- 表格:`.escah-tbl` 恒 `width:max-content!important;min-width:100%`;单元格只许 `overflow-wrap:break-word`,**禁 anywhere/break-all**。宽表用 `.table-scroll` 横滚。
- `config.ts` search.miniSearch 被序列化 eval 重建,闭包变量全丢→须自包含;preview rebuild 后须重启。
- 浮窗与详情页翻译须同源(`char_fill_all` 已挂 sync-site);`charRefs.json` 现已 sync-site 自动重生成(旧手动易漏→中文页浮窗失效)。
- **SearchLoading.vue bug(已修)**:`onClose` 里 `mo.disconnect()` 在空查询时断 MO→进度永久卡 99%。改为 onClose 不断 mo(只复位视觉),mo 仅 onUnmounted 断;加 20s 硬超时兜底。
- `render_locale` 块级回退含 img/table 须 `continue` 保留结构。

## 用户偏好(最高优先级)
- 后台运维纪律:①启动前 `Get-Process -Name python` 查重;②后台任务须有进度日志(`_bg.py`+锁+`[DONE]/[FAIL]`);③能判断 bug/卡住。
- 回收站约定:过期/无用文件移 `recycle_bin/`,**绝不 git rm/永久删**。
- LLM 翻译管线已弃用→`recycle_bin/tools/`,勿重建。
- ⚠️ 推送 GitHub 须经用户明确指令(本任务已获指令);本地可自由构建验证。

## llm_reco 大模型推荐角色(独立,2026-07-29 起)
- `llm_reco/`(reco-method/draft/reasoning-log + `_signal_extract.py`/`_detail.py`→`_signals.txt`/`_details.txt`);已发布 `site/{zh,ja}/llm-recommend.md`。
- ⚠️ 用户硬要求:推荐推理**不得**参考官方攻略/推荐名单,须基于 `llm_reco/char_data.json`(370 角色)与机制事实由大模型自推,思维入文件夹。耗时多久都行。
- v0.2 框架:数值非区分度,**固有效果=区分度**;稀缺机制(不撤退8/全异常免疫1/复活1/攻击增益3…)。后续 v0.3:全量数值排序/装备联动/对策组合。
