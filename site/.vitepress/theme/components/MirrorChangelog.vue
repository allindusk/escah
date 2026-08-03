<script setup lang="ts">
// 首页「镜像站更新记录」模块：复用 theme/changelog.json（镜像站版本更新记录）。
// 注意：changelog.json 位于 theme/ 源码目录（入库），必须直接从源码 import，
// 不能走 .gen-data/（那里是 sync-site 生成、被 gitignore，会导致 CI 构建失败）。
import { computed } from 'vue'
import changelog from '../changelog.json'

interface Version {
  version: string
  date: string
  changes: string[]
}

const props = withDefaults(defineProps<{ limit?: number }>(), { limit: 2 })
const versions = computed<Version[]>(() => {
  const all = (changelog as { versions: Version[] }).versions || []
  return all.slice(0, props.limit)
})
</script>

<template>
  <div class="mirror-changelog">
    <div v-for="v in versions" :key="v.version" class="changelog-item">
      <div class="changelog-head">
        <span class="changelog-ver">v{{ v.version }}</span>
        <span class="changelog-date">{{ v.date }}</span>
      </div>
      <ul class="changelog-list">
        <li v-for="(c, i) in v.changes" :key="i">{{ c }}</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.changelog-item {
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 14px;
  background: var(--vp-c-bg-soft);
}
.changelog-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 6px;
}
.changelog-ver {
  font-size: 16px;
  font-weight: 700;
  color: var(--vp-c-brand-1);
}
.changelog-date {
  font-size: 13px;
  color: var(--vp-c-text-2);
}
.changelog-list {
  margin: 0;
  padding-left: 1.2em;
}
.changelog-list li {
  margin: 2px 0;
  line-height: 1.6;
}
</style>
