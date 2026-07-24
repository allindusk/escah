<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useData, withBase } from 'vitepress'
import { useI18n } from '../i18n'
import { charModalStore as store } from './charModalStore'

interface CharItem {
  name: string
  rarity: string
  icon: string
  meta: Record<string, string>
}

const { t, isZh } = useI18n()
const { lang } = useData()

const chars = ref<CharItem[]>([])
const rarity = ref('')
const keyword = ref('')
const sort = ref<'default' | 'rarity' | 'name'>('default')
const metaFilters = reactive<Record<string, string>>({})
const LS_KEY = 'escah-charlist-filters'

const metaKeys = computed(() => {
  const keys: string[] = []
  for (const c of chars.value) {
    for (const k of Object.keys(c.meta)) {
      if (!keys.includes(k)) keys.push(k)
    }
  }
  return keys.slice(0, 4)
})

const metaOptions = computed(() => {
  const opts: Record<string, string[]> = {}
  for (const k of metaKeys.value) {
    const set = new Set<string>()
    for (const c of chars.value) if (c.meta[k]) set.add(c.meta[k])
    opts[k] = [...set].sort()
  }
  return opts
})

const RARITY_ORDER: Record<string, number> = { SSR: 0, SR: 1, R: 2 }

const filtered = computed(() => {
  let list = chars.value
  if (rarity.value) list = list.filter((c) => c.rarity === rarity.value)
  const q = keyword.value.trim()
  if (q) list = list.filter((c) => c.name.includes(q))
  for (const [k, v] of Object.entries(metaFilters)) {
    if (v) list = list.filter((c) => c.meta[k] === v)
  }
  if (sort.value === 'rarity') {
    list = [...list].sort((a, b) => (RARITY_ORDER[a.rarity] ?? 9) - (RARITY_ORDER[b.rarity] ?? 9) || a.name.localeCompare(b.name, 'ja'))
  } else if (sort.value === 'name') {
    list = [...list].sort((a, b) => a.name.localeCompare(b.name, 'ja'))
  }
  return list
})

// 状态同步：URL query + localStorage
let syncing = false
function syncOut() {
  if (syncing) return
  const state = { rarity: rarity.value, keyword: keyword.value, sort: sort.value, meta: { ...metaFilters } }
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(state))
  } catch { /* ignore */ }
  const params = new URLSearchParams()
  if (rarity.value) params.set('r', rarity.value)
  if (keyword.value) params.set('q', keyword.value)
  if (sort.value !== 'default') params.set('s', sort.value)
  for (const [k, v] of Object.entries(metaFilters)) if (v) params.set('m_' + k, v)
  const qs = params.toString()
  history.replaceState(null, '', qs ? `?${qs}` : location.pathname)
  syncing = false
}
watch([rarity, keyword, sort, metaFilters], syncOut, { deep: true })

function syncIn() {
  syncing = true
  const params = new URLSearchParams(location.search)
  let saved: any = null
  try {
    saved = JSON.parse(localStorage.getItem(LS_KEY) || 'null')
  } catch { /* ignore */ }
  rarity.value = params.get('r') || saved?.rarity || ''
  keyword.value = params.get('q') || saved?.keyword || ''
  sort.value = (params.get('s') as any) || saved?.sort || 'default'
  const metaSaved = saved?.meta || {}
  for (const k of Object.keys(metaSaved)) metaFilters[k] = metaSaved[k]
  for (const [k, v] of params.entries()) if (k.startsWith('m_')) metaFilters[k.slice(2)] = v
}

function detailHref(name: string) {
  const prefix = lang.value.startsWith('zh') ? '/zh/' : '/ja/'
  return withBase(`${prefix.slice(1)}characters/${encodeURIComponent(name)}.html`)
}

onMounted(async () => {
  syncIn()
  const res = await fetch(withBase('data/characters.json'))
  chars.value = await res.json()
})
</script>

<template>
  <div class="charlist">
    <div class="charlist-toolbar">
      <div class="group">
        <label>{{ t('characters.rarity') }}</label>
        <select v-model="rarity">
          <option value="">{{ t('characters.all') }}</option>
          <option value="SSR">SSR</option>
          <option value="SR">SR</option>
          <option value="R">R</option>
        </select>
      </div>
      <div class="group" v-for="k in metaKeys" :key="k">
        <label>{{ k }}</label>
        <select v-model="metaFilters[k]">
          <option value="">{{ t('characters.all') }}</option>
          <option v-for="opt in metaOptions[k]" :key="opt" :value="opt">{{ opt }}</option>
        </select>
      </div>
      <div class="group">
        <input type="text" v-model="keyword" :placeholder="t('characters.searchPlaceholder')" />
      </div>
      <div class="group">
        <select v-model="sort">
          <option value="default">{{ t('characters.sortDefault') }}</option>
          <option value="rarity">{{ t('characters.sortRarity') }}</option>
          <option value="name">{{ t('characters.sortName') }}</option>
        </select>
      </div>
      <span class="charlist-count">{{ t('characters.count', { n: filtered.length }) }}</span>
    </div>

    <div v-if="filtered.length" class="char-grid">
      <div
        v-for="c in filtered"
        :key="c.name"
        class="char-card"
        @mouseenter="store.show(c.name)"
        @mouseleave="store.scheduleHide()"
        @click="store.show(c.name); store.togglePin()"
      >
        <span class="rarity-badge" :class="c.rarity">{{ c.rarity }}</span>
        <img :src="withBase(c.icon)" :alt="c.name" loading="lazy" />
        <span class="name">{{ c.name }}</span>
      </div>
    </div>
    <div v-else class="charlist-empty">{{ t('characters.empty') }}</div>
  </div>
</template>
