import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  buttonPrimaryStyle,
  cardStyle,
  criticalBannerStyle,
  healthLocalFilterFieldStyle,
  healthLocalFilterInputStyle,
  healthLocalFilterRowStyle,
  okBannerStyle,
  pageStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_ANALYTICS_SERVICE_BASE_URL || "/api/analytics";
const API = `${BASE}/api/v1/analytics`;
const PAGE_VERSION = "ops/analytics/financial v0.1";

function actorHeaders() {
  return {
    "X-Actor-Roles": "admin_operacao",
    "X-Service-Name": "frontend_v0_ops",
  };
}

function brlFromReais(value) {
  if (value == null) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value));
}

function brlCents(cents) {
  if (cents == null) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(cents) / 100);
}

function pct(value) {
  if (value == null) return "—";
  return `${Number(value).toFixed(1)}%`;
}

async function apiGet(path) {
  const res = await fetch(`${API}${path}`, { headers: actorHeaders() });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || body.error || `HTTP ${res.status}`);
  return body;
}

async function apiPost(path, payload) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...actorHeaders() },
    body: JSON.stringify(payload),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || body.error || `HTTP ${res.status}`);
  return body;
}

export default function OpsFinancialAnalyticsPage() {
  const { hasAnyRole } = useAuth();
  const isAdmin = hasAnyRole(["admin.operacao", "admin.financeiro"]);

  const [lockerId, setLockerId] = useState("");
  const [month, setMonth] = useState("");
  const [profitability, setProfitability] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [refreshStatus, setRefreshStatus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams();
      if (lockerId) q.set("locker_id", lockerId);
      if (month) q.set("month", month);
      const suffix = q.toString() ? `?${q.toString()}` : "";
      const [p, d, k, s] = await Promise.all([
        apiGet(`/locker-profitability${suffix}`),
        apiGet("/financial-dashboard"),
        apiGet("/realtime-kpis"),
        apiGet("/refresh-status"),
      ]);
      setProfitability(p.items || []);
      setDashboard(d || null);
      setKpis(k || null);
      setRefreshStatus(s.items || []);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }, [lockerId, month]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onRefresh() {
    if (!isAdmin) return;
    setRefreshing(true);
    setMessage("");
    setError("");
    try {
      await apiPost("/refresh", { view: "all" });
      setMessage("Materialized views atualizadas com sucesso.");
      await load();
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setRefreshing(false);
    }
  }

  const kpiCards = useMemo(
    () => [
      { label: "Receita MTD", value: brlFromReais(dashboard?.revenue_mtd_brl) },
      { label: "Lucro MTD", value: brlFromReais(dashboard?.profit_mtd_brl) },
      { label: "Margem MTD", value: pct(dashboard?.margin_mtd_pct) },
      { label: "Pedidos 24h", value: String(kpis?.orders_last_24h ?? "—") },
      { label: "Receita 24h", value: brlFromReais(kpis?.revenue_last_24h) },
      { label: "Lockers offline", value: String(kpis?.offline_lockers ?? "—") },
    ],
    [dashboard, kpis],
  );

  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader
        title="Analytics financeiro"
        subtitle="Rentabilidade por locker, dashboard executivo e KPIs em tempo real."
        version={PAGE_VERSION}
      />

      <div style={toolbarStyle}>
        <Link to="/ops/finance/admin?tab=pnl" style={{ color: "#93c5fd", fontSize: 13 }}>
          Finance PnL
        </Link>
        {isAdmin ? (
          <button type="button" style={buttonPrimaryStyle} disabled={refreshing} onClick={() => void onRefresh()}>
            {refreshing ? "Atualizando…" : "Refresh manual (admin)"}
          </button>
        ) : null}
      </div>

      {error ? <div style={criticalBannerStyle}>{error}</div> : null}
      {message ? <div style={okBannerStyle}>{message}</div> : null}

      <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
        {kpiCards.map((card) => (
          <div key={card.label} style={cardStyle}>
            <div style={{ fontSize: 12, color: "#94a3b8" }}>{card.label}</div>
            <div style={{ fontSize: 22, fontWeight: 700, marginTop: 4 }}>{loading ? "…" : card.value}</div>
          </div>
        ))}
      </div>

      <section style={{ ...cardStyle, marginTop: 14 }}>
        <h3 style={{ margin: 0 }}>Status dos refreshes</h3>
        <table style={{ ...tableStyle, marginTop: 10 }}>
          <thead>
            <tr>
              <th style={thStyle}>View</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Início</th>
              <th style={thStyle}>Duração</th>
            </tr>
          </thead>
          <tbody>
            {refreshStatus.map((row) => (
              <tr key={row.view_name}>
                <td style={tdStyle}>{row.view_name}</td>
                <td style={tdStyle}>{row.status}</td>
                <td style={tdStyle}>{row.started_at ? new Date(row.started_at).toLocaleString("pt-BR") : "—"}</td>
                <td style={tdStyle}>{row.duration_ms != null ? `${row.duration_ms} ms` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section style={{ ...cardStyle, marginTop: 14 }}>
        <h3 style={{ margin: 0 }}>Rentabilidade por locker</h3>
        <div style={healthLocalFilterRowStyle}>
          <label style={healthLocalFilterFieldStyle}>
            locker_id
            <input
              style={healthLocalFilterInputStyle}
              value={lockerId}
              onChange={(e) => setLockerId(e.target.value)}
              placeholder="opcional"
            />
          </label>
          <label style={healthLocalFilterFieldStyle}>
            mês
            <input
              style={healthLocalFilterInputStyle}
              type="month"
              value={month ? month.slice(0, 7) : ""}
              onChange={(e) => setMonth(e.target.value ? `${e.target.value}-01` : "")}
            />
          </label>
          <button type="button" style={buttonPrimaryStyle} onClick={() => void load()}>
            Filtrar
          </button>
        </div>
        <table style={{ ...tableStyle, marginTop: 10 }}>
          <thead>
            <tr>
              <th style={thStyle}>Locker</th>
              <th style={thStyle}>Mês</th>
              <th style={thStyle}>Receita</th>
              <th style={thStyle}>Custos</th>
              <th style={thStyle}>Lucro</th>
              <th style={thStyle}>Margem</th>
            </tr>
          </thead>
          <tbody>
            {profitability.map((row) => (
              <tr key={`${row.locker_id}-${row.month}`}>
                <td style={tdStyle}>{row.locker_id}</td>
                <td style={tdStyle}>{row.month}</td>
                <td style={tdStyle}>{brlCents(row.total_revenue_cents)}</td>
                <td style={tdStyle}>{brlCents(row.total_costs_cents)}</td>
                <td style={tdStyle}>{brlCents(row.net_profit_cents)}</td>
                <td style={tdStyle}>{pct(row.net_margin_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
