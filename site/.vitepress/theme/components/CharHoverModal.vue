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

// hover 预览定位：依据真实渲染尺寸在「右 → 左 → 下 → 上 → 左缘兜底」间择优，
// 最终夹回视口内（绝不越界；名字/头像在右缘时浮窗改放下方或贴左缘，避免遮挡）。
const hoverEl = ref<HTMLElement | null>(null)
const hoverX = ref(0)
const hoverY = ref(0)
const hoverStyle = computed(() => ({ left: hoverX.value + 'px', top: hoverY.value + 'px' }))

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v))
}

// 定位规则：把「不盖住鼠标」当成必须校验的硬约束，而不是靠分支顺序碰运气。
//
// 之前反复出错的原因：只算了水平方向，垂直方向 top 取 min(a.top,my)-4，
// 而浮窗最高可达 94vh，鼠标几乎必然落在浮窗的纵向区间内；此时只要水平
// 兜底把浮窗放到了 mx 附近，就会盖住鼠标。
//
// 现在的做法：
//   1) 先在「鼠标左侧空间」与「鼠标右侧空间」里选放得下且更宽敞的一侧，
//      使浮窗整体位于鼠标的一侧（left+w <= mx-gap 或 left >= mx+gap）。
//   2) 垂直照常对齐锚点/鼠标顶部并夹回视口。
//   3) 最后做一次显式校验：若鼠标点仍落在浮窗矩形内（含 gap 外扩），
//      则把浮窗在垂直方向推到鼠标上方或下方；若上下都塞不下，
//      再退一步把它强行贴到鼠标较宽的那一侧水平边缘。
function placeHover() {
  const el = hoverEl.value
  const a = store.anchor as HoverAnchor | null
  if (!el) return
  const vw = window.innerWidth
  const vh = window.innerHeight
  const gap = 12
  const pad = 8
  const r = el.getBoundingClientRect()
  const w = r.width
  const h = r.height
  const mx = a ? a.mx : Math.round(vw / 2)
  const my = a ? a.my : Math.round(vh / 2)

  const maxLeft = Math.max(pad, vw - pad - w)
  const maxTop = Math.max(pad, vh - pad - h)

  // ---- 水平：优先整体落在鼠标的某一侧 ----
  const spaceLeft = mx - gap - pad          // 鼠标左边可用宽度
  const spaceRight = vw - pad - (mx + gap)  // 鼠标右边可用宽度
  const fitsLeft = w <= spaceLeft
  const fitsRight = w <= spaceRight

  let left: number
  if (!a) {
    left = (vw - w) / 2
  } else if (fitsRight && (!fitsLeft || spaceRight >= spaceLeft)) {
    left = mx + gap
  } else if (fitsLeft) {
    left = mx - gap - w
  } else {
    // 两侧都塞不下（浮窗过宽）：靠更宽的一侧对齐，交由后面的垂直避让兜底
    left = spaceRight >= spaceLeft ? maxLeft : pad
  }
  left = clamp(left, pad, maxLeft)

  // ---- 垂直：贴锚点/鼠标顶部 ----
  let top = (a ? Math.min(a.top, my) : my) - 4
  top = clamp(top, pad, maxTop)

  // ---- 兜底校验：鼠标绝不能落在浮窗内 ----
  const hitsX = mx >= left - gap && mx <= left + w + gap
  const hitsY = my >= top - gap && my <= top + h + gap
  if (a && hitsX && hitsY) {
    const above = my - gap - pad   // 鼠标上方可用高度
    const below = vh - pad - (my + gap)
    if (h <= below) {
      top = my + gap               // 放到鼠标下方
    } else if (h <= above) {
      top = my - gap - h           // 放到鼠标上方
    } else {
      // 上下都放不下：强行水平让开到更宽的一侧
      left = spaceRight >= spaceLeft ? clamp(mx + gap, pad, maxLeft) : clamp(mx - gap - w, pad, maxLeft)
    }
    top = clamp(top, pad, maxTop)
  }

  hoverX.value = Math.round(left)
  hoverY.value = Math.round(top)
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
            <a class="fullpage" :href="detailHref" target="_blank" rel="noopener noreferrer" @click="store.close()">{{ t('modal.fullPage') }}</a>
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
  z-index: 260;            /* 高于表格页面内全屏(250)，使全屏表格里的角色也能正常显示悬停预览 */
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
