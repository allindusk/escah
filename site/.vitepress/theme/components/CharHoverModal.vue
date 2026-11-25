<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useData, withBase } from 'vitepress'
import { useI18n } from '../i18n'
import { charModalStore as store, type HoverAnchor } from './charModalStore'
import siteTerms from '../.gen-data/site-terms.json'

interface Cell { h: boolean; t: string; zh?: string; cs?: number; rs?: number }
interface Section { label: string; rows: Cell[][] }
interface CharData {
  name: string
  name_zh?: string
  rarity?: string
  icon?: string
  release_date?: string
  sections: Record<string, Section>
}

const SECTION_ORDER = ['プロフィール', '入手方法', '基本ステータス', '詳細ステータス', '必殺技', '固有効果']
// hover 预览只展示轻量分段：头像(头部) + 以下分段；基本ステータス 精简为仅显示 100 级属性
const HOVER_SECTIONS = ['プロフィール', '基本ステータス', '詳細ステータス', '必殺技', '固有効果']
const HOVER_LEFT = ['プロフィール', '基本ステータス', '詳細ステータス']   // 人物档案 + 基础属性 + 详细属性
const HOVER_RIGHT = ['必殺技', '固有効果']                                  // 必杀技 + 固有效果
const { t, isZh } = useI18n()
const { lang } = useData()

const data = ref<CharData | null>(null)
const loading = ref(false)
const loadError = ref(false)
const cache = new Map<string, CharData>()

// 中文站标题：中文名（日文名）
const displayName = computed(() => {
  const d = data.value
  if (isZh() && d && d.name_zh) return `${d.name_zh}（${store.name}）`
  return store.name
})

// 拖动状态
const dragging = ref(false)
const dragOffset = { dx: 0, dy: 0 }

const modalStyle = computed(() => {
  if (store.x !== null && store.y !== null) {
    return { left: store.x + 'px', top: store.y + 'px', transform: 'none' }
  }
  return { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }
})

/* 手机端这个浮窗会被 mobile.css 改造成整屏 sheet（pinned 模式），
   打开期间锁住整页滚动，否则 iOS 上背景页会跟着手指一起滚。
   样式见 mobile.css 的 html.escah-sheet-open。 */
const SHEET_OPEN_CLASS = 'escah-sheet-open'
watch(
  () => store.visible && store.mode === 'pinned',
  (open) => {
    if (typeof document === 'undefined') return
    const isPhone = window.matchMedia('(max-width: 767px)').matches
    document.documentElement.classList.toggle(SHEET_OPEN_CLASS, open && isPhone)
  },
  { immediate: true },
)

// 2026-11-24 重写：旧版把「鼠标点 mx/my」当成避让对象，浮窗紧贴鼠标右侧 12px 放置。
// 但触发它的是一整块锚点（头像 + 右侧角色名，宽 100~300px），所以浮窗虽然没压住指针，
// 却把旁边的名字/头像压住了（用户截图里浮窗直接盖在自己的头像与名字上）。
// 现在一律以「锚点矩形」为避让对象：优先整体放在锚点右侧，其次左侧，再其次正下方/上方。
const hoverEl = ref<HTMLElement | null>(null)
const hoverX = ref(0)
const hoverY = ref(0)
// 浮窗尺寸上限：不再写死 680px / 84vh，改为按「锚点周围实际可用空间」动态计算
// （见 placeHover）。固定宽度会把两栏各压到 ~320px，必杀技/固有效果长文本被迫
// 折行过多 → 行数暴涨；再叠加固定 84vh 高度，最后几行直接被 overflow:hidden 裁掉，
// 看上去就是「信息展示不全」。
const HOVER_MIN_SIDE = 460   // 侧边窄于这个宽度就不值得贴（会变成细长条）
const HOVER_MAX_W = 1180     // 舒适上限：再宽只是把页面其它内容遮住，字数不会变少
const hoverMaxW = ref(0)
const hoverMaxH = ref(0)
const hoverStyle = computed(() => {
  const s: Record<string, string> = { left: hoverX.value + 'px', top: hoverY.value + 'px' }
  if (hoverMaxW.value > 0) s.maxWidth = hoverMaxW.value + 'px'
  if (hoverMaxH.value > 0) s.maxHeight = hoverMaxH.value + 'px'
  return s
})

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v))
}

