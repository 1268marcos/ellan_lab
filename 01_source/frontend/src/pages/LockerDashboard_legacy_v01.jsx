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
 * Cores por estado
 */
const STATE_STYLE = {
  AVAILABLE: { bg: "#1f7a3f", fg: "white", label: "Disponível" },
  RESERVED: { bg: "#c79200", fg: "black", label: "Reservada" },
  PAID_PENDING_PICKUP: { bg: "#1b5883", fg: "white", label: "Pago (aguardando)" },
  PICKED_UP: { bg: "#6b6b6b", fg: "white", label: "Retirado" },
  OUT_OF_STOCK: { bg: "#b3261e", fg: "white", label: "Indisponível" },
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
  if (typeof cents !== "number") return "-";
  return (cents / 100).toFixed(2);
}

function formatDateTime(value) {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
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
    <div style={{ display: "grid", gap: 10 }}>
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

const btnSmall = {
  padding: "8px 10px",
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

  const [slots, setSlots] = useState(() => slotsListToMap([]));
  const [cakes, setCakes] = useState(() => buildInitialCakes());

  const [selectedSlot, setSelectedSlot] = useState(null);
  const [activeGroup, setActiveGroup] = useState(0);
  const [slotSelectionExpiresAt, setSlotSelectionExpiresAt] = useState(null);
  const [slotSelectionTick, setSlotSelectionTick] = useState(0);

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

  const isOrderAlreadyPaid =
    currentOrder?.status === "PAID_PENDING_PICKUP" || currentOrder?.status === "PICKED_UP";

  const canRegenerateManualCode =
    currentOrder?.status === "PAID_PENDING_PICKUP" && !!currentOrder?.order_id;

  useEffect(() => {
    setPaySlot(selectedSlot || 1);
  }, [selectedSlot]);

  const groupSlotsList = useMemo(() => groupSlots(activeGroup), [activeGroup]);

  function selectSlot(slot) {
    setSelectedSlot(slot);
    setActiveGroup(groupIndexFromSlot(slot));
    setSlotSelectionExpiresAt(Date.now() + 45_000);
  }

  function updateCake(slot, patch) {
    setCakes((prev) => ({ ...prev, [slot]: { ...prev[slot], ...patch } }));
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

  async function fetchOrdersOnce() {
    setOrdersLoading(true);
    setOrdersError("");

    try {
      const params = new URLSearchParams();
      params.set("region", region);
      params.set("limit", "50");
      if (ordersFilterStatus) params.set("status", ordersFilterStatus);

      const res = await fetch(`${ORDER_PICKUP_BASE}/orders?${params.toString()}`);
      const text = await res.text();

      if (!res.ok) {
        setOrdersError(`HTTP ${res.status}: ${text}`);
        return;
      }

      const data = JSON.parse(text);
      setOrdersData(Array.isArray(data?.items) ? data.items : []);
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
    fetchOrdersOnce();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [region]);

  useEffect(() => {
    // quando mudar apenas o filtro, atualiza a lista sob demanda local
    fetchOrdersOnce();
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

      // Se a mudança de estado afeta pedidos (ex: PICKED_UP), recarregue
      if (nextState === "PICKED_UP" || nextState === "PAID_PENDING_PICKUP") {
        fetchOrdersOnce(); // <-- ADICIONAR AQUI
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
        }),
      });

      const text = await res.text();
      if (!res.ok) {
        setOrderError(`HTTP ${res.status}: ${text}`);
        return;
      }

      const data = JSON.parse(text);
      setCurrentOrder(data);

      if (data?.allocation?.slot) {
        const allocatedSlot = Number(data.allocation.slot);
        setSelectedSlot(allocatedSlot);
        setPaySlot(allocatedSlot);
        setActiveGroup(groupIndexFromSlot(allocatedSlot));
      }

      if (typeof data?.amount_cents === "number") {
        setPayValue(Number(data.amount_cents) / 100);
      }

      setPayResp(JSON.stringify({ step: "order_created", response: data }, null, 2));
      fetchOrdersOnce();
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
      fetchOrdersOnce();
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
    const valNum = Number(payValue);

    if (!slotNum || slotNum < 1 || slotNum > 24) {
      setPayResp("❌ Gaveta inválida (1..24)");
      return;
    }
    if (!valNum || valNum <= 0) {
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
              pickup_id: confirmData?.pickup_id || prev.pickup_id,
              token_id: confirmData?.token_id || prev.token_id,
              manual_code: confirmData?.manual_code || prev.manual_code,
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
      await fetchOrdersOnce();
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
    fetchOrdersOnce();
  }

  const legendItems = Object.entries(STATE_STYLE);

  return (
    <div style={{ minHeight: "100vh", background: "#0f1115", color: "white", padding: 18, fontFamily: "system-ui" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>ELLAN • Locker Dashboard</h1>

        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ opacity: 0.8, fontSize: 12 }}>
            Região: <b>{region}</b> • Backend: <code>{backendBase}</code>
          </div>

          <button onClick={() => { fetchSlotsOnce(); fetchOrdersOnce(); }} style={btnSmall}>
            Atualizar tudo
          </button>

          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, opacity: 0.9 }}>
            <input type="checkbox" checked={syncEnabled} onChange={(e) => setSyncEnabled(e.target.checked)} />
            Polling (3s)
          </label>

          <div style={{ fontSize: 12, opacity: syncStatus.ok ? 0.75 : 1, color: syncStatus.ok ? "white" : "#ffb4b4" }}>
            {syncStatus.ok ? "✅" : "⚠️"} {syncStatus.msg}
          </div>
        </div>
      </div>

      <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "1.25fr 0.95fr", gap: 14, alignItems: "start" }}>
        {/* COLUNA ESQUERDA */}
        <div style={{ display: "grid", gap: 14 }}>
          <section style={panelStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <div style={{ fontWeight: 800 }}>Gavetas (1–24)</div>
              <div style={{ fontSize: 12, opacity: 0.75 }}>
                Selecionada: <b>{selectedSlot ?? "—"}</b>
              </div>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
              {legendItems.map(([key, meta]) => (
                <div
                  key={key}
                  style={{
                    display: "flex",
                    gap: 6,
                    alignItems: "center",
                    padding: "6px 8px",
                    borderRadius: 999,
                    border: "1px solid rgba(255,255,255,0.14)",
                    background: "rgba(0,0,0,0.18)",
                    fontSize: 12,
                  }}
                >
                  <span style={{ width: 10, height: 10, borderRadius: 999, background: meta.bg, display: "inline-block" }} />
                  <span style={{ opacity: 0.9 }}>{meta.label}</span>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
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

            <div style={{ marginTop: 14, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
              <div style={{ fontSize: 12, opacity: 0.8 }}>
                Alterar estado da gaveta {selectedSlot ?? "—"}:
              </div>
              {SLOT_STATES.map((s) => (
                <button
                  key={s}
                  onClick={() => selectedSlot && setStateOnBackend(selectedSlot, s)}
                  style={{
                    padding: "8px 10px",
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

          <section style={panelStyle}>
            <div style={{ fontWeight: 800, marginBottom: 10 }}>Pedidos online</div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <div style={{ fontSize: 12, opacity: 0.75 }}>
                Região atual: <b>{region}</b> • Total carregado: <b>{ordersData.length}</b>
              </div>

              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
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

                <button onClick={fetchOrdersOnce} style={btnSmall}>
                  Atualizar pedidos
                </button>
              </div>
            </div>

            {ordersError ? (
              <pre style={errorPre}>{ordersError}</pre>
            ) : null}

            <div style={{ marginTop: 10, overflowX: "auto", borderRadius: 10, border: "1px solid rgba(255,255,255,0.10)" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, minWidth: 980 }}>
                <thead>
                  <tr style={{ background: "rgba(255,255,255,0.06)" }}>
                    <th style={thStyle}>Order</th>
                    <th style={thStyle}>Status</th>
                    <th style={thStyle}>Slot</th>
                    <th style={thStyle}>Allocation</th>
                    <th style={thStyle}>SKU</th>
                    <th style={thStyle}>Valor</th>
                    <th style={thStyle}>Criado em</th>
                    <th style={thStyle}>Pago em</th>
                    <th style={thStyle}>Deadline</th>
                  </tr>
                </thead>
                <tbody>
                  {ordersLoading ? (
                    <tr>
                      <td style={tdStyle} colSpan={9}>Carregando pedidos...</td>
                    </tr>
                  ) : ordersData.length === 0 ? (
                    <tr>
                      <td style={tdStyle} colSpan={9}>Nenhum pedido encontrado.</td>
                    </tr>
                  ) : (
                    ordersData.map((item) => (
                      <tr
                        key={item.order_id}
                        onClick={() => {
                          if (item.slot) {
                            setSelectedSlot(Number(item.slot));
                            setPaySlot(Number(item.slot));
                            setActiveGroup(groupIndexFromSlot(Number(item.slot)));
                          }
                          setCurrentOrder({
                            order_id: item.order_id,
                            channel: item.channel,
                            status: item.status,
                            amount_cents: item.amount_cents,
                            allocation: {
                              allocation_id: item.allocation_id,
                              slot: item.slot,
                            },
                            pickup_deadline_at: item.pickup_deadline_at,
                          });
                        }}
                        style={{
                          cursor: "pointer",
                          background: currentOrder?.order_id === item.order_id ? "rgba(27,88,131,0.35)" : "transparent",
                        }}
                      >
                        <td style={tdStyle}>{item.order_id}</td>
                        <td style={tdStyle}>{item.status}</td>
                        <td style={tdStyle}>{item.slot ?? "-"}</td>
                        <td style={tdStyle}>{item.allocation_id ?? "-"}</td>
                        <td style={tdStyle}>{item.sku_id}</td>
                        <td style={tdStyle}>{formatMoney(item.amount_cents)}</td>
                        <td style={tdStyle}>{formatDateTime(item.created_at)}</td>
                        <td style={tdStyle}>{formatDateTime(item.paid_at)}</td>
                        <td style={tdStyle}>{formatDateTime(item.pickup_deadline_at)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div style={{ fontSize: 11, opacity: 0.65, marginTop: 8 }}>
              Clique em uma linha para destacar a gaveta correspondente e carregar o pedido no painel.
            </div>
          </section>
        </div>

        {/* COLUNA DIREITA */}
        <div style={{ display: "grid", gap: 14 }}>
          <section style={panelStyle}>
            <div style={{ fontWeight: 800 }}>Pedido atual</div>

            {selectedSlot ? (
              <div style={softInfoBox(slotSelectionRemainingSec > 10 ? "normal" : "warning")}>
                Gaveta selecionada: <b>{selectedSlot}</b> • tempo restante para criar o pedido: <b>{slotSelectionRemainingSec}s</b>
              </div>
            ) : (
              <div style={{ fontSize: 12, opacity: 0.7 }}>
                Selecione uma gaveta disponível para iniciar a criação do pedido.
              </div>
            )}

            <button
              onClick={createOnlineOrder}
              disabled={orderLoading || payLoading}
              style={{
                ...actionBtn,
                background: orderLoading ? "rgba(255,255,255,0.08)" : "#7a5f1f",
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
              <div style={infoCardStyle}>
                <InfoRow label="order_id" value={currentOrder.order_id} />
                <InfoRow label="status" value={currentOrder.status} />
                <InfoRow label="slot" value={currentOrder?.allocation?.slot ?? "-"} />
                <InfoRow label="allocation_id" value={currentOrder?.allocation?.allocation_id ?? "-"} />
                <InfoRow label="amount_cents" value={currentOrder?.amount_cents ?? "-"} />
                <InfoRow label="pickup_deadline_at" value={currentOrder?.pickup_deadline_at || "-"} />
                {currentOrder?.manual_code ? <InfoRow label="manual_code atual" value={currentOrder.manual_code} /> : null}
              </div>
            ) : (
              <div style={{ fontSize: 12, opacity: 0.7 }}>Nenhum pedido criado ou selecionado.</div>
            )}

            {orderError ? <pre style={errorPre}>{orderError}</pre> : null}
          </section>

          <section style={panelStyle}>
            <div style={{ fontWeight: 800 }}>Pagamento do pedido</div>

            <div style={{ fontSize: 12, opacity: 0.75 }}>
              Orders API: <code>{ORDER_PICKUP_BASE}/orders</code>
            </div>
            <div style={{ fontSize: 12, opacity: 0.75 }}>
              Gateway: <code>{gatewayUrl}</code>
            </div>

            {currentOrder?.status === "PAID_PENDING_PICKUP" ? (
              <div style={softInfoBox("info")}>
                ⚠️ Este pedido já está pago e aguardando retirada. Para recuperar o código manual, use <b>“Gerar/Atualizar”</b>
                no painel de retirada ou o botão <b>“Regenerar código manual”</b>.
              </div>
            ) : null}

            <label style={label}>
              Método
              <select
                value={payMethod}
                onChange={(e) => setPayMethod(e.target.value)}
                style={{ ...select, backgroundColor: "#2d2d3a" }}
              >
                <option value="PIX">PIX</option>
                <option value="CARTAO">CARTÃO</option>
                <option value="MBWAY">MBWAY</option>
                <option value="NFC">NFC</option>
              </select>
            </label>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <label style={label}>
                Gaveta
                <input
                  type="number"
                  min="1"
                  max="24"
                  value={paySlot}
                  onChange={(e) => setPaySlot(e.target.value)}
                  style={{ ...input, width: "100%" }}
                />
              </label>

              <label style={label}>
                Valor
                <input
                  type="number"
                  min="1"
                  step="0.01"
                  value={payValue}
                  onChange={(e) => setPayValue(e.target.value)}
                  style={{ ...input, width: "100%" }}
                />
              </label>
            </div>

            <button
              onClick={simulatePayment}
              disabled={payLoading || orderLoading || isOrderAlreadyPaid}
              style={{
                ...actionBtn,
                background: payLoading || orderLoading || isOrderAlreadyPaid ? "rgba(255,255,255,0.08)" : "#2d8a4a",
                cursor: payLoading || orderLoading || isOrderAlreadyPaid ? "not-allowed" : "pointer",
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

            {payResp ? <pre style={resultPre}>{payResp}</pre> : null}
          </section>

          <section style={panelStyle}>
            <div style={{ fontWeight: 800 }}>Retirada do pedido</div>

            <button
              onClick={regenerateManualCode}
              disabled={!canRegenerateManualCode || regenCodeLoading || payLoading || orderLoading}
              style={{
                ...actionBtn,
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
              pickupId={currentOrder?.order_id || ""}
              apiBase={ORDER_PICKUP_BASE}
            />

            <ManualPickupPanel
              region={region}
              apiBase={ORDER_PICKUP_BASE}
              onRedeemed={handleManualRedeemed}
            />

            {pickupResp ? <pre style={resultPre}>{pickupResp}</pre> : null}
          </section>

          <section style={panelStyle}>
            <div style={{ fontWeight: 800, marginBottom: 4 }}>Bolos por grupo (secundário)</div>

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

            <div style={{ display: "grid", gap: 10 }}>
              {groupSlotsList.map((slot) => {
                const st = slots[slot]?.state || "AVAILABLE";
                const meta = STATE_STYLE[st] || { bg: "#333", fg: "white", label: st };
                const cake = cakes[slot];

                return (
                  <div key={slot} style={{ borderRadius: 12, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(0,0,0,0.18)", padding: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <button onClick={() => selectSlot(slot)} style={{ ...btnSmall, padding: "6px 10px", fontWeight: 700 }}>
                        Gaveta {slot}
                      </button>

                      <span style={{ padding: "4px 8px", borderRadius: 999, background: meta.bg, color: meta.fg, fontSize: 11, fontWeight: 700 }}>
                        {meta.label}
                      </span>
                    </div>

                    <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                      <label style={label}>
                        Nome do bolo
                        <input
                          value={cake?.name || ""}
                          onChange={(e) => updateCake(slot, { name: e.target.value })}
                          placeholder="ex.: Bolo de Cenoura"
                          style={input}
                        />
                      </label>

                      <label style={label}>
                        Observações
                        <input
                          value={cake?.notes || ""}
                          onChange={(e) => updateCake(slot, { notes: e.target.value })}
                          placeholder="ex.: sem lactose / promoção / etc."
                          style={input}
                        />
                      </label>

                      <label style={label}>
                        URL da imagem (opcional)
                        <input
                          value={cake?.imageUrl || ""}
                          onChange={(e) => updateCake(slot, { imageUrl: e.target.value })}
                          placeholder="https://..."
                          style={input}
                        />
                      </label>

                      {cake?.imageUrl ? (
                        <img
                          alt={`Bolo da gaveta ${slot}`}
                          src={cake.imageUrl}
                          style={{ width: "100%", borderRadius: 10, border: "1px solid rgba(255,255,255,0.12)", marginTop: 6 }}
                        />
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 8 }}>
      <div style={{ opacity: 0.7 }}>{label}:</div>
      <div style={{ fontWeight: 600, wordBreak: "break-all" }}>{value}</div>
    </div>
  );
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
    padding: 10,
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.12)",
    background: backgrounds[kind] || backgrounds.normal,
  };
}

const panelStyle = {
  borderRadius: 14,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.04)",
  padding: 14,
  display: "grid",
  gap: 10,
};

const infoCardStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.04)",
  padding: 10,
  display: "grid",
  gap: 6,
  fontSize: 12,
};

const actionBtn = {
  padding: "10px 12px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.18)",
  color: "white",
  fontWeight: 800,
};

const label = {
  fontSize: 12,
  opacity: 0.9,
  display: "grid",
  gap: 6,
};

const input = {
  width: "100%",
  padding: "10px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.06)",
  color: "white",
  outline: "none",
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
  maxHeight: 180,
  fontSize: 12,
};

const resultPre = {
  margin: 0,
  padding: 10,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "#0b0d10",
  color: "white",
  overflow: "auto",
  maxHeight: 260,
  fontSize: 12,
};