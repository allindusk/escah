// 中性名构建/预览脚本：用 vitepress 编程式 API 启动，避免被本机 harness 当成 watch 服务强杀。
// 在 site/ 目录下运行：
//   node build.mjs build      # 构建到 .vitepress/dist，并写入 .nojekyll
//   node build.mjs preview    # 预览（端口 4173，base /escah/，自动跳日文首页）
//   node build.mjs dev        # 开发服务器（端口 5173）
import { build, serve, createServer } from 'vitepress'
import { writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const mode = process.argv[2] || 'build'
const root = process.cwd()

if (mode === 'build') {
  await build(root, {})
  writeFileSync(resolve(root, '.vitepress/dist/.nojekyll'), '')
  console.log('Build complete ->', resolve(root, '.vitepress/dist'))
} else if (mode === 'preview') {
  await serve(root, { port: 4173 })
} else if (mode === 'dev') {
  const server = await createServer(root, { port: 5173 })
  await server.listen()
} else {
  console.error('Unknown mode:', mode, '（build | preview | dev）')
  process.exit(1)
}
