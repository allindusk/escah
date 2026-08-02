/**
 * 表格增强：表头排序、列筛选（多选）、页面内全屏（居中留空）、图像/长文本列适配。
 * 由 MirrorContent.vue 在 v-html 注入后调用（enhanceTables）。
 */
import { charModalStore as charModalStore } from './components/charModalStore'
/**
 * 表头行块：表格开头“连续的全 th 行”（PukiWiki 双行表头常带 rowspan/colspan）。
 * 必须整块放进 <thead>：rowspan 无法跨 thead/tbody 行组生效，
 * 只搬第一行会把 rowspan=2 的表头拆成两截（错行/错列的根源）。
 */
function headerRowsOf(table: HTMLTableElement): HTMLTableRowElement[] {
  const thead = table.querySelector('thead')
  if (thead) {
    return (Array.from(thead.querySelectorAll('tr')) as HTMLTableRowElement[]).filter(
      (r) => !r.classList.contains('escah-tbl-filter-row')
    )
  }
  const out: HTMLTableRowElement[] = []
  for (const r of Array.from(table.querySelectorAll('tr')) as HTMLTableRowElement[]) {
    const cells = Array.from(r.children)
    const allTh = cells.length > 0 && cells.every((c) => c.tagName === 'TH')
    if (!allTh) break
    out.push(r)
  }
  return out
}

/**
 * 表头网格展开：算出每个 th 的起始叶列号与表格总列数（正确处理 rowspan/colspan）。
 * 供筛选行（每叶列一格）与排序（th→数据列映射）使用。
 */
function headerGrid(headerRows: HTMLTableRowElement[]): {
  colOf: Map<HTMLElement, number>
  totalCols: number
} {
  const occupied: boolean[][] = []
  const colOf = new Map<HTMLElement, number>()
  let totalCols = 0
  headerRows.forEach((row, ri) => {
    occupied[ri] = occupied[ri] || []
    let col = 0
    for (const cell of Array.from(row.children) as HTMLTableCellElement[]) {
      while (occupied[ri][col]) col++
      colOf.set(cell, col)
      const cs = cell.colSpan || 1
      const rs = cell.rowSpan || 1
      for (let r = ri; r < ri + rs; r++) {
        occupied[r] = occupied[r] || []
        for (let c = col; c < col + cs; c++) occupied[r][c] = true
      }
      col += cs
      totalCols = Math.max(totalCols, col)
    }
  })
  return { colOf, totalCols }
}

/** 数据区是否含合并单元格：含则 children[idx] ≠ 列号，排序/筛选/删列全部禁用以免错位。 */
function bodyHasSpans(table: HTMLTableElement): boolean {
  for (const r of dataRows(table)) {
    for (const c of Array.from(r.children) as HTMLTableCellElement[]) {
      if ((c.colSpan || 1) > 1 || (c.rowSpan || 1) > 1) return true
    }
  }
  return false
}

function getBody(table: HTMLTableElement): HTMLTableSectionElement {
  const tb = table.querySelector('tbody')
  return (tb as HTMLTableSectionElement) || (table as unknown as HTMLTableSectionElement)
}

function dataRows(table: HTMLTableElement): HTMLTableRowElement[] {
  const body = getBody(table)
  const filter = table.querySelector('.escah-tbl-filter-row') as HTMLElement | null
  const rows: HTMLTableRowElement[] = []
  body.querySelectorAll('tr').forEach((r) => {
    if (r !== filter) rows.push(r as HTMLTableRowElement)
  })
  return rows
}

/**
 * 规范化表格结构：确保表头在 <thead>、数据在 <tbody>。
 * 否则无 thead 的表格在排序时会把表头行当作数据行一起重排（表头被排序/数据被隐藏）。
 */
function normalizeTable(table: HTMLTableElement): void {
  let thead = table.querySelector('thead') as HTMLTableSectionElement | null
  let tbody = table.querySelector('tbody') as HTMLTableSectionElement | null
  const headerBlock = headerRowsOf(table)
  if (!thead && headerBlock.length > 0) {
    thead = document.createElement('thead')
    for (const r of headerBlock) thead.appendChild(r)
    table.insertBefore(thead, table.firstChild)
  }
  if (!tbody) {
    tbody = document.createElement('tbody')
    Array.from(table.querySelectorAll(':scope > tr')).forEach((r) =>
      tbody!.appendChild(r as HTMLTableRowElement)
    )
    table.appendChild(tbody)
  }
}

function filterRowOf(table: HTMLTableElement): HTMLElement | null {
  return table.querySelector('.escah-tbl-filter-row') as HTMLElement | null
}

function clearSortIndicators(table: HTMLTableElement): void {
  table.querySelectorAll('th').forEach((th) => {
    th.classList.remove('escah-sort-asc', 'escah-sort-desc')
  })
}

function resetOrder(table: HTMLTableElement): void {
  const orig = getOriginalRows(table)
  if (!orig) return
  const body = getBody(table)
  for (const r of orig) body.appendChild(r)
}

