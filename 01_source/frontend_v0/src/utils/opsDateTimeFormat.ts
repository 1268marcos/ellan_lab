
/**
 * Formatação de data/hora para telas OPS/fiscal com defaults para operação no Brasil
 * (locale pt-BR, fuso America/Sao_Paulo). Útil para relatórios e timeline auditável
 * independentemente do fuso do SO do analista.
 */
export const OPS_DEFAULT_LOCALE = "pt-BR";
export const OPS_DEFAULT_TIMEZONE = "America/Sao_Paulo";

export type FormatOpsDateTimeOptions = {
  locale?: string;
  timeZone?: string;
  dateStyle?: Intl.DateTimeFormatOptions["dateStyle"];
  timeStyle?: Intl.DateTimeFormatOptions["timeStyle"];
};

export function formatOpsDateTime(
  input: Date | string | number,
  opts?: FormatOpsDateTimeOptions,
): string {
  const d = input instanceof Date ? input : new Date(input);
  if (Number.isNaN(d.getTime())) return "-";
  return new Intl.DateTimeFormat(opts?.locale ?? OPS_DEFAULT_LOCALE, {
    dateStyle: opts?.dateStyle ?? "short",
    timeStyle: opts?.timeStyle ?? "medium",
    timeZone: opts?.timeZone ?? OPS_DEFAULT_TIMEZONE,
  }).format(d);
}

/** Hora local no fuso OPS (ex.: eixo de gráfico). */
export function formatOpsTimeShort(
  input: Date | string | number,
  opts?: Pick<FormatOpsDateTimeOptions, "locale" | "timeZone">,
): string {
  const d = input instanceof Date ? input : new Date(input);
  if (Number.isNaN(d.getTime())) return "-";
  return new Intl.DateTimeFormat(opts?.locale ?? OPS_DEFAULT_LOCALE, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: opts?.timeZone ?? OPS_DEFAULT_TIMEZONE,
  }).format(d);
}

