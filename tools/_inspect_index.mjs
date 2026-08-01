import { readFileSync } from 'fs'
import { join } from 'path'
import { readdirSync } from 'fs'

const dir = 'site/.vitepress/dist/assets/chunks'
const f = readdirSync(dir).find(n => n.includes('localSearchIndexzh'))
const raw = readFileSync(join(dir, f))
console.log('file:', f, 'sizeMB:', (raw.length / 1e6).toFixed(1))
let s = raw.toString('utf8')
// 格式： const t='<json>';export{t as default}
const start = s.indexOf("const t='") + "const t='".length
const end = s.lastIndexOf("';export{t as default}")
const json = s.slice(start, end)
const data = JSON.parse(json)
console.log('top-level keys:', Object.keys(data))
for (const k of Object.keys(data)) {
  const v = data[k]
  const size = typeof v === 'string' ? v.length : JSON.stringify(v).length
  console.log(`  key=${k} type=${typeof v} approxSize=${size}`)
}
// 兼容多种结构
const docs = data.documents || data.docs || (Array.isArray(data) ? data : [])
console.log('documents-like length:', docs.length || (docs === data ? Object.keys(data).length : 0))
let totalText = 0, maxText = 0, titlesCount = 0, emptyText = 0
const sample = []
const list = Array.isArray(docs) ? docs : (data.documents ? Object.values(data.documents) : [])
for (const d of list) {
  const txt = d && (d.text || (d[1] && d[1].text) || '')
  const t = (txt || '').length
  totalText += t
  if (t === 0) emptyText++
  if (t > maxText) maxText = t
  const titles = d && (d.titles || (d[1] && d[1].titles))
  if (titles && titles.length) titlesCount++
  if (sample.length < 5) sample.push({ id: d && (d.id || d[0]), titles, textLen: t, textHead: (txt||'').slice(0,80) })
}
console.log('total text chars:', totalText, 'avg:', (totalText/ (list.length||1)).toFixed(0), 'max:', maxText)
console.log('docs with titles:', titlesCount, 'empty text docs:', emptyText)
const ids = Object.values(data.documentIds || {})
console.log('documentIds entries:', ids.length, 'distinct pages:', new Set(ids.map(i => (i||'').split('#')[0])).size)
console.log('sample:', JSON.stringify(sample, null, 2))
