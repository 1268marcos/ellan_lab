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

/**
 * Converte resposta do backend (lista) em map {1..24}
 * Backend: [{slot, state, product_id, updated_at}, ...]
 */
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

/**
 * Fingerprint + idempotência
 */
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
  const cakeName = "";
  const normalized = String(cakeName).trim().toUpperCase().replace(/\s+/g, "_");
  if (normalized) return normalized;
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

/**
 * Gaveta (card)
 */
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

/**
 * Carrossel simples (6 páginas)
 */
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
  // ==== BASE URLs ====
  const BACKEND_SP = import.meta.env.VITE_BACKEND_SP_BASE_URL || "http://localhost:8201";
  const BACKEND_PT = import.meta.env.VITE_BACKEND_PT_BASE_URL || "http://localhost:8202";
  const backendBase = region === "SP" ? BACKEND_SP : BACKEND_PT;

  const GATEWAY_BASE = import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";
  const gatewayUrl = useMemo(() => `${GATEWAY_BASE}/gateway/pagamento`, [GATEWAY_BASE]);

  const ORDER_PICKUP_BASE =
    import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

  const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";

  // ==== slots / cakes ====
  const [slots, setSlots] = useState(() => slotsListToMap([]));
  const [cakes, setCakes] = useState(() => buildInitialCakes());

  const [selectedSlot, setSelectedSlot] = useState(null);
  const [activeGroup, setActiveGroup] = useState(0);
  const [slotSelectionExpiresAt, setSlotSelectionExpiresAt] = useState(null);
  const [slotSelectionTick, setSlotSelectionTick] = useState(0);

  // calcular segundos restantes após a escolha do slot gaveta
  // ⚠️ IMPORTANTE: Calcular slotSelectionRemainingSec AQUI, antes de ser usado
  const slotSelectionRemainingSec = slotSelectionExpiresAt
    ? Math.max(0, Math.ceil((slotSelectionExpiresAt - Date.now()) / 1000))
    : 0;

  // ==== backend sync UI ====
  const [syncEnabled, setSyncEnabled] = useState(true);
  const [syncStatus, setSyncStatus] = useState({ ok: true, msg: "—" });
  const pollTimerRef = useRef(null);
  const abortRef = useRef(null);

  // ==== pedido online dinâmico ====
  const [orderLoading, setOrderLoading] = useState(false);
  const [orderError, setOrderError] = useState("");
  const [currentOrder, setCurrentOrder] = useState(null);
  // shape esperada:
  // {
  //   order_id,
  //   channel,
  //   status,
  //   amount_cents,
  //   allocation: { allocation_id, slot, ttl_sec }
  // }

  // ==== pagamento (gateway) ====
  const [payMethod, setPayMethod] = useState("PIX");
  const [payValue, setPayValue] = useState(100);
  const [paySlot, setPaySlot] = useState(1);
  const [payResp, setPayResp] = useState("");
  const [payLoading, setPayLoading] = useState(false);

  useEffect(() => {
    setPaySlot(selectedSlot);
  }, [selectedSlot]);

  const groupSlotsList = useMemo(() => groupSlots(activeGroup), [activeGroup]);

  /**
   * Refresh após a retirada com o Código do QRCode (manual_code)
   */
  function handleManualRedeemed(data) {
    if (data?.slot) {
      setSelectedSlot(Number(data.slot));
      setActiveGroup(groupIndexFromSlot(Number(data.slot)));
    }

    setCurrentOrder(null);
    setSlotSelectionExpiresAt(null);
    setPayResp(
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
  }

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

  // resetar ao trocar região
  useEffect(() => {
    setSelectedSlot(null);
    setActiveGroup(0);
    setPaySlot(1);
    setCurrentOrder(null);
    setOrderError("");
    setPayResp("");
    setSlotSelectionExpiresAt(null);
  }, [region]);

  // relógio de 1s para a seleção
  useEffect(() => {
    const t = setInterval(() => {
      setSlotSelectionTick((x) => x + 1);
    }, 1000);
    return () => clearInterval(t);
  }, []);

  // expirar seleção automaticamente
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
    } catch (e) {
      setOrderError(String(e?.message || e));
    } finally {
      setOrderLoading(false);
    }
  }

  async function confirmPaymentInternally(orderId, transactionId) {
    if (!INTERNAL_TOKEN) {
      throw new Error(
        "VITE_INTERNAL_TOKEN não configurado no frontend. Configure para usar /internal/orders/{order_id}/payment-confirm em DEV."
      );
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

  async function simulatePayment() {
    if (!currentOrder?.order_id) {
      setPayResp("❌ Antes de pagar, clique em “Criar pedido online”.");
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
    } catch (e) {
      setPayResp(`❌ Falha no fluxo de pagamento\n${String(e?.message || e)}`);
    } finally {
      setPayLoading(false);
    }
  }

  const legendItems = Object.entries(STATE_STYLE);

  return (
    <div style={{ minHeight: "100vh", background: "#0f1115", color: "white", padding: 18, fontFamily: "system-ui" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>ELLAN • Locker Dashboard</h1>

        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ opacity: 0.8, fontSize: 12 }}>
            Região: <b>{region}</b> • Backend: <code>{backendBase}</code>
          </div>

          <button onClick={fetchSlotsOnce} style={btnSmall}>
            Atualizar
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

      <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "1fr 360px", gap: 14 }}>
        {/* (1) GRID DE GAVETAS */}
        <div style={{ borderRadius: 14, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.04)", padding: 14 }}>
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
                <SlotCard key={slot} slot={slot} state={st} selected={slot === selectedSlot} onClick={() => selectSlot(slot)} />
              );
            })}
          </div>

          <div style={{ marginTop: 14, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ fontSize: 12, opacity: 0.8 }}>Alterar estado da gaveta {selectedSlot ?? "—"} (salva no backend):</div>
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
        </div>

        {/* (2) PAINEL LATERAL */}
        <div style={{ borderRadius: 14, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.04)", padding: 14, display: "grid", gap: 12, alignContent: "start" }}>
          {/* Pedido + pagamento */}
          <div style={{ borderRadius: 12, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(0,0,0,0.18)", padding: 12, display: "grid", gap: 10 }}>
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

            <div style={{ fontWeight: 800 }}>Pedido online + pagamento</div>

            <div style={{ fontSize: 12, opacity: 0.75 }}>
              Orders API: <code style={{ opacity: 0.9 }}>{ORDER_PICKUP_BASE}/orders</code>
            </div>
            <div style={{ fontSize: 12, opacity: 0.75 }}>
              Gateway: <code style={{ opacity: 0.9 }}>{gatewayUrl}</code>
            </div>

            {selectedSlot ? (
              <div
                style={{
                  fontSize: 12,
                  opacity: 0.9,
                  padding: 10,
                  borderRadius: 10,
                  border: "1px solid rgba(255,255,255,0.12)",
                  background: slotSelectionRemainingSec > 10 ? "rgba(255,255,255,0.04)" : "rgba(179,38,30,0.18)",
                }}
              >
                Gaveta selecionada: <b>{selectedSlot}</b> • tempo restante para criar o pedido:{" "}
                <b>{slotSelectionRemainingSec}s</b>
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
                padding: "10px 12px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.18)",
                background: orderLoading ? "rgba(255,255,255,0.08)" : "#7a5f1f",
                color: "white",
                cursor: orderLoading || payLoading ? "not-allowed" : "pointer",
                fontWeight: 800,
              }}
            >
              {orderLoading
                ? "Criando pedido..."
                : selectedSlot
                  ? `Criar pedido online — gaveta ${selectedSlot}`
                  : "Criar pedido online"}

            </button>

            {currentOrder ? (
              <div
                style={{
                  borderRadius: 12,
                  border: "1px solid rgba(255,255,255,0.12)",
                  background: "rgba(255,255,255,0.04)",
                  padding: 10,
                  display: "grid",
                  gap: 6,
                  fontSize: 12,
                }}
              >
                <div>
                  <b>order_id:</b> {currentOrder.order_id}
                </div>
                <div>
                  <b>status:</b> {currentOrder.status}
                </div>
                <div>
                  <b>slot:</b> {currentOrder?.allocation?.slot ?? "-"}
                </div>
                <div>
                  <b>allocation_id:</b> {currentOrder?.allocation?.allocation_id ?? "-"}
                </div>
                <div>
                  <b>amount_cents:</b> {currentOrder?.amount_cents ?? "-"}
                </div>
                {currentOrder?.pickup_deadline_at ? (
                  <div>
                    <b>pickup_deadline_at:</b> {currentOrder.pickup_deadline_at}
                  </div>
                ) : null}
                {currentOrder?.manual_code ? (
                  <div>
                    <b>manual_code:</b> {currentOrder.manual_code}
                  </div>
                ) : null}
              </div>
            ) : (
              <div style={{ fontSize: 12, opacity: 0.7 }}>
                Nenhum pedido criado ainda.
              </div>
            )}

            {orderError ? (
              <pre style={{ margin: 0, padding: 10, borderRadius: 12, border: "1px solid rgba(255,255,255,0.12)", background: "#2b1d1d", color: "#ffb4b4", overflow: "auto", maxHeight: 180, fontSize: 12 }}>
                {orderError}
              </pre>
            ) : null}

            <label style={label}>
              Método
              <select
                value={payMethod}
                onChange={(e) => setPayMethod(e.target.value)}
                style={{
                  ...select,
                  color: "white",
                  backgroundColor: "#2d2d3a",
                }}
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
                  style={{ ...input, width: "60%" }}
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
                  style={{ ...input, width: "60%" }}
                />
              </label>
            </div>

            <div style={{ fontSize: 11, opacity: 0.65, marginTop: 4 }}>
              ⓘ O pedido criado define o order_id real. A gaveta/valor são preenchidos a partir da alocação/preço retornados.
            </div>

            <button
              onClick={simulatePayment}
              disabled={payLoading || orderLoading}
              style={{
                padding: "10px 12px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.18)",
                background: payLoading ? "rgba(255,255,255,0.08)" : "#2d8a4a",
                color: "white",
                cursor: payLoading || orderLoading ? "not-allowed" : "pointer",
                fontWeight: 800,
              }}
            >
              {payLoading ? "Enviando..." : "Pagar pedido atual"}
            </button>

            {payResp ? (
              <pre style={{ margin: 0, padding: 10, borderRadius: 12, border: "1px solid rgba(255,255,255,0.12)", background: "#0b0d10", color: "white", overflow: "auto", maxHeight: 260, fontSize: 12 }}>
                {payResp}
              </pre>
            ) : null}
          </div>

          {/* Carrossel */}
          <div style={{ fontWeight: 800, marginTop: 4 }}>Bolos por grupo (4 gavetas)</div>

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

          <div style={{ fontSize: 12, opacity: 0.6 }}>
            Estados vêm do backend. Pedido online agora usa <b>order_id real</b>, não hardcoded.
          </div>
        </div>
      </div>
    </div>
  );
}

const label = { fontSize: 12, opacity: 0.9, display: "grid", gap: 6 };

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