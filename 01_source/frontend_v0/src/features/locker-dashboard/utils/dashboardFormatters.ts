
export function formatMoney(
  cents: unknown,
  options: {
    currency?: string;
    locale?: string;
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
  } = {}
) {
  const value = Number(cents);
  if (!Number.isFinite(value)) return "-";

  const {
    currency = "",
    locale = undefined,
    minimumFractionDigits = 2,
    maximumFractionDigits = 2,
  } = options;

  const amount = value / 100;
  const safeCurrency = String(currency || "").trim().toUpperCase();

  try {
    if (safeCurrency) {
      return new Intl.NumberFormat(locale, {
        style: "currency",
        currency: safeCurrency,
        minimumFractionDigits,
        maximumFractionDigits,
      }).format(amount);
    }

    return new Intl.NumberFormat(locale, {
      minimumFractionDigits,
      maximumFractionDigits,
    }).format(amount);
  } catch {
    return safeCurrency
      ? `${amount.toFixed(2)} ${safeCurrency}`.trim()
      : amount.toFixed(2);
  }
}

export function formatPlainMoney(cents: unknown) {
  const value = Number(cents);
  if (!Number.isFinite(value)) return "-";
  return (value / 100).toFixed(2);
}

export function regionTimeZone(region: string) {
  return region === "SP" ? "America/Sao_Paulo" : "Europe/Lisbon";
}

export function formatDateTime(value: unknown, region = "PT", locale = "pt-BR") {
  if (!value) return "-";

  try {
    const raw = String(value).trim();
    const normalized = /(?:Z|[+-]\d{2}:\d{2})$/.test(raw) ? raw : `${raw}Z`;
    const dt = new Date(normalized);

    if (Number.isNaN(dt.getTime())) {
      return String(value);
    }

    return dt.toLocaleString(locale, {
      timeZone: regionTimeZone(region),
      hour12: false,
    });
  } catch {
    return String(value);
  }
}

export function formatEpochDateTime(epochSec: unknown, region = "PT", locale = "pt-BR") {
  if (!epochSec) return "-";

  try {
    const dt = new Date(Number(epochSec) * 1000);
    if (Number.isNaN(dt.getTime())) return "-";

    return dt.toLocaleString(locale, {
      timeZone: regionTimeZone(region),
      hour12: false,
    });
  } catch {
    return "-";
  }
}

export function formatLockerAddress(locker: Record<string, unknown> | null | undefined) {
  if (!locker) return "-";

  const address = (locker.address as Record<string, unknown> | undefined) || {};
  return [
    [address.address, address.number].filter(Boolean).join(", "),
    address.additional_information || "",
    address.locality || "",
    [address.city, address.federative_unit].filter(Boolean).join(" / "),
    address.postal_code || "",
    address.country || "",
  ]
    .map((x) => String(x || "").trim())
    .filter(Boolean)
    .join(" • ");
}
