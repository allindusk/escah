// 页内锚点跳转的统一实现（右侧大纲 DocOutline / 正文 MirrorContent 共用）。
//
// 2026-11-25 修：wiki 的页内目录与右侧大纲经常指向 **PukiWiki region 折叠块里的标题**
// （如 raid-buff-debuff 的 #content_1_5、#content_1_9：h4 在 .rgn-content 内，
// 该容器初始 style="display:none"）。目标元素此时高度为 0，直接 scrollIntoView /
// scrollTo 等于"点了没反应"，用户看到的就是目录跳不过去。
// 因此跳转前先把目标所在的所有折叠祖先展开，再滚动。
//
// 另外：展开折叠块会让上方内容**长高**，跳转前算好的 y 立刻失效；再加上 smooth
// 滚动动画期间连续点击会互相打断。所以这里不用 smooth，改为"即时滚动 + 连续几帧
// 按目标当前位置纠偏"，保证展开/图片加载等后续重排之后仍落在标题上。

// 2026-11-26 补：折叠块里的表格在增强时 `display:none`（宽度 0），全屏/重置按钮被判为
// 「不需要」而隐藏；这里展开后要像手动点开一样重算按钮可见性，否则跳过去看不到「表格全屏」。
import { syncAllFullBtns } from './tableEnhancer'

/** 展开目标元素所在的所有折叠 region（PukiWiki .rgn-container），返回是否有展开动作。 */
export function expandRgnAncestors(el: HTMLElement): boolean {
  let changed = false
  let cur: HTMLElement | null = el.parentElement
  while (cur && !cur.classList.contains('mirror-content')) {
    if (
      cur.classList.contains('rgn-container') &&
      !cur.classList.contains('expanded')
    ) {
      const content = cur.querySelector('.rgn-content') as HTMLElement | null
      if (content) {
        cur.classList.add('expanded')
        const desc = cur.querySelector('.rgn-description') as HTMLElement | null
        const plus = cur.querySelector('.plus-icon') as HTMLElement | null
        const minus = cur.querySelector('.minus-icon') as HTMLElement | null
        if (desc) desc.style.display = 'none'
        content.style.display = 'block'
        if (plus) plus.style.display = 'none'
        if (minus) minus.style.display = 'block'
        changed = true
      }
    }
    cur = cur.parentElement
  }
  return changed
}

/** 目标标题距视口顶部应处的偏移（避开固定导航栏）。 */
function desiredTop(): number {
  const nav = document.querySelector('.VPNav') as HTMLElement | null
  const navH = nav ? nav.getBoundingClientRect().height : 0
  return navH + 10
}

/**
 * 即时滚动到目标，并在随后的若干帧里持续纠偏。
 * 展开折叠块、懒加载图片等都会在滚动后继续改变上方高度，单次计算容易差一大截。
 * 连续点击不同目录项时，只保留最后一次的纠偏循环，避免两套循环互抢滚动位置。
 */
let jumpToken = 0
function jumpTo(target: HTMLElement): void {
  const token = (jumpToken += 1)
  let ticks = 0
  const correct = () => {
    if (token !== jumpToken) return
    const delta = target.getBoundingClientRect().top - desiredTop()
    if (Math.abs(delta) > 2) {
      window.scrollTo({ top: Math.max(0, (window.scrollY || 0) + delta), behavior: 'auto' })
    }
    // 刚展开的折叠块里，表格此刻才有宽度：重算「表格全屏 / 重置」按钮
    if (ticks === 0 || ticks === 6) syncAllFullBtns()
    ticks += 1
    // 展开折叠块/图片加载会让上方内容持续长高，纠偏窗口留够 ~1.2s
    if (ticks < 16) window.setTimeout(correct, 75)
  }
  correct()
  // 表格宽度也可能在图片/字体加载后变化，收尾再算一次
  window.setTimeout(() => {
    if (token === jumpToken) syncAllFullBtns()
  }, 1300)
}

/** 滚动到指定 id 的标题（必要时先展开折叠块）。返回目标是否存在。 */
export function scrollToAnchor(id: string): boolean {
  if (!id) return false
  const target = document.getElementById(id)
  if (!target) {
    if (typeof history.replaceState === 'function') {
      history.replaceState(null, '', '#' + id)
    }
    return false
  }

  expandRgnAncestors(target)
  jumpTo(target)

  if (typeof history.replaceState === 'function') {
    history.replaceState(null, '', '#' + id)
  }
  return true
}

/** 带 #hash 直接打开页面时（或刷新后），同样先展开再跳转。 */
export function scrollToCurrentHash(): void {
  if (typeof window === 'undefined') return
  const raw = (window.location.hash || '').replace(/^#/, '')
  if (!raw) return
  let id = raw
  try {
    id = decodeURIComponent(raw)
  } catch {
    /* 保持原样 */
  }
  // 正文是挂载后异步注入的，首屏这一刻目标可能还不存在 → 轮询等待
  let tries = 0
  const attempt = () => {
    const target = document.getElementById(id)
    if (!target) {
      tries += 1
      if (tries <= 60) window.setTimeout(attempt, 100)
      return
    }
    expandRgnAncestors(target)
    window.setTimeout(() => jumpTo(target), 50)
    // 首屏图片/表格陆续加载会继续改变上方高度，稍后再纠偏一次
    window.setTimeout(() => jumpTo(target), 500)
  }
  attempt()
}
