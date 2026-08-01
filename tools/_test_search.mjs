import { createRequire } from 'module'
const require = createRequire(import.meta.url)
const { chromium } = require('C:\\Users\\SSS\\AppData\\Roaming\\npm\\node_modules\\@playwright\\cli\\node_modules\\playwright-core')

const EXEC = 'C:\\Users\\SSS\\AppData\\Local\\ms-playwright\\chromium_headless_shell-1234\\chrome-headless-shell-win64\\chrome-headless-shell.exe'
const URL = process.env.SEARCH_URL || 'http://localhost:4173/escah/zh/special-attributes.html'

const browser = await chromium.launch({ executablePath: EXEC, headless: true })
// 空缓存上下文 → 索引分块冷加载
const context = await browser.newContext({ bypassCSP: true })
const page = await context.newPage()
const logs = []
page.on('console', m => logs.push(`[${m.type()}] ${m.text()}`))
page.on('pageerror', e => logs.push(`[pageerror] ${e.message}`))

// 限速：下载 ~5MB/s，使 21MB 索引分块加载约 4s，便于观察进度（设 THROTTLE=0 可关闭）
const THROTTLE = process.env.THROTTLE !== '0'
if (THROTTLE) {
  const client = await context.newCDPSession(page)
  await client.send('Network.enable')
  await client.send('Network.emulateNetworkConditions', {
    offline: false, latency: 150, downloadThroughput: 5_000_000, uploadThroughput: 5_000_000,
  })
}

await page.goto(URL, { waitUntil: 'load', timeout: 60000 }).catch(e => logs.push(`[goto] ${e.message}`))
await page.waitForTimeout(2000)

const samples = []
let sawCard = false
// 点击搜索按钮
await page.click('.DocSearch-Button').catch(e => logs.push(`[click] ${e.message}`))

// 轮询进度卡片与百分比
for (let i = 0; i < 70; i++) {
  const s = await page.evaluate(() => {
    const card = document.querySelector('.escah-search-progress')
    if (!card) return { visible: false }
    const label = card.querySelector('.sp-label')?.textContent || ''
    const fill = card.querySelector('.sp-fill')?.style.width || ''
    const pctMatch = label.match(/（(\d+)%）/)
    return { visible: true, label, fill, pct: pctMatch ? +pctMatch[1] : null }
  })
  if (s.visible) sawCard = true
  samples.push(`${(i * 300)}ms:${s.visible ? s.pct + '%' : 'hidden'}`)
  if (s.visible && s.pct === 100) break
  await page.waitForTimeout(300)
}
logs.push(`[card] sawCard=${sawCard}`)
logs.push(`[card] timeline=${JSON.stringify(samples)}`)

// 转储所有资源条目名，确认索引分块名
const names = await page.evaluate(() =>
  [...performance.getEntriesByType('resource')].map((r) => r.name).filter((n) => /search|index|chunk/i.test(n)),
)
logs.push(`[resources] ${JSON.stringify(names)}`)

// 卡片消失后应能正常搜索
await page.fill('input.search-input', '魔法').catch(e => logs.push(`[fill] ${e.message}`))
await page.waitForTimeout(3000)
const res = await page.evaluate(() => {
  const box = document.querySelector('.VPLocalSearchBox')
  const lis = box ? [...box.querySelectorAll('.results li')] : []
  return { liCount: lis.length, first: lis.slice(0, 3).map(l => l.textContent?.slice(0, 50)) }
})
logs.push(`[result] ${JSON.stringify(res)}`)

console.log('=== LOGS ===')
console.log(logs.join('\n'))
await browser.close()
