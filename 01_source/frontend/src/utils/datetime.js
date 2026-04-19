// 01_source/frontend/src/utils/datetime.js
// 19/04/2026 - novo arquivo
// 19/04/2026 - datetime formato padrão ISO 8601

const REGION_TIMEZONES = {
  SP: "America/Sao_Paulo",
  RJ: "America/Sao_Paulo",
  MG: "America/Sao_Paulo",
  RS: "America/Sao_Paulo",
  BA: "America/Sao_Paulo",
  BR: "America/Sao_Paulo",
  PT: "Europe/Lisbon",
};

export function regionToTimezone(region) {
  const key = String(region || "").trim().toUpperCase();
  return REGION_TIMEZONES[key] || "UTC";
}

export function formatDateTimeByRegion(value, region) {
  if (!value) return "-";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: regionToTimezone(region),
  }).format(date);
}
