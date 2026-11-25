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

/**
 * 解析日期文本（PukiWiki 时间戳「2026-10-19 08:09」、「2026/10/19」等），非日期返回 null。
 * 返回年份/月份（供年月筛选）与可比较的时间戳数值（yyyymmddhhmm，含时分——
 * 同一天内往往有多条更新，只比到「日」会让这些行并列、排序结果不稳定）。
 */
const DATE_RE = /^(\d{4})[-/.](\d{1,2})(?:[-/.](\d{1,2}))?(?:[ T](\d{1,2}):(\d{2}))?/
function dateStamp(s: string): { y: number; m: number; stamp: number } | null {
  const m = s.trim().match(DATE_RE)
  if (!m) return null
  const y = Number(m[1])
  const mo = Number(m[2])
  if (mo < 1 || mo > 12) return null
  const d = m[3] ? Number(m[3]) : 0
  if (d > 31) return null
  const h = m[4] && Number(m[4]) <= 23 ? Number(m[4]) : 0
  const mi = m[5] ? Math.min(Number(m[5]), 59) : 0
  return { y, m: mo, stamp: y * 1e8 + mo * 1e6 + d * 1e4 + h * 100 + mi }
}

function sortByColumn(table: HTMLTableElement, col: number, dir: number): void {
  const body = getBody(table)
  const rows = dataRows(table)
  const textOf = (r: HTMLTableRowElement) => (r.children[col]?.textContent || '').trim()
  const items = rows.map((r) => {
    const text = textOf(r)
    return { r, text, date: dateStamp(text) }
  })
  // 日期列（如「更新记录」的 wiki/镜像时间戳）必须按真实时间比较：
  // 旧逻辑走 cellNumber 只取第一个数字（"2026-10-19 08:09" → 2026），
  // 同一年里各月全部相等 → 点表头排序看起来毫无反应。
  const isDateCol = items.filter((it) => it.date).length >= Math.ceil(items.length * 0.6)
  items.sort((a, b) => {
    if (isDateCol) {
      // 空值（「—」）恒排末尾，与升/降序无关
      if (!a.date && !b.date) return 0
      if (!a.date) return 1
      if (!b.date) return -1
      return (a.date.stamp - b.date.stamp) * dir
    }
    const an = cellNumber(a.text)
    const bn = cellNumber(b.text)
    const cmp = an !== null && bn !== null ? an - bn : a.text.localeCompare(b.text)
    return cmp * dir
  })
  items.forEach((it) => body.appendChild(it.r))
  applyColumnFilters(table)
}

// 预存在表格上的缓存：数据行元素数组 + 每行每列（小写、trim）文本，
// 供 applyColumnFilters 纯内存判断，避免反复 querySelectorAll + 读 textContent 触发强制布局。
// 注意：排序状态绝不能用 `table.col` / `table.dir` 这种名字——`dir` 是 HTMLElement 的
// 反射属性（对应 dir 属性），赋 -1 会被规范化成 ""，导致「第二次点击永远还是升序」。
type TblCache = HTMLTableElement & {
  _escahRows?: HTMLTableRowElement[]
  _escahRowText?: string[][]
  _escahSortCol?: number
  _escahSortDir?: number
  _escahAlwaysCount?: boolean
}

// 这些页面（角色一览与各类列表页）表格**始终**显示行数；其余页面只有超过 10 行才显示，
// 免得正文里每张两三条的小表都顶一个「共 3 行」（2026-11-13 用户要求）。
const COUNT_ALWAYS_PREFIXES = [
  'characters', 'list-ssr', 'list-sr', 'list-r', 'list-supporter', 'list-npc',
]
const COUNT_MIN_ROWS = 10

function alwaysShowCount(pageSlug?: string): boolean {
  if (!pageSlug) return false
  const slug = pageSlug.toLowerCase()
  return COUNT_ALWAYS_PREFIXES.some(
    (p) => slug === p || slug.startsWith(p + '/') || slug.startsWith(p + '-')
  )
}

/**
 * 行数显示：在「表格全屏 / 表格重置」之后紧跟「共 N 行」，筛选后变成「共 N / M 行」。
 * 数字必须随筛选实时变化 —— 所有会改变行可见性的路径（applyColumnFilters / resetTable）
 * 都必须调用本函数，否则会出现「筛了但数字不动」。
 */
