// 动图「海报优先」策略（对应 .vitepress/postprocess-media.mjs）：
//   · HTML 里的 <img> 已被改写成 src=首帧海报（十几 KB）+ data-anim-src=原动图（300~800KB）
//   · 鼠标设备：图片进入视口附近时自动换成动图 → 观感与改造前一致
//   · 触屏设备：保持静帧，用户点按才下载动图（海报角落有 ▶ 角标提示）
const FINE_POINTER = () => window.matchMedia('(hover: hover) and (pointer: fine)').matches

let io: IntersectionObserver | null = null

/** 把某张图从海报换成动图；已换过则返回 false */
export function playAnimImage(img: HTMLImageElement): boolean {
  const src = img.dataset.animSrc
  if (!src || img.dataset.animPlaying === '1') return false
  img.dataset.animPlaying = '1'
  img.src = src
  return true
}

function watchAll() {
  if (!io) return
  document.querySelectorAll<HTMLImageElement>('img[data-anim-src]').forEach((img) => {
    if (img.dataset.animWatched === '1') return
    img.dataset.animWatched = '1'
    io!.observe(img)
  })
}

export function initAnimMedia() {
  if (typeof window === 'undefined') return
  const all = () => document.querySelectorAll<HTMLImageElement>('img[data-anim-src]')
  if (!('IntersectionObserver' in window)) {
    all().forEach((img) => playAnimImage(img))
    return
  }
  io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue
        io?.unobserve(e.target)
        if (FINE_POINTER()) playAnimImage(e.target as HTMLImageElement)
      }
    },
    { rootMargin: '300px 0px' },
  )
  watchAll()
  // 正文是 v-html 注入的，可能晚于 Layout 挂载才出现；补两次扫尾 + 路由切换时再扫（refreshAnimMedia）
  setTimeout(watchAll, 300)
  setTimeout(watchAll, 1200)
}

/** 路由切换后新页面的图片需要重新纳入观察 */
export function refreshAnimMedia() {
  watchAll()
}
