import type { ReactNode } from 'react'
import {
  BTN_OUTLINE,
  BTN_OUTLINE_SM,
  CHIP_ACTIVE,
  CHIP_IDLE,
  ELLAN_INPUT,
  ELLAN_LABEL,
  ELLAN_SELECT,
  ELLAN_TEXTAREA,
} from '../../styles/formClasses'

export {
  BTN_OUTLINE,
  BTN_OUTLINE_SM,
  CHIP_ACTIVE,
  CHIP_IDLE,
  ELLAN_INPUT,
  ELLAN_LABEL,
  ELLAN_SELECT,
  ELLAN_TEXTAREA,
}

export function formatMoney(cents: number | null | undefined, currency = 'BRL') {
  const n = Number(cents)
  if (cents == null || Number.isNaN(n)) return '—'
  try {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(n / 100)
  } catch {
    return `${(n / 100).toFixed(2)} ${currency}`
  }
}

export function formatShortIso(iso: string | null | undefined) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('pt-BR')
  } catch {
    return String(iso)
  }
}

export function StatusPill({ active }: { active: boolean }) {
  const on = Boolean(active)
  return (
    <span
      className={
        on
          ? 'inline-flex rounded-full border border-emerald-500/50 bg-emerald-950/50 px-2 py-0.5 text-xs font-semibold text-emerald-300'
          : 'inline-flex rounded-full border border-red-500/50 bg-red-950/40 px-2 py-0.5 text-xs font-semibold text-red-300'
      }
    >
      {on ? 'Ativa' : 'Inativa'}
    </span>
  )
}

export function KpiCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-blue-500/30 bg-slate-900/40 p-3 dark:border-blue-500/40">
      <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-100">{value}</p>
      {sub ? <p className="mt-0.5 text-xs text-slate-500">{sub}</p> : null}
    </div>
  )
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="mt-3 rounded-xl border border-dashed border-slate-500/50 bg-slate-900/30 px-5 py-8 text-center text-sm text-slate-400">
      {children}
    </div>
  )
}

export function OpsErrorBanner({ children }: { children: ReactNode }) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-red-500/40 bg-red-950/40 px-3 py-2 text-sm text-red-200"
    >
      {children}
    </div>
  )
}

export function OpsSuccessBanner({ children }: { children: ReactNode }) {
  return <p className="rounded-lg border border-emerald-500/30 bg-emerald-950/30 px-3 py-2 text-sm text-emerald-300">{children}</p>
}

export function OpsInfoBanner({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-lg border border-amber-500/35 bg-amber-950/25 px-3 py-2 text-sm text-amber-200/90">{children}</p>
  )
}

export function OpsWorkspaceCard({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-600/60 bg-slate-900/20 p-4 dark:border-slate-600">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
          {hint ? <p className="mt-1 text-xs text-slate-400">{hint}</p> : null}
        </div>
      </div>
      {children}
    </section>
  )
}

export const TAB_BTN_ACTIVE =
  'rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-500'
export const TAB_BTN_IDLE =
  'rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 hover:border-slate-500 hover:bg-slate-700'

export function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button type="button" onClick={onClick} className={active ? TAB_BTN_ACTIVE : TAB_BTN_IDLE}>
      {children}
    </button>
  )
}

export const BTN_PRIMARY =
  'rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50'
export const BTN_GHOST = BTN_OUTLINE
export const BTN_SECONDARY =
  'rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm font-medium text-slate-100 hover:bg-slate-600 disabled:opacity-50'
export const BTN_SUCCESS =
  'rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50'
export const BTN_WARNING =
  'rounded-lg bg-amber-600 px-3 py-2 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50'
export const BTN_DANGER =
  'rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50'
export const BTN_INFO =
  'rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50'
export const BTN_SHORTCUT =
  'rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm font-medium text-indigo-300 hover:border-indigo-500/50 hover:bg-slate-700'

export function chipClass(active: boolean) {
  return active ? CHIP_ACTIVE : CHIP_IDLE
}
