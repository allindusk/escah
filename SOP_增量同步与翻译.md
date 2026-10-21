# 增量同步 → 翻译 → 二次精校 → 上线（供大模型执行的作业规程）

> 适用场景：GitHub Actions 定时抓取原站产物后，由**大模型**在本地执行「拉取 → 零网络重建 → 增量翻译 → 二次校对润色 → 验收 → 落地/上线」。
> 本文件是唯一作业依据；按阶段顺序执行，不要跳步。凡与本文件冲突的临时指令，先停下来问用户。

---

## 0. 你的角色与十条铁律

**角色**：你是《超昂大战》（エスカレーション・ヒロインズ）WIKI 中日本地化项目的**游戏翻译专家**。
译文必须用你的自然语言能力重新组织成「中文游戏攻略/维基」该有的样子，**不是机翻、不是逐词直译、不是挑词表变体**。

| # | 铁律 | 违反后果 |
|---|---|---|
| 1 | **只改 `zh`，绝不改 `ja`**（`ja` 是匹配键） | 改了 ja = 该条译文永久失配、进待译队列重来 |
| 2 | **数值/百分比/倍率/时间/次数/星级一字不改**（`人数×5%`、`999秒`、`VERY HARD`、`★5`） | 攻略数据错，用户会直接发现 |
| 3 | **不机翻、不逐词直译**；按中文语境重写句子、按中文习惯断句 | 会被判为「机翻」退回 |
| 4 | **专名一律以词表为准**（`glossary/names.yaml` > `characters_generated.yaml` > `characters.yaml` > `terms.yaml` > `high_freq.yaml`） | 同角色多译名，全站不一致 |
| 5 | **R18 内容不读、不译、不打印**；只做机械导出/回填（见 §3.3） | 触发内容审查，任务中断 |
| 6 | 只改 `data/parsed/i18n/*.json` 与 `glossary/*.yaml`；**不改 `site/` 生成物、不改 `data/parsed/ja/`** | 改动会在下次重建时被覆盖，白做 |
| 7 | 批次中间**不跑 `sync-site` / 不构建**，全部做完再跑一次 | 每次重建几分钟，纯浪费 |
| 8 | 不跑 `local-sync --fresh`、不跑「全量 i18n build」、不跑 `parse` 全量 `--force` | 会把历史脏数据扩散到全站（实测改动 86 个入库文件） |
| 9 | 交付必须**自证**（渲染口径残留率 + 抽样对照 + 数值抽查），数字写进提交信息 | 未自证视为未完成 |
| 10 | 拿不准（段数对不上、清单 id 缺失、页面性质不明）→ **停下报告**，不要猜着改 | 错误数据比缺译更糟 |

**Windows 环境三条硬规则**（否则会踩到莫名其妙的错）：
1. 需要跑多行 Python 时**写成 .py 文件再执行**，不要用 `python -c "…"` 内联（PowerShell 会吃掉 `$`、引号）。
2. 打印中文前先 `sys.stdout.reconfigure(encoding="utf-8")`，并用 `python -u`（否则 GBK 编码报错/丢输出）。
3. 不要在同一句命令里既读又写同一个文件（会被守卫拦下）；改文件用文本编辑工具或脚本。

---

## 1. 一次看懂：真值与产物

| 路径 | 性质 | 可否手改 |
|---|---|---|
| `data/parsed/i18n/<slug>.json` | **译文真值**（`keyN`/`blkN` 两级，含 `ja`/`zh`） | ✅ 只能通过工具按 id 改 |
| `data/parsed/i18n/<slug>.template.html` | 渲染模板（文本已被 `{{keyN}}` 占位） | ❌ 生成物 |
| `data/registry/pages.yaml` | 镜像页登记表（slug/category/subgroup） | ✅ 新页登记 |
| `glossary/*.yaml` | 词表（专名/术语/高频/整句/保留日文/R18 送翻预替换） | ✅ 但要谨慎（见 §9 坑 8） |
| `data/raw/**` | 原站快照（镜像唯一来源，CI 抓） | ❌ |
| `data/manifest.json` | 每页 URL/时间戳/sha256/`parsed_sha256` | ❌ 只经 CLI 写 |
| `data/upstream/**` | 更新履歴存档、构建报告（工具报告，不入库） | ❌ |
| `tools/_todo_translate/**` | 待译清单 / 译文回填文件（不入库） | ✅ 清单由工具生成 |
| `site/**` | VitePress 站点内容（可重建，绝大多数不入库） | ❌ 生成物 |

