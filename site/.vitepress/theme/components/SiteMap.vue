<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { useI18n } from '../i18n'

interface SiteMapData {
  categories: { key: string; label: string; pages: { title: string; href: string; synced?: string }[] }[]
}

const { t } = useI18n()
const data = ref<SiteMapData | null>(null)

onMounted(async () => {
  const res = await fetch(withBase('data/sitemap.json'))
  data.value = await res.json()
})
</script>

<template>
  <div v-if="data">
    <div v-for="cat in data.categories" :key="cat.key" class="sitemap-cat">
      <h3>{{ cat.label }}（{{ cat.pages.length }} {{ t('sitemap.pages') }}）</h3>
      <ul>
        <li v-for="p in cat.pages" :key="p.href">
          <a :href="p.href">{{ p.title }}</a>
          <span v-if="p.synced" style="color: var(--vp-c-text-2); font-size: 11px">（{{ p.synced }}）</span>
        </li>
      </ul>
    </div>
  </div>
</template>
