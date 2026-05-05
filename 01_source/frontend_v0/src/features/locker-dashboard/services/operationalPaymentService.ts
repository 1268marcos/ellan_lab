
import { buildAuthHeaders } from "../utils/dashboardPaymentUtils";

type UnknownRecord = Record<string, unknown>;

export async function createOperationalOrder({
  orderPickupBase,
  token,
  payload,
}: {
  orderPickupBase: string;
  token: unknown;
  payload: UnknownRecord;
}) {
  const res = await fetch(`${orderPickupBase}/orders`, {
    method: "POST",
    headers: buildAuthHeaders(token),
    body: JSON.stringify(payload),
  });

  const text = await res.text();

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  return text ? (JSON.parse(text) as UnknownRecord) : {};
}

export async function executeGatewayPayment({
  gatewayUrl,
  token,
  payload,
}: {
  gatewayUrl: string;
  token: unknown;
  payload: UnknownRecord;
}) {
  const res = await fetch(gatewayUrl, {
    method: "POST",
    headers: buildAuthHeaders(token),
    body: JSON.stringify(payload),
  });

  const text = await res.text();

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  const data = (text ? JSON.parse(text) : {}) as UnknownRecord & {
    result?: string;
  };

  if (data.result === "requires_confirmation") {
    return {
      ...data,
      ui_status: "pending_action",
      ui_message: "Pagamento requer confirmação adicional",
    };
  }

  return data;
}

export async function confirmOperationalPayment({
  orderPickupBase,
  internalToken,
  orderId,
  payload,
}: {
  orderPickupBase: string;
  internalToken: string;
  orderId: string;
  payload: UnknownRecord;
}) {
  const res = await fetch(
    `${orderPickupBase}/internal/orders/${encodeURIComponent(orderId)}/payment-confirm`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Token": internalToken,
      },
      body: JSON.stringify(payload),
    }
  );

  const text = await res.text();

  if (!res.ok) {
    throw new Error(`payment-confirm HTTP ${res.status}: ${text}`);
  }

  return text ? (JSON.parse(text) as UnknownRecord) : {};
}

