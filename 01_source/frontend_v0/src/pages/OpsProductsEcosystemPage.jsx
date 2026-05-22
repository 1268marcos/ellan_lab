
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { getSeverityBadgeStyle } from "../components/opsVisualTokens";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

const TABS = [
  { id: "overview", label: "Visão geral", hint: "KPIs do ecossistema mundial locker + marketplace" },
  { id: "players", label: "Players", hint: "Redes, carriers, marketplaces, food delivery" },
  { id: "eligibility", label: "Elegibilidade", hint: "Quais categorias podem usar cada rede" },
  { id: "actions", label: "Ações OPS", hint: "Seed, sync parceiros e ligações B2B" },
];

const TYPE_LABELS = {
  LOCKER_NETWORK: "Rede locker",
  MARKETPLACE: "Marketplace",
  CARRIER: "Carrier",
  POSTAL: "Postal",
  RETAIL_PUDO: "PUDO / retalho",
  FOOD_DELIVERY: "Food delivery",
  AGGREGATOR: "Agregador",
  HARDWARE: "Hardware",
  LAST_MILE_SAAS: "SaaS logística",
  NETWORK_OPERATOR: "Operador de rede",
};

function parseError(payload, fallback = "Operação falhou.", status) {
  if (status === 401) return "Sessão inválida. Faça login com admin_operacao.";
  if (status === 403) return "Sem permissão (admin_operacao).";
  if (payload?.detail?.message) return String(payload.detail.message);
  if (typeof payload?.detail === "string") return payload.detail;
  return fallback;
}

async function fetchJson(url, headers) {
  const response = await fetch(url, { headers: { Accept: "application/json", ...headers } });
  const data = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, data };
}

function KpiCard({ label, value, sub }) {
  return (
    <div style={kpiCard}>
      <div style={kpiLabel}>{label}</div>
      <div style={kpiValue}>{value}</div>
      {sub ? <div style={kpiSub}>{sub}</div> : null}
    </div>
  );
}

function TypeBadge({ type }) {
  const label = TYPE_LABELS[type] || type;
  return <span style={typeBadge}>{label}</span>;
}