---

## 2. 阶段 A：拉取 CI 产物

### A1. 同步远端

```powershell
cd <repo>
git pull --rebase origin main
```

- CI 的抓取提交形如 `chore(fetch): 原站增量镜像 YYYY-MM-DD`，由 `escah-bot` 提交。
- 若同时有本地未推送的译文提交，**先提交/推送再 pull**，避免 rebase 卡在冲突里。

### A2. 必须处理的唯一冲突：`data/manifest.json`

两侧都会写这个 1MB 单文件（CI 写抓取侧、本地写解析侧），pull 时**必然**可能冲突。
`manifest merge` 的约定是：`data/manifest.json` 放**本地侧**，另一侧改名成 `data/manifest.merge-theirs.json`。

```powershell
# 1) 若已冲突：先让 CI 侧落到工作区，再改名留存
git checkout --theirs data/manifest.json
git mv data/manifest.json data/manifest.merge-theirs.json
# 2) 本地侧回到工作区
git checkout --ours data/manifest.json

# 3) 合并（按页取 fetched_at 较新者；parsed_sha256 只信本地侧；pending_assets 取并集）
python -u -m escah_pipeline.cli manifest merge --dry-run   # 先看差异
python -u -m escah_pipeline.cli manifest merge
python -u -m escah_pipeline.cli manifest status            # 概览自检
Remove-Item data/manifest.merge-theirs.json                # 合并成功后再删
```

> `pending_assets.json` 同理：若它也冲突，另一侧改名成 `data/pending_assets.merge-theirs.json`，
> `manifest merge` 会按并集合并（两份都要留），合并后删除该临时文件。

> `manifest.json` 里的 `parsed_sha256` 是**本机解析进度标记**。CI 侧永远不写它（CI 用 `parse --no-mark`），
> 所以合并后必须以本地侧为准。若这里弄错，本地 `parse` 会静默跳过、站点继续用旧内容且**不报错**。

### A3. 判断「本轮到底新增/更新了什么」

按顺序读三个文件（都在仓库里，不需要联网）：

1. `data/upstream/latest.json`
   - `counts`：`new` / `update` / `unchanged` / `excluded`
   - `window` 与 `truncated`：**`truncated: true` 表示只覆盖「最新 100 条」更新时间线**，窗口外的改动不在本轮
   - `items[]`：`status` 为 `new`/`update` 的条目即候选；`slug: null` = **未登记的新页**
2. `data/recent_state.json`
   - `candidates` / `hash_forced`：本轮比对过的页数（按正文 sha256 判定，不信时间戳）
   - `changed[]`：实际内容变化页
   - `unregistered[]`：未登记页（多为新角色页）；`known_nav[]`：有意不镜像的导航页；`frozen[]`：时间戳冻结页
   - `fell_back` / `reason`：是否回退到全量通道、为什么
3. `data/pending_assets.json`：待下载图清单。全部应已存在于 `data/assets/img/`（CI 下载即转 WebP）。
   抽查方式：统计条目数 vs 磁盘缺失数，缺失 >0 才需要处理。

### A4. 新页登记（只在确认为「角色页/装备页」时才做）

- 更新履歴里 `status=new` 且 `slug=null` 的页，CI **不会自动抓**（未登记）。
- **允许**自动登记的类型：角色详情页（`characters/<名>`，`category: character-detail`）、
  装备子页（`equip-NNN`，`category: subpage`）、B 宇宙 BOSS 页（`buniv-NNN`，`category: subpage` + `subgroup: b-universe`）。
- **禁止**自动登记：左侧导航类页面（会改变站点骨架），必须人工拍板。
- 登记后**必须推送**：CI 只读 `main` 分支的 `data/registry/pages.yaml`，下一轮 `fetch --mode all` 才会把缺快照的页补齐。
- 登记条目格式（照抄同组已有条目）：

```yaml
- name: 青竜天クチナワ（Bユニバース）
  slug: buniv-012
  category: subpage
  subgroup: b-universe
```

---

## 3. 阶段 B：本地零网络重建（`local-sync`）

### B1. 命令

```powershell
python -u -m escah_pipeline.cli local-sync
# 只处理部分页：
python -u -m escah_pipeline.cli local-sync --pages "characters/X" shop
# 只重建不翻译（排查用）：
python -u -m escah_pipeline.cli local-sync --no-extract --no-site
```

