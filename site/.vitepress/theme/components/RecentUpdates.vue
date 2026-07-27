<script setup lang="ts">
import { computed } from 'vue'
import updatesData from '../.gen-data/updates.json'

interface UpdatesData {
  changed: { date: string; pages: { name: string; status: string }[] }[]
  hrefs?: Record<string, string>
}

const props = withDefaults(defineProps<{ limit?: number }>(), { limit: 8 })
// 直接 import 静态数据并同步计算，SSR 与 CSR 都能渲染
const items = computed<{ date: string; name: string; href: string }[]>(() => {
  const data = updatesData as UpdatesData
  const flat: { date: string; name: string; href: string }[] = []
  for (const g of data.changed) {
    for (const p of g.pages) {
      flat.push({ date: g.date, name: p.name, href: (data.hrefs && data.hrefs[p.name]) || '#' })
    }
  }
  return flat.slice(0, props.limit)
})
</script>

<template>
  <div class="recent-updates">
    <div v-for="it in items" :key="it.date + it.name" class="item">
      <span class="date">{{ it.date }}</span>
      <a v-if="it.href !== '#'" :href="it.href">{{ it.name }}</a>
      <span v-else>{{ it.name }}</span>
    </div>
  </div>
</template>
