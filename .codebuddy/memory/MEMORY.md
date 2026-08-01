# MEMORY — ESCH 超昂大战 WIKI 中日双语镜像站

> 长期记忆（就地更新，保持精简）。逐日过程细节见 `YYYY-MM-DD.md`，此处只留跨会话仍有效的结论。
> 末次整理：2026-08-01（合并去重）。

## 用户偏好（最高优先级）
- ⚠️⚠️ **推送 GitHub（git push）须经用户当次明确指令，且只覆盖该次；绝不因"之前那次说过 push"就自行连续推送**。用户的"commit+push"只授权当次那一个动作，后续修复/重构若还要 push，必须再次征求确认。本地可自由 commit / build 验证，但 push 一律等指令。
- **回收站约定**：过期/无用文件移 `recycle_bin/`，**绝不 git rm/永久删**。
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

## 关键架构
- 原文 HTML → `sitegen._sanitize_html` → `site/.vitepress/frag/<slug>.{ja,zh}.json`；md 里 `import frag` + `MirrorContent.vue` `v-html`（**不可 ?raw**）。`site/*.md`/sidebar 由 sync-site 重生成，勿手改。图片走 `withBase('/img/')`。
- 角色 JSON `data/parsed/characters/<safe_id>.json`（name/name_zh/rarity/icon/sections）→ 复制到 `site/public/data/char/`。`CharHoverModal.displayName`：zh 站为 `name_zh（日文名）`。
- sitegen 特设页「日中用語対照表」slug 必须为 `term-map`，**不可用 glossary**（会覆盖 WIKI 用語集镜像页）。
- z-index 自顶向下：lightbox 300 > char-modal 271 / mask 270 > char-hover 260 > 表格全屏 `.escah-tbl-fs` 250 > VPNav 100。

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

## 前端版本号铁律（2026-08-02 新增）
- 站点右上角版本号：`site/.vitepress/theme/components/SiteAccessSwitch.vue` 的 `const SITE_VERSION`（三位数：①大版本 ②新增功能 ③修改）。当前 `1.2.0`。
- 版本日志数据源：`site/.vitepress/theme/changelog.json`（**源码目录、入库**，更新记录页「镜像站更新记录」区块按此渲染）。⚠️ 切勿放回 `.gen-data/`（那是 sync-site 生成的 `page-times.json`，被 gitignore，放进去会导致 CI 构建报 'Could not resolve' 失败）。
- ⚠️ **升版本号 + 维护 changelog 是 AI 助手的职责，不是用户**：每次改动前端升 `SITE_VERSION` 时，助手自己同步在 `theme/changelog.json` 顶部加该版本 `date`/`changes`，并保持一致。改完前端 commit 后等用户确认再 push（见上方推送纪律）。
