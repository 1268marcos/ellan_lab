
const REGION_TIMEZONES: Record<string, string> = {
  SP: "America/Sao_Paulo",
  RJ: "America/Sao_Paulo",
  MG: "America/Sao_Paulo",
  RS: "America/Sao_Paulo",
  BA: "America/Sao_Paulo",
  BR: "America/Sao_Paulo",
  PT: "Europe/Lisbon",
};

export function regionToTimezone(region: unknown) {
  const key = String(region || "").trim().toUpperCase();
  return REGION_TIMEZONES[key] || "UTC";
}

export function formatDateTimeByRegion(value: unknown, region: unknown) {
  if (!value) return "-";

  const date = new Date(value as string | number | Date);
  if (Number.isNaN(date.getTime())) return String(value);

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: regionToTimezone(region),
  }).format(date);
}

