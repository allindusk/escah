import { defineConfig } from 'vitepress'
import sidebarJa from './generated/sidebar.ja.json'
import sidebarZh from './generated/sidebar.zh.json'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { existsSync, readFileSync } from 'node:fs'

// frag 片段目录（站点正文在此，而非 markdown 内）。
// 注意：VitePress 会把 config.ts 打包到临时目录，import.meta.url 不可靠，
// 故以 process.cwd()（构建/开发时恒为 site 目录）为主，临时目录为辅。
// [搜索功能已禁用] FRAG_DIR 原供搜索索引读取 frag 正文，现已停用，保留备用。
const _fragCandidate = resolve(process.cwd(), '.vitepress', 'frag')
const FRAG_DIR = existsSync(_fragCandidate)
  ? _fragCandidate
  : resolve(dirname(fileURLToPath(import.meta.url)), 'frag')

// [搜索功能已禁用] 以下索引构建逻辑整体停用（搜索已取消）
// function clearTags(s: string): string {
//   return s.replace(/<[^>]*>/g, '')
// }

// 把镜像/普通页面的渲染 HTML 拆成可检索片段（{ anchor, titles, text }）。
// WIKI 原生 <hN> 标题没有锚点 <a href="#...">，需自行生成唯一 anchor，
// 否则同一页面多个片段会得到相同的文档 id（MiniSearch 报 duplicate ID）。
// function slugify(s: string): string {
//   const t = s.trim().toLowerCase().replace(/\s+/g, '-')
//   return t.replace(/[^\w぀-ヿ㐀-鿿-]/g, '') || 'sec'
// }
// [搜索已禁用] function* splitFragSections(...) 停用：
// function* splitFragSections(file: string, html: string): Generator<{ anchor: string; titles: string[]; text: string }> {
//   const cleaned = html
//     .replace(/<script[\s\S]*?<\/script>/gi, '')
//     .replace(/<style[\s\S]*?<\/style>/gi, '')
//   let pageTitle = ''
//   const siH1 = /<div class="search-index"[^>]*>\s*<h1[^>]*>([\s\S]*?)<\/h1>/i.exec(cleaned)
//   if (siH1) pageTitle = clearTags(siH1[1]).trim()
//   if (!pageTitle) {
//     const anyH1 = /<h1[^>]*>([\s\S]*?)<\/h1>/i.exec(cleaned)
//     if (anyH1) pageTitle = clearTags(anyH1[1]).trim()
//   }
//   if (!pageTitle) {
//     const fm = /\/(?:ja|zh)\/([^/]+)\.html$/.exec(file)
//     pageTitle = fm ? fm[1] : file
//   }
//   const withPage = (t: string[]): string[] => {
//     const arr = t.slice()
//     if (pageTitle && arr[arr.length - 1] !== pageTitle) arr.push(pageTitle)
//     return arr
//   }
//   const headingRe = /<h([1-6])\b[^>]*?>(.*?)<\/h\1>/gi
//   const aTagRe = /<a\b[^>]*>[\s\S]*?<\/a>/gi
//   const anchorRe = /<a\b[^>]*?href="#([^"]*)"[^>]*>/i
//   type H = { index: number; level: number; title: string; anchor: string }
//   const heads: H[] = []
//   let m: RegExpExecArray | null
//   while ((m = headingRe.exec(cleaned))) {
//     const inner = m[2]
//     const title = clearTags(inner.replace(aTagRe, '')).trim()
//     const am = anchorRe.exec(inner)
//     heads.push({ index: m.index, level: parseInt(m[1], 10), title, anchor: am ? am[1] : '' })
//   }
//   const used = new Set<string>()
//   const uniq = (base: string, idx: number): string => {
//     let cand = base || `sec-${idx}`
//     let i = 1
//     while (used.has(cand)) cand = `${base || 'sec'}-${i++}`
//     used.add(cand)
//     return cand
//   }
//   if (heads.length === 0) {
//     const text = clearTags(cleaned).replace(/\s+/g, ' ').trim()
//     if (text) yield { anchor: uniq('top', 0), titles: withPage([]), text }
//   } else {
//     const leading = clearTags(cleaned.slice(0, heads[0].index)).replace(/\s+/g, ' ').trim()
//     if (leading) yield { anchor: uniq('top', 0), titles: withPage([]), text: leading }
//     const parentTitles: string[] = []
//     for (let i = 0; i < heads.length; i++) {
//       const cur = heads[i]
//       const end = i + 1 < heads.length ? heads[i + 1].index : cleaned.length
//       const text = clearTags(cleaned.slice(cur.index, end)).replace(/\s+/g, ' ').trim()
//       if (!text) continue
//       parentTitles.length = Math.min(parentTitles.length, cur.level - 1)
//       parentTitles[cur.level - 1] = cur.title
//       const anchor = cur.anchor || uniq(slugify(cur.title), i + 1)
//       yield { anchor, titles: withPage(parentTitles.filter(Boolean)), text }
//     }
//   }
// }

