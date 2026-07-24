# MEMORY

## 项目：ESCH — 超昂大战 WIKI 中日双语镜像站
- 目标：把 escalationheroines.wikiru.jp（PukiWiki）镜像本地，构建 ja/zh 双语静态站，部署 GitHub Pages（base `/escah/`）。
- 架构：Python 流水线（pipeline/escah_pipeline，子命令 discover/fetch/parse/assets/translate/update/sync-site）
  + VitePress 站点（site/，MPA，ja/zh 双 locale）。层间以文件为契约。
- 数据：data/raw(快照) + data/manifest.json(sha256) + data/parsed/{ja,zh,characters}(日文忠实/中文/角色JSON) +
  data/assets/img(哈希命名) + data/registry/pages.yaml(注册表) + glossary/glossary.yaml + overrides/zh(人工校对)。
- 翻译工具链：`tools/zh_patch.py`（词表替换引擎，ja→zh 全站页面）+
  `tools/char_zh.py`（复用 zh_patch.patch() 给角色 JSON tr 单元格补 `zh` 字段，幂等）+
  `tools/_freq_chars.py`（角色页全局残留按频次×长度排序→`_seg_chars.txt`）+ `tools/_page_seg.py <页>`（单页句级候选）。
  词表增长后重跑二者即同步生效。⚠️ 站点特设页「日中用語対照表」slug 必须是 `term-map`，
  不能叫 `glossary`——后者是 WIKI 镜像页「用語集」的 slug，同名会把镜像 md 覆盖掉（已修复过一次）。
- **LLM API 翻译管线（2026-07-24 新增）**：`tools/_export_for_api.py`（段落级导出，按块标签定界不拆句）
  + `tools/_split_for_api.py`（按页分 8 batch）× `tools/_api_pipeline.py`（全自动编排 + 注入）。
  旧 `_export_untranslated.py` + `_split_untranslated.py`（句子级 20 文件）仍保留供豆包方案使用。
  ⚠️ **GLM 模型（glm-5/glm-5.1/glm-5.2，走 tokenhub.tencentmaas.com 的 OpenAI 兼容接口，复用 HY3 的 key）默认开启思考**，
  必须 `extra_body={"thinking":{"type":"disabled"}}` 关掉，否则 reasoning token 烧光额度且 `content` 为空（官方文档 product/1823/132061 确认）。
  `_api_pipeline.py`（主 runner）与 `_run_translate.py`（简化版）都已加该参数。
  ⚠️ **运行方式**：`$env:PYTHONIOENCODING="utf-8"; python tools/_api_pipeline.py`（detached 后台跑）。
  zh_patch.py 子进程在 Win 下用 GBK 打印日文残留统计会 `UnicodeEncodeError` 崩，靠该 env 变量无侵入修复。
  2026-07-24 修复 `_api_pipeline.py` 的 bug：`ROOT` 在 `LOG_FILE` 前未定义(NameError)、`translate_batch` 缺 `global model_index`(UnboundLocalError)；
  新增**模型健康探测**（失败模型停用 10 分钟、自动改用能通的）、子批 1500 token、超时 60s、SDK `max_retries=0`。
  ✅ **2026-07-24 深夜更新**：接口已稳定，三模型全部可用且快。`_api_pipeline.py` 已重写为**多线程(默认6)+三模型 round-robin 并发**，
  含每模型限速器（tokenhub 每模型 RPM=60 → 间隔 1.1s，超了会 429 风暴）、429 退避重试、partial checkpoint、多轮续补漏行。
  实测 6 线程 ≈1100 段/分。⚠️ **历史事故**：旧版按行序 append/zip 译文（丢弃 [N] 序号），模型漏行导致 001 批错位注入 zh_patch.py，
  已回滚（备份 zh_patch.py.bak_rollback001）；新版按 [N] 序号对位、结果文件保留全局序号空洞。改并发/解析逻辑时切勿回退到按行序配对。
  ⚠️ **2026-07-24 改为「翻译-only、注入延后」工作流**（用户要求：本轮只翻译，注入后面做）：
  `_api_pipeline.py` 的 `main()` 默认只把每批译文落盘到 `tools/_api_results/<批>_result.json`，**不再自动注入、也不再自动跑 `zh_patch.py`/`char_zh.py`**。
  注入/应用统一留到事后用 `python tools/_api_pipeline.py inject` 子命令（遍历 `_api_results/*_result.json` → 调 `_inject_batch.py` 幂等写入 JA2ZH，已存在 key 跳过）。
  `main()` 用 `已有结果则跳过` 实现**可中断续跑**（重跑已译批仅重翻、注入跳过，浪费少量额度）。
  ⚠️ 已修 `_inject_batch.py` 用相对路径 `tools/zh_patch.py` 导致 CWD 不对时静默写失败/不生效的隐患 → 改为 `pathlib.Path(__file__).resolve().parent / 'zh_patch.py'` 绝对路径。
  注：001 批在改翻译-only 前已被旧代码译完（001_result.json 存在），008 批更早冒烟译完（008_result.json 存在）；重跑会自动跳过这俩，只译 002–007。

