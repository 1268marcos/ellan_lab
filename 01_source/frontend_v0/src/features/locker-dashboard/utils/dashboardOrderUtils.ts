
import type { CheckoutCurrentOrder } from "../../checkout/types";
import {
  ORDER_STATUS_META,
  PICKUP_STATUS_META,
  ALLOCATION_STATUS_META,
  CHANNEL_META,
} from "./dashboardConstants";
import { formatDateTime } from "./dashboardFormatters";
import { groupIndexFromSlot } from "./dashboardSlotUtils";
import { getWalletProviderForMethod } from "./dashboardPaymentUtils";

type UnknownRecord = Record<string, unknown>;

export function statusBadgeStyle(status: string) {
  const map = {
    PAYMENT_PENDING: { bg: "rgba(199,146,0,0.22)", border: "rgba(199,146,0,0.45)" },
    PAID_PENDING_PICKUP: { bg: "rgba(27,88,131,0.22)", border: "rgba(27,88,131,0.45)" },
    PICKED_UP: { bg: "rgba(107,107,107,0.22)", border: "rgba(107,107,107,0.45)" },
    EXPIRED: { bg: "rgba(179,38,30,0.20)", border: "rgba(179,38,30,0.45)" },
    EXPIRED_CREDIT_50: { bg: "rgba(179,38,30,0.20)", border: "rgba(179,38,30,0.45)" },
    DISPENSED: { bg: "rgba(95,61,196,0.22)", border: "rgba(95,61,196,0.45)" },
    SEM_PEDIDO: { bg: "rgba(255,255,255,0.08)", border: "rgba(255,255,255,0.18)" },
  };

  const meta =
    map[status as keyof typeof map] || {
      bg: "rgba(255,255,255,0.08)",
      border: "rgba(255,255,255,0.18)",
    };

  return {
    padding: "4px 8px",
    borderRadius: 999,
    border: `1px solid ${meta.border}`,
    background: meta.bg,
    fontSize: 11,
    fontWeight: 700,
  };
}

export function genericBadgeStyle(meta: UnknownRecord | null | undefined) {
  const resolved = meta || {
    bg: "rgba(255,255,255,0.08)",
    border: "rgba(255,255,255,0.18)",
  };

  return {
    padding: "4px 8px",
    borderRadius: 999,
    border: `1px solid ${String(resolved.border)}`,
    background: String(resolved.bg),
    fontSize: 11,
    fontWeight: 700,
    display: "inline-flex" as const,
    alignItems: "center" as const,
    gap: 6,
    whiteSpace: "nowrap" as const,
  };
}

export function softInfoBox(kind: string = "normal") {
  const backgrounds = {
    normal: "rgba(255,255,255,0.04)",
    warning: "rgba(179,38,30,0.18)",
    info: "rgba(27,88,131,0.22)",
  };

  const bgKey = kind in backgrounds ? (kind as keyof typeof backgrounds) : "normal";

  return {
    fontSize: 12,
    opacity: 0.95,
    padding: 9,
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.12)",
    background: backgrounds[bgKey],
  };
}

export function getCurrentOrderMeta(status: string) {
  return (
    ORDER_STATUS_META[status as keyof typeof ORDER_STATUS_META] || ORDER_STATUS_META.SEM_PEDIDO
  );
}

export function getOperationalRowHighlight(item: UnknownRecord | null | undefined) {
  if (!item) {
    return {
      bg: "transparent",
      borderLeft: "4px solid transparent",
    };
  }

  if (item.channel === "KIOSK" && item.status === "DISPENSED") {
    return {
      bg: "linear-gradient(135deg, rgba(95,61,196,0.18), rgba(95,61,196,0.06))",
      borderLeft: "4px solid rgba(95,61,196,0.70)",
    };
  }

  if (item.channel === "ONLINE" && item.status === "PAID_PENDING_PICKUP") {
    return {
      bg: "linear-gradient(135deg, rgba(27,88,131,0.22), rgba(27,88,131,0.08))",
      borderLeft: "4px solid rgba(27,88,131,0.70)",
    };
  }

  if (item.channel === "ONLINE" && item.status === "PICKED_UP") {
    return {
      bg: "linear-gradient(135deg, rgba(31,122,63,0.18), rgba(31,122,63,0.06))",
      borderLeft: "4px solid rgba(31,122,63,0.70)",
    };
  }

  return {
    bg: "transparent",
    borderLeft: "4px solid transparent",
  };
}

