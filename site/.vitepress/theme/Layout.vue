<script setup lang="ts">
import DefaultTheme from 'vitepress/theme'
import { useData } from 'vitepress'
import { onMounted, onUnmounted, ref } from 'vue'
import CharHoverModal from './components/CharHoverModal.vue'
import DocOutline from './components/DocOutline.vue'
import MetaBar from './components/MetaBar.vue'
import ScrollButtons from './components/ScrollButtons.vue'
import SiteAccessSwitch from './components/SiteAccessSwitch.vue'
import SearchLoading from './components/SearchLoading.vue'
import { useI18n } from './i18n'
import { uiPrefs, applyUiClasses } from './uiPrefs'

const { Layout } = DefaultTheme
const { t } = useI18n()
const { lang } = useData()

// 图片灯箱（镜像内容图片点击放大）
const lbSrc = ref('')
function onDocClick(e: MouseEvent) {
  const img = (e.target as HTMLElement).closest?.('.mirror-content img') as HTMLImageElement | null
  if (!img) return
  // 角色头像（带 data-char）由 MirrorContent 的点击固定逻辑接管（pin 浮窗），
  // 不能也触发灯箱放大，否则会同时弹出浮窗 + 放大头像 + 玻璃遮罩。
  if (img.hasAttribute('data-char')) return
  lbSrc.value = img.src
}

// Shift + 滚轮：在横向可滚动容器（表格/全屏）内横向滚动
function onShiftWheel(e: WheelEvent) {
  if (!e.shiftKey) return
  const target = e.target as HTMLElement
  const sc = target.closest('.table-scroll, .escah-tbl-fs-scroll') as HTMLElement | null
  if (!sc) return
  if (sc.scrollWidth <= sc.clientWidth + 1) return
  e.preventDefault()
  sc.scrollLeft += e.deltaY
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  window.addEventListener('wheel', onShiftWheel, { passive: false })
  applyUiClasses()
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  window.removeEventListener('wheel', onShiftWheel)
})

const homeHref = () => {
  const base = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '')
  return `${base}/${lang.value.startsWith('zh') ? 'zh' : 'ja'}/`
}
</script>

<template>
  <Layout>
    <template #nav-bar-content-after>
      <div class="escah-nav-controls">
        <button
          class="escah-ctrl-btn"
          :title="uiPrefs.ultraWide ? '切换为标准宽度' : '切换为超宽模式'"
          @click="uiPrefs.ultraWide = !uiPrefs.ultraWide"
        >
          {{ uiPrefs.ultraWide ? '超宽' : '标准' }}宽度
        </button>
        <button
          class="escah-ctrl-btn"
          :title="uiPrefs.navCollapsed ? '展开左侧导航栏' : '收起左侧导航栏'"
          @click="uiPrefs.navCollapsed = !uiPrefs.navCollapsed"
        >
          {{ uiPrefs.navCollapsed ? '展开侧栏' : '收起侧栏' }}
        </button>
        <button
          class="escah-ctrl-btn"
          :title="uiPrefs.tocCollapsed ? '展开右侧目录栏' : '收起右侧目录栏'"
          @click="uiPrefs.tocCollapsed = !uiPrefs.tocCollapsed"
        >
          {{ uiPrefs.tocCollapsed ? '展开目录' : '收起目录' }}
        </button>
        <SiteAccessSwitch />
      </div>
    </template>
    <template #doc-bottom>
      <MetaBar />
    </template>
    <template #aside-top>
      <DocOutline />
    </template>
    <template #not-found>
      <div class="escah-notfound">
        <h1>404</h1>
        <h2>{{ t('notFound.title') }}</h2>
        <p>{{ t('notFound.desc') }}</p>
        <a class="home-btn" :href="homeHref()">{{ t('notFound.home') }}</a>
      </div>
    </template>
  </Layout>
  <CharHoverModal />
  <ScrollButtons />
  <SearchLoading />
  <div v-if="lbSrc" class="lightbox-mask" @click="lbSrc = ''">
    <img :src="lbSrc" alt="" />
  </div>
</template>

<style scoped>
.escah-notfound {
  min-height: 60vh;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; text-align: center; padding: 40px 20px;
}
.escah-notfound h1 {
  font-size: 72px; font-weight: 800; margin: 0;
  background: var(--escah-grad);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.escah-notfound h2 { font-size: 20px; margin: 0; border: none; }
.escah-notfound p { color: var(--vp-c-text-2); }
.home-btn {
  margin-top: 12px; padding: 10px 28px;
  color: #fff; background: var(--escah-grad);
  border-radius: 999px; font-weight: 600; text-decoration: none;
  transition: transform 0.15s, box-shadow 0.15s;
}
.home-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(233, 30, 99, 0.35); }
</style>
