<script setup lang="ts">
/**
 * 站内跳转的加载反馈（2026-11-24）
 * --------------------------------------------------------------------------
 * 背景：本站在 GitHub Pages 上的单页 chunk 约 50~70KB（gzip），国内网络实测
 * 单页要 3s 左右才下载完；VitePress 客户端路由在这段时间里**完全不改界面**，
 * 于是「点了侧栏链接 → 画面没变」被当成没反应（用户会再点一次）。
 *
 * 做法：监听 VitePress router 的「开始换页 / 换页完成」两个钩子，
 *   · 350ms 内完成的跳转不提示（避免快速跳转闪一下提示）；
 *   · 超过 350ms 仍没换完 → 顶部进度条 + 显眼的「正在加载页面…」胶囊提示；
 *   · 超过 5s → 文案换成「网络较慢，仍在加载…」，让用户知道还在跑；
 *   · 15s 兜底收起（防止异常情况下提示常驻）。
 * 提示层 pointer-events:none，不挡任何点击。
 */
import { useRouter } from 'vitepress'
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from '../i18n'

const router = useRouter()
const { t } = useI18n()

const visible = ref(false)
const slow = ref(false)

let showTimer: number | undefined
let slowTimer: number | undefined
let guardTimer: number | undefined

const hint = computed(() => (slow.value ? t('loading.slow') : t('loading.page')))

function clearTimers(): void {
  if (showTimer !== undefined) window.clearTimeout(showTimer)
  if (slowTimer !== undefined) window.clearTimeout(slowTimer)
  if (guardTimer !== undefined) window.clearTimeout(guardTimer)
  showTimer = slowTimer = guardTimer = undefined
}

function stop(): void {
  clearTimers()
  visible.value = false
  slow.value = false
}

function start(): void {
  clearTimers()
  visible.value = false
  slow.value = false
  showTimer = window.setTimeout(() => {
    visible.value = true
  }, 350)
  slowTimer = window.setTimeout(() => {
    slow.value = true
  }, 5000)
  guardTimer = window.setTimeout(stop, 15000)
}

// onBeforeRouteChange：用户点了站内链接、路由开始切换（此时还没下载/渲染新页）
// ⚠️ 这两个钩子是 router 上的「单槽」属性（`router.onBeforeRouteChange = fn`），
//    不是事件订阅方法，不能 `router.onBeforeRouteChange(cb)` 那样调用；
//    且 SSR 阶段的 router 是精简桩对象，所以只在浏览器侧赋值。
if (typeof window !== 'undefined') {
  router.onBeforeRouteChange = (to?: string) => {
    if (typeof to !== 'string') return
    // 参数是归一化后的完整 URL；同页锚点跳转（#xxx）不算换页，不提示
    try {
      if (new URL(to, window.location.href).pathname === window.location.pathname) return
    } catch {
      /* 解析失败就按换页处理 */
    }
    start()
  }

  // onAfterRouteChanged：新页已渲染完成（正文组件的 onMounted 也已跑完）
  router.onAfterRouteChanged = () => {
    // 等两帧再收起，保证提示消失时新内容已经画到屏幕上
    requestAnimationFrame(() => requestAnimationFrame(stop))
  }
}

onUnmounted(clearTimers)
</script>

<template>
  <div v-if="visible" class="escah-route-loading" role="status" aria-live="polite">
    <div class="escah-route-loading-bar"><span /></div>
    <div class="escah-route-loading-hint">
      <i class="escah-route-loading-spin" aria-hidden="true" />
      {{ hint }}
    </div>
  </div>
</template>

<style scoped>
.escah-route-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 120;
  pointer-events: none;
}
.escah-route-loading-bar {
  position: relative;
  height: 5px;
  overflow: hidden;
  background: rgba(233, 30, 99, 0.16);
}
.escah-route-loading-bar span {
  position: absolute;
  top: 0;
  left: -45%;
  width: 45%;
  height: 5px;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(
    90deg,
    rgba(233, 30, 99, 0) 0%,
    var(--escah-pink, #e91e63) 50%,
    rgba(233, 30, 99, 0) 100%
  );
  animation: escahRouteSlide 1.2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}
@keyframes escahRouteSlide {
  0% {
    left: -45%;
  }
  100% {
    left: 100%;
  }
}
.escah-route-loading-hint {
  display: flex;
  align-items: center;
  gap: 11px;
  width: max-content;
  /* 压在导航栏下面，避免挡住导航菜单项 */
  margin: calc(var(--vp-nav-height, 56px) + 16px) auto 0;
  padding: 11px 24px;
  border-radius: 999px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.3px;
  line-height: 1.2;
  color: var(--vp-c-text-1);
  background: var(--vp-c-bg-soft);
  border: 2px solid var(--escah-pink, #e91e63);
  box-shadow:
    0 10px 30px rgba(0, 0, 0, 0.18),
    0 0 0 4px rgba(233, 30, 99, 0.12);
  animation: escahRoutePop 0.22s ease-out;
}
@keyframes escahRoutePop {
  from {
    opacity: 0;
    transform: translateY(-6px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
.escah-route-loading-spin {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid var(--escah-pink, #e91e63);
  border-top-color: transparent;
  animation: escahRouteSpin 0.8s linear infinite;
}
@keyframes escahRouteSpin {
  to {
    transform: rotate(360deg);
  }
}
/* 移动端：顶部导航 + 本地导航条挤在一起，胶囊改到底部居中，避免压住「全部页面/返回顶部」 */
@media (max-width: 767px) {
  .escah-route-loading-hint {
    position: fixed;
    left: 50%;
    bottom: 84px;
    transform: translateX(-50%);
    margin: 0;
    gap: 9px;
    padding: 10px 20px;
    font-size: 14px;
    animation: escahRouteFade 0.2s ease-out;
  }
  .escah-route-loading-spin {
    width: 15px;
    height: 15px;
    border-width: 2.5px;
  }
}
@keyframes escahRouteFade {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@media (prefers-reduced-motion: reduce) {
  .escah-route-loading-bar span,
  .escah-route-loading-spin {
    animation-duration: 3s;
  }
}
</style>