async function placeHover() {
  const el = hoverEl.value
  if (!el) return
  const vw = window.innerWidth
  const vh = window.innerHeight
  const gap = 12      // 浮窗与锚点之间的间隙
  const pad = 8       // 与视口边缘的间隙
  const a = store.anchor as HoverAnchor | null

  // ---- 0) 先按锚点周围可用空间定宽/高上限，再量真实尺寸 ----
  // 上限只取决于锚点几何（与浮窗内容无关），所以可以先写进样式再测量。
  const aR0 = a ? Math.max(a.right ?? a.left + a.width, a.safeRight ?? 0) : 0
  const aB0 = a ? (a.bottom ?? a.top + a.height) : 0
  const sideRoom = a ? Math.max(vw - pad - (aR0 + gap), a.left - gap - pad) : 0
  // 侧边够宽才贴边；否则宁可铺满视口宽度放到锚点上方/下方（同样不遮锚点）。
  const useSide = !!a && sideRoom >= HOVER_MIN_SIDE
  const cap = Math.round(Math.max(
    useSide ? Math.min(sideRoom, HOVER_MAX_W) : Math.min(vw - pad * 2, HOVER_MAX_W),
    240,
  ))
  // 高度：贴边放置时整屏可用高度都能用（不再固定 84vh，矮屏笔记本上 731px 的内容
  // 在 84vh 里会被裁掉最后几行）；改放上下方时只能占锚点上方/下方那一条，必须按
  // 该条的高度收，否则浮窗会反过来盖住锚点。
  const roomBelow = vh - pad - (aB0 + gap)
  const roomAbove = a ? a.top - gap - pad : 0
  const maxH = Math.round(Math.max(
    Math.min(useSide || !a ? vh - pad * 2 : Math.max(roomBelow, roomAbove), vh - pad * 2),
    240,
  ))
  if (hoverMaxW.value !== cap || hoverMaxH.value !== maxH) {
    hoverMaxW.value = cap
    hoverMaxH.value = maxH
    await nextTick()   // 等 max-width / max-height 生效并重排后再测量
  }

  // ⚠️ 测量前先把浮窗挪到左上角：浮窗是 shrink-to-fit，宽度会被「当前 left 到视口
  // 右缘」的可用空间卡住。若沿用上一次的 left 直接量，量到的宽度会偏窄；按这个偏
  // 窄宽度算出的位置落地后，可用空间变大 → 浮窗重新变宽 → 压住锚点（实测 700px
  // 视口下出现过）。这里同一帧内挪开再量，量完立刻写回最终坐标。
  el.style.left = '0px'
  el.style.top = '0px'
  const r = el.getBoundingClientRect()
  const w = r.width
  const h = r.height

  const maxLeft = Math.max(pad, vw - pad - w)
  const maxTop = Math.max(pad, vh - pad - h)

  // 无锚点（点击固定窗）：居中，交给 modalStyle 之外的默认位置
  if (!a) {
    hoverX.value = Math.round((vw - w) / 2)
    hoverY.value = Math.round((vh - h) / 2)
    el.style.left = hoverX.value + 'px'
    el.style.top = hoverY.value + 'px'
    return
  }

  const aL = a.left
  const aR = aR0
  const aT = a.top
  const aB = a.bottom ?? a.top + a.height
  const mx = a.mx
  const my = a.my

  const spaceRight = vw - pad - (aR + gap)
  const spaceLeft = (aL - gap) - pad

  let left: number
  let top: number

  // ---- 1) 水平：整块贴到锚点右侧 / 左侧（优先更宽敞的一侧）----
  if (spaceRight >= w && (spaceRight >= spaceLeft || spaceLeft < w)) {
    left = aR + gap
    top = clamp(aT - 4, pad, maxTop) // 与锚点顶端对齐（略上移 4px 观感更自然）
  } else if (spaceLeft >= w) {
    left = aL - gap - w
    top = clamp(aT - 4, pad, maxTop)
  } else {
    // ---- 2) 两侧都放不下（窄屏或超长名字）：放到锚点下方 / 上方，水平对齐锚点中心 ----
    left = clamp((aL + aR) / 2 - w / 2, pad, maxLeft)
    const below = aB + gap
    const above = aT - gap - h
    if (below <= maxTop) top = below
    else if (above >= pad) top = above
    else top = clamp(aT - 4, pad, maxTop)
  }
  left = clamp(left, pad, maxLeft)

  // ---- 3) 硬校验：绝不与锚点矩形相交（含 gap 缓冲）----
  const hitsAnchor = (l: number, t: number) =>
    l < aR + gap && l + w > aL - gap && t < aB + gap && t + h > aT - gap
  if (hitsAnchor(left, top)) {
    const below = aB + gap
    const above = aT - gap - h
    let placed = false
    if (below <= maxTop) {
      top = below
      placed = true
    } else if (above >= pad) {
      top = above
      placed = true
    }
    if (!placed) {
      // 上下也放不下（浮窗比剩余空间还高）：靠更宽的一侧水平边缘，宁可贴边也不压锚点
      left = spaceRight >= spaceLeft ? clamp(aR + gap, pad, maxLeft) : clamp(aL - gap - w, pad, maxLeft)
      top = clamp(aT, pad, maxTop)
    }
  }

  left = clamp(left, pad, maxLeft)
  top = clamp(top, pad, maxTop)

  // ---- 4) 最后一道：不盖住鼠标指针本身（鼠标可能停在名字右端/行内其它位置）----
  if (mx >= left - 4 && mx <= left + w + 4 && my >= top - 4 && my <= top + h + 4) {
    const below = my + gap
    const above = my - gap - h
    if (below <= maxTop) top = clamp(below, pad, maxTop)
    else if (above >= pad) top = clamp(above, pad, maxTop)
  }

  hoverX.value = Math.round(left)
  hoverY.value = Math.round(top)
  // 必须直接写回：上面为了测量把 left/top 临时改成了 0，若这次算出的坐标与上次相同，
  // Vue 认为绑定值没变就不会重写 style，浮窗会卡在左上角。
  el.style.left = hoverX.value + 'px'
  el.style.top = hoverY.value + 'px'
}

