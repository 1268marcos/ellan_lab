import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const INTERNAL = String(import.meta.env.VITE_INTERNAL_TOKEN || "").trim();

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const muted = { color: "#94A3B8", marginTop: 8 };
const codeInline = { color: "#CBD5E1", fontSize: 12 };
const btnPrimary = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const errBox = { marginTop: 12, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10, whiteSpace: "pre-wrap" };
const tableWrap = { marginTop: 8, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const table = { width: "100%", borderCollapse: "collapse", minWidth: 520 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };

export default function OpsRentalPlansPage() {
  const { hasRole } = useAuth();
  const isAdminOps = hasRole("admin_operacao");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const headers = useMemo(
    () => ({
      Accept: "application/json",
      ...(INTERNAL ? { "X-Internal-Token": INTERNAL } : {}),
    }),
    []
  );

  const load = useCallback(async () => {
    if (!INTERNAL || !isAdminOps) return;
    setLoading(true);
    setErr("");
    try {
      const u = new URL(`${BASE}/internal/rentals/plans`, window.location.origin);
      const r = await fetch(u.toString(), { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail === "string" ? j.detail : JSON.stringify(j?.detail || j));
      setItems(Array.isArray(j.items) ? j.items : []);
    } catch (e) {
      setErr(String(e.message || e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [headers, isAdminOps]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!isAdminOps) {
    return (
      <div style={pageStyle}>
        <section style={cardStyle}>
          <OpsPageTitleHeader title="OPS — Planos de aluguel (rental_plans)" />
          <p style={errBox}>Esta tela é somente leitura e requer perfil admin_operacao.</p>
        </section>
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Planos de aluguel ativos (rental_plans)" />
        <p style={muted}>
          Leitura; <code style={codeInline}>{BASE}/internal/rentals/plans</code> — planos com <code style={codeInline}>active</code>. Token{" "}
          <code style={codeInline}>VITE_INTERNAL_TOKEN</code> + proxy <code style={codeInline}>/api/op</code>.
        </p>
        {!INTERNAL ? <p style={errBox}>Configure VITE_INTERNAL_TOKEN.</p> : null}
        <button type="button" style={{ ...btnPrimary, marginTop: 8, opacity: loading || !INTERNAL ? 0.45 : 1 }} onClick={() => void load()} disabled={loading || !INTERNAL}>
          {loading ? "Carregando…" : "Atualizar"}
        </button>
        {err ? <pre style={errBox}>{err}</pre> : null}
        <div style={tableWrap}>
          <table style={table}>
            <thead>
              <tr>
                {["name", "locker_id", "slot_size", "amount_cents", "billing_cycle"].map((h) => (
                  <th key={h} style={th}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td style={tdStyle}>{row.name}</td>
                  <td style={tdStyle}>{row.locker_id ?? "—"}</td>
                  <td style={tdStyle}>{row.slot_size ?? "—"}</td>
                  <td style={tdStyle}>{row.amount_cents}</td>
                  <td style={tdStyle}>{row.billing_cycle}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && INTERNAL && !items.length ? <p style={muted}>Nenhum plano ativo.</p> : null}
      </section>
    </div>
  );
}
