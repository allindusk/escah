<script setup lang="ts">
// 用 v-html 渲染 PukiWiki 原始 HTML 片段。
// 关键点：原始 HTML 不再作为 Vue 模板编译（其标签层级错乱/多行属性/自闭合写法
// 会让 Vue 严格解析器报 “Element is missing end tag”），而是在运行时由浏览器
// （宽松 HTML 解析）与 SSR 阶段由 v-html 注入。片段已在流水线侧经 _sanitize_html
// 处理（剔除 on* 事件处理器、平衡标签），因此 v-html 注入是安全的。
// 片段通过 JSON 导入（Vite 在 SSR 下可靠转换 JSON，而 ?raw 在 SSR 下返回空），
// 因此预渲染的静态 HTML 中即包含镜像正文，利于 SEO。
import { withBase, useData } from 'vitepress'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { charModalStore as store } from './charModalStore'
import charRefs from '../charRefs.json'
import { enhanceTables, syncAllFullBtns } from '../tableEnhancer'

const props = defineProps<{ html: string }>()

// 当前页面 slug（去掉语言前缀与扩展名），用于让表格增强按页面定制
// （如「角色一览」类页面启用「列宽按最长数据为准」）。
// 注意：useData().relativePath 在客户端 onMounted 时可能为 ''（VitePress hydration 时序），
// 导致此前 shrink 完全不触发。改用 location.pathname 解析（同步可靠），并回退 relativePath。
function deriveSlug(): string {
  const path = (typeof window !== 'undefined' && window.location?.pathname) || ''
  // 形如 /escah/zh/characters.html 或 /escah/ja/list-ssr.html → characters / list-ssr
  const m = path.match(/\/(ja|zh)\/([^/]+?)(?:\.html)?$/i)
  if (m) return decodeURIComponent(m[2])
  const rp = (useData().relativePath as string) || ''
  return rp.replace(/^(ja|zh)\//, '').replace(/\.md$/, '').replace(/\.html$/, '')
}
const pageSlug = computed(deriveSlug)

// 当前语言（ja / zh）。日文站保留原位日文角色名，不执行「句末【】浮窗标签」方案
// （该方案仅中文镜像页使用；日文站把角色名当成中文显示、移到句末属于误用）。
function deriveLocale(): 'ja' | 'zh' {
  const path = (typeof window !== 'undefined' && window.location?.pathname) || ''
  const m = path.match(/\/(ja|zh)\//)
  if (m) return m[1] as 'ja' | 'zh'
  const rp = (useData().relativePath as string) || ''
  return rp.startsWith('ja/') ? 'ja' : 'zh'
}
const pageLocale = computed(deriveLocale)

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
// 供「是否包含角色名」的布尔判定使用（不带 g 标志）。
// ⚠️ 关键：带 g 的正则在被 test()/exec() 混用时 lastIndex 会残留，导致跨文本节点漏判，
// 表现为「部分角色名浮窗失效」。布尔判定必须用无 g 副本，避免共享 lastIndex。
const nameRegexTest = new RegExp(plainDisplays.map(escapeRegExp).join('|'))

const root = ref<HTMLElement | null>(null)

function tagCharLinks(el: HTMLElement) {
  // 角色名是「单独处理逻辑」：原文本里指向角色详情页的 <a> 跳转链接降级为「不跳转」，
  // 去掉 href 仅保留原文显示，浮窗触发统一转移到块末的【角色名】标签（见 collectBlockCharTags）。
  el.querySelectorAll('a').forEach((a) => {
    // 句末【链接】标签（class=escah-ilink）由服务端生成，已是正确跳转超链接，不动。
    if (a.classList.contains('escah-ilink')) return
    const href = a.getAttribute('href') || ''
    const m = href.match(/characters\/(.+)\.html$/)
    if (!m) return
    const name = decodeURIComponent(m[1])
    if (!nameSet.has(name)) return
    // 降级：去掉跳转能力（角色名浮窗不跳转，由 char-ref 接管悬停/点击固定）。
    // 角色名文本由后续 collectBlockCharTags 原位包裹为 char-ref（保留在 <a> 壳内、
    // 显示中文名），故此处仅去跳转属性，不再做块末追加。
    a.removeAttribute('href')
    a.removeAttribute('target')
    a.removeAttribute('rel')
  })
}

function tagAvatars(el: HTMLElement) {
  el.querySelectorAll('img').forEach((img) => {
    // 已在角色容器内的头像：祖先 [data-char] 已覆盖，跳过避免重复
    if (img.closest('[data-char]')) return
    // 角色一览/列表中「图片列」的头像：图片列已有独立的角色名浮窗 span，
    // 头像本身不再打 data-char，避免重复浮窗。
    if (img.closest('.escah-img-col')) return
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

// 角色名统一处理逻辑（独立于正常跳转超链接 escah-ilink）：
// 全页面（含评论区 .pcomment）正文里出现的角色名，无论原文是 <a> 跳转链接、
// <span class="plugin-tooltip"> 蓝字气泡、还是裸 <span>/纯文本，
// 一律「原位包裹」为 <span class="char-ref" data-char="日文名">显示名</span> 浮窗标签
// （不跳转、悬停弹浮窗），**绝不移动到块末**。
//
// ⚠️ 为什么必须原位包裹、不能块末追加：
// 原站「角色名 + 说明列表」结构里，角色名永远在 <ul> 之前（作为该条目标题，
// 如 b-universe 的「登场角色」「时间停止」节：<li><角色名><ul>说明</ul></li>）。
// 旧方案的「块末追加」会把角色名丢到外层 <li> 末尾（= <ul> 之后），
// 既违背原排版、又破坏阅读顺序。原地包裹则角色名始终在原文出现处。
function collectBlockCharTags(el: HTMLElement) {
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const p = node.parentElement
      if (!p) return NodeFilter.FILTER_REJECT
      // 已生成的 .char-ref 标签内部、脚本/样式内不再处理（避免二次包裹）。
      // 已原位升级为 char-ref 的原站 plugin-tooltip 也跳过（upgradeTooltipCharNames 已处理）。
      // 注：<a> 内的角色名「允许」被包裹（tagCharLinks 已去掉 href 降级为浮窗，
      // 此处原位包成 char-ref 即可，不再 reject 'a'）。
      if (p.closest('[data-char], .char-ref, script, style')) return NodeFilter.FILTER_REJECT
      if (p.closest('.plugin-tooltip[data-char-upgraded]')) return NodeFilter.FILTER_REJECT
      return NodeFilter.FILTER_ACCEPT
    },
  })
  const hits: Text[] = []
  let n: Node | null
  while ((n = walker.nextNode())) {
    const t = n as Text
    if (nameRegexTest.test(t.nodeValue || '')) hits.push(t)
  }
  // 原位包裹：遍历文本节点，把每个命中的角色名替换为 <span class="char-ref">，
  // 其余文字（如「5秒（覚醒7.5秒）」后缀）保留原位。从后往前切，避免节点位移影响。
  for (const t of hits) {
    const text = t.nodeValue || ''
    nameRegex.lastIndex = 0
    const parts: Array<{ txt: string; isName: boolean; key: string }> = []
    let last = 0
    let m: RegExpExecArray | null
    while ((m = nameRegex.exec(text)) !== null) {
      if (m.index > last) parts.push({ txt: text.slice(last, m.index), isName: false, key: '' })
      parts.push({ txt: m[0], isName: true, key: nameAliases[m[0]] || m[0] })
      last = m.index + m[0].length
      if (m.index === nameRegex.lastIndex) nameRegex.lastIndex++
    }
    if (last < text.length) parts.push({ txt: text.slice(last), isName: false, key: '' })
    // ⚠️ 仅当整段文本完全不含角色名时才跳过（此前误用 parts.length<=1，
    // 会把「纯角色名、无前后缀」的文本节点（如「节拍婚礼·千麻」「神骑伊芙」）
    // 误判为无角色名而漏包，导致浮窗失效）。
    if (!parts.some((p) => p.isName)) continue
    const parent = t.parentElement!
    const frag = document.createDocumentFragment()
    for (const part of parts) {
      if (!part.isName) {
        frag.appendChild(document.createTextNode(part.txt))
      } else {
        const tag = document.createElement('span')
        tag.className = 'char-ref'
        tag.setAttribute('data-char', part.key)
        tag.textContent = nameAliasesInv(part.key)
        frag.appendChild(tag)
      }
    }
    parent.replaceChild(frag, t)
  }
}

// 原站角色 tooltip（class=plugin-tooltip，内蓝色字为角色名）是死壳（原站 JS 未迁移）。
// ⚠️ 修复（2026-08-13）：旧方案把整个 plugin-tooltip 隐藏、交给 collectBlockCharTags
// 在块末追加【角色名】，但原站 tooltip 蓝字位于 <ul> 之前（是 <li> 的标题/点评者），
// 块末追加会把角色名丢到 <ul> 之后，违背「角色名原位保留、不移到句末」铁律。
// 新方案：把 plugin-tooltip 原位升级为 char-ref 浮窗（保留在原 <ul> 前的位置，
// 显示中文名、不跳转、悬停弹浮窗），并打 data-char-upgraded 标记让 walker 跳过，
// 既保留原位、又避免「原位 + 句末」双重显示。
function upgradeTooltipCharNames(el: HTMLElement) {
  el.querySelectorAll('.plugin-tooltip').forEach((tip) => {
    const txt = tip.textContent || ''
    if (!nameRegexTest.test(txt)) return
    nameRegex.lastIndex = 0
    const m = nameRegex.exec(txt)
    if (!m) return
    const key = nameAliases[m[0]] || m[0]
    const disp = nameAliasesInv(key)
    const tag = document.createElement('span')
    tag.className = 'char-ref'
    tag.setAttribute('data-char', key)
    tag.textContent = disp
    tip.replaceWith(tag)
    tag.setAttribute('data-char-upgraded', '')
  })
}

// 角色名(key=日文名) → 显示名（优先中文名，否则日文名）。nameAliases 是 显示名→key，
// 这里反向查一次构建 key→显示名。
// ⚠️ 反向映射必须「优先中文显示名、跳过日文自映射」：nameAliases 里常含
// `日文原名 → 日文原名` 这样的自映射（gen_char_refs 把原名也加入显示名列表），
// 若直接「取最短」会被日文原名截胡，导致前端 char-ref 浮窗显示日文而非中文译名。
// 因此：跳过 disp===key 的自映射；多个候选时优先含 CJK（中文）且最短者。
const _hasCJK = (s: string) => /[㐀-鿿]/.test(s)
const _nameAliasesInvMap: Record<string, string> = (() => {
  const inv: Record<string, string> = {}
  for (const [disp, key] of Object.entries(nameAliases)) {
    if (disp === key) continue // 跳过日文原名自映射，避免污染显示名
    const cur = inv[key]
    if (!cur) { inv[key] = disp; continue }
    // 已存在候选：优先中文；同为中文/同为日文时取较短者
    const curCJK = _hasCJK(cur)
    const dispCJK = _hasCJK(disp)
    if (dispCJK && !curCJK) { inv[key] = disp }
    else if (dispCJK === curCJK && Array.from(disp).length < Array.from(cur).length) { inv[key] = disp }
  }
  return inv
})()
function nameAliasesInv(key: string): string {
  return _nameAliasesInvMap[key] || key
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
      mx: e.clientX,
      my: e.clientY,
    })
  } else if (store.mode === 'hover' && store.visible) {
    store.scheduleHide()
  }
}