它做的事（全程**不联网**）：`parse`（按 sha256 增量）→ `i18n build`（只 build ja 内容变过的页）→
`char-fill`（角色 JSON 补 zh）→ 待译清单 `extract` → `sync-site`。

### B2. 读输出，重点四行

```
解析完成：成功 N，跳过 M，失败 0；待下载图片 K
i18n build N/N
⚠️ 本轮共 W 条旧译文失效，明细见 data/upstream/build_report.json
local-sync 完成：解析 N 页｜i18n build N 页｜待译清单 X 个｜旧译文失效 W 条｜缺图 0 张｜站点已生成
```

**「旧译文失效 W 条」不是译文被冲掉**：它是「原站改文/删段 → 旧译文对应的原文不存在了」。
典型地，角色页/寝室页评论区日期串（`2021-01-14 (木) 09:23:22` ↔ 旧译 `(周四)`）会成批出现在这里，
那是评论列表变动导致旧节点消失，**不需要处理**。

### B3. 必须自证「没有回退」

```powershell
# 与 HEAD 基线比对：本轮改过的 i18n 文件里，空译净增应为 ≤0（特例：本轮原站真的新增了句子的页会有净增）
git -c core.quotepath=false diff --name-only HEAD -- data/parsed/i18n
```

自证口径（按 ja 文本配对，**不要按 keyN 编号**，编号会平移）：
- 「含假名且 zh 为空」的节点数：本轮后 ≤ 本轮前
- 「ja 含日文星期且 zh 为空」：应为 0 增长
- 唯一允许净增的页，必须是 `recent_state.changed` 里真实改过文的页

---

## 4. 阶段 C：待译清单与分诊

### C1. 清单格式

`tools/_todo_translate/` 下按页按日期生成：

```
<safe>_<YYYYMMDD>.txt          # 单卷
<safe>_<YYYYMMDD>_A.txt / _B.txt   # 单页累计 >1 万字符时切卷
<safe>_<YYYYMMDD>_index.json   # {id: {ja, vol, kind}}，id ↔ 卷映射
```

- `<safe>` = slug 把 `/` 换成 `__`（如 `characters__パイレーツハダル`）。
- 正文每行 `[keyN] 日文` 或 `[blkN#i] 日文`（`blkN` 是整句块，`#i` 是段号，段之间原本是 `<br>`）。
- **跨页/跨块去重**：同一文本只在首次出现的页列一次；`fill` 时按内容广播回填到所有位置。所以**同一条只译一次就够**。
- **清单会自己消失**：某页已无待译（或已被词表覆盖）时，`extract` 会删掉旧清单。清单没了 = 没活儿，不是丢数据。

### C2. 分诊：先按页分「普通」与「R18」

- **R18 页**（默认名单：`bedroom-scenes`；其它含「寝室」「シーン」场景列表的页同理）：**不要打开清单**。
- **普通页**：进入 §5 翻译。
- 拿不准某页是否含 R18 → 先问用户，不要试探性读取。

### C3. R18 导出（模型不读内容）

```powershell
python -u tools/sop/r18_export.py --date 20261021
# 多个 R18 页：
python -u tools/sop/r18_export.py --date 20261021 --slugs bedroom-scenes bedroom-xxx
```

产物在 `tools/_todo_translate/_r18_manual/`（清单与原文件同格式的副本）。
**把目录路径告诉用户，让用户人工逐句翻**；模型在此阶段只报「导出多少条」，任何情况下不得 `type`/`cat`/`Get-Content` 这些文件。

用户翻完交回后（文件名随意，格式 `[id] 中文` 一行一条）：

```powershell
python -u tools/sop/r18_apply.py --date 20261021            # 看统计：各卷清单条数 / 已提供 / 缺哪些 id
python -u tools/sop/r18_apply.py --date 20261021 --apply     # 写出 <stem>_translated.txt
python -u -m escah_pipeline.cli i18n fill --date 20261021 --pages bedroom-scenes
python -u tools/sop/coverage.py bedroom-scenes --list 5      # 只看数字：块覆盖 / 渲染残留率 / 剩余空译 id
```

缺口处理（只按数字判断，不读内容）：
- 「缺 N 条」→ 把缺的 id 列表给用户补；不要自己补写 R18 译文。
- 「段号越界」→ 说明人工译文把某一段拆成了两行（段数 = 原 `ja` 里 `\x01` 分隔的段数）。
  处理方式：把多出来的那两段按**语义连续性**拼回一段（可用段末标点判断：以 `、`/`，`/`…` 结尾的是句中续接），
  再让用户确认。

