import { useCallback, useState } from 'react'
import OpsSidebarNav from './navigation/OpsSidebarNav'
import { OPS_MENU_GROUPS } from '../navigation/opsMenuGroups'
import { buildGroupOpenState, buildSectionOpenState } from '../navigation/opsNavExpandState'

const DEFAULT_OPEN: Record<string, boolean> = {
  ops: true,
  usersSecurityOps: true,
  partnersOps: true,
  cadastros: true,
  hardwareOps: true,
  paymentsOps: true,
  orderPickup: true,
  workersOps: true,
  rentalsOps: true,
  privacyCompliance: false,
  moneyOps: true,
  cambioOps: false,
  fiscalOps: true,
  mlOps: true,
  financeOpsGlobal: true,
  financeOpsCommercial: true,
  financeOps: true,
  marketplace: true,
  marketing: true,
  productsCatalog: true,
  fiscal: true,
}

export default function Sidebar() {
  const [open, setOpen] = useState(DEFAULT_OPEN)
  const [sectionOpen, setSectionOpen] = useState<Record<string, boolean>>({})

  const expandAll = useCallback(() => {
    setOpen((prev) => ({ ...prev, ...buildGroupOpenState(OPS_MENU_GROUPS, true) }))
    setSectionOpen((prev) => ({ ...prev, ...buildSectionOpenState(OPS_MENU_GROUPS, true) }))
  }, [])

  const collapseAll = useCallback(() => {
    setOpen((prev) => ({ ...prev, ...buildGroupOpenState(OPS_MENU_GROUPS, false) }))
    setSectionOpen((prev) => ({ ...prev, ...buildSectionOpenState(OPS_MENU_GROUPS, false) }))
  }, [])

  const toggleSection = useCallback((groupKey: string, sectionKey: string) => {
    const id = `${groupKey}:${sectionKey}`
    setSectionOpen((prev) => {
      const group = OPS_MENU_GROUPS.find((g) => g.key === groupKey)
      const section = group?.sections?.find((s) => s.key === sectionKey)
      const current = id in prev ? prev[id] : Boolean(section?.defaultOpen)
      return { ...prev, [id]: !current }
    })
  }, [])

  return (
    <aside className="hidden h-full w-72 border-r border-gray-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 md:block">
      <OpsSidebarNav
        groups={OPS_MENU_GROUPS}
        open={open}
        onToggleGroup={(key) => setOpen((s) => ({ ...s, [key]: !s[key] }))}
        onExpandAll={expandAll}
        onCollapseAll={collapseAll}
        sectionOpen={sectionOpen}
        onToggleSection={toggleSection}
      />
    </aside>
  )
}
