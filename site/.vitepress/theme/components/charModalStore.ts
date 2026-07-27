import { reactive } from 'vue'

let hideTimer: number | undefined

export interface HoverAnchor {
  left: number
  top: number
  right: number
  bottom: number
  width: number
  height: number
}

/**
 * 角色详情悬浮窗全局状态。
 * 两种模式：
 *  - 'hover'  ：鼠标悬停在正文里的角色名/头像上时，贴着锚点显示的小预览窗
 *              （仅 5 项信息，不遮名字/头像，移出后自动消失）。
 *  - 'pinned' ：点击角色名/头像触发的固定大窗（全部信息、居中、可拖动、带遮罩与菜单栏）。
 */
export const charModalStore = reactive({
  visible: false,
  mode: 'hover' as 'hover' | 'pinned',
  name: '',
  // 居中默认位置；固定并拖动后使用显式坐标
  x: null as number | null,
  y: null as number | null,
  // hover 模式的锚点（触发元素的视口矩形），用于把预览窗贴在名字/头像旁边
  anchor: null as HoverAnchor | null,
  // 固定窗是否处于「可拖动 + 透明遮罩」状态（与旧版 pinned 语义一致）
  pinned: false,

  showHover(name: string, anchor: HoverAnchor) {
    window.clearTimeout(hideTimer)
    this.name = name
    this.mode = 'hover'
    this.anchor = anchor
    this.pinned = false
    this.x = null
    this.y = null
    this.visible = true
  },
  pin(name?: string) {
    window.clearTimeout(hideTimer)
    if (name) this.name = name
    this.mode = 'pinned'
    this.anchor = null
    this.pinned = true
    this.x = null
    this.y = null
    this.visible = true
  },
  scheduleHide() {
    if (this.mode === 'pinned') return
    window.clearTimeout(hideTimer)
    hideTimer = window.setTimeout(() => {
      if (this.mode !== 'pinned') this.visible = false
    }, 200)
  },
  cancelHide() {
    window.clearTimeout(hideTimer)
  },
  togglePin() {
    if (this.mode === 'pinned') this.unpin()
    else this.pin()
  },
  unpin() {
    // 从固定窗退回：无锚点可回贴，直接收起
    window.clearTimeout(hideTimer)
    this.visible = false
    this.mode = 'hover'
    this.anchor = null
    this.pinned = false
    this.x = null
    this.y = null
  },
  close() {
    window.clearTimeout(hideTimer)
    this.visible = false
    this.mode = 'hover'
    this.anchor = null
    this.pinned = false
    this.x = null
    this.y = null
  },
  setPos(x: number, y: number) {
    this.x = x
    this.y = y
  },
})