---

## 5. 阶段 D：翻译（普通页，用自然语言能力）

### D1. 译前必做的三件事

1. **整页通读**（关键，不要只看待译条目）：

```powershell
python -u -X utf8 tools/_dev/_page_dump.py "characters/<名>" --min 12
```

把整页（含已有的中文译文、评论区、表格）读一遍：才能判断语气、指代、术语、有没有串行错位。
若 `tools/_dev/_page_dump.py` 不存在（新环境），改用 `coverage.py --list` + 直接读 i18n JSON。

2. **读词表**（至少这四张，用 `grep` 或搜索定位，不要整篇背）：
   - `glossary/names.yaml`：专名权威译名（最高优先）
   - `glossary/terms.yaml`：UI/属性/系统术语
   - `glossary/high_freq.yaml`：高频短语整句
   - `glossary/r18.yaml`：R18 术语（仅在送翻预替换层用，普通页不必读）

3. **确认参考口径**：项目既有的同类页译文就是「标准答案」，新页要与它一致
   （例：`支援者` 不写「支持者/支持者型」；`Raid` 不写「突袭战/讨伐」；`ダメージ`=所受伤害、`スタミナ`=体力，二者不可混译）。

### D2. 逐条翻译规则

| 规则 | 说明 |
|---|---|
| 一行对一条 | 输出 `[id] 中文`，id 与输入**完全一致**，不合并、不重排、不增删 |
| 句内结构跟随原文 | 原文有 `<br>`（清单里表现为分段）时，中文按语义重新断行即可，**段数不必与原文一致但要能读通**；回填时按段号对齐，所以**清单里有几段就给几段** |
| 数值/符号 | 全角半角按中文习惯（`％`→`%` 可保留原样），但**数字本身不动**；`×`、`＋`、`（）` 统一用中文全角时不要改数值 |
| 专名 | 查表；表里没有的记录到报告里（不要自创后不告知） |
| 拟声/口癖/语气 | 保留角色口癖（`～`、`！！`、`……`），但用中文拟声（`ドキドキ`→`心跳加速`） |
| 省略主语 | 日文常省略主语，中文按上下文补「他/她/该角色」，不要写成「我」 |
| 表格短标签 | 属性名/数值标签优先用 `terms.yaml` 标准译名，不要即兴翻译 |
| 中日同形词 | `防御力`/`上限`/`対象`→`对象` 这类按项目既有译法；旧字体必须转简体（`備考`→`备注`、`装備`→`装备`、`状態異常`→`状态异常`、`確率`→`概率`、`項目`→`项目`、`無料`→`免费`、`効果`→`效果`） |
| 保留日文 | 角色本名、声优名、画师名、五十音行标题、技能/装备的「日文原名注音」按项目规则保留日文（见 `glossary/retain_ja.yaml`），**但保留名单里不该出现公式/台词/技能名**（见 §9 坑 3） |
| 不许加注 | 不要在译文里加「（意译）」「（注：…）」这类说明，除非原文本身有注 |

### D3. 输出

写到 `tools/_todo_translate/<stem>_translated.txt`（与清单同 stem，加 `_translated`）。
只写 `[id] 中文` 行，不要写表头/解释。

```powershell
python -u -m escah_pipeline.cli i18n fill --date 20261021 --pages "characters/X" shop
```

`fill` 行为要点（务必理解，否则会「改了没生效」）：
- **只写空译**：目标已有 `zh` 时**直接跳过**（不会覆盖）。已有译文要改 → 走 §6 的覆盖路径。
- 段级回填：整句块按段号拼回 `\x01`，段号必须落在 `1..段数` 内，越界整块跳过（会打 WARNING）。
- 按 id 精确写 + 按内容广播（去重掉的同文条目一并回填）。
- 写完把 `*_translated.txt` 移到 `tools/_translated_texts/` 留档。

---

## 6. 阶段 E：二次翻译校对润色（**与「重新翻译」不是一回事**）

### E1. 定义与边界

