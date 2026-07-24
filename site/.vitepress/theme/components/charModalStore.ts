import { reactive } from 'vue'

let hideTimer: number | undefined

/** 角色详情悬浮窗全局状态：悬停显示、点击固定、固定后可拖动 */
export const charModalStore = reactive({
  visible: false,
  pinned: false,
  name: '',
  // 居中默认位置；固定并拖动后使用显式坐标
  x: null as number | null,
  y: null as number | null,

  show(name: string) {
    window.clearTimeout(hideTimer)
    this.name = name
    this.visible = true
  },
  scheduleHide() {
    if (this.pinned) return
    window.clearTimeout(hideTimer)
    hideTimer = window.setTimeout(() => {
      if (!this.pinned) this.visible = false
    }, 280)
  },
  cancelHide() {
    window.clearTimeout(hideTimer)
  },
  togglePin() {
    this.pinned = !this.pinned
  },
  close() {
    this.visible = false
    this.pinned = false
    this.x = null
    this.y = null
  },
  setPos(x: number, y: number) {
    this.x = x
    this.y = y
  },
})