// mouseover 只在「进入元素」时触发一次，鼠标在同一个锚点内部移动（宽表格单元格、
// 大图）时坐标会过期，导致浮窗按旧鼠标位置摆放又盖住光标。这里跟踪移动中的
// 真实坐标并刷新锚点，让定位始终基于当前光标。
function onMove(e: MouseEvent) {
  if (!store.visible || store.mode !== 'hover') return
  const name = findChar(e.target)
  if (!name || name !== store.name) return
  const a = store.anchor
  if (!a) return
  if (e.clientX === a.mx && e.clientY === a.my) return
  store.updateHoverPointer(e.clientX, e.clientY)
}

// 离开正文内容区：仅 hover 预览收起，固定窗保持
function onOut() {
  if (store.mode === 'hover') store.scheduleHide()
}

// PukiWiki region 折叠块：默认折叠（rgn-content 内联 display:none），
// 点击左侧 rgn-button 在展开/折叠间切换，并切换 plus/minus 图标显隐。
// 原站靠 tglRgn(this) 内联脚本，但流水线 _sanitize_html 已剔除 on* 属性，
// 故改用事件委托在客户端复刻该交互。全站页面（含未来新增）统一生效。
//
// PukiWiki region 折叠块：点击左侧 rgn-button 在展开/折叠间切换，并切换
// plus/minus 图标。原站靠 tglRgn(this) 内联脚本，流水线 _sanitize_html 已剔除
// on* 属性，故用事件委托在客户端复刻。
// 原站 region 分「默认折叠」与「默认展开」两种，初始 inline 可能写反：
//   展开态：content=block、desc=none；折叠态：content=none、desc=block。
// 旧逻辑只切 content、从不恢复 desc，导致初始展开块点击后 desc 永久不显示、
// 内容收起后整块空白（"整块不见了"）。
// 修复要点：① toggle 同时切换 desc 显隐；② 渲染时把「初始是否展开」直接同步成
// expanded 类的初始值（默认展开块渲染即带 expanded 类，默认折叠块不带）。这样
// **唯一真值就是 expanded 类**——用户首次点击即可在展开/折叠间切换，默认展开块
// （如 raid-005 第5期）既保持初始展开、又拥有完整折叠权；默认折叠块亦可正常双向
// toggle，且不再「整块消失」。
function _syncRgn(container: HTMLElement) {
  const expanded = container.classList.contains('expanded')
  const desc = container.querySelector('.rgn-description') as HTMLElement | null
  const content = container.querySelector('.rgn-content') as HTMLElement | null
  const plus = container.querySelector('.plus-icon') as HTMLElement | null
  const minus = container.querySelector('.minus-icon') as HTMLElement | null
  if (desc) desc.style.display = expanded ? 'none' : 'block'
  if (content) content.style.display = expanded ? 'block' : 'none'
  if (plus) plus.style.display = expanded ? 'none' : 'block'
  if (minus) minus.style.display = expanded ? 'block' : 'none'
}

