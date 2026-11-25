/**
 * 移动端体验增强（2026-09-30）
 * ---------------------------------------------------------------------------
 * 只在 ≤767px 生效，桌面端完全不参与（判定失败即 early-return，不做任何 DOM 改动）。
 *
 * 做四件事：
 *  1. 宽表格「还能往哪滑」提示：按真实溢出与滚动位置给容器打 class，
 *     由 mobile.css 的 .escah-xscroll 系列画出左右渐隐阴影。
 *  2. 页内目录（原站 .contents / official-help .oh-toc）过长时折叠：
 *     默认只露出约一屏内的高度，底部渐隐 + 「展开全部目录（N 项）」按钮。
 *     （样式已在 mobile.css 写好，这里只负责判定与插按钮。）
 *  3. 侧栏抽屉打开时给 <html> 打标，让右下角悬浮栈让开。
 *  4. 悬浮栈滚动时淡出（滚动停止 0.7s 后恢复），避免长时间压在正文上。
 */

const MQ_MOBILE = '(max-width: 767px)'
const TOC_FOLD_RATIO = 0.42 // 折叠后最多占视口高度的比例，与 mobile.css 的 42vh 保持一致

function isMobile(): boolean {
  return typeof window !== 'undefined' && window.matchMedia(MQ_MOBILE).matches
}

function debounce<T extends (...args: any[]) => void>(fn: T, wait: number): T {
  let timer: number | undefined
  return function (this: unknown, ...args: any[]) {
    if (timer) window.clearTimeout(timer)
    timer = window.setTimeout(() => fn.apply(this, args), wait)
  } as T
}

/* ------------------------------------------------------------------ */
/* 1. 横向滚动提示                                                      */
/* ------------------------------------------------------------------ */

const xscrollBound = new WeakSet<HTMLElement>()

function updateXScroll(el: HTMLElement): void {
  const overflowing = el.scrollWidth > el.clientWidth + 2
  el.classList.toggle('escah-xscroll', overflowing)
  if (!overflowing) {
    el.classList.remove('escah-at-start', 'escah-at-end')
    return
  }
  el.classList.toggle('escah-at-start', el.scrollLeft <= 2)
  el.classList.toggle(
    'escah-at-end',
    el.scrollLeft + el.clientWidth >= el.scrollWidth - 2,
  )
}

function scanXScroll(): void {
  if (!isMobile()) return
  document
    .querySelectorAll<HTMLElement>('.table-scroll, .escah-tbl-fs-scroll')
    .forEach((el) => {
      if (!xscrollBound.has(el)) {
        xscrollBound.add(el)
        const rerun = debounce(() => updateXScroll(el), 60)
        el.addEventListener('scroll', rerun, { passive: true })
      }
      updateXScroll(el)
    })
}

/* ------------------------------------------------------------------ */
/* 2. 页内目录折叠                                                      */
/* ------------------------------------------------------------------ */

/** 折叠后按钮上的文案 */
function foldLabel(n: number): string {
  return `展开全部目录（共 ${n} 项）`
}
function unfoldLabel(n: number): string {
  return `收起目录（共 ${n} 项）`
}