// 浮窗可见（hover 模式）时：渲染出真实尺寸后再定位（loading 小尺寸与加载后大尺寸都要重定位）
watch(
  () => [store.visible, store.mode, store.anchor],
  async () => {
    if (store.visible && store.mode === 'hover') {
      await nextTick()
      placeHover()
    }
  },
)

// 数据异步加载完成后浮窗会变大，必须按真实尺寸重新定位（初始只在 loading 小尺寸跑过一次）
watch(
  () => [data.value, loading.value, store.visible, store.mode],
  async () => {
    if (store.visible && store.mode === 'hover') {
      await nextTick()
      placeHover()
    }
  },
)

function onHoverViewportChange() {
  if (store.visible && store.mode === 'hover') placeHover()
}

// 在「人物档案」(プロフィール) 末尾追加「实装日期」一行：
// 数据取角色 JSON 顶层 release_date（原样，可能为空）；中文站标签显示「实装日期」，日文站显示「実装日」。
function withReleaseRow(rows: Cell[][]): Cell[][] {
  const d = data.value
  if (!d || !d.sections['プロフィール']) return rows
  // 実装日为空**不是**缺数据：一覧表该列留空 = 开服时即已实装的角色，
  // 空值本身携带含义，因此这一行必须照常显示（值留白），不能隐藏。
  const dateVal = d.release_date ?? ''
  const row: Cell[] = [
    { h: true, t: '実装日', zh: '实装日期' },
    { h: false, t: dateVal, zh: dateVal },
  ]
  return [...rows, row]
}