| | 二次校对润色（本阶段） | 重新翻译 |
|---|---|---|
| 起点 | **以现有译文为基线** | 忽略现有译文，从 ja 重写 |
| 动作 | 逐条对照原文，**只改有问题的部分**（最小必要修改） | 整段重写 |
| 目标 | 准确、术语统一、中文自然、与上下文一致 | 得到一版新译文 |
| 何时升级为「重新翻译」 | 整段机翻腔严重 / 发现串行错位 / 该页问题率 >40% | — |

**默认做前者。** 不要因为「我有更好的写法」就整页重写——会破坏已统一的术语与用户已确认的语感。

### E2. 标准动作

```powershell
# 1) 整页通读（含现有译文）
python -u -X utf8 tools/_dev/_page_dump.py "characters/<名>" --min 12
# 2) 看覆盖度基线
python -u tools/sop/coverage.py "characters/<名>" --list 20
# 3) 写 fix 字典（id → 新 zh），一次写完该页所有要改的条目
#    {"key12": "…", "blk3#2": "…"}
python -u tools/sop/set_zh.py "characters/<名>" fix_<名>.json          # dry-run 看条数
python -u tools/sop/set_zh.py "characters/<名>" fix_<名>.json --apply
# 4) 若改的是「块内节点」，同步块级（否则页面不变，见 §9 坑 2）
python -u tools/sop/block_sync.py "characters/<名>" --apply
# 5) 复测
python -u tools/sop/coverage.py "characters/<名>" --list 5
```

### E3. 十二项检查表（逐项过，缺一不可）

1. **漏译**：`zh` 为空、或 `zh` 仍含假名（`coverage.py --list` 会给出 id 与假名字数）。
2. **误译/反译**：意思相反（`〜しない` 译成肯定、`条件を緩和` 译成收紧）。
3. **术语**：对照 §D2 与词表；同一概念全页同一译法。
4. **数值**：数字、百分号、倍率、秒数、人数、（`★N`）、Layer/难度名。
5. **专名**：与 `names.yaml` 一致；角色名不要被当成普通词翻（`ナリカ`→成香，不是「香薰」）。
6. **语序与中文通顺**：机翻腔（"的的"、"进行了…的实施"、欧化长句）必须重写。
7. **语气**：攻略正文=客观陈述；评论区=玩家口吻（可带口语、吐槽）。
8. **旧字体/同形未转**：`備考/装備/状態異常/確率/項目/無料/効果` 等（§D2 列表）。
9. **标点与结构**：`<br>` 段数、括号配对、`「」`→ 中文引号（项目正文多用「」保持一致）、多余空格。
10. **重复**：同一句在同一段出现两次（复制粘贴错）；句末多一个句号。
11. **串行错位**：连续多条译文与原文**整体错位一格**（单条看通顺，整页读才暴露）。发现即整页按 ja 重写，并同步块级。
12. **与上下文矛盾**：与本页其它段/表格数据打架（例：上文说 3 人、译文写 4 人）。

### E4. 判定标准（三档，避免过度修改）

- **必须改**：错译/反译、数值错、专名错、漏译、串行错位、术语违反词表。
- **建议改**：机翻腔、指代不明、中文不通顺、重复。
- **不要改**：仅因个人偏好换同义词；风格差异；刻意保留的日文（本名/声优/画师/注音）。

### E5. 两套节点（最容易漏的地方）

同一段原文常常**同时**存在 `keyN`（节点级）与 `blkN`（整句块级）两份数据：

- 渲染顺序：**块级 `blk.zh` 存在时整块用块级译文替换，节点级结构不保留** → 只改 `keyN` 页面不会变。
- 例外（块级回退被跳过，节点级才是唯一显示源）：块内嵌 `<img>`、块内含角色名标记（`data-char`/`char-ref`/`plugin-tooltip`）、
  页面属于「链接索引类」（`artists`、`voice-actors`）。
- 正确做法：改完 `keyN` 后跑 `block_sync.py`，或干脆用 `set_zh.py` 直接写 `blkN#i`。

---

## 7. 阶段 F：验收（必须自证）

### F1. 渲染口径（唯一可信口径）

```powershell
python -u tools/sop/coverage.py "<slug>" --list 10
python -u -X utf8 tools/_dev/_kana_residue.py "<slug>"     # 会列出残留片段，用于确认是否只剩本名/声优名
```

- 判据：**渲染后** zh 页的假名字符数（不是 i18n JSON 里的空译数）。
- 目标：普通正文页残留率 **≤ 0.10%**；剩余应只有本名/声优/画师/刻意注音。

### F2. 语义抽样（不可省）

