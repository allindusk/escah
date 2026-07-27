<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { enhanceTables } from '../tableEnhancer'
// 页面更新时间数据由 sitegen 在 sync-site 阶段生成（grouped: guide / characters）
import pageTimes from '../.gen-data/page-times.json'

interface PageTime {
  ja: string
  zh: string
  wiki: string
  mirror: string
}
const data = pageTimes as unknown as { guide: PageTime[]; characters: PageTime[] }
const root = ref<HTMLElement | null>(null)

onMounted(() => {
  if (root.value) enhanceTables(root.value)
})
</script>

<template>
  <div ref="root" class="mirror-content update-record">
    <section>
      <h2>攻略页面</h2>
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

      <h2>角色页面</h2>
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
.update-record h2 {
  margin-top: 1.4em;
}
.update-record table {
  margin: 0.6em 0 1.2em;
}
</style>
