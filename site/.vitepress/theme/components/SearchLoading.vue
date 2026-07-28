<script setup lang="ts">
// 搜索进度提示：只要用户在搜索框输入了文字、且结果尚未渲染出来，就显示具体进度。
// 不再依赖“本会话是否冷加载索引”的判定（旧逻辑导致已缓存索引后进度永不显示）。
// 触发：输入 input 事件 + DOM 变化（结果渲染）。结果区出现条目或“无结果”即完成。
// 注意：进度卡片不拦截鼠标（pointer-events:none），搜索输入框始终可用。
import { onMounted, onUnmounted, ref } from 'vue'

const visible = ref(false)
const pct = ref(0)
const label = ref('正在搜索…')

let raf = 0
let startTime = 0
let done = false // 当前这一轮查询已完成（结果已出），清空输入后复位
let showTimer: number | null = null // 200ms 防抖：瞬时搜索不闪进度条
let modal: HTMLElement | null = null
let mo: MutationObserver | null = null

const CHUNK_RE = /localSearchIndex/i

function chunkLoaded(): boolean {
  const entries = performance.getEntriesByType('resource') as PerformanceResourceTiming[]
  return entries.some((r) => CHUNK_RE.test(r.name) && r.responseEnd > 0)
}

// 结果是否已就绪：结果列表渲染出条目，或已显示“无结果”
function resultsReady(m: HTMLElement): boolean {
  const results = m.querySelector('.results')
  if (results && results.querySelector('.result, li, a')) return true
  if (results && results.children.length > 0) return true
  const txt = m.textContent || ''
  if (/no results|无结果|未找到|没有找到|没有匹配/i.test(txt)) return true
  return false
}

function complete() {
  if (done) return
  done = true
  if (raf) cancelAnimationFrame(raf)
  if (showTimer) { clearTimeout(showTimer); showTimer = null }
  pct.value = 100
  label.value = '搜索完成'
  window.setTimeout(() => { visible.value = false }, 600)
}

function animate() {
  if (done) return
  // 真实完成信号：索引分块下载结束（冷加载时）
  if (chunkLoaded()) { complete(); return }
  const elapsed = performance.now() - startTime
  const t = Math.min(elapsed / 8000, 1)
  const eased = 1 - Math.pow(1 - t, 2.2)
  pct.value = Math.min(99, Math.round(2 + eased * 97))
  raf = requestAnimationFrame(animate)
}

function findModal(): HTMLElement | null {
  const input = document.querySelector(
    '.VPLocalSearchBox input, .local-search input',
  ) as HTMLInputElement | null
  if (!input) return null
  return (
    (input.closest('.VPLocalSearchBox') as HTMLElement | null) ||
    (input.closest('.local-search') as HTMLElement | null)
  )
}

// 核心扫描：根据“是否输入了文字 + 结果是否已渲染”决定进度卡片显隐
function scan() {
  const m = findModal()
  if (!m) { onClose(); return }
  modal = m
  const input = m.querySelector('input') as HTMLInputElement | null
  const hasQuery = !!input && input.value.trim().length > 0
  const ready = resultsReady(m)

  if (!hasQuery) {
    // 无查询：复位，不显示
    if (showTimer) { clearTimeout(showTimer); showTimer = null }
    if (raf) cancelAnimationFrame(raf)
    visible.value = false
    done = false
    pct.value = 0
    return
  }

  if (ready) {
    // 结果已出（或显示无结果）→ 完成
    if (showTimer) { clearTimeout(showTimer); showTimer = null }
    complete()
    return
  }

  // 有查询、结果还没出来：确保动画在跑，并防抖后显示卡片
  if (!raf && !done) { startTime = performance.now(); animate() }
  if (showTimer == null && !visible.value) {
    showTimer = window.setTimeout(() => {
      showTimer = null
      if (!done) { visible.value = true; label.value = '正在搜索…' }
    }, 200)
  }
}

function onClose() {
  if (raf) cancelAnimationFrame(raf)
  if (showTimer) { clearTimeout(showTimer); showTimer = null }
  if (mo) { mo.disconnect(); mo = null }
  visible.value = false
  pct.value = 0
  modal = null
  done = false
}

function onInputCapture(e: Event) {
  const t = e.target as HTMLElement
  if (t && t.tagName === 'INPUT' && t.closest('.VPLocalSearchBox, .local-search')) {
    scan()
  }
}

onMounted(() => {
  mo = new MutationObserver(() => scan())
  mo.observe(document.body, { childList: true, subtree: true })
  // 输入框事件直接驱动，避免依赖弹窗打开时机的检测
  document.addEventListener('input', onInputCapture, true)
})

onUnmounted(() => {
  document.removeEventListener('input', onInputCapture, true)
  onClose()
})
</script>

<template>
  <div v-if="visible" class="escah-search-progress" role="status" aria-live="polite">
    <div class="sp-card">
      <div class="sp-spinner" aria-hidden="true"></div>
      <div class="sp-label">{{ label }}（{{ pct }}%）</div>
      <div class="sp-bar"><div class="sp-fill" :style="{ width: pct + '%' }"></div></div>
      <div class="sp-hint">正在查找匹配内容，请稍候…</div>
    </div>
  </div>
</template>

<style scoped>
.escah-search-progress {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 不拦截鼠标事件：搜索输入框与关闭按钮始终可用（Esc / ✕） */
  pointer-events: none;
  background: rgba(0, 0, 0, 0.28);
}
.sp-card {
  pointer-events: none;
  width: min(360px, 80vw);
  padding: 22px 24px;
  border-radius: 14px;
  background: var(--vp-c-bg, #fff);
  border: 1px solid var(--vp-c-divider, #e2e2e3);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
  text-align: center;
  animation: sp-pop 0.18s ease;
}
@keyframes sp-pop {
  from { transform: scale(0.94); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.sp-spinner {
  width: 34px;
  height: 34px;
  margin: 0 auto 12px;
  border: 3px solid transparent;
  border-top-color: #e91e63;
  border-right-color: #7c3aed;
  border-radius: 50%;
  animation: sp-rot 0.9s linear infinite;
}
@keyframes sp-rot { to { transform: rotate(360deg); } }
.sp-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--vp-c-text-1, #1b1b1f);
  margin-bottom: 12px;
}
.sp-bar {
  height: 10px;
  border-radius: 999px;
  background: var(--vp-c-bg-soft, #f1f1f3);
  overflow: hidden;
}
.sp-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #e91e63, #7c3aed);
  transition: width 0.2s ease;
}
.sp-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--vp-c-text-2, #71717a);
}
</style>
