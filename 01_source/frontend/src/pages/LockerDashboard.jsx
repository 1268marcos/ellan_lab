import React, { useEffect, useMemo, useRef, useState } from "react";
import PickupQRCodePanel from "../components/PickupQRCodePanel.jsx";
import ManualPickupPanel from "../components/ManualPickupPanel.jsx";

/**
 * Estados das gavetas (use os mesmos nomes do backend)
 */
const SLOT_STATES = [
  "AVAILABLE",
  "RESERVED",
  "PAID_PENDING_PICKUP",
  "PICKED_UP",
  "OUT_OF_STOCK",
];

/**
 * Cores por estado da gaveta
 */
const STATE_STYLE = {
  AVAILABLE: { bg: "#1f7a3f", fg: "white", label: "Disponível" },
  RESERVED: { bg: "#c79200", fg: "black", label: "Reservada" },
  PAID_PENDING_PICKUP: { bg: "#1b5883", fg: "white", label: "Pago (aguardando)" },
  PICKED_UP: { bg: "#6b6b6b", fg: "white", label: "Retirado" },
  OUT_OF_STOCK: { bg: "#b3261e", fg: "white", label: "Indisponível" },
};

const ORDER_STATUS_META = {
  PAYMENT_PENDING: {
    label: "Pagamento pendente",
    tone: "warning",
    bg: "linear-gradient(135deg, rgba(199,146,0,0.22), rgba(199,146,0,0.10))",
    border: "rgba(199,146,0,0.42)",
  },
  PAID_PENDING_PICKUP: {
    label: "Pago / aguardando retirada",
    tone: "info",
    bg: "linear-gradient(135deg, rgba(27,88,131,0.28), rgba(27,88,131,0.12))",
    border: "rgba(27,88,131,0.45)",
  },
  PICKED_UP: {
    label: "Retirado",
    tone: "neutral",
    bg: "linear-gradient(135deg, rgba(107,107,107,0.24), rgba(107,107,107,0.10))",
    border: "rgba(107,107,107,0.40)",
  },
  EXPIRED: {
    label: "Expirado",
    tone: "danger",
    bg: "linear-gradient(135deg, rgba(179,38,30,0.26), rgba(179,38,30,0.12))",
    border: "rgba(179,38,30,0.42)",
  },
  EXPIRED_CREDIT_50: {
    label: "Expirado / crédito 50%",
    tone: "danger",
    bg: "linear-gradient(135deg, rgba(179,38,30,0.26), rgba(179,38,30,0.12))",
    border: "rgba(179,38,30,0.42)",
  },
  SEM_PEDIDO: {
    label: "Sem pedido",
    tone: "neutral",
    bg: "linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))",
    border: "rgba(255,255,255,0.14)",
  },
};

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

function groupIndexFromSlot(slot) {
  return Math.floor((slot - 1) / 4);
}

function groupSlots(groupIdx) {
  const start = groupIdx * 4 + 1;
  return [start, start + 1, start + 2, start + 3];
}

function slotsListToMap(list) {
  const out = {};
  for (let i = 1; i <= 24; i++) {
    out[i] = { slot: i, state: "AVAILABLE", product_id: null, updated_at: null };
  }
  for (const item of list || []) {
    const s = Number(item.slot);
    if (s >= 1 && s <= 24) {
      out[s] = {
        slot: s,
        state: item.state || "AVAILABLE",
        product_id: item.product_id ?? null,
        updated_at: item.updated_at ?? null,
      };
    }
  }
  return out;
}

function buildInitialCakes() {
  const cakes = {};
  for (let i = 1; i <= 24; i++) {
    cakes[i] = { name: "", notes: "", imageUrl: "" };
  }
  return cakes;
}

function getOrCreateDeviceFingerprint() {
  const key = "ellan_device_fp_v1";
  let fp = localStorage.getItem(key);
  if (!fp) {
    fp = crypto.randomUUID();
    localStorage.setItem(key, fp);
  }
  return fp;
}

function generateIdempotencyKey() {
  return crypto.randomUUID();
}

function generateClientTransactionId() {
  return `txn_${crypto.randomUUID()}`;
}

function buildTotemId(region) {
  return region === "SP" ? "CACIFO-SP-001" : "CACIFO-PT-001";
}

function buildDefaultSkuId(region, slot) {
  return region === "SP" ? `BOLO_SLOT_${slot}_SP` : `BOLO_SLOT_${slot}_PT`;
}

function pickGatewayTransactionId(respObj) {
  if (!respObj || typeof respObj !== "object") return generateClientTransactionId();

  return (
    respObj.transaction_id ||
    respObj.sale_id ||
    respObj.payment_id ||
    respObj.id ||
    respObj.request_id ||
    generateClientTransactionId()
  );
}

function formatMoney(cents) {
  const value = Number(cents);
  if (!Number.isFinite(value)) return "-";
  return (value / 100).toFixed(2);
}

function regionTimeZone(region) {
  return region === "SP" ? "America/Sao_Paulo" : "Europe/Lisbon";
}

function formatDateTime(value, region = "PT") {
  if (!value) return "-";

  try {
    const raw = String(value).trim();

    // Se veio sem timezone explícito, tratar como UTC
    const normalized =
      /(?:Z|[+-]\d{2}:\d{2})$/.test(raw)
        ? raw
        : `${raw}Z`;

    const dt = new Date(normalized);

    if (Number.isNaN(dt.getTime())) {
      return String(value);
    }

    return dt.toLocaleString("pt-BR", {
      timeZone: regionTimeZone(region),
      hour12: false,
    });
  } catch {
    return String(value);
  }
}

function useMediaQuery(query) {
  const getMatches = () =>
    typeof window !== "undefined" ? window.matchMedia(query).matches : false;

  const [matches, setMatches] = useState(getMatches);

  useEffect(() => {
    const media = window.matchMedia(query);
    const listener = () => setMatches(media.matches);
    listener();
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, [query]);

  return matches;
}

function statusBadgeStyle(status) {
  const map = {
    PAYMENT_PENDING: { bg: "rgba(199,146,0,0.22)", border: "rgba(199,146,0,0.45)" },
    PAID_PENDING_PICKUP: { bg: "rgba(27,88,131,0.22)", border: "rgba(27,88,131,0.45)" },
    PICKED_UP: { bg: "rgba(107,107,107,0.22)", border: "rgba(107,107,107,0.45)" },
    EXPIRED: { bg: "rgba(179,38,30,0.20)", border: "rgba(179,38,30,0.45)" },
    EXPIRED_CREDIT_50: { bg: "rgba(179,38,30,0.20)", border: "rgba(179,38,30,0.45)" },
    SEM_PEDIDO: { bg: "rgba(255,255,255,0.08)", border: "rgba(255,255,255,0.18)" },
  };
  const m = map[status] || { bg: "rgba(255,255,255,0.08)", border: "rgba(255,255,255,0.18)" };
  return {
    padding: "4px 8px",
    borderRadius: 999,
    border: `1px solid ${m.border}`,
    background: m.bg,
    fontSize: 11,
    fontWeight: 700,
  };
}

function softInfoBox(kind = "normal") {
  const backgrounds = {
    normal: "rgba(255,255,255,0.04)",
    warning: "rgba(179,38,30,0.18)",
    info: "rgba(27,88,131,0.22)",
  };

  return {
    fontSize: 12,
    opacity: 0.95,
    padding: 9,
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.12)",
    background: backgrounds[kind] || backgrounds.normal,
  };
}

