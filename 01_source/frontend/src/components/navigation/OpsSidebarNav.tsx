import { useMemo, useState } from 'react'
import OpsNavLink from './OpsNavLink'
import type { OpsNavGroup } from '../../navigation/opsMenuTypes'
import { itemMatchesMenuQuery } from '../../navigation/opsNavMatch'

type Props = {
  groups: OpsNavGroup[]
  open: Record<string, boolean>
  onToggleGroup: (key: string) => void
}

function navLinkClass(active: boolean) {
  return `block rounded-md px-3 py-2 text-sm ${
    active
      ? 'bg-indigo-100 text-indigo-700 dark:bg-slate-800 dark:text-indigo-300'
      : 'text-gray-600 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-800'
  }`
}

function hubLinkClass(active: boolean) {
  return `mb-2 block rounded-lg border px-3 py-2.5 text-sm font-medium ${
    active
      ? 'border-indigo-400 bg-indigo-50 text-indigo-800 dark:border-indigo-500 dark:bg-indigo-950/50 dark:text-indigo-200'
      : 'border-indigo-200 bg-white text-indigo-700 hover:bg-indigo-50/80 dark:border-slate-600 dark:bg-slate-800/60 dark:text-indigo-200 dark:hover:bg-slate-800'
  }`
}

export default function OpsSidebarNav({ groups, open, onToggleGroup }: Props) {
  const [menuQuery, setMenuQuery] = useState('')
  const [sectionOpen, setSectionOpen] = useState<Record<string, boolean>>({})

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

  const toggleSection = (groupKey: string, sectionKey: string) => {
    const id = `${groupKey}:${sectionKey}`
    setSectionOpen((s) => ({ ...s, [id]: !(s[id] ?? true) }))
  }

  const isSectionExpanded = (group: OpsNavGroup, sectionKey: string, defaultOpen?: boolean) => {
    const id = `${group.key}:${sectionKey}`
    if (menuQuery.trim()) return true
    if (id in sectionOpen) return sectionOpen[id]
    return defaultOpen ?? false
  }

  return (
    <>
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
          className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
          autoComplete="off"
          spellCheck={false}
        />
        {menuQuery.trim() ? (
          <p className="mt-1 text-[11px] text-gray-500 dark:text-slate-400">
            {filteredGroups.length === 0 ? 'Nenhum resultado' : `${filteredGroups.length} grupo(s)`}
          </p>
        ) : null}
      </div>

      {filteredGroups.map((group) => (
        <div key={group.key} className="mb-2">
          <button
            type="button"
            className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm font-semibold text-gray-700 hover:bg-gray-100 dark:text-slate-200 dark:hover:bg-slate-800"
            onClick={() => onToggleGroup(group.key)}
            aria-expanded={open[group.key]}
          >
            <span className="flex items-center gap-2">
              <span aria-hidden>{group.icon}</span>
              {group.label}
            </span>
            <span className="text-xs text-gray-400" aria-hidden>
              {open[group.key] ? '▾' : '▸'}
            </span>
          </button>

          {open[group.key] && (
            <div className="mt-1 pl-2">
              {group.hub ? (
                <OpsNavLink
                  to={group.hub.to}
                  className={(active) => hubLinkClass(active)}
                >
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
                  <div key={section.key} className="mb-1">
                    <button
                      type="button"
                      className="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-[11px] font-bold uppercase tracking-wide text-gray-500 hover:bg-gray-50 dark:text-slate-400 dark:hover:bg-slate-800/80"
                      onClick={() => toggleSection(group.key, section.key)}
                      aria-expanded={expanded}
                    >
                      {section.label}
                      <span className="font-normal normal-case tracking-normal text-gray-400">
                        {expanded ? '▾' : '▸'}
                      </span>
                    </button>
                    {expanded && (
                      <div className="space-y-0.5 pl-1">
                        {section.items.map((item) => (
                          <OpsNavLink
                            key={item.to}
                            to={item.to}
                            className={(active) => navLinkClass(active)}
                          >
                            <span className="flex items-center justify-between gap-2">
                              <span>{item.label}</span>
                              {item.newTag ? (
                                <span className="shrink-0 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                                  {item.newTag}
                                </span>
                              ) : null}
                            </span>
                          </OpsNavLink>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}

              {group.items?.map((item) => (
                <OpsNavLink key={item.to} to={item.to} className={(active) => navLinkClass(active)}>
                  <span className="flex items-center justify-between gap-2">
                    <span>{item.label}</span>
                    {item.newTag ? (
                      <span className="shrink-0 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                        {item.newTag}
                      </span>
                    ) : null}
                  </span>
                </OpsNavLink>
              ))}
            </div>
          )}
        </div>
      ))}
    </>
  )
}
