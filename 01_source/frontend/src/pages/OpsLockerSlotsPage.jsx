import React, { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const PAGE_VERSION = "ops/lockers/slots v0.2-health-shell";

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
        <div style={crossShortcutStyle}>
          <Link to="/ops/health" style={crossShortcutLinkStyle}>
            Ir para saúde operacional
          </Link>
        </div>
        <div style={headerRowStyle}>
          <div>
            <OpsPageTitleHeader
              title="OPS — Slots do locker (configs + status)"
              versionLabel={PAGE_VERSION}
              versionTo="/ops/auth/policy/versioning"
              containerStyle={{ marginBottom: 0 }}
              titleStyle={{ margin: 0 }}
            />
            <p style={mutedTextStyle}>
              <code style={{ color: "#e2e8f0" }}>{BASE}/locker/slots/config|status</code> e{" "}
              <code style={{ color: "#e2e8f0" }}>POST .../locker/slots/&#123;slot&#125;/force-release</code> — role{" "}
              <code style={{ color: "#e2e8f0" }}>admin_operacao</code>.
            </p>
          </div>
        </div>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Locker</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              locker_id
              <input value={lockerId} onChange={(e) => setLockerId(e.target.value)} style={healthLocalFilterInputStyle} />
            </label>
          </div>
          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !lockerId.trim()}>
              {loading ? "Atualizando..." : "Carregar"}
            </button>
          </div>
          <div style={{ ...toolbarStyle, marginTop: 4 }}>
            <span style={summary24hHintStyle}>Legenda:</span>
            {["AVAILABLE", "OCCUPIED", "MAINTENANCE"].map((s) => (
              <span key={s} style={{ ...legendSwatch, ...cellStyle(s) }}>
                {s}
              </span>
            ))}
          </div>
        </section>

        {err ? (
          <div style={criticalBannerStyle} role="alert">
            {err}
          </div>
        ) : null}
        {msg ? <small style={predictiveReviewStatusStyle}>{msg}</small> : null}

        {!token ? <p style={summary24hHintStyle}>Faça login com perfil admin_operacao.</p> : null}

        {configs.length > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>locker_slot_configs</h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["slot_size", "slot_count", "avail", "W×H×D mm"].map((h) => (
                      <th key={h} style={thStyle}>
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
          </section>
        ) : null}

        {slots.length > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>locker_slots (grade)</h3>
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
                gap: 10,
                marginTop: 4,
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
                      {s.current_allocation_id ? (
                        <div style={{ fontSize: 9, opacity: 0.75 }}>alloc: {String(s.current_allocation_id).slice(0, 8)}...</div>
                      ) : null}
                    </div>
                    {busy ? (
                      <button type="button" style={warnButtonStyle} onClick={() => void forceRelease(s.slot_label || s.id)}>
                        Force release
                      </button>
                    ) : (
                      <span style={{ fontSize: 10, opacity: 0.7 }}>livre</span>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        ) : null}
        {token && !loading && lockerId.trim() && !slots.length && !configs.length && !err ? (
          <p style={summary24hHintStyle}>Nenhum dado para este locker.</p>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

const cardStyle = {
  width: "100%",
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const headerRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  alignItems: "flex-start",
  flexWrap: "wrap",
};

const crossShortcutStyle = {
  display: "flex",
  justifyContent: "flex-end",
  marginBottom: 10,
};

const crossShortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const labelStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle = {
  width: 90,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const healthLocalFilterRowStyle = {
  marginTop: 10,
  marginBottom: 8,
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  alignItems: "end",
};

const healthLocalFilterFieldStyle = {
  ...labelStyle,
  color: "#cbd5e1",
};

const healthLocalFilterInputStyle = {
  ...inputStyle,
  width: "100%",
  border: "1px solid rgba(148,163,184,0.5)",
};

const toolbarStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-end",
  flexWrap: "wrap",
};

const buttonGhostStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const warnButtonStyle = {
  ...buttonGhostStyle,
  border: "1px solid rgba(251,191,36,0.5)",
  background: "rgba(120,53,15,0.26)",
  color: "#fde68a",
  fontSize: 11,
  padding: "4px 8px",
  alignSelf: "flex-start",
};

const opsSanityCardStyle = {
  marginTop: 6,
  borderRadius: 12,
  border: "1px solid rgba(59,130,246,0.45)",
  background: "rgba(30,58,138,0.2)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const summary24hHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const summary24hHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const predictiveReviewStatusStyle = {
  color: "#e2e8f0",
  fontSize: 12,
  fontWeight: 700,
};

const criticalBannerStyle = {
  borderRadius: 10,
  border: "1px solid rgba(248,113,113,0.72)",
  background: "linear-gradient(180deg, rgba(127,29,29,0.58) 0%, rgba(127,29,29,0.3) 100%)",
  color: "#fecaca",
  padding: "10px 12px",
  fontWeight: 700,
  fontSize: 13,
};

const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 400, fontSize: 12 };
const thStyle = { textAlign: "left", borderBottom: "1px solid #444", padding: 8, color: "#cbd5e1" };
const tdStyle = { padding: 8, borderTop: "1px solid #333", color: "#e2e8f0" };

const legendSwatch = { padding: "6px 10px", borderRadius: 8, minHeight: "auto", fontWeight: 700 };
