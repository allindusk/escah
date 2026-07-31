<script setup lang="ts">
// 用 v-html 渲染 PukiWiki 原始 HTML 片段。
// 关键点：原始 HTML 不再作为 Vue 模板编译（其标签层级错乱/多行属性/自闭合写法
// 会让 Vue 严格解析器报 “Element is missing end tag”），而是在运行时由浏览器
// （宽松 HTML 解析）与 SSR 阶段由 v-html 注入。片段已在流水线侧经 _sanitize_html
// 处理（剔除 on* 事件处理器、平衡标签），因此 v-html 注入是安全的。
// 片段通过 JSON 导入（Vite 在 SSR 下可靠转换 JSON，而 ?raw 在 SSR 下返回空），
// 因此预渲染的静态 HTML 中即包含镜像正文，利于 SEO。
import { withBase } from 'vitepress'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { charModalStore as store } from './charModalStore'
import charRefs from '../charRefs.json'
import { enhanceTables } from '../tableEnhancer'

const props = defineProps<{ html: string }>()

// 片段内图片以 /img/<hash> 绝对路径写入，但站点 base 为 /escah/；
// v-html 注入的字符串 URL 不会被 Vite 自动加 base，需在此手动补全，
// 否则本地预览与线上均会 404。withBase 随 base 配置自动适应。
const resolved = computed(() =>
  (props.html || '').replace(/\/img\//g, withBase('/img/')),
)

// ===== 全页面角色浮窗 =====
// charRefs 由 tools/gen_char_refs.py 生成：角色名(=日文 key) + 头像 hash→名 映射 + nameAliases(日文名/中文名→key)。
// 正文里无论「角色链接 / 独立头像 / 纯文本角色名」出现，都打 data-char 标记，
// 统一接入与「角色一览」一致的悬停展示 / 点击固定逻辑。
const nameSet = new Set<string>(charRefs.names)
const avatarMap: Record<string, string> = charRefs.avatarHashes

const escapeRegExp = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
// 纯文本匹配覆盖「日文名 + 中文名(name_zh)」全部出现形式：中文页正文把角色名渲染成 name_zh，
// 必须映射回日文 key(=文件名) 才能正确加载浮窗数据（否则 404）。按长度降序使长名优先（不吃掉短名）。
const nameAliases: Record<string, string> = (charRefs as any).nameAliases || {}
const plainDisplays = Object.keys(nameAliases)
  .filter((n) => Array.from(n).length >= 3)
  .sort((a, b) => Array.from(b).length - Array.from(a).length)
const nameRegex = new RegExp(plainDisplays.map(escapeRegExp).join('|'), 'g')

const root = ref<HTMLElement | null>(null)

function tagCharLinks(el: HTMLElement) {
  el.querySelectorAll('a').forEach((a) => {
    const href = a.getAttribute('href') || ''
    const m = href.match(/characters\/(.+)\.html$/)
    if (!m) return
    const name = decodeURIComponent(m[1])
    if (nameSet.has(name)) a.setAttribute('data-char', name)
  })
}

function tagAvatars(el: HTMLElement) {
  el.querySelectorAll('img').forEach((img) => {
    // 已在角色链接内的头像：祖先 <a data-char> 已覆盖，跳过避免重复
    if (img.closest('a[data-char]')) return
    const src = img.getAttribute('src') || ''
    const m = src.match(/\/img\/([^"?#]+)/)
    if (!m) return
    let name = avatarMap[m[1]]
    // 兜底：avatarMap 未命中（同一角色在「角色一览缩略图」与「正文内联头像」用了
    // 不同图片 hash）时，用 alt/title 里的角色名解析。wiki 头像 alt 形如
    // "花のチルカ_icon.png"，去掉 _icon 与扩展名即得角色名，再经 nameAliases 回 key。
    if (!name) {
      const alt = (img.getAttribute('alt') || img.getAttribute('title') || '').trim()
      if (alt) {
        const nm = alt.replace(/\.(png|gif|jpe?g)$/i, '').replace(/_icon$/i, '').trim()
        const key = nameAliases[nm] || (nameSet.has(nm) ? nm : null)
        if (key) name = key
      }
    }
    if (name) img.setAttribute('data-char', name)
  })
}

function wrapPlainTextNames(el: HTMLElement) {
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const p = node.parentElement
      if (!p) return NodeFilter.FILTER_REJECT
      // 跳过已标记的 span、脚本/样式；但「非 /characters/ 的外部链接」内的角色名
      // 仍要作为纯文本打 data-char（tagCharLinks 仅处理指向角色页的链接，会漏掉外链中的名字）
      if (p.closest('[data-char], script, style')) return NodeFilter.FILTER_REJECT
      return NodeFilter.FILTER_ACCEPT
    },
  })
  const targets: Text[] = []
  let n: Node | null
  while ((n = walker.nextNode())) targets.push(n as Text)

  for (const textNode of targets) {
    const text = textNode.nodeValue || ''
    nameRegex.lastIndex = 0
    if (!nameRegex.test(text)) continue
    const frag = document.createDocumentFragment()
    let last = 0
    nameRegex.lastIndex = 0
    let m: RegExpExecArray | null
    while ((m = nameRegex.exec(text)) !== null) {
      const idx = m.index
      const matched = m[0]
      if (idx > last) frag.appendChild(document.createTextNode(text.slice(last, idx)))
      const span = document.createElement('span')
      span.className = 'char-ref'
      span.setAttribute('data-char', nameAliases[matched] || matched)
      span.textContent = matched
      frag.appendChild(span)
      last = idx + matched.length
      if (m.index === nameRegex.lastIndex) nameRegex.lastIndex++
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)))
    textNode.parentNode?.replaceChild(frag, textNode)
  }
}

