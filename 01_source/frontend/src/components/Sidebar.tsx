import { useState } from 'react'
import OpsSidebarNav from './navigation/OpsSidebarNav'
import { OPS_MENU_GROUPS } from '../navigation/opsMenuGroups'

export default function Sidebar() {
  const [open, setOpen] = useState<Record<string, boolean>>({
    ops: true,
    partnersOps: true,
    cadastros: true,
    paymentsOps: true,
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
    inteligencia: true,
    fiscal: true,
  })

  return (
    <aside className="hidden h-full w-72 border-r border-gray-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 md:block">
      <OpsSidebarNav
        groups={OPS_MENU_GROUPS}
        open={open}
        onToggleGroup={(key) => setOpen((s) => ({ ...s, [key]: !s[key] }))}
      />
    </aside>
  )
}