function getOriginalRows(table: HTMLTableElement): HTMLTableRowElement[] | null {
  const body = getBody(table)
  let orig = (body as unknown as { _escahOrig?: HTMLTableRowElement[] })._escahOrig
  if (!orig) {
    orig = dataRows(table)
    ;(body as unknown as { _escahOrig?: HTMLTableRowElement[] })._escahOrig = orig
  }
  return orig
}

/** 提取单元格数值（去千分位/单位），仅当整格为数字类时返回数值，否则 null */
function cellNumber(s: string): number | null {
  if (!s) return null
  const m = s.replace(/,/g, '').match(/-?\d+(\.\d+)?/)
  if (!m) return null
  const n = parseFloat(m[0])
  return isNaN(n) ? null : n
}

function sortByColumn(table: HTMLTableElement, col: number, dir: number): void {
  const body = getBody(table)
  const rows = dataRows(table)
  rows.sort((a, b) => {
    const av = (a.children[col]?.textContent || '').trim()
    const bv = (b.children[col]?.textContent || '').trim()
    const an = cellNumber(av)
    const bn = cellNumber(bv)
    let cmp: number
    if (an !== null && bn !== null) cmp = an - bn
    else cmp = av.localeCompare(bv)
    return cmp * dir
  })
  rows.forEach((r) => body.appendChild(r))
  applyColumnFilters(table)
}

// 预存在表格上的缓存：数据行元素数组 + 每行每列（小写、trim）文本，
// 供 applyColumnFilters 纯内存判断，避免反复 querySelectorAll + 读 textContent 触发强制布局。
type TblCache = HTMLTableElement & {
  _escahRows?: HTMLTableRowElement[]
  _escahRowText?: string[][]
}

function applyColumnFilters(table: HTMLTableElement): void {
  const filterRow = filterRowOf(table)
  if (!filterRow) return
  const cache = table as TblCache
  const dataRowEls = cache._escahRows || (dataRows(table) as HTMLTableRowElement[])
  const rowTexts = cache._escahRowText
  const cells = Array.from(filterRow.children) as HTMLElement[]
  // 收集每列激活的筛选条件：
  //  - 多选枚举列（checkbox）：列内取“或”，值用「精确相等」匹配——
  //    否则稀有度 SSR/SR/R 互为子串（"ssr".includes("r") 为真）会互相误匹配。
  //  - 自由文本列（input.escah-col-filter）：值用「子串包含」匹配。
  //  多列之间取“与”：所有列的条件同时满足才显示。
  type FilterCond = { idx: number; mode: 'exact' | 'substr'; vals: string[] }
  const active: FilterCond[] = []
  cells.forEach((cell, idx) => {
    if (cell.classList.contains('escah-col-filter-none')) return
    const checked = Array.from(
      cell.querySelectorAll('input[type="checkbox"]:checked')
    ) as HTMLInputElement[]
    const cvals = checked
      .map((c) => (c.value || '').trim().toLowerCase())
      .filter(Boolean)
    if (cvals.length) {
      active.push({ idx, mode: 'exact', vals: cvals })
      return
    }
    const inp = cell.querySelector('input.escah-col-filter') as HTMLInputElement | null
    if (inp && inp.value.trim()) {
      active.push({ idx, mode: 'substr', vals: [inp.value.trim().toLowerCase()] })
    }
  })
  // 切换大量行的 display 前先隐藏整表，抑制逐行中间重绘；下一帧一次性恢复，
  // 浏览器只做一次完整布局/绘制，避免取消筛选（数百行宽表恢复）时的多次重绘卡顿。
  const restoring = active.length === 0 || dataRowEls.some((r) => r.style.display === 'none')
  if (restoring) table.style.visibility = 'hidden'
  const finish = () => {
    requestAnimationFrame(() => {
      table.style.visibility = ''
    })
  }
  if (!active.length) {
    dataRowEls.forEach((r) => (r.style.display = ''))
    finish()
    return
  }
  dataRowEls.forEach((r, ri) => {
    let show = true
    for (const f of active) {
      const txt =
        rowTexts && rowTexts[ri]
          ? (rowTexts[ri][f.idx] ?? '')
          : ((r.children[f.idx]?.textContent || '').trim().toLowerCase())
      if (f.mode === 'exact') {
        // 枚举列：该列值必须精确等于某个勾选项
        if (!f.vals.includes(txt)) show = false
      } else {
        // 自由文本列：该列值包含关键字即命中
        if (!f.vals.some((v) => txt.includes(v))) show = false
      }
      if (!show) break
    }
    r.style.display = show ? '' : 'none'
  })
  finish()
}

