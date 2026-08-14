# Escah — 超昂大战 エスカレイション 中文镜像站

本站是 [escalationheroines.wikiru.jp](https://escalationheroines.wikiru.jp/)（PukiWiki）的**中日双语静态镜像**。
把日文原站抓取、解析为结构化数据，再用 VitePress 构建出 `ja`（日文）与 `zh`（中文）两套页面，
中文译文在渲染期套用专有名词/技能词表，并保留大量日文原站未汉化的成人内容不翻译。

部署由 GitHub Actions 完成：推送到 `main` 分支即触发 `.github/workflows/deploy.yml`，
自动执行 `sync-site → build`，产物发布到 GitHub Pages（`/escah/` 基路径）。

---

## 目录结构

```
escah/
├── .github/workflows/deploy.yml   # CI：push main 即构建并部署
├── data/
│   ├── raw/                       # 原站快照（git + LFS 入库），解析与抓取的输入源
│   ├── manifest.json              # 抓取清单（页面列表/配置）
│   ├── parsed/
│   │   ├── ja/                    # 日文解析产物（HTML），由 parse 重建，不入库
│   │   ├── characters/            # 角色 JSON（name/rarity/icon/sections）
│   │   └── i18n/                  # ⚠️ 人工译文唯一真值，必入库（CI 直接读它，不跑 i18n 构建）
│   └── assets/img/                # 图片（约 2900 图，LFS 入库）
├── glossary/                      # 渲染期词表（仅 zh 生效，手工维护）
│   ├── terms.yaml                 # 页面标题/章节/标签/术语
│   ├── names.yaml                 # 专名（角色/声优/画师/技能名），翻译绝对权威
│   ├── skills.yaml                # 必杀技/固有效果 JA→ZH
│   └── high_freq.yaml             # 高频词精确/子串纠正
├── site/                          # VitePress 前端（MPA，ja/zh 双 locale）
│   ├── .vitepress/theme/          # 自定义组件/样式/表格增强
│   ├── build.mjs                  # 中性名构建脚本（build / preview / dev）
│   ├── public/data/char/          # 角色 JSON 复制目标（供浮窗）
│   └── *.md                       # 站点页（sidebar 等由 sync-site 生成，勿手改）
├── pipeline/escah_pipeline/       # Python 流水线（discover/fetch/parse/assets/i18n/chara/sync-site）
├── tools/                         # 一次性/辅助脚本（含历史脚本，部分仅审计留痕）
└── llm_reco/                      # 大模型推荐角色子项目（独立文档见其目录）
```

---

## 技术栈

- **解析/构建流水线**：Python（`pipeline/escah_pipeline`），层间以文件为契约。
- **前端**：VitePress（MPA 模式，`ja`/`zh` 双 locale，`base: /escah/`）。
- **翻译方式**：见下方「翻译工作流」。译文不依赖 LLM 在线调用；专有名词/技能在渲染期套词表。
- **图片**：走 `withBase('/img/')`，原站图存于 `data/assets/img`（LFS）。
- **搜索**：VitePress 内置 local search（miniSearch），配置见 `site/.vitepress/config.ts`。

---

## 本地构建与预览

```powershell
# 1. 同步站点（把 parsed 数据烘焙成 frag、生成 site/*.md 与角色 JSON）
python -m escah_pipeline.cli sync-site

# 2. 构建 / 预览（在 site/ 目录下）
cd site
node build.mjs build     # 构建到 .vitepress/dist，并写入 .nojekyll
node build.mjs preview   # 预览（端口 4173，base /escah/，自动跳日文首页）
node build.mjs dev       # 开发服务器（端口 5173）
```

改动 `site/.vitepress/theme/` 下的组件或样式后，建议先删除 `.vitepress/cache` 再 build，避免缓存导致改动不生效。

> 图片与 LFS：`data/assets/img` 走 Git LFS，首次 clone 后 `git lfs pull` 拉取。

---

## 翻译工作流（key 化 i18n）

中文译文以 `data/parsed/i18n/` 下的 JSON 为**唯一真值**，由流水线直接读取构建，不在线调用翻译 API。

主要环节（`python -m escah_pipeline.cli i18n`）：

| 子命令 | 作用 |
| --- | --- |
| `build` | 解析日文页为 `<slug>.template.html` + `<slug>.json`（节点级 keyN / 整句块 blkN） |
| `extract` | 生成待译清单 `<日期>.txt` + 空白 `<日期>_translated.txt`（中日同形自动视为已译） |
| `fill` | 从 `<日期>_translated.txt` 按 `[N]` 序号回填中文；成功后移入 `_translated_texts` |
| `migrate` | 旧 `[N]` 译文按页面迁移（兼容历史遗留） |
| `char-fill` | 给角色数据 JSON 补 `zh` 字段（取代旧 `char_zh.py`） |

**渲染期词表覆盖**（`glossary/`，仅 zh 生效，优先级高于 i18n 译文）：

- `names.yaml` / `skills.yaml`：专有名词与技能名，**翻译绝对权威**，加词即生效。
- `terms.yaml`：页面标题、章节、标签、通用术语。
- `high_freq.yaml`：高频词的精确匹配与句中子串纠正（如避免错译）。

> 历史方案 `tools/zh_patch.py`（正则串替换引擎）已废弃，移入 `recycle_bin/`，请勿恢复使用。
> 同形词或错译无法被词表覆盖，必须直接修订 `data/parsed/i18n/` 源头 JSON。

---

## 抓取与解析

```powershell
python -m escah_pipeline.cli discover   # 按 manifest 发现页面
python -m escah_pipeline.cli fetch      # 抓取快照到 data/raw（LFS）
python -m escah_pipeline.cli parse      # 解析 ja HTML / 角色数据
```

`data/manifest.json` 控制抓取范围（含跳过成人内容页等开关）。解析产物 `data/parsed/ja/*` 与 `data/parsed/characters/*` 由流水线重建，**不入库**；仅 `data/parsed/i18n/` 例外（人工译文必入库）。

---

## 不要碰的

- `data/parsed/i18n/**`：译文真值，改完必须 commit，否则 CI 部署看不到。
- `data/assets/img/**`：原站图片（LFS 入库），新增图片须 `git lfs track` 后随提交入库。
- 官方帮助中心（公式ヘルプ）等由正文超链接进入的页面，仅经站内链接访问、不进导航栏；译文真值在 `data/parsed/i18n/<slug>.json`。
- `site/*.md` 的 sidebar/目录结构：由 `sync-site` 生成，手改会被覆盖。
- `recycle_bin/`：按约定只回收、不永久删除，勿手删。
- `glossary/names.yaml` 等词表：改专名译名需同步角色 JSON 与 `charRefs.json`（详见代码注释），否则浮窗/跳转失效。
- 成人内容正文：按项目约定不翻译，保持日文原文。
