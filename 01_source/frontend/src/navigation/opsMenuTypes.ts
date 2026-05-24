export type OpsNavItem = {
  to: string
  label: string
  newTag?: string
  /** Texto extra para filtro no menu (não exibido). */
  keywords?: string
}

export type OpsNavSection = {
  key: string
  label: string
  /** Aberto por padrão ao expandir o grupo. */
  defaultOpen?: boolean
  items: OpsNavItem[]
}

export type OpsNavGroup = {
  key: string
  icon: string
  label: string
  /** Entrada principal (atalho destacado no topo do grupo). */
  hub?: OpsNavItem
  sections?: OpsNavSection[]
  items?: OpsNavItem[]
}