function resetTable(table: HTMLTableElement): void {
  resetOrder(table)
  clearSortIndicators(table)
  ;(table as unknown as { col?: number }).col = undefined
  ;(table as unknown as { dir?: number }).dir = undefined
  const filterRow = filterRowOf(table)
  if (filterRow) {
    // 清空多选：取消勾选、复原按钮文字、去掉高亮整格
    filterRow.querySelectorAll('input[type="checkbox"]').forEach((c) => {
      ;(c as HTMLInputElement).checked = false
    })
    filterRow.querySelectorAll('.escah-filter-btn').forEach((b) => {
      ;(b as HTMLElement).textContent = '筛选 ▾'
    })
    filterRow.querySelectorAll('input.escah-col-filter').forEach((i) => {
      ;(i as HTMLInputElement).value = ''
    })
    filterRow.querySelectorAll('td').forEach((td) => {
      td.classList.remove('escah-filter-active')
    })
  }
  applyColumnFilters(table)
}

function buildColumnFilterRow(table: HTMLTableElement): void {
  if (table.querySelector('.escah-tbl-filter-row')) return
  if (bodyHasSpans(table)) return
  const headerRows = headerRowsOf(table)
  if (!headerRows.length) return
  const { totalCols } = headerGrid(headerRows)
  const rows = dataRows(table)
  if (!rows.length || !totalCols) return
  // 预存每行每列的小写 trim 文本 + 数据行数组，供 applyColumnFilters 纯内存判定，
  // 避免勾选/取消时反复 querySelectorAll 与读 textContent（后者易触发强制布局）。
  const rowTexts: string[][] = rows.map((r) => {
    const arr: string[] = []
    for (let c = 0; c < totalCols; c++) {
      const dc = r.children[c] as HTMLElement | undefined
      arr.push(((dc?.textContent || '').trim().toLowerCase()))
    }
    return arr
  })
  ;(table as TblCache)._escahRows = rows as HTMLTableRowElement[]
  ;(table as TblCache)._escahRowText = rowTexts
  const filterRow = document.createElement('tr')
  filterRow.className = 'escah-tbl-filter-row'
  let hasAnyFilter = false
  for (let c = 0; c < totalCols; c++) {
    const cell = document.createElement('td')
    cell.className = 'escah-col-filter-none'
    filterRow.appendChild(cell)
    const vals = new Set<string>()
    for (const r of rows) {
      const dc = r.children[c] as HTMLElement | undefined
      if (!dc) continue
      const t = (dc.textContent || '').trim()
      if (t) vals.add(t)
    }
    if (vals.size === 0) continue
    hasAnyFilter = true
    cell.classList.remove('escah-col-filter-none')
    cell.classList.add('escah-col-filter')
    if (vals.size <= 50) {
      // 枚举适中的列 → 多选下拉（checkbox popover，OR 逻辑）
      const wrap = document.createElement('div')
      wrap.className = 'escah-filter-multi'
      const btn = document.createElement('button')
      btn.type = 'button'
      btn.className = 'escah-filter-btn'
      btn.textContent = '筛选 ▾'
      btn.title = '点击勾选要保留的值（可多选）'
      const pop = document.createElement('div')
      pop.className = 'escah-filter-pop'
      const sorted = [...vals].sort((a, b) => a.localeCompare(b))
      sorted.forEach((v) => {
        const label = document.createElement('label')
        label.className = 'escah-filter-opt'
        const cb = document.createElement('input')
        cb.type = 'checkbox'
        cb.value = v
        cb.addEventListener('change', () => {
          const n = pop.querySelectorAll('input[type="checkbox"]:checked').length
          btn.textContent = n > 0 ? `筛选·${n} ▾` : '筛选 ▾'
          // 操作后高亮整格（escah-filter-active），让用户一眼看到对哪列做了筛选
          cell.classList.toggle('escah-filter-active', n > 0)
          applyColumnFilters(table)
        })
        label.appendChild(cb)
        label.appendChild(document.createTextNode(' ' + v))
        pop.appendChild(label)
      })
      const toggle = (e: MouseEvent) => {
        e.stopPropagation()
        const open = pop.classList.contains('open')
        document.querySelectorAll('.escah-filter-pop.open').forEach((p) => p.classList.remove('open'))
        if (!open) pop.classList.add('open')
      }
      btn.addEventListener('click', toggle)
      pop.addEventListener('click', (e) => e.stopPropagation())
      wrap.append(btn, pop)
      cell.appendChild(wrap)
    } else {
      // 高基数自由文本列 → “包含”文本框实时筛选
      const inp = document.createElement('input')
      inp.type = 'text'
      inp.className = 'escah-col-filter'
      inp.placeholder = '包含筛选…'
      inp.title = '输入关键字，仅显示该列包含此文本的行'
      inp.addEventListener('input', () => {
        cell.classList.toggle('escah-filter-active', inp.value.trim().length > 0)
        applyColumnFilters(table)
      })
      cell.appendChild(inp)
    }
  }
  if (!hasAnyFilter) return
  const lastHeader = headerRows[headerRows.length - 1]
  const thead = lastHeader.parentElement as HTMLElement
  thead.insertBefore(filterRow, lastHeader.nextSibling)
}

