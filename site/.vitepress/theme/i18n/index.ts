import { useData } from 'vitepress'
import ja from './ja.json'
import zh from './zh.json'

type Dict = typeof ja
const dicts: Record<string, Dict> = { ja, zh }

export function useI18n() {
  const { lang } = useData()
  const dict = () => (lang.value.startsWith('zh') ? zh : ja)
  const t = (path: string, vars?: Record<string, string | number>): string => {
    const parts = path.split('.')
    let cur: any = dict()
    for (const p of parts) cur = cur?.[p]
    let s = typeof cur === 'string' ? cur : path
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, String(v))
    return s
  }
  const isZh = () => lang.value.startsWith('zh')
  return { t, isZh, dict }
}
