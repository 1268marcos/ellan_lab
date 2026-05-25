import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  buttonGhostStyle,
  buttonPrimaryStyle,
  cardStyle,
  criticalBannerStyle,
  crossShortcutLinkStyle,
  healthLocalFilterFieldStyle,
  healthLocalFilterInputStyle,
  healthLocalFilterRowStyle,
  mutedTextStyle,
  okBannerStyle,
  opsSanityCardStyle,
  pageStyle,
  summary24hHeaderStyle,
  summary24hHintStyle,
  tabButtonStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_ORDER_PICKUP_ADMIN_BASE_URL || "/api/opa";
const API = `${BASE}/v1/order-pickup-admin`;
const PAGE_VERSION = "ops/workers/admin v0.2";

const TAB_ITEMS = [
  { id: "overview", label: "Visão geral" },
  { id: "domain", label: "Domain outbox" },
  { id: "lifecycle", label: "Lifecycle" },
  { id: "inventory", label: "Inventory sync" },
  { id: "dlq", label: "Dead letter" },
];

const WORKER_STATUS_META = {
  PENDING: { bg: "rgba(199,146,0,0.22)", border: "rgba(199,146,0,0.45)", color: "#fde68a" },
  PROCESSING: { bg: "rgba(27,88,131,0.22)", border: "rgba(27,88,131,0.45)", color: "#bae6fd" },
  PUBLISHED: { bg: "rgba(22,101,52,0.35)", border: "rgba(34,197,94,0.55)", color: "#bbf7d0" },
  SYNCED: { bg: "rgba(22,101,52,0.35)", border: "rgba(34,197,94,0.55)", color: "#bbf7d0" },
  EXECUTED: { bg: "rgba(22,101,52,0.35)", border: "rgba(34,197,94,0.55)", color: "#bbf7d0" },
  FAILED: { bg: "rgba(179,38,30,0.20)", border: "rgba(179,38,30,0.45)", color: "#fecaca" },
  DEAD_LETTER: { bg: "rgba(120,53,15,0.35)", border: "rgba(251,191,36,0.5)", color: "#fde68a" },
  EXECUTING: { bg: "rgba(95,61,196,0.22)", border: "rgba(95,61,196,0.45)", color: "#e9d5ff" },
  CANCELLED: { bg: "rgba(107,107,107,0.22)", border: "rgba(107,107,107,0.45)", color: "#e2e8f0" },
};

const kpiCardStyle = {
  borderRadius: 12,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.55)",
  padding: "12px 14px",
  minWidth: 140,
};

const kpiGridStyle = {
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
  marginTop: 4,
};

function parseError(payload, fallback = "Falha na API workers.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicação com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexão (${endpoint}). Verifique proxy ${BASE} (porta 8018) e order-pickup-admin.`;
  }
  return raw;
}

function workerStatusBadge(status) {
  const key = String(status || "").toUpperCase();
  const meta = WORKER_STATUS_META[key] || {
    bg: "rgba(255,255,255,0.08)",
    border: "rgba(255,255,255,0.18)",
    color: "#e2e8f0",
  };
  return {
    display: "inline-block",
    padding: "4px 10px",
    borderRadius: 999,
    border: `1px solid ${meta.border}`,
    background: meta.bg,
    color: meta.color,
    fontSize: 11,
    fontWeight: 700,
    whiteSpace: "nowrap",
  };
}

function sumCounts(counts) {
  return Object.values(counts || {}).reduce((n, v) => n + Number(v || 0), 0);
}

function filterByStatus(rows, statusFilter) {
  if (!statusFilter) return rows;
  const want = statusFilter.toUpperCase();
  return rows.filter((r) => String(r.status || "").toUpperCase() === want);
}

