
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  buttonPrimaryStyle,
  cardStyle,
  crossShortcutLinkStyle,
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

const DASHBOARD_SECTIONS = [
  {
    title: "Nucleo capability",
    hint: "Canais, contextos, regioes e perfis",
    keys: [
      ["channels", "Canais"],
      ["contexts", "Contextos"],
      ["regions", "Regioes"],
      ["profiles", "Perfis"],
      ["active_profiles", "Perfis ativos"],
    ],
  },
  {
    title: "Catalogo e geo",
    hint: "Pagamento e cobertura geografica",
    keys: [
      ["payment_methods", "Metodos pagamento"],
      ["countries", "Paises"],
      ["provinces", "Provincias"],
      ["locker_locations", "Lockers"],
    ],
  },
  {
    title: "Integracao",
    hint: "Webhooks e entregas",
    keys: [["webhooks", "Webhooks"]],
  },
  {
    title: "Ecossistema mundial",
    hint: "Segmentos, players e bindings",
    keys: [
      ["ecosystem_segments", "Segmentos"],
      ["ecosystem_players", "Players"],
      ["player_bindings", "Bindings perfil-player"],
    ],
  },
  {
    title: "Matriz e auditoria",
    hint: "Cobertura regiao x canal x contexto",
    keys: [
      ["matrix_coverage_pct", "Cobertura matriz"],
      ["audit_events_24h", "Eventos auditoria 24h"],
    ],
  },
];

function formatDashboardValue(key, value) {
  if (value == null || value === "") return "0";
  if (key === "matrix_coverage_pct") {
    const n = Number(value);
    return Number.isFinite(n) ? n.toFixed(1) + "%" : String(value);
  }
  return String(value);
}

