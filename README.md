# ESCAH 超昂大戦 Wiki 中日双语镜像站

镜像 [escalationheroines.wikiru.jp](https://escalationheroines.wikiru.jp/)（PukiWiki 站），
经本地流水线「抓取 → 解析 → 翻译 → 生成」，产出 **ja / zh 双语种静态站**，
部署于 GitHub Pages（base `/escah/`）与 Cloudflare Pages（base `/`）。

- 线上入口：GitHub Pages `/escah/`，自动跳转日文首页
- 技术栈：Python 流水线（`pipeline/escah_pipeline`）+ VitePress 1.x（`site/`）
- 仓库：<https://github.com/allindusk/escah>

---

## 1. 环境要求

| 组件 | 版本 | 来源 |
|---|---|---|
| Python | `>=3.11` | `pipeline/pyproject.toml` |
| Node.js | 20 | `.github/workflows/deploy.yml` |
| Git LFS | 必需（图片资产） | `.gitignore` / `deploy.yml` |

## 2. 安装

```bash
# Python 依赖 + 以可编辑模式安装流水线（提供 escah-pipeline 命令）
pip install -r requirements.txt
pip install -e pipeline

# 前端依赖
cd site && npm install
```

安装后任意目录可用 `escah-pipeline <命令>`；未安装则在 `pipeline/` 目录下用
`python -m escah_pipeline.cli <命令>`（见 `update.ps1` 的回退逻辑）。

## 3. 快速开始

| 目的 | 操作 |
|---|---|
| 开发（热更新） | 双击 `start-dev.bat` → <http://localhost:5173/escah/> |
| 预览构建产物 | 双击 `start-site.bat` → <http://localhost:4173/escah/> |
| 停止 | `stop-dev.bat` / `stop-site.bat` |
| 手动增量更新原站 | `.\update.ps1`（加 `-NoTranslate` 只抓取不翻译） |

`start-dev.bat` 会先跑一次 `sync-site`，再同时启动 VitePress Dev 服务器（5173）
与内容源监听 `tools/dev-watch.py`（改译文 / 词表 / `data/parsed` 后自动 `sync-site` 并热刷新）。

手动等价命令：

```bash
python -m escah_pipeline.cli sync-site   # 生成站点内容
cd site && node build.mjs build          # 构建到 site/.vitepress/dist
node build.mjs preview                   # 预览 4173
node build.mjs dev                       # 开发 5173
```

> `build.mjs` 是 vitepress 编程式 API 的封装（避免被本机 harness 当成 watch 服务强杀），
> `build` 会额外写入 `.nojekyll`。

**构建产物不留档**（2026-10-19 用户要求）：`build` 开始前会把旧的 `dist` / `.temp`
改名让开（本机 safe-delete 守卫会拦 >500 文件的删除），**构建成功后直接删除**这些快照，
不再像以前那样堆进 `recycle_bin/_build_snapshots/`（那个目录一度攒到 11.7 万文件 / 8.7 GB）。
构建失败时保留现场便于排查。手动清理：`cd site && node build.mjs prune`；
确实想留一份 dist 回滚：`ESCAH_KEEP_DIST_SNAPSHOTS=1 node build.mjs prune`。

## 4. 目录结构

```
.
├── pipeline/escah_pipeline/   # Python 流水线（唯一数据处理入口）
│   ├── cli.py                 # 命令行入口，所有子命令在此注册
│   ├── config.py              # 路径常量 / 抓取参数 / SITE_BASE
│   ├── registry.py / plan.py  # 页面注册表、镜像计划（discover / sync-plan）
│   ├── fetcher.py / snapshot.py   # 礼貌抓取、快照与 manifest
│   ├── parser_puki.py / chara.py  # PukiWiki 解析、角色数据抽取
│   ├── assets.py              # 图片下载（哈希命名去重）
│   ├── i18n.py                # key 化 i18n 引擎（模板 + 双语 JSON）
│   ├── gtrans.py              # 谷歌免费翻译（translate-pa 内部接口）
│   ├── glossary_scan.py       # 词表扫描
│   ├── changelog.py           # 原站「更新履歴」存档（sync-cron 周存档用）
│   ├── imgx.py                # 图片转码（下载即转 WebP）
│   ├── statpages.py           # 「数据统计」页生成（data/statdata → md + frag）
│   └── sitegen.py             # 生成 VitePress 内容（md / frag / public / sidebar / 首页）
├── site/
│   ├── .vitepress/
│   │   ├── config.ts          # 双 locale（root=ja、zh）、nav、sidebar
│   │   ├── seo.ts             # 每页 canonical / hreflang / 结构化数据、sitemap 口径
│   │   ├── frag/              # <slug>.<locale>.json 正文片段（构建期生成）
│   │   ├── generated/         # sidebar.ja.json / sidebar.zh.json（sync-site 生成）
│   │   └── theme/             # Vue 组件、changelog.json、charRefs.json
│   ├── ja/ zh/                # 生成的 .md（勿手改，含首页 index.md —— 见 §12.1）
│   ├── public/                # 数据与图片（构建期生成）
│   └── build.mjs              # build / preview / dev
├── tools/                     # 辅助脚本 + 翻译工作目录
│   ├── dev-watch.py           # 内容源监听（start-dev.bat 拉起）
│   ├── gen_char_refs.py       # charRefs.json（sync-site 自动调用）
│   ├── extract_subpages.py    # 子页待译清单抽取
│   ├── translate_glossary.py  # 高频词表构建
│   └── verify_consistency.py  # 一致性校验
├── glossary/                  # 日→中词表（6 个 yaml）
├── data/
│   ├── raw/                   # 原站 HTML 快照（入库）
│   ├── parsed/
│   │   ├── ja/                # 解析后的日文片段（可重建）
│   │   ├── i18n/              # ★ 译文真值（模板 + 双语 JSON，入库）
│   │   ├── characters/        # 角色数据（可重建）
│   │   └── index.json / comment_zh.json
│   ├── assets/img/            # 图片（Git LFS 跟踪，入库）
│   ├── registry/              # pages.yaml、mirror_plan.yaml（入库）
│   ├── statdata/              # ★ 攻略作者实测数据 JSON（入库；「数据统计」页数据源）
│   └── manifest.json / pending_assets.json
└── .github/workflows/         # deploy.yml、sync-cron.yml
```

## 5. 流水线命令

入口：`escah-pipeline <命令>`（或 `python -m escah_pipeline.cli <命令>`）。完整定义见 `cli.py`。

| 命令 | 作用 | 常用参数 |
|---|---|---|
| `discover` | 两阶段发现页面（MenuBar → 观察页；角色一览 → 角色详情），随后自动 `sync-plan` | — |
| `fetch` | 按注册表抓取页面（断点续抓） | `--force`、`--mode all\|watch\|static`、`--pages` |
| `parse` | 解析快照 → 日文片段 / 角色 JSON | `--pages`、`--force` |
| `assets` | 下载页面引用的图片（哈希命名去重） | `--force` |
| `translate` | 应用翻译（`i18n build → migrate → fill → char-fill`） | `--pages` |
| `update` | 自动更新：处理 planned + 检测变更 → 重抓 / 重解析 / 重翻译 | `--full`、`--no-translate` |
| `sync-plan` | 重建 `mirror_plan.yaml` 的 mirrored（planned 保留） | — |
| `sync-site` | 生成 VitePress 站点内容（ja/zh），末尾自动重生成 `charRefs.json` | — |
| `i18n` | key 化 i18n 全套子命令，见下节 | 见下 |
| `gtrans` | 谷歌免费翻译待译清单 → `*_translated.txt` | `--src`、`--tgt`、`--force` |

抓取为「礼貌抓取」：间隔 2–4 秒、429/5xx 指数退避（10/20/40 秒）、最多重试 3 次
（`config.py` 的 `FETCH_*` 常量，可用环境变量覆盖）。

## 6. 翻译工作流（key 化 i18n）

翻译引擎为 `i18n.py`：**查表替换，零正则扫描**。产物在 `data/parsed/i18n/`：

- `<slug>.template.html` — 净化并改写路由后的 HTML 模板，文本节点替换为 `{{keyN}}` 占位，
  标签 / 链接 / 图片 / 表格结构原样保留；行内句子块带 `data-i18n-blk` 标记。
- `<slug>.json` — 双语字典：
  ```json
  {
    "key1": { "ja": "原文", "zh": "译文或空" },
    "_blocks": { "blk1": { "keys": ["key1"], "ja": "整句纯文本", "zh": "" } }
  }
  ```

**两级粒度**

- 节点级 `keyN`：结构（链接 / 加粗 / 图片）完整保留，逐节点查表替换。
- 行内句子块 `blkN`（块内全是行内标签且含 ≥2 个日文文本节点）：块内任一 `keyN` 缺译而整句
  译文存在时，整块回退为 zh 纯文本；块内 `keyN` 全部有译时优先节点级。

### i18n 子命令

| action | 作用 |
|---|---|
| `build` | 从 `parsed/ja/<slug>.html` 生成模板 + 双语 JSON。**默认按 ja 文本内容回贴已有译文**：句子没变的保住译文、变了的留空进待译，因此可在每次同步时安全执行。加 `--fresh` 则全量重翻（zh 全空），仅用于更换翻译引擎等场景 |
| `migrate` | 迁移旧 `[N]` 存量译文（`_translated_texts/<slug>.txt`） |
| `extract` | 生成待译清单 `tools/_todo_translate/<slug>_YYYYMMDD.txt` |
| `extract-dedup` | 跨页去重待译清单（每句只译一次） |
| `apply-dedup` | 把去重译文按出现位置写回所有页 |
| `fill` | 从 `*_translated.txt` 回填译文到 i18n JSON |
| `char-fill` | 给角色 JSON 补 `zh` 字段 |
| `glossary-fill` | 把词表已覆盖的词一次性注入各页 i18n（写进真值） |
| `repair-glossary` | 把词表**回补**到「已译但残留日文术语」的译文上。默认 dry-run，`--apply` 写盘 |
| `fix-br` | 规范化块级换行：把「zh 换行数与 ja 不一致」的块对齐（差异 ≤2 自动对齐，>2 清空重翻）。默认 dry-run，`--apply` 写盘 |
| `verify-links` | 校验 ja / zh 链接数量与位置是否一一对应 |

常用开关：`--pages`（限定 slug）、`--per-page`（按页日期命名，条目为 `[keyN]`/`[blkN]`，
直接对应 i18n id，**无错位**）、`--date`、`--todo`、`--pages-file`。

### 典型流程

```bash
escah-pipeline i18n build                  # 1. 重建模板与 JSON（回贴未变句子的译文）
escah-pipeline i18n extract --per-page     # 2. 导出待译清单
escah-pipeline gtrans                      # 3. 机翻 → *_translated.txt
escah-pipeline i18n fill --per-page        # 4. 按 key 回填真值
escah-pipeline sync-site                   # 5. 重建站点
```

> ⚠️ **不要加 `i18n build --fresh`**。默认模式会按 ja 文本回贴已有译文，
> 原站增删段落时只会让"变了的句子"进待译；`--fresh` 则清空全站译文（约 21 万条），
> 等同于全量重翻，人工精校成果会全部丢失。仅更换翻译引擎时才应使用它。

**待译清单格式**（与 `extract`/`fill` 严格对称，勿另创格式）：

- 开头若干 `#` 注释 / 提示词行 → 原样保留，不翻译
- 条目行 `[keyN] 日文` / `[blkN] 日文` / `[12] 日文` → 只翻译方括号后的正文
- **多行块按段拆分**成 `[blkN#1]` `[blkN#2]` …，每段独立成行
- 段分隔符 `===A===` → 原样保留（**丢了就 0 回填**）
- 页面映射记在 ASCII 元数据行 `# MAP A=<slug> …`

> **待译文本中不含任何换行标记。** 多行块的排版由段号承载：`extract` 按换行把块拆成
> 一段一条，回填时按段号顺序重新拼回，段数由原文决定并与译文强校验。
> 翻译者只需逐段照译，无需保留任何特殊字符。
>
> 旧方案把换行写成 `⏎` 夹在整句里、要求译文精确保留，实测造成全站 2% 的块换行数不符
> （中文页段落断行与日文原页错位）。该格式仅保留向后兼容，不再产出。

### 待译判定（三层，顺序不可颠倒）

1. **是否需译**：空串 / 纯拉丁 ASCII 数字（如 HP、Lv）/ 中日同形词白名单 → 不进待译；
   含假名或日式扩展汉字，或其余纯汉字（含繁体汉字句、日式专名）→ 需译。
2. **是否已译**：`zh` 非空 **且** `zh != ja` **且** `zh` 不含日文残留 → 跳过；否则进待译。
3. **词表整串覆盖 / 元数据戳 / 数字模板** → 跳过。

设计原则：**兜底 = 译**。拿不准的一律进待译，绝不靠正则推断「不译」去填 `zh = ja`。

## 7. 词表 `glossary/`

| 文件 | 用途 |
|---|---|
| `terms.yaml` | 站点 UI 文案（页面标题 / 侧栏 / 角色浮窗分段标题） |
| `names.yaml` | 专有名词（角色、声优、画师等） |
| `high_freq.yaml` | 全站高频游戏术语，含假名的走子串替换，纯汉字走整词精确匹配 |
| `link_terms.yaml` | 正文内链接文字 |
| `r18.yaml` | R18 术语（翻译前预替换） |

词表在渲染期由 `sitegen` → `i18n.render_locale` 自动套用，**仅对 zh 生效**，
优先级高于 i18n 译文。中日同形词或错译无法被词表覆盖时，必须直接改
`data/parsed/i18n/` 的源头 JSON。

> **技能/效果译文不再走词表**：原 `glossary/skills.yaml`（2770 条）已于 2026-08-31
> 移除（备份在 `recycle_bin/glossary/skills.yaml`）。它是「整串 ja → zh」的平译文，
> 不带排版信息，却因优先级高于 i18n 真值，会把带换行的整句译文打回无排版旧译文
> （角色浮窗 `zh` 长期不更新的根因）。其中 i18n 漏译的 35 条短技能名已迁移进
> i18n 真值，其余技能/效果一律以 i18n 为准，排版随 `_blocks` 的换行占位符保留。

## 8. 站点（VitePress）

- 双 locale：`root` = 日文（`link: /ja/`）、`zh` = 简体中文（`link: /zh/`）
- base：`process.env.BASE || '/escah/'`；Python 侧为 `ESCAH_BASE`（默认 `/escah/`），
  两处必须一致，否则站内绝对链接（`/zh/xxx.html`）会 404
- 侧边栏：`generated/sidebar.ja.json` / `sidebar.zh.json`，由 `sync-site` 生成，勿手改
- 正文：镜像页 `.md` 只 `import frag` 后交给 `MirrorContent.vue` 用 `v-html` 渲染
- 搜索功能已禁用（`config.ts` 中相关代码注释保留）
- 自定义目录树 `DocOutline.vue` 取代默认 outline
- 「数据统计」栏目：由 `pipeline/escah_pipeline/statpages.py` 依据 `data/statdata/*.json`
  直接渲染（**不是镜像页** ⇒ 不进 `data/registry`、不计入首页统计与更新履历），
  在 `sync_site` 里落 md + frag，侧栏由 `_write_sidebars` 显式注入「其他 → 数据统计」。
  表格加 `class="escah-tbl"` 即自动获得排序 / 列筛选 / 全屏（见 `tableEnhancer.ts`）。
  ⚠️ 两条硬约束：① 片段经 `v-html` 注入，**其中的链接不会被 base 重写** ⇒ 站内链接必须写相对路径；
  ② 表格增强器靠 `<th>` 行识别表头 ⇒ 生成的表必须带真正的表头行。
  质量自检：`python -m escah_pipeline.statpages --kana`（还剩多少日文）与
  `python tools/_dev/verify_statpages.py`（表格数 / 表头数 / 非空单元格数与数据源是否一致）。

### 8.1 SEO（Google / 百度）

全部在**构建期**生成，产物是静态标签，不依赖客户端 JS（百度爬虫不执行 JS）：

| 产物 | 实现位置 | 说明 |
|---|---|---|
| 每页独立摘要、canonical、hreflang、Open Graph、JSON-LD | `site/.vitepress/seo.ts`（`transformPageData` / `transformHead`） | description 取该页正文首段可读文本（不是全站共用一句）；canonical / hreflang 用绝对地址，按 `BASE` 推导 |
| `sitemap.xml` | `site/build.mjs` → `writeSitemap()` | 按 dist 里真实存在的页面生成，ja ↔ zh 用 `xhtml:link` 互指（含 `x-default`），日文文件名做百分号编码 |
| `robots.txt` | `site/build.mjs` → `writeRobots()` | 含 `Sitemap:` 声明；`404.html` 另外注入 `noindex` |
| 正文页可见 `<h1>` | `sitegen.MD_TEMPLATE` + `custom.css` 的 `.escah-page-h1` | 此前全站 0 个 h1 |

**主站地址（canonical / sitemap 域名）默认 self-canonical**：`BASE=/escah/` → `https://allindusk.github.io/escah`，
`BASE=/` → `https://escah.pages.dev`。两个镜像各自 canonical 到自己，任一镜像下线都不会把搜索引擎指向死链。
若要收敛到单一主站（放弃另一个镜像的收录），构建时设 `SEO_ORIGIN`（如 `SEO_ORIGIN=https://escah.pages.dev`）；
CI 里配 repository variable 即可让两地构建同步指向它。站长平台校验用 `GOOGLE_SITE_VERIFICATION` /
`BAIDU_SITE_VERIFICATION` 环境变量（不配则不输出对应 meta）。

> ⚠️ GitHub Pages 是项目页（`/escah/` 子路径），而爬虫只读**域名根**的 `robots.txt`，
> 因此 `.../escah/robots.txt` 对它不生效 ⇒ 需在 Search Console / 百度站长平台**手工提交**
> `https://allindusk.github.io/escah/sitemap.xml`。Cloudflare Pages 是根路径部署，`robots.txt` 直接生效。
> 首次上线后还应在两个站长平台各提交一次「站点地图 + 首页」，收录才会开始。

> sitemap 不用 VitePress 内置实现：内置版会对**每个页面**跑一次 `git log -1` 取 lastmod（1300+ 次子进程，
> 构建被拖到数分钟），且取到的只是 CI checkout 时间，对爬虫无意义。

## 9. 数据：真值 vs 可重建

**必须入库（不可重建）**

- `data/raw/` — 原站 HTML 快照
- `data/parsed/i18n/` — 译文真值（CI 构建 zh 站依赖它）
- `data/statdata/` — 攻略作者实测统计数据（「数据统计」页的数据源；原始素材已不在仓库，
  要改只能改这里，或按 `tools/_dev/parse_shiraberu.py` 的说明重新解析）
- `data/assets/img/` — 图片（Git LFS 跟踪，换机器 `git lfs pull` 即可）
- `data/registry/`、`data/manifest.json`、`charRefs.json`
- `glossary/`、`pipeline/`、`site/` 与 `tools/` 源码

**不入库 / 可重建**（见 `.gitignore`）

- `data/parsed/ja`、`data/parsed/characters`、`data/parsed/*.json`（i18n 除外）
- `site/public`、`site/ja|zh/*.md`、`site/.vitepress/frag`、`generated/sidebar.*.json`
- `site/.vitepress/dist`、`cache`、`theme/.gen-data`
- `tools/_todo_translate/`、`_translated_texts/`、`_texts_for_translation/`
- `data/logs/`、`recycle_bin/`

## 10. 自动化（GitHub Actions）

**`deploy.yml`** — push 到 `main` 或手动触发

1. checkout + Git LFS 对象缓存与增量 pull
2. Python 3.11 → `pip install -r requirements.txt` + `pip install -e pipeline`
3. `parse`（由入库的 `data/raw` 本地解析，**不联网**）
4. `sync-site`
5. Node 20 → `npm install` → `node build.mjs build`
6. 上传 Pages artifact → 部署 GitHub Pages
7. 可选：以 `BASE=/` 重建并部署到 Cloudflare Pages（需
   `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID`；未配置则跳过，标黄但不影响主部署）。
   重建前会用 `ESCAH_BASE=/` 重跑一次 `sync-site`：正文片段里的站内绝对链接带生成期 base 前缀，
   不重跑的话根路径部署的镜像站内链接全部 404（成片死链，直接影响收录）

**`sync-cron.yml`（2026-10-19 起只做一件事：原站更新履歴存档）** — ⏸️ **定时仍关闭**，
目前只能**手动触发**（Actions → Weekly Upstream Changelog → Run workflow）

> 初次手动运行已成功（2026-10-18，run 39156499263：HTTP 通道 1 次请求即拿到正文、
> 没用上浏览器兜底，产出 2026-W42 存档并自动提交）。要恢复每周自动跑，把
> `on.schedule` 那三行的 `# ` 删掉即可。

`changelog fetch` → 有变更则 commit & push `data/upstream/`。

- **抓取分两步（2026-10-19 起）**：先跑纯 HTTP 的 `changelog fetch`（内部已含 3 次
  退避重试）；**只有它失败**才安装 playwright chromium 并用 `--browser` 重试。
  之前是无条件下载 120 MiB 的 chromium，绝大多数周次根本用不上。
- **artifact 保留 90 天 ≠ 存档丢失**：artifact 只是「不 clone 也能下载本周结果」的
  临时件；真值是提交进 `data/upstream/` 的文件，跟 git 历史一起长期保存。

- ⚠️ **CI 不再自动同步/建站**：原先的 `discover → fetch → update → sync-recent →
  sync-stale → parse → assets → i18n build/glossary-fill/char-fill → sync-site →
  extract` 整条流水线已移除（历史版本见 git），镜像与发布**全部在本地完成后推送**。
- 它只发 **1 次请求**读原站「更新履歴ページ」（PukiWiki `#recent`，最新 100 条 =
  日期 + 页面名），与仓库里的 `registry`/`manifest` 对照后落存档：

  | 产物 | 用途 |
  |---|---|
  | `data/upstream/latest.json` | 最新一份（本地更新时读它） |
  | `data/upstream/weekly/<ISO周>.json` / `.md` | 按周存档 + 人类可读摘要 |
  | `data/upstream/history.ndjson` | 累积流水，可查"某页哪周动过" |

- 条目 `status`：`new`（原站有、本地未登记 → 需 `discover` + 抓取）／`update`
  （原站比本地快照新）／`unchanged`（本地已覆盖）／`frozen`（`no_auto_update`，
  站点照常渲染但不自动更新）／`excluded`（命中 `registry.EXCLUDE_PATTERNS`，
  **不单独建页**：MenuBar/SideBar/ヘッダ/フッタ 等 wiki 系统·导航页、練習/雛形
  模板页、`コメント/`·掲示板 等独立页）。
  ⚠️ 注意：**评论区是页面正文的一部分**（每个页面底部都有），随所属页面一起镜像；
  这里排除的是 PukiWiki 的**独立评论页**，不是页面里的评论区。
- 本地用法：`git pull` → `python -m escah_pipeline.cli changelog show`（看摘要）→
  `changelog names`（列出要处理的页面名）→ 定向 `fetch` / `update`，不必全量爬取比对。
- 解析到 0 条时命令**主动失败不落盘**（原站反爬等待页会把页面换成
  「少々お待ちください…」），以免空存档覆盖上周数据。
- ⚠️ **原站加了 Cloudflare 无感 JS 挑战**（2026-10-19 起，标题 `One moment, please...`
  + 5 秒后 JS reload，早先是日文「少々お待ちください…」）：不执行 JS 的客户端一律只
  拿得到 12KB 的挑战页。应对（按成本递增）：
  1. `changelog fetch --browser`：HTTP 被拦时改用真实浏览器（playwright+chromium）
     重试，能执行 JS，挑战通常会在 reload 后放行。**CI 只在 HTTP 失败时才装 chromium
     并走这条**；本机实测（2026-10-19）HTTP 3 次全被拦（末次 11976 字节挑战页），
     本地直接加 `--browser` 更省事；
  2. `WIKIRU_COOKIE` 环境变量 / `--cookie`：填浏览器里的 `cf_clearance=...` 直接通过
     （CI 侧可配同名 repository secret）；
  3. `changelog fetch --html <文件>`：浏览器打开更新履歴页另存 HTML，离线解析兜底。
  另外 `fetcher.is_challenge_page` 已补上这两类特征 —— 避免把挑战页当正文存进
  `data/raw`（那会触发重解析/重翻译，等于污染真值）。

## 11. 环境变量

| 变量 | 默认值 | 用途 |
|---|---|---|
| `ESCAH_BASE` | `/escah/` | Python 侧站内链接前缀，须与 VitePress `base` 一致 |
| `BASE` | `/escah/` | VitePress 侧 base（CF 部署时设为 `/`） |
| `FETCH_MIN_INTERVAL` / `FETCH_MAX_INTERVAL` | `2.0` / `4.0` | 抓取间隔（秒） |
| `FETCH_UA` | `escah-bilingual-mirror/0.1 …` | 抓取 User-Agent |
| `SEO_ORIGIN` / `SEO_SITE_PATH` | 按 `BASE` 推导（self-canonical） | 覆盖 canonical / sitemap 的主站地址（见 §8.1） |
| `GOOGLE_SITE_VERIFICATION` / `BAIDU_SITE_VERIFICATION` | 空 | 站长平台校验 meta，不配则不输出 |

`.env`（被 gitignore）由 `config.py` 通过 `python-dotenv` 自动加载。

## 12. 版本号与更新记录

当前站点版本：**1.2.15**（2026-10-19）。

前端版本号常量 `SITE_VERSION` 定义在
`site/.vitepress/theme/components/SiteAccessSwitch.vue`，更新记录数据位于
`site/.vitepress/theme/changelog.json`（由 `MirrorChangelog.vue`、`UpdateRecord.vue` 渲染）。

源码注释中明确要求：**改动前端后递增 `SITE_VERSION` 并同步维护 `changelog.json`，两者保持一致**。

### 12.1 生成物：哪些文件不要手改

| 生成物 | 生成者 |
|---|---|
| `site/{ja,zh}/<slug>.md`（镜像页） | `sync-site`（`sitegen._write_md`） |
| **`site/{ja,zh}/index.md`（首页）** | `sync-site`（`sitegen._home_md`）——加内容请改生成器 |
| `site/.vitepress/frag/*.json` | `sync-site` |
| `site/.vitepress/generated/sidebar.*.json` | `sync-site` |
| `site/.vitepress/theme/.gen-data/*` | `sync-site` |
| `site/index.md`（根跳转壳） | `sync-site` |

⚠️ 直接编辑上表文件会在下一次 `sync-site` 被覆盖，且因为内容与 HEAD 相同，`git diff`
里**看不出改动**（2026-10-19 首页「关于本站」就是这么丢的）。

### 12.2 术语与命名约定

- 玩法名统一写作 **Raid**（首个字母大写），不再使用「突袭战 / 突袭 / 讨伐」混称；
  正文、导航、页标题一致。**URL slug 仍为小写**（`raid.html` / `raid-recommended.html`），
  改大小写会断链、丢外链。
- 改页标题/侧栏文字需同时改两处：`glossary/terms.yaml` 的 `page_titles`，
  以及 `pipeline/escah_pipeline/i18n.py` 的 `_PAGE_SLUG_ZH_FALLBACK`
  （后者在 page_titles 之后 `update()`，会覆盖前者）。
- 技能文本的两个易混概念（详见 `glossary/` 词表注释）：
  `ダメージを回復` = 恢复**所受的伤害**（治疗/吸血）；`スタミナを回復` = 恢复**体力**，不可互译。
- 角色名一律不跳转：正文里的角色名（含角色页链接）统一降级为浮窗标签，
  悬停出预览、点击出固定浮窗（浮窗内提供「打开角色页」）。
- 扭蛋与卡券：`ガチャ` = **扭蛋**、`ガチャチケット` = **扭蛋券**（単発=单发/ 十連=十连 / 高级）。
  早期机翻的「招募 / 抽卡 / 抽卡券 / 单抽券」已于 2026-10-19 全站清零（326 处）。
- Raid 小节术语：`必殺ゲージ` = **必杀槽**（`必殺充填量` = 必杀充能量）、
  `フィーバー` = **FEVER**、`軽減率` = **减伤率**、`必殺技` = **必杀技**（不可译成「特殊技能 / 终极攻击」）。

#### ⚠️ 标题类文本为什么改了 i18n 却不生效（2026-10-19 踩坑，务必先读）

页面 `<h2>/<h3>` 大标题的 `ja` 原文里**内嵌了 `†` 锚点与多余空格**（例：
`<h2 id="content_1_0">キャラクターガチャ  <a …>†</a> …</h2>`），因此**对不上任何 i18n key**，
渲染时走的是 `glossary` 兜底链，而不是 `data/parsed/i18n/<slug>.json`。
兜底优先级（`i18n.py` 的 `_apply_overrides`）：

```
names.yaml（专有名词，子串） → 纠正映射 → high_freq.yaml → terms.yaml 的 inline_terms
```

由此产生两条硬规矩：

1. **只改 `<slug>.json` 里的 `zh` 改不动标题**，必须同时改 `glossary/` 里对应的 JA→ZH 词条。
2. **绝不要去改 `site/.vitepress/frag/*.zh.json`**（见 §12.1，那是被覆盖的生成物）。
   frag 层的临时补丁本地看着生效，下一次 `sync-site` 就消失，**CI 更是从头生成、根本不会带上**。

排查手法：`tools/_dev/_where_mt.py <token…>` 列出某机翻 token 在各 frag 的分布，
`tools/_dev/_verify_frag_terms.py` 做发版前全站体检。

## 13. 常用操作速查

```bash
# 全量重建（改了 i18n 引擎 / 模板 / 词表后必须走完整流程）
escah-pipeline parse
escah-pipeline sync-site
cd site && node build.mjs build

# 只重建站点内容（改了译文 JSON 或词表）
escah-pipeline sync-site && cd site && node build.mjs build

# 增量同步原站并翻译
escah-pipeline update

# 单独翻译某几页
escah-pipeline i18n extract --per-page --pages faq tips-tricks
escah-pipeline gtrans
escah-pipeline i18n fill --per-page --pages faq tips-tricks
escah-pipeline sync-site

# 校验 ja / zh 链接是否一一对应
escah-pipeline i18n verify-links
```

> ⚠️ 只跑 `node build.mjs build` 而不先跑 `sync-site`，会用旧的 `frag` 缓存，改动不生效。

### 13.1 译文排查工具（`tools/_dev/`，本地脚本，不入库）

```bash
# 导出某页的 ja|zh 对照，供人工精校（-u 避免管道缓冲吞输出）
python -u tools/_dev/_i18n_dump.py raid-formations gacha faq

# 发版前全站体检：机翻残留 token + 目标术语出现次数
python -X utf8 tools/_dev/_verify_frag_terms.py

# 定位某个机翻 token 分布在哪些页面、多少处
python -X utf8 tools/_dev/_where_mt.py 特殊技能 特殊招式 招募
```

判读要点：`招募` / `抽卡券` / `特殊技能` / `终极攻击` / `必杀能量槽` / `狂暴` 这类
**出现在正确语境之外**的词就是机翻残留；`_verify_frag_terms.py` 里 `GOOD` 段的词
（`扭蛋券` / `扭蛋`）是应当大量出现的规范译名。
⚠️ 残留计数长期不降时，先确认它是不是来自 `glossary` 兜底（见 §12.2）——那要改词表，不是改 `<slug>.json`。
