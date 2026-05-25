import { useMemo, useState } from 'react'
import OpsNavLink from './OpsNavLink'
import type { OpsNavGroup } from '../../navigation/opsMenuTypes'
import { itemMatchesMenuQuery } from '../../navigation/opsNavMatch'

type Props = {
  groups: OpsNavGroup[]
  open: Record<string, boolean>
  onToggleGroup: (key: string) => void
  onExpandAll: (visibleGroups: OpsNavGroup[]) => void
  onCollapseAll: (visibleGroups: OpsNavGroup[]) => void
  sectionOpen: Record<string, boolean>
  onToggleSection: (groupKey: string, sectionKey: string) => void
}

function navLinkClass(active: boolean) {
  return `block rounded-md px-3 py-2 text-sm ${
    active
      ? 'bg-slate-800 text-indigo-300'
      : 'text-slate-300 hover:bg-slate-800'
  }`
}

function hubLinkClass(active: boolean) {
  return `mb-2 block rounded-lg border px-3 py-2.5 text-sm font-medium ${
    active
      ? 'border-indigo-500 bg-indigo-950/50 text-indigo-200'
      : 'border-slate-600 bg-slate-800/60 text-indigo-200 hover:bg-slate-800'
  }`
}

const TOOLBAR_BTN =
  'flex flex-1 items-center justify-center gap-1 rounded-md border border-slate-600 bg-slate-800/80 px-2 py-1.5 text-[11px] font-medium text-slate-200 hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/40'

export default function OpsSidebarNav({
  groups,
  open,
  onToggleGroup,
  onExpandAll,
  onCollapseAll,
  sectionOpen,
  onToggleSection,
}: Props) {
  const [menuQuery, setMenuQuery] = useState('')

  const filteredGroups = useMemo(() => {
    const q = menuQuery.trim()
    if (!q) return groups
    return groups
      .map((group) => {
        if (group.sections?.length) {
          const sections = group.sections
            .map((sec) => ({
              ...sec,
              items: sec.items.filter((item) =>
                itemMatchesMenuQuery(item, group.label, sec.label, q),
              ),
            }))
            .filter((sec) => sec.items.length > 0)
          const hubOk = group.hub && itemMatchesMenuQuery(group.hub, group.label, undefined, q)
          if (!sections.length && !hubOk) return null
          return { ...group, sections, hub: hubOk ? group.hub : undefined }
        }
        const items = (group.items ?? []).filter((item) =>
          itemMatchesMenuQuery(item, group.label, undefined, q),
        )
        if (!items.length) return null
        return { ...group, items }
      })
      .filter(Boolean) as OpsNavGroup[]
  }, [groups, menuQuery])

  const isSectionExpanded = (group: OpsNavGroup, sectionKey: string, defaultOpen?: boolean) => {
    const id = `${group.key}:${sectionKey}`
    if (menuQuery.trim()) return true
    if (id in sectionOpen) return sectionOpen[id]
    return defaultOpen ?? false
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="shrink-0 border-b border-slate-700 bg-slate-900 px-3 py-3">
      <div className="mb-2 flex gap-1" role="toolbar" aria-label="Controles do menu">
        <button
          type="button"
          className={TOOLBAR_BTN}
          onClick={() => onExpandAll(filteredGroups)}
          title="Expandir todos os grupos e seções"
        >
          <span aria-hidden className="text-xs leading-none">
            ⊞
          </span>
          Expandir
        </button>
        <button
          type="button"
          className={TOOLBAR_BTN}
          onClick={() => onCollapseAll(filteredGroups)}
          title="Recolher todos os grupos e seções"
        >
          <span aria-hidden className="text-xs leading-none">
            ⊟
          </span>
          Recolher
        </button>
      </div>

      <div className="mb-3">
        <label htmlFor="ops-menu-search" className="sr-only">
          Buscar no menu OPS
        </label>
        <input
          id="ops-menu-search"
          type="search"
          value={menuQuery}
          onChange={(e) => setMenuQuery(e.target.value)}
          placeholder="Buscar telas OPS…"
          className="ellan-field w-full"
          autoComplete="off"
          spellCheck={false}
        />
        {menuQuery.trim() ? (
          <p className="mt-1 text-[11px] text-slate-400">
            {filteredGroups.length === 0 ? 'Nenhum resultado' : `${filteredGroups.length} grupo(s)`}
          </p>
        ) : null}
      </div>
      </div>

      <div className="ellan-sidebar-scroll min-h-0 flex-1 overflow-x-hidden overflow-y-auto px-3 py-2">
      {filteredGroups.map((group) => (
        <div key={group.key} className="mb-1">
          <button
            type="button"
            className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm font-semibold text-slate-200 hover:bg-slate-800"
            onClick={() => onToggleGroup(group.key)}
            aria-expanded={Boolean(open[group.key])}
          >
            <span className="flex min-w-0 items-center gap-2">
              <span className="shrink-0 text-base leading-none" aria-hidden>
                {group.icon}
              </span>
              <span className="truncate">{group.label}</span>
            </span>
            <span className="shrink-0 text-xs text-slate-500" aria-hidden>
              {open[group.key] ? '▾' : '▸'}
            </span>
          </button>

          {open[group.key] ? (
            <div className="mt-0.5 border-l border-slate-700/80 pl-2">
              {group.hub ? (
                <OpsNavLink to={group.hub.to} className={(active) => hubLinkClass(active)}>
                  <span className="flex items-center justify-between gap-2">
                    <span>{group.hub.label}</span>
                    {group.hub.newTag ? (
                      <span className="shrink-0 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                        {group.hub.newTag}
                      </span>
                    ) : null}
                  </span>
                </OpsNavLink>
              ) : null}

              {group.sections?.map((section) => {
                const expanded = isSectionExpanded(group, section.key, section.defaultOpen)
                return (
                  <div key={section.key} className="mb-0.5">
                    <button
                      type="button"
                      className="flex w-full items-center justify-between rounded px-2 py-1 text-left text-[11px] font-bold uppercase tracking-wide text-slate-400 hover:bg-slate-800/80"
                      onClick={() => onToggleSection(group.key, section.key)}
                      aria-expanded={expanded}
                    >
                      <span className="truncate">{section.label}</span>
                      <span className="shrink-0 font-normal normal-case tracking-normal text-slate-500">
                        {expanded ? '▾' : '▸'}
                      </span>
                    </button>
                    {expanded ? (
                      <div className="space-y-0.5 border-l border-slate-800 pl-1">
                        {section.items.map((item) => (
                          <OpsNavLink
                            key={item.to}
                            to={item.to}
                            className={(active) => navLinkClass(active)}
                          >
                            <span className="flex items-center justify-between gap-2">
                              <span className="truncate">{item.label}</span>
                              {item.newTag ? (
                                <span className="shrink-0 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                                  {item.newTag}
                                </span>
                              ) : null}
                            </span>
                          </OpsNavLink>
                        ))}
                      </div>
                    ) : null}
                  </div>
                )
              })}

              {group.items?.map((item) => (
                <OpsNavLink key={item.to} to={item.to} className={(active) => navLinkClass(active)}>
                  <span className="flex items-center justify-between gap-2">
                    <span className="truncate">{item.label}</span>
                    {item.newTag ? (
                      <span className="shrink-0 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                        {item.newTag}
                      </span>
                    ) : null}
                  </span>
                </OpsNavLink>
              ))}
            </div>
          ) : null}
        </div>
      ))}
      </div>
    </div>
  )
}
