<script setup lang="ts">
// 页面右下角浮动操作按钮：回到顶部 / 向上翻页 / 向下翻页 / 前往底部
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
    <button class="escah-sb" title="回到顶部" aria-label="回到顶部" @click="top">⤒</button>
    <button class="escah-sb" title="向上翻页" aria-label="向上翻页" @click="up">︿</button>
    <button class="escah-sb" title="向下翻页" aria-label="向下翻页" @click="down">﹀</button>
    <button class="escah-sb" title="前往底部" aria-label="前往底部" @click="bottom">⤓</button>
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
/* 窄屏避免挡内容 */
@media (max-width: 768px) {
  .escah-scroll-btns {
    right: 10px;
    bottom: 12px;
    gap: 6px;
  }
  .escah-sb {
    width: 36px;
    height: 36px;
    font-size: 15px;
  }
}
</style>
