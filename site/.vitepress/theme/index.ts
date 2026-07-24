import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import Layout from './Layout.vue'
import CharList from './components/CharList.vue'
import CharHoverModal from './components/CharHoverModal.vue'
import MetaBar from './components/MetaBar.vue'
import GlossaryTable from './components/GlossaryTable.vue'
import UpdatesLog from './components/UpdatesLog.vue'
import SiteMap from './components/SiteMap.vue'
import RecentUpdates from './components/RecentUpdates.vue'
import CategoryCards from './components/CategoryCards.vue'
import MirrorContent from './components/MirrorContent.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('CharList', CharList)
    app.component('CharHoverModal', CharHoverModal)
    app.component('MetaBar', MetaBar)
    app.component('GlossaryTable', GlossaryTable)
    app.component('UpdatesLog', UpdatesLog)
    app.component('SiteMap', SiteMap)
    app.component('RecentUpdates', RecentUpdates)
    app.component('CategoryCards', CategoryCards)
    app.component('MirrorContent', MirrorContent)
  },
} satisfies Theme
