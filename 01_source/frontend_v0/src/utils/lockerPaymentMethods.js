/**
 * Normaliza métodos de pagamento vindos do gateway (runtime), order_pickup ou admin.
 */

export function parsePaymentMethodsFromRaw(locker) {
  if (!locker || typeof locker !== "object") return [];

  const candidates = [
    locker.payment_methods,
    locker.payment_methods_json,
    locker.allowed_payment_methods,
  ];

  for (const raw of candidates) {
    const parsed = coercePaymentMethodList(raw);
    if (parsed.length) return parsed;
  }

  return [];
}

function coercePaymentMethodList(raw) {
  if (Array.isArray(raw)) {
    return raw.map((item) => String(item).trim()).filter(Boolean);
  }
  if (typeof raw === "string" && raw.trim()) {
    return raw
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

export function defaultPaymentMethodsForRegion(region) {
  const r = String(region || "").trim().toUpperCase();
  if (r === "PT") return ["MBWAY", "MULTIBANCO_REFERENCE", "CARD"];
  if (r === "ES") return ["CARD", "BIZUM"];
  return ["PIX", "CARD", "CASH"];
}

export function mergeLockerPaymentSources(...sources) {
  const seen = new Set();
  const out = [];
  for (const locker of sources) {
    for (const method of parsePaymentMethodsFromRaw(locker)) {
      const key = method.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(method);
    }
  }
  return out;
}
