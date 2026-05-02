import React, { useCallback, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

const STATUS_BG = {
  AVAILABLE: { bg: "rgba(22,163,74,0.35)", border: "rgba(34,197,94,0.55)", fg: "#BBF7D0" },
  OCCUPIED: { bg: "rgba(234,179,8,0.28)", border: "rgba(250,204,21,0.5)", fg: "#FEF9C3" },
  MAINTENANCE: { bg: "rgba(139,92,246,0.28)", border: "rgba(167,139,250,0.55)", fg: "#EDE9FE" },
  default: { bg: "rgba(71,85,105,0.35)", border: "rgba(148,163,184,0.45)", fg: "#E2E8F0" },
};

function cellStyle(st) {
  const k = String(st || "").toUpperCase();
  const p = STATUS_BG[k] || STATUS_BG.default;
  return {
    border: `1px solid ${p.border}`,
    background: p.bg,
    color: p.fg,
    borderRadius: 10,
    padding: "10px 8px",
    minHeight: 72,
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    gap: 6,
    fontSize: 12,
  };
}

export default function OpsLockerSlotsPage() {
  const { token } = useAuth();
  const [lockerId, setLockerId] = useState("");
  const [configs, setConfigs] = useState([]);
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const headers = useMemo(
    () => ({ Accept: "application/json", "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token]
  );

  const load = useCallback(async () => {
    const lid = String(lockerId || "").trim();
    if (!token || !lid) return;
    setLoading(true);
    setErr("");
    setMsg("");
    try {
      const u1 = new URL(`${BASE}/locker/slots/config`, window.location.origin);
      u1.searchParams.set("locker_id", lid);
      const u2 = new URL(`${BASE}/locker/slots/status`, window.location.origin);
      u2.searchParams.set("locker_id", lid);
      const [r1, r2] = await Promise.all([fetch(u1.toString(), { headers }), fetch(u2.toString(), { headers })]);
      const j1 = await r1.json().catch(() => ({}));
      const j2 = await r2.json().catch(() => ({}));
      if (!r1.ok) throw new Error(typeof j1?.detail?.message === "string" ? j1.detail.message : r1.statusText);
      if (!r2.ok) throw new Error(typeof j2?.detail?.message === "string" ? j2.detail.message : r2.statusText);
      setConfigs(Array.isArray(j1.configs) ? j1.configs : []);
      setSlots(Array.isArray(j2.slots) ? j2.slots : []);
    } catch (e) {
      setErr(String(e.message || e));
      setConfigs([]);
      setSlots([]);
    } finally {
      setLoading(false);
    }
  }, [token, lockerId, headers]);

  const forceRelease = async (slotKey) => {
    const lid = String(lockerId || "").trim();
    if (!token || !lid) return;
    setErr("");
    setMsg("");
    try {
      const path = encodeURIComponent(slotKey);
      const u = new URL(`${BASE}/locker/slots/${path}/force-release`, window.location.origin);
      u.searchParams.set("locker_id", lid);
      const r = await fetch(u.toString(), { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail?.message === "string" ? j.detail.message : JSON.stringify(j.detail || j));
      setMsg(j.idempotent ? "Slot já estava livre." : `Liberação OK: ${j.slot_label || slotKey}`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Slots do locker (configs + status)" />
        <p style={muted}>
          <code style={codeInline}>{BASE}/locker/slots/config|status</code> e{" "}
          <code style={codeInline}>POST .../locker/slots/&#123;slot&#125;/force-release</code> — role{" "}
          <code style={codeInline}>admin_operacao</code>.
        </p>
        <div style={toolbar}>
          <label style={lbl}>
            locker_id
            <input value={lockerId} onChange={(e) => setLockerId(e.target.value)} style={{ ...inp, minWidth: 260 }} />
          </label>
          <button type="button" style={{ ...btnPrimary, opacity: loading || !lockerId.trim() ? 0.45 : 1 }} onClick={load} disabled={loading || !lockerId.trim()}>
            {loading ? "Carregando…" : "Carregar"}
          </button>
        </div>
        <div style={{ ...toolbar, marginTop: 8 }}>
          <span style={{ fontSize: 11, color: "#94A3B8" }}>Legenda:</span>
          {["AVAILABLE", "OCCUPIED", "MAINTENANCE"].map((s) => (
            <span key={s} style={{ ...legendSwatch, ...cellStyle(s) }}>
              {s}
            </span>
          ))}
        </div>
        {err ? <pre style={errBox}>{err}</pre> : null}
        {msg ? <pre style={okBox}>{msg}</pre> : null}
        {!token ? <p style={muted}>Faça login com perfil admin_operacao.</p> : null}

        {configs.length > 0 ? (
          <div style={{ marginTop: 16 }}>
            <h3 style={h3}>locker_slot_configs</h3>
            <div style={tableWrap}>
              <table style={table}>
                <thead>
                  <tr>
                    {["slot_size", "slot_count", "avail", "W×H×D mm"].map((h) => (
                      <th key={h} style={th}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {configs.map((c) => (
                    <tr key={c.id}>
                      <td style={tdStyle}>{c.slot_size}</td>
                      <td style={tdStyle}>{c.slot_count}</td>
                      <td style={tdStyle}>{c.available_count ?? "—"}</td>
                      <td style={tdStyle}>{[c.width_mm, c.height_mm, c.depth_mm].map((x) => x ?? "—").join(" / ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {slots.length > 0 ? (
          <div style={{ marginTop: 20 }}>
            <h3 style={h3}>locker_slots (grade)</h3>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
                gap: 10,
                marginTop: 10,
              }}
            >
              {slots.map((s) => {
                const busy = String(s.status || "").toUpperCase() !== "AVAILABLE" || Boolean(s.current_allocation_id);
                return (
                  <div key={s.id} style={cellStyle(s.status)}>
                    <div>
                      <strong>{s.slot_label}</strong>
                      <div style={{ fontSize: 10, opacity: 0.9 }}>{s.slot_size}</div>
                      <div style={{ fontSize: 10, opacity: 0.85 }}>{String(s.status || "").toUpperCase()}</div>
                      {s.current_allocation_id ? <div style={{ fontSize: 9, opacity: 0.75 }}>alloc: {String(s.current_allocation_id).slice(0, 8)}…</div> : null}
                    </div>
                    {busy ? (
                      <button type="button" style={btnSmWarn} onClick={() => forceRelease(s.slot_label || s.id)}>
                        Force release
                      </button>
                    ) : (
                      <span style={{ fontSize: 10, opacity: 0.7 }}>livre</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ) : null}
        {token && !loading && lockerId.trim() && !slots.length && !configs.length && !err ? <p style={muted}>Nenhum dado para este locker.</p> : null}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const muted = { color: "#94A3B8", marginTop: 8 };
const codeInline = { color: "#CBD5E1", fontSize: 12 };
const toolbar = { display: "flex", flexWrap: "wrap", gap: 12, marginTop: 12, alignItems: "flex-end" };
const lbl = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inp = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const btnPrimary = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const errBox = { marginTop: 12, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10, whiteSpace: "pre-wrap" };
const okBox = { marginTop: 12, background: "rgba(22,163,74,0.12)", color: "#BBF7D0", border: "1px solid rgba(34,197,94,0.35)", borderRadius: 10, padding: 10, whiteSpace: "pre-wrap" };
const tableWrap = { marginTop: 8, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const table = { width: "100%", borderCollapse: "collapse", minWidth: 400 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
const h3 = { fontSize: 14, color: "#BFDBFE", margin: 0 };
const legendSwatch = { padding: "6px 10px", borderRadius: 8, minHeight: "auto", fontWeight: 700 };
const btnSmWarn = {
  padding: "4px 8px",
  borderRadius: 8,
  border: "1px solid rgba(251,191,36,0.5)",
  background: "rgba(120,53,15,0.45)",
  color: "#FEF3C7",
  fontSize: 11,
  cursor: "pointer",
  alignSelf: "flex-start",
};
