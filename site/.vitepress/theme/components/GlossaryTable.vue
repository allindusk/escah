<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { useI18n } from '../i18n'

const { t } = useI18n()
const rows = ref<{ ja: string; zh: string; note?: string }[]>([])
const keyword = ref('')

const filtered = computed(() => {
  const q = keyword.value.trim()
  if (!q) return rows.value
  return rows.value.filter((r) => r.ja.includes(q) || r.zh.includes(q))
})

onMounted(async () => {
  const res = await fetch(withBase('data/glossary.json'))
  rows.value = await res.json()
})
</script>

<template>
  <div>
    <input v-model="keyword" class="filter-input" :placeholder="t('glossary.filter')" />
    <table class="glossary-table">
      <thead>
        <tr><th>{{ t('glossary.ja') }}</th><th>{{ t('glossary.zh') }}</th><th>{{ t('glossary.note') }}</th></tr>
      </thead>
      <tbody>
        <tr v-for="r in filtered" :key="r.ja">
          <td>{{ r.ja }}</td>
          <td>{{ r.zh }}</td>
          <td>{{ r.note || '' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