const allSections = computed(() => {
  if (!data.value) return []
  return SECTION_ORDER.filter((k) => data.value!.sections[k]).map((k) => {
    const sec = data.value!.sections[k]
    return {
      key: k,
      label: sec.label,
      rows: k === 'プロフィール' ? withReleaseRow(sec.rows) : sec.rows,
    }
  })
})

// 星阶成长说明：如「基本ステータス(⭐︎1時点)※⭐︎1つ増加毎に+50%、⭐︎5で⭐︎1時点の3倍」
// 这是分段「标题」里附加的说明，占空间大。小浮窗（hover 预览）隐藏，放大固定窗再显示。
function stripStarNote(label: string): string {
  const i = label.indexOf('(⭐︎1時点)')
  if (i < 0) return label
  return label.slice(0, i).trim()
}

// 小浮窗去除「フレーバーテキスト」行（成人简介，镜像站不需要）：
// 它在プロフィール 内以「单行 th(cs>=2) 表头」+「紧随其值行」出现。
function cleanHoverRows(rows) {
  const out = []
  let skipNext = false
  for (let i = 0; i < rows.length; i++) {
    if (skipNext) { skipNext = false; continue }
    const row = rows[i]
    const first = row[0]
    if (first && first.h && (first.cs || 1) >= 2 && row.length === 1) {
      const next = rows[i + 1]
      const nextFirst = next && next[0]
      const hasValue = nextFirst && !nextFirst.h
      if (!hasValue) continue                                  // 独立子标题（如 SDキャラ 空行）→ 丢弃
      if ((first.t || '').trim() === 'フレーバーテキスト') { skipNext = true; continue }  // 表头 + 值行一起丢弃
    }
    out.push(row)
  }
  return out
}

// 小浮窗的基础属性：只保留表头 + 100 级那一行（其余等级隐藏），避免 11 行等级数据撑爆小浮窗
function simplifyBasicStatus(rows) {
  if (!rows.length) return rows
  const header = rows[0]
  const lv100 = rows.find((r) => r[0] && !r[0].h && (r[0].t || '').trim() === '100')
  if (!lv100) return rows
  return [header, lv100]
}

// hover 预览仅展示指定分段（剔除フレーバーテキスト；并从小浮窗分段标题剔除星阶成长说明；基础属性仅留 100 级）
const hoverSections = computed(() =>
  allSections.value
    .filter((s) => HOVER_SECTIONS.includes(s.key))
    .map((s) => {
      let rows = cleanHoverRows(s.rows)
      if (s.key === '基本ステータス') rows = simplifyBasicStatus(rows)
      return { ...s, label: stripStarNote(s.label), rows }
    })
)

// 左栏：人物档案 + 详细属性；右栏：基础属性 + 必杀技 + 固有效果
const hoverLeft = computed(() => hoverSections.value.filter((s) => HOVER_LEFT.includes(s.key)))
const hoverRight = computed(() => hoverSections.value.filter((s) => HOVER_RIGHT.includes(s.key)))

// 三列分配（固定窗用）：档案+获取 / 基础+详细属性 / 必杀技+固有效果
const columns = computed(() => {
  const cols: { [k: number]: typeof allSections.value } = { 0: [], 1: [], 2: [] }
  const colOf = (key: string) =>
    key === 'プロフィール' || key === '入手方法' ? 0 : key === '基本ステータス' || key === '詳細ステータス' ? 1 : 2
  for (const s of allSections.value) cols[colOf(s.key)].push(s)
  return [cols[0], cols[1], cols[2]]
})

