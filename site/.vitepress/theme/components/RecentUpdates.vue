<script setup lang="ts">
import { computed } from 'vue'
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
  pages: PageRow[]
}

const props = withDefaults(defineProps<{ limit?: number }>(), { limit: 8 })
const items = computed<{ date: string; name: string; zhName: string; slug: string }[]>(() => {
  const data = updatesData as UpdatesData
  return data.pages
    .slice()
    .sort((a, b) => (a.date < b.date ? 1 : -1))
    .slice(0, props.limit)
    .map((p) => ({ date: p.date, name: p.name, zhName: p.zhName, slug: p.slug }))
})
</script>

<template>
  <div class="recent-updates">
    <div v-for="it in items" :key="it.slug" class="item">
      <span class="date">{{ it.date }}</span>
      <a :href="`./${it.slug}.html`">{{ it.zhName }}</a>
    </div>
  </div>
</template>