export function buildCurrentOrderFromListItem(
  item: UnknownRecord | null | undefined
): UnknownRecord | null {
  if (!item) return null;

  return {
    order_id: item.order_id,
    channel: item.channel,
    status: item.status,
    amount_cents: item.amount_cents,
    payment_method: item.payment_method,
    pickup_id: item.pickup_id,
    pickup_status: item.pickup_status,
    token_id: item.token_id,
    manual_code: item.manual_code,
    paid_at: item.paid_at,
    created_at: item.created_at,
    expires_at: item.expires_at,
    pickup_deadline_at: item.pickup_deadline_at,
    picked_up_at: item.picked_up_at,
    totem_id: item.totem_id,
    allocation: {
      allocation_id: item.allocation_id,
      slot: item.slot,
      state: item.allocation_state,
    },
  };
}

export function tryParseJson(text: unknown): unknown {
  if (!text) return null;
  try {
    return JSON.parse(String(text));
  } catch {
    return null;
  }
}

export function extractBackendDetailFromErrorMessage(message: unknown): unknown {
  if (!message || typeof message !== "string") return null;

  const match = message.match(/payment-confirm HTTP \d+:\s*(.*)$/s);
  if (!match?.[1]) return null;

  return tryParseJson(match[1]);
}

export function extractOperationalErrorType(err: unknown) {
  const rawMessage = String((err as Error)?.message || err || "");
  const parsed = extractBackendDetailFromErrorMessage(rawMessage) as UnknownRecord | null;
  const detail = parsed?.detail as UnknownRecord | undefined;

  if (detail && typeof detail === "object" && detail.type) {
    return detail.type as string;
  }

  return null;
}

export function extractOperationalErrorMessage(err: unknown) {
  const rawMessage = String((err as Error)?.message || err || "");
  const parsed = extractBackendDetailFromErrorMessage(rawMessage) as UnknownRecord | null;
  const detail = parsed?.detail as UnknownRecord | undefined;

  if (detail && typeof detail === "object") {
    if (detail.message) return String(detail.message);
    if (detail.type) return String(detail.type);
  }

  return rawMessage;
}

export function isStaleCurrentOrderErrorType(type: unknown) {
  return (
    typeof type === "string" &&
    [
      "REALLOCATE_CONFLICT",
      "LOCKER_COMMIT_FAILED",
      "COMMIT_AFTER_REALLOCATE_FAILED",
    ].includes(type)
  );
}

export function buildPaymentSummary({
  gatewayData,
  confirmData,
  region,
  currentOrderId,
  lockerId,
}: {
  gatewayData: UnknownRecord;
  confirmData: UnknownRecord;
  region: string;
  currentOrderId?: string;
  lockerId?: string;
}) {
  const lines: string[] = [];

  lines.push("✅ Pagamento confirmado com sucesso");

  if (currentOrderId) lines.push(`Pedido: ${currentOrderId}`);
  if (lockerId) lines.push(`Locker: ${lockerId}`);
  if (confirmData?.slot) lines.push(`Gaveta: ${String(confirmData.slot)}`);
  if (confirmData?.payment_method)
    lines.push(`Método: ${String(confirmData.payment_method)}`);
  if (confirmData?.pickup_id) lines.push(`Pickup: ${String(confirmData.pickup_id)}`);
  if (confirmData?.manual_code)
    lines.push(`Código manual atual: ${String(confirmData.manual_code)}`);

  if (confirmData?.pickup_deadline_at || confirmData?.pickup_expires_at) {
    lines.push(
      `Expira em: ${formatDateTime(
        confirmData?.pickup_expires_at || confirmData?.pickup_deadline_at,
        region
      )}`
    );
  }

  const payment = gatewayData?.payment as UnknownRecord | undefined;
  if (payment?.currency) {
    lines.push(`Moeda: ${String(payment.currency)}`);
  }

  return lines.join("\n");
}

export function buildManualCodeSummary(data: UnknownRecord, region: string) {
  const lines: string[] = [];

  lines.push("✅ Código manual regenerado com sucesso");
  if (data?.order_id) lines.push(`Pedido: ${String(data.order_id)}`);
  if (data?.pickup_id) lines.push(`Pickup: ${String(data.pickup_id)}`);
  if (data?.manual_code) lines.push(`Novo código: ${String(data.manual_code)}`);
  if (data?.expires_at) lines.push(`Expira em: ${formatDateTime(data.expires_at, region)}`);
  lines.push("Códigos anteriores foram invalidados.");

  return lines.join("\n");
}

