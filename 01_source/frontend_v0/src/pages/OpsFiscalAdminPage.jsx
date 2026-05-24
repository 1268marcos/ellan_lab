
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  buttonGhostStyle,
  buttonPrimaryStyle,
  cardStyle,
  crossShortcutLinkStyle,
  mutedTextStyle,
  opsSanityCardStyle,
  pageStyle,
  summary24hHeaderStyle,
  tabButtonStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_FISCAL_ADMIN_BASE_URL || "/api/fca";
const API = `${BASE}/v1/fiscal-admin`;
const PAGE_VERSION = "ops/fiscal/admin v0.1";

function parseError(payload, status, fallback = "Falha na API fiscal-admin.") {
  if (status === 502 || status === 503 || status === 504) {
    return "fiscal-admin indisponivel. Suba o servico na porta 8024 (ver runbook abaixo).";
  }
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (Array.isArray(payload?.detail)) {
    const msg = payload.detail.map((d) => d?.msg || d?.loc?.join(".")).filter(Boolean).join("; ");
    if (msg) return msg;
  }
  return fallback;
}

async function fetchJson(url, headers) {
  const r = await fetch(url, { headers });
  const json = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, json };
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8024).`;
  }
  return raw;
}

const TABS = [
  "global",
  "issuers",
  "documents",
  "gaps",
  "corridors",
  "readiness",
  "certifications",
  "classification",
  "slo",
  "webhooks",
  "config",
  "governance",
];

export default function OpsFiscalAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = TABS.includes(searchParams.get("tab") || "") ? searchParams.get("tab") : "global";
  const setTab = (t) => setSearchParams({ tab: t }, { replace: true });

  const [issuers, setIssuers] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [products, setProducts] = useState([]);
  const [health, setHealth] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [callbacks, setCallbacks] = useState([]);
  const [summary, setSummary] = useState(null);
  const [jurisdictions, setJurisdictions] = useState([]);
  const [corridors, setCorridors] = useState([]);
  const [certifications, setCertifications] = useState([]);
  const [readiness, setReadiness] = useState([]);
  const [classRules, setClassRules] = useState([]);
  const [classLogs, setClassLogs] = useState([]);
  const [slos, setSlos] = useState([]);
  const [webhookDlq, setWebhookDlq] = useState([]);
  const [issuerForm, setIssuerForm] = useState({ name: "", code: "", issuer_type: "SEFAZ", country: "BR" });
  const [selectedId, setSelectedId] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [lastApiKey, setLastApiKey] = useState("");
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

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const [sm, i, d, g, t, p, h, a, c, j, cor, cert, rd, cr, cl, slo, wh] = await Promise.all([
        fetchJson(`${API}/fiscal-global-ops/summary`, headers),
        fetchJson(`${API}/fiscal-issuer-partners`, headers),
        fetchJson(`${API}/fiscal-documents`, headers),
        fetchJson(`${API}/fiscal-ops/reconciliation-gaps`, headers),
        fetchJson(`${API}/fiscal-ops/tenant-config`, headers),
        fetchJson(`${API}/fiscal-ops/product-fiscal-config`, headers),
        fetchJson(`${API}/fiscal-ops/provider-health`, headers),
        fetchJson(`${API}/fiscal-ops/accounting-approvals`, headers),
        fetchJson(`${API}/fiscal-ops/authority-callbacks`, headers),
        fetchJson(`${API}/fiscal-global-ops/jurisdictions`, headers),
        fetchJson(`${API}/fiscal-global-ops/corridors`, headers),
        fetchJson(`${API}/fiscal-global-ops/certifications`, headers),
        fetchJson(`${API}/fiscal-global-ops/integration-readiness`, headers),
        fetchJson(`${API}/fiscal-global-ops/classification-rules`, headers),
        fetchJson(`${API}/fiscal-ops/classification-logs`, headers),
        fetchJson(`${API}/fiscal-global-ops/slo-policies`, headers),
        fetchJson(`${API}/fiscal-global-ops/webhook-deliveries?failed_only=true`, headers),
      ]);
      const failures = [sm, i, d, g].filter((r) => !r.ok);
      if (sm.ok) setSummary(sm.json);
      if (i.ok) setIssuers(i.json.issuers || []);
      if (d.ok) setDocuments(d.json.items || []);
      if (g.ok) setGaps(g.json.items || []);
      if (t.ok) setTenants(t.json.items || []);
      if (p.ok) setProducts(p.json.items || []);
      if (h.ok) setHealth(h.json.items || []);
      if (a.ok) setApprovals(a.json.items || []);
      if (c.ok) setCallbacks(c.json.items || []);
      if (j.ok) setJurisdictions(j.json.items || []);
      if (cor.ok) setCorridors(cor.json.items || []);
      if (cert.ok) setCertifications(cert.json.items || []);
      if (rd.ok) setReadiness(rd.json.items || []);
      if (cr.ok) setClassRules(cr.json.items || []);
      if (cl.ok) setClassLogs(cl.json.items || []);
      if (slo.ok) setSlos(slo.json.items || []);
      if (wh.ok) setWebhookDlq(wh.json.items || []);
      if (failures.length) {
        const primary = failures[0];
        throw new Error(parseError(primary.json, primary.status));
      }
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setIssuers([]);
      setDocuments([]);
      setGaps([]);
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  useEffect(() => {
    void load();
  }, [load]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j, r.status));
      setOk("Seed fiscal aplicado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateIssuer = async () => {
    if (!token || !canMutate || !issuerForm.name || !issuerForm.code) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/fiscal-issuer-partners`, {
        method: "POST",
        headers,
        body: JSON.stringify(issuerForm),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j, r.status));
      setOk(`Emissor ${j.code} criado.`);
      setSelectedId(j.id);
      setIssuerForm({ name: "", code: "", issuer_type: "SEFAZ", country: "BR" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/fiscal-issuer-partners`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!token || !canMutate || !selectedId || !webhookUrl) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/fiscal-issuer-partners/${encodeURIComponent(selectedId)}/webhook`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          url: webhookUrl,
          secret: webhookSecret || undefined,
          events: ["fiscal.document.authorized", "fiscal.callback.received"],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j, r.status));
      setOk(`Webhook salvo para ${selectedId}.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/fiscal-issuer-partners/.../webhook`));
    } finally {
      setLoading(false);
    }
  };

  const onRotate = async () => {
    if (!token || !canMutate || !selectedId) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/fiscal-issuer-partners/${encodeURIComponent(selectedId)}/api-keys/rotate`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j, r.status));
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/fiscal-issuer-partners/.../api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const onResolveGap = async (gapId) => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/fiscal-ops/reconciliation-gaps/${encodeURIComponent(gapId)}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ status: "RESOLVED" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j, r.status));
      setOk(`Gap ${gapId} resolvido.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/fiscal-ops/reconciliation-gaps`));
    } finally {
      setLoading(false);
    }
  };

  const onRecomputeReadiness = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/fiscal-global-ops/integration-readiness/recompute`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j, r.status));
      setOk(`Readiness recalculado: ${j.updated ?? 0} emissores.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/fiscal-global-ops/integration-readiness/recompute`));
    } finally {
      setLoading(false);
    }
  };

  const tableRows = (() => {
    if (tab === "global") {
      return [
        ...(summary
          ? Object.entries(summary).map(([k, v]) => ({
              key: `kpi-${k}`,
              tipo: "kpi",
              id: k,
              detalhe: String(v),
            }))
          : []),
        ...jurisdictions.map((j) => ({
          key: `j-${j.country}`,
          tipo: "jurisdicao",
          id: j.country,
          detalhe: `${j.name} · ${j.currency} · ${j.authority_name || "—"}`,
        })),
      ];
    }
    if (tab === "issuers") {
      return issuers.map((p) => ({
        key: `i-${p.id}`,
        tipo: "emissor",
        id: p.code,
        detalhe: `${p.name} · ${p.issuer_type} · ${p.country} · ${p.active ? "ativo" : "inativo"}`,
      }));
    }
    if (tab === "documents") {
      return documents.map((d) => ({
        key: `d-${d.id}`,
        tipo: "doc",
        id: d.receipt_code,
        detalhe: `${d.order_id} · ${d.document_type} · ${d.send_status || "—"}`,
      }));
    }
    if (tab === "gaps") {
      return gaps.map((g) => ({
        key: `g-${g.id}`,
        tipo: "gap",
        id: g.id,
        detalhe: `${g.gap_type} · ${g.severity} · ${g.status}`,
        gapId: g.id,
        status: g.status,
      }));
    }
    if (tab === "corridors") {
      return corridors.map((c) => ({
        key: `c-${c.id}`,
        tipo: "corredor",
        id: c.corridor_code,
        detalhe: `${c.origin_country}→${c.dest_country} · ${c.primary_issuer_code} · ${c.document_type_code}`,
      }));
    }
    if (tab === "readiness") {
      return readiness.map((r) => ({
        key: `r-${r.issuer_id}`,
        tipo: "readiness",
        id: r.issuer_code,
        detalhe: `band ${r.readiness_band} · score ${r.score_total} · ${(r.blockers || []).join(", ") || "ok"}`,
      }));
    }
    if (tab === "certifications") {
      return certifications.map((c) => ({
        key: `cert-${c.id}`,
        tipo: "cert",
        id: c.certification_type,
        detalhe: `${c.issuer_code} · ${c.status} · exp ${c.expires_at || "—"}`,
      }));
    }
    if (tab === "classification") {
      return [
        ...classRules.map((r) => ({
          key: `rule-${r.id}`,
          tipo: "regra",
          id: r.sku_pattern,
          detalhe: `NCM ${r.ncm_code} · CFOP ${r.cfop || "—"} · ${r.country}`,
        })),
        ...classLogs.map((l) => ({
          key: `log-${l.id}`,
          tipo: "log",
          id: l.order_id,
          detalhe: `${l.sku_id} · NCM ${l.ncm_applied} · ${l.source}`,
        })),
      ];
    }
    if (tab === "slo") {
      return slos.map((s) => ({
        key: `slo-${s.id}`,
        tipo: "slo",
        id: s.corridor_code,
        detalhe: `${s.metric_name} · p99 ${s.target_p99_ms}ms · ${s.target_success_rate_pct}%`,
      }));
    }
    if (tab === "webhooks") {
      return webhookDlq.map((w) => ({
        key: `wh-${w.id}`,
        tipo: "webhook",
        id: w.event_type,
        detalhe: `${w.delivery_status} · HTTP ${w.http_status ?? "—"} · ${w.error_message || ""}`,
      }));
    }
    if (tab === "config") {
      return [
        ...tenants.map((t) => ({ key: `t-${t.tenant_id}`, tipo: "tenant", id: t.tenant_id, detalhe: t.razao_social })),
        ...products.map((p) => ({ key: `p-${p.sku_id}`, tipo: "sku", id: p.sku_id, detalhe: `NCM ${p.ncm_code || "—"}` })),
        ...health.map((h) => ({
          key: `h-${h.country}`,
          tipo: "health",
          id: h.country,
          detalhe: `${h.provider_name} · ${h.last_status}`,
        })),
      ];
    }
    return [
      ...approvals.map((a) => ({
        key: `a-${a.id}`,
        tipo: "approval",
        id: a.id,
        detalhe: `${a.owner} · ${a.status}`,
      })),
      ...callbacks.map((c) => ({
        key: `c-${c.id}`,
        tipo: "callback",
        id: c.id,
        detalhe: `${c.authority} · ${c.event_type || "—"}`,
      })),
    ];
  })();

  const listCount = tableRows.length;

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
            Payment Gateway
          </Link>
          <Link to="/ops/finance/admin" style={crossShortcutLinkStyle}>
            Finance
          </Link>
          <Link to="/fiscal/global" style={crossShortcutLinkStyle}>
            Fiscal Global
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Fiscal (admin)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Emissores fiscais (SEFAZ, AT-PT), documentos NFC-e, gaps, tenant/SKU, health, aprovações e callbacks —{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code>
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Domínio fiscal</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {[
                ["global", "Global"],
                ["issuers", "Emissores"],
                ["documents", "Docs"],
                ["gaps", "Gaps"],
                ["corridors", "Corredores"],
                ["readiness", "Readiness"],
                ["certifications", "Certs"],
                ["classification", "NCM/CFOP"],
                ["slo", "SLA"],
                ["webhooks", "DLQ"],
                ["config", "Config"],
                ["governance", "Gov"],
              ].map(([t, label]) => (
                <button key={t} type="button" style={tabButtonStyle(tab === t)} onClick={() => setTab(t)}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading}>
              Atualizar
            </button>
            {canMutate ? (
              <>
                <button type="button" style={buttonPrimaryStyle} onClick={() => void onSeed()} disabled={loading}>
                  Seed
                </button>
                {tab === "readiness" ? (
                  <button type="button" style={buttonGhostStyle} onClick={() => void onRecomputeReadiness()} disabled={loading}>
                    Recalc readiness
                  </button>
                ) : null}
              </>
            ) : null}
            <span style={mutedTextStyle}>{listCount} registro(s)</span>
          </div>

          {ok ? <p style={{ color: "#6ee7b7", fontSize: 13 }}>{ok}</p> : null}
          {err ? (
            <div style={{ color: "#fca5a5", fontSize: 13 }}>
              <p style={{ margin: "0 0 8px" }}>{err}</p>
              <pre
                style={{
                  margin: 0,
                  padding: 8,
                  fontSize: 11,
                  background: "rgba(0,0,0,0.25)",
                  borderRadius: 6,
                  whiteSpace: "pre-wrap",
                  color: "#cbd5e1",
                }}
              >
                {`cd 01_source/fiscal_admin_service
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8024 --reload

# ou Docker:
cd 02_docker && docker compose up -d fiscal_admin_service`}
              </pre>
            </div>
          ) : null}
          {lastApiKey ? (
            <p style={{ fontFamily: "monospace", fontSize: 11, color: "#fcd34d" }}>API key: {lastApiKey}</p>
          ) : null}

          {tab === "issuers" && canMutate ? (
            <div style={{ display: "grid", gap: 8, marginBottom: 12 }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                <input
                  placeholder="Nome emissor"
                  value={issuerForm.name}
                  onChange={(e) => setIssuerForm((f) => ({ ...f, name: e.target.value }))}
                  style={{ flex: 1, minWidth: 120 }}
                />
                <input
                  placeholder="Código"
                  value={issuerForm.code}
                  onChange={(e) => setIssuerForm((f) => ({ ...f, code: e.target.value }))}
                  style={{ flex: 1, minWidth: 100 }}
                />
                <button type="button" style={buttonPrimaryStyle} onClick={() => void onCreateIssuer()}>
                  Criar emissor
                </button>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
                  <option value="">Emissor</option>
                  {issuers.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.code}
                    </option>
                  ))}
                </select>
                <input
                  placeholder="Webhook URL"
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  style={{ flex: 2, minWidth: 160 }}
                />
                <input
                  placeholder="Secret"
                  value={webhookSecret}
                  onChange={(e) => setWebhookSecret(e.target.value)}
                />
                <button type="button" style={buttonGhostStyle} onClick={() => void onWebhook()}>
                  Webhook
                </button>
                <button type="button" style={buttonGhostStyle} onClick={() => void onRotate()}>
                  Rotacionar API key
                </button>
              </div>
            </div>
          ) : null}

          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Tipo</th>
                <th style={thStyle}>ID</th>
                <th style={thStyle}>Detalhe</th>
                {tab === "gaps" ? <th style={thStyle}>Ação</th> : null}
              </tr>
            </thead>
            <tbody>
              {tableRows.map((r) => (
                <tr key={r.key}>
                  <td style={tdStyle}>{r.tipo}</td>
                  <td style={tdStyle}>{r.id}</td>
                  <td style={tdStyle}>{r.detalhe}</td>
                  {tab === "gaps" ? (
                    <td style={tdStyle}>
                      {r.gapId && r.status !== "RESOLVED" ? (
                        <button type="button" style={buttonGhostStyle} onClick={() => void onResolveGap(r.gapId)}>
                          Resolver
                        </button>
                      ) : (
                        "—"
                      )}
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
          {!tableRows.length && !loading ? <p style={mutedTextStyle}>Nenhum registro. Execute Seed.</p> : null}
        </section>
      </section>
    </div>
  );
}
