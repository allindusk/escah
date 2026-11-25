/**
 * 语言切换后的滚动位置恢复（2026-11-24）。
 *
 * 中文页 /ja 页是**同一份 frag 的两个译文**，结构一一对应（章节顺序、标题层级都一样），
 * 所以可以「按第几个标题 + 该标题下的偏移」把位置搬到另一种语言的同一页上：
 *   1. 点击跨语言链接时，记下「当前视口顶部上方最近的那个标题是第几个、距它多远」；
 *   2. 新页渲染完成后（正文是 v-html，落下得比较晚，所以要重试等待），
 *      找到同序号的标题，滚到「标题位置 + 原偏移」；
 *   3. 标题数量对不上（译文缺章节）时退化为「整页进度比例」，至少不会跳到页首。
 *
 * 只在「同 slug 换语言」时生效：普通的站内跳转、带 #hash 的跳转都不动，避免和浏览器/
 * VitePress 自己的滚动行为打架。
 */
const KEY = 'escah:lang-scroll'
const BASE = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '')

type Payload = {
  /** 目标路由（base 之后的形式，如 /ja/characters.html） */
  to: string
  /** 视口上方最近标题在整页标题序列中的下标 */
  heading: number
  /** 该标题的层级，用于校验结构是否对得上 */
  level: string
  /** 视口顶部相对该标题顶部的像素偏移 */
  offset: number
  /** 整页进度（0~1），标题对不上时的兜底 */
  ratio: number
  at: number
}

/** 把 pathname 拆成 { lang, rest }；非 /zh|ja 前缀返回 null */
function splitLocale(pathname: string): { lang: string; rest: string } | null {
  const p = pathname.startsWith(BASE) ? pathname.slice(BASE.length) : pathname
  const m = /^\/(zh|ja)(\/.*)?$/.exec(p)
  if (!m) return null
  return { lang: m[1], rest: m[2] || '/' }
}

/** 正文里的标题序列（h1~h4，按文档顺序），语言切换后靠它对齐 */
function headings(): HTMLElement[] {
  const doc = document.querySelector('.vp-doc')
  if (!doc) return []
  return Array.from(doc.querySelectorAll<HTMLElement>('h1, h2, h3, h4'))
}

function maxScroll(): number {
  return Math.max(0, document.documentElement.scrollHeight - window.innerHeight)
}

function snapshot(to: string): Payload | null {
  const hs = headings()
  const y = window.scrollY
  let idx = -1
  for (let i = 0; i < hs.length; i++) {
    const top = hs[i].getBoundingClientRect().top + y
    if (top <= y + 4) idx = i
    else break
  }
  return {
    to,
    heading: idx,
    level: idx >= 0 ? hs[idx].tagName : '',
    offset: idx >= 0 ? y - (hs[idx].getBoundingClientRect().top + y) : 0,
    ratio: maxScroll() > 0 ? y / maxScroll() : 0,
    at: Date.now(),
  }
}

/** 用户自己动了页面就不要再校正（避免抢走用户操作） */
let moved = false
function watchUserScroll() {
  moved = false
  const stop = () => {
    moved = true
    window.removeEventListener('wheel', stop)
    window.removeEventListener('touchstart', stop)
    window.removeEventListener('keydown', stop)
  }
  window.addEventListener('wheel', stop, { passive: true })
  window.addEventListener('touchstart', stop, { passive: true })
  window.addEventListener('keydown', stop)
}

function jumpTo(y: number) {
  const target = Math.max(0, Math.min(y, maxScroll()))
  window.scrollTo({ top: target, behavior: 'auto' })
}

function apply(p: Payload) {
  if (moved) return
  const hs = headings()
  if (p.heading >= 0 && hs[p.heading] && hs[p.heading].tagName === p.level) {
    const top = hs[p.heading].getBoundingClientRect().top + window.scrollY
    jumpTo(top + p.offset)
    return
  }
  jumpTo(p.ratio * maxScroll())
}

/**
 * 捕获「同页换语言」的点击。只记一次，点击后 VitePress 会自己 push 到目标路由。
 */
export function initLangScroll() {
  document.addEventListener(
    'click',
    (e: MouseEvent) => {
      // ⚠️ 不能拦 e.defaultPrevented：VitePress 的路由拦截在 window 捕获阶段就先
      // preventDefault 了站内链接，等我们（document 捕获）跑到时它已经是 true。
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
      const a = (e.target as HTMLElement | null)?.closest?.('a') as HTMLAnchorElement | null
      if (!a || a.target === '_blank') return
      const href = a.getAttribute('href')
      if (!href || href.startsWith('#')) return
      let url: URL
      try {
        url = new URL(href, location.href)
      } catch {
        return
      }
      if (url.origin !== location.origin) return
      const cur = splitLocale(location.pathname)
      const next = splitLocale(url.pathname)
      if (!cur || !next || cur.lang === next.lang || next.rest !== cur.rest) return
      if (url.hash) return
      const p = snapshot(`/${next.lang}${next.rest}`)
      if (!p) return
      try {
        sessionStorage.setItem(KEY, JSON.stringify(p))
      } catch {
        /* 隐私模式下写不进去就算了 */
      }
    },
    true,
  )
}

/**
 * 路由变化后调用：如果这次跳转正是被记录的语言切换，就恢复滚动位置。
 * 正文晚到 → 轮询等它落地（最多 ~1s），落地后再校一次（图片撑高会改变 offset）。
 */
export function restoreLangScroll(routePath: string) {
  let p: Payload | null = null
  try {
    const raw = sessionStorage.getItem(KEY)
    if (raw) p = JSON.parse(raw) as Payload
  } catch {
    p = null
  }
  if (!p) return
  if (Date.now() - p.at > 120_000) {
    sessionStorage.removeItem(KEY)
    return
  }
  // VitePress 的 route.path 是**带 base** 的（/escah/ja/xxx.html），而 payload 存的是 base 之后的形式
  const routeNoBase = routePath.startsWith(BASE) ? routePath.slice(BASE.length) || '/' : routePath
  if (p.to !== routeNoBase) {
    // 这次跳转不是那次语言切换（用户又点了别处），记录作废，别在另页乱恢复
    sessionStorage.removeItem(KEY)
    return
  }
  sessionStorage.removeItem(KEY)
  watchUserScroll()

  let tries = 0
  const run = () => {
    const doc = document.querySelector('.vp-doc')
    if ((!doc || (doc.textContent || '').trim().length < 20) && tries++ < 20) {
      window.setTimeout(run, 80)
      return
    }
    apply(p as Payload)
    window.setTimeout(() => apply(p as Payload), 500)
    window.setTimeout(() => apply(p as Payload), 1200)
  }
  run()
}
