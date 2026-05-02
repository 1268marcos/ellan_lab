import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsActionButton from "../components/OpsActionButton";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const API_CHUNK = 300;

function parseError(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

function filterByDateRange(items, dateFrom, dateTo) {
  const fromT = String(dateFrom || "").trim() ? new Date(dateFrom).getTime() : null;
  const toT = String(dateTo || "").trim() ? new Date(dateTo).getTime() : null;
  if (fromT != null && Number.isNaN(fromT)) return items;
  if (toT != null && Number.isNaN(toT)) return items;
  return items.filter((ev) => {
    const t = new Date(ev.occurred_at).getTime();
    if (Number.isNaN(t)) return false;
    if (fromT != null && t < fromT) return false;
    if (toT != null && t > toT) return false;
    return true;
  });
}

export default function OpsReturnTrackingPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [returnLegId, setReturnLegId] = useState(() => String(searchParams.get("return_leg_id") || searchParams.get("leg_id") || "").trim());
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [total, setTotal] = useState(0);
  const [rows, setRows] = useState([]);
  const [clientFiltered, setClientFiltered] = useState(null);

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  useEffect(() => {
    const q = String(searchParams.get("return_leg_id") || searchParams.get("leg_id") || "").trim();
    if (q) setReturnLegId(q);
  }, [searchParams]);

  const hasDateFilter = Boolean(String(dateFrom || "").trim() || String(dateTo || "").trim());

  const fetchServerPage = useCallback(
    async (leg, off, lim) => {
      const params = new URLSearchParams();
      params.set("limit", String(Math.max(1, Math.min(300, lim))));
      params.set("offset", String(Math.max(0, off)));
      const endpoint = `${ORDER_PICKUP_BASE}/logistics/return-legs/${encodeURIComponent(leg)}/tracking-events?${params}`;
      const res = await fetch(endpoint, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseError(data, "Falha ao carregar eventos de tracking."));
      setRows(Array.isArray(data.items) ? data.items : []);
      setTotal(Number(data.total) || 0);
    },
    [authHeaders],
  );

  const load = useCallback(async () => {
    const leg = String(returnLegId || "").trim();
    if (!leg) {
      setError("Informe o return_leg_id.");
      return;
    }
    if (!token) {
      setError("Sessao necessaria.");
      return;
    }
    setLoading(true);
    setError("");
    setClientFiltered(null);
    try {
      if (!hasDateFilter) {
        await fetchServerPage(leg, offset, limit);
      } else {
        const merged = [];
        let off = 0;
        let reportedTotal = 0;
        while (off < 10000) {
          const params = new URLSearchParams();
          params.set("limit", String(API_CHUNK));
          params.set("offset", String(off));
          const endpoint = `${ORDER_PICKUP_BASE}/logistics/return-legs/${encodeURIComponent(leg)}/tracking-events?${params}`;
          const res = await fetch(endpoint, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
          const data = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(parseError(data, "Falha ao carregar eventos de tracking."));
          const chunk = Array.isArray(data.items) ? data.items : [];
          merged.push(...chunk);
          reportedTotal = Number(data.total) || merged.length;
          off += chunk.length;
          if (chunk.length === 0 || off >= reportedTotal) break;
        }
        const filtered = filterByDateRange(merged, dateFrom, dateTo);
        setClientFiltered(filtered);
        setTotal(filtered.length);
        const lim = Math.max(1, Math.min(300, Number(limit) || 50));
        const offv = Math.max(0, Number(offset) || 0);
        setRows(filtered.slice(offv, offv + lim));
      }
    } catch (e) {
      setRows([]);
      setTotal(0);
      setError(String(e?.message || e || "Erro ao carregar."));
    } finally {
      setLoading(false);
    }
  }, [returnLegId, dateFrom, dateTo, limit, offset, hasDateFilter, token, authHeaders, fetchServerPage]);

  useEffect(() => {
    if (!hasDateFilter || clientFiltered == null) return;
    const lim = Math.max(1, Math.min(300, Number(limit) || 50));
    const offv = Math.max(0, Number(offset) || 0);
    setRows(clientFiltered.slice(offv, offv + lim));
  }, [offset, limit, hasDateFilter, clientFiltered]);

  function applyLegToUrl() {
    const leg = String(returnLegId || "").trim();
    const next = new URLSearchParams(searchParams);
    if (leg) next.set("return_leg_id", leg);
    else next.delete("return_leg_id");
    setSearchParams(next, { replace: true });
  }

  const limPage = Math.max(1, Math.min(300, Number(limit) || 50));
  const canPrev = offset > 0;
  const canNext = offset + limPage < total;

  async function goRelative(delta) {
    const leg = String(returnLegId || "").trim();
    if (!leg || !token) return;
    const next = Math.max(0, offset + delta);
    setOffset(next);
    if (!hasDateFilter) {
      setLoading(true);
      setError("");
      try {
        await fetchServerPage(leg, next, limit);
      } catch (e) {
        setError(String(e?.message || e || "Erro ao carregar."));
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Return tracking events" />
        <p style={mutedStyle}>Proxy <code style={{ color: "#93C5FD" }}>/api/op</code> (order pickup, ex.: porta 8010 no dev proxy).</p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            return_leg_id
            <input style={inputStyle} value={returnLegId} onChange={(e) => setReturnLegId(e.target.value)} placeholder="UUID da perna" />
          </label>
          <label style={labelStyle}>
            date_from
            <input style={inputStyle} type="datetime-local" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </label>
          <label style={labelStyle}>
            date_to
            <input style={inputStyle} type="datetime-local" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </label>
          <label style={labelStyle}>
            limit
            <input style={inputStyle} type="number" min={1} max={300} value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
          </label>
          <label style={labelStyle}>
            offset
            <input style={inputStyle} type="number" min={0} value={offset} onChange={(e) => setOffset(Number(e.target.value))} />
          </label>
        </div>

        <div style={actionsRowStyle}>
          <OpsActionButton type="button" variant="primary" disabled={loading} onClick={() => void load()}>
            {loading ? "Carregando…" : "Carregar"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => applyLegToUrl()}>
            Sincronizar URL
          </OpsActionButton>
          <Link
            to={returnLegId.trim() ? `/ops/logistics/returns?leg_id=${encodeURIComponent(returnLegId.trim())}` : "/ops/logistics/returns"}
            style={backLinkStyle}
          >
            Voltar ao return leg (returns)
          </Link>
        </div>

        {hasDateFilter ? (
          <p style={mutedStyleSmall}>
            Com date_from/date_to o frontend busca todas as páginas (até 10k) e filtra por occurred_at; paginação abaixo é sobre o resultado filtrado.
          </p>
        ) : null}

        {error ? <div style={errorStyle}>{error}</div> : null}

        <div style={tableWrapStyle}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>event_code</th>
                <th style={thStyle}>description</th>
                <th style={thStyle}>location</th>
                <th style={thStyle}>occurred_at</th>
                <th style={thStyle}>source</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && !loading ? (
                <tr>
                  <td colSpan={5} style={tdStyle}>
                    Nenhum evento (carregue com um return_leg_id válido).
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.event_code}</td>
                    <td style={tdStyle}>{row.description ?? "—"}</td>
                    <td style={tdStyle}>{row.location_name ?? "—"}</td>
                    <td style={tdStyle}>{row.occurred_at ? new Date(row.occurred_at).toLocaleString("pt-BR") : "—"}</td>
                    <td style={tdStyle}>{row.source}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div style={pagerStyle}>
          <OpsActionButton type="button" variant="secondary" disabled={!canPrev || loading} onClick={() => void goRelative(-limPage)}>
            Anterior
          </OpsActionButton>
          <span style={mutedStyleSmall}>
            offset={offset} limit={limit} total={total}
            {clientFiltered != null ? ` (filtrados ${clientFiltered.length})` : ""}
          </span>
          <OpsActionButton type="button" variant="secondary" disabled={!canNext || loading} onClick={() => void goRelative(limPage)}>
            Próxima
          </OpsActionButton>
        </div>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8 };
const mutedStyleSmall = { color: "#94A3B8", fontSize: 12 };
const filtersGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10, marginTop: 12 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const actionsRowStyle = { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginTop: 12 };
const backLinkStyle = { color: "#93C5FD", fontWeight: 600, textDecoration: "none", padding: "8px 10px", border: "1px solid #334155", borderRadius: 8 };
const errorStyle = { marginTop: 12, background: "rgba(220, 38, 38, 0.12)", color: "#FCA5A5", border: "1px solid rgba(220, 38, 38, 0.45)", borderRadius: 10, padding: 10 };
const tableWrapStyle = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 720 };
const thStyle = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
const pagerStyle = { display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginTop: 14 };