function makeSortable(table: HTMLTableElement): void {
  if (bodyHasSpans(table)) return
  const headerRows = headerRowsOf(table)
  if (!headerRows.length) return
  const { colOf } = headerGrid(headerRows)
  const ths = headerRows.flatMap(
    (r) => Array.from(r.children).filter((c) => c.tagName === 'TH') as HTMLTableCellElement[]
  )
  ths.forEach((th) => {
    if (th.classList.contains('escah-no-sort')) return
    if ((th.colSpan || 1) > 1) return
    const idx = colOf.get(th)
    if (idx === undefined) return
    th.classList.add('escah-sortable')
    th.addEventListener('click', (e) => {
      e.stopPropagation()
      const cur = (table as unknown as { col?: number }).col
      const c = (table as unknown as { dir?: number }).dir ?? 0
      let dir: number
      if (cur === idx) dir = c === 1 ? -1 : c === -1 ? 0 : 1
      else dir = 1
      if (dir === 0) {
        resetOrder(table)
        clearSortIndicators(table)
        ;(table as unknown as { col?: number }).col = undefined
        ;(table as unknown as { dir?: number }).dir = undefined
        applyColumnFilters(table)
        return
      }
      clearSortIndicators(table)
      sortByColumn(table, idx, dir)
      th.classList.add(dir === 1 ? 'escah-sort-asc' : 'escah-sort-desc')
      ;(table as unknown as { col?: number }).col = idx
      ;(table as unknown as { dir?: number }).dir = dir
    })
  })
}

/**
 * 标记图像单元格（固定最小宽度保证图片正常显示）与超长文本单元格（限高并加宽）。
 */
function markSpecialColumns(table: HTMLTableElement): void {
  for (const row of dataRows(table)) {
    for (const cell of Array.from(row.children) as HTMLElement[]) {
      const img = cell.querySelector('img')
      if (img) {
        const w = parseInt(img.getAttribute('width') || '', 10)
        const mw = Math.max(64, Math.min(isNaN(w) || !w ? 120 : w, 280))
        cell.classList.add('escah-img-col')
        cell.style.minWidth = mw + 'px'
      }
      if ((cell.textContent || '').trim().length > 40) cell.classList.add('escah-long')
    }
  }
}

/**
 * 图标列表竖向堆叠：单元格内容“除图片链接外无其它文字”时
 * （纯图标列表 / 图标+其名称），把图片链接改为竖向排列，避免横排挤一行。
 */
function applyImageStack(table: HTMLTableElement): void {
  for (const cell of Array.from(table.querySelectorAll('td, th')) as HTMLElement[]) {
    const anchors = Array.from(cell.querySelectorAll('a')).filter((a) => a.querySelector('img'))
    if (anchors.length === 0) continue
    const probe = cell.cloneNode(true) as HTMLElement
    probe.querySelectorAll('a, img').forEach((e) => e.remove())
    const rest = (probe.textContent || '').replace(/\s+/g, '')
    if (rest.length === 0) {
      cell.classList.add(anchors.length === 1 ? 'escah-img-stack' : 'escah-img-row')
    }
  }
}

// 全屏状态：移动真实表格容器，保证内容/功能与页面内完全一致
interface FsState {
  container: HTMLElement
  parent: HTMLElement
  next: Node | null
  table: HTMLTableElement
}
let fsState: FsState | null = null

function onFsKey(e: KeyboardEvent): void {
  if (e.key === 'Escape') {
    if (charModalStore.visible) return
    closeFullscreen()
  }
}

// 滚动时把冻结的表头/首列/角落/筛选行切为「不透明实色」（内联最高优先级，盖过任何 CSS），
// 避免半透明底色透出底下滚动经过的数据文字；静止 150ms 后清除内联背景 → 恢复原来的
// --escah-grad-soft 半透明样式。用内联而非 class 切换，避免 CSS 层叠优先级踩坑。
function freezeCellsOpaque(scroller: HTMLElement, on: boolean): void {
  const root = scroller.querySelector('table')
  if (!root) return
  const cells = root.querySelectorAll(
    'thead th, thead .escah-tbl-filter-row td, th:first-child, td:first-child'
  )
  // 滚动不透明实色：与常态 --escah-grad-soft 同色系（紫），只是不透明，避免切到白底难看
  const opaque = scroller.classList.contains('escah-dark') || document.documentElement.classList.contains('dark')
    ? '#2c2238'
    : '#e3b9ec'
  cells.forEach((c) => {
    const el = c as HTMLElement
    if (on) {
      if (el.style.background !== opaque) el.dataset.escahBg = el.style.background
      el.style.background = opaque
    } else if (el.dataset.escahBg !== undefined) {
      el.style.background = el.dataset.escahBg
      delete el.dataset.escahBg
    }
  })
}