// 这些「行标签」的值是固有名词（本名 / 声优 / 画师），项目要求保留日文原名：
// 角色详情页已按此处理，浮窗这里再兜一层——即使 JSON 里带了 zh，也只显示 t。
const RETAIN_JA_ROWS = new Set(['本名', 'CV', 'イラスト', 'イラストレーター', '声優', '原画'])

function rowKeepsJa(row: Cell[] | undefined): boolean {
  const head = row && row[0]
  return !!(head && head.h && RETAIN_JA_ROWS.has((head.t || '').trim()))
}

function cellText(cell: Cell, row?: Cell[]): string {
  if (row && rowKeepsJa(row) && !cell.h) return cell.t
  return isZh() ? cell.zh || cell.t : cell.t
}

function charSectionZh(label: string): string {
  if (!isZh()) return label
  const map = (siteTerms as { char_sections?: Record<string, string> }).char_sections || {}
  if (map[label]) return map[label]
  for (const key of SECTION_ORDER) {
    if (label.startsWith(key) && map[key]) return map[key] + label.slice(key.length)
  }
  return label
}

async function load(name: string) {
  if (cache.has(name)) {
    data.value = cache.get(name)!
    return
  }
  loading.value = true
  loadError.value = false
  data.value = null
  try {
    const res = await fetch(withBase(`/data/char/${encodeURIComponent(name)}.json`))
    if (!res.ok) throw new Error(String(res.status))
    const json = (await res.json()) as CharData
    cache.set(name, json)
    if (store.name === name) data.value = json
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

// 名字变化或浮窗重新可见时都（重新）加载，避免切角色时内容残留旧数据
watch(
  () => [store.name, store.visible] as const,
  ([name, vis]) => {
    if (name && vis) load(name)
  },
)

function onMaskClick() {
  store.close()
}
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') store.close()
}
function onModalEnter() {
  if (store.mode === 'pinned') store.cancelHide()
}
function onModalLeave() {
  if (store.mode === 'pinned') store.scheduleHide()
}
function startDrag(e: MouseEvent) {
  if (!store.pinned || (e.target as HTMLElement).closest('button, a')) return
  dragging.value = true
  const rect = (e.currentTarget as HTMLElement).parentElement!.getBoundingClientRect()
  dragOffset.dx = e.clientX - rect.left
  dragOffset.dy = e.clientY - rect.top
  e.preventDefault()
}
function onDrag(e: MouseEvent) {
  if (!dragging.value) return
  store.setPos(e.clientX - dragOffset.dx, e.clientY - dragOffset.dy)
}
function stopDrag() {
  dragging.value = false
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  window.addEventListener('resize', onHoverViewportChange)
  window.addEventListener('scroll', onHoverViewportChange, true)
})
onUnmounted(() => {
  window.removeEventListener('resize', onHoverViewportChange)
  window.removeEventListener('scroll', onHoverViewportChange, true)
})
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.documentElement.classList.remove(SHEET_OPEN_CLASS)
})

const detailHref = computed(() => {
  const prefix = lang.value.startsWith('zh') ? '/zh/' : '/ja/'
  return withBase(`/${prefix.slice(1)}characters/${encodeURIComponent(store.name)}.html`)
})

const avatarSrc = computed(() => (data.value?.icon ? withBase(`/${data.value.icon}`) : ''))
</script>

