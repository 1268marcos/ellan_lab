import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { fetchOpsMonitoringSummary } from "../api/opsMonitoringApi";
import {
  cardStyle,
  crossShortcutLinkStyle,
  mutedTextStyle,
  pageStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

function fmtAge(sec) {
  const n = Number(sec || 0);
  if (n < 60) return `${n}s`;
  if (n < 3600) return `${Math.round(n / 60)}min`;
  return `${(n / 3600).toFixed(1)}h`;
}

function kpiCard(label, value, sub, alert) {
  return (
    <div
      style={{
        ...cardStyle,
        borderColor: alert ? "rgba(248,113,113,0.75)" : cardStyle.border,
      }}
    >
      <div style={{ fontSize: 12, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.04em" }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 800, marginTop: 6 }}>{value}</div>
      {sub ? <div style={{ ...mutedTextStyle, fontSize: 13 }}>{sub}</div> : null}
    </div>
  );
}

export default function OpsMonitoringDashboardPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchOpsMonitoringSummary(token);
      setSummary(data);
    } catch (exc) {
      setError(exc?.message || "Falha ao carregar monitoramento OPS.");
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const credits = summary?.credits_health || {};
  const recon = summary?.reconciliation_lag || {};
  const runtime = summary?.runtime_deadlocks || {};
  const alerts = Array.isArray(summary?.alerts) ? summary.alerts : [];

  const statusDistribution = useMemo(() => {
    const dist = recon.status_distribution || {};
    return Object.entries(dist).sort((a, b) => b[1] - a[1]);
  }, [recon.status_distribution]);

  return (
    <div style={pageStyle} data-testid="ops-monitoring-dashboard">
      <OpsPageTitleHeader
        title="Monitoramento OPS"
        subtitle="Créditos · reconciliação · alocações presas (order_pickup_service)"
        versionLabel="ops/monitoring v1"
      />

      <div style={{ ...toolbarStyle, marginBottom: 16 }}>
        <button type="button" onClick={load} disabled={loading} style={crossShortcutLinkStyle}>
          {loading ? "Atualizando…" : "Atualizar"}
        </button>
        <Link to="/ops/reconciliation" style={crossShortcutLinkStyle}>
          Reconciliação manual
        </Link>
        <Link to="/ops/health" style={crossShortcutLinkStyle}>
          Saúde OPS
        </Link>
        <Link to="/ops/runtime/sync" style={crossShortcutLinkStyle}>
          Runtime sync
        </Link>
      </div>

      {loading && !summary ? (
        <div style={{ ...cardStyle, marginBottom: 16, color: "#cbd5e1" }}>Carregando monitoramento…</div>
      ) : null}

      {error ? (
        <div style={{ ...cardStyle, borderColor: "rgba(248,113,113,0.6)", color: "#fecaca", marginBottom: 16 }}>
          <p style={{ margin: "0 0 12px" }}>{error}</p>
          <button type="button" onClick={load} disabled={loading} style={crossShortcutLinkStyle}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {!loading && !summary && !error ? (
        <div style={{ ...cardStyle, marginBottom: 16, color: "#cbd5e1" }}>
          Nenhum dado carregado. Clique em Atualizar.
        </div>
      ) : null}

      {summary ? (
        <>
          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", marginBottom: 16 }}>
            {kpiCard(
              "Status geral",
              summary.ok ? "OK" : "ALERTA",
              summary.as_of ? `atualizado ${summary.as_of}` : "",
              !summary.ok,
            )}
            {kpiCard("Créditos totais", credits.total_credits ?? "—", `USED hoje: ${credits.used_today ?? 0}`)}
            {kpiCard(
              "Reconciliação aberta",
              recon.open_pending_count ?? 0,
              `idade máx ${fmtAge(recon.max_pending_age_sec)}`,
              recon.alert,
            )}
            {kpiCard(
              "Alocações presas",
              runtime.stuck_count ?? 0,
              `limiar ${fmtAge(runtime.lock_age_threshold_sec)}`,
              runtime.alert,
            )}
          </div>

          {alerts.length ? (
            <div style={{ ...cardStyle, marginBottom: 16 }}>
              <h3 style={{ margin: "0 0 10px" }}>Alertas</h3>
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {alerts.map((a) => (
                  <li key={a.code} style={{ marginBottom: 6 }}>
                    <strong>{a.severity}</strong> — {a.message}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
            <div style={cardStyle}>
              <h3 style={{ marginTop: 0 }}>Créditos</h3>
              <p style={mutedTextStyle}>Expirados hoje: {credits.expired_today ?? 0}</p>
              <p style={mutedTextStyle}>
                Expirando em {credits.expiring_within_days ?? 7}d: {credits.available_expiring_within_days ?? 0}
              </p>
              {(credits.top_users_expiring || []).slice(0, 5).map((u) => (
                <div key={u.user_id} style={{ fontSize: 13, marginTop: 8 }}>
                  <code>{u.user_id}</code> — {u.credits_count} crédito(s), {u.total_amount_cents}c
                </div>
              ))}
            </div>

            <div style={cardStyle}>
              <h3 style={{ marginTop: 0 }}>Reconciliação</h3>
              <p style={mutedTextStyle}>Média idade pendente: {fmtAge(recon.avg_pending_age_sec)}</p>
              <p style={mutedTextStyle}>PROCESSING obsoleto: {recon.stale_processing_count ?? 0}</p>
              {statusDistribution.map(([status, count]) => (
                <div key={status} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginTop: 6 }}>
                  <span>{status}</span>
                  <strong>{count}</strong>
                </div>
              ))}
            </div>

            <div style={cardStyle}>
              <h3 style={{ marginTop: 0 }}>Runtime / alocações</h3>
              <p style={mutedTextStyle}>Itens com estado ativo sem progresso &gt; 1h.</p>
              {(runtime.items || []).slice(0, 8).map((item) => (
                <div key={item.allocation_id} style={{ fontSize: 12, marginTop: 8, color: "#cbd5e1" }}>
                  {item.allocation_id} · pedido {item.order_id} · {item.state} · {fmtAge(item.age_sec)}
                </div>
              ))}
              {!runtime.items?.length ? <p style={mutedTextStyle}>Nenhuma alocação presa.</p> : null}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
