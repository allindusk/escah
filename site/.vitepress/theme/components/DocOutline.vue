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
  _el?: HTMLElement // 内部用：DOM 锚点元素，用于按正文位置排序
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

  // official-help 等页面在正文内注入了专属 .oh-toc 节点目录（两级：toc-l1 / toc-l2）。
  // 优先复用该目录数据（与页内目录完全一致，避免右侧大纲与页内目录结构/文案脱节）。
  const ohToc = root.querySelector('.oh-toc')
  if (ohToc) {
    const items: HNode[] = []
    const lis = Array.from(ohToc.querySelectorAll('li')) as HTMLElement[]
    for (const li of lis) {
      const a = li.querySelector('a')
      if (!a) continue
      const href = a.getAttribute('href') || ''
      if (!href.startsWith('#')) continue
      const id = href.slice(1)
      const txt = (a.textContent || '').trim()
      if (!id || !txt) continue
      const isL2 = li.classList.contains('toc-l2')
      const node: HNode = { id, text: txt, level: isL2 ? 2 : 1, children: [] }
      if (isL2 && items.length) {
        // 挂到最近的 L1 下
        for (let i = items.length - 1; i >= 0; i--) {
          if (items[i].level === 1) {
            items[i].children.push(node)
            break
          }
        }
      } else {
        items.push(node)
      }
    }
    if (items.length) {
      tree.value = items
      if (items.length) {
        observer = new IntersectionObserver(
          (entries) => {
            const visible = entries
              .filter((e) => e.isIntersecting)
              .map((e) => e.target as HTMLElement)
              .sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)
            if (visible.length) activeId.value = visible[0].id
          },
          { rootMargin: '0px 0px -70% 0px', threshold: 0 },
        )
        items.forEach((n) => {
          const el = document.getElementById(n.id)
          if (el) observer!.observe(el)
        })
      }
      return
    }
  }

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
  let result: HNode[] = []
  const stack: HNode[] = []
  for (const h of heads) {
    const node: HNode = { id: h.id, text: h.text, level: h.level, children: [] }
    while (stack.length && stack[stack.length - 1].level >= h.level) stack.pop()
    if (stack.length === 0) result.push(node)
    else stack[stack.length - 1].children.push(node)
    stack.push(node)
  }
  tree.value = result

  // 额外注册「页内表格目录」的锚点项（bedroom-scenes 等：表格前的 strong 标题，
  // 不是 h2/h3/h4，故默认大纲扫不到）。这些项作为**上一个 level-2 标题的子节点**挂入，
  // 形成「寝室列表 ▸ 各表格」的嵌套；而后续的「评论表格」等 h2 仍保持顶级、与之同级。
  const toc = root.querySelector('.escah-table-toc')
  if (toc) {
    const links = Array.from(toc.querySelectorAll('a')) as HTMLAnchorElement[]
    const existing = new Set(result.map((n) => n.text))
    // 父级固定为「第一个 level-2 标题」（bedroom-scenes 中即「寝室列表」），
    // 把表格锚点项挂到其下；后续的「评论表格」等 level-2 保持顶级、与之同级。
    const parent = result.find((n) => n.level === 2) || null
    for (const a of links) {
      const href = a.getAttribute('href') || ''
      if (!href.startsWith('#')) continue
      const id = href.slice(1)
      const text = (a.textContent || '').trim()
      if (!id || !text) continue
      // 若该项标题已在 h2/h3 大纲中（如「寝室列表」既是 h2 也是 toc 首项），则跳过避免重复
      if (existing.has(text)) continue
      const target = document.getElementById(id)
      const node: HNode = { id, text, level: 3, children: [], _el: target || undefined }
      if (parent) parent.children.push(node)
      else result.push(node)
    }
    tree.value = result
  }

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

onMounted(() => {
  nextTick(build)
  // 表格目录（escah-table-toc）由 tableEnhancer 在 enhanceTables 时注入，可能晚于
  // 本组件首次 build，故监听其完成事件再重建一次，确保右侧目录也包含表格标题项。
  document.addEventListener('escah:table-toc-built', onTocBuilt)
})
function onTocBuilt() {
  nextTick(build)
}
watch(
  () => route.path,
  () => nextTick(build),
)
onBeforeUnmount(() => {
  document.removeEventListener('escah:table-toc-built', onTocBuilt)
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
