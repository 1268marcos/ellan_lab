import type { OpsNavGroup } from './opsMenuTypes'

export function buildGroupOpenState(groups: OpsNavGroup[], expanded: boolean): Record<string, boolean> {
  return Object.fromEntries(groups.map((g) => [g.key, expanded]))
}

export function buildSectionOpenState(groups: OpsNavGroup[], expanded: boolean): Record<string, boolean> {
  const out: Record<string, boolean> = {}
  for (const group of groups) {
    for (const section of group.sections ?? []) {
      out[`${group.key}:${section.key}`] = expanded
    }
  }
  return out
}

export function mergeGroupOpenState(
  prev: Record<string, boolean>,
  groups: OpsNavGroup[],
  fallback = false,
): Record<string, boolean> {
  const next = { ...prev }
  for (const group of groups) {
    if (!(group.key in next)) next[group.key] = fallback
  }
  return next
}