- 每页抽 8～10 条（含最长的 3 条、含数值的 3 条、评论区的 2 条），逐条对照 ja 判断准确度。
- 发现 1 条错 → 该页**全量重查同类**（同段/同表/同批机翻），别只修那一条。

### F3. 结构抽查

- 表格：行数/列数与 ja 页一致（用渲染产物抽 1 个表数 `<tr>`/`<td>`）。
- 链接/图片：`site/.vitepress/frag/<slug>.zh.json` 里不含 `{{key`（占位符未替换）与 `src=""`。
- 占位符残留：`grep -c "{{" site/.vitepress/frag/<slug>.zh.json` 应为 0。

### F4. 交付数字（写进提交信息）

```
该页：块级 46/46｜节点 413/444｜渲染假名 13 字（0.25%）｜本轮改 29 条
全站本轮：i18n 变更 N 页｜空译净增 ≤0（列出净增页与原因）
```

---

## 8. 阶段 G：落地与上线

### G1. 生成站点内容

```powershell
python -u -X utf8 -m escah_pipeline.cli sync-site
# 输出示例：站点内容生成完成：md 1508 页，角色 450，角色数据 450，图片 3129
```

### G2. 构建（只是本地验证时才需要）

```powershell
cd site
node build.mjs build      # ✅ 唯一正确方式：会额外写 .nojekyll、并暴露真实报错
# ❌ 不要用 npx vitepress build（会吞掉报错）
```

### G3. 提交与推送

```powershell
git add -A
git commit -m "feat(i18n): <一句话说明>" -m "- 具体改动 1" -m "- 自证数字"
git push origin main
```

**部署触发条件（务必知道，避免误以为推了就上线）**：`deploy.yml` 第一道闸门只看
`site/.vitepress/theme/components/SiteAccessSwitch.vue`（`SITE_VERSION` 所在文件）是否被改动。

- 只提交译文/词表/工具 → **不会部署**（不占 Actions 分钟）。这是常态。
- 要发版：改 `SITE_VERSION`（该 .vue 文件里）**并同步**在 `site/.vitepress/theme/changelog.json` 加一条记录
  （项目规矩：两者必须一致）。
- 应急强制部署：`workflow_dispatch` 或提交信息带 `[deploy]`。

### G4. 让 CI 能抓到新登记的页

- `data/registry/pages.yaml` 必须推到 `main`；下一轮 CI 的 `fetch --mode all` 会补抓缺快照的页。
- 推送后不要期待「立刻」有新图：CI 是每周一轮（`cron: 30 15 * * 1`，UTC 周一 15:30），也可在 Actions 页手动 Run。

---

## 9. 坑清单（症状 → 原因 → 正确做法）

