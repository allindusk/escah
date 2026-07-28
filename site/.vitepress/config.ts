import { defineConfig } from 'vitepress'
import sidebarJa from './generated/sidebar.ja.json'
import sidebarZh from './generated/sidebar.zh.json'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { existsSync, readFileSync } from 'node:fs'

// frag 片段目录（站点正文在此，而非 markdown 内），用于搜索索引。
// 注意：VitePress 会把 config.ts 打包到临时目录，import.meta.url 不可靠，
// 故以 process.cwd()（构建/开发时恒为 site 目录）为主，临时目录为辅。
const _fragCandidate = resolve(process.cwd(), '.vitepress', 'frag')
const FRAG_DIR = existsSync(_fragCandidate)
  ? _fragCandidate
  : resolve(dirname(fileURLToPath(import.meta.url)), 'frag')

// 角色/攻略页正文经 v-html 注入（markdown 仅含 <MirrorContent> 标签），
// VitePress 默认本地搜索只索引 markdown 编译后的 HTML，因此镜像正文不会被收录。
// 下面两个钩子让搜索索引直接读取 frag 的 html 字段，并对缺少锚点 <a> 的
// WIKI 原生 <h3> 标题也能正确分段。
function clearTags(s: string): string {
  return s.replace(/<[^>]*>/g, '')
}

// 把镜像/普通页面的渲染 HTML 拆成可检索片段（{ anchor, titles, text }）。
// WIKI 原生 <hN> 标题没有锚点 <a href="#...">，需自行生成唯一 anchor，
// 否则同一页面多个片段会得到相同的文档 id（MiniSearch 报 duplicate ID）。
function slugify(s: string): string {
  const t = s.trim().toLowerCase().replace(/\s+/g, '-')
  return t.replace(/[^\w぀-ヿ㐀-鿿-]/g, '') || 'sec'
}
function* splitFragSections(file: string, html: string): Generator<{ anchor: string; titles: string[]; text: string }> {
  const cleaned = html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
  const headingRe = /<h([1-6])\b[^>]*?>(.*?)<\/h\1>/gi
  const aTagRe = /<a\b[^>]*>[\s\S]*?<\/a>/gi
  const anchorRe = /<a\b[^>]*?href="#([^"]*)"[^>]*>/i
  type H = { index: number; level: number; title: string; anchor: string }
  const heads: H[] = []
  let m: RegExpExecArray | null
  while ((m = headingRe.exec(cleaned))) {
    const inner = m[2]
    const title = clearTags(inner.replace(aTagRe, '')).trim()
    const am = anchorRe.exec(inner)
    heads.push({ index: m.index, level: parseInt(m[1], 10), title, anchor: am ? am[1] : '' })
  }
  // 为缺少锚点的片段生成页面内唯一 anchor
  const used = new Set<string>()
  const uniq = (base: string, idx: number): string => {
    let cand = base || `sec-${idx}`
    let i = 1
    while (used.has(cand)) cand = `${base || 'sec'}-${i++}`
    used.add(cand)
    return cand
  }
  if (heads.length === 0) {
    const text = clearTags(cleaned).replace(/\s+/g, ' ').trim()
    if (text) yield { anchor: uniq('top', 0), titles: [], text }
  } else {
    const leading = clearTags(cleaned.slice(0, heads[0].index)).replace(/\s+/g, ' ').trim()
    if (leading) yield { anchor: uniq('top', 0), titles: [], text: leading }
    const parentTitles: string[] = []
    for (let i = 0; i < heads.length; i++) {
      const cur = heads[i]
      const end = i + 1 < heads.length ? heads[i + 1].index : cleaned.length
      const text = clearTags(cleaned.slice(cur.index, end)).replace(/\s+/g, ' ').trim()
      if (!text) continue
      parentTitles.length = Math.min(parentTitles.length, cur.level - 1)
      parentTitles[cur.level - 1] = cur.title
      const anchor = cur.anchor || uniq(slugify(cur.title), i + 1)
      yield { anchor, titles: parentTitles.filter(Boolean), text }
    }
  }
}

// 自定义渲染：镜像页直接返回对应 frag 的 html；其余页回退到默认 markdown 渲染。
async function renderMirror(_mdSrc: string, env: { relativePath: string }, md: { render: (s: string, e: any) => string }): Promise<string> {
  const rel = env.relativePath || ''
  const mm = /^(ja|zh)\/(.+)\.md$/.exec(rel)
  if (mm) {
    const locale = mm[1]
    const slug = mm[2]
    if (slug !== 'index' && slug !== 'updates') {
      const fragPath = resolve(FRAG_DIR, `${slug}.${locale}.json`)
      if (existsSync(fragPath)) {
        try {
          const frag = JSON.parse(readFileSync(fragPath, 'utf-8'))
          if (frag && typeof frag.html === 'string') return frag.html
        } catch {
          /* 回落默认渲染 */
        }
      }
    }
  }
  return md.render(_mdSrc, env)
}

// CJK 自定义分词：单字 + bigram，保证中日文检索召回
// ⚠️ tokenize 会被 VitePress 序列化后在浏览器端 eval 重建（deserializeFunctions），
// 闭包外的变量全部丢失 → 正则必须定义在函数体内，否则运行时 ReferenceError、搜索 0 结果。
function tokenize(text: string): string[] {
  const CJK_RE = /[\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/
  const tokens: string[] = []
  for (const word of text.split(/[\s\-–—/\\,.;:!?()[\]{}<>"'`~@#$%^&*+=|、。・，；：！？「」『』（）]+/)) {
    if (!word) continue
    if (CJK_RE.test(word)) {
      for (const ch of word) tokens.push(ch)
      for (let i = 0; i < word.length - 1; i++) tokens.push(word.slice(i, i + 2))
    } else {
      tokens.push(word.toLowerCase())
    }
  }
  return tokens
}

const navJa = [
  { text: 'ホーム', link: '/ja/' },
  { text: 'キャラクター', link: '/ja/characters.html' },
  { text: '更新履歴', link: '/ja/updates.html' },
  { text: '原WIKI站点', link: 'https://escalationheroines.wikiru.jp/' },
]
const navZh = [
  { text: '首页', link: '/zh/' },
  { text: '角色一览', link: '/zh/characters.html' },
  { text: '更新记录', link: '/zh/updates.html' },
  { text: '原WIKI站点', link: 'https://escalationheroines.wikiru.jp/' },
]

export default defineConfig({
  base: process.env.BASE || '/escah/',
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
        sidebar: sidebarJa,
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
        sidebar: sidebarZh,
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
    search: {
      provider: 'local',
      options: {
        // 镜像页正文在 frag 中，需自定义渲染/分段才能被收录（见文件顶部）。
        _render: renderMirror,
        locales: {
          zh: {
            translations: {
              button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
              modal: {
                noResultsText: '没有找到相关结果',
                resetButtonTitle: '清除搜索',
                footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' },
              },
            },
          },
        },
        miniSearch: { options: { tokenize }, _splitIntoSections: splitFragSections },
      },
    },
  },
})