function scanInlineToc(): void {
  const boxes = Array.from(
    document.querySelectorAll<HTMLElement>(
      '.mirror-content .contents, .mirror-content .oh-toc',
    ),
  )

  const cleanup = (box: HTMLElement): void => {
    box.classList.remove('escah-toc-folded')
    const nb = box.nextElementSibling as HTMLElement | null
    if (nb && nb.classList.contains('escah-toc-more')) nb.remove()
  }

  if (!isMobile()) {
    boxes.forEach(cleanup)
    return
  }

  for (const box of boxes) {
    const items = box.querySelectorAll('li').length
    let btn = box.nextElementSibling as HTMLElement | null
    if (!btn || !btn.classList.contains('escah-toc-more')) btn = null

    // 项数太少没必要折叠（12 项以内，双列后约 6 行）
    if (items < 12) {
      cleanup(box)
      continue
    }

    // overflow:hidden 下 scrollHeight 仍是内容完整高度，可直接量
    const full = box.scrollHeight
    const limit = window.innerHeight * TOC_FOLD_RATIO

    if (full <= limit + 16) {
      cleanup(box)
      continue
    }

    box.classList.add('escah-toc-folded')
    if (!btn) {
      btn = document.createElement('button')
      btn.type = 'button'
      btn.className = 'escah-toc-more'
      const target = box
      const self = btn
      btn.addEventListener('click', () => {
        if (target.classList.contains('escah-toc-folded')) {
          target.classList.remove('escah-toc-folded')
          self.textContent = unfoldLabel(items)
        } else {
          target.classList.add('escah-toc-folded')
          self.textContent = foldLabel(items)
          target.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      })
      box.insertAdjacentElement('afterend', btn)
    }
    btn.textContent = foldLabel(items)
  }
}

/* ------------------------------------------------------------------ */
/* 3. 侧栏抽屉状态 → html.escah-drawer-open                             */
/* ------------------------------------------------------------------ */
/* mobile.css 里已用 html:has(.VPSidebar.open) 做同样的事，
   这里补一条 JS 兜底（老浏览器不支持 :has() 时仍能隐藏悬浮栈）。 */

const drawerWatched = new WeakSet<HTMLElement>()

/**
 * 移动端底部位移用**内联 important** 控制，不靠 CSS 类选择器。
 * 原因（2026-11-26 实测）：VitePress 的 scoped 规则
 * `.VPSidebar.open[data-v-xxx]{transform:translateX(0)}` 特异性高于我们的
 * `.VPSidebar.open`，而 `.VPSidebar:not(.open)` 那条 important 又只在关闭态生效；
 * 两边一叠加，打开时面板纹丝不动（永远停在屏幕下方）。内联 important 优先级最高，
 * 且跟随 open 类变化同步 → 打开/关闭都有过渡。
 */
/** 底部面板的标题栏：与「本页目录」面板同一套（标题 + 「关闭 ✕」），避免两处交互割裂 */
function ensureSheetHead(sb: HTMLElement, narrow: boolean): void {
  const existing = sb.querySelector<HTMLElement>('.escah-sheet-head')
  if (!narrow) {
    existing?.remove()
    return
  }
  if (existing) return
  const ja = (document.documentElement.lang || '').toLowerCase().startsWith('ja')
  const head = document.createElement('div')
  head.className = 'escah-sheet-head'
  const title = document.createElement('span')
  title.textContent = ja ? 'ページ一覧' : '全站页面'
  const btn = document.createElement('button')
  btn.type = 'button'
  btn.className = 'escah-sheet-close'
  btn.textContent = ja ? '閉じる ✕' : '关闭 ✕'
  btn.addEventListener('click', () => {
    // 关抽屉：点遮罩（VitePress 的关闭入口），没有遮罩就再点一次 menu
    const bd = document.querySelector<HTMLElement>('.VPBackdrop')
    if (bd) bd.click()
    else document.querySelector<HTMLElement>('.VPLocalNav button.menu')?.click()
  })
  head.append(title, btn)
  sb.insertBefore(head, sb.firstChild)
}

function syncSheetState(): void {
  const sb = document.querySelector<HTMLElement>('.VPSidebar')
  if (!sb) return
  const open = sb.classList.contains('open')
  const narrow = window.matchMedia('(max-width: 959px)').matches
  document.documentElement.classList.toggle('escah-drawer-open', open)
  ensureSheetHead(sb, narrow)
  if (narrow) {
    sb.style.setProperty('transform', open ? 'translateY(0)' : 'translateY(100%)', 'important')
  } else {
    sb.style.removeProperty('transform')
  }
}

function bindDrawerState(): void {
  const sb = document.querySelector<HTMLElement>('.VPSidebar')
  if (!sb) return
  syncSheetState()
  if (drawerWatched.has(sb)) return
  drawerWatched.add(sb)
  new MutationObserver(syncSheetState).observe(sb, {
    attributes: true,
    attributeFilter: ['class'],
  })
}

/* ------------------------------------------------------------------ */
/* 4. 生命周期                                                          */
/* ------------------------------------------------------------------ */

/** 页面渲染/路由切换后重跑全部移动端增强（Layout.vue 调用） */
export function refreshMobileUX(): void {
  if (typeof document === 'undefined') return
  bindDrawerState()
  if (!isMobile()) return
  scanInlineToc()
  scanXScroll()
}

let started = false

/* ------------------------------------------------------------------ */
/* 5. 悬浮控件：滚动时淡出，停手 0.7s 后回来                            */
/* ------------------------------------------------------------------ */

let dockIdle: number | undefined

/** 滚动时淡出的悬浮控件：右下悬浮栈 + 左下「全站页面」按钮（两者表现必须一致） */
function dockTargets(): HTMLElement[] {
  return [document.querySelector('.escah-dock'), document.querySelector('.escah-sitemenu-btn')].filter(
    (el): el is HTMLElement => !!el,
  )
}

function bindDockDim(): void {
  window.addEventListener(
    'scroll',
    () => {
      if (!isMobile()) return
      const els = dockTargets()
      if (!els.length) return
      els.forEach((el) => el.classList.add('escah-dock-dim'))
      if (dockIdle) window.clearTimeout(dockIdle)
      dockIdle = window.setTimeout(() => {
        els.forEach((el) => el.classList.remove('escah-dock-dim'))
      }, 700)
    },
    { passive: true },
  )
}

/** 全局只调用一次：绑定各种被动监听（Layout.vue onMounted 调用） */
export function initMobileUX(): void {
  if (typeof window === 'undefined' || started) return
  started = true

  const rerun = debounce(() => refreshMobileUX(), 220)

  window.addEventListener('resize', () => {
    // 离开移动端断点时也要清理折叠态，故不在这里 early-return
    rerun()
  })
  window.addEventListener('orientationchange', rerun)
  // 排序/筛选/全屏等都会引发点击，之后表格溢出状态可能变化
  document.addEventListener('click', (e) => {
    if (!isMobile()) return
    const t = e.target as HTMLElement | null
    if (!t) return
    if (t.closest('.escah-tbl, .escah-tbl-fs, .escah-filter-pop, .charlist-toolbar')) rerun()
  })
  bindDockDim()
  refreshMobileUX()
}

/** 供外部（如表格全屏打开后）主动触发一次 */
export const refreshMobileUXDebounced = debounce(() => refreshMobileUX(), 260)