function OverviewKpis({ stats }) {
  if (!stats) return <p style={summary24hHintStyle}>Carregue os dados com Listar.</p>;
  const blocks = [
    {
      title: "Domain event outbox",
      counts: stats.domain_event_outbox,
      tab: "domain",
      hint: "Webhooks parceiros · PENDING → PUBLISHED",
    },
    {
      title: "Lifecycle deadlines",
      counts: stats.lifecycle_deadlines,
      tab: "lifecycle",
      hint: "PREPAYMENT · POSTPAYMENT · PICKUP",
    },
    {
      title: "Inventory sync",
      counts: stats.inventory_sync_queue,
      tab: "inventory",
      hint: "Shopee · Magalu · Mercado Livre",
    },
    {
      title: "Dead letter",
      counts: stats.worker_dead_letter_queue,
      tab: "dlq",
      hint: "Falhas permanentes por worker",
    },
  ];
  return (
    <div style={kpiGridStyle}>
      {blocks.map((b) => {
        const entries = Object.entries(b.counts || {});
        const total = sumCounts(b.counts);
        const pending = Number(b.counts?.PENDING || 0);
        const failed = Number(b.counts?.FAILED || 0) + Number(b.counts?.DEAD_LETTER || 0);
        return (
          <div key={b.title} style={kpiCardStyle}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#cbd5e1", marginBottom: 6 }}>{b.title}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: "#f8fafc" }}>{total}</div>
            <p style={{ ...summary24hHintStyle, marginTop: 6, marginBottom: 8 }}>{b.hint}</p>
            {entries.length ? (
              <ul style={{ margin: 0, paddingLeft: 16, fontSize: 11, color: "#94a3b8" }}>
                {entries.map(([k, v]) => (
                  <li key={k}>
                    <span style={workerStatusBadge(k)}>{k}</span> {v}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={summary24hHintStyle}>Sem registros</p>
            )}
            <p style={{ ...summary24hHintStyle, marginTop: 8 }}>
              PENDING: {pending} · falhas/DLQ: {failed}
            </p>
            <Link to={`/ops/workers/admin?tab=${b.tab}`} style={{ ...crossShortcutLinkStyle, fontSize: 11, marginTop: 8 }}>
              Abrir fila →
            </Link>
          </div>
        );
      })}
    </div>
  );
}

export default function OpsWorkersAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab") || "overview";
  const [stats, setStats] = useState(null);
  const [domainOutbox, setDomainOutbox] = useState([]);
  const [lifecycle, setLifecycle] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [dlq, setDlq] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [marketplaceFilter, setMarketplaceFilter] = useState("");
  const [dlqWorkerFilter, setDlqWorkerFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const headers = useMemo(
    () => ({
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }),
    [token],
  );

  const setTabAndUrl = (id) => {
    const p = new URLSearchParams(searchParams);
    p.set("tab", id);
    setSearchParams(p);
    setStatusFilter("");
    setMarketplaceFilter("");
    setDlqWorkerFilter("");
  };

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const qs = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
      const invQs = [
        statusFilter ? `status=${encodeURIComponent(statusFilter)}` : "",
        marketplaceFilter ? `marketplace=${encodeURIComponent(marketplaceFilter)}` : "",
      ]
        .filter(Boolean)
        .join("&");
      const dlqQs = dlqWorkerFilter ? `?worker_name=${encodeURIComponent(dlqWorkerFilter)}` : "";
      const [st, dom, life, inv, dl] = await Promise.all([
        fetch(`${API}/workers/stats`, { headers }),
        fetch(`${API}/domain-event-outbox${qs}`, { headers }),
        fetch(`${API}/workers/lifecycle-deadlines${qs}`, { headers }),
        fetch(`${API}/workers/inventory-sync-queue${invQs ? `?${invQs}` : ""}`, { headers }),
        fetch(`${API}/workers/dead-letter-queue${dlqQs}`, { headers }),
      ]);
      const payloads = await Promise.all([
        st.json().catch(() => ({})),
        dom.json().catch(() => ({})),
        life.json().catch(() => ({})),
        inv.json().catch(() => ({})),
        dl.json().catch(() => ({})),
      ]);
      if (!st.ok) throw new Error(parseError(payloads[0], normalizeNetworkError(null, "/workers/stats")));
      setStats(payloads[0]);
      setDomainOutbox(payloads[1]?.items ?? []);
      setLifecycle(payloads[2]?.items ?? []);
      setInventory(payloads[3]?.items ?? []);
      setDlq(payloads[4]?.items ?? []);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  }, [headers, statusFilter, marketplaceFilter, dlqWorkerFilter]);

  useEffect(() => {
    if (token) void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Listar reaplica filtros
  }, [token]);

  const replayDomain = async (id) => {
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const r = await fetch(`${API}/domain-event-outbox/${encodeURIComponent(id)}/replay`, {
        method: "POST",
        headers,
      });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(body));
      setOk(`Domain outbox ${id} reenfileirado (PENDING).`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, "replay domain"));
    } finally {
      setLoading(false);
    }
  };

  const replayInventory = async (id) => {
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const r = await fetch(`${API}/workers/inventory-sync-queue/${encodeURIComponent(id)}/replay`, {
        method: "POST",
        headers,
      });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(body));
      setOk(`Inventory sync ${id} reenfileirado (PENDING).`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, "replay inventory"));
    } finally {
      setLoading(false);
    }
  };

  const tableRows = useMemo(() => {
    if (tab === "domain") return filterByStatus(domainOutbox, statusFilter);
    if (tab === "lifecycle") return filterByStatus(lifecycle, statusFilter);
    if (tab === "inventory") return filterByStatus(inventory, statusFilter);
    if (tab === "dlq") return dlq;
    return [];
  }, [tab, domainOutbox, lifecycle, inventory, dlq, statusFilter]);

  const listCount = tableRows.length;

  const listTitle =
    tab === "domain"
      ? `Domain event outbox (${listCount})`
      : tab === "lifecycle"
        ? `Lifecycle deadlines (${listCount})`
        : tab === "inventory"
          ? `Inventory sync queue (${listCount})`
          : tab === "dlq"
            ? `Dead letter queue (${listCount})`
            : "";

  return (
    <div style={pageStyle} data-testid="ops-workers-admin-page">
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/order-pickup/admin" style={crossShortcutLinkStyle}>
            Order Pickup
          </Link>
          <Link to="/ops/marketplace/admin" style={crossShortcutLinkStyle}>
            Marketplace
          </Link>
          <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>
            Parceiros
          </Link>
          <Link to="/ops/order/domain-events" style={crossShortcutLinkStyle}>
            Domain events (legado)
          </Link>
          <Link to="/ops/order/pickup-health" style={crossShortcutLinkStyle}>
            Pickup health
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Workers PostgreSQL (Node)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Filas <code style={{ color: "#e2e8f0" }}>domain_event_outbox</code>,{" "}
          <code style={{ color: "#e2e8f0" }}>lifecycle_deadlines</code>,{" "}
          <code style={{ color: "#e2e8f0" }}>inventory_sync_queue</code> — worker Node cron 10s · SKIP LOCKED — API{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code>
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Filas e monitoramento</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {TAB_ITEMS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  style={tabButtonStyle(tab === t.id)}
                  onClick={() => setTabAndUrl(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {tab === "overview" ? (
            <p style={summary24hHintStyle}>
              KPIs por fila. Use as abas para listar, filtrar por status e reenfileirar (replay) itens com falha.
            </p>
          ) : null}

          {tab === "domain" ? (
            <p style={summary24hHintStyle}>
              Eventos PENDING publicados via <code>partner_webhook_endpoints</code> (retry exponencial, máx. 5).
            </p>
          ) : null}

          {tab === "lifecycle" ? (
            <p style={summary24hHintStyle}>
              Deadlines vencidos: PREPAYMENT_TIMEOUT, POSTPAYMENT_EXPIRY, PICKUP_TIMEOUT (cancelar pedido, liberar slot, notificar).
            </p>
          ) : null}

          {tab === "inventory" ? (
            <p style={summary24hHintStyle}>
              Sincronização de estoque com marketplaces (rate limit por canal). Auditoria em{" "}
              <code>marketplace_sync_audit_log</code>.
            </p>
          ) : null}

          {tab === "dlq" ? (
            <p style={summary24hHintStyle}>Itens em <code>worker_dead_letter_queue</code> após esgotar tentativas.</p>
          ) : null}

          {tab !== "overview" ? (
            <div style={healthLocalFilterRowStyle}>
              {tab !== "dlq" ? (
                <label style={healthLocalFilterFieldStyle}>
                  status
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    style={healthLocalFilterInputStyle}
                  >
                    <option value="">— todos —</option>
                    <option value="PENDING">PENDING</option>
                    <option value="PROCESSING">PROCESSING</option>
                    <option value="FAILED">FAILED</option>
                    {tab === "domain" ? <option value="PUBLISHED">PUBLISHED</option> : null}
                    {tab === "lifecycle" ? (
                      <>
                        <option value="EXECUTING">EXECUTING</option>
                        <option value="EXECUTED">EXECUTED</option>
                        <option value="CANCELLED">CANCELLED</option>
                      </>
                    ) : null}
                    {tab === "inventory" ? (
                      <>
                        <option value="SYNCED">SYNCED</option>
                        <option value="DEAD_LETTER">DEAD_LETTER</option>
                      </>
                    ) : null}
                  </select>
                </label>
              ) : (
                <label style={healthLocalFilterFieldStyle}>
                  worker_name
                  <select
                    value={dlqWorkerFilter}
                    onChange={(e) => setDlqWorkerFilter(e.target.value)}
                    style={healthLocalFilterInputStyle}
                  >
                    <option value="">— todos —</option>
                    <option value="domain_event_outbox">domain_event_outbox</option>
                    <option value="lifecycle_deadlines">lifecycle_deadlines</option>
                    <option value="inventory_sync_queue">inventory_sync_queue</option>
                  </select>
                </label>
              )}
              {tab === "inventory" ? (
                <label style={healthLocalFilterFieldStyle}>
                  marketplace
                  <select
                    value={marketplaceFilter}
                    onChange={(e) => setMarketplaceFilter(e.target.value)}
                    style={healthLocalFilterInputStyle}
                  >
                    <option value="">— todos —</option>
                    <option value="SHOPEE">SHOPEE</option>
                    <option value="MAGALU">MAGALU</option>
                    <option value="MERCADO_LIVRE">MERCADO_LIVRE</option>
                  </select>
                </label>
              ) : null}
            </div>
          ) : null}

          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !token}>
              {loading ? "Atualizando…" : "Listar"}
            </button>
          </div>
        </section>

        {err ? (
          <div style={criticalBannerStyle} role="alert">
            {err}
          </div>
        ) : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {!token ? <p style={summary24hHintStyle}>Faça login com perfil OPS para listar filas.</p> : null}
        {token && !canMutate ? (
          <p style={summary24hHintStyle}>Replay exige role admin_operacao.</p>
        ) : null}

        {tab === "overview" ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Resumo das filas</h3>
            </div>
            <OverviewKpis stats={stats} />
          </section>
        ) : null}

        {tab !== "overview" && listCount > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>{listTitle}</h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              {tab === "domain" ? (
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      {["evento", "aggregate", "status", "retries", "ação"].map((h) => (
                        <th key={h} style={thStyle}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row) => (
                      <tr key={row.id}>
                        <td style={tdStyle}>
                          <div>{row.event_name || "—"}</div>
                          <code style={{ fontSize: 10, color: "#94a3b8" }}>{row.event_key}</code>
                        </td>
                        <td style={tdStyle}>
                          <code>{row.aggregate_id || "—"}</code>
                        </td>
                        <td style={tdStyle}>
                          <span style={workerStatusBadge(row.status)}>{row.status}</span>
                        </td>
                        <td style={tdStyle}>{row.retry_count ?? 0}</td>
                        <td style={tdStyle}>
                          {row.status !== "PUBLISHED" && canMutate ? (
                            <button
                              type="button"
                              style={buttonGhostStyle}
                              onClick={() => void replayDomain(row.id)}
                              disabled={loading}
                            >
                              Replay
                            </button>
                          ) : (
                            "—"
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}

              {tab === "lifecycle" ? (
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      {["tipo", "pedido", "status", "due_at", "falhas"].map((h) => (
                        <th key={h} style={thStyle}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row) => (
                      <tr key={row.id}>
                        <td style={tdStyle}>
                          <span style={workerStatusBadge(row.deadline_type)}>{row.deadline_type}</span>
                        </td>
                        <td style={tdStyle}>
                          <code>{row.order_id}</code>
                        </td>
                        <td style={tdStyle}>
                          <span style={workerStatusBadge(row.status)}>{row.status}</span>
                        </td>
                        <td style={tdStyle}>{row.due_at ? new Date(row.due_at).toLocaleString("pt-BR") : "—"}</td>
                        <td style={tdStyle}>{row.failure_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}

              {tab === "inventory" ? (
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      {["marketplace", "produto", "qtd", "status", "retries", "ação"].map((h) => (
                        <th key={h} style={thStyle}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row) => (
                      <tr key={row.id}>
                        <td style={tdStyle}>
                          <span style={workerStatusBadge(row.marketplace)}>{row.marketplace}</span>
                        </td>
                        <td style={tdStyle}>
                          <code>{row.product_id}</code>
                        </td>
                        <td style={tdStyle}>{row.quantity_available}</td>
                        <td style={tdStyle}>
                          <span style={workerStatusBadge(row.status)}>{row.status}</span>
                        </td>
                        <td style={tdStyle}>{row.retry_count ?? 0}</td>
                        <td style={tdStyle}>
                          {row.status !== "SYNCED" && canMutate ? (
                            <button
                              type="button"
                              style={buttonGhostStyle}
                              onClick={() => void replayInventory(row.id)}
                              disabled={loading}
                            >
                              Replay
                            </button>
                          ) : (
                            "—"
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}

              {tab === "dlq" ? (
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      {["worker", "origem", "tentativas", "erro", "quando"].map((h) => (
                        <th key={h} style={thStyle}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row) => (
                      <tr key={row.id}>
                        <td style={tdStyle}>
                          <code>{row.worker_name}</code>
                        </td>
                        <td style={tdStyle}>
                          <code>{row.source_table}</code> / <code>{row.source_id}</code>
                        </td>
                        <td style={tdStyle}>{row.attempt_count}</td>
                        <td style={tdStyle} title={row.error_message || ""}>
                          <span
                            style={{
                              display: "block",
                              maxWidth: 320,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {row.error_message || "—"}
                          </span>
                        </td>
                        <td style={tdStyle}>
                          {row.dead_lettered_at ? new Date(row.dead_lettered_at).toLocaleString("pt-BR") : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}
            </div>
          </section>
        ) : null}

        {tab !== "overview" && token && !loading && listCount === 0 ? (
          <p style={summary24hHintStyle}>Nenhum registro para os filtros atuais. Ajuste status ou use Listar.</p>
        ) : null}
      </section>
    </div>
  );
}
