import { reactive, watch } from 'vue'

export interface UiPrefs {
  /** 超宽模式（默认关）：开启则侧栏贴最左、目录贴最右、正文填满中间；关=标准居中宽度 */
  ultraWide: boolean
  /** 收起左侧导航栏 */
  navCollapsed: boolean
  /** 收起右侧目录栏 */
  tocCollapsed: boolean
}

const KEY = 'escah-ui-prefs'
/** 存档版本：v3 起恢复「标准宽度」为默认（v2 期间默认超宽，v1 及更早也是标准） */
const VER = 3

/** 新访客的默认偏好（改这里必须同步 config.ts 里首屏预置脚本的判定） */
const DEFAULT: UiPrefs = { ultraWide: false, navCollapsed: false, tocCollapsed: false }

type StoredPrefs = Partial<UiPrefs> & { v?: number }

function load(): UiPrefs {
  if (typeof localStorage === 'undefined') return { ...DEFAULT }
  let saved: StoredPrefs | null = null
  try {
    const raw = localStorage.getItem(KEY)
    saved = raw ? (JSON.parse(raw) as StoredPrefs) : null
  } catch {
    saved = null
  }
  if (!saved) return { ...DEFAULT }

  const next: UiPrefs = { ...DEFAULT }
  // 旧存档里的 ultraWide 只是「当时的默认值」，无法区分用户是否主动选过，
  // 故每次变更默认值时（v2 超宽 → v3 标准）都不继承它，统一改用新默认；
  // 侧栏/目录的偏好照旧保留。
  if (Number(saved.v) >= VER && typeof saved.ultraWide === 'boolean') next.ultraWide = saved.ultraWide
  if (typeof saved.navCollapsed === 'boolean') next.navCollapsed = saved.navCollapsed
  if (typeof saved.tocCollapsed === 'boolean') next.tocCollapsed = saved.tocCollapsed
  return next
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
        localStorage.setItem(KEY, JSON.stringify({ ...uiPrefs, v: VER }))
      } catch {
        /* ignore */
      }
      applyUiClasses()
    },
    { deep: true },
  )
}