### 关键架构决策（务必遵守）
- **原文 HTML 注入方式**：PukiWiki 原始 HTML 经 `sitegen._sanitize_html`（lxml 平衡标签 + 折叠属性换行 +
  剔除 on*）后，以 JSON 文件 `site/.vitepress/frag/<slug>.json` 落盘，md 内 `import frag from "...json"`，
  由 `MirrorContent.vue` 用 `v-html` 渲染。**不可用 `?raw` 导入**（SSR 下返回空）。**不要**把原始 HTML 直接
  内联进 md（Vue 严格解析器报 "Element is missing end tag"）。
- 日文忠实：解析不纠错不删减；结构化角色数据存语言中立 JSON。
- 礼貌抓取：2~4s 间隔+抖动，429/5xx 按 10/20/40s 退避，断点续抓。
  下载图片可用环境变量 `FETCH_MIN_INTERVAL`/`FETCH_MAX_INTERVAL` 覆盖间隔（静态附件可设 0.6/1.2 提速）。
- **图片资产管线**：parse 阶段扫描每页 `#body` 的 <img>，把 attach2 图 URL→哈希名登记进
  `data/pending_assets.json`；`assets` 命令按此清单下载到 `data/assets/img/`（断点续传，跳过已存在）。
  ⚠️ PukiWiki 内容图被"查看大图"链接包裹 `<a href="...plugin=attach...">​<img></a>`，
  `parser_puki._remove_chrome` 处理 plugin=attach 链接时必须"含 img 则 unwrap 保留、否则 decompose"，
  切勿直接 decompose（否则连内容图一起删）。改 parser 后需 `parse --force` 重建 pending 再跑 assets。
- 全站图片总数应约 2386 张（非 627）。若发现 assets/img 明显偏少，先查是否又被 _remove_chrome 误删。

### 构建命令与两个已修复的阻断 bug
- 用户标准：`cd site && npm run build`（构建后自动写 `.nojekyll`）。
- 本机 harness 会把 `vitepress build` 当 watch 杀掉；用 `node build.mjs`（中性名，调用 vitepress 编程式 build API）
  以 Start-Process detached 运行可正常完成。
- ⚠️ `site/build.mjs` 必须 `import { build, serve, createServer }` —— 本机 vitepress 版本**只导出这三者**，
  没有 `dev`/`preview`。旧代码 import 了 `dev` 导致整模块加载失败、build 不执行、dist 不更新。
- ⚠️ **所有 `site/*.md`（含 `index.md`）、sidebar 等都是由 `sync-site` 用 `sitegen.py` 模板重新生成的，
  不要手改这些文件，否则下次 `sync-site` 会被覆盖回退**。根跳转页重定向逻辑在 `sitegen.py:318` 附近模板，
  必须放在 `<script setup>` 的 `onMounted` 里（仅客户端执行 `location.replace`），否则 SSR 渲染首页时
  `ReferenceError: location is not defined` 让构建崩溃。
- 图片引用链：frag 用 `/img/HASH` → `MirrorContent.vue` 渲染时 `withBase('/img/')` → `/escah/img/HASH` →
  `dist/img`（构建自 `site/public/img`←`data/assets/img`）。改 parser/新增图片后务必 `sync-site` 再 `build.mjs build`，
  否则 dist 是旧快照（图缺）。

