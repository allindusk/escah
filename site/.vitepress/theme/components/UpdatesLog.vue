<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from '../i18n'
import updatesData from '../.gen-data/updates.json'

interface PageRow {
  name: string
  zhName: string
  slug: string
  date: string
  type: 'new' | 'updated'
  latest: boolean
  progress: number | null
  wikiTime: string
  mirrorTime: string
}
interface UpdatesData {
  lastRun: string | null
  watchCount: number
  stats: { total: number; new: number; updated: number; latest: number; translated: number; untranslated: number }
  pages: PageRow[]
}

const { t } = useI18n()
const data = updatesData as UpdatesData
// 首页摘要卡：最近一期同步的页
const latestDate = computed(() => {
  const ds = data.pages.map((p) => p.date).filter(Boolean).sort().reverse()
  return ds[0] || ''
})
const latestPages = computed(() => data.pages.filter((p) => p.date === latestDate.value))
</script>

<template>
  <div v-if="data" class="updates-log">
    <div class="home-stats" style="margin: 0 0 18px">
      <div class="stat" style="color: var(--vp-c-text-1)"><b>{{ data.stats.total }}</b><span style="color: var(--vp-c-text-2)">{{ t('updates.totalPages') }}</span></div>
      <div class="stat" style="color: var(--vp-c-text-1)"><b>{{ data.stats.latest }}</b><span style="color: var(--vp-c-text-2)">{{ t('updates.latest') }}</span></div>
      <div class="stat" style="color: var(--vp-c-text-1)"><b>{{ data.stats.untranslated }}</b><span style="color: var(--vp-c-text-2)">{{ t('updates.untranslated') }}</span></div>
      <div class="stat" style="color: var(--vp-c-text-1)"><b style="font-size: 16px">{{ data.lastRun ? data.lastRun.slice(0, 10) : '-' }}</b><span style="color: var(--vp-c-text-2)">{{ t('updates.lastRun') }}</span></div>
    </div>
    <div v-if="!latestPages.length" class="charlist-empty">{{ t('updates.noChanges') }}</div>
    <div v-else>
      <h3 style="font-size: 14px; margin: 0 0 8px">{{ latestDate }}</h3>
      <div class="recent-updates">
        <div v-for="p in latestPages" :key="p.slug" class="item">
          <span class="date">{{ p.type === 'new' ? t('updates.new') : t('updates.updated') }}</span>
          <a :href="`./${p.slug}.html`">{{ p.zhName }}</a>
        </div>
      </div>
    </div>
  </div>
</template>