export default function OpsProductsEcosystemPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = TABS.some((t) => t.id === searchParams.get("tab")) ? searchParams.get("tab") : "overview";

  const [overview, setOverview] = useState(null);
  const [players, setPlayers] = useState([]);
  const [eligibility, setEligibility] = useState([]);
  const [playerTypes, setPlayerTypes] = useState([]);
  const [source, setSource] = useState("registry");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [filter, setFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [integrations, setIntegrations] = useState([]);
  const [eligForm, setEligForm] = useState({
    category_id: "LOCKER_PARCEL",
    player_code: "INPOST",
    eligibility: "PREFERRED",
    notes: "",
  });

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const setTab = (id) => {
    setSearchParams({ tab: id });
    setError("");
    setSuccess("");
  };

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const [ov, pl, el, ref] = await Promise.all([
        fetchJson(`${BASE}/catalog-professional/ecosystem-overview`, authHeaders),
        fetchJson(`${BASE}/catalog-professional/global-players?limit=500`, authHeaders),
        fetchJson(`${BASE}/catalog-professional/category-eligibility`, authHeaders),
        fetchJson(`${BASE}/catalog-professional/players-reference`, authHeaders),
      ]);
      if (ov.ok) setOverview(ov.data);
      else setError(parseError(ov.data, "Falha ao carregar visão geral.", ov.status));
      if (pl.ok) setPlayers(Array.isArray(pl.data.items) ? pl.data.items : []);
      if (el.ok) setEligibility(Array.isArray(el.data.items) ? el.data.items : []);
      if (ref.ok) {
        setSource(ref.data.source || "registry");
        setPlayerTypes(ref.data.player_types || []);
      }
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }, [token, authHeaders]);

  useEffect(() => {
    void load();
  }, [load]);

  const q = filter.trim().toLowerCase();
  const filteredPlayers = useMemo(() => {
    let list = players;
    if (typeFilter) list = list.filter((p) => p.player_type === typeFilter);
    if (!q) return list;
    return list.filter(
      (p) =>
        p.code.toLowerCase().includes(q) ||
        p.name.toLowerCase().includes(q) ||
        (p.operator_id || "").toLowerCase().includes(q),
    );
  }, [players, q, typeFilter]);

  async function runAction(path, label) {
    if (!token) return;
    setBusy(label);
    setError("");
    setSuccess("");
    try {
      const r = await fetch(`${BASE}/catalog-professional/${path}`, {
        method: "POST",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(data, `${label} falhou.`));
      setSuccess(`${label} concluído.`);
      await load();
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setBusy("");
    }
  }

  async function openPlayerDetail(code) {
    setSelectedPlayer(code);
    setIntegrations([]);
    const r = await fetchJson(
      `${BASE}/catalog-professional/global-players/${encodeURIComponent(code)}/integrations`,
      authHeaders,
    );
    if (r.ok) setIntegrations(r.data.items || []);
  }

  async function saveEligibility(e) {
    e.preventDefault();
    if (!token) return;
    setBusy("eligibility");
    try {
      const r = await fetch(`${BASE}/catalog-professional/category-eligibility`, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify(eligForm),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(data));
      setSuccess(`Elegibilidade ${eligForm.player_code} → ${eligForm.category_id} criada.`);
      await load();
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setBusy("");
    }
  }

  const activeTab = TABS.find((t) => t.id === tab) || TABS[0];

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Ecossistema mundial" versionLabel="GLOBAL" />
        <p style={muted}>
          Hub de valor: players locker/marketplace, elegibilidade por categoria, integrações B2B e readiness
          operacional. Fonte: <strong>{source}</strong>.
        </p>

        <nav style={breadcrumbRow} aria-label="Navegação catálogo">
          <Link to="/ops/products/professional" style={breadcrumbLink}>
            PIM profissional
          </Link>
          <Link to="/ops/products/catalog" style={breadcrumbLink}>
            Catálogo SKU
          </Link>
          <Link to="/ops/products/categories" style={breadcrumbLink}>
            Categorias
          </Link>
        </nav>

        <div style={tabRow} role="tablist">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              style={tabButton(tab === t.id)}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <p style={tabHint}>{activeTab.hint}</p>

        <div style={toolbarRow}>
          <button type="button" style={btnPrimary} disabled={loading || !token} onClick={() => void load()}>
            {loading ? "Carregando…" : "Atualizar"}
          </button>
        </div>

        {success ? <div style={successBox}>{success}</div> : null}
        {error ? <pre style={errBox}>{error}</pre> : null}
        {!token ? <p style={muted}>Login admin_operacao necessário.</p> : null}

        {token && tab === "overview" && overview ? (
          <>
            <div style={kpiGrid}>
              <KpiCard label="Players" value={overview.players_total} sub={`${overview.players_locker_ready} locker-ready`} />
              <KpiCard label="Taxonomias" value={overview.taxonomy_mappings} sub="categoria → rede" />
              <KpiCard label="Listings" value={overview.channel_listings} sub="SKUs em canais" />
              <KpiCard label="Elegibilidade" value={overview.eligibility_rules} sub="regras categoria×player" />
              <KpiCard label="Integrações" value={overview.integration_targets} sub="targets mapeados" />
              <KpiCard
                label="Parceiros B2B"
                value={(overview.ecommerce_partner_links || 0) + (overview.logistics_partner_links || 0)}
                sub={`ecom ${overview.ecommerce_partner_links} · log ${overview.logistics_partner_links}`}
              />
            </div>
            {overview.players_by_type?.length ? (
              <div style={chipSection}>
                <div style={sectionTitle}>Players por segmento</div>
                <div style={chipRow}>
                  {overview.players_by_type.map((row) => (
                    <span key={row.player_type} style={chip}>
                      {TYPE_LABELS[row.player_type] || row.player_type}: {row.count}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
            {overview.top_players?.length ? (
              <div style={{ marginTop: 16 }}>
                <div style={sectionTitle}>Destaques locker / marketplace</div>
                <div style={playerGrid}>
                  {overview.top_players.map((p) => (
                    <button
                      key={p.code}
                      type="button"
                      style={playerCardBtn}
                      onClick={() => {
                        setTab("players");
                        void openPlayerDetail(p.code);
                      }}
                    >
                      <div style={playerCardTitle}>{p.name}</div>
                      <div style={playerCardCode}>{p.code}</div>
                      <TypeBadge type={p.player_type} />
                      {p.operator_id ? <div style={kpiSub}>{p.operator_id}</div> : null}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </>
        ) : null}

        {token && tab === "players" ? (
          <>
            <div style={toolbarRow}>
              <label style={searchLabel}>
                Buscar
                <input style={inp} value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="nome, código, OP-…" />
              </label>
              <label style={searchLabel}>
                Segmento
                <select style={inp} value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                  <option value="">Todos</option>
                  {playerTypes.map((t) => (
                    <option key={t} value={t}>
                      {TYPE_LABELS[t] || t}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div style={playerGrid}>
              {filteredPlayers.map((p) => (
                <button
                  key={p.code}
                  type="button"
                  style={{
                    ...playerCardBtn,
                    border: selectedPlayer === p.code ? "1px solid #3B82F6" : playerCardBtn.border,
                  }}
                  onClick={() => void openPlayerDetail(p.code)}
                >
                  <div style={playerCardTitle}>{p.name}</div>
                  <div style={playerCardCode}>{p.code}</div>
                  <TypeBadge type={p.player_type} />
                  <div style={flagRow}>
                    {p.supports_lockers ? <span style={getSeverityBadgeStyle("OK")}>Locker</span> : null}
                    {p.supports_marketplace ? <span style={getSeverityBadgeStyle("WARN")}>MKT</span> : null}
                    {p.supports_food_delivery ? <span style={getSeverityBadgeStyle("HIGH")}>Food</span> : null}
                    {p.supports_pudo ? <span style={getSeverityBadgeStyle("WARN")}>PUDO</span> : null}
                  </div>
                  {p.regions?.length ? (
                    <div style={kpiSub}>{p.regions.slice(0, 4).join(" · ")}</div>
                  ) : null}
                </button>
              ))}
            </div>
            {selectedPlayer ? (
              <div style={detailPanel}>
                <div style={sectionTitle}>Integrações — {selectedPlayer}</div>
                {!integrations.length ? (
                  <p style={muted}>Sem targets. Execute sync parceiros na aba Ações.</p>
                ) : (
                  <ul style={listPlain}>
                    {integrations.map((it) => (
                      <li key={`${it.target_type}-${it.target_key}`}>
                        <code>{it.target_type}</code> → <code>{it.target_key}</code>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : null}
          </>
        ) : null}

        {token && tab === "eligibility" ? (
          <>
            <form onSubmit={(e) => void saveEligibility(e)} style={formGrid}>
              <label style={lbl}>
                Categoria
                <input
                  style={inp}
                  value={eligForm.category_id}
                  onChange={(e) => setEligForm({ ...eligForm, category_id: e.target.value })}
                />
              </label>
              <label style={lbl}>
                Player
                <input
                  style={inp}
                  value={eligForm.player_code}
                  onChange={(e) => setEligForm({ ...eligForm, player_code: e.target.value })}
                />
              </label>
              <label style={lbl}>
                Nível
                <select
                  style={inp}
                  value={eligForm.eligibility}
                  onChange={(e) => setEligForm({ ...eligForm, eligibility: e.target.value })}
                >
                  <option value="PREFERRED">PREFERRED</option>
                  <option value="ALLOWED">ALLOWED</option>
                  <option value="RESTRICTED">RESTRICTED</option>
                </select>
              </label>
              <button type="submit" style={btnPrimary} disabled={busy === "eligibility"}>
                Adicionar regra
              </button>
            </form>
            <div style={tableWrap}>
              <table style={table}>
                <thead>
                  <tr>
                    <th style={th}>Categoria</th>
                    <th style={th}>Player</th>
                    <th style={th}>Nível</th>
                  </tr>
                </thead>
                <tbody>
                  {eligibility.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>
                        <code>{row.category_id}</code>
                        {row.category_name ? <div style={kpiSub}>{row.category_name}</div> : null}
                      </td>
                      <td style={tdStyle}>
                        <code>{row.player_code}</code>
                        {row.player_name ? <div style={kpiSub}>{row.player_name}</div> : null}
                      </td>
                      <td style={tdStyle}>
                        <span style={getSeverityBadgeStyle(row.eligibility === "PREFERRED" ? "OK" : "WARN")}>
                          {row.eligibility}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}

        {token && tab === "actions" ? (
          <div style={actionsGrid}>
            <div style={actionCard}>
              <h3 style={h3}>Seed mundial completo</h3>
              <p style={muted}>Players, taxonomias, categorias locker, operadores OP-&#123;code&#125;, parceiros e ligações.</p>
              <button
                type="button"
                style={btnPrimary}
                disabled={!!busy}
                onClick={() => void runAction("seed", "Seed mundial")}
              >
                {busy === "Seed mundial" ? "Aplicando…" : "Executar seed mundial"}
              </button>
            </div>
            <div style={actionCard}>
              <h3 style={h3}>Registo global_players</h3>
              <p style={muted}>Persiste ~90 players + regiões + capacidades.</p>
              <button
                type="button"
                style={btnSecondary}
                disabled={!!busy}
                onClick={() => void runAction("global-players/seed", "Seed players")}
              >
                Seed players
              </button>
            </div>
            <div style={actionCard}>
              <h3 style={h3}>Sync parceiros B2B</h3>
              <p style={muted}>Cria operadores em falta, parceiros e liga ecommerce/logistics.</p>
              <button
                type="button"
                style={btnSecondary}
                disabled={!!busy}
                onClick={() => void runAction("global-players/sync-partners", "Sync parceiros")}
              >
                Sync parceiros
              </button>
            </div>
            <div style={actionCard}>
              <h3 style={h3}>Religar parceiros existentes</h3>
              <p style={muted}>Mapeia codes legados (ex. MERCADOLIVRE) → global_players.</p>
              <button
                type="button"
                style={btnSecondary}
                disabled={!!busy}
                onClick={() => void runAction("global-players/link-partners", "Link parceiros")}
              >
                Link parceiros
              </button>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const muted = { color: "#94A3B8", marginTop: 8, fontSize: 13, lineHeight: 1.45 };
const breadcrumbRow = { display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 };
const breadcrumbLink = {
  padding: "6px 10px",
  borderRadius: 999,
  border: "1px solid #334155",
  background: "#0B1220",
  color: "#93C5FD",
  fontSize: 12,
  fontWeight: 600,
  textDecoration: "none",
};
const tabRow = { display: "flex", flexWrap: "wrap", gap: 8, marginTop: 16 };
const tabHint = { color: "#64748B", fontSize: 12, marginTop: 6 };
const tabButton = (active) => ({
  padding: "8px 14px",
  borderRadius: 999,
  border: active ? "1px solid #1D4ED8" : "1px solid #334155",
  background: active ? "rgba(29,78,216,0.25)" : "#0B1220",
  color: active ? "#BFDBFE" : "#CBD5E1",
  fontWeight: active ? 700 : 600,
  fontSize: 13,
  cursor: "pointer",
});
const toolbarRow = { display: "flex", flexWrap: "wrap", gap: 12, marginTop: 14, alignItems: "flex-end" };
const searchLabel = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1", flex: "1 1 200px" };
const btnPrimary = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const btnSecondary = { padding: "10px 14px", borderRadius: 10, border: "1px solid #334155", background: "#0B1220", color: "#E2E8F0", fontWeight: 600, cursor: "pointer" };
const successBox = { marginTop: 12, background: "rgba(22,163,74,0.15)", color: "#86EFAC", border: "1px solid rgba(34,197,94,0.45)", borderRadius: 10, padding: 10, fontSize: 13 };
const errBox = { marginTop: 12, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10, whiteSpace: "pre-wrap" };
const kpiGrid = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10, marginTop: 16 };
const kpiCard = { background: "#0B1220", border: "1px solid #1E293B", borderRadius: 12, padding: 12 };
const kpiLabel = { fontSize: 11, color: "#94A3B8", textTransform: "uppercase" };
const kpiValue = { fontSize: 22, fontWeight: 800, color: "#F8FAFC", marginTop: 4 };
const kpiSub = { fontSize: 11, color: "#64748B", marginTop: 4 };
const chipSection = { marginTop: 16 };
const sectionTitle = { fontSize: 14, fontWeight: 700, color: "#E2E8F0", marginBottom: 8 };
const chipRow = { display: "flex", flexWrap: "wrap", gap: 8 };
const chip = { padding: "4px 10px", borderRadius: 999, background: "#1E293B", fontSize: 12, color: "#CBD5E1" };
const playerGrid = { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 10, marginTop: 12 };
const playerCardBtn = {
  textAlign: "left",
  padding: 12,
  borderRadius: 12,
  border: "1px solid #334155",
  background: "#0B1220",
  color: "#E2E8F0",
  cursor: "pointer",
  display: "grid",
  gap: 6,
};
const playerCardTitle = { fontWeight: 700, fontSize: 13 };
const playerCardCode = { fontSize: 11, color: "#93C5FD", fontFamily: "monospace" };
const typeBadge = { fontSize: 10, color: "#A5B4FC", fontWeight: 600 };
const flagRow = { display: "flex", flexWrap: "wrap", gap: 4 };
const detailPanel = { marginTop: 16, padding: 12, border: "1px solid #334155", borderRadius: 12, background: "#020617" };
const listPlain = { margin: 0, paddingLeft: 18, color: "#CBD5E1", fontSize: 12 };
const formGrid = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10, marginTop: 12, alignItems: "end" };
const lbl = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inp = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const tableWrap = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const table = { width: "100%", borderCollapse: "collapse", minWidth: 520 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B" };
const tdStyle = { padding: 10, fontSize: 12, borderBottom: "1px solid #1E293B" };
const actionsGrid = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12, marginTop: 16 };
const actionCard = { padding: 14, border: "1px solid #334155", borderRadius: 12, background: "#0B1220" };
const h3 = { margin: "0 0 8px", fontSize: 15, color: "#F8FAFC" };