<template>
  <Teleport to="body">
    <template v-if="store.visible">
      <!-- ===== 固定大窗（点击角色名/头像触发）：全部信息、居中、可拖动、带遮罩 ===== -->
      <template v-if="store.mode === 'pinned'">
        <div class="char-modal-mask" :class="{ transparent: store.pinned }" @click="onMaskClick"></div>
        <div class="char-modal" :style="modalStyle" @mouseenter="onModalEnter" @mouseleave="onModalLeave">
          <div class="char-modal-header" :style="{ cursor: store.pinned ? 'move' : 'default' }" @mousedown="startDrag">
            <img v-if="avatarSrc" class="char-avatar" :src="avatarSrc" :alt="store.name" loading="lazy" />
            <span class="title">{{ displayName }}</span>
            <span v-if="data?.rarity" class="rarity-badge" :class="data.rarity">{{ data.rarity }}</span>
            <span class="spacer"></span>
            <span v-if="store.pinned" class="hint">{{ t('modal.dragHint') }}</span>
            <div class="char-modal-actions">
              <a class="fullpage" :href="detailHref" target="_blank" rel="noopener noreferrer" @click="store.close()">{{ t('modal.fullPage') }}</a>
              <button @click="store.togglePin()">{{ store.pinned ? t('modal.unpin') : t('modal.pin') }}</button>
              <button @click="store.close()">{{ t('modal.close') }}</button>
            </div>
          </div>
          <div class="char-modal-body">
            <div v-if="loading" class="char-modal-loading">{{ t('modal.loading') }}</div>
            <div v-else-if="loadError" class="char-modal-error">{{ t('modal.error') }}</div>
            <div v-else-if="data" class="sections">
              <div v-for="(col, ci) in columns" :key="ci" class="column">
                <div v-for="sec in col" :key="sec.key" class="section">
                  <h5>{{ charSectionZh(sec.label) }}</h5>
                  <table>
                    <tbody>
                      <tr v-for="(row, ri) in sec.rows" :key="ri">
                        <component
                          :is="cell.h ? 'th' : 'td'"
                          v-for="(cell, i) in row"
                          :key="i"
                          :colspan="cell.cs"
                          :rowspan="cell.rs"
                          :class="{ 'long-text': cellText(cell, row).length > 60 }"
                          >{{ cellText(cell, row) }}</component
                        >
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- ===== hover 预览小窗：头像 + 4 个分段，贴着名字/头像，不遮挡 ===== -->
      <template v-else>
        <div class="char-hover" ref="hoverEl" :style="hoverStyle" @mouseenter="onModalEnter" @mouseleave="onModalLeave">
          <div class="char-hover-header">
            <img v-if="avatarSrc" class="char-avatar" :src="avatarSrc" :alt="store.name" loading="lazy" />
            <span class="title">{{ displayName }}</span>
            <span v-if="data?.rarity" class="rarity-badge" :class="data.rarity">{{ data.rarity }}</span>
          </div>
          <div class="char-hover-body">
            <div v-if="loading" class="char-modal-loading">{{ t('modal.loading') }}</div>
            <div v-else-if="loadError" class="char-modal-error">{{ t('modal.error') }}</div>
            <template v-else-if="data">
              <div class="hover-col">
                <section v-for="sec in hoverLeft" :key="sec.key" class="section">
                  <h5>{{ charSectionZh(sec.label) }}</h5>
                  <table>
                    <tbody>
                      <tr v-for="(row, ri) in sec.rows" :key="ri">
                        <component
                          :is="cell.h ? 'th' : 'td'"
                          v-for="(cell, i) in row"
                          :key="i"
                          :colspan="cell.cs"
                          :rowspan="cell.rs"
                          :class="{ 'long-text': cellText(cell, row).length > 60 }"
                          >{{ cellText(cell, row) }}</component
                        >
                      </tr>
                    </tbody>
                  </table>
                </section>
              </div>
              <div class="hover-col">
                <section v-for="sec in hoverRight" :key="sec.key" class="section">
                  <h5>{{ charSectionZh(sec.label) }}</h5>
                  <table>
                    <tbody>
                      <tr v-for="(row, ri) in sec.rows" :key="ri">
                        <component
                          :is="cell.h ? 'th' : 'td'"
                          v-for="(cell, i) in row"
                          :key="i"
                          :colspan="cell.cs"
                          :rowspan="cell.rs"
                          :class="{ 'long-text': cellText(cell, row).length > 60 }"
                          >{{ cellText(cell, row) }}</component
                        >
                      </tr>
                    </tbody>
                  </table>
                </section>
              </div>
              <div class="char-hover-hint">{{ t('modal.clickToPin') }}</div>
            </template>
          </div>
        </div>
      </template>
    </template>
  </Teleport>
