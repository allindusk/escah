/**
 * SEO 模块（Google / 百度通用）
 *
 * 站点原先只有一个全局 `<meta name="description">`、没有任何 canonical / hreflang /
 * Open Graph / 结构化数据、没有 sitemap.xml 与 robots.txt —— 对搜索引擎来说 2700+ 页
 * 全是"同标题同描述"的弱相关页面，且 ja/zh 两份译文互相竞争（重复内容）。
 *
 * 本模块在**构建期**（VitePress transformPageData / transformHead / sitemap 钩子）
 * 一次性补齐，因此线上产物里就是完整的静态标签，不依赖任何客户端 JS（百度不执行 JS）。
 *
 * 关键设计：
 * 1. **主站地址**默认 = 当前构建实际部署的地址（self-canonical）：
 *    `BASE=/escah/` → https://allindusk.github.io/escah，`BASE=/` → https://escah.pages.dev。
 *    两个镜像各自 canonical 到自己，任一镜像下线都不会把搜索引擎指向死链。
 *    若要收敛到单一主站（把另一个镜像作为重复内容放弃），构建时设 `SEO_ORIGIN`
 *    （如 `SEO_ORIGIN=https://escah.pages.dev`），第二个镜像的页面就会 canonical 到它。
 * 2. **每页独立 description**：直接从已生成的正文片段（.vitepress/frag/*.json）抽取
 *    首段可读正文，避免 2700 页共用一句站点简介被判定为低质。
 * 3. **hreflang**：ja ↔ zh 互指 + x-default，中英/中日双语站的标准做法。
 */
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

type Loc = 'ja' | 'zh'
type HeadTag = [string, Record<string, string>, string?]

// ---------------------------------------------------------------- 基础常量 ----
const BASE = process.env.BASE || '/escah/'
const CWD = process.cwd()
const FRAG_DIR = resolve(CWD, '.vitepress', 'frag')

const GH_ORIGIN = 'https://allindusk.github.io'
const CF_ORIGIN = 'https://escah.pages.dev'
const trimSlash = (s: string) => s.replace(/\/+$/, '')
const isGhBuild = BASE.startsWith('/escah')

const envOrigin = trimSlash(process.env.SEO_ORIGIN || '')
export const SITE_ORIGIN = envOrigin || (isGhBuild ? GH_ORIGIN : CF_ORIGIN)
const envPath = process.env.SEO_SITE_PATH
export const SITE_PATH = trimSlash(
  envPath === undefined ? (envOrigin ? '' : isGhBuild ? '/escah' : '') : envPath,
)
/** 站点根地址（含路径前缀），canonical / og:url / sitemap / robots 统一用它 */
export const SITE_ROOT = SITE_ORIGIN + SITE_PATH

export const SITE_NAME = '超昂大戦 Wiki'
export const SITE_TAGLINE = '超昂大戦エスカレーションヒロインズ（超昂大战）攻略 Wiki・日中バイリンガル'

const HTML_LANG: Record<Loc, string> = { ja: 'ja-JP', zh: 'zh-CN' }
const OG_LOCALE: Record<Loc, string> = { ja: 'ja_JP', zh: 'zh_CN' }
const HOME_LABEL: Record<Loc, string> = { ja: 'ホーム', zh: '首页' }
const FALLBACK_DESC: Record<Loc, string> = {
  ja: '超昂大戦エスカレーションヒロインズ（エスカヒロ）の攻略 Wiki。キャラクター・必殺技・覚醒・装備・レイド・イベントなど日中バイリンガルで収録。',
  zh: '超昂大战 Escalation Heroines（エスカヒロ）攻略 Wiki 中文镜像：角色一览、必杀技、觉醒强化、装备、Raid、活动等中日双语对照资料。',
}
// 站点图片 2026-10-18 起统一为 WebP（下载即转码，见 pipeline/escah_pipeline/imgx.py）。
// favicon / apple-touch-icon / og:image 都用同一张 webp：Chrome 32+/FF 65+/Safari 14+
// 均支持 webp 图标；若将来要照顾老客户端分享卡片，可另存一张 png 换这里。
const LOGO_PATH = `${BASE}img/63de516dca671d22.webp`
const OG_IMAGE = `${SITE_ROOT}/img/63de516dca671d22.webp`

