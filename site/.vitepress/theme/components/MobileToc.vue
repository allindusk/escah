<script setup lang="ts">
/**
 * 移动端「本页目录」抽屉（2026-09-30）
 * ---------------------------------------------------------------------------
 * 桌面端右侧目录（DocOutline 挂在 #aside-top）在 <1280px 被 VitePress 压成 0 宽，
 * 手机上完全没有页内导航 —— 技能表那种 3.7 万像素高的页面只能靠手指硬划。
 *
 * 这里复用 DocOutline 已经构建好的目录树（打开时克隆它的 <ul>），
 * 用一个右下角悬浮按钮 + 底部抽屉补回页内导航。
 * 桌面端（>767px）按钮不渲染，本组件等价于不存在。
 */
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vitepress'

const route = useRoute()
const hasToc = ref(false)
const visible = ref(false)
const tocHtml = ref('')

let mo: MutationObserver | null = null
let timer: number | undefined

function checkToc(): void {
  hasToc.value = !!document.querySelector('.escah-doc-outline .escah-outline-list li')
}

function observeToc(): void {
  mo?.disconnect()
  const target = document.querySelector('.VPDoc') || document.body
  mo = new MutationObserver(() => {
    if (timer) window.clearTimeout(timer)
    timer = window.setTimeout(checkToc, 260)
  })
  mo.observe(target, { childList: true, subtree: true })
  if (timer) window.clearTimeout(timer)
  timer = window.setTimeout(checkToc, 260)
}

function open(): void {
  const list = document.querySelector('.escah-doc-outline .escah-outline-list')
  if (!list) return
  tocHtml.value = list.outerHTML
  visible.value = true
  document.body.style.overflow = 'hidden'
}

function close(): void {
  visible.value = false
  document.body.style.overflow = ''
}

function onItemClick(e: MouseEvent): void {
  const a = (e.target as HTMLElement).closest('a') as HTMLAnchorElement | null
  if (!a) return
  e.preventDefault()
  const href = a.getAttribute('href') || ''
  if (!href.startsWith('#')) return
  const id = href.slice(1)
  close()
  const target = document.getElementById(id)
  if (!target) {
    history.replaceState(null, '', '#' + id)
    return
  }
  window.setTimeout(() => {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
    history.replaceState(null, '', '#' + id)
  }, 60)
}

function onKey(e: KeyboardEvent): void {
  if (e.key === 'Escape' && visible.value) close()
}

onMounted(() => {
  nextTick(() => {
    checkToc()
    observeToc()
  })
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  mo?.disconnect()
  if (timer) window.clearTimeout(timer)
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})

watch(
  () => route.path,
  () => {
    close()
    nextTick(observeToc)
  },
)
</script>

<template>
  <div class="escah-mtoc">
    <button
      v-if="hasToc"
      type="button"
      class="escah-mtoc-btn"
      aria-label="本页目录"
      title="本页目录"
      @click="open"
    >
      <span class="escah-mtoc-ico">☰</span>
      <span class="escah-mtoc-txt">目录</span>
    </button>
  </div>

  <Teleport to="body">
    <Transition name="escah-sheet">
      <div v-if="visible" class="escah-mtoc-mask" @click="close" />
    </Transition>
    <Transition name="escah-sheet">
      <div v-if="visible" class="escah-mtoc-sheet" role="dialog" aria-label="本页目录">
        <div class="escah-mtoc-head">
          <span>本页目录</span>
          <button type="button" class="escah-mtoc-close" @click="close">关闭 ✕</button>
        </div>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="escah-mtoc-body" @click="onItemClick" v-html="tocHtml" />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* 桌面端：整个组件不显示，等价于不存在 */
.escah-mtoc {
  display: none;
}

/* 断点 959px：与 mobile.css 的 .escah-dock 保持一致（768–959 的“导航真空区”
   同样没有桌面侧栏与右侧目录，页内目录入口必须有）。 */
@media (max-width: 959px) {
  .escah-mtoc {
    display: block;
    align-items: flex-end;
  }
  .escah-mtoc-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 3px;
    width: 38px;
    height: 38px;
    margin-bottom: 6px;
    padding: 0;
    font-size: 11px;
    font-weight: 700;
    line-height: 1;
    color: #fff;
    background: var(--escah-grad);
    border: none;
    border-radius: 11px;
    box-shadow: 0 4px 14px rgba(233, 30, 99, 0.32);
    cursor: pointer;
    flex-direction: column;
    opacity: 0.92;
  }
  .escah-mtoc-btn:active {
    opacity: 1;
    transform: scale(0.96);
  }
  .escah-mtoc-ico {
    font-size: 14px;
    line-height: 1;
  }
  .escah-mtoc-txt {
    font-size: 9.5px;
    letter-spacing: 0.5px;
  }
}

/* 抽屉（Teleport 到 body，不受 dock 影响） */
.escah-mtoc-mask {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: rgba(10, 10, 18, 0.45);
}

.escah-mtoc-sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 301;
  display: flex;
  flex-direction: column;
  max-height: 72dvh;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: var(--vp-c-bg-soft);
  border-top: 1px solid var(--escah-border);
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -12px 40px rgba(10, 10, 20, 0.28);
}

.escah-mtoc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  padding: 12px 16px 10px;
  font-size: 14px;
  font-weight: 700;
  color: var(--vp-c-text-1);
  border-bottom: 1px solid var(--escah-border);
}

.escah-mtoc-close {
  padding: 7px 12px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--vp-c-text-1);
  background: var(--vp-c-default-soft);
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.escah-mtoc-body {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 10px 14px 22px;
  font-size: 14px;
  line-height: 1.5;
}

/* 目录树样式：与桌面 DocOutline 同一视觉语言（悬停/激活色一致） */
.escah-mtoc-body :deep(.escah-outline-list) {
  list-style: none;
  margin: 0;
  padding: 0;
}
.escah-mtoc-body :deep(.escah-outline-list .escah-outline-list) {
  padding-left: 12px;
  margin-left: 6px;
  border-left: 1px solid var(--vp-c-divider);
}
.escah-mtoc-body :deep(.escah-ol-item > a) {
  display: block;
  padding: 9px 10px;
  margin: 1px 0;
  font-size: 14px;
  color: var(--vp-c-text-2);
  text-decoration: none;
  border-radius: 8px;
  border-left: 2px solid transparent;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.escah-mtoc-body :deep(.escah-ol-item > a:active) {
  background: var(--vp-c-default-soft);
  color: var(--vp-c-text-1);
}
.escah-mtoc-body :deep(.escah-ol-item > a.active) {
  color: var(--vp-c-brand-1);
  border-left-color: var(--vp-c-brand-1);
  font-weight: 600;
}

/* 抽屉动画 */
.escah-sheet-enter-active,
.escah-sheet-leave-active {
  transition: transform 0.22s ease, opacity 0.22s ease;
}
.escah-sheet-enter-from,
.escah-sheet-leave-to {
  transform: translateY(14px);
  opacity: 0;
}
.escah-mtoc-mask.escah-sheet-enter-active,
.escah-mtoc-mask.escah-sheet-leave-active {
  transition: opacity 0.22s ease;
}
.escah-mtoc-mask.escah-sheet-enter-from,
.escah-mtoc-mask.escah-sheet-leave-to {
  opacity: 0;
  transform: none;
}
</style>