| # | 症状 | 原因 | 正确做法 |
|---|---|---|---|
| 1 | 写了 `*_translated.txt`，`fill` 后页面没变 | `fill` **只填空译**，目标 `zh` 已非空就跳过 | 已有译文要改 → `tools/sop/set_zh.py`（覆盖）或 `apply_ja_map.py --force` |
| 2 | 改了 `keyN` 页面还是旧译文 | 块级 `blk.zh` 覆盖节点级 | `block_sync.py <slug> --apply`，或直接 `set_zh.py` 写 `blkN#i` |
| 3 | `zh` 明明写了中文，页面仍显示日文 | `glossary/retain_ja.yaml` **命中即强制日文，无视 zh** | 审计：`_audit_retain_ja.py`（在 `tools/_dev/`）→ 删掉不该保留的条目（公式/台词/技能名）。**声优/画师/本名不要删** |
| 4 | 待译清单「不见了」 | `extract` 判定该页已无待译（被词表覆盖或已译完）会删旧清单 | 不是丢数据；用 `coverage.py` 看实际覆盖度 |
| 5 | 同一句要译好几遍 | 跨页/跨块去重：同文只列一次 | 译一次即可，`fill` 会按内容广播 |
| 6 | `fill` 报「段号越界」 | 人工译文把一段拆成了两行（段数 = ja 里 `\x01` 段数） | 按语义拼回（看段末标点是否续接），或让用户确认后重写该块 |
| 7 | 数值被改了 | 手写/机翻自作聪明补单位、改倍数 | 数值一律原样；`人数×5%` 不能写成「每有 1 人 +5%」 |
| 8 | 词表改了导致别的词被劈开 | 2 字假名条目做子串替换（`リア` 把 `レガリア` 劈成「レガ莉亚」） | 短条目只做整词匹配（代码已有最小长度 3 保护）；改词表后必须全站抽查 |
| 9 | 全站突然多出上百文件改动 | 跑了 `--fresh` / 全量 `i18n build`，把历史「块级长句塞进节点」的脏值扩散 | 严禁；只跑默认增量。已误跑 → `git checkout -- data/parsed/i18n` 回滚 |
| 10 | 本地解析「什么都没做」 | `parsed_sha256` 被写过（CI 侧或手动 `parse` 无 `--no-mark`） | 合并 manifest 时 `parsed_sha256` 只信本地；CI 永远不写 |
| 11 | CI 抓的页和本地对不上/冲突不断 | `data/manifest.json` 两侧都写 | `manifest merge`（§A2） |
| 12 | Wiki 源码示例块被翻成中文，示例失效 | `#region`/`#includex` 等插件指令块被翻译 | 这类块**必须原样日文**；`_fix_legacy_terms.py` 已内置跳过 |
| 13 | 某个块怎么改都不生效 | 块内含 `img`/`data-char` → 块级回退被跳过，节点级才是显示源 | 改用 `set_zh.py` 改该块的节点（`keyN`） |
| 14 | 误判「译文被改写」 | 按 `keyN` 编号比对，编号会平移 | 一律**按 ja 文本配对**（`_diag_zh_delta.py` 口径） |
| 15 | 批量改译名污染了别处 | 跨文件纯子串替换（`凪`→`娜姬` 把 `神凪繭` 也改了） | 改译名走 `names.yaml`/`characters.yaml` + 精确 key；先比对 HEAD 基线 |
| 16 | 中文短译被判「短词冒充整句」，整块回退日文 | 块级安全阀：`len(zh) < len(ja)*0.35` 且 ja≥30 字（已剥评论签名/[ID]） | 正常短评不会命中；若命中说明该块 `zh` 真的残缺 → 补全，别调阈值 |
| 17 | 页面出现「」与「“”」混用、多余空格 | 不同批次译文风格不一 | 正文统一用项目既有风格（「」、全角括号），校对阶段统一 |
| 18 | 直接 `grep`/正则改 JSON 后结构损坏 | JSON 是嵌套结构，正则替换会伤到 `ja` 或别的字段 | 只用 `set_zh.py` / `i18n fill` 等按 id 的工具 |
| 19 | 「声优名怎么是日文」 | 项目规则就是保留日文 | 不要「修」成中文 |
| 20 | 工作区巨大 diff（几万行） | 脚本写 JSON 用了 2 空格缩进，引擎是 1 空格 | 工具统一 `indent=1`（`tools/sop/*` 已如此） |

---

## 10. 命令速查

```powershell
# 同步与重建
git pull --rebase origin main
python -u -m escah_pipeline.cli manifest merge          # 仅在 manifest 冲突时
python -u -m escah_pipeline.cli local-sync              # 零网络重建（核心）
python -u -m escah_pipeline.cli local-sync --pages <slug...>

# 看本轮有什么
type data\upstream\latest.json          # counts / window / truncated / items
type data\recent_state.json             # candidates / changed / unregistered
python -u -m escah_pipeline.cli changelog show          # 更新履歴摘要
python -u -m escah_pipeline.cli changelog names         # 只列 new/update 页名

# 待译清单
Get-ChildItem tools\_todo_translate -Filter "*<date>*"
python -u tools/sop/r18_export.py --date <date>         # R18 导出（模型不读）
python -u tools/sop/r18_apply.py --date <date> [--apply]

# 翻译回填
python -u -m escah_pipeline.cli i18n fill --date <date> --pages <slug...>
python -u tools/sop/set_zh.py MULTI fix.json [--apply]  # 覆盖已有译文（二次精校用）
python -u tools/sop/block_sync.py <slug> [--apply]

# 验收
python -u tools/sop/coverage.py <slug> --list 10
python -u -X utf8 tools/_dev/_kana_residue.py <slug>
python -u -X utf8 tools/_dev/_page_dump.py <slug> --min 12

# 落地
python -u -X utf8 -m escah_pipeline.cli sync-site
cd site; node build.mjs build
git add -A; git commit -m "..."; git push origin main
```

---

## 11. 完成标准（逐项打勾才可交付）

