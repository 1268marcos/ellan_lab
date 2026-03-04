import React, { useEffect, useMemo, useRef, useState } from "react";

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

  // ==== slots / cakes ====
  const [slots, setSlots] = useState(() => slotsListToMap([]));
  const [cakes, setCakes] = useState(() => buildInitialCakes());

  const [selectedSlot, setSelectedSlot] = useState(1);
  const [activeGroup, setActiveGroup] = useState(0);

  // ==== backend sync UI ====
  const [syncEnabled, setSyncEnabled] = useState(true); // polling on/off
  const [syncStatus, setSyncStatus] = useState({ ok: true, msg: "—" });
  const pollTimerRef = useRef(null);
  const abortRef = useRef(null);

  // ==== pagamento (gateway) ====
  const [payMethod, setPayMethod] = useState("PIX");
  const [payValue, setPayValue] = useState(100);
  const [paySlot, setPaySlot] = useState(1);
  const [payResp, setPayResp] = useState("");
  const [payLoading, setPayLoading] = useState(false);

  useEffect(() => {
    setPaySlot(selectedSlot);
  }, [selectedSlot]);

  function selectSlot(slot) {
    setSelectedSlot(slot);
    setActiveGroup(groupIndexFromSlot(slot));
  }

  const groupSlotsList = useMemo(() => groupSlots(activeGroup), [activeGroup]);

  function updateCake(slot, patch) {
    setCakes((prev) => ({ ...prev, [slot]: { ...prev[slot], ...patch } }));
  }

  async function fetchSlotsOnce() {
    // cancela request anterior
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

  // polling
  useEffect(() => {
    // ao mudar região, faz fetch imediato
    fetchSlotsOnce();

    // limpa timer antigo
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

  async function setStateOnBackend(slot, nextState) {
    const payload = { state: nextState, product_id: slots[slot]?.product_id ?? null };

    // otimista (UI muda na hora)
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
        // rollback soft: refetch
        setSyncStatus({ ok: false, msg: `set-state falhou HTTP ${res.status}: ${text}` });
        await fetchSlotsOnce();
        return;
      }

      // backend retorna JSON (ok:true etc)
      setSyncStatus({ ok: true, msg: `set-state OK (${slot} → ${nextState})` });
    } catch (e) {
      setSyncStatus({ ok: false, msg: `set-state erro: ${String(e?.message || e)}` });
      await fetchSlotsOnce();
    }
  }

  async function simulatePayment() {
    const slotNum = Number(paySlot);
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
      const res = await fetch(gatewayUrl, {
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

      const text = await res.text();
      if (!res.ok) {
        setPayResp(`❌ HTTP ${res.status}\n${text}\n\nURL: ${gatewayUrl}`);
        return;
      }

      try {
        setPayResp(JSON.stringify(JSON.parse(text), null, 2));
      } catch {
        setPayResp(text);
      }

      // opcional: atualizar estado no backend logo após pagamento (pra simular fluxo)
      // Se você NÃO quiser esse efeito, comente a linha abaixo.
      await setStateOnBackend(slotNum, "PAID_PENDING_PICKUP");

      setSelectedSlot(slotNum);
    } catch (e) {
      setPayResp(`❌ Falha ao chamar gateway\n${String(e?.message || e)}\n\nURL: ${gatewayUrl}`);
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
              Selecionada: <b>{selectedSlot}</b>
            </div>
          </div>

          {/* legenda */}
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

          {/* grid 24 */}
          <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
            {Array.from({ length: 24 }).map((_, idx) => {
              const slot = idx + 1;
              const st = slots[slot]?.state || "AVAILABLE";
              return (
                <SlotCard key={slot} slot={slot} state={st} selected={slot === selectedSlot} onClick={() => selectSlot(slot)} />
              );
            })}
          </div>

          {/* state changer (agora salva no backend) */}
          <div style={{ marginTop: 14, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ fontSize: 12, opacity: 0.8 }}>Alterar estado da gaveta {selectedSlot} (salva no backend):</div>
            {SLOT_STATES.map((s) => (
              <button
                key={s}
                onClick={() => setStateOnBackend(selectedSlot, s)}
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
          {/* Simular pagamento */}
          <div style={{ borderRadius: 12, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(0,0,0,0.18)", padding: 12, display: "grid", gap: 10 }}>
            <div style={{ fontWeight: 800 }}>Simular pagamento (Gateway)</div>

            <div style={{ fontSize: 12, opacity: 0.75 }}>
              Endpoint: <code style={{ opacity: 0.9 }}>{gatewayUrl}</code>
            </div>

            <label style={label}>
              Método
              <select value={payMethod} onChange={(e) => setPayMethod(e.target.value)} style={select}>
                <option value="PIX">PIX</option>
                <option value="CARTAO">CARTÃO</option>
                <option value="MBWAY">MBWAY</option>
                <option value="NFC">NFC</option>
              </select>
            </label>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <label style={label}>
                Gaveta
                <input type="number" min="1" max="24" value={paySlot} onChange={(e) => setPaySlot(e.target.value)} style={input} />
                <div style={{ fontSize: 11, opacity: 0.65, marginTop: 4 }}>(auto preenche a selecionada)</div>
              </label>

              <label style={label}>
                Valor
                <input type="number" min="1" step="1" value={payValue} onChange={(e) => setPayValue(e.target.value)} style={input} />
              </label>
            </div>

            <button
              onClick={simulatePayment}
              disabled={payLoading}
              style={{
                padding: "10px 12px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.18)",
                background: payLoading ? "rgba(255,255,255,0.08)" : "#2d8a4a",
                color: "white",
                cursor: payLoading ? "not-allowed" : "pointer",
                fontWeight: 800,
              }}
            >
              {payLoading ? "Enviando..." : "Enviar pagamento"}
            </button>

            {payResp ? (
              <pre style={{ margin: 0, padding: 10, borderRadius: 12, border: "1px solid rgba(255,255,255,0.12)", background: "#0b0d10", color: "white", overflow: "auto", maxHeight: 220, fontSize: 12 }}>
                {payResp}
              </pre>
            ) : null}
          </div>

          {/* Carrossel */}
          <div style={{ fontWeight: 800, marginTop: 4 }}>Bolos por grupo (4 gavetas)</div>

          <Carousel pages={6} activeIndex={activeGroup} onPrev={() => setActiveGroup((g) => (g - 1 + 6) % 6)} onNext={() => setActiveGroup((g) => (g + 1) % 6)} onGo={(i) => setActiveGroup(clamp(i, 0, 5))} />

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
                      <input value={cake?.name || ""} onChange={(e) => updateCake(slot, { name: e.target.value })} placeholder="ex.: Bolo de Cenoura" style={input} />
                    </label>

                    <label style={label}>
                      Observações
                      <input value={cake?.notes || ""} onChange={(e) => updateCake(slot, { notes: e.target.value })} placeholder="ex.: sem lactose / promoção / etc." style={input} />
                    </label>

                    <label style={label}>
                      URL da imagem (opcional)
                      <input value={cake?.imageUrl || ""} onChange={(e) => updateCake(slot, { imageUrl: e.target.value })} placeholder="https://..." style={input} />
                    </label>

                    {cake?.imageUrl ? (
                      <img alt={`Bolo da gaveta ${slot}`} src={cake.imageUrl} style={{ width: "100%", borderRadius: 10, border: "1px solid rgba(255,255,255,0.12)", marginTop: 6 }} />
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ fontSize: 12, opacity: 0.6 }}>
            Estados agora vêm do backend (GET /locker/slots) e set-state atualiza no backend.
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