# 超昂大戦エスカレーションヒロインズ 攻略 Wiki — 中日双语镜像站

将日文游戏攻略 WIKI（[escalationheroines.wikiru.jp](https://escalationheroines.wikiru.jp/)，PukiWiki 系统）镜像到本地，
规范化存储原网页资源，并构建可在**中文 / 日文**之间一键切换的静态站点，最终部署到 **GitHub Pages**。

> 本仓库为正式工程化重构版本。原根目录 `index.html` 的**独立角色浮窗 demo 已作废**（浮窗现已成为全页面功能，无需单独 demo 页）；根目录 `img/` 下的图片已迁移进
> `data/assets/img/` 并按内容哈希去重复用；原始 HTML 不再手工维护，全部由流水线生成。

---

## 架构概览

数据流水线（Python）与静态站点（VitePress）以**文件为契约**分层协作，任一层可单独重跑：

```
源站 wikiru.jp
   │  礼貌抓取（限速 / 抖动 / 退避重试 / 断点续抓）
   ▼
data/raw/           原始 HTML 快照 + data/manifest.json（URL / 时间 / sha256 / Last-Modified / 状态）
   │  PukiWiki 解析（一次遍历，日文逐字忠实）
   ▼
data/parsed/i18n/<slug>.template.html   模板：HTML 结构原样保留，文本节点替换为 {{keyN}} 占位
data/parsed/i18n/<slug>.json            每页双语字典 { "keyN": {"ja":"原文","zh":"译文"} }（key=单纯序列递增）
data/parsed/characters/                 语言中立角色结构化 JSON（悬浮详情窗数据源）
   │  用户手工翻译（tools/_translated_texts/<slug>.txt，[N] 对行）→ 脚本解析回填 zh
   │  站点生成：拆分单语言 JSON（zh/<slug>.json、ja/<slug>.json，含 _url）+ glossary 词汇替换
   ▼
site/               VitePress 双语站点（MPA，ja / zh 两套 locale；渲染 = 模板占位 + 查表填充，零正则）
   │  本地构建（用户自行推送）；Pagefind 爬构建后 HTML 建全局搜索索引
   ▼
GitHub Pages（base 路径 /escah/）
```

**关键设计（key 化 i18n，2026-07-27 定稿，以后固定采用此方式）**

- **key 化 i18n（核心）**：解析器在**同一次遍历**里给每个有意义的文本节点按文档顺序分配
  `key1, key2, …`（单纯序列递增，非路径、非哈希），同时产出「模板 HTML（文本变 `{{keyN}}`
  占位，标签 / 链接 / 图片 / 表格结构原样保留）」与「pageX.json（keyN → {ja, zh}）」。
  渲染时按当前语言查表替换占位符——**零正则、零错位**（key 与文本节点在 parse 时即绑定）。
  日文原文变动 → key 顺延变化 → 该处本就需要重译，配合 ja→zh 翻译记忆自动回填未变动部分。
- **文本与页面解耦**：正文存每页双语 JSON，角色属性存语言中立 JSON；
  HTML 只是构建产物，切换语言即切换文本源。
- **日文忠实原则**：解析器对日文正文逐字保留，只做结构提取（标题层级、表格转 Markdown），绝不改写。
- **原始 HTML 注入方式**：PukiWiki 原始 HTML 在 parse 阶段一次性经 `_sanitize_html` 规范化
  （lxml 整树平衡标签、折叠多行属性、剔除 `on*` 事件处理器）并抽出模板；构建时 `MirrorContent`
  组件做「模板占位替换（plain 查表）+ `v-html`」渲染。这样既不触发 Vue 模板编译报错，
  又能把镜像正文写入预渲染静态 HTML（利于 SEO）。
- **礼貌抓取**：默认请求间隔 2~4 秒加随机抖动；遇 429/5xx 按 10/20/40 秒指数退避，最多 3 轮后跳过并记录；
  中断后可断点续抓，已抓且哈希未变的页面绝不重复下载。

---

## 目录结构

```
escah/
├── pipeline/                    # Python 数据流水线包
│   ├── pyproject.toml
│   └── escah_pipeline/          # cli / config / fetcher / registry / snapshot /
│                               # parser_puki / assets / translator / tm / chara / updater / sitegen
├── data/
│   ├── registry/pages.yaml      # 页面注册表：页面名、slug、分类、static 或 watch、排除项
│   ├── raw/                     # 原始 HTML 快照
│   ├── manifest.json            # 每页 URL / 抓取时间 / sha256 / Last-Modified / 状态
│   ├── parsed/i18n/             # 每页「模板 HTML + 双语 JSON」（key 化 i18n 核心产物）
│   ├── parsed/characters/       # 语言中立角色结构化 JSON
│   └── assets/img/              # 本地化图片（哈希命名去重）
├── site/                        # VitePress 站点（base=/escah/）
│   ├── .vitepress/{config.ts, theme/}
│   ├── {ja,zh}/                 # 流水线生成的双语内容（不手工编辑）
│   ├── public/                  # img 同步来源；含 .nojekyll
│   └── package.json
├── tools/
│   └── _translated_texts/       # 用户手工译文（一页一 txt，唯一翻译输入源，入库）
└── README.md
```

---

## 环境依赖

- **Python** ≥ 3.11（流水线）
- **Node.js** ≥ 18（站点构建）
- **翻译不需要 LLM / API Key**。译文**以用户手工翻译为唯一来源**：用户把译文按 `[N]` 对行填入
  `tools/_translated_texts/<slug>.txt`（一页一文件），脚本解析后回填该页 `pageX.json` 的 `zh` 字段。
  ⚠️ 旧「正则词表替换引擎」（`tools/zh_patch.py` / `tools/char_zh.py` / 全局 `_manual_zh.json`）已于
  2026-07-27 决策废弃，由 key 化 i18n 流程取代（原因：正则替换慢、不可跟踪、且曾出现整页错位 bug）。
  详见下方「翻译工作流（key 化 i18n）」。

---

## 快速开始

> 代码块为 bash 语法。**Windows 自带 PowerShell 5.1 不支持 `&&` 串联命令**，请逐行粘贴执行，或在 PowerShell 中用 `;` 替代 `&&`（PowerShell 7+ 才支持 `&&`）。

### 1. 安装依赖

```bash
# Python 流水线
pip install -e ./pipeline

# Node 站点
cd site
npm install
```

### 2. 数据流水线（按序执行）

```bash
# ① 两阶段发现：MenuBar → 观察页；キャラクター一覧 → 角色详情页，写入注册表
python -m escah_pipeline.cli discover

# ② 抓取（断点续抓，礼貌限速）
python -m escah_pipeline.cli fetch

# ③ 解析快照 → 每页「模板 HTML + 双语 JSON」/ 角色 JSON
python -m escah_pipeline.cli parse

# ④ 下载页面引用的图片（哈希命名去重）
python -m escah_pipeline.cli assets

# ⑤ 翻译：用户把译文填入 tools/_translated_texts/，脚本回填每页 JSON 的 zh 字段
#   （见下方「翻译工作流（key 化 i18n）」）

# ⑥ 生成 VitePress 站点内容（拆分单语言 JSON + glossary 替换 + md/侧栏）
python -m escah_pipeline.cli sync-site
```

各子命令均支持 `--help` 查看参数。如需仅重抓不翻译可用 `update --no-translate`。

### 3. 构建站点

```bash
cd site
npm run build        # 输出到 site/.vitepress/dist（等价：node build.mjs build）
# 本地预览：npm run dev  或  npm run preview（等价：node build.mjs dev / node build.mjs preview）
# 注：build.mjs 为中性名构建脚本，内部用 VitePress 编程式 API，便于在持续集成 / 进程管理器下稳定构建。
```

> 注意：GitHub Pages 部署需要 `base: /escah/`（已在 `.vitepress/config.ts` 配置），
> 站点产物根目录为 `site/.vitepress/dist`。`site/public/.nojekyll` 已自动随构建复制到 `dist`，
> 防止 GitHub Pages 的 Jekyll 处理破坏产物。

### 4. 部署到 GitHub Pages

本仓库**不提供 CI 工作流**，由你自行提交并发布：

1. 在本地完成上述 `sync-site` 与 `npm run build`。
2. 将 `site/.vitepress/dist` 的内容推送到仓库的 `gh-pages` 分支（或使用 GitHub Pages 的
   “Deploy from a branch” 指向该分支的根目录）。
3. 仓库设置 → Pages → Branch 选择 `gh-pages` / root，保存后访问 `https://<user>.github.io/escah/`。

---

## 翻译工作流（key 化 i18n，2026-07-27 起唯一方式）

中文翻译**不走 LLM、不走正则替换**。核心契约是**每页一份双语 JSON**（`pageX.json`）+
**每页一份模板 HTML**（文本节点为 `{{keyN}}` 占位），二者由 parser 同一次遍历产出，天然一一对应。

```
1. parse    ：一次遍历 → <slug>.template.html（结构保留、文本变 {{keyN}}）
                        + <slug>.json（{ keyN: {ja:"原文", zh:""} }，key 序列递增）
2. extract  ：把 zh 为空的条目汇总成**一份集中待译清单**
              tools/_todo_translate/new_translation_<YYYYMMDD>.txt（new_translation_ 表意「新增翻译」+ 紧凑 8 位日期，无中文、无连字符）；
              文件开头为翻译指令（用户给定提示词原样，无中文使用说明）；
              页面用不可翻译的字母标记「===A===」「===B===」… 分隔（纯 ASCII，不进翻译），
              页面↔标记映射记在 ASCII 行「# MAP A=<slug> …」；条目为老格式「[N] 日文」，N 本页从 1 递增。
              同时在同一目录生成空白的 new_translation_<YYYYMMDD>_translated.txt 供翻译模型产出译文。
3. 用户翻译 ：把清单（连同 ===X=== 分段与 [N] 日文）交给翻译模型，模型把「[N] 中文」写到
              new_translation_<YYYYMMDD>_translated.txt（沿用同样的 ===X=== 分段）；旧 _translated_texts/<slug>.txt 的 [N] 为迁移遗留勿动
4. 回填     ：i18n fill → 从 new_translation_<YYYYMMDD>_translated.txt 取「[N] 中文」按页写入各页 <slug>.json 的 zh
              （页面映射取自待译清单的 # MAP 行，[N] 序号与 extract 同源对齐；纯数字 [N] 旧版走 migrate 整页配对，无全局塌缩）；
              取成功后该 new_translation_<YYYYMMDD>_translated.txt 自动移入 tools/_translated_texts/，
              待翻译文件 new_translation_<YYYYMMDD>.txt 同时移入 tools/_texts_for_translation/（保留原文+映射作审计留痕）。
5. sync-site：拆分单语言 JSON（zh/<slug>.json、ja/<slug>.json，带 _url 路由）
              + 应用 glossary 词汇替换（词汇表统一译法在这一步作用于单语言 JSON）；
                根 `glossary/` 含三张表——`terms.yaml`（UI/页标题/浮窗分段）、`names.yaml`
                （角色/NPC/道具/装备/BOSS 等专有名词，亦供角色中文名）、`skills.yaml`
                （必殺技/固有効果 精翻）——全部以**渲染期最高优先级覆盖**作用于 zh，
                不破坏 LLM 句级翻译，ja 站不受影响。
6. build    ：VitePress 渲染 = 模板 {{keyN}} → langMap[keyN] 查表填充（零正则）
7. 搜索     ：Pagefind 爬构建后的 HTML 建全局索引
```

**关键规则**

- `tools/_todo_translate/new_translation_<YYYYMMDD>.txt` 是**译者手持的待译清单**（按日期一份、
  文件名 `new_translation_`+8 位日期，表意「新增翻译」且无中文/无连字符，目录名 _todo_translate 已含 todo）：
  开头固定翻译指令（用户给定提示词原样，不含中文使用说明）+ 按 `===A===`/`===B===` 字母标记分段
  + 老格式 `[N] 日文`，一份文件覆盖全部待译，不用在 400+ 文件里翻找。**已译（JSON 有 zh）的条目不出现；已列入的页面不重复追加。**
- 译文落盘在**同目录同名 + `_translated`** 的空文件 `new_translation_<YYYYMMDD>_translated.txt`（extract 自动创建空白）：翻译模型把 `[N] 中文`
  写进去（沿用同样 `===X===` 分段），`i18n fill` 从中取译文；**取成功后该文件自动移入 `tools/_translated_texts/`**（已消费，移出待译目录），
  待翻译清单 `new_translation_<YYYYMMDD>.txt` 同时移入 `tools/_texts_for_translation/`（保留原文+映射作审计留痕）。
- 旧版 `tools/_translated_texts/<slug>.txt`（一页一文件、`[N]` 为迁移遗留）仍由 `i18n migrate` 一次性回填；
  超大页被拆成 `<slug>-N.txt`（如 `faq-1/2/3.txt`、`raid-1/2/3.txt`、`bedroom-scenes-1..8.txt`），
  `migrate` 会自动按 `^<slug>-(\d+)\.txt$` 合并拼接（[N] 跨文件连续、0 起，与 chunks 索引对齐），
  400+ 存量译文文件全程复用，已译页面零重译；新翻译统一走上面的待译清单 + `_translated` 文件，不再往 `_translated_texts` 写 `<slug>.txt`。
  ⚠️ `external-projects.txt` / `prereg-bonus.txt` 是 orphan：对应页面已移 `recycle_bin/`（不再镜像），无 slug 可落，无法使用。
- **无重名歧义**：`extract`（生成集中清单 + 空白 _translated）与 `fill`（取 _translated 回填）成对，
  译者把译文放进 `new_translation_<YYYYMMDD>_translated.txt` 后跑 `i18n fill` 即可，无需另存/复制。
- **ja→zh 翻译记忆按页复用**：源站页面更新重新 parse 后，对每个新 key 的 JA 文本先查该页
  已有译文自动回填，只有真正新增 / 改动的文本才留空待译。**禁止使用旧全局 `_manual_zh.json`
  做迁移源**（存在跨页译法塌缩与错位脏数据）。
- 同一日文在不同页可有不同译法（名前=姓名/名称/角色名 等），按页隔离，切勿"全局统一"。
- 角色名 / 声优 / 画师名按约定保留日文。

**已废弃（勿再使用/重建）**：`tools/zh_patch.py`、`tools/char_zh.py`（正则词表替换引擎）、
全局 `tools/_manual_zh.json`、`tools/inject_translations.py`（全局兜底表重建）。
废弃原因：巨型正则扫全站慢（~6 分钟）、进度不可跟踪、曾出现「物理→远距离」整页错位 bug。
文件按回收站约定移入 `recycle_bin/`，不永久删除。

## 增量更新（手动）

源站页面会变动。提供**单脚本手动**更新（不做定时任务，由你不定期运行）：

```bash
# 轮询观察列表与“最近更新”，哈希比对后仅重抓、重解析、重翻变更页
python -m escah_pipeline.cli update          # 完整增量（含翻译）
python -m escah_pipeline.cli update --no-translate   # 仅重抓+重解析，不翻译
python -m escah_pipeline.cli update --mock           # 翻译占位模式
```

Windows 用户可直接运行包装脚本 `update.ps1`。更新后重新执行 `sync-site` 与 `npm run build` 并重新部署。

---

## 页面与分类

- **角色一览**：稀有度 / 属性 / 类型筛选 + 关键字搜索；悬停头像或名字弹出**角色详情悬浮窗**（核心交互，zh 站显示「中文名（日文名）」）。
- **角色详情页 / 图鉴（装备·道具·技能）/ 攻略文章 / 更新记录** 等模板化页面。
- **全局搜索**：顶部导航内置搜索框，按 ja / zh 分别建索引，覆盖所有子页面（含评论页）。
- **双语 + 双主题**：日 / 中 一键切换，明亮 / 暗黑双主题。

## 抓取范围与排除

- **观察列表页**（约 40 个，需跟踪更新）：游戏指南、角色、系统、装备道具、任务、其他各分类导航项。
- **角色静态详情页**（约 400 个，抓一次基本不变）：由「キャラクター一覧」SSR/SR/R 分区链接发现。
- **评论页**（`コメント/` 前缀）：作为独立分类一并抓取与翻译。
- **默认不抓取**（可在注册表中显式开启）：掲示板、編集者用页面、寝室シーン一覧（R18）。

---

## 许可与合规

仅做游戏数据镜像与翻译，遵守原站使用条款；R18 分类默认排除。
