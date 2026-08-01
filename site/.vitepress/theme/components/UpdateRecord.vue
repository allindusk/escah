<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { enhanceTables } from '../tableEnhancer'
// 页面更新时间数据由 sitegen 在 sync-site 阶段生成（grouped: guide / characters）
import pageTimes from '../.gen-data/page-times.json'
// 镜像站版本更新记录（手工维护）
import changelog from '../.gen-data/changelog.json'

interface PageTime {
  ja: string
  zh: string
  wiki: string
  mirror: string
}
const data = pageTimes as unknown as { guide: PageTime[]; characters: PageTime[] }
const versions = (changelog as { versions: { version: string; date: string; changes: string[] }[] }).versions
const root = ref<HTMLElement | null>(null)

onMounted(() => {
  if (root.value) enhanceTables(root.value)
})
</script>

<template>
  <div ref="root" class="mirror-content update-record">
    <nav class="update-toc">
      <a href="#mirror-changelog">镜像站更新记录</a>
      <a href="#guide-updates">攻略页面更新记录</a>
      <a href="#character-updates">角色页面更新记录</a>
    </nav>

    <section class="mirror-changelog">
      <h2 id="mirror-changelog">镜像站更新记录</h2>
      <div v-for="v in versions" :key="v.version" class="changelog-item">
        <div class="changelog-head">
          <span class="changelog-ver">v{{ v.version }}</span>
          <span class="changelog-date">{{ v.date }}</span>
        </div>
        <ul class="changelog-list">
          <li v-for="(c, i) in v.changes" :key="i">{{ c }}</li>
        </ul>
      </div>
    </section>

    <section>
      <h2 id="guide-updates">攻略页面更新记录</h2>
      <table>
        <thead>
          <tr>
            <th>页面日文名</th>
            <th>页面中文名</th>
            <th>原WIKI站点最后编辑时间</th>
            <th>镜像站点更新时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in data.guide" :key="r.ja">
            <td>{{ r.ja }}</td>
            <td>{{ r.zh }}</td>
            <td>{{ r.wiki || '—' }}</td>
            <td>{{ r.mirror || '—' }}</td>
          </tr>
        </tbody>
      </table>

      <h2 id="character-updates">角色页面更新记录</h2>
      <table>
        <thead>
          <tr>
            <th>页面日文名</th>
            <th>页面中文名</th>
            <th>原WIKI站点最后编辑时间</th>
            <th>镜像站点更新时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in data.characters" :key="r.ja">
            <td>{{ r.ja }}</td>
            <td>{{ r.zh }}</td>
            <td>{{ r.wiki || '—' }}</td>
            <td>{{ r.mirror || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.update-toc {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 1.4em;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg-soft);
}
.update-toc a {
  font-weight: 600;
  color: var(--vp-c-brand-1);
  text-decoration: none;
}
.update-toc a:hover {
  text-decoration: underline;
}
.update-record h2 {
  margin-top: 1.4em;
  scroll-margin-top: 80px;
}
.update-record table {
  margin: 0.6em 0 1.2em;
}
.mirror-changelog h2 {
  margin-top: 0;
}
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
