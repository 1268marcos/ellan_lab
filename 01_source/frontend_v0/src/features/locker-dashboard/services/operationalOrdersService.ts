
import { buildAuthHeaders } from "../utils/dashboardPaymentUtils";

type UnknownRecord = Record<string, unknown>;

export async function fetchOperationalOrdersPage({
  orderPickupBase,
  token,
  params,
}: {
  orderPickupBase: string;
  token: unknown;
  params: Record<string, string>;
}) {
  const search = new URLSearchParams(params);
  const res = await fetch(`${orderPickupBase}/orders?${search.toString()}`, {
    headers: buildAuthHeaders(token),
  });

  const text = await res.text();

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  const data = JSON.parse(text) as { items?: unknown; has_next?: unknown };

  return {
    items: Array.isArray(data?.items) ? (data.items as UnknownRecord[]) : [],
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
}: {
  orderPickupBase: string;
  token: unknown;
  region: string;
  status?: string;
  channel?: string;
}) {
  const collected: UnknownRecord[] = [];
  let page = 1;
  let hasNext = true;

  while (hasNext) {
    const params: Record<string, string> = {
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
}: {
  items: UnknownRecord[];
  page: number;
  pageSize: number;
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

