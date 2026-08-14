<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vitepress'

// 双部署访问域名：直接写死（不依赖 .env，因 .env 被 gitignore，CF 云端构建读不到）。
// GitHub Pages 带 /escah 子路径；Cloudflare Pages 以根路径部署（zh 走 /zh/... 自动拼接）。
const ghUrl = 'https://allindusk.github.io/escah'
const cfUrl = 'https://escah.pages.dev'

// 站点前端版本号（三位数：①大版本 ②新增功能 ③修改）。改前端后递增对应位并 commit+push，
// 线上才会更新，方便核对本地/线上是否一致。
// 铁律：每次升版本号，助手（AI）必须同步维护 theme/changelog.json（更新记录页"镜像站更新记录"区块），
// 两者保持一致；改动前端后务必 commit+push 到 main，否则线上版本号与改动不生效。
// 注意 changelog.json 位于 theme/ 源码目录（入库），不要放回 .gen-data/（那里是 sync-site 生成的
// page-times.json，被 gitignore，会导致 CI 构建因文件缺失而失败）。
const SITE_VERSION = '1.2.6'

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
  <span v-if="options.length > 1" class="site-access-wrap">
    <select
      class="escah-ctrl-btn site-access-switch"
      :value="current"
      title="切换站点访问方式"
      @change="onChange"
    >
      <option v-for="o in options" :key="o.key" :value="o.key">{{ o.label }}</option>
    </select>
    <span class="site-help" tabindex="0" role="img" aria-label="站点说明">❓
      <span class="site-help-tip">
        <strong>为什么要切换站点？</strong><br />
        <b>GitHub Pages</b>：与代码仓库同源、稳定可靠；但国内访问可能偏慢、缓存刷新偶有延迟。<br />
        <b>Cloudflare Pages</b>：全球 CDN 更快、地址更短（根路径）；但个别网络可能受限。<br />
        两个镜像内容完全一致，哪个打开快就用哪个。
      </span>
    </span>
    <span class="site-version" :title="'站点前端版本 ' + SITE_VERSION">v{{ SITE_VERSION }}</span>
  </span>
</template>

<style scoped>
.site-access-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.site-access-switch {
  height: 28px;
  padding: 0 8px;
  appearance: auto;
  -webkit-appearance: auto;
  cursor: pointer;
}
.site-help {
  cursor: help;
  font-size: 14px;
  line-height: 1;
  user-select: none;
  outline: none;
}
.site-help-tip {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: 250px;
  padding: 8px 10px;
  background: var(--vp-c-bg-soft, #fff);
  border: 1px solid var(--vp-c-divider, #ddd);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  font-size: 12px;
  font-weight: normal;
  line-height: 1.6;
  text-align: left;
  color: var(--vp-c-text-1, #333);
  white-space: normal;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.15s ease;
  z-index: 50;
}
.site-help:hover .site-help-tip,
.site-help:focus .site-help-tip,
.site-help:focus-visible .site-help-tip {
  opacity: 1;
  visibility: visible;
}
.site-version {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 8px;
  margin-left: 2px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  color: var(--vp-c-white, #fff);
  background: var(--escah-grad, linear-gradient(135deg, #e91e63, #ff6f91));
  letter-spacing: 0.3px;
  user-select: none;
  cursor: default;
  white-space: nowrap;
}
</style>
