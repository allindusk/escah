// 图片「省流量」改写的纯逻辑（浏览器与 SSR 都能跑：不 import 任何 node 模块）。
//   · 动图：src 指向首帧海报（十余 KB），原动图挂 data-anim-src，由 theme/animMedia.ts
//     在「鼠标设备进入视口」或「用户点按」时才真正加载；
//   · 静态大图：补 srcset/sizes，手机按视口宽度取 480w/1200w，不再下载 1920×1080 原图。
// 清单由 tools/gen_img_variants.py 生成（.vitepress/img-variants.json）。
// 使用方：components/MirrorContent.vue（正文渲染时改写，dev/preview/prod 一致）
//         + .vitepress/postprocess-media.mjs（构建后兜底扫 dist 里的静态 HTML）。

/** 与站点版式对应：≤959px 内容近似满宽（左右各 24px 内边距），桌面正文最宽约 780px */
export const SIZES = '(max-width: 959px) 92vw, 780px'

/** 只留 /img/... 作为清单键 */
export function manifestKey(src) {
  const i = src.indexOf('/img/')
  return i >= 0 ? src.slice(i) : null
}

/** 用原 src 的站点前缀（如 /escah）拼新 URL */
export function withPrefix(src, url) {
  const i = src.indexOf('/img/')
  return i >= 0 ? src.slice(0, i) + url : url
}

function addClass(tag, cls) {
  const m = tag.match(/\sclass="([^"]*)"/)
  if (m) return m[1].split(/\s+/).includes(cls) ? tag : tag.replace(m[0], ` class="${m[1]} ${cls}"`)
  return tag.replace(/^<img/, `<img class="${cls}"`)
}

function delClass(tag, cls) {
  const m = tag.match(/\sclass="([^"]*)"/)
  if (!m) return tag
  const list = m[1].split(/\s+/).filter((x) => x && x !== cls)
  return list.length ? tag.replace(m[0], ` class="${list.join(' ')}"`) : tag.replace(m[0], '')
}

function setAttr(tag, name, value) {
  const re = new RegExp(`\\s${name}="[^"]*"`)
  if (re.test(tag)) return tag.replace(re, ` ${name}="${value}"`)
  return tag.replace(/^<img/, `<img ${name}="${value}"`)
}

function delAttr(tag, name) {
  return tag.replace(new RegExp(`\\s${name}="[^"]*"`), '')
}

/** 把一个 <img> 归一化再按当前清单改写。
 *  关键：不是「已改过就跳过」，而是先还原成原图（原图地址存在 data-anim-src 里），
 *  再按清单重新算 —— 否则变体换了文件名（源图更新 / 生成规则升级）时，
 *  旧内容会一直带着已经 404 的旧海报地址。结果与原文一致时返回 null（视为没变）。 */
function rewriteTag(tag, map, stats) {
  const animM = tag.match(/\sdata-anim-src="([^"]+)"/)
  const srcNow = (tag.match(/\ssrc="([^"]+)"/) || [])[1]
  const origSrc = animM ? animM[1] : srcNow
  if (!origSrc) return null
  const key = manifestKey(origSrc)
  if (!key) return null
  const entry = map[key]

  // 还原成原图：去掉上一轮加的 data-anim-src / srcset / sizes / escah-anim，src 指回原图
  let base = tag
  if (animM) base = delAttr(base, 'data-anim-src')
  base = delAttr(base, 'srcset')
  base = delAttr(base, 'sizes')
  base = delClass(base, 'escah-anim')
  const baseSrc = base.match(/\ssrc="([^"]+)"/)
  base = baseSrc ? base.replace(baseSrc[0], ` src="${origSrc}"`) : base.replace(/^<img/, `<img src="${origSrc}"`)

  let next = base
  if (entry && entry.anim && entry.poster) {
    next = setAttr(next, 'src', withPrefix(origSrc, entry.poster))
    next = next.replace(/^<img/, `<img data-anim-src="${origSrc}"`)
    next = addClass(next, 'escah-anim')
    if (next !== tag) stats.anim++
  } else if (entry && Array.isArray(entry.srcset) && entry.srcset.length) {
    const list = entry.srcset.map(([url, w]) => `${withPrefix(origSrc, url)} ${w}w`)
    list.push(`${origSrc} ${entry.w}w`)
    next = setAttr(next, 'srcset', list.join(', '))
    next = setAttr(next, 'sizes', SIZES)
    if (next !== tag) stats.srcset++
  }
  if (next === tag) {
    if (entry) stats.skipped++
    return null
  }
  return next
}

/** 给 <img> 补懒加载/异步解码（已显式声明的不动，幂等）。
 *
 *  为什么必须有：正文图片来自 PukiWiki 原样 HTML，没有 loading 属性，
 *  「角色一览」这类页面一屏外还有 400+ 张头像，浏览器会全部并发下载
 *  （实测 442 张 / 2.7 MB），移动端首屏被图片抢带宽。
 *  首屏图用 loading="lazy" 无副作用：浏览器对视口内的懒加载图仍然是立即请求的，
 *  只是把视口外的那几百张推迟到滚动到附近。 */
function ensureImgHints(tag) {
  let out = tag
  if (!/\sloading\s*=/i.test(out)) out = out.replace(/^<img/i, '<img loading="lazy"')
  if (!/\sdecoding\s*=/i.test(out)) out = out.replace(/^<img/i, '<img decoding="async"')
  return out
}

/** 单段 HTML 的改写；返回 null 表示没变 */
export function rewriteHtml(html, map, stats = { anim: 0, srcset: 0, skipped: 0 }) {
  if (!html || html.indexOf('<img') < 0) return null
  const out = html.replace(/<img\s[^>]*>/g, (tag) => {
    const hinted = ensureImgHints(tag)
    const next = map ? rewriteTag(hinted, map, stats) : null
    return next == null ? hinted : next
  })
  return out === html ? null : out
}
