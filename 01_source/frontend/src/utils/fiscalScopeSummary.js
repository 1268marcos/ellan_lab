import { buildFiscalScopePrefix } from "../constants/fiscalScope";

export function withScopePrefixIfGenericSummary(summaryValue, country) {
  const summary = String(summaryValue || "").trim();
  const normalized = summary.toLowerCase();
  const genericSignals = [
    "checklist",
    "go/no-go",
    "gate",
    "não carregado",
    "nao carregado",
    "indisponível",
    "indisponivel",
    "sem dados",
  ];
  const hasScopeSignal =
    normalized.includes("escopo") ||
    normalized.includes("trilha b") ||
    normalized.includes("br") ||
    normalized.includes("pt");
  const looksGeneric = !summary || genericSignals.some((token) => normalized.includes(token));
  const baseSummary = summary || `Checklist ${country} não carregado.`;
  if (!looksGeneric || hasScopeSignal) return baseSummary;
  return `${buildFiscalScopePrefix(country)} ${baseSummary}`;
}