// 渲染时把初始展开态（content 是否可见）同步成 expanded 类：展开则加类、折叠则
// 不加。之后显示完全由 expanded 类单一控制，用户首次点击即生效。
function _initRgnBase(container: HTMLElement) {
  if (container.dataset.rgnInit === '1') return
  container.dataset.rgnInit = '1'
  const content = container.querySelector('.rgn-content') as HTMLElement | null
  const visible = content
    ? (content.style.display || getComputedStyle(content).display) !== 'none'
    : false
  if (visible) container.classList.add('expanded')
}

function toggleRgn(btn: HTMLElement) {
  const container = btn.closest('.rgn-container') as HTMLElement | null
  if (!container) return
  const expanded = container.classList.toggle('expanded')
  _syncRgn(container)
  // 折叠内容里含表格时，初始增强因 display:none 宽度=0 把全屏/重置按钮隐藏，
  // 展开后宽度恢复，需重算按钮可见性，否则展开后看不到全屏/重置按钮。
  if (expanded) {
    requestAnimationFrame(() => syncAllFullBtns())
  }
}

function onRgnClick(e: MouseEvent) {
  const btn = (e.target as HTMLElement).closest('.rgn-button') as HTMLElement | null
  if (!btn) return
  e.preventDefault()
  e.stopPropagation()
  toggleRgn(btn)
}

