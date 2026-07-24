<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useData, withBase } from 'vitepress'
import { useI18n } from '../i18n'
import { charModalStore as store } from './charModalStore'

interface Cell { h: boolean; t: string; zh?: string; cs?: number; rs?: number }
interface Section { label: string; rows: Cell[][] }
interface CharData {
  name: string
  rarity?: string
  sections: Record<string, Section>
}

const SECTION_ORDER = ['プロフィール', '入手方法', '基本ステータス', '詳細ステータス', '必殺技', '固有効果']
const { t, isZh } = useI18n()
const { lang } = useData()

const data = ref<CharData | null>(null)
const loading = ref(false)
const loadError = ref(false)
const cache = new Map<string, CharData>()

// 拖动状态
const dragging = ref(false)
const dragOffset = { dx: 0, dy: 0 }

const modalStyle = computed(() => {
  if (store.x !== null && store.y !== null) {
    return { left: store.x + 'px', top: store.y + 'px', transform: 'none' }
  }
  return { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }
})

const sections = computed(() => {
  if (!data.value) return []
  return SECTION_ORDER.filter((k) => data.value!.sections[k]).map((k) => ({
    key: k,
    ...data.value!.sections[k],
  }))
})

// 三列分配：档案+获取 / 基础+详细属性 / 必杀技+固有效果
const columns = computed(() => {
  const cols: { [k: number]: typeof sections.value } = { 0: [], 1: [], 2: [] }
  const colOf = (key: string) =>
    key === 'プロフィール' || key === '入手方法' ? 0 : key === '基本ステータス' || key === '詳細ステータス' ? 1 : 2
  for (const s of sections.value) cols[colOf(s.key)].push(s)
  return [cols[0], cols[1], cols[2]]
})

function cellText(cell: Cell): string {
  return isZh.value ? cell.zh || cell.t : cell.t
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
    const res = await fetch(withBase(`data/char/${encodeURIComponent(name)}.json`))
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
  return withBase(`${prefix.slice(1)}characters/${encodeURIComponent(store.name)}.html`)
})
</script>

<template>
  <Teleport to="body">
    <template v-if="store.visible">
      <div class="char-modal-mask" :class="{ transparent: store.pinned }" @click="onMaskClick"></div>
      <div class="char-modal" :style="modalStyle" @mouseenter="store.cancelHide()" @mouseleave="store.scheduleHide()">
        <div class="char-modal-header" :style="{ cursor: store.pinned ? 'move' : 'default' }" @mousedown="startDrag">
          <span class="title">{{ store.name }}</span>
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
                <h5>{{ sec.label }}</h5>
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
  </Teleport>
</template>

<style scoped>
.column { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.section { min-width: 0; }
.char-modal-body .sections { overflow: hidden; }
.char-modal-body .column { max-height: calc(min(920px, 92vh) - 110px); overflow-y: auto; scrollbar-width: none; }
.char-modal-body .column::-webkit-scrollbar { display: none; }
</style>