function CapabilityKpiCard({ label, value, warnEmpty }) {
  const isZero = value === 0 || value === "0" || value === "0.0%";
  return (
    <div
      style={{
        padding: "12px 14px",
        borderRadius: 12,
        border: isZero && warnEmpty ? "1px solid rgba(251,191,36,0.45)" : "1px solid rgba(148,163,184,0.22)",
        background: isZero && warnEmpty ? "rgba(120,53,15,0.18)" : "rgba(15,23,42,0.85)",
        minHeight: 72,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <div style={{ fontSize: 11, color: "#94a3b8", lineHeight: 1.3, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        {label}
      </div>
      <div
        style={{
          marginTop: 6,
          fontSize: 22,
          fontWeight: 700,
          color: isZero && warnEmpty ? "#fcd34d" : "#f8fafc",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </div>
    </div>
  );
}

function CapabilityDashboardGrid({ dash }) {
  if (!dash) return null;
  return (
    <div style={{ display: "grid", gap: 20 }}>
      {DASHBOARD_SECTIONS.map((section) => (
        <section key={section.title} style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <div>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: "#e2e8f0" }}>{section.title}</h3>
              <p style={{ ...summary24hHintStyle, marginTop: 4 }}>{section.hint}</p>
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
              gap: 12,
            }}
          >
            {section.keys.map(([key, label]) => (
              <CapabilityKpiCard
                key={key}
                label={label}
                value={formatDashboardValue(key, dash[key])}
                warnEmpty={key !== "audit_events_24h"}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

const BASE = import.meta.env.VITE_CAPABILITY_ADMIN_BASE_URL || "/api/cap";
const API = `${BASE}/v1/capability-admin`;

async function parseJsonSafe(res) {
  const text = await res.text();
  if (!text || !String(text).trim()) {
    if (!res.ok) {
      throw new Error("HTTP " + res.status + " (resposta vazia - servico parado?)");
    }
    return {};
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new Error("Resposta invalida HTTP " + res.status + ". Verifique capability-admin na porta 8028.");
  }
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return (
      "Servico indisponivel (" +
      endpoint +
      "). Suba: cd 01_source/capability_admin_service && ./dev.sh"
    );
  }
  return raw;
}

export default function OpsCapabilityAdminPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab") || "overview";
  const urlView = searchParams.get("view");
  const setTab = (k) => {
    const p = new URLSearchParams(searchParams);
    if (k === "overview") p.delete("tab");
    else p.set("tab", k);
    p.delete("view");
    setSearchParams(p, { replace: true });
  };

  const [dash, setDash] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [channels, setChannels] = useState([]);
  const [methods, setMethods] = useState([]);
  const [interfaces, setInterfaces] = useState([]);
  const [wallets, setWallets] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [matrix, setMatrix] = useState(null);
  const [segments, setSegments] = useState([]);
  const [ecoPlayers, setEcoPlayers] = useState([]);
  const [bindings, setBindings] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [regions, setRegions] = useState([]);
  const [lockerPresence, setLockerPresence] = useState([]);
  const [worldReport, setWorldReport] = useState(null);
  const [readiness, setReadiness] = useState([]);
  const [insights, setInsights] = useState([]);
  const [resolved, setResolved] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [webhookUrl, setWebhookUrl] = useState("https://hooks.example.com/capability");
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

  const fetchApi = useCallback(
    async (path, options = {}) => {
      const res = await fetch(`${API}${path}`, { ...options, headers: { ...headers, ...(options.headers || {}) } });
      const body = await parseJsonSafe(res);
      if (!res.ok) {
        if (res.status === 429) throw new Error("Muitas requisicoes (429). Aguarde e recarregue.");
        if (res.status === 404) {
          throw new Error("API capability-admin nao encontrada (404). Suba: cd 01_source/capability_admin_service && ./dev.sh");
        }
        throw new Error(body.detail || "HTTP " + res.status);
      }
      return body;
    },
    [headers],
  );

  const loadTab = useCallback(
    async (activeTab) => {
      if (!token) return;
      setLoading(true);
      setErr("");
      try {
        if (activeTab === "overview") {
          const dj = await fetchApi("/dashboard");
          setDash(dj);
        } else if (activeTab === "profiles") {
          const pj = await fetchApi("/profiles");
          setProfiles(pj.items || []);
          if (!selectedId && pj.items?.length) setSelectedId(pj.items[0].id);
        } else if (activeTab === "channels") {
          const cj = await fetchApi("/channels");
          setChannels(cj.items || []);
        } else if (activeTab === "catalogs") {
          const [pm, iface, wal] = await Promise.all([
            fetchApi("/payment-methods"),
            fetchApi("/payment-interfaces"),
            fetchApi("/wallet-providers"),
          ]);
          setMethods(pm.items || []);
          setInterfaces(iface.items || []);
          setWallets(wal.items || []);
        } else if (activeTab === "matrix") {
          setMatrix(await fetchApi("/matrix"));
        } else if (activeTab === "regions") {
          const rj = await fetchApi("/regions");
          setRegions(rj.items || []);
        } else if (activeTab === "geo") {
          const co = await fetchApi("/geo/countries");
          setRegions(co.items || []);
        } else if (activeTab === "ecosystem") {
          if (urlView === "locker") {
            const lp = await fetchApi("/ecosystem/locker-presence");
            setLockerPresence(lp.items || []);
          } else {
            const [seg, ep, bind] = await Promise.all([
              fetchApi("/ecosystem/segments"),
              fetchApi("/ecosystem/players"),
              fetchApi("/ecosystem/bindings"),
            ]);
            setSegments(seg.items || []);
            setEcoPlayers(ep.items || []);
            setBindings(bind.items || []);
          }
        } else if (activeTab === "tools") {
          setTemplates((await fetchApi("/ops/templates")).items || []);
          const res = await fetchApi("/ops/resolve", {
            method: "POST",
            body: JSON.stringify({
              region_code: "SP",
              channel_code: "kiosk",
              context_code: "purchase",
            }),
          });
          setResolved(res);
        } else if (activeTab === "intelligence") {
          const view = urlView || "world";
          if (view === "readiness") {
            setReadiness((await fetchApi("/intelligence/readiness")).items || []);
          } else if (view === "insights") {
            setInsights((await fetchApi("/intelligence/insights")).items || []);
          } else {
            setWorldReport(await fetchApi("/intelligence/world-report"));
          }
        } else if (activeTab === "webhooks") {
          const pj = await fetchApi("/profiles");
          setProfiles(pj.items || []);
          if (!selectedId && pj.items?.length) setSelectedId(pj.items[0].id);
          const wj = await fetchApi("/webhooks");
          setWebhooks(wj.items || []);
        } else if (activeTab === "audit") {
          const aud = await fetchApi("/ecosystem/audit-log");
          setAuditLog(aud.items || []);
        }
      } catch (e) {
        setErr(normalizeNetworkError(e, API));
      } finally {
        setLoading(false);
      }
    },
    [token, fetchApi, selectedId, urlView],
  );

  useEffect(() => {
    void loadTab(tab);
  }, [tab, urlView, loadTab]);

  const onSeed = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const j = await fetchApi("/seed");
      setOk(`Seed OK: ${JSON.stringify(j)}`);
      await loadTab(tab);
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onRotate = async () => {
    if (!selectedId) return;
    try {
      const res = await fetch(`${API}/profiles/${selectedId}/api-keys/rotate`, { method: "POST", headers });
      const j = await parseJsonSafe(res);
      if (!res.ok) throw new Error(j.detail || "rotate failed");
      setLastApiKey(j.api_key);
      setOk("API key rotacionada");
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    }
  };

  const tabs = [
    ["overview", "Visao"],
    ["matrix", "Matriz"],
    ["profiles", "Perfis"],
    ["channels", "Canais"],
    ["regions", "Regioes"],
    ["catalogs", "Catalogos"],
    ["geo", "Geo"],
    ["ecosystem", "Players"],
    ["tools", "Ferramentas"],
    ["intelligence", "Inteligencia"],
    ["webhooks", "Webhooks"],
    ["audit", "Auditoria"],
  ];

  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader
        title="Capability OPS"
        subtitle="Configuração de capacidade · capability-admin :8028"
      />
      <div style={toolbarStyle}>
        {tabs.map(([k, label]) => (
          <button
            key={k}
            type="button"
            style={tabButtonStyle(tab === k)}
            onClick={() => {
              setTab(k);
              void loadTab(k);
            }}
          >
            {label}
          </button>
        ))}
        <button type="button" style={buttonPrimaryStyle} onClick={() => void loadTab(tab)}>
          Recarregar
        </button>
        <button type="button" style={buttonPrimaryStyle} onClick={() => void onSeed()}>
          Seed mundial
        </button>
      </div>
      {ok && <div style={okBannerStyle}>{ok}</div>}
      {err && <div style={opsSanityCardStyle}>{err}</div>}
      {tab === "overview" && loading && !dash ? (
        <p style={summary24hHintStyle}>Carregando indicadores...</p>
      ) : null}
      {tab === "overview" && !loading && !dash && token ? (
        <p style={summary24hHintStyle}>
          Nenhum dado no dashboard. Use Recarregar ou Seed mundial (capability-admin :8028).
        </p>
      ) : null}
      {tab === "overview" && dash ? (
        <div style={{ display: "grid", gap: 16 }}>
          <CapabilityDashboardGrid dash={dash} />
          <div style={cardStyle}>
            <p style={{ ...mutedTextStyle, marginTop: 0 }}>Atalhos</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
                Payment Gateway
              </Link>
              <Link to="/integrations/partners" style={crossShortcutLinkStyle}>
                Integrations
              </Link>
              <button
                type="button"
                style={crossShortcutLinkStyle}
                onClick={() => {
                  setTab("matrix");
                  void loadTab("matrix");
                }}
              >
                Ver matriz
              </button>
              <button
                type="button"
                style={crossShortcutLinkStyle}
                onClick={() => {
                  setTab("ecosystem");
                  void loadTab("ecosystem");
                }}
              >
                Ver players
              </button>
            </div>
          </div>
        </div>
      ) : null}
      {tab === "matrix" && matrix && (
        <div style={cardStyle}>
          <p style={mutedTextStyle}>Cobertura: {matrix.coverage_pct}%</p>
          <pre style={{ fontSize: 10, maxHeight: 280, overflow: "auto" }}>
            {JSON.stringify(matrix.cells?.slice(0, 40), null, 2)}
          </pre>
        </div>
      )}
      {tab === "regions" && (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>code</th>
              <th style={thStyle}>name</th>
              <th style={thStyle}>currency</th>
            </tr>
          </thead>
          <tbody>
            {regions.map((row) => (
              <tr key={row.id}>
                <td style={tdStyle}>{row.code}</td>
                <td style={tdStyle}>{row.name}</td>
                <td style={tdStyle}>{row.default_currency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {tab === "ecosystem" && urlView === "locker" && (
        <div style={cardStyle}>
          <p style={mutedTextStyle}>Locker world: {lockerPresence.length} programas</p>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>player</th>
                <th style={thStyle}>role</th>
                <th style={thStyle}>program</th>
              </tr>
            </thead>
            <tbody>
              {lockerPresence.slice(0, 30).map((row) => (
                <tr key={row.id}>
                  <td style={tdStyle}>{row.player_code}</td>
                  <td style={tdStyle}>{row.locker_role}</td>
                  <td style={tdStyle}>{row.program_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {tab === "ecosystem" && urlView !== "locker" && (
        <div style={cardStyle}>
          <p style={mutedTextStyle}>
            Segmentos: {segments.length} · Players: {ecoPlayers.length} · Bindings: {bindings.length}
          </p>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>player</th>
                <th style={thStyle}>segment</th>
              </tr>
            </thead>
            <tbody>
              {ecoPlayers.slice(0, 20).map((row) => (
                <tr key={row.id}>
                  <td style={tdStyle}>{row.code}</td>
                  <td style={tdStyle}>{row.segment_code}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {tab === "tools" && (
        <div style={cardStyle}>
          <p style={mutedTextStyle}>Resolver SP:kiosk:purchase</p>
          {resolved && <pre style={{ fontSize: 11, margin: 0 }}>{JSON.stringify(resolved, null, 2)}</pre>}
          <p style={mutedTextStyle}>Templates: {templates.length}</p>
          <pre style={{ fontSize: 10, maxHeight: 200, overflow: "auto" }}>
            {JSON.stringify(templates.slice(0, 8), null, 2)}
          </pre>
        </div>
      )}
      {tab === "intelligence" && (
        <div style={cardStyle}>
          {urlView === "readiness" && (
            <pre style={{ fontSize: 11, margin: 0 }}>{JSON.stringify(readiness.slice(0, 15), null, 2)}</pre>
          )}
          {urlView === "insights" && (
            <pre style={{ fontSize: 11, margin: 0 }}>{JSON.stringify(insights.slice(0, 15), null, 2)}</pre>
          )}
          {urlView !== "readiness" && urlView !== "insights" && worldReport && (
            <pre style={{ fontSize: 11, margin: 0 }}>{JSON.stringify(worldReport, null, 2)}</pre>
          )}
        </div>
      )}
      {tab === "audit" && (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>type</th>
              <th style={thStyle}>action</th>
              <th style={thStyle}>at</th>
            </tr>
          </thead>
          <tbody>
            {auditLog.map((a) => (
              <tr key={a.id}>
                <td style={tdStyle}>{a.entity_type}</td>
                <td style={tdStyle}>{a.action}</td>
                <td style={tdStyle}>{a.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {tab === "profiles" && (
        <table style={tableStyle}>
          <thead>
            <tr>
              {["profile_code", "name", "currency", "is_active"].map((h) => (
                <th key={h} style={thStyle}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {profiles.map((row) => (
              <tr key={row.id}>
                <td style={tdStyle}>{row.profile_code}</td>
                <td style={tdStyle}>{row.name}</td>
                <td style={tdStyle}>{row.currency}</td>
                <td style={tdStyle}>{String(row.is_active)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {tab === "catalogs" && (
        <div style={{ display: "grid", gap: 12 }}>
          <TableMini title="Metodos" rows={methods} cols={["code", "name"]} />
          <TableMini title="Interfaces" rows={interfaces} cols={["code", "name"]} />
          <TableMini title="Wallets" rows={wallets} cols={["code", "name"]} />
        </div>
      )}
      {tab === "channels" && (
        <table style={tableStyle}>
          <thead>
            <tr>
              {["code", "name"].map((h) => (
                <th key={h} style={thStyle}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {channels.map((row) => (
              <tr key={row.id}>
                <td style={tdStyle}>{row.code}</td>
                <td style={tdStyle}>{row.name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {tab === "webhooks" && (
        <div style={cardStyle}>
          <label>
            Perfil
            <select value={selectedId || ""} onChange={(e) => setSelectedId(Number(e.target.value))}>
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.profile_code}
                </option>
              ))}
            </select>
          </label>
          <label>
            URL{" "}
            <input value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} style={{ width: "100%" }} />
          </label>
          <button
            type="button"
            style={buttonPrimaryStyle}
            onClick={async () => {
              try {
                const res = await fetch(`${API}/webhooks`, {
                  method: "PUT",
                  headers,
                  body: JSON.stringify({ profile_id: selectedId, url: webhookUrl }),
                });
                await parseJsonSafe(res);
                setOk("Webhook salvo");
                void loadTab("webhooks");
              } catch (e) {
                setErr(normalizeNetworkError(e, API));
              }
            }}
          >
            Salvar webhook
          </button>
          <button type="button" style={buttonPrimaryStyle} onClick={() => void onRotate()}>
            Rotacionar API key
          </button>
          {lastApiKey && <p style={{ fontFamily: "monospace", fontSize: 11 }}>{lastApiKey}</p>}
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>profile</th>
                <th style={thStyle}>url</th>
                <th style={thStyle}>active</th>
              </tr>
            </thead>
            <tbody>
              {webhooks.map((w) => (
                <tr key={w.id}>
                  <td style={tdStyle}>{w.profile_code}</td>
                  <td style={tdStyle}>{w.url}</td>
                  <td style={tdStyle}>{String(w.active)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {loading && <p style={mutedTextStyle}>Carregando…</p>}
    </div>
  );
}

function TableMini({ title, rows, cols }) {
  return (
    <div style={cardStyle}>
      <strong>{title}</strong>
      <table style={tableStyle}>
        <thead>
          <tr>
            {cols.map((h) => (
              <th key={h} style={thStyle}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id ?? i}>
              {cols.map((c) => (
                <td key={c} style={tdStyle}>
                  {String(row[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
