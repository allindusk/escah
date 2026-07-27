/**
 * 表格增强：表头排序、列筛选、页面内全屏、图像/长文本列适配。
 * 由 MirrorContent.vue 在 v-html 注入后调用（enhanceTables）。
 */
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
  // ⚠️ 整块搬移表头：连续的全 th 行（含 rowspan/colspan 的双行表头）必须一起进 thead，
  // 只搬第一行会把 rowspan=2 表头拆断（历史 bug：表头分两行错位、第二表头行被当数据排序）。
  const headerBlock = headerRowsOf(table)
  if (!thead && headerBlock.length > 0) {
    thead = document.createElement('thead')
    for (const r of headerBlock) thead.appendChild(r)
    table.insertBefore(thead, table.firstChild)
  }
  if (!tbody) {
    tbody = document.createElement('tbody')
    // 仅把表头以外的直接子 <tr> 移入 tbody（按列筛选行尚未生成）
    Array.from(table.querySelectorAll(':scope > tr')).forEach((r) =>
      tbody!.appendChild(r as HTMLTableRowElement)
    )
    table.appendChild(tbody)
  }
}

/**
 * 删除“全空的首列”：PukiWiki 表格常有首格为空的占位列（如 <th colspan="2"></th>），
 * 在所有行都为空（无文字、无图片）且 colspan 一致时整列移除，避免表格前端出现无用空列。
 */
function trimEmptyLeadingColumns(table: HTMLTableElement): void {
  const rows = Array.from(table.querySelectorAll('tr'))
  if (!rows.length) return
  // 含 rowspan 的表：children[0] 不一定是第 1 列，删了必错位 → 跳过
  for (const r of rows) {
    for (const c of Array.from(r.children) as HTMLTableCellElement[]) {
      if ((c.rowSpan || 1) > 1) return
    }
  }
  const firsts = rows.map((r) => r.children[0]).filter(Boolean) as HTMLElement[]
  if (firsts.length !== rows.length) return
  const allEmpty = firsts.every((c) => {
    const txt = (c.textContent || '').trim()
    return txt === '' && !c.querySelector('img')
  })
  if (!allEmpty) return
  const colspans = firsts.map((c) => parseInt(c.getAttribute('colspan') || '1', 10))
  if (new Set(colspans).size !== 1) return // 各行列宽不一致 → 不处理，避免错位
  firsts.forEach((c) => c.remove())
}

/**
 * 删除“编辑”列：原站点给管理员用的表格编辑链接（href 含 cmd=table_edit，
 * 链接文字 ja=編集 / zh=编辑），镜像站不需要。仅当“所有行”的末列都是
 * 该编辑链接、且至少剩 2 列时才整列移除（避免误删唯一数据列）。
 */
function removeEditColumn(table: HTMLTableElement): void {
  const rows = Array.from(table.querySelectorAll('tr'))
  if (rows.length === 0) return
  const lasts = rows.map((r) => r.lastElementChild).filter(Boolean) as HTMLElement[]
  if (lasts.length !== rows.length) return
  if (lasts.length === 0) return
  const allEdit = lasts.every((c) => {
    const a = c.querySelector('a')
    if (!a) return false
    const href = (a.getAttribute('href') || '').toLowerCase()
    if (href.includes('table_edit')) return true
    const txt = (c.textContent || '').trim()
    return txt === '編集' || txt === '编辑'
  })
  const colCount = (rows[0] as HTMLTableRowElement).children.length
  if (!allEdit || colCount <= 1) return
  lasts.forEach((c) => c.remove())
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
    if (an !== null && bn !== null) cmp = an - bn // 数字按 1→9
    else cmp = av.localeCompare(bv) // 文本按 locale（A-Z / あいう…）
    return cmp * dir
  })
  rows.forEach((r) => body.appendChild(r))
  applyColumnFilters(table)
}

function applyColumnFilters(table: HTMLTableElement): void {
  const filterRow = filterRowOf(table)
  if (!filterRow) return
  const cols = Array.from(filterRow.children) as HTMLElement[]
  const active: { idx: number; val: string; isSelect: boolean }[] = []
  cols.forEach((cell, idx) => {
    if (cell.classList.contains('escah-col-filter-none')) return
    const inp = cell.querySelector('input, select') as HTMLInputElement | HTMLSelectElement | null
    if (!inp) return
    const v = (inp.value || '').trim().toLowerCase()
    if (!v) return
    active.push({ idx, val: v, isSelect: inp.tagName === 'SELECT' })
  })
  if (!active.length) {
    dataRows(table).forEach((r) => (r.style.display = ''))
    return
  }
  for (const r of dataRows(table)) {
    let show = true
    for (const f of active) {
      const cell = r.children[f.idx] as HTMLElement | undefined
      const txt = (cell?.textContent || '').trim().toLowerCase()
      if (f.isSelect) {
        // select 存的是规范化值，需与单元格原始文本比对（多值用 | 分隔）
        const opts = f.val.split('|')
        if (!opts.some((o) => txt.includes(o))) show = false
      } else if (!txt.includes(f.val)) {
        show = false
      }
      if (!show) break
    }
    r.style.display = show ? '' : 'none'
  }
}

function resetTable(table: HTMLTableElement): void {
  resetOrder(table)
  clearSortIndicators(table)
  ;(table as unknown as { col?: number }).col = undefined
  ;(table as unknown as { dir?: number }).dir = undefined
  const filterRow = filterRowOf(table)
  if (filterRow) {
    filterRow.querySelectorAll('.escah-col-filter').forEach((c) => {
      ;(c as HTMLInputElement | HTMLSelectElement).value = ''
    })
  }
  applyColumnFilters(table)
}

