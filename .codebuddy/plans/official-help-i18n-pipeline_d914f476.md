---
name: official-help-i18n-pipeline
overview: 把"官方帮助中心"从根目录野路子文件改造为项目正规流程页面：递归抓取 App 站 help 全部分类正文 → 落盘 data/raw/公式ヘルプ.html → 注册进 pages.yaml → 走 parse/i18n build/extract 流水线，由用户翻译后 fill/sync-site/build 生成双语页，并清理根目录野路子文件。
todos:
  - id: crawl-help
    content: 用 [skill:playwright-cli] 递归展开 helptab 树节点抓全部分类正文
    status: completed
  - id: write-raw
    content: "将正文按原站层级包 #body 落盘 data/raw/公式ヘルプ.html"
    status: completed
    dependencies:
      - crawl-help
  - id: register-page
    content: 向 data/registry/pages.yaml 追加 official-help 注册项
    status: completed
    dependencies:
      - write-raw
  - id: run-pipeline
    content: 运行 parse 与 i18n build 生成 official-help 双语 JSON
    status: completed
    dependencies:
      - register-page
  - id: extract-todo
    content: 运行 i18n extract 产出待译清单交付用户翻译
    status: completed
    dependencies:
      - run-pipeline
  - id: cleanup-rogue
    content: 将根目录野路子文件与手写 md 移入 recycle_bin/
    status: completed
    dependencies:
      - register-page
---

## 用户需求

将游戏官方 App 站点（prod.e-heroines.net）「ヘルプ」目录的全部内容接入项目正规翻译流程，页面中文名「官方帮助中心」，入口置于顶部菜单「首页」之后。

## 产品概述

- 抓取官方 App 站「ヘルプ」目录下**全部**分类与子项正文（含二级树节点，如キャラクター強化→ステータス/覚醒強化、ガチャ→ガチャの種類等），不遗漏（修正前期仅抓到 76 条、漏掉树状子项的错误）。
- 将抓到的日文正文按原站分类层级组织，落盘到项目约定的 raw 位置 `data/raw/公式ヘルプ.html`。
- 注册页面进入流水线（`data/registry/pages.yaml`），使其走项目标准 `parse → i18n build → extract → fill → sync-site → build` 流程，由用户翻译后生成中日双语页。
- 清理前期在根目录创建的野路子文件（移入 `recycle_bin/`，不永久删除）。
- 顶部菜单已挂官方帮助中心入口（`config.ts`），保留即可。

## 核心功能

- 递归展开 Vue SPA 的 helptab 树节点，抓取全部分类正文（含嵌套子项）。
- 生成带 `#body` 包裹、按原站层级（h2/h3+段落）组织的日文 raw HTML。
- 直接写 `pages.yaml` 注册项（name=公式ヘルプ, slug=official-help, category=misc, mode=static），不触动 wikiru 发现逻辑。
- 运行 `parse`/`i18n build`/`extract` 产出待译清单交付用户翻译。
- 移除根目录 `help_待翻译.md`、`help_ja_source.json`、`help_snap.yaml`、`help_missing.json`、`_emit_md.py` 等野路子文件。

## 技术栈选择

- 语言/运行：Python 3（沿用 `pipeline/escah_pipeline` 与 `tools/` 现有脚本，标准库 + lxml/bs4/playwright-core）。
- 抓取：playwright-core（Edge channel），递归展开 Vue 树节点（前期已确认该站为 SPA，#app 无 `__vue_app__`、正文不内联 HTML，须 DOM 交互抓取）。
- 复用现有流水线：`parser_puki.parse_all`（读 `data/raw` 本地文件，不 fetch）、`i18n build/extract/fill`、`sitegen.sync_site`，零新增引擎代码。

## 实现方案

整体采用「递归抓取 App 站 help → 落盘 `data/raw/公式ヘルプ.html` → 注册 pages.yaml → 走标准 parse/i18n/extract 流水线 → 交付用户翻译 → fill/sync-site/build」的正规接入，彻底替换前期根目录野路子。

关键技术决策：

