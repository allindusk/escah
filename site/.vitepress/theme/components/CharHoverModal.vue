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
  sections: Record<string, Section>
}

const SECTION_ORDER = ['プロフィール', '入手方法', '基本ステータス', '詳細ステータス', '必殺技', '固有効果']
// hover 预览只展示轻量分段：头像(头部) + 以下 4 个分段；基本ステータス 内容多，仅放大浮窗显示
const HOVER_SECTIONS = ['プロフィール', '詳細ステータス', '必殺技', '固有効果']
const HOVER_LEFT = ['プロフィール', '詳細ステータス']   // 角色信息 + 属性
const HOVER_RIGHT = ['必殺技', '固有効果']                              // 必杀技 + 固有效果
const HOVER_WIDTH = 760
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

// hover 预览定位：先按锚点初步定位，再依据真实渲染尺寸夹取到视口内（绝不越界）
const hoverEl = ref<HTMLElement | null>(null)
const hoverX = ref(0)
const hoverY = ref(0)
const hoverStyle = computed(() => ({ left: hoverX.value + 'px', top: hoverY.value + 'px' }))

function placeHoverInitial() {
  const a = store.anchor as HoverAnchor | null
  if (!a) {
    hoverX.value = Math.max(8, (window.innerWidth - HOVER_WIDTH) / 2)
    hoverY.value = 40
    return
  }
  const vw = window.innerWidth
  const gap = 10
  let left = a.right + gap // 优先放右侧
  let top = a.top
  if (left + HOVER_WIDTH > vw - 8) left = a.left - HOVER_WIDTH - gap // 右侧放不下→放左侧
  if (left < 8) {
    // 左右都放不下→放到下方（不遮挡名字/头像）
    left = a.left
    top = a.bottom + gap
  }
  hoverX.value = Math.max(8, left)
  hoverY.value = Math.max(8, top)
}

// 用真实尺寸把浮窗夹回视口内（宽度可能因 max-width:96vw / 网格而小于 HOVER_WIDTH，
// 高度可达 94vh，须保证右下角不超出视口）
function clampHoverToViewport() {
  const el = hoverEl.value
  if (!el) return
  const r = el.getBoundingClientRect()
  const vw = window.innerWidth
  const vh = window.innerHeight
  let left = r.left
  let top = r.top
  if (r.right > vw - 8) left = vw - 8 - r.width
  if (r.bottom > vh - 8) top = vh - 8 - r.height
  if (left < 8) left = 8
  if (top < 8) top = 8
  hoverX.value = Math.round(left)
  hoverY.value = Math.round(top)
}

watch(
  () => [store.visible, store.mode, store.anchor],
  async () => {
    if (store.visible && store.mode === 'hover') {
      placeHoverInitial()
      await nextTick()
      clampHoverToViewport()
    }
  },
)

// 数据异步加载完成后，浮窗内容会变大（更高/更宽）——必须重新夹取视口，
// 否则膨胀后的浮窗底部/右侧会越出浏览器窗口，导致内容看不到。
// （初始 clamp 只在 loading 小尺寸时跑过一次，加载完即失效）
watch(
  () => [data.value, loading.value, store.visible, store.mode],
  async () => {
    if (store.visible && store.mode === 'hover') {
      await nextTick()
      clampHoverToViewport()
    }
  },
)

function onHoverViewportChange() {
  if (store.visible && store.mode === 'hover') clampHoverToViewport()
}

const allSections = computed(() => {
  if (!data.value) return []
  return SECTION_ORDER.filter((k) => data.value!.sections[k]).map((k) => {
    const sec = data.value!.sections[k]
    return {
      key: k,
      label: sec.label,
      rows: sec.rows,
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

// hover 预览仅展示指定分段（剔除フレーバーテキスト；并从小浮窗分段标题剔除星阶成长说明）
const hoverSections = computed(() =>
  allSections.value
    .filter((s) => HOVER_SECTIONS.includes(s.key))
    .map((s) => ({ ...s, label: stripStarNote(s.label), rows: cleanHoverRows(s.rows) }))
)

// 左栏：角色信息 + 属性；右栏：必杀技 + 固有效果
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

function cellText(cell: Cell): string {
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
            <a class="fullpage" :href="detailHref">{{ t('modal.fullPage') }}</a>
            <button @click="store.togglePin()">{{ store.pinned ? t('modal.unpin') : t('modal.pin') }}</button>
            <button @click="store.close()">{{ t('modal.close') }}</button>
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
                          :class="{ 'long-text': cellText(cell).length > 60 }"
                          >{{ cellText(cell) }}</component
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
                          :class="{ 'long-text': cellText(cell).length > 60 }"
                          >{{ cellText(cell) }}</component
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
                          :class="{ 'long-text': cellText(cell).length > 60 }"
                          >{{ cellText(cell) }}</component
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
  z-index: 60;
  max-width: 96vw;
  background: var(--vp-c-bg, #fff);
  color: var(--vp-c-text-1, #1b1b1f);
  border: 1px solid var(--vp-c-divider, #e2e2e3);
  border-radius: 10px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
  padding: 10px 12px;
  pointer-events: none; /* 不拦截鼠标，离开名字/头像即消失 */
  font-size: 14px;            /* 与页面正文（.mirror-content 14px）保持一致 */
  max-height: 94vh;
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
.char-hover-body td.long-text { white-space: normal; }
.char-hover-hint {
  margin-top: 4px; font-size: 11px; color: var(--vp-c-text-3, #8b949e);
  text-align: center; opacity: 0.8;
}
</style>
