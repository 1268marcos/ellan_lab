import React, { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

import {
  IconBars,
  IconBox,
  IconChart,
  IconCheck,
  IconRocket,
  IconTruck,
} from '../../components/coo/CooNavIcons'

import '../../styles/coo/coo.css'
import '../../styles/coo/global.css'
import { getCooThemeCssVariables } from '../../styles/coo/theme'

const COO_MENU = [
  {
    section: 'Operações',
    icon: IconRocket,
    items: [
      { path: '/coo/dashboard', label: 'Dashboard OPS consolidado', endpoint: 'dashboard/consolidated' },
      { path: '/coo/health/pickups', label: 'Saúde de pickups', endpoint: 'health/pickups' },
      { path: '/coo/deadlines/urgent', label: 'Deadlines urgentes', endpoint: 'deadlines/urgent' },
    ],
  },
  {
    section: 'Logística',
    icon: IconBox,
    items: [
      { path: '/coo/logistics/manifests', label: 'Manifestos ativos', endpoint: 'logistics/manifests/active' },
      { path: '/coo/logistics/routing', label: 'Roteirização em tempo real', endpoint: 'logistics/routing/realtime' },
      { path: '/coo/logistics/inventory', label: 'Inventário por depot', endpoint: 'logistics/inventory/by-depot' },
    ],
  },
  {
    section: 'Fornecedores',
    icon: IconTruck,
    items: [
      { path: '/coo/suppliers/sla', label: 'SLA por fornecedor', endpoint: 'suppliers/sla' },
      { path: '/coo/suppliers/penalties', label: 'Penalidades aplicadas', endpoint: 'suppliers/penalties' },
      { path: '/coo/suppliers/compliance', label: 'Compliance reports', endpoint: 'suppliers/compliance' },
    ],
  },
  {
    section: 'KPIs operacionais',
    icon: IconChart,
    items: [
      { path: '/coo/kpis/uptime', label: 'Uptime da rede', endpoint: 'kpis/network/uptime' },
      { path: '/coo/kpis/mttr', label: 'Tempo médio de resolução (MTTR)', endpoint: 'kpis/mttr' },
      { path: '/coo/kpis/fleet', label: 'Eficiência de frota', endpoint: 'kpis/fleet/efficiency' },
    ],
  },
  {
    section: 'Aprovações',
    icon: IconCheck,
    items: [
      { path: '/coo/approvals/pending', label: 'Procedimentos pendentes', endpoint: 'approvals/pending' },
      { path: '/coo/approvals/sla', label: 'Ajustes de SLA regional', endpoint: 'approvals/sla/adjust' },
      { path: '/coo/approvals/expansion', label: 'Solicitações de expansão', endpoint: 'approvals/expansion' },
    ],
  },
] as const

export const COOLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="coo-layout coo-portal" style={getCooThemeCssVariables()}>
      <aside
        className={`coo-sidebar ${collapsed ? 'coo-sidebar--collapsed' : 'coo-sidebar--expanded'}`}
        aria-label="Navegação COO"
      >
        <div className="coo-sidebar__header">
          {!collapsed && <span className="coo-sidebar__title">COO Portal</span>}
          <button
            type="button"
            className="coo-sidebar__toggle"
            aria-expanded={!collapsed}
            aria-label={collapsed ? 'Expandir menu' : 'Recolher menu'}
            onClick={() => setCollapsed((v) => !v)}
          >
            <IconBars width={18} height={18} />
          </button>
        </div>

        {COO_MENU.map((section, idx) => {
          const Icon = section.icon
          return (
            <div key={idx} className="coo-nav-section">
              {!collapsed && (
                <div className="coo-sidebar__section-label" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Icon width={14} height={14} />
                  {section.section}
                </div>
              )}
              {section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `coo-navlink ${isActive ? 'coo-navlink--active' : ''}`
                  }
                >
                  <Icon width={collapsed ? 20 : 18} height={collapsed ? 20 : 18} />
                  {!collapsed && <span>{item.label}</span>}
                </NavLink>
              ))}
            </div>
          )
        })}
      </aside>

      <main
        className={`coo-main ${collapsed ? 'coo-main--collapsed' : 'coo-main--expanded'}`}
      >
        <div className="coo-main__inner">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
