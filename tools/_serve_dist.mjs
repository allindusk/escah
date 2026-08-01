import http from 'http'
import { readFile } from 'fs/promises'
import { join, extname, normalize } from 'path'

const dist = join(process.cwd(), '.vitepress/dist')
const types = {
  '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.html': 'text/html', '.json': 'application/json', '.woff2': 'font/woff2',
  '.woff': 'font/woff', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.gif': 'image/gif', '.ico': 'image/x-icon',
}
const port = 8088
const server = http.createServer(async (req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0])
  if (p.startsWith('/escah')) p = p.slice(5) || '/'
  if (p.endsWith('/')) p += 'index.html'
  // prevent path traversal (strip leading slash before join)
  const fp = normalize(join(dist, p.replace(/^\/+/, '')))
  console.log('REQ', p, '->', fp)
  if (!fp.startsWith(dist)) { res.statusCode = 403; return res.end('forbidden') }
  try {
    const data = await readFile(fp)
    res.setHeader('Content-Type', types[extname(fp)] || 'application/octet-stream')
    res.setHeader('Cache-Control', 'no-cache')
    res.end(data)
  } catch {
    res.statusCode = 404
    res.end('404 ' + fp)
  }
})
server.listen(port, () => console.log('serving dist at http://localhost:' + port + ' (base /escah/)'))