function bindScrollOpacity(scroller: HTMLElement): void {
  let timer: number | undefined
  const onScroll = () => {
    freezeCellsOpaque(scroller, true)
    if (timer) window.clearTimeout(timer)
    timer = window.setTimeout(() => freezeCellsOpaque(scroller, false), 150)
  }
  scroller.addEventListener('scroll', onScroll, { passive: true })
}

function openFullscreen(table: HTMLTableElement): void {
  closeFullscreen()
  const container = table.closest('.escah-tbl') as HTMLElement | null
  if (!container) return
  const parent = container.parentNode as HTMLElement
  const next = container.nextSibling
  const overlay = document.createElement('div')
  overlay.className = 'escah-tbl-fs'
  const panel = document.createElement('div')
  panel.className = 'escah-tbl-fs-panel'
  const bar = document.createElement('div')
  bar.className = 'escah-tbl-fs-bar'
  const title = document.createElement('span')
  title.textContent = '表格全屏浏览（页面内）'
  const closeBtn = document.createElement('button')
  closeBtn.className = 'escah-tbl-btn escah-tbl-fs-close'
  closeBtn.textContent = '✕ 关闭'
  closeBtn.title = '关闭全屏（Esc）'
  closeBtn.addEventListener('click', () => closeFullscreen())
  bar.append(title, closeBtn)
  const scroll = document.createElement('div')
  scroll.className = 'escah-tbl-fs-scroll'
  scroll.appendChild(container) // 移动真实表格（含工具栏/排序/筛选），与原表格完全一致
  // ⚠️ 关键（2026-08-02 修复）：全屏时**只**对正文里原本就是 shrink 的表（角色一览类等）
  // 沿用 fixed 布局 + 内联 width:0 兜底，避免列宽回到 auto 与正文不一致。
  // 非 shrink 表（绝大多数普通内容表）正文是 auto + max-content，全屏后应保持不变——
  // 若这里也强加 escah-tbl-shrink + fixed，会被全屏 CSS 的 width:auto!important 破坏，
  // 导致全屏后样式全部错乱（这正是除 characters/ssr/sr/r 外页面全屏错乱的根因）。
  if (table.classList.contains('escah-tbl-shrink')) {
    table.style.tableLayout = 'fixed'
    table.style.minWidth = '0'
    table.style.width = '0' // 同 shrinkColumnsToData：必须 0 而非 auto，否则按内容撑开、<col> 失效
  }
  bindScrollOpacity(scroll) // 全屏滚动时冻结单元格切不透明
  panel.append(bar, scroll)
  overlay.appendChild(panel)
  overlay.addEventListener('mousedown', (e) => {
    if (e.target === overlay) closeFullscreen()
  })
  document.body.appendChild(overlay)
  fsState = { container, parent, next, table }
  document.addEventListener('keydown', onFsKey)
}

function closeFullscreen(): void {
  if (charModalStore.mode === 'hover' && charModalStore.visible) charModalStore.close()
  if (fsState) {
    const { container, parent, next, table } = fsState
    // 关键：关闭全屏前，清掉表格上「滚动时」残留的内联不透明背景。
    // 否则若关闭瞬间正处于滚动态（150ms 还原定时器尚未触发），残留内联 background
    // 会随同一张 table 元素被移回正文，导致正文表格表头/首列变成不透明实色，
    // 失去常态半透明样式。
    const root = table.closest('.escah-tbl-fs-scroll')?.querySelector('table') || table
    root.querySelectorAll(
      'thead th, thead .escah-tbl-filter-row td, th:first-child, td:first-child'
    ).forEach((c) => {
      const el = c as HTMLElement
      el.style.background = ''
      delete el.dataset.escahBg
    })
    // 关键（2026-08-02 修复）：若表格**不是**正文里的 shrink 表（普通内容表），
    // 全屏期间可能被旧版逻辑强加过 escah-tbl-shrink 类 + fixed/width:0 内联样式，
    // 关闭后这张表被移回正文，残留的 fixed 布局会让正文表格同样错乱。
    // 这里对称清理（仅对非 shrink 表），让正文恢复 auto + max-content 布局。
    // shrink 表正文本身就带该 class 与内联 fixed，故不会被误清（用 contains 判断）。
    if (!table.classList.contains('escah-tbl-shrink')) {
      table.classList.remove('escah-tbl-shrink')
      table.style.removeProperty('table-layout')
      table.style.removeProperty('width')
      table.style.removeProperty('min-width')
    }
    if (next) parent.insertBefore(container, next)
    else parent.appendChild(container)
    fsState = null
  }
  const ov = document.querySelector('.escah-tbl-fs')
  if (ov) ov.remove()
  document.removeEventListener('keydown', onFsKey)
}

function toggleFullscreen(table: HTMLTableElement): void {
  if (fsState && fsState.table === table) closeFullscreen()
  else openFullscreen(table)
}

