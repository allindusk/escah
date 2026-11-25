<script setup lang="ts">
import DefaultTheme from 'vitepress/theme'
import { useData, useRoute } from 'vitepress'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import CharHoverModal from './components/CharHoverModal.vue'
import DocOutline from './components/DocOutline.vue'
import MetaBar from './components/MetaBar.vue'
import MobileToc from './components/MobileToc.vue'
import RouteLoading from './components/RouteLoading.vue'
import ScrollButtons from './components/ScrollButtons.vue'
import SiteAccessSwitch from './components/SiteAccessSwitch.vue'
// 搜索功能已禁用（性能开销）
// import SearchLoading from './components/SearchLoading.vue'
// import VPNavBarSearch from './components/VPNavBarSearch.vue'
import { useI18n } from './i18n'
import { uiPrefs, applyUiClasses } from './uiPrefs'
import { initMobileUX, refreshMobileUX } from './mobileUX'
import { initAnimMedia, refreshAnimMedia, playAnimImage } from './animMedia'
import { initLangScroll, restoreLangScroll } from './langScroll'

const { Layout } = DefaultTheme
const { t } = useI18n()
const { lang } = useData()
const route = useRoute()

// 图片灯箱（镜像内容图片点击放大）
const lbSrc = ref('')
function onDocClick(e: MouseEvent) {
  // 表格「全屏」是把表格克隆到 body 下的 .escah-tbl-fs 里，不在 .mirror-content 内，
  // 也要能点开动图/灯箱。
  const img = (e.target as HTMLElement).closest?.('.mirror-content img, .escah-tbl-fs img') as HTMLImageElement | null
  if (!img) return
  // 角色头像由 MirrorContent 的点击固定逻辑接管（pin 浮窗），不能也触发灯箱放大，
  // 否则会同时弹出浮窗 + 放大头像 + 玻璃遮罩。头像 img 自身通常不带 data-char，
  // 而是包在带 data-char 的 span/祖先元素内，故用 closest 向上查找。
  if (img.closest('[data-char]')) return
  // 指向角色页的图片（支援者/NPC 的头像自 2026-10-20 起不挂 data-char、不弹角色浮窗，
  // 点击是直接跳转角色页）：不能再叠一层灯箱放大，否则「跳页 + 图片遮罩」同时发生。
  // 只拦角色页链接，其它链接内的图片（如 raid/装备页横幅）维持原行为。
  if (img.closest('a[href*="characters/"]')) return
  // 动图默认只显示首帧海报（省流量，见 animMedia.ts）：触屏设备上第一下点按 = 播放动画，
  // 动图之后再点才进灯箱放大；鼠标设备进视口已自动播放，行为不变。
  if (img.dataset.animSrc && img.dataset.animPlaying !== '1' && !img.closest('a')) {
    if (playAnimImage(img)) return
  }
  // 灯箱放大用原图：动图取其原动图，srcset 图取 src（=原尺寸）
  lbSrc.value = img.dataset.animSrc || img.src
}

// Shift + 滚轮：在横向可滚动容器（表格/全屏）内横向滚动
function onShiftWheel(e: WheelEvent) {
  if (!e.shiftKey) return
  const target = e.target as HTMLElement
  const sc = target.closest('.table-scroll, .escah-tbl-fs-scroll') as HTMLElement | null
  if (!sc) return
  if (sc.scrollWidth <= sc.clientWidth + 1) return
  // 浏览器在 shift+滚轮时，不同设备把位移放进不同字段：
  // 多数鼠标滚轮 → deltaY；部分鼠标/触控板横向滚轮 → deltaX。
  // 只取绝对值较大的那个，避免「只读了 0 而提前 return」导致无法横滚。
  const d = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
  if (d === 0) return
  e.preventDefault()
  sc.scrollLeft += d
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  window.addEventListener('wheel', onShiftWheel, { passive: false })
  applyUiClasses()
  // 移动端增强：表格横滑提示 + 页内目录折叠（≤767px 才生效）
  initMobileUX()
  // 动图海报优先：鼠标设备进视口自动播放，触屏点按才播
  initAnimMedia()
  // 语言切换后回到「同一处内容」（中/日页结构同源，按标题序号对齐，见 langScroll.ts）
  initLangScroll()
  // v-html 正文可能晚于 Layout 挂载落地，下一拍再扫一次
  nextTick(() => refreshAnimMedia())
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  window.removeEventListener('wheel', onShiftWheel)
})

// 路由切换后重跑移动端增强（新页面的目录与表格需要重新判定）
watch(
  () => route.path,
  (path) =>
    nextTick(() => {
      refreshMobileUX()
      refreshAnimMedia()
      // 语言切换（同 slug 换 /zh ↔ /ja）后恢复阅读位置；普通跳转不受影响
      restoreLangScroll(path)
    }),
)

const homeHref = () => {
  const base = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '')
  return `${base}/${lang.value.startsWith('zh') ? 'zh' : 'ja'}/`
}
</script>

<template>
  <Layout>
    <template #nav-bar-content-before>
      <!-- 搜索功能已禁用 <VPNavBarSearch /> -->
    </template>
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
  <!-- 站内跳转的加载反馈：换页超过 350ms 才出现（顶部进度条 + 「正在加载页面…」） -->
  <RouteLoading />
  <!-- 右下角悬浮控件栈：桌面端 .escah-dock 为 display:contents（子元素各自 fixed 定位，
       外观与改造前完全一致）；移动端才收成一个纵向悬浮栈（见 mobile.css）。 -->
  <div class="escah-dock">
    <MobileToc />
    <ScrollButtons />
  </div>
  <!-- 搜索功能已禁用 <SearchLoading /> -->
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
