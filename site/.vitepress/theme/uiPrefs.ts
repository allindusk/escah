import { reactive, watch } from 'vue'

export interface UiPrefs {
  /** 超宽模式（默认关=标准居中宽度）：开启则侧栏贴最左、目录贴最右、正文填满中间 */
  ultraWide: boolean
  /** 收起左侧导航栏 */
  navCollapsed: boolean
  /** 收起右侧目录栏 */
  tocCollapsed: boolean
}

const KEY = 'escah-ui-prefs'

function load(): UiPrefs {
  const def: UiPrefs = { ultraWide: false, navCollapsed: false, tocCollapsed: false }
  if (typeof localStorage === 'undefined') return def
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) return { ...def, ...JSON.parse(raw) }
  } catch {
    /* ignore */
  }
  return def
}

export const uiPrefs = reactive<UiPrefs>(load())

export function applyUiClasses(): void {
  if (typeof document === 'undefined') return
  const el = document.documentElement
  el.classList.toggle('escah-ultrawide', uiPrefs.ultraWide)
  el.classList.toggle('escah-nav-collapsed', uiPrefs.navCollapsed)
  el.classList.toggle('escah-toc-collapsed', uiPrefs.tocCollapsed)
}

if (typeof window !== 'undefined') {
  applyUiClasses()
  watch(
    uiPrefs,
    () => {
      try {
        localStorage.setItem(KEY, JSON.stringify({ ...uiPrefs }))
      } catch {
        /* ignore */
      }
      applyUiClasses()
    },
    { deep: true },
  )
}
