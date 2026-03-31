// 01_source/frontend/src/features/locker-dashboard/services/operationalPickupService.js

import { buildAuthHeaders } from "../utils/dashboardPaymentUtils.js";

export async function regeneratePickupToken({
  orderPickupBase,
  token,
  orderId,
}) {
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

  return text ? JSON.parse(text) : {};
}