// [搜索已禁用] 镜像页自定义渲染钩子（原供搜索索引收录 frag 正文）已停用：
// // 自定义渲染：镜像页直接返回对应 frag 的 html；其余页回退到默认 markdown 渲染。
// const SEARCH_INDEX_RE = /<div class="search-index"[^>]*>([\s\S]*?)<\/div>/i
// async function renderMirror(_mdSrc: string, env: { relativePath: string }, md: { render: (s: string, e: any) => string }): Promise<string> {
//   const rel = env.relativePath || ''
//   const mm = /^(ja|zh)\/(.+)\.md$/.exec(rel)
//   if (mm) {
//     const locale = mm[1]
//     const slug = mm[2]
//     if (slug !== 'index' && slug !== 'updates') {
//       const fragPath = resolve(FRAG_DIR, `${slug}.${locale}.json`)
//       if (existsSync(fragPath)) {
//         try {
//           const frag = JSON.parse(readFileSync(fragPath, 'utf-8'))
//           if (frag && typeof frag.html === 'string') {
//             let extra = ''
//             try {
//               const si = SEARCH_INDEX_RE.exec(_mdSrc)
//               if (si) extra = `<div class="search-index" style="display:none" aria-hidden="true">${si[1]}</div>`
//             } catch {
//               // 无 search-index 块则跳过
//             }
//             return frag.html + extra
//           }
//         } catch {
//           // 回落默认渲染
//         }
//       }
//     }
//   }
//   return md.render(_mdSrc, env)
// }

// [搜索已禁用] CJK 自定义分词函数 tokenize 已停用：
// // CJK 自定义分词：单字 + bigram，保证中日文检索召回
// function tokenize(text: string): string[] {
//   const CJK_RE = /[\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/
//   const tokens: string[] = []
//   for (const word of text.split(/[\s\-–—/\\,.;:!?()[\]{}<>"'`~@#$%^&*+=|、。・，；：！？「」『』（）]+/)) {
//     if (!word) continue
//     if (CJK_RE.test(word)) {
//       for (const ch of word) tokens.push(ch)
//       for (let i = 0; i < word.length - 1; i++) tokens.push(word.slice(i, i + 2))
//     } else {
//       tokens.push(word.toLowerCase())
//     }
//   }
//   return tokens
// }

// combined 节点（如 "SSR | SR | R"）的 text 内含裸 <a href="/zh/...">，
// VitePress 只给 "link" 字段补 base、不会处理 text 内的 HTML 链接，
// 在 /escah/ base 下会变成 /zh/...（缺前缀）→ 404。这里统一用 withBase 补全。
function applySidebarBase(sidebar: any[]): any[] {
  const base = process.env.BASE || '/escah/'
  const fixText = (s: string): string =>
    typeof s === 'string'
      ? s.replace(/<a\s+([^>]*?)href="(\/[^"]*)"([^>]*)>/gi,
          (_m, pre: string, href: string, post: string) =>
            `<a ${pre}href="${base}${href.replace(/^\//, '')}"${post}>`)
      : s
  const walk = (nodes: any[]): any[] =>
    (nodes || []).map((n) => {
      const copy = { ...n }
      if (typeof copy.text === 'string') copy.text = fixText(copy.text)
      if (Array.isArray(copy.items)) copy.items = walk(copy.items)
      return copy
    })
  return walk(sidebar)
}

