import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import Layout from './Layout.vue'
import CharHoverModal from './components/CharHoverModal.vue'
import MetaBar from './components/MetaBar.vue'
import UpdatesLog from './components/UpdatesLog.vue'
import UpdateRecord from './components/UpdateRecord.vue'
import RecentUpdates from './components/RecentUpdates.vue'
import MirrorChangelog from './components/MirrorChangelog.vue'
import CategoryCards from './components/CategoryCards.vue'
import MirrorContent from './components/MirrorContent.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('CharHoverModal', CharHoverModal)
    app.component('MetaBar', MetaBar)
    app.component('UpdatesLog', UpdatesLog)
    app.component('UpdateRecord', UpdateRecord)
    app.component('RecentUpdates', RecentUpdates)
    app.component('MirrorChangelog', MirrorChangelog)
    app.component('CategoryCards', CategoryCards)
    app.component('MirrorContent', MirrorContent)
  },
} satisfies Theme