function onClick(e: MouseEvent) {
  const cc = (e.target as HTMLElement).closest('a.escah-ilink') as HTMLElement | null
  // 句末【角色名】链接：是正文超链接，点击应跳转角色详情页（默认业内、中键新标签），
  // 不 pin 浮窗。hover 仍由 onOver 委托触发预览。
  if (cc && findChar(e.target)) {
    return
  }
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
  // 仅中文镜像页执行「句末【】浮窗标签」方案（collectBlockCharTags）与把原站
  // tooltip 蓝色气泡原位升级为 char-ref 浮窗（upgradeTooltipCharNames）。
  // 日文站保留原位日文角色名，不升级、不追加中文句末标签（避免把日文名误显示成中文并移动位置）。
  if (pageLocale.value === 'zh') {
    upgradeTooltipCharNames(el)
    collectBlockCharTags(el)
  }
  enhanceTables(el, pageSlug.value)
  // region 折叠块：先记初始展开基准（避免脏 inline 态导致无法重新折叠），
  // 再按基准+expanded 类规整 desc/content/图标。默认展开块保持展开，
  // 默认折叠块可正常双向 toggle（展开后能重新折叠），且不再「整块消失」。
  el.querySelectorAll('.rgn-container').forEach((c) => {
    const cc = c as HTMLElement
    _initRgnBase(cc)
    _syncRgn(cc)
  })
}

onMounted(() => {
  const el = root.value
  if (!el) return
  processEl(el)
  // 悬停/点击监听挂到 document 而非 root：表格「页面内全屏」会把表格移出 root，
  // 挂 root 会让全屏表格里的角色头像/名字无法触发悬停预览与点击固定。
  document.addEventListener('mouseover', onOver)
  document.addEventListener('mousemove', onMove)
  document.addEventListener('click', onRgnClick)
  document.addEventListener('click', onClick)
  document.addEventListener('click', onAnchorClick)
  // 离开正文内容区（mouseleave 在 document 上不可靠）：仅在 root 上收起 hover 预览
  el.addEventListener('mouseleave', onOut)
})
onUnmounted(() => {
  document.removeEventListener('mouseover', onOver)
  document.removeEventListener('mousemove', onMove)
  document.removeEventListener('click', onRgnClick)
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
