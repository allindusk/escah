<script setup lang="ts">
import { computed } from 'vue'
import { useData } from 'vitepress'
import { useI18n } from '../i18n'

const { frontmatter } = useData()
const { t } = useI18n()

const meta = computed(() => (frontmatter.value as any).meta as
  | { sourceUrl?: string; sourceUpdated?: string; synced?: string; reviewed?: boolean; translated?: boolean }
  | undefined)
</script>

<template>
  <div v-if="meta" class="meta-bar">
    <span v-if="meta.sourceUpdated">{{ t('meta.sourceUpdated') }}：{{ meta.sourceUpdated }}</span>
    <span v-if="meta.synced">{{ t('meta.synced') }}：{{ meta.synced }}</span>
    <span v-if="meta.translated" class="badge" :class="meta.reviewed ? 'reviewed' : 'mt'">
      {{ meta.reviewed ? t('meta.reviewed') : t('meta.mt') }}
    </span>
    <span v-else class="badge mt">{{ t('meta.untranslated') }}</span>
    <a v-if="meta.sourceUrl" :href="meta.sourceUrl" target="_blank" rel="noopener">{{ t('meta.viewSource') }} ↗</a>
  </div>
</template>
