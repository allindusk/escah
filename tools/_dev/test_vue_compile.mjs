// 可行性试验：把 frag 的正文 HTML 直接放进 Vue 模板（v-pre 包裹）能否编译，
// 以及编译产物里是否出现 createStaticVNode（= lean 包可被剥离的静态内容）。
import { readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { compile } from '@vue/compiler-dom'

const FRAG = resolve('site/.vitepress/frag')
const files = readdirSync(FRAG).filter((f) => f.endsWith('.json'))

let ok = 0
let staticVNode = 0
let fail = 0
const errs = []
let worst = null

for (const f of files) {
  const frag = JSON.parse(readFileSync(resolve(FRAG, f), 'utf-8'))
  const html = frag.html || ''
  const code = `<div v-pre>${html}</div>`
  try {
    const out = compile(code, { hoistStatic: true, onError: () => {} })
    ok++
    if (out.code.includes('createStaticVNode')) staticVNode++
    if (!worst || out.code.length > worst.len) worst = { f, len: out.code.length }
  } catch (e) {
    fail++
    if (errs.length < 6) errs.push(`${f}: ${String(e.message).slice(0, 160)}`)
  }
}

console.log(`frag 总数 ${files.length}  编译通过 ${ok}  含 createStaticVNode ${staticVNode}  失败 ${fail}`)
console.log('最大产物:', worst)
errs.forEach((e) => console.log('  ✗', e))
