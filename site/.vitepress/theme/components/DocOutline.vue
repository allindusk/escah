<script setup lang="ts">
// 自定义右侧目录（树状），从 .mirror-content 的 h2/h3/h4 标题构建。
// 与 VitePress 默认 outline 相比：清理 anchor_super(†) 噪声、过滤异常长标题、
// 多级嵌套成树，并复用 MirrorContent 的平滑滚动逻辑。
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute } from 'vitepress'

interface HNode {
  id: string
  text: string
  level: number
  children: HNode[]
}

const route = useRoute()
const tree = ref<HNode[]>([])
const activeId = ref('')
let observer: IntersectionObserver | null = null

function cleanText(el: HTMLElement): string {
  const c = el.cloneNode(true) as HTMLElement
  c.querySelectorAll('.anchor_super').forEach((n) => n.remove())
  // 只删无实际文字的锚点噪声（†/↑/空 anchor），保留角色名等内容链接的文字
  c.querySelectorAll('a').forEach((n) => {
    const t = (n.textContent || '').trim()
    if (!t || /^[†↑#※・]+$/.test(t)) n.remove()
  })
  return (c.textContent || '')
    .replace(/†/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function build() {
  const root = document.querySelector('.mirror-content') as HTMLElement | null
  tree.value = []
  activeId.value = ''
  if (observer) {
    observer.disconnect()
    observer = null
  }
  if (!root) return
  const heads = Array.from(
    root.querySelectorAll('h2[id], h3[id], h4[id]'),
  )
    .map((h) => {
      const el = h as HTMLElement
      return {
        el,
        level: parseInt(el.tagName.substring(1), 10),
        id: el.id,
        text: cleanText(el),
      }
    })
    .filter((h) => h.text)
    .map((h) =>
      h.text.length > 40 ? { ...h, text: h.text.slice(0, 40) + '…' } : h,
    )

  // 按层级构建嵌套树
  const result: HNode[] = []
  const stack: HNode[] = []
  for (const h of heads) {
    const node: HNode = { id: h.id, text: h.text, level: h.level, children: [] }
    while (stack.length && stack[stack.length - 1].level >= h.level) stack.pop()
    if (stack.length === 0) result.push(node)
    else stack[stack.length - 1].children.push(node)
    stack.push(node)
  }
  tree.value = result

  // 当前阅读位置高亮
  if (heads.length) {
    observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .map((e) => e.target as HTMLElement)
          .sort(
            (a, b) =>
              a.getBoundingClientRect().top - b.getBoundingClientRect().top,
          )
        if (visible.length) activeId.value = visible[0].id
      },
      { rootMargin: '0px 0px -70% 0px', threshold: 0 },
    )
    heads.forEach((h) => observer!.observe(h.el))
  }
}

function onClick(e: MouseEvent) {
  const a = (e.target as HTMLElement).closest('a')
  if (!a) return
  const href = a.getAttribute('href') || ''
  if (!href.startsWith('#')) return
  e.preventDefault()
  const id = href.slice(1)
  const target = document.getElementById(id)
  if (!target) {
    history.replaceState(null, '', '#' + id)
    return
  }
  target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  history.replaceState(null, '', '#' + id)
  activeId.value = id
}

onMounted(() => nextTick(build))
watch(
  () => route.path,
  () => nextTick(build),
)
onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})
</script>

<template>
  <nav class="escah-doc-outline" v-if="tree.length">
    <p class="escah-doc-outline-title">目录</p>
    <ul class="escah-outline-list">
      <li
        v-for="n in tree"
        :key="n.id"
        class="escah-ol-item"
        :class="'escah-ol-l' + n.level"
      >
        <a :href="'#' + n.id" @click="onClick" :class="{ active: activeId === n.id }">{{ n.text }}</a>
        <ul v-if="n.children.length" class="escah-outline-list">
          <li
            v-for="c in n.children"
            :key="c.id"
            class="escah-ol-item"
            :class="'escah-ol-l' + c.level"
          >
            <a :href="'#' + c.id" @click="onClick" :class="{ active: activeId === c.id }">{{ c.text }}</a>
            <ul v-if="c.children.length" class="escah-outline-list">
              <li
                v-for="g in c.children"
                :key="g.id"
                class="escah-ol-item"
                :class="'escah-ol-l' + g.level"
              >
                <a :href="'#' + g.id" @click="onClick" :class="{ active: activeId === g.id }">{{ g.text }}</a>
              </li>
            </ul>
          </li>
        </ul>
      </li>
    </ul>
  </nav>
</template>
