<script setup lang="ts">
// 首次打开本地搜索时，搜索索引是懒加载的（按 locale 动态 import），
// 打开后到索引就绪之间有一段空窗：默认不显示任何提示，用户会以为搜索坏了。
// 本组件在搜索弹窗打开、且结果尚未出现、且未输入查询的冷加载窗口内，
// 给结果区加上 escah-search-loading 类，由 CSS 显示「正在搜索中，请稍等…」。
import { onMounted, onUnmounted } from 'vue'

let modal: HTMLElement | null = null
let observer: MutationObserver | null = null
let timer: number | null = null

function findModal(): HTMLElement | null {
  // 搜索弹窗只有在打开时才把输入框渲染进 DOM
  const input = document.querySelector(
    '.VPLocalSearchBox input, .local-search input',
  ) as HTMLInputElement | null
  if (!input) return null
  return (
    (input.closest('.VPLocalSearchBox') as HTMLElement | null) ||
    (input.closest('.local-search') as HTMLElement | null)
  )
}

function refresh() {
  if (!modal) return
  const li = modal.querySelector('.results li')
  const input = modal.querySelector('input') as HTMLInputElement | null
  const hasText = !!input && input.value.trim().length > 0
  // 冷加载 = 结果未出现且未输入查询（输入后索引必然已就绪）
  const loading = !li && !hasText
  modal.classList.toggle('escah-search-loading', loading)
}

function onOpen(m: HTMLElement) {
  modal = m
  modal.classList.add('escah-search-loading')
  refresh()
  observer = new MutationObserver(refresh)
  observer.observe(modal, { childList: true, subtree: true })
  if (timer) clearTimeout(timer)
  // 兜底：最多显示 2.5s，避免索引极慢时提示常驻
  timer = window.setTimeout(() => modal?.classList.remove('escah-search-loading'), 2500)
}

function onClose() {
  modal?.classList.remove('escah-search-loading')
  modal = null
  if (observer) {
    observer.disconnect()
    observer = null
  }
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
}

onMounted(() => {
  const mo = new MutationObserver(() => {
    const m = findModal()
    if (m && !modal) onOpen(m)
    else if (!m && modal) onClose()
  })
  mo.observe(document.body, { childList: true, subtree: true })
})

onUnmounted(onClose)
</script>

<template></template>