function syncFullBtnFor(
  _container: HTMLElement,
  wrapper: HTMLElement,
  toolbar: HTMLElement,
  btnFull: HTMLElement
): void {
  const overflowing = wrapper.scrollWidth > wrapper.clientWidth + 1
  btnFull.style.display = overflowing ? '' : 'none'
  const visible = toolbar.querySelector('button:not([style*="display: none"])')
  toolbar.style.display = visible ? '' : 'none'
}

let resizeBound = false
function syncAllFullBtns(): void {
  document.querySelectorAll('.escah-tbl').forEach((c) => {
    const w = c.querySelector('.table-scroll') as HTMLElement | null
    const t = c.querySelector('.escah-tbl-toolbar') as HTMLElement | null
    const b = c.querySelector('.escah-tbl-full-btn') as HTMLElement | null
    if (w && t && b) syncFullBtnFor(c as HTMLElement, w, t, b)
  })
}
function bindFullBtnResize(): void {
  if (resizeBound) return
  resizeBound = true
  window.addEventListener('resize', syncAllFullBtns)
}

function mkBtn(label: string, title: string, onClick: (e: MouseEvent) => void): HTMLButtonElement {
  const b = document.createElement('button')
  b.className = 'escah-tbl-btn'
  b.textContent = label
  b.title = title
  b.addEventListener('click', (e) => {
    e.stopPropagation()
    onClick(e)
  })
  return b
}

// 列宽按数据最长字符为准的页面（角色一览类，属性多为短数字、表头反而更长）
// 用「前缀匹配」而非精确集合：relativePath 解析出的 slug 可能因目录式路由/
// 大小写等偏差（如 characters/index、Characters）而漏匹配，之前因此 shrink 完全没触发。
const SHRINK_PREFIXES = ['characters', 'list-ssr', 'list-sr', 'list-r', 'list-npc']
function shouldShrink(pageSlug?: string): boolean {
  if (!pageSlug) return false
  const slug = pageSlug.toLowerCase()
  return SHRINK_PREFIXES.some((p) => slug === p || slug.startsWith(p + '/') || slug.startsWith(p + '-'))
}

/**
 * 列宽按“数据区最长内容”的像素宽为准（忽略表头）：
 * 用脱离表格布局的临时 <span> 测每格内容真实宽，取列最大值 → 写进 <col> 的 width。
 * 表头不参与测量、在 CSS 里 break-all 强制换行，因此列宽完全由数据决定，
 * 长中文表头（如“行动速度”）在窄数据列里自动换行。
 *
 * ⚠️ 列宽生效的两个前提（缺一个都会被打回内容最小宽，名称列 81px）：
 *  1) table-layout:fixed 下「首行单元格的显式 width」优先级高于 <col>，
 *     故必须清掉 <th> 的内联/属性 width（本函数做），且 CSS 里 shrink 表的
 *     th/td 要 width:unset!important（撤掉通用规则的 width:auto!important）。
 *  2) 表格不能被 min-width:100% 拉伸后均分，故内联 min-width:0 + width:auto。
 */
