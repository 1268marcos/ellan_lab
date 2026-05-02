import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const INTERNAL = String(import.meta.env.VITE_INTERNAL_TOKEN || "").trim();

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const muted = { color: "#94A3B8", marginTop: 8 };
const codeInline = { color: "#CBD5E1", fontSize: 12 };
const toolbar = { display: "flex", flexWrap: "wrap", gap: 12, marginTop: 12, alignItems: "flex-end" };
const lbl = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inp = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const btnPrimary = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const errBox = { marginTop: 12, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10, whiteSpace: "pre-wrap" };
const tableWrap = { marginTop: 8, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const table = { width: "100%", borderCollapse: "collapse", minWidth: 640 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
const linkStyle = { color: "#93C5FD", textDecoration: "underline" };

function buildHeaders() {
  return {
    Accept: "application/json",
    ...(INTERNAL ? { "X-Internal-Token": INTERNAL } : {}),
  };
}

export default function OpsRentalContractsPage() {
  const { id: contractId } = useParams();
  const [status, setStatus] = useState("");
  const [lockerId, setLockerId] = useState("");
  const [renterUserId, setRenterUserId] = useState("");
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [detail, setDetail] = useState(null);
  const headers = useMemo(() => buildHeaders(), []);

  const loadList = useCallback(async () => {
    if (!INTERNAL) return;
    setLoading(true);
    setErr("");
    try {
      const u = new URL(`${BASE}/internal/rentals/contracts`, window.location.origin);
      if (status.trim()) u.searchParams.set("status", status.trim());
      if (lockerId.trim()) u.searchParams.set("locker_id", lockerId.trim());
      if (renterUserId.trim()) u.searchParams.set("renter_user_id", renterUserId.trim());
      const r = await fetch(u.toString(), { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail === "string" ? j.detail : JSON.stringify(j?.detail || j));
      setItems(Array.isArray(j.items) ? j.items : []);
      setTotal(typeof j.total === "number" ? j.total : 0);
    } catch (e) {
      setErr(String(e.message || e));
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [headers, status, lockerId, renterUserId]);

  const loadDetail = useCallback(async () => {
    if (!INTERNAL || !contractId) return;
    setLoading(true);
    setErr("");
    try {
      const u = `${BASE}/internal/rentals/contracts/${encodeURIComponent(contractId)}`;
      const r = await fetch(new URL(u, window.location.origin).toString(), { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail === "string" ? j.detail : JSON.stringify(j?.detail || j));
      setDetail(j);
    } catch (e) {
      setErr(String(e.message || e));
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [headers, contractId]);

  useEffect(() => {
    if (contractId) void loadDetail();
    else void loadList();
  }, [contractId, loadDetail, loadList]);

  if (contractId) {
    return (
      <div style={pageStyle}>
        <section style={cardStyle}>
          <OpsPageTitleHeader title={`OPS — Contrato de aluguel (${contractId})`} />
          <p style={muted}>
            <code style={codeInline}>{BASE}/internal/rentals/contracts/&#123;id&#125;</code> — header{" "}
            <code style={codeInline}>X-Internal-Token</code> (<code style={codeInline}>VITE_INTERNAL_TOKEN</code>). Proxy{" "}
            <code style={codeInline}>/api/op</code>.
          </p>
          <p style={muted}>
            <Link to="/ops/rentals/contracts" style={linkStyle}>
              Voltar à listagem
            </Link>
          </p>
          {!INTERNAL ? <p style={errBox}>Configure VITE_INTERNAL_TOKEN para carregar dados internos.</p> : null}
          {err ? <pre style={errBox}>{err}</pre> : null}
          {loading ? <p style={muted}>Carregando…</p> : null}
          {detail && !loading ? (
            <pre style={{ ...tdStyle, marginTop: 12, overflow: "auto", maxHeight: "70vh", background: "#020617", padding: 12, borderRadius: 12 }}>
              {JSON.stringify(detail, null, 2)}
            </pre>
          ) : null}
        </section>
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Contratos de aluguel (rental_contracts)" />
        <p style={muted}>
          <code style={codeInline}>{BASE}/internal/rentals/contracts</code> — filtros opcionais; token interno obrigatório. Proxy{" "}
          <code style={codeInline}>/api/op</code> (order_pickup_service).
        </p>
        {!INTERNAL ? <p style={errBox}>Configure VITE_INTERNAL_TOKEN para carregar dados internos.</p> : null}
        <div style={toolbar}>
          <label style={lbl}>
            status
            <input value={status} onChange={(e) => setStatus(e.target.value)} placeholder="ACTIVE, PENDING…" style={{ ...inp, minWidth: 140 }} />
          </label>
          <label style={lbl}>
            locker_id
            <input value={lockerId} onChange={(e) => setLockerId(e.target.value)} style={{ ...inp, minWidth: 200 }} />
          </label>
          <label style={lbl}>
            renter_user_id
            <input value={renterUserId} onChange={(e) => setRenterUserId(e.target.value)} style={{ ...inp, minWidth: 200 }} />
          </label>
          <button type="button" style={{ ...btnPrimary, opacity: loading || !INTERNAL ? 0.45 : 1 }} onClick={() => void loadList()} disabled={loading || !INTERNAL}>
            {loading ? "Carregando…" : "Atualizar"}
          </button>
        </div>
        {err ? <pre style={errBox}>{err}</pre> : null}
        <p style={{ ...muted, fontSize: 11 }}>Total: {total}</p>
        <div style={tableWrap}>
          <table style={table}>
            <thead>
              <tr>
                {["id", "locker_id", "renter_name", "status", "billing_cycle", "amount_cents", "next_billing_at", "detalhe"].map((h) => (
                  <th key={h} style={th}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td style={tdStyle}>{row.id}</td>
                  <td style={tdStyle}>{row.locker_id}</td>
                  <td style={tdStyle}>{row.renter_name ?? "—"}</td>
                  <td style={tdStyle}>{row.status}</td>
                  <td style={tdStyle}>{row.billing_cycle}</td>
                  <td style={tdStyle}>{row.amount_cents}</td>
                  <td style={tdStyle}>{row.next_billing_at ?? "—"}</td>
                  <td style={tdStyle}>
                    <Link to={`/ops/rentals/contracts/${encodeURIComponent(row.id)}`} style={linkStyle}>
                      abrir
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && INTERNAL && !items.length ? <p style={muted}>Nenhum contrato encontrado.</p> : null}
      </section>
    </div>
  );
}
