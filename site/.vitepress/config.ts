import { defineConfig } from 'vitepress'
import sidebarJa from './generated/sidebar.ja.json'
import sidebarZh from './generated/sidebar.zh.json'

// CJK 自定义分词：单字 + bigram，保证中日文检索召回
const CJK_RE = /[぀-ヿ㐀-䶿一-鿿豈-﫿]/
function tokenize(text: string): string[] {
  const tokens: string[] = []
  for (const word of text.split(/[\s\-–—/\\,.;:!?()[\]{}<>"'`~@#$%^&*+=|、。・，；：！？「」『』（）]+/)) {
    if (!word) continue
    if (CJK_RE.test(word)) {
      for (const ch of word) tokens.push(ch)
      for (let i = 0; i < word.length - 1; i++) tokens.push(word.slice(i, i + 2))
    } else {
      tokens.push(word.toLowerCase())
    }
  }
  return tokens
}

const navJa = [
  { text: 'ホーム', link: '/ja/' },
  { text: 'キャラクター', link: '/ja/characters.html' },
  { text: 'ページ一覧', link: '/ja/sitemap.html' },
  { text: '更新履歴', link: '/ja/updates.html' },
  { text: '原文Wiki', link: 'https://escalationheroines.wikiru.jp/' },
]
const navZh = [
  { text: '首页', link: '/zh/' },
  { text: '角色一览', link: '/zh/characters.html' },
  { text: '全部页面', link: '/zh/sitemap.html' },
  { text: '更新记录', link: '/zh/updates.html' },
  { text: '原文Wiki', link: 'https://escalationheroines.wikiru.jp/' },
]

export default defineConfig({
  base: '/escah/',
  title: '超昂大戦 Wiki',
  description: '超昂大戦エスカレーションヒロインズ攻略 Wiki 中日双语镜像站',
  ignoreDeadLinks: true,
  locales: {
    root: {
      label: '日本語',
      lang: 'ja-JP',
      link: '/ja/',
      themeConfig: {
        nav: navJa,
        sidebar: sidebarJa,
        outline: { label: '目次' },
        docFooter: { prev: '前のページ', next: '次のページ' },
        lastUpdated: { text: '最終更新' },
        returnToTopLabel: 'トップへ戻る',
        darkModeSwitchLabel: 'ダークモード',
      },
    },
    zh: {
      label: '简体中文',
      lang: 'zh-CN',
      link: '/zh/',
      themeConfig: {
        nav: navZh,
        sidebar: sidebarZh,
        outline: { label: '目录' },
        docFooter: { prev: '上一页', next: '下一页' },
        lastUpdated: { text: '最后更新' },
        returnToTopLabel: '返回顶部',
        darkModeSwitchLabel: '深色模式',
      },
    },
  },
  themeConfig: {
    search: {
      provider: 'local',
      options: {
        locales: {
          zh: {
            translations: {
              button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
              modal: {
                noResultsText: '没有找到相关结果',
                resetButtonTitle: '清除搜索',
                footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' },
              },
            },
          },
        },
        miniSearch: { options: { tokenize } },
      },
    },
  },
})