// -------------------------------------------------------------- 页面路径解析 ----
type PageInfo = { loc: Loc | null; slug: string; file: string }

/** `zh/characters/花のチルカ.md` → { loc:'zh', slug:'characters/花のチルカ', file:'characters/花のチルカ.html' } */
function resolvePage(relativePath: string | undefined): PageInfo {
  const rel = (relativePath || '').replace(/\\/g, '/')
  const m = /^(ja|zh)\/(.+)\.md$/.exec(rel)
  if (!m) return { loc: null, slug: '', file: '' }
  const loc = m[1] as Loc
  const slug = m[2].replace(/\/?index$/, '')
  return { loc, slug, file: slug ? `${slug}.html` : '' }
}

function pageUrl(loc: Loc, file: string): string {
  return `${SITE_ROOT}/${loc}/${file}`
}

/** 站点根跳转页（/）的 canonical 指向中文首页 */
export const HOME_ZH = `${SITE_ROOT}/zh/`
export const HOME_JA = `${SITE_ROOT}/ja/`

function mdExists(loc: Loc, file: string): boolean {
  const p = resolve(CWD, loc, file ? file.replace(/\.html$/, '.md') : 'index.md')
  return existsSync(p)
}

// ------------------------------------------------------------ 正文文本抽取 ----
const fragCache = new Map<string, string>()

function fragHtml(slug: string, loc: Loc): string {
  if (!slug) return ''
  const key = `${slug}.${loc}`
  const hit = fragCache.get(key)
  if (hit !== undefined) return hit
  let html = ''
  const p = resolve(FRAG_DIR, `${slug}.${loc}.json`)
  if (existsSync(p)) {
    try {
      const j = JSON.parse(readFileSync(p, 'utf-8'))
      html = typeof j?.html === 'string' ? j.html : ''
    } catch {
      html = ''
    }
  }
  fragCache.set(key, html)
  return html
}

const ENTITIES: Record<string, string> = {
  '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
  '&#39;': "'", '&apos;': "'", '&middot;': '·', '&times;': '×',
}

function htmlToText(html: string): string {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&[a-z#0-9]+;/gi, (e) => ENTITIES[e.toLowerCase()] ?? ' ')
    .replace(/[\s\u3000]+/g, ' ')
    .trim()
}

/** 导航噪声段落（"相关页面：A | B | C" 之类）不适合做 description */
const NOISE_HEAD = /^(相关页面|関連ページ|目次|コンテンツ|スポンサー|お知らせ一覧|このページの|編集者|最終更新|コメント|评论|留言|索引|インデックス|※)/
const HAS_KANA = /[\u3040-\u309f\u30a0-\u30ff]/
const HAS_CJK = /[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]/

/** 收尾清理：去掉句末残留的【链接标签】、空括号与多余空白 */
function tidy(t: string): string {
  return t
    .replace(/(?:\s*【[^】]{1,24}】)+\s*$/g, '')
    .replace(/[\s\u3000]+/g, ' ')
    .replace(/[\s、,，]+$/, '')
    .trim()
}

function cutText(t: string, max: number): string {
  const text = tidy(t)
  if (text.length <= max) return text
  const head = text.slice(0, max)
  const stop = Math.max(
    head.lastIndexOf('。'), head.lastIndexOf('．'), head.lastIndexOf('.'),
    head.lastIndexOf('！'), head.lastIndexOf('？'),
  )
  return stop > max * 0.5 ? head.slice(0, stop + 1) : head.trimEnd() + '…'
}

/**
 * 从正文片段里挑一段"像人话"的文本做 description：
 * 先找带句末标点的段落，其次找足够长的段落，最后回退到站点简介。
 * 纯表格页（角色一览等）没有散文，直接走回退，避免把链接列表当描述。
 */
function pickExcerpt(html: string, loc: Loc): string {
  const max = loc === 'zh' ? 110 : 110
  const blocks = html.split(/<\/(?:p|div|li|td|th|h[1-6]|dt|dd|section|tr|table)>/i)
  let best = ''
  for (const raw of blocks) {
    const t = htmlToText(raw)
    if (t.length < 28 || NOISE_HEAD.test(t)) continue
    // 以中日文为主、且不是"一列链接名"的块
    const cjk = (t.match(/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]/g) || []).length
    if (cjk < 14) continue
    if (t.split('|').length > 3 && !/[。！？]/.test(t)) continue
    if (/[。！？]/.test(t)) return cutText(t, max)
    if (!best) best = t
  }
  return best ? cutText(best, max) : ''
}

