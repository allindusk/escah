// 构建期图片改写（node 侧）：
//   纯逻辑在 ./media-rewrite.mjs（浏览器 / SSR / node 共用，见 components/MirrorContent.vue）。
//   这里只做「读清单 + 扫 dist 静态 HTML」的兜底：
//     正文一般由 <MirrorContent :html="frag.html" /> 渲染，组件里已实时改写，
//     但少数图片直接写在页面 HTML 里（不经 v-html），构建后再扫一遍补齐。
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs'
import { resolve, join, extname } from 'node:path'
import { rewriteHtml } from './media-rewrite.mjs'

export { rewriteHtml }

const MANIFEST = resolve(import.meta.dirname, 'img-variants.json')

function loadMap() {
  if (!existsSync(MANIFEST)) return null
  try {
    const map = JSON.parse(readFileSync(MANIFEST, 'utf-8'))
    return Object.keys(map).length ? map : null
  } catch {
    return null
  }
}

function collectHtml(dir, acc = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name)
    if (e.isDirectory()) {
      if (e.name === 'assets' || e.name === 'img') continue
      collectHtml(p, acc)
    } else if (extname(e.name) === '.html') acc.push(p)
  }
  return acc
}

/** 构建后：兜底改写 dist 里的静态 HTML（幂等，重复跑 = 0 改动） */
export function rewriteMedia(distDir, { log = () => {} } = {}) {
  const stats = { files: 0, anim: 0, srcset: 0, skipped: 0 }
  const map = loadMap()
  // 清单缺失时仍要跑：rewriteHtml 还负责补 <img loading="lazy">，只跳过 srcset/动图部分。
  if (!map) log('[media] 缺少 img-variants.json：只补懒加载属性，跳过 srcset/动图改写')
  if (!existsSync(distDir)) return stats
  for (const file of collectHtml(distDir)) {
    const html = readFileSync(file, 'utf-8')
    if (!html.includes('<img')) continue
    const next = rewriteHtml(html, map, stats)
    if (next != null) {
      writeFileSync(file, next, 'utf-8')
      stats.files++
    }
  }
  return stats
}

if (process.argv[1]?.endsWith('postprocess-media.mjs')) {
  const dist = process.argv[2] || resolve(process.cwd(), '.vitepress/dist')
  const s = rewriteMedia(dist, { log: console.log })
  console.log(`[media] dist 改写：文件 ${s.files}，动图 ${s.anim}，srcset ${s.srcset}`)
}
