// 01_source/frontend/src/features/locker-dashboard/services/operationalPaymentService.js

import { buildAuthHeaders } from "../utils/dashboardPaymentUtils.js";

export async function createOperationalOrder({
  orderPickupBase,
  token,
  payload,
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

  return text ? JSON.parse(text) : {};
}

export async function executeGatewayPayment({
  gatewayUrl,
  token,
  payload,
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

  return text ? JSON.parse(text) : {};
}

export async function confirmOperationalPayment({
  orderPickupBase,
  internalToken,
  orderId,
  payload,
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

  return text ? JSON.parse(text) : {};
}