- [ ] `git pull` 完成；若 manifest 冲突已按 §A2 合并并 `manifest status` 自检
- [ ] `local-sync` 退出码 0，`失败 0`，`缺图 0`
- [ ] 「旧译文失效」已核实为评论区/删段，不是译文被冲；已按 ja 配对给出空译净增（≤0 或逐页解释）
- [ ] 普通页待译清单全部译完 → `fill` 成功；`*_translated.txt` 已归档
- [ ] R18 页：已导出给人工、人工译文已 `r18_apply` + `fill`，模型全程未读内容
- [ ] 二次精校十二项检查过完；`set_zh` 覆盖的条目已 `block_sync`
- [ ] `coverage.py` 显示目标页残留率 ≤0.10%，残留只剩本名/声优/画师/注音
- [ ] 语义抽样 8～10 条、数值抽查 3 条、结构抽查 1 表 1 链接
- [ ] `sync-site` 完成；需要上线才动 `SITE_VERSION` + `changelog.json`
- [ ] 提交信息写明改动与自证数字；已推送（是否需要部署已判断清楚）

---

## 附录 A：`tools/sop/` 脚本一览（入库、可复用）

| 脚本 | 作用 | 关键点 |
|---|---|---|
| `r18_export.py` | 把 R18 页待译清单原样导出 | **不打印正文**，只报条数 |
| `r18_apply.py` | 合并人工译文并按卷归位，写出 `*_translated.txt` | **不打印正文**；写哪份文件都行 |
| `set_zh.py` | 按 id 覆盖 `zh`（单页 / MULTI） | `fill` 做不到的「改已有译文」走这里 |
| `block_sync.py` | 块级 `blk.zh` 按同名节点译文重拼 | 只对目标页跑，**不要全站无脑跑** |
| `coverage.py` | 覆盖度 + 渲染口径残留度量 | 只输出数字；`--list N` 列空译 id |

> 诊断类脚本（`_page_dump.py`、`_kana_residue.py`、`_audit_retain_ja.py`、`_diag_zh_delta.py` 等）在
> `tools/_dev/`，该目录**整体不入库**（本地历史工具）。若新环境缺失，按本文件 §5/§7 的口径自行实现等价脚本，
> 不要因为「脚本没了」就跳过验收。

## 附录 B：词表优先级与文件用途

| 文件 | 用途 | 渲染优先级 |
|---|---|---|
| `glossary/phrases_manual.yaml` | 人工整句表 | 最高（覆盖一切） |
| `glossary/retain_ja.yaml` | 保留日文名单（人名/声优/画师） | 高于 `zh`（命中即显示日文） |
| `glossary/names.yaml` | 专名（角色/装备/BOSS） | 高（独立名词与 zh 内嵌日文名替换） |
| `glossary/terms.yaml` | UI/属性/系统术语 | 中高 |
| `glossary/high_freq.yaml` | 高频短语/整词 | 中 |
| `glossary/phrases.yaml` | 生成式整句（渲染期兜底，仅在 `zh` 为空时用） | 低 |
| `glossary/r18.yaml` | 送翻预替换 + 渲染术语修复 | 仅 R18 链路 |
| `data/parsed/i18n/*.json` 的 `zh` | 译文真值 | 基础值 |

## 附录 C：与本项目强绑定的既定口径（不要重新发明）

- `レイド` → **Raid**（不用「突袭战/讨伐」）；`討伐` → Raid。
- `サポーター` → **支援者**（不是「支持者/支援型」）。
- `ダメージ` = **所受伤害**；`スタミナ` = **体力**；两者绝不可混译。
  `ダメージを回復` = 恢复所受的伤害；`スタミナを回復` = 恢复体力。
- `ヘイト` → 仇恨值；`スタミナゲージ` → 体力槽；`必殺ゲージ` → 必杀槽；`固有効果` → 固有效果。
- `優先1 / 優先2` → 优先1 / 优先2；`麺メンバー` → 面成员；`多麺編成` → 多面编成。
- `ハニージッポ` → 哈尼打火机；`ジッポ効果` → 打火机效果。
- `堕威大仏` → 堕威大佛；`BRAKE` → BREAK；`フラスト` 系列 BOSS → 「轨道/波涛/影像/科学 + 弗拉斯托」。
- 角色名长音+ル → 「尔」（フィール→菲尔），短音+ル → 「鲁」；`エスカ` 前缀 → **超昂**。
- 角色本名/声优/画师名保留日文；支援者详情的名字用日文本名。