function getCurrentOrderMeta(status) {
  return ORDER_STATUS_META[status] || ORDER_STATUS_META.SEM_PEDIDO;
}

function buildCurrentOrderFromListItem(item) {
  if (!item) return null;

  return {
    order_id: item.order_id,
    channel: item.channel,
    status: item.status,
    amount_cents: item.amount_cents,
    payment_method: item.payment_method,
    pickup_id: item.pickup_id,
    token_id: item.token_id,
    manual_code: item.manual_code,
    paid_at: item.paid_at,
    created_at: item.created_at,
    expires_at: item.expires_at,
    pickup_deadline_at: item.pickup_deadline_at,
    picked_up_at: item.picked_up_at,
    allocation: {
      allocation_id: item.allocation_id,
      slot: item.slot,
    },
  };
}

function focusOrderFromListItem(item, setters) {
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
  } = setters;

  if (item?.payment_method) {
    setPayMethod(item.payment_method);
  }

  if (typeof item?.amount_cents === "number") {
    setPayValue(Number(item.amount_cents) / 100);
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

function SlotCard({ slot, state, selected, onClick }) {
  const st = STATE_STYLE[state] || { bg: "#333", fg: "white", label: state };

  return (
    <button
      onClick={onClick}
      title={`Gaveta ${slot} • ${st.label}`}
      style={{
        width: "100%",
        aspectRatio: "3 / 2",
        borderRadius: 10,
        border: selected ? "3px solid #fff" : "1px solid rgba(255,255,255,0.2)",
        background: st.bg,
        color: st.fg,
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: 10,
        boxShadow: selected ? "0 0 0 3px rgba(0,0,0,0.25)" : "none",
      }}
    >
      <div style={{ fontSize: 16, fontWeight: 800 }}>{slot}</div>
      <div style={{ fontSize: 11, opacity: 0.9, textAlign: "right" }}>{st.label}</div>
    </button>
  );
}

function Carousel({ pages, activeIndex, onPrev, onNext, onGo }) {
  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button onClick={onPrev} style={btnSmall}>
          ◀
        </button>
        <div style={{ fontWeight: 700 }}>
          Grupo {activeIndex + 1} / {pages}
        </div>
        <button onClick={onNext} style={btnSmall}>
          ▶
        </button>
      </div>

      <div style={{ display: "flex", gap: 6, justifyContent: "center" }}>
        {Array.from({ length: pages }).map((_, i) => (
          <button
            key={i}
            onClick={() => onGo(i)}
            style={{
              width: 10,
              height: 10,
              borderRadius: 999,
              border: "none",
              cursor: "pointer",
              background: i === activeIndex ? "white" : "rgba(255,255,255,0.35)",
            }}
            aria-label={`Ir para grupo ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8 }}>
      <div style={{ opacity: 0.7 }}>{label}:</div>
      <div style={{ fontWeight: 600, wordBreak: "break-all" }}>{value}</div>
    </div>
  );
}

function OrdersCardList({
  ordersData,
  ordersLoading,
  currentOrder,
  onSelectOrder,
}) {
  if (ordersLoading) {
    return <div style={{ fontSize: 12, opacity: 0.75 }}>Carregando pedidos...</div>;
  }

  if (!ordersData.length) {
    return <div style={{ fontSize: 12, opacity: 0.75 }}>Nenhum pedido encontrado.</div>;
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {ordersData.map((item) => (
        <button
          key={item.order_id}
          onClick={() => onSelectOrder(item)}
          style={{
            textAlign: "left",
            padding: 10,
            borderRadius: 12,
            border:
              currentOrder?.order_id === item.order_id
                ? "1px solid rgba(255,255,255,0.38)"
                : "1px solid rgba(255,255,255,0.12)",
            background:
              currentOrder?.order_id === item.order_id
                ? "rgba(27,88,131,0.28)"
                : "rgba(255,255,255,0.03)",
            color: "white",
            cursor: "pointer",
            display: "grid",
            gap: 6,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
            <div style={{ fontWeight: 700 }}>{item.order_id}</div>
            <span style={statusBadgeStyle(item.status)}>{item.status}</span>
          </div>

          <div style={{ fontSize: 12, opacity: 0.85 }}>
            Slot: <b>{item.slot ?? "-"}</b> • Valor: <b>{formatMoney(item.amount_cents)}</b>
          </div>

          <div style={{ fontSize: 12, opacity: 0.72 }}>
            Método: <b>{item.payment_method || "-"}</b> • Pickup: <b>{item.pickup_id || "-"}</b>
          </div>

          <div style={{ fontSize: 11, opacity: 0.62 }}>
            Criado: {formatDateTime(item.created_at, item.region)}
          </div>

          <div style={{ fontSize: 11, opacity: 0.62 }}>
            Pago: {formatDateTime(item.paid_at, item.region)} • Retirado: {formatDateTime(item.picked_up_at, item.region)}
          </div>

          <div style={{ fontSize: 11, opacity: 0.62 }}>
            Expira em: {formatDateTime(item.expires_at || item.pickup_deadline_at, item.region)}
          </div>
        </button>
      ))}
    </div>
  );
}

const btnSmall = {
  padding: "7px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.2)",
  background: "rgba(255,255,255,0.08)",
  color: "white",
  cursor: "pointer",
};

export default function LockerDashboard({ region = "PT" }) {
  const BACKEND_SP = import.meta.env.VITE_BACKEND_SP_BASE_URL || "http://localhost:8201";
  const BACKEND_PT = import.meta.env.VITE_BACKEND_PT_BASE_URL || "http://localhost:8202";
  const backendBase = region === "SP" ? BACKEND_SP : BACKEND_PT;

  const GATEWAY_BASE = import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";
  const gatewayUrl = useMemo(() => `${GATEWAY_BASE}/gateway/pagamento`, [GATEWAY_BASE]);

  const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
  const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";

  const isNarrow = useMediaQuery("(max-width: 1280px)");
  const isVeryNarrow = useMediaQuery("(max-width: 980px)");

  const [slots, setSlots] = useState(() => slotsListToMap([]));
  const [cakes, setCakes] = useState(() => buildInitialCakes());

  const [selectedSlot, setSelectedSlot] = useState(null);
  const [activeGroup, setActiveGroup] = useState(0);
  const [slotSelectionExpiresAt, setSlotSelectionExpiresAt] = useState(null);
  const [slotSelectionTick, setSlotSelectionTick] = useState(0);
  const [showCakesPanel, setShowCakesPanel] = useState(false);

  const slotSelectionRemainingSec = slotSelectionExpiresAt
    ? Math.max(0, Math.ceil((slotSelectionExpiresAt - Date.now()) / 1000))
    : 0;

  const [syncEnabled, setSyncEnabled] = useState(true);
  const [syncStatus, setSyncStatus] = useState({ ok: true, msg: "—" });
  const pollTimerRef = useRef(null);
  const abortRef = useRef(null);

  const [orderLoading, setOrderLoading] = useState(false);
  const [orderError, setOrderError] = useState("");
  const [currentOrder, setCurrentOrder] = useState(null);

  const [payMethod, setPayMethod] = useState("PIX");
  const [payValue, setPayValue] = useState(100);
  const [paySlot, setPaySlot] = useState(1);
  const [payResp, setPayResp] = useState("");
  const [payLoading, setPayLoading] = useState(false);

  const [pickupResp, setPickupResp] = useState("");
  const [regenCodeLoading, setRegenCodeLoading] = useState(false);

  const [ordersLoading, setOrdersLoading] = useState(false);
  const [ordersError, setOrdersError] = useState("");
  const [ordersFilterStatus, setOrdersFilterStatus] = useState("");
  const [ordersData, setOrdersData] = useState([]);
  const [showOrdersPanel, setShowOrdersPanel] = useState(true);
  const [ordersPage, setOrdersPage] = useState(1);
  const [ordersPageSize, setOrdersPageSize] = useState(10);
  const [ordersTotal, setOrdersTotal] = useState(0);
  const [ordersHasNext, setOrdersHasNext] = useState(false);
  const [ordersHasPrev, setOrdersHasPrev] = useState(false);
  const [ordersTableDensity, setOrdersTableDensity] = useState("10");

  const currentOrderMeta = getCurrentOrderMeta(currentOrder?.status || "SEM_PEDIDO");

  const isOrderAlreadyPaid =
    currentOrder?.status === "PAID_PENDING_PICKUP" || currentOrder?.status === "PICKED_UP";

  const canRegenerateManualCode =
    currentOrder?.status === "PAID_PENDING_PICKUP" && !!currentOrder?.order_id;

  const hasActiveSlotSelection =
    !!selectedSlot &&
    !currentOrder &&
    !!slotSelectionExpiresAt &&
    slotSelectionRemainingSec > 0;

  const selectedSlotState = selectedSlot ? slots[selectedSlot]?.state || "AVAILABLE" : null;

  const groupSlotsList = useMemo(() => groupSlots(activeGroup), [activeGroup]);

  const totalOrdersPages = Math.max(1, Math.ceil(ordersTotal / ordersPageSize));
  const visibleOrdersFrom = ordersTotal === 0 ? 0 : (ordersPage - 1) * ordersPageSize + 1;
  const visibleOrdersTo = Math.min(ordersPage * ordersPageSize, ordersTotal);
  const ordersTableHeight =
    ordersTableDensity === "3"
      ? 3 * 44 + 44
      : 10 * 44 + 44;

  useEffect(() => {
    setPaySlot(selectedSlot || 1);
  }, [selectedSlot]);

  useEffect(() => {
    if (isNarrow) {
      setShowCakesPanel(false);
    }
  }, [isNarrow]);

  function selectSlot(slot) {
    setSelectedSlot(slot);
    setActiveGroup(groupIndexFromSlot(slot));
    setCurrentOrder(null);
    setOrderError("");
    setPayResp("");
    setPickupResp("");
    setSlotSelectionExpiresAt(Date.now() + 45_000);
  }

  function updateCake(slot, patch) {
    setCakes((prev) => ({ ...prev, [slot]: { ...prev[slot], ...patch } }));
  }

  function handleSelectOrder(item) {
    focusOrderFromListItem(item, {
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
    });
  }

  async function fetchSlotsOnce() {
    if (abortRef.current) abortRef.current.abort();
    const ac = new AbortController();
    abortRef.current = ac;

    try {
      const res = await fetch(`${backendBase}/locker/slots`, { signal: ac.signal });
      if (!res.ok) {
        const text = await res.text();
        setSyncStatus({ ok: false, msg: `HTTP ${res.status}: ${text}` });
        return;
      }
      const data = await res.json();
      setSlots(slotsListToMap(data));
      setSyncStatus({ ok: true, msg: `Atualizado ${new Date().toLocaleTimeString()}` });
    } catch (e) {
      if (String(e?.name) === "AbortError") return;
      setSyncStatus({ ok: false, msg: String(e?.message || e) });
    }
  }

  async function fetchOrdersOnce(targetPage = ordersPage, targetPageSize = ordersPageSize) {
    setOrdersLoading(true);
    setOrdersError("");

    try {
      const params = new URLSearchParams();
      params.set("region", region);
      params.set("page", String(targetPage));
      params.set("page_size", String(targetPageSize));
      if (ordersFilterStatus) params.set("status", ordersFilterStatus);

      const res = await fetch(`${ORDER_PICKUP_BASE}/orders?${params.toString()}`);
      const text = await res.text();

      if (!res.ok) {
        setOrdersError(`HTTP ${res.status}: ${text}`);
        return;
      }

      const data = JSON.parse(text);

      const items = Array.isArray(data?.items) ? data.items : [];
      const total = Number(data?.total ?? items.length);
      const resolvedPage = Number(data?.page ?? targetPage);
      const resolvedPageSize = Number(data?.page_size ?? targetPageSize);

      const resolvedHasPrev =
        typeof data?.has_prev === "boolean"
          ? data.has_prev
          : resolvedPage > 1;

      const resolvedHasNext =
        typeof data?.has_next === "boolean"
          ? data.has_next
          : resolvedPage * resolvedPageSize < total;

      setOrdersData(items);
      setOrdersTotal(total);
      setOrdersHasNext(resolvedHasNext);
      setOrdersHasPrev(resolvedHasPrev);
      setOrdersPage(resolvedPage);
      setOrdersPageSize(resolvedPageSize);
    } catch (e) {
      setOrdersError(String(e?.message || e));
    } finally {
      setOrdersLoading(false);
    }
  }

  useEffect(() => {
    fetchSlotsOnce();

    if (pollTimerRef.current) clearInterval(pollTimerRef.current);

    if (syncEnabled) {
      pollTimerRef.current = setInterval(() => {
        fetchSlotsOnce();
      }, 3000);
    }

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendBase, syncEnabled]);

  useEffect(() => {
    fetchOrdersOnce(1, ordersPageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [region]);

  useEffect(() => {
    fetchOrdersOnce(1, ordersPageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ordersFilterStatus]);

  useEffect(() => {
    setSelectedSlot(null);
    setActiveGroup(0);
    setPaySlot(1);
    setCurrentOrder(null);
    setOrderError("");
    setPayResp("");
    setPickupResp("");
    setSlotSelectionExpiresAt(null);
    setOrdersPage(1);
  }, [region]);

  useEffect(() => {
    const t = setInterval(() => {
      setSlotSelectionTick((x) => x + 1);
    }, 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!slotSelectionExpiresAt) return;
    if (Date.now() < slotSelectionExpiresAt) return;

    setSelectedSlot(null);
    setPaySlot(1);
    setSlotSelectionExpiresAt(null);
  }, [slotSelectionExpiresAt, slotSelectionTick]);

  async function setStateOnBackend(slot, nextState) {
    const payload = { state: nextState, product_id: slots[slot]?.product_id ?? null };

    setSlots((prev) => ({
      ...prev,
      [slot]: { ...prev[slot], state: nextState },
    }));

    try {
      const res = await fetch(`${backendBase}/locker/slots/${slot}/set-state`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const text = await res.text();
      if (!res.ok) {
        setSyncStatus({ ok: false, msg: `set-state falhou HTTP ${res.status}: ${text}` });
        await fetchSlotsOnce();
        return;
      }

      setSyncStatus({ ok: true, msg: `set-state OK (${slot} → ${nextState})` });

      if (nextState === "PICKED_UP" || nextState === "PAID_PENDING_PICKUP") {
        fetchOrdersOnce(ordersPage, ordersPageSize);
      }
    } catch (e) {
      setSyncStatus({ ok: false, msg: `set-state erro: ${String(e?.message || e)}` });
      await fetchSlotsOnce();
    }
  }

  async function createOnlineOrder() {
    if (!selectedSlot) {
      setOrderError("Selecione uma gaveta antes de criar o pedido.");
      return;
    }

    if (slotSelectionRemainingSec <= 0) {
      setOrderError("A seleção da gaveta expirou. Escolha novamente.");
      return;
    }

    const slotNum = Number(selectedSlot);
    const skuId = buildDefaultSkuId(region, slotNum);
    const totemId = buildTotemId(region);

    setOrderLoading(true);
    setOrderError("");
    setPayResp("");
    setPickupResp("");

    try {
      const res = await fetch(`${ORDER_PICKUP_BASE}/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region,
          sku_id: skuId,
          totem_id: totemId,
          desired_slot: slotNum,
          amount_cents: Math.round(Number(payValue) * 100),
        }),
      });

      const text = await res.text();
      if (!res.ok) {
        setOrderError(`HTTP ${res.status}: ${text}`);
        return;
      }

      const data = JSON.parse(text);
      setCurrentOrder(data);
      setSlotSelectionExpiresAt(null);

      if (data?.allocation?.slot) {
        const allocatedSlot = Number(data.allocation.slot);
        setSelectedSlot(allocatedSlot);
        setPaySlot(allocatedSlot);
        setActiveGroup(groupIndexFromSlot(allocatedSlot));
      }

      if (typeof data?.amount_cents === "number") {
        setPayValue(Number(data.amount_cents) / 100);
      }

      if (data?.payment_method) {
        setPayMethod(data.payment_method);
      }

      setPayResp(JSON.stringify({ step: "order_created", response: data }, null, 2));
      fetchOrdersOnce(1, ordersPageSize);
    } catch (e) {
      setOrderError(String(e?.message || e));
    } finally {
      setOrderLoading(false);
    }
  }

  async function confirmPaymentInternally(orderId, transactionId) {
    if (!INTERNAL_TOKEN) {
      throw new Error("VITE_INTERNAL_TOKEN não configurado no frontend.");
    }

    if (!currentOrder) {
      throw new Error("Nenhum pedido atual carregado para confirmação interna.");
    }

    const totemId = buildTotemId(region);
    const amountCents =
      typeof currentOrder.amount_cents === "number"
        ? currentOrder.amount_cents
        : Math.round(Number(payValue) * 100);

    const payload = {
      order_id: orderId,
      region,
      totem_id: totemId,
      channel: "ONLINE",
      provider: payMethod,
      transaction_id: transactionId,
      amount_cents: amountCents,
    };

    const res = await fetch(
      `${ORDER_PICKUP_BASE}/internal/orders/${encodeURIComponent(orderId)}/payment-confirm`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Internal-Token": INTERNAL_TOKEN,
        },
        body: JSON.stringify(payload),
      }
    );

    const text = await res.text();
    if (!res.ok) {
      throw new Error(`payment-confirm HTTP ${res.status}: ${text}`);
    }

    return JSON.parse(text);
  }

  async function regenerateManualCode() {
    if (!currentOrder?.order_id) {
      setPickupResp("❌ Nenhum pedido selecionado para regenerar código.");
      return;
    }

    if (currentOrder?.status !== "PAID_PENDING_PICKUP") {
      setPickupResp("❌ Só é possível regenerar código para pedido em PAID_PENDING_PICKUP.");
      return;
    }

    setRegenCodeLoading(true);

    try {
      const res = await fetch(
        `${ORDER_PICKUP_BASE}/orders/${encodeURIComponent(currentOrder.order_id)}/pickup-token`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        }
      );

      const text = await res.text();
      if (!res.ok) {
        setPickupResp(`❌ Falha ao regenerar código manual\nHTTP ${res.status}: ${text}`);
        return;
      }

      const data = JSON.parse(text);

      setCurrentOrder((prev) =>
        prev
          ? {
              ...prev,
              manual_code: data?.manual_code || prev.manual_code,
              pickup_id: data?.pickup_id || prev.pickup_id,
              token_id: data?.token_id || prev.token_id,
              expires_at: data?.expires_at || prev.expires_at,
              pickup_deadline_at: data?.expires_at || prev.pickup_deadline_at,
            }
          : prev
      );

      setPickupResp(
        JSON.stringify(
          {
            step: "manual_code_regenerated",
            response: data,
            security_note: "Códigos anteriores foram invalidados; use somente o código recém-gerado.",
          },
          null,
          2
        )
      );
      fetchOrdersOnce(ordersPage, ordersPageSize);
    } catch (e) {
      setPickupResp(`❌ Erro ao regenerar código manual\n${String(e?.message || e)}`);
    } finally {
      setRegenCodeLoading(false);
    }
  }

  async function simulatePayment() {
    if (!currentOrder?.order_id) {
      setPayResp("❌ Antes de pagar, clique em “Criar pedido online”.");
      return;
    }

    if (currentOrder?.status === "PAID_PENDING_PICKUP") {
      setPayResp("⚠️ Pedido já pago. Use “Gerar/Atualizar” ou “Regenerar código manual”.");
      return;
    }

    if (currentOrder?.status === "PICKED_UP") {
      setPayResp("⚠️ Pedido já retirado. Não é possível pagar novamente.");
      return;
    }

    const slotNum = Number(currentOrder?.allocation?.slot || paySlot);
    const orderAmountCents =
      typeof currentOrder?.amount_cents === "number"
        ? currentOrder.amount_cents
        : Math.round(Number(payValue) * 100);

    const valNum = Number(orderAmountCents) / 100;

    if (!slotNum || slotNum < 1 || slotNum > 24) {
      setPayResp("❌ Gaveta inválida (1..24)");
      return;
    }
    if (!Number.isFinite(valNum) || valNum <= 0) {
      setPayResp("❌ Valor inválido (>0)");
      return;
    }

    const deviceFp = getOrCreateDeviceFingerprint();
    const idemKey = generateIdempotencyKey();

    setPayLoading(true);
    setPayResp("");

    try {
      const gatewayRes = await fetch(gatewayUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idemKey,
          "X-Device-Fingerprint": deviceFp,
        },
        body: JSON.stringify({
          regiao: region,
          metodo: payMethod,
          valor: valNum,
          porta: slotNum,
        }),
      });

      const gatewayText = await gatewayRes.text();
      if (!gatewayRes.ok) {
        setPayResp(`❌ Gateway HTTP ${gatewayRes.status}\n${gatewayText}\n\nURL: ${gatewayUrl}`);
        return;
      }

      let gatewayData;
      try {
        gatewayData = JSON.parse(gatewayText);
      } catch {
        gatewayData = { raw: gatewayText };
      }

      const transactionId = pickGatewayTransactionId(gatewayData);
      const confirmData = await confirmPaymentInternally(currentOrder.order_id, transactionId);

      setCurrentOrder((prev) =>
        prev
          ? {
              ...prev,
              status: confirmData?.status || prev.status,
              payment_method: confirmData?.payment_method || prev.payment_method,
              picked_up_at: confirmData?.picked_up_at || prev.picked_up_at,
              pickup_id: confirmData?.pickup_id || prev.pickup_id,
              token_id: confirmData?.token_id || prev.token_id,
              manual_code: confirmData?.manual_code || prev.manual_code,
              expires_at: confirmData?.pickup_deadline_at || prev.expires_at,
              pickup_deadline_at: confirmData?.pickup_deadline_at || prev.pickup_deadline_at,
            }
          : prev
      );

      setPayResp(
        JSON.stringify(
          {
            step: "payment_confirmed",
            order_id: currentOrder.order_id,
            gateway_response: gatewayData,
            payment_confirm_response: confirmData,
          },
          null,
          2
        )
      );

      await fetchSlotsOnce();
      await fetchOrdersOnce(ordersPage, ordersPageSize);
    } catch (e) {
      setPayResp(`❌ Falha no fluxo de pagamento\n${String(e?.message || e)}`);
    } finally {
      setPayLoading(false);
    }
  }

  function handleManualRedeemed(data) {
    if (data?.slot) {
      setSelectedSlot(Number(data.slot));
      setActiveGroup(groupIndexFromSlot(Number(data.slot)));
    }

    setCurrentOrder(null);
    setSlotSelectionExpiresAt(null);
    setPickupResp(
      JSON.stringify(
        {
          step: "manual_redeem_success",
          response: data,
        },
        null,
        2
      )
    );

    fetchSlotsOnce();
    fetchOrdersOnce(ordersPage, ordersPageSize);
  }

  const legendItems = Object.entries(STATE_STYLE);

  return (
    <div style={{ minHeight: "100vh", background: "#0f1115", color: "white", padding: 16, fontFamily: "system-ui" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>ELLAN • Locker Dashboard</h1>

        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ opacity: 0.8, fontSize: 12 }}>
            Região: <b>{region}</b> • Backend: <code>{backendBase}</code>
          </div>

          <button
            onClick={() => {
              fetchSlotsOnce();
              fetchOrdersOnce(ordersPage, ordersPageSize);
            }}
            style={btnSmall}
          >
            Atualizar tudo
          </button>

          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, opacity: 0.9 }}>
            <input type="checkbox" checked={syncEnabled} onChange={(e) => setSyncEnabled(e.target.checked)} />
            Polling gavetas (3s)
          </label>

          <div style={{ fontSize: 12, opacity: syncStatus.ok ? 0.75 : 1, color: syncStatus.ok ? "white" : "#ffb4b4" }}>
            {syncStatus.ok ? "✅" : "⚠️"} {syncStatus.msg}
          </div>
        </div>
      </div>

      <div
        style={{
          marginTop: 12,
          display: "grid",
          gridTemplateColumns: isVeryNarrow ? "1fr" : "1.2fr 0.95fr",
          gap: 12,
          alignItems: "start",
        }}
      >
        {/* COLUNA ESQUERDA */}
        <div style={{ display: "grid", gap: 12 }}>
          <section style={panelStyleCompact}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <div style={{ fontWeight: 800 }}>Gavetas (1–24)</div>
              <div style={{ fontSize: 12, opacity: 0.75 }}>
                Selecionada: <b>{selectedSlot ?? "—"}</b>
                {selectedSlot ? (
                  <>
                    {" "}• Estado: <b>{STATE_STYLE[selectedSlotState]?.label || selectedSlotState || "-"}</b>
                  </>
                ) : null}
              </div>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
              {legendItems.map(([key, meta]) => (
                <div
                  key={key}
                  style={{
                    display: "flex",
                    gap: 6,
                    alignItems: "center",
                    padding: "5px 8px",
                    borderRadius: 999,
                    border: "1px solid rgba(255,255,255,0.14)",
                    background: "rgba(0,0,0,0.18)",
                    fontSize: 11,
                  }}
                >
                  <span style={{ width: 10, height: 10, borderRadius: 999, background: meta.bg, display: "inline-block" }} />
                  <span style={{ opacity: 0.9 }}>{meta.label}</span>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 10, display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
              {Array.from({ length: 24 }).map((_, idx) => {
                const slot = idx + 1;
                const st = slots[slot]?.state || "AVAILABLE";
                return (
                  <SlotCard
                    key={slot}
                    slot={slot}
                    state={st}
                    selected={slot === selectedSlot}
                    onClick={() => selectSlot(slot)}
                  />
                );
              })}
            </div>

            <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <div style={{ fontSize: 12, opacity: 0.8 }}>
                Alterar estado da gaveta {selectedSlot ?? "—"}:
              </div>
              {SLOT_STATES.map((s) => (
                <button
                  key={s}
                  onClick={() => selectedSlot && setStateOnBackend(selectedSlot, s)}
                  style={{
                    padding: "7px 10px",
                    borderRadius: 10,
                    border: "1px solid rgba(255,255,255,0.18)",
                    background: "rgba(255,255,255,0.06)",
                    color: "white",
                    cursor: "pointer",
                    fontSize: 12,
                  }}
                >
                  {STATE_STYLE[s]?.label || s}
                </button>
              ))}
            </div>
          </section>

          <section style={panelStyleCompact}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <div style={{ fontWeight: 800 }}>Pedidos online</div>
                <button onClick={() => setShowOrdersPanel((v) => !v)} style={btnSmall}>
                  {showOrdersPanel ? "Ocultar" : "Mostrar"}
                </button>
              </div>

              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <div style={{ fontSize: 12, opacity: 0.75 }}>
                  Região: <b>{region}</b> • Total: <b>{ordersTotal}</b>
                  {showOrdersPanel ? (
                    <>
                      {" "}• Exibindo: <b>{visibleOrdersFrom}-{visibleOrdersTo}</b>
                    </>
                  ) : null}
                </div>

                <select
                  value={ordersFilterStatus}
                  onChange={(e) => setOrdersFilterStatus(e.target.value)}
                  style={{ ...select, width: 190, backgroundColor: "#2d2d3a" }}
                >
                  <option value="">Todos os status</option>
                  <option value="PAYMENT_PENDING">PAYMENT_PENDING</option>
                  <option value="PAID_PENDING_PICKUP">PAID_PENDING_PICKUP</option>
                  <option value="PICKED_UP">PICKED_UP</option>
                  <option value="EXPIRED">EXPIRED</option>
                  <option value="EXPIRED_CREDIT_50">EXPIRED_CREDIT_50</option>
                </select>

                <select
                  value={ordersPageSize}
                  onChange={(e) => {
                    const nextSize = Number(e.target.value);
                    setOrdersPageSize(nextSize);
                    fetchOrdersOnce(1, nextSize);
                  }}
                  style={{ ...select, width: 130, backgroundColor: "#2d2d3a" }}
                >
                  <option value={10}>10 por página</option>
                  <option value={3}>3 por página</option>
                </select>

                <select
                  value={ordersTableDensity}
                  onChange={(e) => setOrdersTableDensity(e.target.value)}
                  style={{ ...select, width: 140, backgroundColor: "#2d2d3a" }}
                >
                  <option value="10">Altura 10 itens</option>
                  <option value="3">Altura 3 itens</option>
                </select>

                <button onClick={() => fetchOrdersOnce(ordersPage, ordersPageSize)} style={btnSmall}>
                  Atualizar pedidos
                </button>
              </div>
            </div>

            {showOrdersPanel ? (
              <>
                {ordersError ? <pre style={errorPre}>{ordersError}</pre> : null}

                {isNarrow ? (
                  <div style={{ marginTop: 10 }}>
                    <OrdersCardList
                      ordersData={ordersData}
                      ordersLoading={ordersLoading}
                      currentOrder={currentOrder}
                      onSelectOrder={handleSelectOrder}
                    />
                  </div>
                ) : (
                  <div
                    style={{
                      marginTop: 10,
                      overflowX: "auto",
                      overflowY: "auto",
                      maxHeight: ordersTableHeight,
                      borderRadius: 10,
                      border: "1px solid rgba(255,255,255,0.10)",
                    }}
                  >
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, minWidth: 1360 }}>
                      <thead>
                        <tr style={{ background: "rgba(255,255,255,0.06)" }}>
                          <th style={thStyle}>Order</th>
                          <th style={thStyle}>Status</th>
                          <th style={thStyle}>Método</th>
                          <th style={thStyle}>Pickup</th>
                          <th style={thStyle}>Slot</th>
                          <th style={thStyle}>Allocation</th>
                          <th style={thStyle}>SKU</th>
                          <th style={thStyle}>Valor</th>
                          <th style={thStyle}>Criado em</th>
                          <th style={thStyle}>Pago em</th>
                          <th style={thStyle}>Retirado em</th>
                          <th style={thStyle}>Expira em</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ordersLoading ? (
                          <tr>
                            <td style={tdStyle} colSpan={12}>
                              Carregando pedidos...
                            </td>
                          </tr>
                        ) : ordersData.length === 0 ? (
                          <tr>
                            <td style={tdStyle} colSpan={12}>
                              Nenhum pedido encontrado.
                            </td>
                          </tr>
                        ) : (
                          ordersData.map((item) => (
                            <tr
                              key={item.order_id}
                              onClick={() => handleSelectOrder(item)}
                              style={{
                                cursor: "pointer",
                                background:
                                  currentOrder?.order_id === item.order_id ? "rgba(27,88,131,0.35)" : "transparent",
                              }}
                            >
                              <td style={tdStyle}>{item.order_id}</td>
                              <td style={tdStyle}>
                                <span style={statusBadgeStyle(item.status)}>{item.status}</span>
                              </td>
                              <td style={tdStyle}>{item.payment_method || "-"}</td>
                              <td style={tdStyle}>{item.pickup_id || "-"}</td>
                              <td style={tdStyle}>{item.slot ?? "-"}</td>
                              <td style={tdStyle}>{item.allocation_id ?? "-"}</td>
                              <td style={tdStyle}>{item.sku_id}</td>
                              <td style={tdStyle}>{formatMoney(item.amount_cents)}</td>
                              <td style={tdStyle}>{formatDateTime(item.created_at, item.region)}</td>
                              <td style={tdStyle}>{formatDateTime(item.paid_at, item.region)}</td>
                              <td style={tdStyle}>{formatDateTime(item.picked_up_at, item.region)}</td>
                              <td style={tdStyle}>{formatDateTime(item.expires_at || item.pickup_deadline_at, item.region)}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                <div
                  style={{
                    marginTop: 10,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 8,
                    flexWrap: "wrap",
                  }}
                >
                  <div style={{ fontSize: 11, opacity: 0.65 }}>
                    Pedidos online não entram no polling automático. Atualize pelo botão.
                  </div>

                  <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                    <button
                      onClick={() => fetchOrdersOnce(Math.max(1, ordersPage - 1), ordersPageSize)}
                      disabled={!ordersHasPrev}
                      style={{
                        ...btnSmall,
                        opacity: !ordersHasPrev ? 0.45 : 1,
                        cursor: !ordersHasPrev ? "not-allowed" : "pointer",
                      }}
                    >
                      Anterior
                    </button>

                    <div style={{ fontSize: 12, opacity: 0.85 }}>
                      Página <b>{ordersPage}</b> de <b>{totalOrdersPages}</b>
                    </div>

                    <button
                      onClick={() => fetchOrdersOnce(ordersPage + 1, ordersPageSize)}
                      disabled={!ordersHasNext}
                      style={{
                        ...btnSmall,
                        opacity: !ordersHasNext ? 0.45 : 1,
                        cursor: !ordersHasNext ? "not-allowed" : "pointer",
                      }}
                    >
                      Próxima
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div style={{ fontSize: 12, opacity: 0.65, marginTop: 4 }}>
                Painel de pedidos oculto para reduzir ruído visual.
              </div>
            )}
          </section>
        </div>

        {/* COLUNA DIREITA */}
        <div style={{ display: "grid", gap: 12 }}>
          <section
            style={{
              ...panelStyleCompact,
              border: `1px solid ${currentOrderMeta.border}`,
              boxShadow: currentOrder ? `0 0 0 1px rgba(255,255,255,0.03), inset 0 0 0 1px rgba(255,255,255,0.04)` : "none",
              background: currentOrderMeta.bg,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <div style={{ fontWeight: 800 }}>Pedido atual</div>
              <span style={statusBadgeStyle(currentOrder?.status || "SEM_PEDIDO")}>
                {currentOrder?.status || "SEM_PEDIDO"}
              </span>
            </div>

            {currentOrder ? (
              <div style={softInfoBox(currentOrderMeta.tone === "danger" ? "warning" : currentOrderMeta.tone === "info" ? "info" : "normal")}>
                <b>{currentOrderMeta.label}</b>
                {currentOrder?.allocation?.slot ? (
                  <> • Gaveta <b>{currentOrder.allocation.slot}</b></>
                ) : null}
                {currentOrder?.payment_method ? (
                  <> • Método <b>{currentOrder.payment_method}</b></>
                ) : null}
                {currentOrder?.pickup_id ? (
                  <> • Pickup <b>{currentOrder.pickup_id}</b></>
                ) : null}
              </div>
            ) : hasActiveSlotSelection ? (
              <div style={softInfoBox(slotSelectionRemainingSec > 10 ? "normal" : "warning")}>
                Gaveta selecionada: <b>{selectedSlot}</b> • tempo restante para criar o pedido:{" "}
                <b>{slotSelectionRemainingSec}s</b>
              </div>
            ) : (
              <div style={{ fontSize: 12, opacity: 0.82 }}>
                Selecione uma gaveta disponível para iniciar a criação do pedido.
              </div>
            )}

            <button
              onClick={createOnlineOrder}
              disabled={orderLoading || payLoading}
              style={{
                ...actionBtnCompact,
                background: orderLoading ? "rgba(255,255,255,0.10)" : "#7a5f1f",
                cursor: orderLoading || payLoading ? "not-allowed" : "pointer",
              }}
            >
              {orderLoading
                ? "Criando pedido..."
                : selectedSlot
                  ? `Criar pedido online — gaveta ${selectedSlot}`
                  : "Criar pedido online"}
            </button>

            {currentOrder ? (
              <div style={infoCardStyleCompact}>
                <InfoRow label="order_id" value={currentOrder.order_id} />
                <InfoRow label="status" value={currentOrder.status} />
                <InfoRow label="pickup_id" value={currentOrder.pickup_id || "-"} />
                <InfoRow label="payment_method" value={currentOrder.payment_method || "-"} />
                <InfoRow label="slot" value={currentOrder?.allocation?.slot ?? "-"} />
                <InfoRow label="allocation_id" value={currentOrder?.allocation?.allocation_id ?? "-"} />
                <InfoRow label="amount_cents" value={currentOrder?.amount_cents ?? "-"} />
                <InfoRow
                  label="expires_at"
                  value={formatDateTime(currentOrder?.expires_at || currentOrder?.pickup_deadline_at, region)}
                />
                <InfoRow
                  label="pickup_deadline_at"
                  value={formatDateTime(currentOrder?.pickup_deadline_at, region)}
                />
                <InfoRow
                  label="picked_up_at"
                  value={formatDateTime(currentOrder?.picked_up_at, region)}
                />
                {currentOrder?.manual_code ? <InfoRow label="manual_code atual" value={currentOrder.manual_code} /> : null}
              </div>
            ) : (
              <div style={{ fontSize: 12, opacity: 0.78 }}>Nenhum pedido criado ou selecionado.</div>
            )}

            {orderError ? <pre style={errorPre}>{orderError}</pre> : null}
          </section>

          <section style={panelStyleCompact}>
            <div style={{ fontWeight: 800 }}>Pagamento do pedido</div>

            <div style={{ fontSize: 12, opacity: 0.72 }}>
              Gateway: <code>{gatewayUrl}</code>
            </div>

            {currentOrder?.status === "PAID_PENDING_PICKUP" ? (
              <div style={softInfoBox("info")}>
                ⚠️ Pedido já pago. Para recuperar o código, use <b>Gerar/Atualizar</b> ou <b>Regenerar código manual</b>.
              </div>
            ) : null}

            <label style={labelCompact}>
              Método
              <select
                value={payMethod}
                onChange={(e) => setPayMethod(e.target.value)}
                style={{ ...selectCompact, backgroundColor: "#2d2d3a" }}
              >
                <option value="PIX">PIX</option>
                <option value="CARTAO">CARTÃO</option>
                <option value="MBWAY">MBWAY</option>
                <option value="NFC">NFC</option>
              </select>
            </label>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <label style={labelCompact}>
                Gaveta
                <input
                  type="number"
                  min="1"
                  max="24"
                  value={paySlot}
                  onChange={(e) => setPaySlot(e.target.value)}
                  style={inputCompact}
                />
              </label>

              <label style={labelCompact}>
                Valor
                <input
                  type="number"
                  min="1"
                  step="0.01"
                  value={payValue}
                  onChange={(e) => setPayValue(e.target.value)}
                  disabled={!!currentOrder?.order_id}
                  style={{
                    ...inputCompact,
                    opacity: currentOrder?.order_id ? 0.7 : 1,
                    cursor: currentOrder?.order_id ? "not-allowed" : "text",
                  }}
                />
              </label>

              {currentOrder?.order_id ? (
                <div style={softInfoBox("normal")}>
                  Valor congelado no pedido atual: <b>{formatMoney(currentOrder.amount_cents)}</b>
                </div>
              ) : null}

            </div>

            <button
              onClick={simulatePayment}
              disabled={payLoading || orderLoading || isOrderAlreadyPaid}
              style={{
                ...actionBtnCompact,
                background:
                  payLoading || orderLoading || isOrderAlreadyPaid
                    ? "rgba(255,255,255,0.08)"
                    : "#2d8a4a",
                cursor:
                  payLoading || orderLoading || isOrderAlreadyPaid
                    ? "not-allowed"
                    : "pointer",
              }}
            >
              {payLoading
                ? "Enviando..."
                : currentOrder?.status === "PAID_PENDING_PICKUP"
                  ? "Pedido já pago"
                  : currentOrder?.status === "PICKED_UP"
                    ? "Pedido já retirado"
                    : "Pagar pedido atual"}
            </button>

            {payResp ? <pre style={resultPreCompact}>{payResp}</pre> : null}
          </section>

          <section style={panelStyleCompact}>
            <div style={{ fontWeight: 800 }}>Retirada do pedido</div>

            <button
              onClick={regenerateManualCode}
              disabled={!canRegenerateManualCode || regenCodeLoading || payLoading || orderLoading}
              style={{
                ...actionBtnCompact,
                background:
                  !canRegenerateManualCode || regenCodeLoading || payLoading || orderLoading
                    ? "rgba(255,255,255,0.08)"
                    : "#5f3dc4",
                cursor:
                  !canRegenerateManualCode || regenCodeLoading || payLoading || orderLoading
                    ? "not-allowed"
                    : "pointer",
              }}
            >
              {regenCodeLoading ? "Regenerando código..." : "Regenerar código manual"}
            </button>

            <PickupQRCodePanel
              region={region}
              pickupId={currentOrder?.pickup_id || ""}
              apiBase={ORDER_PICKUP_BASE}
            />

            <ManualPickupPanel
              region={region}
              apiBase={ORDER_PICKUP_BASE}
              onRedeemed={handleManualRedeemed}
            />

            {pickupResp ? <pre style={resultPreCompact}>{pickupResp}</pre> : null}
          </section>

          <section style={panelStyleCompact}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
              <div style={{ fontWeight: 800 }}>Bolos por grupo</div>
              <button onClick={() => setShowCakesPanel((v) => !v)} style={btnSmall}>
                {showCakesPanel ? "Ocultar" : "Mostrar"}
              </button>
            </div>

            {!showCakesPanel ? (
              <div style={{ fontSize: 12, opacity: 0.65 }}>
                Painel secundário oculto para reduzir ruído visual.
              </div>
            ) : (
              <>
                <Carousel
                  pages={6}
                  activeIndex={activeGroup}
                  onPrev={() => setActiveGroup((g) => (g - 1 + 6) % 6)}
                  onNext={() => setActiveGroup((g) => (g + 1) % 6)}
                  onGo={(i) => setActiveGroup(clamp(i, 0, 5))}
                />

                <div style={{ fontSize: 12, opacity: 0.75 }}>
                  Grupo atual: gavetas <b>{groupSlotsList.join(", ")}</b>
                </div>

                <div style={{ display: "grid", gap: 8 }}>
                  {groupSlotsList.map((slot) => {
                    const st = slots[slot]?.state || "AVAILABLE";
                    const meta = STATE_STYLE[st] || { bg: "#333", fg: "white", label: st };
                    const cake = cakes[slot];

                    return (
                      <div
                        key={slot}
                        style={{
                          borderRadius: 12,
                          border: "1px solid rgba(255,255,255,0.12)",
                          background: "rgba(0,0,0,0.18)",
                          padding: 9,
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <button onClick={() => selectSlot(slot)} style={{ ...btnSmall, padding: "6px 10px", fontWeight: 700 }}>
                            Gaveta {slot}
                          </button>

                          <span
                            style={{
                              padding: "4px 8px",
                              borderRadius: 999,
                              background: meta.bg,
                              color: meta.fg,
                              fontSize: 11,
                              fontWeight: 700,
                            }}
                          >
                            {meta.label}
                          </span>
                        </div>

                        <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
                          <label style={labelCompact}>
                            Nome do bolo
                            <input
                              value={cake?.name || ""}
                              onChange={(e) => updateCake(slot, { name: e.target.value })}
                              placeholder="ex.: Bolo de Cenoura"
                              style={inputCompact}
                            />
                          </label>

                          <label style={labelCompact}>
                            Observações
                            <input
                              value={cake?.notes || ""}
                              onChange={(e) => updateCake(slot, { notes: e.target.value })}
                              placeholder="ex.: sem lactose / promoção / etc."
                              style={inputCompact}
                            />
                          </label>

                          <label style={labelCompact}>
                            URL da imagem (opcional)
                            <input
                              value={cake?.imageUrl || ""}
                              onChange={(e) => updateCake(slot, { imageUrl: e.target.value })}
                              placeholder="https://..."
                              style={inputCompact}
                            />
                          </label>

                          {cake?.imageUrl ? (
                            <img
                              alt={`Bolo da gaveta ${slot}`}
                              src={cake.imageUrl}
                              style={{
                                width: "100%",
                                borderRadius: 10,
                                border: "1px solid rgba(255,255,255,0.12)",
                                marginTop: 4,
                              }}
                            />
                          ) : null}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

const panelStyleCompact = {
  borderRadius: 14,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.04)",
  padding: 12,
  display: "grid",
  gap: 8,
};

const infoCardStyleCompact = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.05)",
  padding: 10,
  display: "grid",
  gap: 5,
  fontSize: 12,
};

const actionBtnCompact = {
  padding: "9px 12px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.18)",
  color: "white",
  fontWeight: 800,
};

const labelCompact = {
  fontSize: 12,
  opacity: 0.9,
  display: "grid",
  gap: 5,
};

const inputCompact = {
  width: "100%",
  padding: "9px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.06)",
  color: "white",
  outline: "none",
};

const selectCompact = {
  width: "100%",
  padding: "9px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.06)",
  color: "white",
  outline: "none",
};

const thStyle = {
  textAlign: "left",
  padding: "10px 8px",
  borderBottom: "1px solid rgba(255,255,255,0.12)",
  whiteSpace: "nowrap",
};

const tdStyle = {
  padding: "10px 8px",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
  verticalAlign: "top",
  whiteSpace: "nowrap",
};

const errorPre = {
  margin: 0,
  padding: 10,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "#2b1d1d",
  color: "#ffb4b4",
  overflow: "auto",
  maxHeight: 160,
  fontSize: 12,
};

const resultPreCompact = {
  margin: 0,
  padding: 10,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "#0b0d10",
  color: "white",
  overflow: "auto",
  maxHeight: 190,
  fontSize: 12,
};

const select = {
  width: "100%",
  padding: "10px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.06)",
  color: "white",
  outline: "none",
};