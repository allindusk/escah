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
   │  PukiWiki 解析（日文逐字忠实，结构转 Markdown）
   ▼
data/parsed/ja/     日文 Markdown 中间层（忠实原文，不纠错不删减）
data/parsed/characters/  语言中立角色结构化 JSON（悬浮详情窗数据源）
data/parsed/zh/     中文 Markdown（词表替换引擎：术语表 + 正则 + 通用规则，确定性可重跑，无需 LLM）
   │  站点生成
   ▼
site/               VitePress 双语站点（MPA，ja / zh 两套 locale）
   │  本地构建（用户自行推送）
   ▼
GitHub Pages（base 路径 /escah/）
```

**关键设计**

- **文本与页面解耦**：界面文案存 i18n 字典（ja/zh），正文存双语 Markdown，角色属性存语言中立 JSON；
  HTML 只是构建产物，切换语言即切换文本源。
- **日文忠实原则**：解析器对日文正文逐字保留，只做结构提取（标题层级、表格转 Markdown），绝不改写。
- **原始 HTML 注入方式**：PukiWiki 原始 HTML 经流水线侧 `_sanitize_html` 规范化（lxml 整树平衡标签、
  折叠多行属性、剔除 `on*` 事件处理器）后，以 **JSON 文件** 形式随页面导入，并由 `MirrorContent`
  组件用 `v-html` 渲染。这样既不触发 Vue 模板编译报错，又能把镜像正文写入预渲染静态 HTML（利于 SEO）。
- **礼貌抓取**：默认请求间隔 2~4 秒加随机抖动；遇 429/5xx 按 10/20/40 秒指数退避，最多 3 轮后跳过并记录；
  中断后可断点续抓，已抓且哈希未变的页面绝不重复下载。

---

## 目录结构

```
escah/
├── pipeline/                    # Python 数据流水线包
│   ├── pyproject.toml
│   └── escah_pipeline/          # cli / config / fetcher / registry / snapshot /
│                               # parser_puki / assets / translator / tm / glossary / chara / updater / sitegen
├── data/
│   ├── registry/pages.yaml      # 页面注册表：页面名、slug、分类、static 或 watch、排除项
│   ├── raw/                     # 原始 HTML 快照
│   ├── manifest.json            # 每页 URL / 抓取时间 / sha256 / Last-Modified / 状态
│   ├── parsed/{ja,zh,characters}/  # 解析 / 翻译结果 + 角色 JSON
│   └── assets/img/              # 本地化图片（哈希命名去重）
├── glossary/glossary.yaml       # 日→中游戏术语表
├── overrides/zh/                # 人工校对覆盖文件（优先级高于机翻）
├── site/                        # VitePress 站点（base=/escah/）
│   ├── .vitepress/{config.ts, theme/, frag/}
│   ├── {ja,zh}/                 # 流水线生成的双语内容（不手工编辑）
│   ├── public/                  # img 同步来源；含 .nojekyll
│   └── package.json
├── tools/                        # 翻译工具链（zh_patch / char_zh / 频率分析 / 分页候选生成）
└── README.md
```

---

## 环境依赖

- **Python** ≥ 3.11（流水线）
- **Node.js** ≥ 18（站点构建）
- **翻译不需要 LLM / API Key**。中文由本地「词表替换引擎」`tools/zh_patch.py` 生成（JA2ZH 精确串 +
  正则规则 + 通用替换），`tools/char_zh.py` 复用其 patch 给角色 JSON 补译。扩展翻译即向词表追加条目，
  然后重跑两步即可全局生效（`python tools/zh_patch.py && python tools/char_zh.py`）。详见下方「翻译工具链」。

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

# ③ 解析快照 → 日文 Markdown / 角色 JSON
python -m escah_pipeline.cli parse

# ④ 下载页面引用的图片（哈希命名去重）
python -m escah_pipeline.cli assets

# ⑤ 翻译日文 → 中文（本地词表替换引擎，无需 LLM；见下方「翻译工具链」）
python -m escah_pipeline.cli translate

# ⑥ 生成 VitePress 站点内容（ja/zh）
python -m escah_pipeline.cli sync-site
```

各子命令均支持 `--help` 查看参数。`translate` 子命令现已改为直接调用 `tools/zh_patch.py`（词表引擎），
不再走 LLM；如需仅重抓不翻译可用 `update --no-translate`。

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

## 翻译工具链（词表替换引擎）

中文翻译**不走 LLM**，而是一套可确定性重跑的「词表替换引擎」，全部位于 `tools/`：

- `tools/zh_patch.py` — 核心引擎。对 `data/parsed/ja/*.html` 依次应用 **JA2ZH（精确串替换）+ REGEX_RULES（正则）+ GENERIC（通用替换）**，
  重新生成 `data/parsed/zh/*.html`。幂等：词表增长后重跑即全站同步生效。
- `tools/char_zh.py` — 复用 `zh_patch.patch()`，给 `data/parsed/characters/*.json` 的 `tr` 单元格补写 `zh` 字段（角色详情 JSON 译文字段），幂等。
- `tools/_freq_chars.py` — 全局扫描 369 个角色页日文源，按「频次×长度」排序输出未译净文本（`tools/_seg_chars.txt`），用于挑高性价比词条。
- `tools/_page_seg.py <页名>` — 生成单页句级待译候选，用于大页分块补译。

**扩展翻译的标准流程**（也是 `translate` 子命令与 `update` 内部所调用的唯一路径）：

```bash
# 1) 生成待译候选（页面或角色散文）
python tools/_page_seg.py <页名>        # 或 python tools/_freq_chars.py
# 2) 向 tools/zh_patch.py 的 JA2ZH / GENERIC / REGEX_RULES 追加译条
#    （精确 key 须匹配文件原文，含标签切分；公式类宜整句精确键或正则）
# 3) 重跑引擎，全站同步
python tools/zh_patch.py && python tools/char_zh.py
# 4) 重新生成站点并构建
python -m escah_pipeline.cli sync-site
cd site && node build.mjs build
```

> 角色名 / 声优 / 画师名按约定保留日文。已完成的续译批次与后续待译清单见
> `.codebuddy/memory/TRANSLATION_TODO.md`（当前全站可译内容覆盖率持续提升中，残留集中在角色页独有散文与 raid/faq 等集中大页）。

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

- **角色一览**：稀有度 / 属性 / 类型筛选 + 关键字搜索；悬停头像或名字弹出**角色详情悬浮窗**（核心交互）。
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
