<script setup lang="ts">
import { computed } from 'vue'
import { useData, withBase } from 'vitepress'

const { lang } = useData()

const cards = computed(() => {
  const zh = lang.value.startsWith('zh')
  const prefix = zh ? 'zh/' : 'ja/'
  const link = (slug: string) => withBase(prefix + slug + '.html')
  return zh
    ? [
        { icon: '🗡️', title: '角色', desc: 'SSR / SR / R 全角色图鉴', href: link('characters') },
        { icon: '✨', title: '技能与效果', desc: '必杀技 · 固有效果 · 特殊属性', href: link('skills') },
        { icon: '🛡️', title: '装备与道具', desc: '装备 · 超昂装备 · 道具一览', href: link('equipment') },
        { icon: '⚔️', title: '战斗系统', desc: '讨伐战 · 强敌战 · 广域战', href: link('battle') },
        { icon: '📜', title: '任务与活动', desc: '主线 · 每日 · 使命 · 活动', href: link('main-story') },
        { icon: '📖', title: '攻略指南', desc: '前期指南 · FAQ · 术语', href: link('getting-started') },
      ]
    : [
        { icon: '🗡️', title: 'キャラクター', desc: 'SSR / SR / R 全キャラ図鑑', href: link('characters') },
        { icon: '✨', title: 'スキル・効果', desc: '必殺技・固有効果・特殊属性', href: link('skills') },
        { icon: '🛡️', title: '装備・アイテム', desc: '装備・超昂装備・アイテム一覧', href: link('equipment') },
        { icon: '⚔️', title: '戦闘システム', desc: 'レイド・強敵戦・広域戦', href: link('battle') },
        { icon: '📜', title: 'クエスト', desc: 'メイン・デイリー・ミッション', href: link('main-story') },
        { icon: '📖', title: '攻略ガイド', desc: '序盤の手引き・FAQ・用語', href: link('getting-started') },
      ]
})
</script>

<template>
  <div class="category-cards">
    <a v-for="c in cards" :key="c.title" class="category-card" :href="c.href">
      <div class="icon">{{ c.icon }}</div>
      <h3>{{ c.title }}</h3>
      <p>{{ c.desc }}</p>
    </a>
  </div>
</template>
