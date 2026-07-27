---
name: 修复图片路径并由助手直接翻译
overview: 两项修复：1) 站点图片因 base 路径缺失全部 404，在 MirrorContent.vue 用 withBase 重写 /img/ 为 /escah/img/；2) 翻译此前是 mock 占位（【译】+日文），改由助手直接产出中文，分段分批覆盖 data/parsed/zh 下的片段并重建。
todos:
  - id: fix-image-base
    content: 修改 MirrorContent.vue,将片段内 src="/img/ 重写为 BASE_URL 感知路径
    status: completed
  - id: add-detached-build
    content: 新增 site/build.mjs,以 detached 方式重建并确认图片在 /escah/ 下正常加载
    status: completed
    dependencies:
      - fix-image-base
  - id: translate-first-batch
    content: 首批发译重点页(getting-started/faq/tips/tips-tricks/slang),写 zh 片段并 sync-site+构建验证
    status: completed
    dependencies:
      - add-detached-build
  - id: translate-remaining
    content: 分批续译剩余镜像页与大页分块,每批 sync-site+构建验证
    status: pending
    dependencies:
      - translate-first-batch
  - id: translate-characters
    content: 补译角色详情 JSON 的 zh 字段(data/parsed/characters/*.json),逐批覆盖 mock
    status: pending
    dependencies:
      - translate-remaining
---

## 用户需求

1. 修复本地预览时所有图片 404 的问题(正文图片路径缺少站点 base 前缀 `/escah/`)。
2. 真正完成中日翻译:此前 `data/parsed/zh` 片段是 mock 占位(`【译】`+日文),未实际翻译;用户要求由助手(大模型)直接翻译,内容量太大时分批/分段推进。
3. 本机已装好真实 Node.js LTS(≥18),可以正常构建与预览。

## 产品概述

超昂大战 Wiki 中日双语镜像站,基于 Python 抓取解析流水线 + VitePress 双语静态站(`base='/escah/'`),部署 GitHub Pages。当前两个阻塞:正文图片因 base 缺失无法显示;中文内容缺失(仅有 mock 占位)。

## 核心功能

- 正文图片在 `/escah/` base 下正确加载(浏览器请求 `localhost:4173/escah/img/...` 而非 `.../img/...`)。
- 由助手将日文镜像页逐批翻译为简体中文,覆盖 `data/parsed/zh` 片段并重新生成站点;后续批次补译角色详情 JSON 的 `zh` 字段。

## 技术栈

- 站点:VitePress 1.6.3 + Vue 3 + TypeScript(static MPA,`base='/escah/'`)
- 流水线:Python(`escah_pipeline`),层间以文件为契约
- 构建/预览:真实 Node.js(已装),需以 detached 方式运行以规避本机 harness 将 vitepress 误判为 watch 服务而 `kill(0)` 强杀

## 实现方案

### 一、图片路径修复(阻断性)

根因:`parser_puki.py:106` 将图片写成 `src="/img/<hash>.<ext>"`(绝对路径、无 base),而站点 `base='/escah/'`(`config.ts:37`)。`MirrorContent.vue` 用 `v-html` 注入该字符串,`v-html` 内的 URL 不会被 Vite 自动加 base,浏览器请求 `localhost:4173/img/...`(缺 `/escah/`)→ 404。角色图标无此问题(`CharList.vue:150` 用 `withBase(c.icon)`,`c.icon="img/<hash>"` 相对路径,`withBase` 自动补 base)。

策略:在 `MirrorContent.vue` 渲染前,用 `import.meta.env.BASE_URL` 对片段内 `src="/img/` 做字符串重写。该修复**无需重新 parse/translate**,改组件即生效。

关键决策:

- 选组件层重写而非 pipeline 层(parser/sitegen):避免重跑 `parse`(重新生成 ja 片段)与 `translate`(巨大开销),改动面最小、回归风险最低。
- 用 `import.meta.env.BASE_URL` 而非硬编码 `/escah/`:与 VitePress 的 base 解耦,dev/preview/prod 一致,后续改 base 不影响。

### 二、翻译(助手直译,分批)

数据流:`data/parsed/ja/<slug>.html`(日文,HTML 结构)→ `data/parsed/zh/<slug>.html`(译文)。`sitegen._read_fragment`(sitegen.py:145-157)读取 zh 生成 `site/.vitepress/frag/<slug>.json` 与 `site/<locale>/<slug>.md`。

策略:由助手直接翻译——读取 ja 片段,保留全部 HTML 标签/属性/结构,仅翻译标签内文本(术语参照 `glossary/glossary.yaml`,人名/技能名保留日文原文,数字/URL/英文缩写不变),写入 `data/parsed/zh/<slug>.html` 覆盖 mock 占位。每批完成后 `python -m escah_pipeline.cli sync-site` 重生成 frag/md,再 detached 构建并预览验证。大页(>200KB,如 skills/unique-effects/characters)在单页内再按块分译。

性能/可靠性:翻译为人工可控的批量写文件,无运行时开销;`sync-site` 仅重写受影响页的 frag,增量成本低;构建用 detached 脚本避免 harness 误杀产生半截产物。

## 实现注意

- 仅改 `MirrorContent.vue` 渲染逻辑,不要改动 `parser_puki.py` 的图片写入,避免被迫重跑整条 pipeline。
- 翻译写入 `data/parsed/zh/` 时严格保留原 HTML 结构,否则 `sitegen` 生成的 frag 会破坏 `v-html` 渲染。
- 构建务必 detached(Start-Process 绝对路径调用 node + vitepress bin,或独立 node 脚本 `unref()`),否则被 harness `kill(0)` 中断。
- 每个批次后验证:预览中抽查该页中文与图片是否正常,再继续下一批。

## 架构与目录

仅涉及少量文件修改/新增,符合现有分层(流水线数据 → VitePress 站点):

```
site/.vitepress/theme/components/MirrorContent.vue  # [MODIFY] 渲染前将 src="/img/ 重写为 BASE_URL 感知路径(base 无关)
site/build.mjs                                       # [NEW] 编程式调用 vitepress build 并写 .nojekyll,供 detached 运行规避 harness 误杀
data/parsed/zh/<slug>.html                           # [MODIFY/NEW] 助手逐批写入的真实中文片段(覆盖 mock 占位)
data/parsed/characters/*.json                        # [MODIFY] 后续批次补译角色详情的 zh 字段(当前为 mock)
```

## 关键代码结构(MirrorContent.vue 修改示意)

```ts
<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ html: string }>()
const BASE = import.meta.env.BASE_URL
const rendered = computed(() =>
  (props.html || '').replace(/src="\/img\//g, `src="${BASE}img/`)
)
</script>
<template>
  <div class="mirror-content" v-html="rendered" />
</template>
```