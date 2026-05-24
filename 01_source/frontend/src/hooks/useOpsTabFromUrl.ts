import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { OPS_ROUTE_DEFAULT_TAB } from '../navigation/opsRouteDefaults'

/** Sincroniza aba da página admin com `?tab=` na URL (deep links do menu). */
export function useOpsTabFromUrl<T extends string>(
  pathname: string,
  allowed: readonly T[],
  fallback?: T,
) {
  const [searchParams, setSearchParams] = useSearchParams()
  const defaultTab = (OPS_ROUTE_DEFAULT_TAB[pathname] as T | undefined) ?? fallback ?? allowed[0]
  const raw = searchParams.get('tab')
  const tab: T = raw && (allowed as readonly string[]).includes(raw) ? (raw as T) : defaultTab

  const setTab = useCallback(
    (next: T) => {
      const p = new URLSearchParams(searchParams)
      if (next === defaultTab) p.delete('tab')
      else p.set('tab', next)
      setSearchParams(p, { replace: true })
    },
    [searchParams, setSearchParams, defaultTab],
  )

  return { tab, setTab, defaultTab }
}