function buildColumnFilterRow(table: HTMLTableElement): void {
  if (table.querySelector('.escah-tbl-filter-row')) return
  // 数据区含合并单元格：children[idx] ≠ 列号，筛选必错位 → 不提供列筛选
  if (bodyHasSpans(table)) return
  const headerRows = headerRowsOf(table)
  if (!headerRows.length) return
  const { totalCols } = headerGrid(headerRows)
  const rows = dataRows(table)
  if (!rows.length || !totalCols) return
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
    if (vals.size === 0 || vals.size > 40) continue // 无值或选项过多 → 不做筛选控件
    hasAnyFilter = true
    cell.classList.remove('escah-col-filter-none')
    cell.classList.add('escah-col-filter')
    if (vals.size <= 12) {
      const sel = document.createElement('select')
      sel.innerHTML = '<option value="">（全部）</option>'
      ;[...vals].sort((a, b) => a.localeCompare(b)).forEach((v) => {
        const o = document.createElement('option')
        o.value = v
        o.textContent = v
        sel.appendChild(o)
      })
      sel.addEventListener('change', () => applyColumnFilters(table))
      cell.appendChild(sel)
    } else {
      const inp = document.createElement('input')
      inp.type = 'text'
      inp.placeholder = '筛选…'
      inp.addEventListener('input', () => applyColumnFilters(table))
      cell.appendChild(inp)
    }
  }
  // 一个可筛选列都没有 → 不插入空行（避免表头下多出一行空格子）
  if (!hasAnyFilter) return
  // 插在整个表头块之后（历史 bug：插在第一表头行后，会插进双行表头中间）
  const lastHeader = headerRows[headerRows.length - 1]
  const thead = lastHeader.parentElement as HTMLElement
  thead.insertBefore(filterRow, lastHeader.nextSibling)
}

function makeSortable(table: HTMLTableElement): void {
  // 数据区含合并单元格：排序会拆散 rowspan 行组 → 禁用排序
  if (bodyHasSpans(table)) return
  const headerRows = headerRowsOf(table)
  if (!headerRows.length) return
  const { colOf } = headerGrid(headerRows)
  const ths = headerRows.flatMap(
    (r) => Array.from(r.children).filter((c) => c.tagName === 'TH') as HTMLTableCellElement[]
  )
  ths.forEach((th) => {
    if (th.classList.contains('escah-no-sort')) return
    if ((th.colSpan || 1) > 1) return // 分组表头不对应单一数据列 → 不可排序
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
 * 按“单元格”处理而非按列索引映射（含合并单元格的表按 children[idx] 找列必错位）。
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
 * 含「+」组合、尾部说明文字、裸 <img>xN 等一律保持横排（不标记）。
 */
function applyImageStack(table: HTMLTableElement): void {
  for (const cell of Array.from(table.querySelectorAll('td, th')) as HTMLElement[]) {
    const anchors = Array.from(cell.querySelectorAll('a')).filter((a) => a.querySelector('img'))
    if (anchors.length === 0) continue
    // 去掉所有链接与图片后若仍剩非空白文字 → 图文混合/组合，保持横排
    const probe = cell.cloneNode(true) as HTMLElement
    probe.querySelectorAll('a, img').forEach((e) => e.remove())
    const rest = (probe.textContent || '').replace(/\s+/g, '')
    if (rest.length === 0) {
      // 多图标横向排列（与原站点一致）；单图标维持竖向堆叠（视觉无差异）
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
  if (e.key === 'Escape') closeFullscreen()
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
  if (fsState) {
    const { container, parent, next } = fsState
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

// 仅当表格超出可视宽度（出现横向滚动条、信息展示不全）时显示全屏按钮；
// 若工具栏内已无任何可见按钮，则隐藏整条工具栏。
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

function enhanceTable(table: HTMLTableElement): void {
  if (table.getAttribute('data-escah') === '1') return
  normalizeTable(table)
  trimEmptyLeadingColumns(table)
  removeEditColumn(table)
  getOriginalRows(table)
  // 行数 < 20 的小表格：不提供筛选/排序/重置（交互无意义）
  const smallTable = dataRows(table).length < 20
  if (!smallTable) {
    buildColumnFilterRow(table)
    makeSortable(table)
  }
  markSpecialColumns(table)
  applyImageStack(table)

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
  const btnFull = mkBtn('表格全屏', '页面内全屏查看（仅在表格超出可视宽度时出现）', () => toggleFullscreen(table))
  btnFull.classList.add('escah-tbl-full-btn')
  toolbar.appendChild(btnFull)
  if (!smallTable) {
    const btnReset = mkBtn('表格重置', '重置排序与筛选', () => resetTable(table))
    toolbar.appendChild(btnReset)
  }
  container.insertBefore(toolbar, wrapper)

  // 仅当表格出现横向滚动条（信息展示不全）时才显示全屏按钮；无溢出则隐藏整条工具栏
  requestAnimationFrame(() => syncFullBtnFor(container, wrapper, toolbar, btnFull))
  bindFullBtnResize()

  table.setAttribute('data-escah', '1')
}

export function enhanceTables(el: HTMLElement): void {
  el.querySelectorAll('table').forEach((t) => {
    enhanceTable(t as HTMLTableElement)
  })
}

export function destroyTables(_el: HTMLElement): void {
  closeFullscreen()
}