function shrinkColumnsToData(table: HTMLTableElement): void {
  if (bodyHasSpans(table)) return
  const rows = dataRows(table)
  if (!rows.length) return
  let ncols = 0
  for (const r of rows) ncols = Math.max(ncols, r.children.length)
  if (!ncols) return

  // PukiWiki 原 HTML 会给 <th> 带内联 width:Npx。挂上 fixed 布局后，
  // 「首行单元格的显式 width」优先级高于 <col> → 内联 width 会直接压掉我们算出的列宽。
  // CSS 的 width:unset!important 管不了内联样式，必须在这里永久清掉（不再恢复）。
  const headerCells = Array.from(table.querySelectorAll('thead th')) as HTMLElement[]
  headerCells.forEach((th) => {
    th.style.removeProperty('width')
    th.removeAttribute('width')
  })

  const maxPx = new Array(ncols).fill(0)
  const isImgCol = new Array(ncols).fill(false)
  let imgWidth = 110

  // 筛选行的「筛选 ▾」按钮下限：fixed 布局下单元格的 min-width 不生效（列宽只认 <col>），
  // 所以必须让 <col> 本身 ≥ 按钮宽，否则窄数字列的筛选按钮会溢出、与相邻列重叠（标签重合）。
  const FILTER_BTN_MIN = 76

  // 测量：用「脱离表格布局」的临时 span 读取每个单元格内容的真实像素宽，
  // 完全不受 table-layout:auto/fixed 或相邻列约束干扰（之前用 cell.scrollWidth
  // 在 auto 布局下会被整行列宽分配虚高，导致 col 宽度远大于真实内容宽，
  // 列虚胖、名字虽不换行却留大片空白）。span 取 display:inline-block + nowrap，
  // 直接反映内容最小宽；padding（单元格左右各 10px）单独补偿。
  // ⚠️ 关键（2026-08-02 修复）：测量 span 必须继承**表格实际单元格**的 font-size/font-family，
  // 否则脱离文档流后它继承 body 默认 16px（而 shrink 表单元格实际是 13px）→ 测宽虚高约 23%，
  // 名称列被撑到 217px 而视觉最长名字远没那么宽。这里从首个数据单元格取计算样式套上去。
  const sampleCell = rows[0]?.children[0] as HTMLElement | undefined
  const cs = sampleCell ? getComputedStyle(sampleCell) : null
  const span = document.createElement('span')
  span.style.cssText =
    'position:absolute;left:-99999px;top:0;visibility:hidden;white-space:nowrap;display:inline-block;' +
    `font-size:${cs ? cs.fontSize : '13px'};font-family:${cs ? cs.fontFamily : 'inherit'};`
  document.body.appendChild(span)
  const CELL_PAD = 20 // 单元格 padding 左右之和（5px 10px → 10+10）
  // 数据行（tbody）
  for (const r of rows) {
    for (let c = 0; c < ncols; c++) {
      const cell = r.children[c] as HTMLElement | undefined
      if (!cell) continue
      const img = cell.querySelector('img')
      if (img) {
        isImgCol[c] = true
        const w = parseInt(img.getAttribute('width') || '', 10)
        if (!isNaN(w) && w > imgWidth) imgWidth = Math.min(w, 280)
        continue
      }
      // 克隆单元格内部 HTML 进 span（保留 <a>/<br> 等结构），测真实内容宽
      span.innerHTML = cell.innerHTML
      const w = span.getBoundingClientRect().width + CELL_PAD
      if (w > maxPx[c]) maxPx[c] = w
    }
  }
  // 筛选行（thead 内 .escah-tbl-filter-row，enhanceTable 先于 shrink 创建）：
  // 把每列筛选按钮的真实宽纳入列宽下限，保证按钮不被压窄。
  const filterRow = table.querySelector('.escah-tbl-filter-row') as HTMLElement | null
  if (filterRow) {
    for (let c = 0; c < ncols; c++) {
      const cell = filterRow.children[c] as HTMLElement | undefined
      if (!cell) continue
      const btn = cell.querySelector('.escah-filter-btn') as HTMLElement | null
      if (!btn) continue
      const w = btn.getBoundingClientRect().width + CELL_PAD
      if (w > maxPx[c]) maxPx[c] = w
    }
  }
  document.body.removeChild(span)

  const colgroup = document.createElement('colgroup')
  for (let c = 0; c < ncols; c++) {
    const col = document.createElement('col')
    if (isImgCol[c]) col.style.width = imgWidth + 'px'
    else col.style.width = Math.max(FILTER_BTN_MIN, Math.round(maxPx[c]) + 2) + 'px'
    colgroup.appendChild(col)
  }
  const old = table.querySelector('colgroup')
  if (old) old.remove()
  table.insertBefore(colgroup, table.firstChild)
  table.classList.add('escah-tbl-shrink')
  // 内联兜底（最高优先级，压过任何 CSS 层叠歧义）：
  // 1) table-layout:fixed —— 列宽严格由 <col> 决定，auto 算法不再按内容撑列。
  // 2) min-width:0 —— 取消 .table-scroll>table 的 min-width:100%，表格不被拉伸到容器宽。
  // 3) width:0 —— ⚠️ 必须是 0，不能是 auto！通用规则是 width:max-content!important，
  //    auto 在 fixed 下仍会退化成「按内容撑开」（实测 2336px > 各 col 之和 2037px），
  //    多出的 299px 会被 fixed 按比例摊派回各列，导致 <col> 形同虚设
  //    （名称列声明 217px 却渲染 81px、角色名折行）。width:0 让表格不主动撑开，
  //    fixed 下宽度自然收敛为各 <col> 之和。
  table.style.tableLayout = 'fixed'
  table.style.minWidth = '0'
  table.style.width = '0'
}

/** 测量表头高度（不含筛选行），供筛选行吸顶时偏移，避免与表头重叠 */
function measureHeadHeight(table: HTMLTableElement): void {
  const headerRows = headerRowsOf(table)
  let h = 0
  for (const r of headerRows) {
    if (r.classList.contains('escah-tbl-filter-row')) continue
    h += r.getBoundingClientRect().height
  }
  if (h > 0) table.style.setProperty('--escah-thead-h', Math.ceil(h) + 'px')
}