const sidebarJaFixed = applySidebarBase(sidebarJa as any[])
const sidebarZhFixed = applySidebarBase(sidebarZh as any[])

const navJa = [
  { text: 'ホーム', link: '/ja/' },
  { text: '公式ヘルプ', link: '/ja/official-help.html' },
  { text: 'キャラクター', link: '/ja/characters.html' },
  { text: '更新履歴', link: '/ja/updates.html' },
  { text: '原WIKI站点', link: 'https://escalationheroines.wikiru.jp/' },
]
const navZh = [
  { text: '首页', link: '/zh/' },
  { text: '官方帮助中心', link: '/zh/official-help.html' },
  { text: '角色一览', link: '/zh/characters.html' },
  { text: '更新记录', link: '/zh/updates.html' },
  { text: '原WIKI站点', link: 'https://escalationheroines.wikiru.jp/' },
]

export default defineConfig({
  base: process.env.BASE || '/escah/',
  // dev 模式 vite 的 optimizeDeps 自动扫描在本机环境会陷入预构建卡死（进程常驻、内存飙到 800MB+ 且不监听端口）。
  // 关闭启动期自动扫描入口，改为请求时按需优化，避免 dev server 起不来。
  vite: {
    optimizeDeps: { entries: [] },
  },
  title: '超昂大戦 Wiki',
  description: '超昂大戦エスカレーションヒロインズ攻略 Wiki 中日双语镜像站',
  ignoreDeadLinks: true,
  locales: {
    root: {
      label: '日本語',
      lang: 'ja-JP',
      link: '/ja/',
      themeConfig: {
        nav: navJa,
        sidebar: sidebarJaFixed,
        // 默认 outline 关闭：改用自定义树状目录 DocOutline（见 Layout.vue #aside-top）
        outline: false,
        docFooter: { prev: '前のページ', next: '次のページ' },
        lastUpdated: { text: '最終更新' },
        returnToTopLabel: 'トップへ戻る',
        darkModeSwitchLabel: 'ダークモード',
      },
    },
    zh: {
      label: '简体中文',
      lang: 'zh-CN',
      link: '/zh/',
      themeConfig: {
        nav: navZh,
        sidebar: sidebarZhFixed,
        // 默认 outline 关闭：改用自定义树状目录 DocOutline（见 Layout.vue #aside-top）
        outline: false,
        docFooter: { prev: '上一页', next: '下一页' },
        lastUpdated: { text: '最后更新' },
        returnToTopLabel: '返回顶部',
        darkModeSwitchLabel: '深色模式',
      },
    },
  },
  themeConfig: {
    // 顶部标题左侧 logo：エスカレイヤー头像（public/img，withBase 自动处理双部署 base）
    logo: '/img/63de516dca671d22.png',
    // 导航栏最右侧 GitHub 图标（官方 mark），点击打开项目仓库
    socialLinks: [
      { icon: 'github', link: 'https://github.com/allindusk/escah' },
    ],
    // 搜索功能已禁用（本地搜索索引构建/分词开销大，且 dev server 启动卡死）
    // search: {
    //   provider: 'local',
    //   options: {
    //     // 镜像页正文在 frag 中，需自定义渲染/分段才能被收录（见文件顶部）。
    //     _render: renderMirror,
    //     locales: {
    //       zh: {
    //         translations: {
    //           button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
    //           modal: {
    //             noResultsText: '没有找到相关结果',
    //             resetButtonTitle: '清除搜索',
    //             footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' },
    //           },
    //         },
    //       },
    //     },
    //     miniSearch: { options: { tokenize, storeFields: ['title', 'titles', 'text'] }, _splitIntoSections: splitFragSections },
    //   },
    // },
  },
})
