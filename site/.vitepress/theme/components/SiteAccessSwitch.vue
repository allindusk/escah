<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vitepress'

// 双部署访问域名：优先读 site/.env 的 VITE_ 变量；缺失时回退到当前站点 origin，
// 使 GitHub Pages / Cloudflare Pages 部署后无需配置也能正常显示与互切。
const envGh = (import.meta.env.VITE_GHPAGES_URL as string | undefined)?.trim()
const envCf = (import.meta.env.VITE_CF_URL as string | undefined)?.trim()
const ghUrl = envGh || (typeof window !== 'undefined' ? window.location.origin : '')
const cfUrl = envCf || ''

const options = computed(() => {
  const list: { key: string; label: string; url: string }[] = []
  if (ghUrl) list.push({ key: 'gh', label: 'GitHub Pages', url: ghUrl })
  if (cfUrl) list.push({ key: 'cf', label: 'Cloudflare Pages', url: cfUrl })
  return list
})

const route = useRoute()
const current = ref('')

function normalize(u: string): string {
  return u.replace(/\/+$/, '')
}

onMounted(() => {
  const here = normalize(window.location.origin + (import.meta.env.BASE_URL || '/'))
  let matched = ''
  for (const o of options.value) {
    if (normalize(o.url) === here) {
      matched = o.key
      break
    }
  }
  current.value = matched || options.value[0]?.key || ''
})

// 切换到另一部署：剥离当前 base 得到相对路径，再拼接到目标部署根地址
function onChange(e: Event) {
  const key = (e.target as HTMLSelectElement).value
  const opt = options.value.find((o) => o.key === key)
  if (!opt) return
  const base = import.meta.env.BASE_URL || '/'
  const rel = route.path.startsWith(base) ? route.path.slice(base.length) : route.path
  const target = normalize(opt.url) + '/' + rel.replace(/^\/+/, '')
  window.location.href = target
}
</script>

<template>
  <select
    v-if="options.length > 1"
    class="escah-ctrl-btn site-access-switch"
    :value="current"
    title="切换站点访问方式"
    @change="onChange"
  >
    <option v-for="o in options" :key="o.key" :value="o.key">{{ o.label }}</option>
  </select>
</template>

<style scoped>
.site-access-switch {
  height: 28px;
  padding: 0 8px;
  appearance: auto;
  -webkit-appearance: auto;
  cursor: pointer;
}
</style>
