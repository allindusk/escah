<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
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
// hover 预览只展示的 5 项：头像(头部) + 以下 4 个分段
const HOVER_SECTIONS = ['プロフィール', '詳細ステータス', '必殺技', '固有効果']
const HOVER_WIDTH = 340
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

// hover 预览定位：贴在锚点（角色名/头像）旁边，不遮挡它
const hoverStyle = computed(() => {
  const a = store.anchor as HoverAnchor | null
  if (!a) return { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }
  const vw = window.innerWidth
  const vh = window.innerHeight
  const gap = 10
  let left = a.right + gap // 优先放右侧
  let top = a.top
  if (left + HOVER_WIDTH > vw - 8) left = a.left - HOVER_WIDTH - gap // 右侧放不下→放左侧
  if (left < 8) {
    // 左右都放不下→放到下方（不遮挡名字/头像）
    left = a.left
    top = a.bottom + gap
  }
  left = Math.min(Math.max(left, 8), vw - HOVER_WIDTH - 8)
  const maxTop = Math.max(8, vh - 360) // 预览窗最大高度约 360，超出则上移
  top = Math.min(Math.max(top, 8), maxTop)
  return { left: left + 'px', top: top + 'px', width: HOVER_WIDTH + 'px' }
})

const allSections = computed(() => {
  if (!data.value) return []
  return SECTION_ORDER.filter((k) => data.value!.sections[k]).map((k) => ({
    key: k,
    ...data.value!.sections[k],
  }))
})

// hover 预览仅展示指定分段
const hoverSections = computed(() => allSections.value.filter((s) => HOVER_SECTIONS.includes(s.key)))

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

watch(
  () => store.name,
  (name) => {
    if (name && store.visible) load(name)
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
        <div class="char-hover" :style="hoverStyle" @mouseenter="onModalEnter" @mouseleave="onModalLeave">
          <div class="char-hover-header">
            <img v-if="avatarSrc" class="char-avatar" :src="avatarSrc" :alt="store.name" loading="lazy" />
            <span class="title">{{ displayName }}</span>
            <span v-if="data?.rarity" class="rarity-badge" :class="data.rarity">{{ data.rarity }}</span>
          </div>
          <div class="char-hover-body">
            <div v-if="loading" class="char-modal-loading">{{ t('modal.loading') }}</div>
            <div v-else-if="loadError" class="char-modal-error">{{ t('modal.error') }}</div>
            <div v-else-if="data">
              <div v-for="sec in hoverSections" :key="sec.key" class="section">
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
              <div class="char-hover-hint">{{ t('modal.clickToPin') }}</div>
            </div>
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
  max-height: 70vh;
  overflow: auto;
  background: var(--vp-c-bg, #fff);
  color: var(--vp-c-text-1, #1b1b1f);
  border: 1px solid var(--vp-c-divider, #e2e2e3);
  border-radius: 10px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
  padding: 10px 12px;
  pointer-events: none; /* 不拦截鼠标，离开名字/头像即消失 */
}
.char-hover-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.char-hover-header .char-avatar {
  width: 28px; height: 28px; border-radius: 6px; object-fit: cover; flex: 0 0 auto;
  border: 1px solid var(--vp-c-divider, #e2e2e3);
}
.char-hover-header .title { font-weight: 600; font-size: 14px; }
.char-hover-body .section { margin-bottom: 10px; }
.char-hover-body .section h5 {
  margin: 0 0 4px; font-size: 12px; color: var(--vp-c-text-2, #57606a);
  border-left: 3px solid var(--vp-c-brand-1, #3451b2); padding-left: 6px;
}
.char-hover-hint {
  margin-top: 4px; font-size: 11px; color: var(--vp-c-text-3, #8b949e);
  text-align: center; opacity: 0.8;
}
</style>
