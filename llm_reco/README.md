# llm_reco — 大模型推荐角色（知识库与推理工作区）

本文件夹用于支撑「大模型推荐角色」页面（`site/zh/llm-recommend.md` + `site/ja/llm-recommend.md`）。
页面**默认隐藏**（不进 registry / 侧边栏），仅可通过直接输入 URL 访问，待推荐质量稳定后再正式发布。

## 目标
由大模型阅读全部角色详情页（属性 / 必杀技 / 固有效果）与系统·装备·道具类页面
（养成、战斗机制、装备、重要副本），给出**带理由的角色推荐**。

## 文件夹结构
- `README.md`：本说明。
- `extract_chars.py`：从 `data/parsed/characters/*.json` 抽取全部角色关键数据 → `char_data.json`。
- `char_data.json`：所有角色的结构化数据（稀有度 / 元素 / 攻防魔抗 / 必杀技 / 固有效果 / 获取方式）。
- `game-mechanics.md`：阅读系统·装备·道具页后整理的游戏机制理解（战斗、养成、装备、副本）。
- `reco-draft.md`：**推荐推理工作稿**（按角色/定位分组，每条含推荐理由）；用户在此纠正，我据此修正。
- `reco-method.md`：推荐评价维度与权重（用户可一并纠正“该用什么标准推荐”）。

## 协作方式（与用户）
1. 我基于 `char_data.json` + `game-mechanics.md` 在 `reco-draft.md` 写推荐与理由。
2. 用户阅读后纠正（例如“XX 不该推荐，因为…”“标准里应更看重…”）→ 在 `reco-draft.md` / `reco-method.md` 批注或告诉我。
3. 我修改推理与页面内容，重新生成 `site/*/llm-recommend.md`。

## 重抽取
角色数据随 wiki 更新变化，重跑：`python llm_reco/extract_chars.py`