</template>

<style scoped>
.column { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.section { min-width: 0; }
.char-modal-header .char-avatar {
  width: 34px; height: 34px; border-radius: 8px;
  object-fit: cover; border: 1px solid rgba(255, 255, 255, 0.4);
  flex: 0 0 auto; background: rgba(255, 255, 255, 0.15);
}
/* hover 预览小窗 */
.char-hover {
  position: fixed;
  z-index: 260;            /* 高于表格页面内全屏(250)，使全屏表格里的角色也能正常显示悬停预览 */
  /* 首帧兜底：真实宽/高上限由 placeHover() 按锚点周围可用空间写成内联 max-width /
     max-height（侧边够宽就贴边用满那一侧，否则铺满视口宽度放到锚点上下）。写死
     680px / 84vh 会让两栏各只剩 ~320px，长文本折行过多再被高度裁掉。 */
  max-width: min(680px, 94vw);
  background: var(--vp-c-bg, #fff);
  color: var(--vp-c-text-1, #1b1b1f);
  border: 1px solid var(--vp-c-divider, #e2e2e3);
  border-radius: 10px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
  padding: 10px 12px;
  pointer-events: none; /* 不拦截鼠标，离开名字/头像即消失 */
  font-size: 14px;            /* 与页面正文（.mirror-content 14px）保持一致 */
  max-height: 84vh;           /* 首帧兜底，真实上限由 placeHover() 写内联 max-height */
  overflow: hidden;           /* 小浮窗一页展示完，不出现滚轮 */
}
.char-hover-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.char-hover-header .char-avatar {
  width: 28px; height: 28px; border-radius: 6px; object-fit: cover; flex: 0 0 auto;
  border: 1px solid var(--vp-c-divider, #e2e2e3);
}
.char-hover-header .title { font-weight: 600; font-size: 14px; }
.char-hover-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}
.char-hover-body > .char-modal-loading,
.char-hover-body > .char-modal-error,
.char-hover-body > .char-hover-hint { grid-column: 1 / -1; }
.hover-col { min-width: 0; }
.char-hover-body .section { margin-bottom: 10px; }
.char-hover-body .section h5 {
  margin: 0 0 4px; font-size: 12px; color: var(--vp-c-text-2, #57606a);
  border-left: 3px solid var(--vp-c-brand-1, #3451b2); padding-left: 6px;
}
.char-hover-body table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.char-hover-body th,
.char-hover-body td {
  border: 1px solid var(--vp-c-divider, #e2e2e3);
  padding: 3px 7px;
  text-align: left;
  vertical-align: top;
  word-break: break-word;
}
.char-hover-body th {
  background: var(--vp-c-bg-soft, #f6f6f7);
  font-weight: 600;
  white-space: nowrap;
}
/* 单元格文本里的 \n = 原 wiki 的换行（浮窗 zh 由 i18n 块级译文带出排版）。
   pre-line：保留换行、合并多余空白、超长仍自动折行（不会横向溢出）。 */
.char-hover-body td,
.char-modal-body td { white-space: pre-line; }
.char-hover-body td.long-text { white-space: pre-line; }
.char-hover-hint {
  margin-top: 8px; font-size: 14px; font-weight: 700;
  color: var(--vp-c-brand-1, #3451b2);
  text-align: center; opacity: 1;
  background: var(--vp-c-bg-soft, #f6f6f7);
  border-radius: 6px; padding: 6px 8px;
}
</style>
