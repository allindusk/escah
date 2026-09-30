<script setup lang="ts">
// 页面右下角浮动操作按钮：回到顶部 / 向上翻页 / 向下翻页 / 前往底部
// 移动端（≤767px）由 mobile.css 接管：容器被收进 .escah-dock 悬浮栈，
// 并隐藏「上/下翻页」两个（手机靠惯性滚动即可，四个按钮在窄屏太占地方）。
function top() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
function bottom() {
  window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' })
}
function up() {
  window.scrollBy({ top: -Math.max(window.innerHeight * 0.85, 400), behavior: 'smooth' })
}
function down() {
  window.scrollBy({ top: Math.max(window.innerHeight * 0.85, 400), behavior: 'smooth' })
}
</script>

<template>
  <div class="escah-scroll-btns" aria-label="页面滚动控制">
    <button class="escah-sb escah-sb-top" title="回到顶部" aria-label="回到顶部" @click="top">⤒</button>
    <button class="escah-sb escah-sb-up" title="向上翻页" aria-label="向上翻页" @click="up">︿</button>
    <button class="escah-sb escah-sb-down" title="向下翻页" aria-label="向下翻页" @click="down">﹀</button>
    <button class="escah-sb escah-sb-bottom" title="前往底部" aria-label="前往底部" @click="bottom">⤓</button>
  </div>
</template>

<style scoped>
.escah-scroll-btns {
  position: fixed;
  right: 18px;
  bottom: 22px;
  z-index: 60;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.escah-sb {
  width: 42px;
  height: 42px;
  border: none;
  border-radius: 12px;
  background: var(--escah-grad);
  color: #fff;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(233, 30, 99, 0.32);
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.escah-sb:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(233, 30, 99, 0.45);
}
.escah-sb:active {
  transform: translateY(0);
}
.dark .escah-sb {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}
/* 移动端：位置/尺寸统一交给 mobile.css 的 .escah-dock 控制，
   这里只做「砍掉两个翻页按钮」。断点与 dock 一致（959px）。 */
@media (max-width: 959px) {
  .escah-sb-up,
  .escah-sb-down {
    display: none;
  }
}
</style>