1. **不改写为 wikiru 发现页**：`official-help` 内容源是外部 App 站 SPA，`discover()` 会从 wikiru MenuBar 尝试 fetch 而失败。因此**直接往 `data/registry/pages.yaml` 追加一条注册项**（`name: 公式ヘルプ`、`slug: official-help`、`category: misc`、`mode: static`），`parse_all` 按 `page_filename(name)` 读本地 `data/raw/公式ヘルプ.html`，与 i18n/sync-site 用同一 slug 链路一致（已读 `snapshot.py:13`/`parser_puki.py:333`/`i18n.py:1112`/`sitegen.py:495` 确认）。
2. **递归展开树节点抓取**：前期漏抓因只做一级 BFS。修正为：从 helptab 根开始，对每个含子项的节点点击展开→等待子项渲染→递归，直到所有叶子正文面板展开，再逐面板抓正文。仅点击 Vue 内部链接（过滤 `twitter`/`ログイン`/外链，前期已踩坑）。
3. **raw HTML 结构适配 parser**：落盘文件必须包 `<div id="body">…</div>`（`parse_page_html` 取 `#body`，无则整页当正文）；正文用 h2（顶级分类）/h3（子项）+ 段落组织，保留日文原文原样（翻译由 `extract` 产出清单，遵循「ja 站保留日文」铁律）。
4. **菜单已就绪**：`config.ts:166,173` 的 nav 已指向 `/zh|ja/official-help.html`，slug 一致，无需改动。

性能与可靠性：抓取为一次性交互操作（数百节点），无性能瓶颈；parse/i18n 为 O(条目数) 线性，量极小。幂等：`parse` 按 raw 存在与否处理，`i18n build` 按归一化 ja 回贴已有 zh；重跑无副作用。

## 实现注意事项

- **接地**：落盘 raw 文件名必须 = `page_filename("公式ヘルプ")`（`quote(name, safe="")+".html"`，短于 180 字符直接用 `公式ヘルプ.html`），与 `pages.yaml` 的 `name` 字段严格对应，否则 parse 找不到 raw。
- **防回归**：清理野路子文件前，确认 `site/zh/official-help.md`、`site/ja/official-help.md` 是前期手写游离产物——`sync_site` 只处理 registry 内 `has_i18n` 页，这俩手写 md 不被管理，重跑会被覆盖或残留，须一并移 `recycle_bin/`。
- **blast radius**：仅新增 `data/raw/公式ヘルプ.html` + 改 `pages.yaml` + 清理根目录野文件；不改动 `registry.py` 发现逻辑、`parser_puki`、`i18n`、`sitegen` 核心代码、`config.ts`（nav 已正确）。
- **铁律遵守**：ja 站保留日文；blk.zh 不人工加换行；图片绝不动（App 站外链图先抓正文，pending_assets 后续按需补）。

## 架构设计

```mermaid
flowchart LR
  A[官方 App 站 helptab SPA] -->|playwright 递归展开树节点抓取| B[日文正文 全部分类+子项]
  B -->|按原站层级包 #body 落盘| C[data/raw/公式ヘルプ.html]
  C -->|parse_all 读本地 raw| D[data/parsed/ja/official-help.html + .chunks.json]
  D -->|i18n build_page| E[data/parsed/i18n/official-help.template.html + .json]
  E -->|extract 出 [N]日文清单| F[tools/_todo_translate/new_translation_*.txt]
  F -->|用户翻译后 fill| E
  E -->|sync-site render_locale| G[site/zh|ja/official-help.md]
  G -->|node build.mjs build| H[dist 双语页]
  I[pages.yaml 注册项 official-help] -->|驱动 parse/i18n/sync-site| D
  I -->|nav 链接| H
```

## 目录结构

```
escah/
├── data/
│   ├── raw/
│   │   └── 公式ヘルプ.html              # [NEW] 递归抓取的全部 helptab 日文正文，包 <div id="body">，按原站 h2/h3+段落层级组织
│   └── registry/
│       └── pages.yaml                  # [MODIFY] 追加注册项 {name: 公式ヘルプ, slug: official-help, category: misc, mode: static}
├── recycle_bin/                        # [MOVE] 野路子文件（不永久删）
│   ├── help_待翻译.md                   # 前期根目录错误产物
│   ├── help_ja_source.json
│   ├── help_snap.yaml
│   ├── help_missing.json
│   ├── _emit_md.py
│   └── site_zh_official-help.md        # 前期手写游离 md
│   └── site_ja_official-help.md
├── site/.vitepress/config.ts           # [KEEP] nav 已含 official-help 入口，无需改
└── tools/                              # [KEEP] 复用现有 i18n/parse 流程，无新增引擎
```

## 关键代码结构

```python
# data/registry/pages.yaml 追加的注册项（手动写入，不走 discover）
- name: 公式ヘルプ
  slug: official-help
  category: misc
  mode: static
```

## Agent Extensions

### Skill

- **playwright-cli**
- Purpose: 递归展开官方 App 站 helptab 的 Vue 树节点（含二级子项），抓取「ヘルプ」目录下全部日文正文
- Expected outcome: 获得完整分类+子项正文（修正前期仅 76 条、漏树状子项的错误），用于落盘 raw HTML