/**
 * 摘要安全化：**必须去掉半角双引号**。
 * VitePress 把 pageData.description 直接拼进 `<meta name="description" content="…">`（不做
 * HTML 转义），正文里只要有一个 `"`（角色台词很常见）就会把属性截断，搜索引擎读到的摘要
 * 只剩引号前那几个字 —— 实测「魔女ピカ」整段简介就是这样丢掉的。
 */
function sanitizeDesc(s: string): string {
  return s
    .replace(/"([^"]{1,160})"/g, '「$1」')
    .replace(/"/g, '”')
    .replace(/[<>]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

/** 每页独立的 meta description（无正文时回退到「页面名 + 站点简介」） */
export function pageDescription(pageData: any): string {
  const info = resolvePage(pageData?.relativePath)
  const title = String(pageData?.title || SITE_NAME).trim()
  if (!info.loc) return FALLBACK_DESC.zh
  // 先清理再判长度：部分角色页的正文段落只剩「【角色名】」标签，清理后为空串
  const body = pickExcerpt(fragHtml(info.slug, info.loc), info.loc)
  const clean = body ? cutText(body, 120) : ''
  if (clean.length >= 20) {
    // 页面名前置：让「角色名 / 装备名 / 关卡名」出现在描述最前面（百度摘要按字符截断，
    // 主题词越靠前越容易被判定相关），同时避免与标题在摘要里重复出现。
    if (!title || clean.includes(title)) return sanitizeDesc(clean)
    const room = Math.max(50, 120 - title.length - 1)
    return sanitizeDesc(`${title}｜${cutText(clean, room)}`)
  }
  const brand = FALLBACK_DESC[info.loc]
  if (!title || brand.startsWith(title)) return sanitizeDesc(brand)
  return sanitizeDesc(`${title}｜${cutText(brand, Math.max(60, 120 - title.length - 1))}`)
}

// --------------------------------------------------------------- 全局 head ----
export function seoHead(): HeadTag[] {
  const tags: HeadTag[] = [
    ['link', { rel: 'icon', type: 'image/webp', href: LOGO_PATH }],
    ['link', { rel: 'apple-touch-icon', href: LOGO_PATH }],
    // 允许大图预览（Google 图片/发现流），并声明 PC+移动自适应（百度移动适配）
    ['meta', { name: 'robots', content: 'index,follow,max-image-preview:large,max-snippet:-1' }],
    ['meta', { name: 'applicable-device', content: 'pc,mobile' }],
    ['meta', { name: 'format-detection', content: 'telephone=no' }],
    ['meta', { name: 'theme-color', content: '#e91e63' }],
    ['meta', { property: 'og:site_name', content: SITE_NAME }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:image', content: OG_IMAGE }],
    ['meta', { name: 'twitter:card', content: 'summary' }],
  ]
  // 站长平台校验（在 CI 里配 repository variables 即可生效，无需改代码）
  const google = process.env.GOOGLE_SITE_VERIFICATION
  if (google) tags.push(['meta', { name: 'google-site-verification', content: google }])
  const baidu = process.env.BAIDU_SITE_VERIFICATION
  if (baidu) tags.push(['meta', { name: 'baidu-site-verification', content: baidu }])
  return tags
}

// ------------------------------------------------- transformPageData / Head ----
/** 把每页独立的 description 写进 pageData，VitePress 会自动输出 <meta name="description"> */
export function seoTransformPageData(pageData: any): any {
  if (pageData?.frontmatter?.description) return
  const description = pageDescription(pageData)
  if (!description) return
  return { description }
}

function jsonLd(info: PageInfo, title: string, description: string, canonical: string, pageData: any): string {
  const lang = info.loc ? HTML_LANG[info.loc] : 'zh-CN'
  const home = info.loc === 'ja' ? HOME_JA : HOME_ZH
  const synced = String(pageData?.frontmatter?.meta?.synced || '').slice(0, 10)
  const graph: Record<string, any>[] = [
    {
      '@type': 'WebSite',
      '@id': `${SITE_ROOT}/#website`,
      url: `${SITE_ROOT}/`,
      name: SITE_NAME,
      alternateName: ['超昂大戦 Wiki', '超昂大战攻略Wiki', 'エスカヒロ 攻略'],
      description: SITE_TAGLINE,
      inLanguage: ['ja-JP', 'zh-CN'],
    },
    {
      '@type': info.file ? 'Article' : 'WebPage',
      '@id': `${canonical}#webpage`,
      url: canonical,
      name: title,
      headline: title,
      description,
      inLanguage: lang,
      isPartOf: { '@id': `${SITE_ROOT}/#website` },
      ...(synced && /^\d{4}-\d{2}-\d{2}$/.test(synced) ? { dateModified: synced, datePublished: synced } : {}),
      publisher: { '@type': 'Organization', name: SITE_NAME, url: `${SITE_ROOT}/` },
    },
  ]
  if (info.file) {
    graph.push({
      '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: HOME_LABEL[info.loc as Loc], item: home },
        { '@type': 'ListItem', position: 2, name: title, item: canonical },
      ],
    })
  }
  return JSON.stringify({ '@context': 'https://schema.org', '@graph': graph }).replace(/</g, '\\u003c')
}

export function seoTransformHead(ctx: any): HeadTag[] {
  const pageData = ctx?.pageData || {}
  const info = resolvePage(pageData.relativePath)
  const title = String(ctx?.title || pageData.title || SITE_NAME)
  const description = String(ctx?.description || pageDescription(pageData))
  const tags: HeadTag[] = []

  // 根跳转页（/）：目标是即时跳到中文首页，不参与索引，canonical 指向 /zh/
  if (!info.loc) {
    tags.push(['link', { rel: 'canonical', href: HOME_ZH }])
    tags.push(['meta', { name: 'robots', content: 'noindex,follow' }])
    tags.push(['meta', { property: 'og:title', content: title }])
    tags.push(['meta', { property: 'og:description', content: description }])
    tags.push(['meta', { property: 'og:url', content: HOME_ZH }])
    return tags
  }

  const canonical = pageUrl(info.loc, info.file)
  tags.push(['link', { rel: 'canonical', href: canonical }])

  // hreflang：ja ↔ zh 互为 alternate（对侧页面必须真实存在，否则不发）
  const alt: { loc: Loc; url: string }[] = []
  for (const l of ['ja', 'zh'] as Loc[]) {
    if (mdExists(l, info.file)) alt.push({ loc: l, url: pageUrl(l, info.file) })
  }
  for (const a of alt) {
    tags.push(['link', { rel: 'alternate', hreflang: HTML_LANG[a.loc], href: a.url }])
  }
  const jaAlt = alt.find((a) => a.loc === 'ja')
  if (jaAlt) tags.push(['link', { rel: 'alternate', hreflang: 'x-default', href: jaAlt.url }])

  tags.push(['meta', { property: 'og:title', content: title }])
  tags.push(['meta', { property: 'og:description', content: description }])
  tags.push(['meta', { property: 'og:url', content: canonical }])
  tags.push(['meta', { property: 'og:locale', content: OG_LOCALE[info.loc] }])
  for (const a of alt) {
    if (a.loc !== info.loc) tags.push(['meta', { property: 'og:locale:alternate', content: OG_LOCALE[a.loc] }])
  }
  tags.push(['meta', { name: 'twitter:title', content: title }])
  tags.push(['meta', { name: 'twitter:description', content: description }])

  tags.push(['script', { type: 'application/ld+json' }, jsonLd(info, title, description, canonical, pageData)])
  return tags
}

// sitemap.xml 由 build.mjs 在构建结束后按 dist 里实际存在的页面生成（见该文件
// writeSitemap()）。这里不用 VitePress 内置 sitemap 的原因：内置实现对**每个页**都
// 跑一次 `git log -1` 取 lastmod（2700+ 次子进程），本机构建被拖到数分钟且极易超时；
// 而 lastmod 取到的只是 CI checkout 时间，对爬虫毫无意义。
