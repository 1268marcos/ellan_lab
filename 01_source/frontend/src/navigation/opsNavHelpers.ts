import type { OpsNavGroup, OpsNavItem, OpsNavSection } from './opsMenuTypes'

export function navItem(
  to: string,
  label: string,
  opts?: { newTag?: string; keywords?: string },
): OpsNavItem {
  return { to, label, ...opts }
}

export function section(
  key: string,
  label: string,
  items: OpsNavItem[],
  defaultOpen = false,
): OpsNavSection {
  return { key, label, items, defaultOpen }
}

export function opsGroup(
  key: string,
  icon: string,
  label: string,
  config: {
    hub?: OpsNavItem
    sections?: OpsNavSection[]
    items?: OpsNavItem[]
  },
): OpsNavGroup {
  return { key, icon, label, ...config }
}
