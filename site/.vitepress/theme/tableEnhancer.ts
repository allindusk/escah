/**
 * 表格增强：表头排序、列筛选、页面内全屏、图像/长文本列适配。
 * 由 MirrorContent.vue 在 v-html 注入后调用（enhanceTables）。
 */
function headerRowOf(table: HTMLTableElement): HTMLTableRowElement | null {
  const thead = table.querySelector('thead')
  if (thead) {
    const r = thead.querySelector('tr')
    if (r) return r as HTMLTableRowElement
  }
  const r = table.querySelector('tr')
  return (r as HTMLTableRowElement) || null
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
  const header = headerRowOf(table)
  if (!header) return
  if (table.querySelector('.escah-tbl-filter-row')) return
  const filterRow = document.createElement('tr')
  filterRow.className = 'escah-tbl-filter-row'
  for (let c = 0; c < header.children.length; c++) {
    const cell = document.createElement('td')
    cell.className = 'escah-col-filter-none'
    filterRow.appendChild(cell)
  }
  const ths = Array.from(header.children) as HTMLElement[]
  ths.forEach((th, idx) => {
    const vals = new Set<string>()
    for (const r of dataRows(table)) {
      const cell = r.children[idx] as HTMLElement | undefined
      if (!cell) continue
      const t = (cell.textContent || '').trim()
      if (t) vals.add(t)
    }
    const cell = filterRow.children[idx] as HTMLElement
    if (vals.size === 0 || vals.size > 40) return // 无值或选项过多 → 不做筛选控件
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
  })
  const thead = header.parentElement as HTMLElement
  thead.insertBefore(filterRow, header.nextSibling)
}

function makeSortable(table: HTMLTableElement): void {
  const header = headerRowOf(table)
  if (!header) return
  const ths = Array.from(header.querySelectorAll('th'))
  ths.forEach((th, idx) => {
    if (th.classList.contains('escah-no-sort')) return
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

/** 标记图像列（固定最小宽度保证图片正常显示）与超长文本列（限高并加宽） */
function markSpecialColumns(table: HTMLTableElement): void {
  const header = headerRowOf(table)
  if (!header) return
  const colCount = header.children.length
  for (let c = 0; c < colCount; c++) {
    let hasImg = false
    let maxImgW = 0
    let longCount = 0
    const cells: HTMLElement[] = []
    for (const row of dataRows(table)) {
      const cell = row.children[c] as HTMLElement | undefined
      if (!cell) continue
      cells.push(cell)
      const img = cell.querySelector('img')
      if (img) {
        hasImg = true
        const w = parseInt(img.getAttribute('width') || '', 10)
        if (!isNaN(w)) maxImgW = Math.max(maxImgW, w)
      }
      if ((cell.textContent || '').trim().length > 40) longCount++
    }
    if (hasImg) {
      const w = Math.max(64, Math.min(maxImgW || 120, 280))
      ;(header.children[c] as HTMLElement).classList.add('escah-img-col')
      for (const cell of cells) {
        cell.classList.add('escah-img-col')
        cell.style.minWidth = w + 'px'
      }
    }
    if (longCount > 0) {
      for (const cell of cells) {
        if ((cell.textContent || '').trim().length > 40) cell.classList.add('escah-long')
      }
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
  getOriginalRows(table)
  buildColumnFilterRow(table)
  makeSortable(table)
  markSpecialColumns(table)

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
  const btnFilter = mkBtn('筛选', '显示/隐藏列筛选行', () => {
    const fr = filterRowOf(table)
    if (!fr) return
    fr.style.display = fr.style.display === 'none' ? '' : 'none'
  })
  const btnFull = mkBtn('全屏', '页面内全屏查看（与原表格一致）', () => toggleFullscreen(table))
  const btnReset = mkBtn('重置', '重置排序与筛选', () => resetTable(table))
  toolbar.append(btnFilter, btnFull, btnReset)
  container.insertBefore(toolbar, wrapper)

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
