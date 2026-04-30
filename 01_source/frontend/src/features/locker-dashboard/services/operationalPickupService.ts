import { buildAuthHeaders } from "../utils/dashboardPaymentUtils";

type UnknownRecord = Record<string, unknown>;

export async function regeneratePickupToken({
  orderPickupBase,
  token,
  orderId,
}: {
  orderPickupBase: string;
  token: unknown;
  orderId: string;
}): Promise<UnknownRecord> {
  const res = await fetch(
    `${orderPickupBase}/orders/${encodeURIComponent(orderId)}/pickup-token`,
    {
      method: "POST",
      headers: buildAuthHeaders(token),
      body: "{}",
    }
  );

  const text = await res.text();

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  return text ? (JSON.parse(text) as UnknownRecord) : {};
}
