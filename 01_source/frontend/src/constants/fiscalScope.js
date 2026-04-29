export const FISCAL_SCOPE_TRACK_LABEL = "Trilha B real";
export const FISCAL_SCOPE_COUNTRIES_LABEL = "BR/PT";
export const FISCAL_SCOPE_PREFIX_BASE = "Escopo atual";

export const FISCAL_SCOPE_GATE_PANEL_TITLE = `Gates fiscais (${FISCAL_SCOPE_PREFIX_BASE.toLowerCase()}: ${FISCAL_SCOPE_TRACK_LABEL} ${FISCAL_SCOPE_COUNTRIES_LABEL})`;
export const FISCAL_SCOPE_QUICK_ACTIONS_TITLE = `Ações rápidas de plantão (${FISCAL_SCOPE_PREFIX_BASE.toLowerCase()} ${FISCAL_SCOPE_COUNTRIES_LABEL})`;
export const FISCAL_SCOPE_PROVIDERS_INFO = `${FISCAL_SCOPE_GATE_PANEL_TITLE}. Novos gates poderão ser adicionados neste painel.`;

export function buildFiscalScopePrefix(country) {
  return `[${FISCAL_SCOPE_PREFIX_BASE}: ${FISCAL_SCOPE_TRACK_LABEL} ${country}]`;
}

export function buildFiscalScopedGateTitle(country) {
  return `Gate fiscal (escopo atual) - ${country} real`;
}
