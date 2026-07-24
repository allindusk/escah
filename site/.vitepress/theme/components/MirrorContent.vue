<script setup lang="ts">
// 用 v-html 渲染 PukiWiki 原始 HTML 片段。
// 关键点：原始 HTML 不再作为 Vue 模板编译（其标签层级错乱/多行属性/自闭合写法
// 会让 Vue 严格解析器报 “Element is missing end tag”），而是在运行时由浏览器
// （宽松 HTML 解析）与 SSR 阶段由 v-html 注入。片段已在流水线侧经 _sanitize_html
// 处理（剔除 on* 事件处理器、平衡标签），因此 v-html 注入是安全的。
// 片段通过 JSON 导入（Vite 在 SSR 下可靠转换 JSON，而 ?raw 在 SSR 下返回空），
// 因此预渲染的静态 HTML 中即包含镜像正文，利于 SEO。
import { withBase } from 'vitepress'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { charModalStore as store } from './charModalStore'
import charRefs from '../charRefs.json'

const props = defineProps<{ html: string }>()

// 片段内图片以 /img/<hash> 绝对路径写入，但站点 base 为 /escah/；
// v-html 注入的字符串 URL 不会被 Vite 自动加 base，需在此手动补全，
// 否则本地预览与线上均会 404。withBase 随 base 配置自动适应。
const resolved = computed(() =>
  (props.html || '').replace(/\/img\//g, withBase('/img/')),
)

// ===== 全页面角色浮窗 =====
// charRefs 由 tools/gen_char_refs.py 生成：369 个角色名 + 头像 hash→名 映射。
// 正文里无论「角色链接 / 独立头像 / 纯文本角色名」出现，都打 data-char 标记，
// 统一接入与「角色一览」一致的悬停展示 / 点击固定逻辑。
const nameSet = new Set<string>(charRefs.names)
const avatarMap: Record<string, string> = charRefs.avatarHashes

const escapeRegExp = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
// 纯文本匹配仅用长度 ≥ 3 的名字，避免过短名字造成大量误命中；
// 按长度降序排列，使较长名字优先（重叠处不吃掉短名）。
const plainNames = charRefs.names
  .filter((n) => Array.from(n).length >= 3)
  .sort((a, b) => Array.from(b).length - Array.from(a).length)
const nameRegex = new RegExp(plainNames.map(escapeRegExp).join('|'), 'g')

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
    const name = avatarMap[m[1]]
    if (name) img.setAttribute('data-char', name)
  })
}

function wrapPlainTextNames(el: HTMLElement) {
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const p = node.parentElement
      if (!p) return NodeFilter.FILTER_REJECT
      // 跳过链接内、已标记的 span、脚本/样式
      if (p.closest('a, [data-char], script, style')) return NodeFilter.FILTER_REJECT
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
      span.setAttribute('data-char', matched)
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
  let node = target as HTMLElement | null
  while (node && node !== root.value) {
    const c = node.dataset?.char
    if (c) return c
    node = node.parentElement
  }
  return null
}

function onOver(e: MouseEvent) {
  const name = findChar(e.target)
  if (name) {
    store.cancelHide()
    store.show(name)
  } else if (!store.pinned && store.visible) {
    store.scheduleHide()
  }
}

function onClick(e: MouseEvent) {
  const name = findChar(e.target)
  if (name) {
    // 点击角色引用：不跳转，改为固定（pin）浮窗；
    // 阻断冒泡，避免头像同时触发 Layout 的图片灯箱
    e.preventDefault()
    e.stopPropagation()
    store.show(name)
    store.pinned = true
  }
}

onMounted(() => {
  const el = root.value
  if (!el) return
  tagCharLinks(el)
  tagAvatars(el)
  wrapPlainTextNames(el)
  el.addEventListener('mouseover', onOver)
  el.addEventListener('click', onClick)
})
onUnmounted(() => {
  const el = root.value
  if (!el) return
  el.removeEventListener('mouseover', onOver)
  el.removeEventListener('click', onClick)
})
</script>

<template>
  <div ref="root" class="mirror-content" v-html="resolved" />
</template>