export function buildRedeemSummary(data: UnknownRecord, region: string, mode = "manual") {
  const lines: string[] = [];

  lines.push(
    mode === "manual"
      ? "✅ Retirada manual concluída com sucesso"
      : "✅ Retirada por QR concluída com sucesso"
  );

  if (data?.order_id) lines.push(`Pedido: ${String(data.order_id)}`);
  if (data?.pickup_id) lines.push(`Pickup: ${String(data.pickup_id)}`);
  if (data?.slot) lines.push(`Gaveta: ${String(data.slot)}`);
  if (data?.locker_id) lines.push(`Locker: ${String(data.locker_id)}`);
  if (data?.expires_at) lines.push(`Janela original: ${formatDateTime(data.expires_at, region)}`);

  return lines.join("\n");
}

export interface FocusOrderSetters {
  setCurrentOrder: (order: UnknownRecord | null) => void;
  setSelectedSlot: (slot: number | null) => void;
  setPaySlot: (slot: number) => void;
  setActiveGroup: (group: number) => void;
  setSlotSelectionExpiresAt: (expires: number | null) => void;
  setOrderError: (message: string) => void;
  setPayResp: (message: string) => void;
  setPickupResp: (message: string) => void;
  setPayMethod: (method: string) => void;
  setPayValue: (value: number) => void;
  setSelectedLockerId: (id: string) => void;
  setWalletProvider: (provider: string) => void;
}

export function focusOrderFromListItem(
  item: UnknownRecord | null | undefined,
  setters: FocusOrderSetters
) {
  const {
    setCurrentOrder,
    setSelectedSlot,
    setPaySlot,
    setActiveGroup,
    setSlotSelectionExpiresAt,
    setOrderError,
    setPayResp,
    setPickupResp,
    setPayMethod,
    setPayValue,
    setSelectedLockerId,
    setWalletProvider,
  } = setters;

  if (item?.payment_method) {
    setPayMethod(String(item.payment_method));
    const wallet = getWalletProviderForMethod(item.payment_method);
    setWalletProvider(wallet || "");
  }

  if (typeof item?.amount_cents === "number") {
    setPayValue(Number(item.amount_cents) / 100);
  }

  if (item?.totem_id) {
    setSelectedLockerId(String(item.totem_id));
  }

  if (item?.slot) {
    const slotNum = Number(item.slot);
    setSelectedSlot(slotNum);
    setPaySlot(slotNum);
    setActiveGroup(groupIndexFromSlot(slotNum));
  }

  setSlotSelectionExpiresAt(null);
  setOrderError("");
  setPayResp("");
  setPickupResp("");
  setCurrentOrder(buildCurrentOrderFromListItem(item));
}

export function getOrderSupportMeta(
  currentOrder: UnknownRecord | CheckoutCurrentOrder | null | undefined
) {
  const row = currentOrder as UnknownRecord | null | undefined;
  const currentOrderMeta = getCurrentOrderMeta(String(row?.status || "SEM_PEDIDO"));

  const pickupKey = row?.pickup_status as keyof typeof PICKUP_STATUS_META | undefined;
  const currentPickupMeta = pickupKey ? PICKUP_STATUS_META[pickupKey] ?? null : null;

  const allocation = row?.allocation as UnknownRecord | undefined;
  const allocState = allocation?.state as keyof typeof ALLOCATION_STATUS_META | undefined;
  const currentAllocationMeta = allocState
    ? ALLOCATION_STATUS_META[allocState] ?? null
    : null;

  const currentOrderWarning =
    row?.status === "EXPIRED" || row?.status === "EXPIRED_CREDIT_50"
      ? "Este pedido expirou. Não tente pagar ou retirar. Crie um novo pedido."
      : row?.status === "PICKED_UP"
        ? "Este pedido já foi retirado. Não tente pagar novamente."
        : null;

  const isOrderAlreadyPaid =
    row?.status === "PAID_PENDING_PICKUP" || row?.status === "PICKED_UP";

  const canRegenerateManualCode =
    row?.status === "PAID_PENDING_PICKUP" && !!row?.order_id;

  return {
    currentOrderMeta,
    currentPickupMeta,
    currentAllocationMeta,
    currentOrderWarning,
    isOrderAlreadyPaid,
    canRegenerateManualCode,
  };
}

export { PICKUP_STATUS_META, ALLOCATION_STATUS_META, CHANNEL_META };