function findChar(target: EventTarget | null): string | null {
  // 向上查找 data-char：终止条件用 document.body 而非 root，
  // 因为「表格页面内全屏」会把表格移出 root（挂到 body 的全屏遮罩里），
  // 若止步于 root 就会漏掉全屏表格内的角色头像/名字触发。
  let node = target as HTMLElement | null
  while (node && node !== document.body) {
    const c = node.dataset?.char
    if (c) return c
    node = node.parentElement
  }
  return null
}

function onOver(e: MouseEvent) {
  const name = findChar(e.target)
  if (name) {
    const el = (e.target as HTMLElement).closest('[data-char]') as HTMLElement
    const r = el.getBoundingClientRect()
    store.showHover(name, {
      left: r.left,
      top: r.top,
      right: r.right,
      bottom: r.bottom,
      width: r.width,
      height: r.height,
    })
  } else if (store.mode === 'hover' && store.visible) {
    store.scheduleHide()
  }
}

// 离开正文内容区：仅 hover 预览收起，固定窗保持
function onOut() {
  if (store.mode === 'hover') store.scheduleHide()
}

function onClick(e: MouseEvent) {
  const name = findChar(e.target)
  if (name) {
    // 点击角色引用：不跳转，改为固定（pin）浮窗（全部信息、居中、可拖动）；
    // 阻断冒泡，避免头像同时触发 Layout 的图片灯箱
    e.preventDefault()
    e.stopPropagation()
    store.pin(name)
  }
}

// 页内锚点跳转（wiki .contents 目录 / 正文内 #xxx 链接）：
// 平滑滚动到目标标题，并避让固定导航栏高度。
function onAnchorClick(e: MouseEvent) {
  const a = (e.target as HTMLElement).closest('a[href^="#"]') as HTMLAnchorElement | null
  if (!a) return
  const href = a.getAttribute('href') || ''
  if (!href.startsWith('#')) return
  const id = decodeURIComponent(href.slice(1))
  if (!id) return
  const target = document.getElementById(id)
  if (!target) return
  e.preventDefault()
  const nav = document.querySelector('.VPNav') as HTMLElement | null
  const navH = nav ? nav.getBoundingClientRect().height : 0
  const y = target.getBoundingClientRect().top + window.scrollY - navH - 10
  window.scrollTo({ top: y, behavior: 'smooth' })
  if (typeof history.replaceState === 'function') history.replaceState(null, '', '#' + id)
}

function processEl(el: HTMLElement) {
  tagCharLinks(el)
  tagAvatars(el)
  wrapPlainTextNames(el)
  enhanceTables(el)
}

onMounted(() => {
  const el = root.value
  if (!el) return
  processEl(el)
  // 悬停/点击监听挂到 document 而非 root：表格「页面内全屏」会把表格移出 root，
  // 挂 root 会让全屏表格里的角色头像/名字无法触发悬停预览与点击固定。
  document.addEventListener('mouseover', onOver)
  document.addEventListener('click', onClick)
  document.addEventListener('click', onAnchorClick)
  // 离开正文内容区（mouseleave 在 document 上不可靠）：仅在 root 上收起 hover 预览
  el.addEventListener('mouseleave', onOut)
})
onUnmounted(() => {
  document.removeEventListener('mouseover', onOver)
  document.removeEventListener('click', onClick)
  document.removeEventListener('click', onAnchorClick)
  const el = root.value
  if (el) el.removeEventListener('mouseleave', onOut)
})

// 片段内容随路由/语言切换变化时，重新处理（角色标记 + 表格增强）
watch(
  () => props.html,
  () => {
    nextTick(() => {
      const el = root.value
      if (el) processEl(el)
    })
  },
)
</script>

<template>
  <div ref="root" class="mirror-content" v-html="resolved" />
</template>
