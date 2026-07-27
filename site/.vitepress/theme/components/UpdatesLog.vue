<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from '../i18n'
import updatesData from '../.gen-data/updates.json'

interface UpdatesData {
  lastRun: string | null
  watchCount: number
  changed: { date: string; pages: { name: string; status: string }[] }[]
}

const { t } = useI18n()
// 直接 import 静态数据：SSR 与 CSR 都能渲染，消除首屏空白
const data = ref<UpdatesData | null>(updatesData as UpdatesData)
</script>

<template>
  <div v-if="data" class="updates-log">
    <div class="home-stats" style="margin: 0 0 18px">
      <div class="stat" style="color: var(--vp-c-text-1)"><b>{{ data.watchCount }}</b><span style="color: var(--vp-c-text-2)">{{ t('updates.watchPages') }}</span></div>
      <div class="stat" style="color: var(--vp-c-text-1)"><b>{{ data.changed.length }}</b><span style="color: var(--vp-c-text-2)">{{ t('updates.changed') }}</span></div>
      <div class="stat" style="color: var(--vp-c-text-1)"><b style="font-size: 16px">{{ data.lastRun || '-' }}</b><span style="color: var(--vp-c-text-2)">{{ t('updates.lastRun') }}</span></div>
    </div>
    <div v-if="!data.changed.length" class="charlist-empty">{{ t('updates.noChanges') }}</div>
    <div v-for="group in data.changed" :key="group.date" style="margin-bottom: 16px">
      <h3 style="font-size: 14px; margin: 0 0 8px">{{ group.date }}</h3>
      <div class="recent-updates">
        <div v-for="p in group.pages" :key="p.name" class="item">
          <span class="date">{{ p.status }}</span>
          <span>{{ p.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