### 镜像计划配置与自动更新（2026-07-24）
- **`data/registry/mirror_plan.yaml`**（新增，由 `sync-plan` 生成）：顶层 `planned`（待镜像页，默认空，可填页名字符串或 `{name,group}`）
  与 `mirrored`（已镜像页，按原 WIKI 11 组分组有序：`ゲームガイド/キャラクター一覧/キャラクター一覧SSR/SR/R/サポーター/NPC/
  システム/装備･アイテム/クエスト･ミッション/その他`，每条含 name/slug/url）。`pages.yaml` 仍是机器侧真源，二者经 `sync-plan` 保持同步。
- `pipeline/escah_pipeline/plan.py`：11 组映射 `page_group(entry)`、解析 WIKI 最后编辑时间 `parse_wiki_lastmod`（已移至 `fetcher.py`）、
  `fetch_recent_changes`（PukiWiki `?cmd=rss` 近期变更页，用于每日增量）、`build/load/save_mirror_plan`、`sync_plan`。
- 自动更新 = 本地命令 `python -m escah_pipeline.cli update`（默认 RSS 增量；`--full` 逐页比对最后编辑时间；`--no-translate` 跳过重译）。
  **不配置 GitHub Action**（决策：CI 内 AI 无法为新散文补译 `zh_patch.py` 词条，确定性重跑会遗留未译日文；故人工翻译+更新由用户在对话里触发）。
- `updater.run_update` 流程：处理 planned(抓/解析/注册/移入 mirrored) → RSS/`--full` 检测变更 → 重抓+`parse_all(force)`+
  `extract_all_characters` → **子进程跑 `tools/zh_patch.py`** → `download_assets`+`sync_site`+刷新 plan+写 manifest。
- **translate 命令为跑 `tools/zh_patch.py`（词表确定性替换）。** 翻译由 AI 通过扩展 `zh_patch.py` 的 JA2ZH/GENERIC/REGEX_RULES 词表完成，本地确定性可复跑。
- `snapshot.Manifest.record_page` 新增 `wiki_last_modified` 字段（存页面内 `最終更新日時:YYYY-MM-DD (曜) HH:MM:SS`），`fetcher.parse_wiki_lastmod` 提取。
- 实测当前注册表 ~418 页（SSR 259 / R 86 / SR 27 / システム 17 / クエスト 6 / 装備 4 / ゲームガイド 4 / キャラクター一覧 8 / サポーター 1 / NPC 1 / その他 5）。

## 用户偏好与运行约定
- **用户硬件**：AMD Ryzen 7 8845HS（8 核 16 线程）。本地脚本并行上限统一取 `min(os.cpu_count() or 4, 16)`。
- **强偏好**：本地跑的应用"尽量多线程尽快处理"。凡 CPU/IO 密集且无共享可变状态的串行脚本（逐页/逐文件/逐图处理），应主动改造成 `ProcessPoolExecutor`（CPU 密集）或 `ThreadPoolExecutor`（IO 密集）；worker 返回局部结果、主线程合并，保证结果幂等零差异。
- **不可盲目并行**：`fetch_registered_pages`（单个 PoliteFetcher 全局礼貌限速 2–4s，并发会破坏限速→封禁/429）、`sync_site`（manifest/sidebar 顺序依赖）、`build.mjs`（Vite 本就多线程，仅需 detached 防 harness 强杀）。
- 已并行化：tools/zh_patch.py、tools/char_zh.py、tools/_freq_chars.py、parser_puki.parse_all、assets.download_assets。
- **回收站约定（最高优先级，防误删）**：用户极度反感文件被永久删除（曾遇 deepseek 误删找不回）。凡识别为过期/无用的文件，**一律移入项目根 `recycle_bin/`**（按 `recycle_bin/tools/`、`recycle_bin/root/` 等子目录归类），**绝不 `git rm` 或永久删除**，随时可恢复。2026-07-25 首次执行：tools/ 仅保留 13 个活跃文件（zh_patch/char_zh/_freq_chars/_page_seg/_inject_batch/_api_pipeline/_export_for_api/_split_for_api/_export_untranslated/_split_untranslated/gen_char_refs + 两个备份 zh_patch.bak.py、zh_patch.py.bak_rollback001），其余一次性注入脚本/注入批次 json/调试分段产物/日志/_api_batches/_api_results/_untranslated 子目录共 ~247 项移入回收站。今后任何清理默认只进回收站。
