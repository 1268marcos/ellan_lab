// 01_source/frontend/src/features/locker-dashboard/services/operationalOrdersService.js

import { buildAuthHeaders } from "../utils/dashboardPaymentUtils.js";

export async function fetchOperationalOrdersPage({
  orderPickupBase,
  token,
  params,
}) {
  const search = new URLSearchParams(params);
  const res = await fetch(`${orderPickupBase}/orders?${search.toString()}`, {
    headers: buildAuthHeaders(token),
  });

  const text = await res.text();

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  const data = JSON.parse(text);

  return {
    items: Array.isArray(data?.items) ? data.items : [],
    hasNext: Boolean(data?.has_next),
    raw: data,
  };
}

export async function fetchAllOperationalOrders({
  orderPickupBase,
  token,
  region,
  status,
  channel,
}) {
  const collected = [];
  let page = 1;
  let hasNext = true;

  while (hasNext) {
    const params = {
      region,
      scope: "ops",
      page: String(page),
      page_size: "100",
    };

    if (status) params.status = status;
    if (channel) params.channel = channel;

    const result = await fetchOperationalOrdersPage({
      orderPickupBase,
      token,
      params,
    });

    collected.push(...result.items);
    hasNext = result.hasNext;
    page += 1;
  }

  return collected;
}

export function paginateOperationalOrders({
  items,
  page,
  pageSize,
}) {
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const resolvedPage = Math.min(Math.max(1, page), totalPages);

  const start = (resolvedPage - 1) * pageSize;
  const end = start + pageSize;
  const pageItems = items.slice(start, end);

  return {
    total,
    totalPages,
    resolvedPage,
    pageItems,
    hasPrev: resolvedPage > 1,
    hasNext: resolvedPage < totalPages,
  };
}