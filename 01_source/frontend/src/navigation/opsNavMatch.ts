import type { Location } from 'react-router-dom'
import { OPS_ROUTE_DEFAULT_TAB } from './opsRouteDefaults'

/** Ativo por pathname + query `tab` (evita marcar todas as abas do mesmo admin). */
export function isOpsNavItemActive(to: string, location: Location): boolean {
  const [path, query = ''] = to.split('?')
  if (location.pathname !== path) return false
  if (!query) {
    const current = new URLSearchParams(location.search).get('tab')
    const defaultTab = OPS_ROUTE_DEFAULT_TAB[path]
    if (!current) return true
    if (!defaultTab) return false
    return current === defaultTab
  }
  const expected = new URLSearchParams(query)
  const actual = new URLSearchParams(location.search)
  for (const [key, value] of expected.entries()) {
    if (actual.get(key) !== value) return false
  }
  return true
}

export function itemMatchesMenuQuery(
  item: { label: string; keywords?: string; to?: string },
  groupLabel: string,
  sectionLabel: string | undefined,
  query: string,
): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  const hay = [item.label, item.keywords, item.to, groupLabel, sectionLabel].filter(Boolean).join(' ').toLowerCase()
  return hay.includes(q)
}
