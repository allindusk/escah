<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

interface UpdatesData {
  changed: { date: string; pages: { name: string; status: string }[] }[]
}

const props = withDefaults(defineProps<{ limit?: number }>(), { limit: 8 })
const items = ref<{ date: string; name: string; href: string }[]>([])

onMounted(async () => {
  const res = await fetch(withBase('data/updates.json'))
  const data: UpdatesData & { hrefs?: Record<string, string> } = await res.json()
  const flat: { date: string; name: string; href: string }[] = []
  for (const g of data.changed) {
    for (const p of g.pages) {
      flat.push({ date: g.date, name: p.name, href: (data.hrefs && data.hrefs[p.name]) || '#' })
    }
  }
  items.value = flat.slice(0, props.limit)
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