function enhanceTable(table: HTMLTableElement, pageSlug?: string): void {
  if (table.getAttribute('data-escah') === '1') return
  normalizeTable(table)
  getOriginalRows(table)
  const smallTable = dataRows(table).length < 20
  if (!smallTable) {
    buildColumnFilterRow(table) // 多选筛选（含 OR 逻辑）
    makeSortable(table)
  }
  markSpecialColumns(table)
  applyImageStack(table)
  const doShrink = shouldShrink(pageSlug)
  if (import.meta.env.DEV) console.log('[escah-tbl] slug=', pageSlug, 'shrink=', doShrink)
  if (doShrink) shrinkColumnsToData(table)

  let wrapper = table.parentElement
  if (!wrapper || !wrapper.classList.contains('table-scroll')) {
    wrapper = document.createElement('div')
    wrapper.className = 'table-scroll'
    table.parentNode?.insertBefore(wrapper, table)
    wrapper.appendChild(table)
  }
  const container = document.createElement('div')
  container.className = 'escah-tbl'
  wrapper.parentNode?.insertBefore(container, wrapper)
  container.appendChild(wrapper)

  const toolbar = document.createElement('div')
  toolbar.className = 'escah-tbl-toolbar'
  // 全屏 + 重置 放在同一工具条（同一行）
  const btnFull = mkBtn('表格全屏', '页面内全屏查看（仅在表格超出可视宽度时出现）', () => toggleFullscreen(table))
  btnFull.classList.add('escah-tbl-full-btn')
  toolbar.appendChild(btnFull)
  if (!smallTable) {
    const btnReset = mkBtn('表格重置', '重置排序与筛选（清空多选）', () => resetTable(table))
    toolbar.appendChild(btnReset)
  }
  container.insertBefore(toolbar, wrapper)

  requestAnimationFrame(() => syncFullBtnFor(container, wrapper, toolbar, btnFull))
  bindFullBtnResize()
  measureHeadHeight(table)

  table.setAttribute('data-escah', '1')
}

// 真实表格 class 是 PukiWiki 自带的 style_table（全站一致），同时兼容 escah-tbl。
export function enhanceTables(root: HTMLElement, pageSlug?: string): void {
  for (const tbl of Array.from(
    root.querySelectorAll('table.style_table, table.escah-tbl')
  )) {
    enhanceTable(tbl as HTMLTableElement, pageSlug)
  }
  // bedroom-scenes 等「每个表格前已有 strong 标题」的页面：在正文开头插入一个
  // 表格目录（列出各表标题并锚点跳转）。标题文字直接取表格前已有的 strong，不重复添加。
  if (pageSlug === 'bedroom-scenes') buildTableToc(root)
}

/**
 * 页内表格目录：扫描页面内各表格前已有的 strong 标题（如「SSR角色（常驻）」），
 * 给每张表格容器打锚点 id，并在正文开头注入一个 <nav> 目录，点击平滑跳转。
 * 仅用于「标题已经在表格前面」的页面（bedroom-scenes），不额外新增标题。
 */
function buildTableToc(root: HTMLElement): void {
  const scrolls = Array.from(
    root.querySelectorAll('.table-scroll')
  ) as HTMLElement[]
  if (scrolls.length < 2) return // 单表页没必要做目录

  // 沿 previousElementSibling 链（含逐级父级的兄弟）找第一个含非空 strong 的块
  function titleBefore(scroll: HTMLElement): HTMLElement | null {
    let sib = scroll.previousElementSibling as HTMLElement | null
    while (sib) {
      const st = sib.querySelector('strong')
      if (st && st.textContent && st.textContent.trim()) return st
      sib = sib.previousElementSibling as HTMLElement | null
    }
    let p = scroll.parentElement
    while (p) {
      sib = p.previousElementSibling as HTMLElement | null
      while (sib) {
        const st = sib.querySelector('strong')
        if (st && st.textContent && st.textContent.trim()) return st
        sib = sib.previousElementSibling as HTMLElement | null
      }
      p = p.parentElement
    }
    return null
  }

  const items: { id: string; text: string }[] = []
  scrolls.forEach((scroll, i) => {
    const st = titleBefore(scroll)
    const text = st ? st.textContent!.trim() : `表格 ${i + 1}`
    const id = `escah-tbl-toc-${i + 1}`
    scroll.id = id
    items.push({ id, text })
  })

  if (items.length === 0) return
  // 避免重复注入（enhanceTables 可能被多次调用）
  const existing = root.querySelector('.escah-table-toc')
  if (existing) existing.remove()

  const nav = document.createElement('nav')
  nav.className = 'escah-table-toc'
  const title = document.createElement('p')
  title.className = 'escah-table-toc-title'
  title.textContent = '表格目录'
  nav.appendChild(title)
  const ul = document.createElement('ul')
  for (const it of items) {
    const li = document.createElement('li')
    const a = document.createElement('a')
    a.href = '#' + it.id
    a.textContent = it.text
    li.appendChild(a)
    ul.appendChild(li)
  }
  nav.appendChild(ul)
  // 插入到正文内容的最前面（mirror-content 首个子节点之前）
  root.insertBefore(nav, root.firstChild)
  // 通知右侧 DocOutline 重建大纲（收集本目录的锚点项）。DocOutline 在挂载时
  // 可能早于本函数执行，故用事件解耦，确保表格目录也出现在右侧目录导航里。
  document.dispatchEvent(new Event('escah:table-toc-built'))
}

export function destroyTables(_el: HTMLElement): void {
  closeFullscreen()
}
