import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";

function toHeaders(token) {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(INTERNAL_TOKEN ? { "X-Internal-Token": INTERNAL_TOKEN } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function parseApiError(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

export default function OpsPartnersHypertablesPage() {
  const { token } = useAuth();
  const headers = useMemo(() => toHeaders(token), [token]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState("");
  const [lastHttpStatus, setLastHttpStatus] = useState(null);
  const [copyStatus, setCopyStatus] = useState("");
  const playbookPath = "docs/FA5_PLAYBOOK_PLANTAO_1PAGINA.md";
  const playbookQuickContent = `FA-5 Playbook de Plantao (1 Pagina)

Quando usar:
- Incidente em /ops/partners/hypertables
- Falha em recompute FA-5 (revenue-recognition, kpi/daily, pnl)
- Falha em models/testes dbt financeiros

Objetivo do plantao:
1) SMOKE_OK no Timescale FA-5
2) recompute admin funcionando
3) dbt run/test em verde
4) divergencias contabeis sob controle

Triage rapido:
1) docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
2) cd /home/marcos/ellan_lab && ./02_docker/run_fa5_timescale_smoke.sh
3) curl "http://localhost:8020/admin/fiscal/timescale/status" -H "X-Internal-Token: <TOKEN>"

Arvore de decisao:

Caso A - billing_fiscal_service DOWN:
docker compose -f /home/marcos/ellan_lab/02_docker/docker-compose.yml up -d --build billing_fiscal_service

Caso B - SMOKE_FAIL:
docker cp /home/marcos/ellan_lab/02_docker/postgres_central/ops/enable_fa5_hypertables.sql postgres_central:/tmp/enable_fa5_hypertables.sql
docker exec postgres_central sh -lc "psql -U admin -d locker_central -v ON_ERROR_STOP=1 -f /tmp/enable_fa5_hypertables.sql"
Reexecutar smoke.

Caso C - endpoint 403/422:
- Validar X-Internal-Token
- Confirmar VITE_INTERNAL_TOKEN no frontend

Caso D - dbt falha:
curl -X POST "http://localhost:8020/admin/fiscal/revenue-recognition/recompute?date_ref=<YYYY-MM-DD>" -H "X-Internal-Token: <TOKEN>"
curl -X POST "http://localhost:8020/admin/fiscal/kpi/daily/recompute?date_ref=<YYYY-MM-DD>" -H "X-Internal-Token: <TOKEN>"
curl -X POST "http://localhost:8020/admin/fiscal/pnl/recompute?month=<YYYY-MM>" -H "X-Internal-Token: <TOKEN>"

cd /home/marcos/ellan_lab/01_source/backend/billing_fiscal_service/dbt_financial
. .venv/bin/activate
dbt run --select marts.partner_revenue_monthly marts.locker_pnl marts.company_mrr_trend
dbt test --select marts.partner_revenue_monthly marts.locker_pnl marts.company_mrr_trend

Checklist de saida:
- SMOKE_OK
- /admin/fiscal/timescale/status OK
- recomputes FA-5 sem erro
- dbt run/test sem erro
- ledger-compat/audit?only_mismatches=true sem aumento anormal

Referencia completa:
- docs/FA5_RUNBOOK_TIMESCALE_DBT.md
- docs/FA5_PLAYBOOK_PLANTAO_1PAGINA.md`;

  async function loadStatus() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${BILLING_BASE}/admin/fiscal/timescale/status`, {
        method: "GET",
        headers,
      });
      setLastHttpStatus(response.status);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        if (response.status === 403 || response.status === 422) {
          throw new Error("Token interno ausente/inválido (422/403). Configure VITE_INTERNAL_TOKEN com o valor correto.");
        }
        throw new Error(parseApiError(data, "Falha ao carregar status de hypertables."));
      }
      setPayload(data || null);
      setLastUpdatedAt(new Date().toLocaleString("pt-BR"));
    } catch (err) {
      const raw = String(err?.message || err || "Erro desconhecido");
      if (lastHttpStatus === null) {
        setLastHttpStatus("NETWORK_ERROR");
      }
      if (raw.toLowerCase().includes("failed to fetch")) {
        setError("Falha de conexão com billing_fiscal_service. Verifique se o container está ativo na porta 8020.");
      } else {
        setError(raw);
      }
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleCopyPlaybookContent() {
    try {
      await navigator.clipboard.writeText(playbookQuickContent);
      setCopyStatus("Conteúdo do playbook copiado.");
      window.setTimeout(() => setCopyStatus(""), 1800);
    } catch (_) {
      setCopyStatus("Falha ao copiar automaticamente. Tente novamente.");
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0, marginBottom: 8 }}>OPS - Partners Hypertables</h1>
        <p style={mutedStyle}>
          Visão organizada das hypertables/policies do bloco FA-5 (Timescale). Esta tela consolida o smoke operacional.
        </p>
        <section style={diagCardStyle}>
          <h3 style={{ marginTop: 0, marginBottom: 8 }}>Diagnóstico rápido</h3>
          <div style={diagGridStyle}>
            <DiagItem label="Base URL (VITE_BILLING_FISCAL_BASE_URL)" value={BILLING_BASE} />
            <DiagItem label="Token interno presente" value={INTERNAL_TOKEN ? "SIM" : "NÃO"} />
            <DiagItem label="Último status HTTP" value={lastHttpStatus === null ? "-" : String(lastHttpStatus)} />
          </div>
          <div style={diagActionsStyle}>
            <Link to="/ops/updates" style={diagLinkStyle}>
              Abrir playbook no OPS Updates
            </Link>
            <button type="button" style={diagCopyButtonStyle} onClick={() => void handleCopyPlaybookContent()}>
              Copiar conteúdo do playbook
            </button>
            <small style={mutedStyle}>`{playbookPath}`</small>
          </div>
          {copyStatus ? <small style={copyStatusStyle}>{copyStatus}</small> : null}
        </section>
        <div style={actionsStyle}>
          <button type="button" style={buttonPrimaryStyle} onClick={() => void loadStatus()} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar status Timescale"}
          </button>
          <Link to="/ops/partners/billing-monitor" style={linkButtonStyle}>
            Voltar para billing-monitor
          </Link>
          {lastUpdatedAt ? <small style={mutedStyle}>Última atualização: {lastUpdatedAt}</small> : null}
        </div>
        {error ? <pre style={errorStyle}>{error}</pre> : null}
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Resumo de smoke</h2>
        {!payload ? (
          <p style={mutedStyle}>Clique em "Atualizar status Timescale" para carregar o status.</p>
        ) : (
          <div style={kpiGridStyle}>
            <Kpi label="Smoke Result" value={payload.smoke_result || "-"} />
            <Kpi label="Extension" value={payload.ext_ok ? `OK (${payload.extension?.extversion || "?"})` : "Indisponível"} />
            <Kpi label="Hypertables" value={payload.hypertable_count ?? 0} />
            <Kpi label="Policies Jobs" value={payload.policy_count ?? 0} />
            <Kpi label="Dedupe Indexes" value={payload.dedupe_index_count ?? 0} />
          </div>
        )}
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Hypertables</h2>
        <TableWrap>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>schema</th>
                <th style={thStyle}>hypertable_name</th>
              </tr>
            </thead>
            <tbody>
              {(payload?.hypertables || []).length ? (
                payload.hypertables.map((row) => (
                  <tr key={`${row.hypertable_schema}-${row.hypertable_name}`}>
                    <td style={tdStyle}>{row.hypertable_schema}</td>
                    <td style={tdStyle}>{row.hypertable_name}</td>
                  </tr>
                ))
              ) : (
                <tr><td style={tdStyle} colSpan={2}>Sem hypertables encontradas para FA-5.</td></tr>
              )}
            </tbody>
          </table>
        </TableWrap>
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Policies / Jobs</h2>
        <TableWrap>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>hypertable_name</th>
                <th style={thStyle}>proc_name</th>
                <th style={thStyle}>schedule_interval</th>
              </tr>
            </thead>
            <tbody>
              {(payload?.jobs || []).length ? (
                payload.jobs.map((row) => (
                  <tr key={`${row.hypertable_name}-${row.proc_name}`}>
                    <td style={tdStyle}>{row.hypertable_name}</td>
                    <td style={tdStyle}>{row.proc_name}</td>
                    <td style={tdStyle}>{row.schedule_interval || "-"}</td>
                  </tr>
                ))
              ) : (
                <tr><td style={tdStyle} colSpan={3}>Sem jobs encontrados para FA-5.</td></tr>
              )}
            </tbody>
          </table>
        </TableWrap>
      </section>
    </div>
  );
}

function TableWrap({ children }) {
  return <div style={{ overflowX: "auto" }}>{children}</div>;
}

function Kpi({ label, value }) {
  return (
    <article style={kpiStyle}>
      <strong style={{ color: "#BFDBFE", fontSize: 18 }}>{value}</strong>
      <small style={{ color: "#94A3B8" }}>{label}</small>
    </article>
  );
}

function DiagItem({ label, value }) {
  return (
    <article style={diagItemStyle}>
      <small style={{ color: "#93C5FD" }}>{label}</small>
      <strong style={{ color: "#E2E8F0" }}>{value}</strong>
    </article>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif", display: "grid", gap: 12 };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 0 };
const diagCardStyle = { border: "1px solid #334155", borderRadius: 12, padding: 10, background: "#0B1220", marginTop: 10 };
const diagGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 8 };
const diagItemStyle = { display: "grid", gap: 4, border: "1px solid #334155", borderRadius: 10, background: "#020617", padding: 8 };
const diagActionsStyle = { marginTop: 10, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" };
const diagLinkStyle = { textDecoration: "none", padding: "8px 10px", borderRadius: 10, border: "1px solid rgba(59,130,246,0.45)", background: "rgba(59,130,246,0.12)", color: "#BFDBFE", fontWeight: 700, fontSize: 12 };
const diagCopyButtonStyle = { padding: "8px 10px", borderRadius: 10, border: "1px solid rgba(148,163,184,0.5)", background: "transparent", color: "#E2E8F0", cursor: "pointer", fontWeight: 700, fontSize: 12 };
const copyStatusStyle = { marginTop: 8, color: "#93C5FD", display: "block" };
const actionsStyle = { marginTop: 10, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" };
const buttonPrimaryStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const linkButtonStyle = { textDecoration: "none", padding: "10px 14px", borderRadius: 10, border: "1px solid rgba(148,163,184,0.5)", color: "#E2E8F0", fontWeight: 600 };
const errorStyle = { marginTop: 10, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10 };
const kpiGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 8 };
const kpiStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 10, padding: 10, display: "grid", gap: 4 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 680 };
const thStyle = { textAlign: "left", borderBottom: "1px solid rgba(255,255,255,0.14)", padding: "8px 10px", fontSize: 12 };
const tdStyle = { borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "8px 10px", verticalAlign: "top", fontSize: 12 };