function updateRowCount(table: HTMLTableElement): void {
  // ⚠️ 不能用 table.closest('.escah-tbl')：数据统计等页面的 <table> **本身**就带
  // .escah-tbl（那是容器 class，statpages 生成时直接挂在 table 上），closest 会命中自己，
  // 于是查不到工具栏里的徽标、行数永远空白。必须从父级往上找真正的容器。
  const container = (table.parentElement?.closest('.escah-tbl') as HTMLElement | null) || null
  const el = container?.querySelector(
    ':scope > .escah-tbl-toolbar > .escah-tbl-count'
  ) as HTMLElement | null
  if (!el) return
  const cache = table as TblCache
  const rows = cache._escahRows || (dataRows(table) as HTMLTableRowElement[])
  const total = rows.length
  // 非列表页：≤10 行的表不显示行数（按总行数判断，不随筛选变化，避免徽标忽隐忽现）
  if (!cache._escahAlwaysCount && total <= COUNT_MIN_ROWS) {
    el.style.display = 'none'
    el.textContent = ''
    return
  }
  el.style.display = ''
  let shown = 0
  for (const r of rows) if (r.style.display !== 'none') shown++
  el.textContent = shown === total ? `共 ${total} 行` : `共 ${shown} / ${total} 行`
  el.classList.toggle('is-filtered', shown !== total)
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
  //  - 日期列（年 / 月下拉）：年、月同时生效（AND），空值表示该级不限。
  type FilterCond =
    | { idx: number; mode: 'exact' | 'substr'; vals: string[] }
    | { idx: number; mode: 'date'; year: string; month: string }
  const active: FilterCond[] = []
  cells.forEach((cell, idx) => {
    if (cell.classList.contains('escah-col-filter-none')) return
    const yearSel = cell.querySelector('select.escah-date-sel[data-part="year"]') as HTMLSelectElement | null
    const monthSel = cell.querySelector('select.escah-date-sel[data-part="month"]') as HTMLSelectElement | null
    if (yearSel && (yearSel.value || (monthSel && monthSel.value))) {
      active.push({ idx, mode: 'date', year: yearSel.value, month: monthSel ? monthSel.value : '' })
      return
    }
    // 下拉打开时 pop 被临时移到 <body>（见 attachPop），故不能只看 cell 内部
    const pop = (cell as any)._escahPop as HTMLElement | null
    const checked = Array.from(
      (pop || cell).querySelectorAll('input[type="checkbox"]:checked')
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
    updateRowCount(table)
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
      if (f.mode === 'date') {
        // 日期列：年、月逐级比对（该列不是日期或为空 → 不命中）
        const d = dateStamp(txt)
        if (!d) show = false
        else if (f.year && String(d.y) !== f.year) show = false
        else if (f.month && String(d.m) !== f.month) show = false
      } else if (f.mode === 'exact') {
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
  updateRowCount(table)
  finish()
}

function resetTable(table: HTMLTableElement): void {
  closeAllFilterPops() // 先把下拉挪回各自格子，下面的 querySelectorAll 才读得到勾选状态
  resetOrder(table)
  clearSortIndicators(table)
  ;(table as TblCache)._escahSortCol = undefined
  ;(table as TblCache)._escahSortDir = undefined
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
    // 日期列的年/月下拉回到「全部」
    filterRow.querySelectorAll('select.escah-date-sel').forEach((s) => {
      ;(s as HTMLSelectElement).value = ''
    })
    filterRow.querySelectorAll('td').forEach((td) => {
      td.classList.remove('escah-filter-active')
    })
  }
  applyColumnFilters(table)
}

/**
 * 日期列筛选控件：年 / 月两级下拉（同级取「且」，空值 = 不限）。
 * 日期列的高基数值（几百个「YYYY-MM-DD HH:MM」）如果走精确多选或「包含」文本框，
 * 用户既没法按年、按月聚合，也得逐位敲字，因此单独做一套年月下拉。
 */
function buildDateFilterCell(
  cell: HTMLElement,
  table: HTMLTableElement,
  years: number[],
  months: number[]
): void {
  const wrap = document.createElement('div')
  wrap.className = 'escah-date-filter'
  const sync = () => {
    const active = Array.from(wrap.querySelectorAll('select')).some(
      (s) => (s as HTMLSelectElement).value !== ''
    )
    cell.classList.toggle('escah-filter-active', active)
    applyColumnFilters(table)
  }
  const mkSel = (part: 'year' | 'month', allLabel: string, opts: { v: string; t: string }[]) => {
    const sel = document.createElement('select')
    sel.className = 'escah-date-sel'
    sel.dataset.part = part
    sel.title = part === 'year' ? '按年份筛选（可与月份叠加）' : '按月份筛选（可与年份叠加）'
    const o0 = document.createElement('option')
    o0.value = ''
    o0.textContent = allLabel
    sel.appendChild(o0)
    for (const o of opts) {
      const op = document.createElement('option')
      op.value = o.v
      op.textContent = o.t
      sel.appendChild(op)
    }
    sel.addEventListener('change', sync)
    sel.addEventListener('click', (e) => e.stopPropagation())
    return sel
  }
  wrap.appendChild(mkSel('year', '全部年', years.map((y) => ({ v: String(y), t: `${y}年` }))))
  wrap.appendChild(mkSel('month', '全部月', months.map((m) => ({ v: String(m), t: `${m}月` }))))
  cell.appendChild(wrap)
}

/**
 * 筛选下拉（多选 checkbox popover）的定位与关闭。
 *
 * ⚠️ 必须用 position:fixed + 手动摆放，不能靠 CSS 的 absolute(top:100%)：
 * 表格被 `.escah-tbl .table-scroll { overflow-x:auto; overflow-y:hidden }` 包裹，
 * 绝对定位的下拉会被这个滚动容器**裁剪**——表现为「下拉内容被下面的单元格挡住/截断」，
 * 全屏模式（.escah-tbl-fs-scroll{overflow:auto}）同理。fixed 定位相对视口，不受祖先裁剪。
 */
function positionFilterPop(pop: HTMLElement, btn: HTMLElement): void {
  pop.style.position = 'fixed'
  pop.style.marginTop = '0px'
  pop.style.left = '0px'
  pop.style.top = '0px'
  const b = btn.getBoundingClientRect()
  const w = pop.offsetWidth
  const h = pop.offsetHeight
  const vw = window.innerWidth
  const vh = window.innerHeight
  const gap = 2
  let left = b.left
  if (left + w > vw - 8) left = Math.max(8, vw - 8 - w)
  let top = b.bottom + gap
  // 下方放不下（贴近视口底部）就翻到按钮上方，保证内容完整可见
  if (top + h > vh - 8 && b.top - gap - h > 8) top = b.top - gap - h
  pop.style.left = `${Math.round(left)}px`
  pop.style.top = `${Math.round(top)}px`
}

/**
 * 打开时把下拉移进 <body>。**必须**这么做而不能只靠 fixed：
 * 筛选行的 td 是 `position: sticky; z-index: 3`（见 custom.css 吸顶规则），sticky +
 * z-index 会自建层叠上下文，fixed 下拉的 z-index 只在该格内部生效 —— 对外层它整个
 * 就是「z-index:3 的格子」，会被吸顶表头（4）、同级其它筛选格、首列冻结（2）盖住，
 * 表现为「下拉被下面的控件挡住」。移出到 body 后彻底脱离这个上下文。
 */
function attachPop(pop: HTMLElement): void {
  if (pop.parentElement !== document.body) document.body.appendChild(pop)
}

function closeAllFilterPops(): void {
  document.querySelectorAll('.escah-filter-pop.open').forEach((p) => {
    const el = p as HTMLElement
    el.classList.remove('open')
    el.style.position = ''
    el.style.marginTop = ''
    el.style.left = ''
    el.style.top = ''
    // 关掉就挪回原来的格子，保持 DOM 可预期（重置/读值都还在原位）
    const home = (el as any)._escahHome as HTMLElement | null
    if (home && el.parentElement !== home) home.appendChild(el)
  })
}

let popDismissBound = false
function bindPopDismiss(): void {
  if (popDismissBound) return
  popDismissBound = true
  // 位置是打开那一刻算的，页面/表格一滚动就会错位 → 直接收起（比跟随重算稳定）。
  // 但下拉自身列表滚动（pop 有 max-height:auto 内滚）不能触发关闭，否则滚两下就没了。
  window.addEventListener(
    'scroll',
    (e) => {
      const t = e.target as HTMLElement | null
      if (t && typeof t.closest === 'function' && t.closest('.escah-filter-pop')) return
      closeAllFilterPops()
    },
    true
  )
  window.addEventListener('resize', closeAllFilterPops)
  document.addEventListener('click', (e) => {
    const t = e.target as HTMLElement | null
    if (!t || typeof t.closest !== 'function') return closeAllFilterPops()
    // 打开时下拉已挂到 body，故两处都要放行
    if (t.closest('.escah-filter-multi') || t.closest('.escah-filter-pop')) return
    closeAllFilterPops()
  })
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
    // 日期列（>=60% 的非空值形如 YYYY-MM-DD）→ 年 / 月两级下拉，
    // 比几百个精确日期值的多选（会退化成文本框）更符合「按年按季按月看更新」的需求。
    const years = new Set<number>()
    const months = new Set<number>()
    let nonEmpty = 0
    let dateHit = 0
    for (let ri = 0; ri < rowTexts.length; ri++) {
      const t = rowTexts[ri]?.[c] || ''
      if (!t) continue
      nonEmpty++
      const d = dateStamp(t)
      if (!d) continue
      dateHit++
      years.add(d.y)
      months.add(d.m)
    }
    if (dateHit > 0 && dateHit >= Math.ceil(nonEmpty * 0.6)) {
      buildDateFilterCell(
        cell,
        table,
        [...years].sort((a, b) => b - a),
        [...months].sort((a, b) => a - b)
      )
      continue
    }
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
        closeAllFilterPops()
        if (!open) {
          attachPop(pop) // 先脱离 sticky 单元格的层叠上下文
          pop.classList.add('open')
          positionFilterPop(pop, btn) // 必须在显示之后量尺寸
        }
      }
      ;(pop as any)._escahHome = wrap
      ;(cell as any)._escahPop = pop
      btn.addEventListener('click', toggle)
      bindPopDismiss()
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
      const cache = table as TblCache
      const cur = cache._escahSortCol
      const c = cache._escahSortDir ?? 0
      let dir: number
      if (cur === idx) dir = c === 1 ? -1 : c === -1 ? 0 : 1
      else dir = 1
      if (dir === 0) {
        resetOrder(table)
        clearSortIndicators(table)
        cache._escahSortCol = undefined
        cache._escahSortDir = undefined
        applyColumnFilters(table)
        return
      }
      clearSortIndicators(table)
      sortByColumn(table, idx, dir)
      th.classList.add(dir === 1 ? 'escah-sort-asc' : 'escah-sort-desc')
      cache._escahSortCol = idx
      cache._escahSortDir = dir
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
      if (anchors.length === 1) {
        cell.classList.add('escah-img-stack')
        continue
      }
      // 2026-11-25 修：多图标**不能**把 display:flex 直接加在 td/th 上。那会把单元格
      // 从 table-cell 变成 flex 容器，表格算法失效（raid-buff-debuff 实测：同一行的
      // 多个单元格重叠、每行图标起止位置各不相同，角色完全不在原站对应的列下）。
      // 改为在单元格内包一层 flex 容器，单元格本身保持 table-cell。
      let wrap = cell.querySelector(':scope > .escah-img-row') as HTMLElement | null
      if (!wrap) {
        wrap = document.createElement('div')
        wrap.className = 'escah-img-row'
        while (cell.firstChild) wrap.appendChild(cell.firstChild)
        // 原站用 <br class="spacer"> 在单元格内强制分行（raid-buff-debuff 的表格 3 个一行）。
        // <br> 在 flex 容器里不占位、不会换行，换成 100% 宽的空占位块才能真正断行。
        wrap.querySelectorAll('br').forEach((br) => {
          const lineBreak = document.createElement('div')
          lineBreak.className = 'escah-img-break'
          br.replaceWith(lineBreak)
        })
        cell.appendChild(wrap)
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
  if (e.key === 'Escape') {
    if (charModalStore.visible) return
    closeFullscreen()
  }
}

// 2026-11-24：冻结区（表头/筛选行/首列）底色改由 CSS 常驻不透明实色，
// 不再在滚动时用内联样式切色——旧实现滚动即变色、停下 150ms 又变回半透明，
// 一滑动就闪，像页面出故障，且半透明期间下层文字透上来糊成一片。
// 这里只保留微信/诊断用的注意事项：不要再给冻结单元格写内联 background。

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
    // 2026-11-24：冻结底色已交给 CSS（不再有滚动期内联色），只需清掉可能残留的内联背景。
    const root = table.closest('.escah-tbl-fs-scroll')?.querySelector('table') || table
    root.querySelectorAll(
      'thead th, thead .escah-tbl-filter-row td, th:first-child, td:first-child'
    ).forEach((c) => {
      const el = c as HTMLElement
      el.style.removeProperty('background')
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
  // 工具栏里有可见的行数徽标，故不再「没按钮就整条隐藏」
  const countEl = toolbar.querySelector('.escah-tbl-count') as HTMLElement | null
  const hasCount = !!countEl && countEl.style.display !== 'none'
  const visible = toolbar.querySelector('button:not([style*="display: none"])')
  toolbar.style.display = hasCount || visible ? '' : 'none'
}

let resizeBound = false
export function syncAllFullBtns(): void {
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
/**
 * 把原站表头里的多行文本收成一行可读标签。
 * - `<br>` 已被替换成 \u0001 标记：两侧都是纯中文时直接拼接（「体<br>力」→「体力」、
 *   「必杀<br>充能<br>量」→「必杀充能量」），否则留一个空格（「体力<br>改进后：」→「体力 改进后：」）。
 * - 原站 wiki 文本里没被排版渲染的 markdown 强调标记会原样显示成星号
 *   （表头里真实存在「**改进后：**」这种），不清理的话吸顶表头看起来像乱码。
 */
function normHeaderLabel(raw: string): string {
  const isCjk = (s: string) => /^[\u3000-\u303f\u4e00-\u9fff\uf900-\ufaff]+$/.test(s)
  const segs = raw
    .replace(/[\s\u3000]+/g, ' ')
    .split('\u0001')
    .map((s) => s.trim())
    .filter(Boolean)
  if (!segs.length) return ''
  let out = segs[0]
  for (let i = 1; i < segs.length; i++) out += (isCjk(segs[i - 1]) && isCjk(segs[i]) ? '' : ' ') + segs[i]
  return out.replace(/\*+/g, '').replace(/[\s\u3000]+/g, ' ').trim()
}

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
    // 表头单行化（2026-11-24）：原站部分表头用 <br> 把「攻击力」写成三行，吸顶后
    // 整个表头被撑成 141px 的竖条（截图里像一块紫色大横幅盖住半屏）。这里把表头内的
    // <br> 收成标记符，再按「中文对中文直接拼、整词之间留空格」的规则拼成一行，
    // 配合 CSS 的 nowrap + 省略号，表头稳定一行；完整文字进 title。
    const BR = '\u0001'
    th.querySelectorAll('br').forEach((br) => br.replaceWith(document.createTextNode(BR)))
    th.normalize()
    const label = normHeaderLabel(th.textContent || '')
    if (label) {
      if (!th.title) th.title = label
      // 原站表头常写「　　画像　　」这种全角空格填充：手机上允许折行的列里会折成两行，
      // 表头高度从 33 涨到 57。纯文本表头（没有排序箭头等子元素）直接换成规范文本。
      if (!th.children.length) th.textContent = label
      else
        th.childNodes.forEach((n) => {
          // 带子元素（排序箭头等）的表头不动结构，只把临时标记符清成空格
          if (n.nodeType === 3 && n.nodeValue && n.nodeValue.includes(BR)) n.nodeValue = n.nodeValue.split(BR).join(' ')
        })
    }
  })

  const maxPx = new Array(ncols).fill(0)
  const isImgCol = new Array(ncols).fill(false)
  let imgWidth = 110

  // 筛选行的「筛选 ▾」按钮下限：fixed 布局下单元格的 min-width 不生效（列宽只认 <col>），
  // 所以必须让 <col> 本身 ≥ 按钮宽，否则窄数字列的筛选按钮会溢出、与相邻列重叠（标签重合）。
  const FILTER_BTN_MIN = 76
  const CELL_PAD = 20 // 单元格 padding 左右之和（5px 10px → 10+10）

  // 图片列先扫一遍（纯 DOM 查询，不触发布局）：列宽取图片自身 width，跳过文本测量。
  // 仅在表里确实有图时才扫，避免大数据表白跑几千次 querySelector。
  if (getBody(table).querySelector('img')) {
    for (const r of rows) {
      for (let c = 0; c < ncols; c++) {
        const cell = r.children[c] as HTMLElement | undefined
        if (!cell) continue
        const img = cell.querySelector('img')
        if (!img) continue
        isImgCol[c] = true
        const w = parseInt(img.getAttribute('width') || '', 10)
        if (!isNaN(w) && w > imgWidth) imgWidth = Math.min(w, 280)
      }
    }
  }

  // ===== 列宽测量（2026-10-18 重写）=====
  // 旧实现：逐格把 cell.innerHTML 拷进同一个临时 span，每格读一次
  // getBoundingClientRect()。每次 innerHTML 赋值都会让文档样式/布局失效，紧接着的
  // 读操作就触发一次「整页强制重排」—— 角色一览（432 行 × 6 列 ≈ 2600 格）实测
  // 单次长任务 2.4s（4× CPU 节流下 9.6s），是全站最重的阻塞源。
  //
  // 新实现：把所有待测单元格的 innerHTML **一次性**拼进同一个隐藏容器（每格一个
  // nowrap inline-block 的 span），DOM 只解析/失效一次，然后连续读 N 个宽度（读操作
  // 彼此不触发重排）。测量结果与旧实现逐格量取的语义完全一致（同样的字体、同样的
  // nowrap、同样的单元格内联结构），只是把 2600 次重排压成 1 次。
  //
  // 为什么不直接读真实表格的列宽（更省事）：表格是 auto 布局 + max-content 时列宽
  // 还受**表头**与 min-width:100% 拉伸影响，实测名称列会被表头/撑开的分配算成 481px
  // （正确值 193px）、备注列 290px→103px，列宽整体错乱，故不可用。
  const sampleCell0 = rows[0]?.children[0] as HTMLElement | undefined
  const cs0 = sampleCell0 ? getComputedStyle(sampleCell0) : null
  const measureFont =
    `font-size:${cs0 ? cs0.fontSize : '13px'};font-family:${cs0 ? cs0.fontFamily : 'inherit'};`
  const parts: string[] = []
  const partCols: number[] = []
  for (const r of rows) {
    for (let c = 0; c < ncols; c++) {
      const cell = r.children[c] as HTMLElement | undefined
      if (!cell || isImgCol[c]) continue
      // 克隆单元格内部 HTML（保留 <a>/<br> 等结构），测真实内容宽
      parts.push(`<span style="display:inline-block;white-space:nowrap">${cell.innerHTML}</span>`)
      partCols.push(c)
    }
  }
  if (parts.length) {
    const box = document.createElement('div')
    box.style.cssText = `position:absolute;left:-99999px;top:0;visibility:hidden;${measureFont}`
    box.innerHTML = parts.join('')
    document.body.appendChild(box)
    const spans = box.children
    // 结构异常（单元格 HTML 里有未闭合标签把相邻 span 吞掉）时退回逐格测量，保证正确性
    if (spans.length === parts.length) {
      for (let i = 0; i < partCols.length; i++) {
        const w = (spans[i] as HTMLElement).getBoundingClientRect().width + CELL_PAD
        if (w > maxPx[partCols[i]]) maxPx[partCols[i]] = w
      }
    } else {
      const single = document.createElement('span')
      single.style.cssText = `position:absolute;left:-99999px;top:0;visibility:hidden;white-space:nowrap;display:inline-block;${measureFont}`
      document.body.appendChild(single)
      for (const r of rows) {
        for (let c = 0; c < ncols; c++) {
          const cell = r.children[c] as HTMLElement | undefined
          if (!cell || isImgCol[c]) continue
          single.innerHTML = cell.innerHTML
          const w = single.getBoundingClientRect().width + CELL_PAD
          if (w > maxPx[c]) maxPx[c] = w
        }
      }
      document.body.removeChild(single)
    }
    document.body.removeChild(box)
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

  // 表头单行宽度下限（2026-11-24 新增）：
  // 旧逻辑只按数据宽算列宽、表头允许 break-all 逐字折行，窄数字列里的「体力/攻击力/魔法抗性」
  // 被拆成一字一行，表头行高涨到 200px+，吸顶后压掉半个视口 —— 用户直接反馈「像页面故障」。
  // 这里把「表头单行文字宽」也算进列宽下限，让表头永远一行（放不下就省略号，完整文字进 title）。
  const headRows = headerRowsOf(table).filter((r) => !r.classList.contains('escah-tbl-filter-row'))
  const headCells: { cell: HTMLElement; col: number }[] = []
  if (headRows.length) {
    const covered: boolean[][] = [] // covered[row][col]：被上方 rowspan 占住的格子
    headRows.forEach((r, ri) => {
      const occ = covered[ri] || (covered[ri] = [])
      let col = 0
      for (const cell of Array.from(r.children) as HTMLElement[]) {
        while (occ[col]) col++
        const colspan = cell.colSpan || 1
        const rowspan = cell.rowSpan || 1
        for (let k = 0; k < colspan; k++) {
          headCells.push({ cell, col: col + k })
          occ[col + k] = true
          if (rowspan > 1) {
            for (let rr = ri + 1; rr < ri + rowspan; rr++) {
              const a = covered[rr] || (covered[rr] = [])
              a[col + k] = true
            }
          }
        }
        col += colspan
      }
    })
    // 一次性测量所有表头文字的单行宽（同样只触发一次布局）
    const hbox = document.createElement('div')
    hbox.style.cssText = `position:absolute;left:-99999px;top:0;visibility:hidden;${measureFont}`
    hbox.innerHTML = headCells
      .map(({ cell }) => `<span style="display:inline-block;white-space:nowrap">${cell.textContent || ''}</span>`)
      .join('')
    document.body.appendChild(hbox)
    const hspans = hbox.children
    if (hspans.length === headCells.length) {
      for (let i = 0; i < headCells.length; i++) {
        const { cell, col } = headCells[i]
        // 表头完整文字存进 title：列宽不够被省略号截断时，悬停/长按仍能看到全称
        const label = (cell.textContent || '').trim()
        if (label && !cell.title) cell.title = label
        const w = (hspans[i] as HTMLElement).getBoundingClientRect().width + CELL_PAD
        if (w > maxPx[col]) maxPx[col] = w
      }
    }
    document.body.removeChild(hbox)
  }

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

// 表头高度必须读 getBoundingClientRect（强制布局）。若每增强一张表就读一次，前一张表
// 刚做的 DOM 变更会让下一张表的读操作重新布局整页 —— 技能一览这类上百张表的页面，
// 这项「写-读」交替实测占主线程 ~10%。改为先排队、等所有表增强完（DOM 变更收敛）
// 再统一读，全页只多付出一次布局。
const pendingHeadMeasures: HTMLTableElement[] = []
function flushHeadMeasures(): void {
  const list = pendingHeadMeasures.splice(0)
  for (const t of list) {
    measureHeadHeight(t)
    markFrozenColumns(t)
  }
}

/**
 * 决定要不要冻结「身份列」（首列头像 / 首列名称）。
 * 以前是无条件冻结首列，结果：① 不横向溢出的普通表（详情页 2 列表）也被冻住，没意义还叠层；
 * ② 角色一览的「画像」和「名称」是两列，只冻第一列时名字被压在头像下面、只剩半截字，
 *   看起来就像页面错位。
 * 现在的规则：
 *  - 表格没横向溢出 → 完全不做列冻结（只留表头吸顶）。
 *  - 有溢出 → 冻结 1 列；若第 2 列表头是「名称 / 名前」之类的身份列，
 *    且冻结后仍留出足够宽度给数据列（桌面 ≥ 320px，手机 ≥ 140px），则冻结 2 列。
 *  - 手机（< 960）同样冻结，但把「画像 + 名称」两列压窄（70 + 104px，名称截断省略），
 *    否则 110 + 193 的身份块会吃掉 390 屏宽的 89%，等于没地方看数据。
 */
const IDENT_HEAD_RE = /^(名称|名前|角色名|角色名稱|姓名|caption|name)$/i
const MOBILE_IDENT_COLS: [number, number] = [70, 120]

/** 手机上把身份两列压窄，宽度变化（旋转/回桌面）时恢复原始列宽 */
function applyIdentityWidths(table: HTMLTableElement, narrow: boolean): number[] | null {
  const cols = Array.from(table.querySelectorAll('colgroup > col')) as HTMLElement[]
  if (cols.length < 2) return null
  const widths: number[] = []
  for (let i = 0; i < 2; i++) {
    const col = cols[i]
    if (col.dataset.escahW === undefined) col.dataset.escahW = col.style.width || ''
    if (narrow) col.style.width = MOBILE_IDENT_COLS[i] + 'px'
    else {
      col.style.width = col.dataset.escahW
      delete col.dataset.escahW
    }
    const w = parseFloat(col.style.width)
    if (w) widths[i] = w
  }
  return widths.length === 2 ? widths : null
}

/**
 * 跨整行的分隔行（`<td colspan="9">优先1</td>` 这种）不是身份列，不能套冻结列的实色底：
 * 冻结列用的是 `background-color:…!important`，会压掉原站内联的 `background-color:red`，
 * 于是「红底白字」变成「白底白字」——字直接看不见（2026-11-24 用户反馈 buniv-008）。
 * 这里按「起始列 + 跨列数」标记：从第 0 列起、却宽过整个冻结块的单元格打上 .escah-nofreeze，
 * 冻结相关样式全部带 :not(.escah-nofreeze) 排除它（恰好覆盖身份块整宽的合并表头仍保留冻结）。
 */
function markNoFreezeSpans(table: HTMLTableElement, frozenCount: number): void {
  for (const r of Array.from(table.querySelectorAll('tr'))) {
    let col = 0
    for (const cell of Array.from(r.children) as HTMLElement[]) {
      const cs = Number(cell.getAttribute('colspan') || 1)
      cell.classList.toggle('escah-nofreeze', col === 0 && cs > frozenCount)
      col += cs
    }
  }
}

/** 表格真实列数（正确处理 rowspan/colspan；没有全 th 表头时按首行累加）。 */
function tableCols(table: HTMLTableElement): number {
  const { totalCols } = headerGrid(headerRowsOf(table))
  if (totalCols) return totalCols
  const first = dataRows(table)[0]
  if (!first) return 0
  let n = 0
  for (const c of Array.from(first.children) as HTMLTableCellElement[]) n += c.colSpan || 1
  return n
}

function markFrozenColumns(table: HTMLTableElement): void {
  table.classList.remove('escah-frozen-1', 'escah-frozen-2')
  const wrap = table.parentElement
  if (!wrap || !wrap.classList.contains('table-scroll')) return
  // 用户规则（2026-11-26）：**列数 > 10 才冻结列**。
  // 角色详情页的档案表（3 列）、属性表（6 列）这类普通内容表一旦冻结首列，
  // 手机上等于把大半个屏幕钉住，右侧内容被永久遮住 —— 宁可不冻。
  if (tableCols(table) <= 10) return
  const overflows = wrap.scrollWidth > wrap.clientWidth + 8
  const narrow = window.matchMedia('(max-width: 959px)').matches

  const firstRow = headerRowsOf(table).find((r) => !r.classList.contains('escah-tbl-filter-row'))
  if (!firstRow) return
  const ths = Array.from(firstRow.children) as HTMLElement[]
  const c1 = ths[0] ? (ths[0].textContent || '').replace(/\s+/g, '').trim() : ''
  const c2 = ths[1] ? (ths[1].textContent || '').replace(/\s+/g, '').trim() : ''
  if (ths.length < 2) return
  const nameCol = IDENT_HEAD_RE.test(c2) && !IDENT_HEAD_RE.test(c1) // 首列本身就是名称列时不必再冻第二列

  // 列宽先恢复/压窄再读（否则读到的是上一个断点的宽度）；只有「要冻两列的列表」在手机上才压窄
  const identW = applyIdentityWidths(table, narrow && overflows && nameCol && table.classList.contains('escah-tbl-shrink'))
  if (!overflows) return // 不横向溢出，不需要冻结

  // 首列宽（第二列 sticky 左偏移用）：shrink 表以 <col> 为准，普通表量真实单元格
  let w1 = identW ? identW[0] : 0
  if (!w1) {
    const cell = (dataRows(table)[0]?.children[0] as HTMLElement | undefined) || ths[0]
    w1 = cell ? cell.getBoundingClientRect().width : 0
  }
  if (w1 <= 0) return

  // 2026-11-26：首列宽到快占满整屏时**不要冻结**。
  // 手机上角色详情页的「基本信息」表：首列「变身立绘」被压成视口宽（实测 343 / 容器 342），
  // 一旦 sticky 就等于把整个屏幕盖住 —— 右侧「个人档案」横向滚到底也只露出 20 多像素，
  // 用户反馈"怎么滑都看不到第二列"。这类表改为不冻结，让首列跟着一起横向滚走。
  if (w1 > wrap.clientWidth * 0.7) {
    table.style.removeProperty('--escah-col1-w')
    return
  }

  table.style.setProperty('--escah-col1-w', Math.round(w1) + 'px')

  const w2 = identW ? identW[1] : 0
  const rest = wrap.clientWidth - w1 - (identW ? w2 : 0)
  const two = nameCol && rest >= (narrow ? 140 : 320) && (!narrow || !!identW)
  table.classList.add(two ? 'escah-frozen-2' : 'escah-frozen-1')
  markNoFreezeSpans(table, two ? 2 : 1)
}

// 视口宽度变化（跨 960 断点 / 侧栏收放）后重新判定列冻结，避免手机上残留桌面冻结状态
let frozenResizeBound = false
function bindFrozenResize(): void {
  if (frozenResizeBound) return
  frozenResizeBound = true
  let timer: number | undefined
  window.addEventListener('resize', () => {
    if (timer) window.clearTimeout(timer)
    timer = window.setTimeout(() => {
      document.querySelectorAll<HTMLTableElement>('table[data-escah="1"]').forEach((t) => {
        if (!t.isConnected) return
        markFrozenColumns(t)
        measureHeadHeight(t)
      })
    }, 250)
  })
}

function enhanceTable(table: HTMLTableElement, pageSlug?: string): void {
  if (table.getAttribute('data-escah') === '1') return
  normalizeTable(table)
  getOriginalRows(table)
  const smallTable = dataRows(table).length < 20
  // 「冻结行」= 表头吸顶：只在数据行 **超过 20** 时启用（2026-11-26 用户要求）。
  // 角色属性表（10 行）、装备表这类短表滚一下就过去，吸顶反而把内容挡住；
  // 样式见 custom.css 的 `table.escah-sticky-head thead th`。
  table.classList.toggle('escah-sticky-head', !smallTable)
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
  // 行数紧跟按钮之后（不要右对齐：表格需横向滚动时，行数在行尾会被挤出可视区）
  ;(table as TblCache)._escahAlwaysCount = alwaysShowCount(pageSlug)
  const btnFull = mkBtn('表格全屏', '页面内全屏查看（仅在表格超出可视宽度时出现）', () => toggleFullscreen(table))
  btnFull.classList.add('escah-tbl-full-btn')
  toolbar.appendChild(btnFull)
  if (!smallTable) {
    const btnReset = mkBtn('表格重置', '重置排序与筛选（清空多选）', () => resetTable(table))
    toolbar.appendChild(btnReset)
  }
  const countEl = document.createElement('span')
  countEl.className = 'escah-tbl-count'
  toolbar.appendChild(countEl)
  container.insertBefore(toolbar, wrapper)
  updateRowCount(table)

  requestAnimationFrame(() => syncFullBtnFor(container, wrapper, toolbar, btnFull))
  bindFullBtnResize()
  pendingHeadMeasures.push(table)

  table.setAttribute('data-escah', '1')
}

// 真实表格 class 是 PukiWiki 自带的 style_table（全站一致），同时兼容 escah-tbl；
// Vue 组件里手写的表（如更新记录）用 data-escah-enhance 显式开启——
// 不能给 table 挂 .escah-tbl：那是**容器** class，table.closest('.escah-tbl') 会命中自己，
// 导致工具栏/全屏/重置按钮查找全部落空。
export function enhanceTables(root: HTMLElement, pageSlug?: string): void {
  // table.stat-tbl：数据统计页里直接嵌入的作者原始小表（无 class 标记，也不该有排序/筛选），
  // 但行数显示要覆盖全站表格，故一并纳入（行数徽标 + 溢出时的全屏，不进排序/筛选）。
  for (const tbl of Array.from(
    root.querySelectorAll('table.style_table, table.escah-tbl, table.stat-tbl, table[data-escah-enhance]')
  )) {
    enhanceTable(tbl as HTMLTableElement, pageSlug)
  }
  // 所有表增强完（DOM 变更收敛）后再统一测表头高度，避免「写-读」交替反复重排整页
  flushHeadMeasures()
  bindFrozenResize()
  // 相邻表格连成一片（角色详情页的 基础属性/详细属性/必杀技/固有效果 原站本就是紧贴的一整块）
  joinAdjacentTables(root, pageSlug)
  // bedroom-scenes 等「每个表格前已有 strong 标题」的页面：在正文开头插入一个
  // 表格目录（列出各表标题并锚点跳转）。标题文字直接取表格前已有的 strong，不重复添加。
  if (pageSlug === 'bedroom-scenes') buildTableToc(root)
}

/* ------------------------------------------------------------------ */
/* 相邻表格拼接（2026-11-26）                                            */
/* ------------------------------------------------------------------ */
/**
 * 角色详情页的「基础属性 / 详细属性 / 必杀技 / 固有效果」在原站（raw）就是 4 个
 * **紧贴**的 PukiWiki style_table 小节表，每张只带一行 colspan 表头，视觉上像一个整块。
 * 本站每张都被包成 .escah-tbl（0.8em 外边距 + 一整套大按钮工具栏），手机上看起来像被
 * 拆成了 4 块、噪音很大。这里把「同一父节点、元素级相邻」的表串成一组：
 *   · 去掉中间空隙（CSS 里 .escah-tbl:has(+ .escah-tbl-sub) / .escah-tbl-sub）；
 *   · ≤959px 时把后续表的工具栏收敛成「⤢ + 小字行数」，避免 4 组大按钮糊满屏幕。
 * 幂等：路由来回切换时重复调用不会叠加。
 */
function joinAdjacentTables(root: HTMLElement, pageSlug?: string): void {
  const list = Array.from(root.querySelectorAll<HTMLElement>('.escah-tbl'))
  const narrow = window.matchMedia('(max-width: 959px)').matches

  // 两张表在版面里是否紧贴：从 a 出发逐级向上找「下一个兄弟」，命中的块包含 b 即算相邻。
  // （实测结构是 .mirror-content > .ie5 > .escah-tbl ×N —— 两张表各自在独立的 .ie5 里，
  //   所以不能只看 a.nextElementSibling === b。）
  const adjacent = (a: HTMLElement, b: HTMLElement): boolean => {
    let node: HTMLElement | null = a
    while (node && node !== b) {
      const nxt = node.nextElementSibling as HTMLElement | null
      if (nxt) return nxt === b || nxt.contains(b)
      node = node.parentElement
    }
    return false
  }

  const joined = list.map((el, i) => i > 0 && adjacent(list[i - 1], el))

  // 宽度（2026-11-26 最终版）：角色页这组小节表**必须四张同宽**，且「必杀技 / 固有效果」
  // 两表的第一列（名称）、第二列（效果）列宽也要严格一致。
  // 做法全部走 CSS 类 + colgroup（不做任何 px 测量，规避之前「手机宽带到 PC」「超宽被拉满」）：
  //   .escah-tbl-samew → width:100% + table-layout:fixed + max-width:min(100%,688px)
  //   列数 2 的表额外插 <colgroup>（26% / 74%），两表列宽天然相同。
  // 清理旧版本可能留在 DOM 上的 inline 宽度。
  // 是否角色详情页：slug 命中，或页面里存在「变身立绘 / 変身画像」这个**只有角色页才有**的
  // 表头（比 rowspan 图片可靠得多 —— raid-formations 的编队表也有 rowspan 图片，
  // 用那种判断会被误伤成 100%/fixed，图片全叠在一起）。
  // 实测 dev 环境 relativePath 有时拿不到 `characters/` 前缀，光靠 slug 会漏。
  const isCharPage =
    (!!pageSlug && pageSlug.includes('characters/')) ||
    Array.from(root.querySelectorAll('table th')).some((th) =>
      /变身立绘|変身画像|変身立絵/.test((th.textContent || '').trim()),
    )

  const groups: HTMLElement[][] = []
  let acc: HTMLElement[] = []
  list.forEach((el, i) => {
    if (joined[i]) acc.push(el)
    else {
      if (acc.length) groups.push(acc)
      acc = [el]
    }
  })
  if (acc.length) groups.push(acc)

  for (const g of groups) {
    // 角色页：排除「基本信息」表（含 rowspan 立绘图），其余小节表统一宽度
    const members = isCharPage ? g.filter((el) => !el.querySelector('td[rowspan] img')) : []
    for (const el of g) {
      el.classList.toggle('escah-tbl-samew', members.includes(el) && members.length >= 2)
      const t = el.querySelector('table')
      if (!t) continue
      t.style.removeProperty('width')
      t.style.removeProperty('max-width')
    }
    if (members.length < 2) continue
    for (const el of members) {
      const t = el.querySelector('table')
      if (!t) continue
      // 必杀技 / 固有效果：2 列表，插 <colgroup> 固定 26% / 74%，两表列宽严格一致
      if (tableCols(t) === 2) {
        t.classList.add('escah-tbl-2col')
        if (!t.querySelector('colgroup')) {
          const cg = document.createElement('colgroup')
          const c1 = document.createElement('col')
          c1.style.width = '26%'
          const c2 = document.createElement('col')
          c2.style.width = '74%'
          cg.append(c1, c2)
          t.insertBefore(cg, t.firstChild)
        }
      }
    }
  }

  list.forEach((el, i) => {
    el.classList.toggle('escah-tbl-sub', joined[i])
    // 组首：自己不是"后续表"、但下一张紧贴自己 → 去掉自身下外边距，两表无缝衔接
    el.classList.toggle('escah-tbl-join-head', !!joined[i + 1])
    const full = el.querySelector<HTMLElement>('.escah-tbl-full-btn')
    if (!full) return
    if (joined[i] && narrow) {
      if (!full.dataset.escahCompact) {
        full.dataset.escahLabel = full.textContent || '表格全屏'
        full.dataset.escahCompact = '1'
      }
      // 用文字而非符号：⤢ 这类箭头字形在部分中文字体里缺字，会显示成空白按钮
      full.textContent = '全屏'
      full.title = '放大表格'
    } else if (full.dataset.escahCompact) {
      full.textContent = full.dataset.escahLabel || '表格全屏'
      delete full.dataset.escahCompact
    }
  })
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
  closeAllFilterPops() // 切页时别留下 fixed 定位的筛选下拉
}
