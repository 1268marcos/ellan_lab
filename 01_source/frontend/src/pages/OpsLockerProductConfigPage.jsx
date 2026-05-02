import React, { useCallback, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

export default function OpsLockerProductConfigPage() {
  const { token } = useAuth();
  const [lockerId, setLockerId] = useState("");
  const [category, setCategory] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const headers = useMemo(
    () => ({ Accept: "application/json", "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token]
  );

  const load = useCallback(async () => {
    const lid = String(lockerId || "").trim();
    if (!token || !lid) return;
    setLoading(true);
    setErr("");
    try {
      const u = new URL(`${BASE}/locker/product-configs`, window.location.origin);
      u.searchParams.set("locker_id", lid);
      const r = await fetch(u.toString(), { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail?.message === "string" ? j.detail.message : r.statusText);
      setItems(Array.isArray(j.items) ? j.items : []);
    } catch (e) {
      setErr(String(e.message || e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [token, lockerId, headers]);

  const add = async () => {
    const lid = String(lockerId || "").trim();
    const cat = String(category || "").trim();
    if (!token || !lid || !cat) return;
    setErr("");
    try {
      const r = await fetch(`${BASE}/locker/product-configs`, {
        method: "POST",
        headers,
        body: JSON.stringify({ locker_id: lid, category: cat, allowed: true, temperature_zone: "ANY" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail?.message === "string" ? j.detail.message : JSON.stringify(j.detail || j));
      setCategory("");
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const del = async (id) => {
    if (!token) return;
    setErr("");
    try {
      const r = await fetch(`${BASE}/locker/product-configs/${id}`, { method: "DELETE", headers: { Authorization: headers.Authorization } });
      if (!r.ok && r.status !== 204) {
        const j = await r.json().catch(() => ({}));
        throw new Error(typeof j?.detail?.message === "string" ? j.detail.message : r.statusText);
      }
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Locker × categoria (product_locker_configs)" />
        <p style={muted}>
          GET/POST/DELETE <code style={codeInline}>{BASE}/locker/product-configs</code> — role <code style={codeInline}>admin_operacao</code>.
        </p>
        <div style={toolbar}>
          <label style={lbl}>
            locker_id
            <input value={lockerId} onChange={(e) => setLockerId(e.target.value)} style={{ ...inp, minWidth: 220 }} />
          </label>
          <button
            type="button"
            style={{ ...btnPrimary, opacity: loading || !lockerId.trim() ? 0.45 : 1 }}
            onClick={load}
            disabled={loading || !lockerId.trim()}
          >
            {loading ? "Carregando…" : "Listar"}
          </button>
          <label style={lbl}>
            category (nova associação)
            <input value={category} onChange={(e) => setCategory(e.target.value)} style={{ ...inp, minWidth: 180 }} />
          </label>
          <button
            type="button"
            style={{ ...btnSecondary, opacity: !lockerId.trim() || !category.trim() ? 0.45 : 1 }}
            onClick={add}
            disabled={!lockerId.trim() || !category.trim()}
          >
            Associar
          </button>
        </div>
        {err ? <pre style={errBox}>{err}</pre> : null}
        {!token ? <p style={muted}>Faça login com perfil admin_operacao.</p> : null}
        {token && !loading && !items.length && !err ? <p style={muted}>Nenhuma config para este locker.</p> : null}
        {items.length > 0 ? (
          <div style={tableWrap}>
            <table style={table}>
              <thead>
                <tr>
                  {["id", "category", "sub", "allowed", "temp", "sig", "idChk", "g", "mm W/H/D", "haz", "frag", "pri", ""].map((h) => (
                    <th key={h || "act"} style={th}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.id}>
                    <td style={tdStyle}>{r.id}</td>
                    <td style={tdStyle}>{r.category}</td>
                    <td style={tdStyle}>{r.subcategory || "—"}</td>
                    <td style={tdStyle}>{r.allowed ? "Y" : "N"}</td>
                    <td style={tdStyle}>{r.temperature_zone}</td>
                    <td style={tdStyle}>{r.requires_signature ? "Y" : "N"}</td>
                    <td style={tdStyle}>{r.requires_id_check ? "Y" : "N"}</td>
                    <td style={tdStyle}>{r.max_weight_g ?? "—"}</td>
                    <td style={tdStyle}>{[r.max_width_mm, r.max_height_mm, r.max_depth_mm].map((x) => x ?? "—").join("/")}</td>
                    <td style={tdStyle}>{r.is_hazardous ? "Y" : "N"}</td>
                    <td style={tdStyle}>{r.is_fragile ? "Y" : "N"}</td>
                    <td style={tdStyle}>{r.priority}</td>
                    <td style={tdStyle}>
                      <button type="button" style={btnSmDanger} onClick={() => del(r.id)}>
                        Excluir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
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
const btnSecondary = { padding: "10px 14px", borderRadius: 10, border: "1px solid #334155", background: "#0B1220", color: "#E2E8F0", fontWeight: 600, cursor: "pointer" };
const errBox = { marginTop: 12, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10, whiteSpace: "pre-wrap" };
const tableWrap = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const table = { width: "100%", borderCollapse: "collapse", minWidth: 720 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B", verticalAlign: "top" };
const btnSmDanger = {
  padding: "4px 8px",
  borderRadius: 8,
  border: "1px solid #7f1d1d",
  background: "rgba(127,29,29,0.35)",
  color: "#E2E8F0",
  fontSize: 11,
  cursor: "pointer",
};
