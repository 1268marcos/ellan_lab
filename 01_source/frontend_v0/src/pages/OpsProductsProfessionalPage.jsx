
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { getSeverityBadgeStyle } from "../components/opsVisualTokens";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

const TABS = [
  {
    id: "taxonomy",
    label: "Taxonomias globais",
    hint: "GS1 GPC, Amazon, Mercado Livre, InPost, DHL…",
  },
  {
    id: "channels",
    label: "Canais & marketplaces",
    hint: "SKU central → listing por rede (ML, Magalu, Amazon Hub…)",
  },
  {
    id: "attributes",
    label: "Atributos PIM",
    hint: "Definições por categoria (marca, tamanho, compliance)",
  },
];

/** Fallback se /players-reference indisponível */
const FALLBACK_TAXONOMY_SCHEMES = [
  "GS1_GPC", "UNSPSC", "AMAZON_US", "AMAZON_EU", "AMAZON_ES", "MERCADO_LIVRE", "MAGALU", "WORTEN",
  "EL_CORTE_INGLES", "INPOST", "DHL_PACKSTATION", "DHL_PARCEL", "DPD", "DPD_LOCKER", "CORREIOS", "CTT",
  "ROYAL_MAIL", "LA_POSTE", "COLISSIMO", "HERMES_DE", "PACKETA", "VINTED", "VINTED_GO",
];
const FALLBACK_CHANNEL_CODES = [
  "MERCADO_LIVRE", "MAGALU", "AMAZON_HUB", "AMAZON_US", "AMAZON_EU", "WORTEN", "EL_CORTE_INGLES",
  "INPOST", "DHL_PACKSTATION", "DPD", "DPD_LOCKER", "CORREIOS", "CTT", "ROYAL_MAIL", "LA_POSTE",
  "COLISSIMO", "HERMES_DE", "PACKETA", "QUADIENT", "BLOQ_IT", "VINTED_GO", "CAINIAO", "MELHOR_ENVIO",
];

function schemeLabel(code, playerByCode) {
  const p = playerByCode?.[code];
  return p ? `${code} — ${p.name}` : code;
}

const RELATED_LINKS = [
  { to: "/ops/products/ecosystem", label: "Ecossistema mundial" },
  { to: "/ops/products/catalog", label: "Catálogo SKU" },
  { to: "/ops/products/categories", label: "Categorias" },
  { to: "/ops/products/assets", label: "Mídia & barcodes" },
  { to: "/ops/products/bundles", label: "Bundles" },
];

function parseError(payload, fallback = "Não foi possível concluir a operação.", status) {
  if (status === 401) {
    return "Sessão inválida ou expirada. Faça login novamente com perfil admin_operacao.";
  }
  if (status === 403) {
    return "Sem permissão (role admin_operacao necessária).";
  }
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) {
    const d = payload.detail.trim();
    if (d === "missing_or_invalid_token") return "Token ausente ou inválido. Refaça o login.";
    return d;
  }
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) {
      return payload.detail.message.trim();
    }
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) {
      return payload.detail.type.trim();
    }
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

async function fetchJson(url, headers) {
  const response = await fetch(url, { headers: { Accept: "application/json", ...headers } });
  const data = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, data };
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicação com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexão (${endpoint}). Verifique o proxy /api/op e o order_pickup_service (porta 8003).`;
  }
  return raw;
}

function listingStatusSeverity(status) {
  const s = String(status || "").toUpperCase();
  if (s === "ACTIVE") return "OK";
  if (s === "DRAFT") return "WARN";
  if (s === "SUSPENDED" || s === "DELISTED") return "HIGH";
  return "WARN";
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

function StatusBadge({ status }) {
  const sev = listingStatusSeverity(status);
  return <span style={getSeverityBadgeStyle(sev)}>{status}</span>;
}

export default function OpsProductsProfessionalPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = TABS.some((t) => t.id === searchParams.get("tab")) ? searchParams.get("tab") : "taxonomy";

  const [taxonomy, setTaxonomy] = useState([]);
  const [channels, setChannels] = useState([]);
  const [defs, setDefs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState("");
  const [partialWarning, setPartialWarning] = useState("");
  const [success, setSuccess] = useState("");
  const [filter, setFilter] = useState("");
  const [modal, setModal] = useState(null);
  const [taxonomySchemes, setTaxonomySchemes] = useState(FALLBACK_TAXONOMY_SCHEMES);
  const [channelCodes, setChannelCodes] = useState(FALLBACK_CHANNEL_CODES);
  const [globalPlayers, setGlobalPlayers] = useState([]);

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const playerByCode = useMemo(() => {
    const m = {};
    for (const p of globalPlayers) {
      if (p?.code) m[p.code] = p;
    }
    return m;
  }, [globalPlayers]);

  const setTab = (id) => {
    setSearchParams({ tab: id });
    setFilter("");
    setSuccess("");
  };

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    setPartialWarning("");
    const errors = [];
    try {
      const [tr, cr, dr, pr] = await Promise.all([
        fetchJson(`${BASE}/catalog-professional/category-taxonomy`, authHeaders),
        fetchJson(`${BASE}/catalog-professional/channel-listings?limit=200`, authHeaders),
        fetchJson(`${BASE}/catalog-professional/attribute-definitions`, authHeaders),
        fetchJson(`${BASE}/catalog-professional/players-reference`, authHeaders),
      ]);

      if (pr.ok) {
        const schemes = Array.isArray(pr.data.taxonomy_schemes) ? pr.data.taxonomy_schemes : [];
        const channels = Array.isArray(pr.data.channel_codes) ? pr.data.channel_codes : [];
        if (schemes.length) setTaxonomySchemes(schemes);
        if (channels.length) setChannelCodes(channels);
        setGlobalPlayers(Array.isArray(pr.data.players) ? pr.data.players : []);
      }

      if (tr.ok) {
        setTaxonomy(Array.isArray(tr.data.items) ? tr.data.items : []);
      } else {
        setTaxonomy([]);
        errors.push(`Taxonomias (${tr.status}): ${parseError(tr.data, "Falha ao carregar taxonomias.", tr.status)}`);
      }

      if (cr.ok) {
        setChannels(Array.isArray(cr.data.items) ? cr.data.items : []);
      } else {
        setChannels([]);
        errors.push(`Canais (${cr.status}): ${parseError(cr.data, "Falha ao carregar canais.", cr.status)}`);
      }

      if (dr.ok) {
        setDefs(Array.isArray(dr.data.items) ? dr.data.items : []);
      } else {
        setDefs([]);
        errors.push(`Atributos (${dr.status}): ${parseError(dr.data, "Falha ao carregar atributos.", dr.status)}`);
      }

      const tabPrefix = { taxonomy: "Taxonomias", channels: "Canais", attributes: "Atributos" }[tab];
      const tabErrors = errors.filter((line) => line.startsWith(tabPrefix));
      const otherErrors = errors.filter((line) => !line.startsWith(tabPrefix));
      if (tabErrors.length) {
        setError(tabErrors.join("\n"));
      }
      if (otherErrors.length) {
        setPartialWarning(otherErrors.join(" · "));
      }
    } catch (e) {
      setError(normalizeNetworkError(e, `${BASE}/catalog-professional`));
      setTaxonomy([]);
      setChannels([]);
      setDefs([]);
    } finally {
      setLoading(false);
    }
  }, [token, authHeaders]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runSeed() {
    if (!token) return;
    setSeeding(true);
    setError("");
    setSuccess("");
    try {
      const r = await fetch(`${BASE}/catalog-professional/seed`, {
        method: "POST",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(data, "Seed profissional falhou."));
      setSuccess(
        `Seed mundial: ${data.taxonomy_rows ?? 0} taxonomias, ${data.channel_rows ?? 0} canais, ${data.attribute_definitions ?? 0} atributos` +
          (data.locker_categories_created ? `, ${data.locker_categories_created} categorias locker.` : "."),
      );
      await load();
    } catch (e) {
      setError(normalizeNetworkError(e, `${BASE}/catalog-professional/seed`));
    } finally {
      setSeeding(false);
    }
  }

  const q = filter.trim().toLowerCase();

  const filteredTaxonomy = useMemo(() => {
    if (!q) return taxonomy;
    return taxonomy.filter(
      (r) =>
        String(r.category_id).toLowerCase().includes(q) ||
        String(r.taxonomy_scheme).toLowerCase().includes(q) ||
        String(r.external_code).toLowerCase().includes(q) ||
        String(r.external_name || "").toLowerCase().includes(q),
    );
  }, [taxonomy, q]);

  const filteredChannels = useMemo(() => {
    if (!q) return channels;
    return channels.filter(
      (r) =>
        String(r.product_id).toLowerCase().includes(q) ||
        String(r.channel_code).toLowerCase().includes(q) ||
        String(r.external_sku || "").toLowerCase().includes(q) ||
        String(r.listing_status).toLowerCase().includes(q),
    );
  }, [channels, q]);

  const filteredDefs = useMemo(() => {
    if (!q) return defs;
    return defs.filter(
      (d) =>
        String(d.category_id || "GLOBAL").toLowerCase().includes(q) ||
        String(d.attr_key).toLowerCase().includes(q) ||
        String(d.attr_label).toLowerCase().includes(q),
    );
  }, [defs, q]);

  const activeTabMeta = TABS.find((t) => t.id === tab) || TABS[0];

  const openCreateTaxonomy = () => {
    setModal({
      kind: "taxonomy",
      category_id: "ELECTRONICS",
      taxonomy_scheme: "MERCADO_LIVRE",
      external_code: "",
      external_name: "",
      country_code: "BR",
      is_primary: false,
    });
  };

  const openCreateChannel = () => {
    setModal({
      kind: "channel",
      product_id: "",
      channel_code: "MERCADO_LIVRE",
      external_sku: "",
      listing_status: "DRAFT",
      price_reais: "",
    });
  };

  const saveModal = async () => {
    if (!token || !modal) return;
    setError("");
    setSuccess("");
    try {
      if (modal.kind === "taxonomy") {
        const r = await fetch(`${BASE}/catalog-professional/category-taxonomy`, {
          method: "POST",
          headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
          body: JSON.stringify({
            category_id: modal.category_id.trim(),
            taxonomy_scheme: modal.taxonomy_scheme,
            external_code: modal.external_code.trim(),
            external_name: modal.external_name.trim() || null,
            country_code: modal.country_code.trim() || null,
            is_primary: Boolean(modal.is_primary),
          }),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(parseError(data, "Falha ao criar taxonomia."));
        setSuccess(`Taxonomia ${modal.taxonomy_scheme} vinculada à categoria ${modal.category_id}.`);
      } else {
        const reais = Number(String(modal.price_reais || "").replace(",", "."));
        const r = await fetch(`${BASE}/catalog-professional/channel-listings`, {
          method: "POST",
          headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
          body: JSON.stringify({
            product_id: modal.product_id.trim(),
            channel_code: modal.channel_code,
            external_sku: modal.external_sku.trim() || null,
            listing_status: modal.listing_status,
            price_cents: Number.isFinite(reais) && reais >= 0 ? Math.round(reais * 100) : null,
          }),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(parseError(data, "Falha ao criar listing."));
        setSuccess(`Listing ${modal.channel_code} criado para ${modal.product_id}.`);
      }
      setModal(null);
      await load();
    } catch (e) {
      setError(normalizeNetworkError(e, BASE));
    }
  };

  const onDeleteTaxonomy = async (row) => {
    if (!token || !window.confirm(`Remover mapeamento ${row.taxonomy_scheme} → ${row.category_id}?`)) return;
    try {
      const r = await fetch(`${BASE}/catalog-professional/category-taxonomy/${encodeURIComponent(row.id)}`, {
        method: "DELETE",
        headers: { Accept: "application/json", ...authHeaders },
      });
      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        throw new Error(parseError(data));
      }
      setSuccess("Taxonomia removida.");
      await load();
    } catch (e) {
      setError(normalizeNetworkError(e, BASE));
    }
  };

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Catálogo profissional mundial" versionLabel="PIM+" />
        <p style={muted}>
          Integração multi-rede: taxonomias externas, listings por marketplace/carrier e atributos extensíveis.
          API: <code style={codeInline}>{BASE}/catalog-professional</code> (role <code style={codeInline}>admin_operacao</code>).
        </p>

        <nav style={breadcrumbRow} aria-label="Navegação relacionada">
          {RELATED_LINKS.map((l) => (
            <Link key={l.to} to={l.to} style={breadcrumbLink}>
              {l.label}
            </Link>
          ))}
        </nav>

        <div style={kpiGrid}>
          <KpiCard label="Taxonomias" value={taxonomy.length} sub="mapeamentos categoria → rede" />
          <KpiCard label="Listings" value={channels.length} sub="SKUs em canais externos" />
          <KpiCard label="Atributos" value={defs.length} sub="definições PIM por categoria" />
          <KpiCard
            label="Players"
            value={globalPlayers.length || taxonomySchemes.length}
            sub="InPost, DHL, Magalu, ML, Amazon, Worten, ECI, Correios, CTT…"
          />
        </div>

        <div style={tabRow} role="tablist" aria-label="Seções do catálogo profissional">
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
        <p style={tabHint}>{activeTabMeta.hint}</p>

        <div style={toolbarRow}>
          <label style={searchLabel}>
            Buscar
            <input
              style={inp}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="categoria, canal, SKU, código…"
              aria-label="Filtrar resultados da aba atual"
            />
          </label>
          <div style={rowActions}>
            <button type="button" style={btnPrimary} disabled={loading || !token} onClick={() => void load()}>
              {loading ? "Carregando…" : "Atualizar"}
            </button>
            <button type="button" style={btnSecondary} disabled={seeding || !token} onClick={() => void runSeed()}>
              {seeding ? "Aplicando seed…" : "Seed demo mundial"}
            </button>
            {tab === "taxonomy" ? (
              <button type="button" style={btnSecondary} disabled={!token} onClick={openCreateTaxonomy}>
                Nova taxonomia
              </button>
            ) : null}
            {tab === "channels" ? (
              <button type="button" style={btnSecondary} disabled={!token} onClick={openCreateChannel}>
                Novo listing
              </button>
            ) : null}
          </div>
        </div>

        {success ? <div style={successBox}>{success}</div> : null}
        {partialWarning ? <div style={warnBox}>{partialWarning}</div> : null}
        {error ? <pre style={errBox}>{error}</pre> : null}
        {!token ? <p style={muted}>Faça login com perfil admin_operacao para operar este módulo.</p> : null}

        {token && tab === "taxonomy" ? (
          <>
            {!loading && !filteredTaxonomy.length && !error ? (
              <p style={muted}>Nenhuma taxonomia. Use &quot;Seed demo mundial&quot; ou &quot;Nova taxonomia&quot;.</p>
            ) : null}
            {filteredTaxonomy.length > 0 ? (
              <div style={tableWrap}>
                <table style={table}>
                  <thead>
                    <tr>
                      <th style={th}>Categoria</th>
                      <th style={th}>Rede / scheme</th>
                      <th style={th}>Código externo</th>
                      <th style={th}>Nome</th>
                      <th style={th}>País</th>
                      <th style={th}>Primária</th>
                      <th style={th}>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTaxonomy.map((r) => (
                      <tr key={r.id}>
                        <td style={tdStyle}>
                          <code style={codeStyle}>{r.category_id}</code>
                        </td>
                        <td style={tdStyle}>{r.taxonomy_scheme}</td>
                        <td style={tdStyle}>{r.external_code}</td>
                        <td style={tdStyle}>{r.external_name || "—"}</td>
                        <td style={tdStyle}>{r.country_code || "—"}</td>
                        <td style={tdStyle}>{r.is_primary ? "Sim" : "—"}</td>
                        <td style={tdStyle}>
                          <button type="button" style={btnSmDanger} onClick={() => void onDeleteTaxonomy(r)}>
                            Excluir
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </>
        ) : null}

        {token && tab === "channels" ? (
          <>
            {!loading && !filteredChannels.length && !error ? (
              <p style={muted}>Nenhum listing de canal. Crie após ter SKUs no catálogo central.</p>
            ) : null}
            {filteredChannels.length > 0 ? (
              <div style={tableWrap}>
                <table style={table}>
                  <thead>
                    <tr>
                      <th style={th}>SKU (product_id)</th>
                      <th style={th}>Canal</th>
                      <th style={th}>SKU externo</th>
                      <th style={th}>Status</th>
                      <th style={th}>Preço</th>
                      <th style={th}>Sync</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredChannels.map((r) => (
                      <tr key={r.id}>
                        <td style={tdStyle}>
                          <code style={codeStyle}>{r.product_id}</code>
                        </td>
                        <td style={tdStyle}>{r.channel_code}</td>
                        <td style={tdStyle}>{r.external_sku || "—"}</td>
                        <td style={tdStyle}>
                          <StatusBadge status={r.listing_status} />
                        </td>
                        <td style={tdStyle}>
                          {r.price_cents != null
                            ? (r.price_cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
                            : "—"}
                        </td>
                        <td style={tdStyle}>{r.sync_mode || "MANUAL"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </>
        ) : null}

        {token && tab === "attributes" ? (
          <>
            {!loading && !filteredDefs.length && !error ? (
              <p style={muted}>Nenhuma definição de atributo. O seed cria marca, tamanho e compliance por categoria.</p>
            ) : null}
            {filteredDefs.length > 0 ? (
              <div style={tableWrap}>
                <table style={table}>
                  <thead>
                    <tr>
                      <th style={th}>Categoria</th>
                      <th style={th}>Chave</th>
                      <th style={th}>Rótulo</th>
                      <th style={th}>Tipo</th>
                      <th style={th}>Obrigatório</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDefs.map((d) => (
                      <tr key={d.id}>
                        <td style={tdStyle}>
                          <code style={codeStyle}>{d.category_id || "GLOBAL"}</code>
                        </td>
                        <td style={tdStyle}>{d.attr_key}</td>
                        <td style={tdStyle}>{d.attr_label}</td>
                        <td style={tdStyle}>{d.data_type}</td>
                        <td style={tdStyle}>{d.is_required ? "Sim" : "Não"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
            <p style={{ ...muted, marginTop: 12 }}>
              Valores por produto: <code style={codeInline}>PUT {BASE}/catalog-professional/products/{"{sku}"}/attributes</code>
            </p>
          </>
        ) : null}
      </section>

      {modal ? (
        <div style={backdrop} role="presentation" onClick={() => setModal(null)}>
          <div
            style={modalCard}
            role="dialog"
            aria-modal="true"
            aria-labelledby="ops-professional-modal-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="ops-professional-modal-title" style={h2}>
              {modal.kind === "taxonomy" ? "Nova taxonomia global" : "Novo listing de canal"}
            </h2>
            {modal.kind === "taxonomy" ? (
              <>
                <label style={lbl}>
                  category_id
                  <input
                    style={inp}
                    value={modal.category_id}
                    onChange={(e) => setModal({ ...modal, category_id: e.target.value })}
                    placeholder="ex.: ELECTRONICS"
                  />
                </label>
                <label style={lbl}>
                  taxonomy_scheme
                  <select
                    style={inp}
                    value={modal.taxonomy_scheme}
                    onChange={(e) => setModal({ ...modal, taxonomy_scheme: e.target.value })}
                  >
                    {taxonomySchemes.map((s) => (
                      <option key={s} value={s}>
                        {schemeLabel(s, playerByCode)}
                      </option>
                    ))}
                  </select>
                </label>
                <label style={lbl}>
                  external_code
                  <input
                    style={inp}
                    required
                    value={modal.external_code}
                    onChange={(e) => setModal({ ...modal, external_code: e.target.value })}
                  />
                </label>
                <label style={lbl}>
                  external_name
                  <input
                    style={inp}
                    value={modal.external_name}
                    onChange={(e) => setModal({ ...modal, external_name: e.target.value })}
                  />
                </label>
                <label style={lbl}>
                  country_code
                  <input
                    style={inp}
                    maxLength={3}
                    value={modal.country_code}
                    onChange={(e) => setModal({ ...modal, country_code: e.target.value })}
                  />
                </label>
                <label style={{ ...lbl, flexDirection: "row", alignItems: "center", gap: 8 }}>
                  <input
                    type="checkbox"
                    checked={modal.is_primary}
                    onChange={(e) => setModal({ ...modal, is_primary: e.target.checked })}
                  />
                  Mapeamento primário neste scheme
                </label>
              </>
            ) : (
              <>
                <label style={lbl}>
                  product_id (SKU)
                  <input
                    style={inp}
                    required
                    value={modal.product_id}
                    onChange={(e) => setModal({ ...modal, product_id: e.target.value })}
                  />
                </label>
                <label style={lbl}>
                  channel_code
                  <select
                    style={inp}
                    value={modal.channel_code}
                    onChange={(e) => setModal({ ...modal, channel_code: e.target.value })}
                  >
                    {channelCodes.map((c) => (
                      <option key={c} value={c}>
                        {schemeLabel(c, playerByCode)}
                      </option>
                    ))}
                  </select>
                </label>
                <label style={lbl}>
                  external_sku
                  <input
                    style={inp}
                    value={modal.external_sku}
                    onChange={(e) => setModal({ ...modal, external_sku: e.target.value })}
                  />
                </label>
                <label style={lbl}>
                  listing_status
                  <select
                    style={inp}
                    value={modal.listing_status}
                    onChange={(e) => setModal({ ...modal, listing_status: e.target.value })}
                  >
                    {["DRAFT", "ACTIVE", "SUSPENDED", "DELISTED"].map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </label>
                <label style={lbl}>
                  price (R$)
                  <input
                    style={inp}
                    inputMode="decimal"
                    value={modal.price_reais}
                    onChange={(e) => setModal({ ...modal, price_reais: e.target.value })}
                    placeholder="opcional"
                  />
                </label>
              </>
            )}
            <div style={rowActions}>
              <button type="button" style={btnPrimary} onClick={() => void saveModal()}>
                Salvar
              </button>
              <button type="button" style={btnSecondary} onClick={() => setModal(null)}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const muted = { color: "#94A3B8", marginTop: 8, fontSize: 13, lineHeight: 1.45 };
const codeInline = { fontSize: 11, color: "#93C5FD" };
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
const kpiGrid = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10, marginTop: 16 };
const kpiCard = { background: "#0B1220", border: "1px solid #1E293B", borderRadius: 12, padding: 12 };
const kpiLabel = { fontSize: 11, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.04em" };
const kpiValue = { fontSize: 22, fontWeight: 800, color: "#F8FAFC", marginTop: 4 };
const kpiSub = { fontSize: 11, color: "#64748B", marginTop: 4 };
const tabRow = { display: "flex", flexWrap: "wrap", gap: 8, marginTop: 16 };
const tabHint = { color: "#64748B", fontSize: 12, marginTop: 6, marginBottom: 0 };
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
const toolbarRow = {
  display: "flex",
  flexWrap: "wrap",
  gap: 12,
  alignItems: "flex-end",
  justifyContent: "space-between",
  marginTop: 14,
};
const searchLabel = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1", flex: "1 1 220px", minWidth: 180 };
const rowActions = { display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" };
const btnPrimary = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "none",
  background: "#1D4ED8",
  color: "#F8FAFC",
  fontWeight: 700,
  cursor: "pointer",
};
const btnSecondary = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #334155",
  background: "#0B1220",
  color: "#E2E8F0",
  fontWeight: 600,
  cursor: "pointer",
};
const successBox = {
  marginTop: 12,
  background: "rgba(22,163,74,0.15)",
  color: "#86EFAC",
  border: "1px solid rgba(34,197,94,0.45)",
  borderRadius: 10,
  padding: 10,
  fontSize: 13,
};
const warnBox = {
  marginTop: 12,
  background: "rgba(180,83,9,0.12)",
  color: "#FCD34D",
  border: "1px solid rgba(245,158,11,0.45)",
  borderRadius: 10,
  padding: 10,
  fontSize: 12,
};
const errBox = {
  marginTop: 12,
  background: "rgba(220,38,38,0.12)",
  color: "#FCA5A5",
  border: "1px solid rgba(220,38,38,0.45)",
  borderRadius: 10,
  padding: 10,
  whiteSpace: "pre-wrap",
};
const tableWrap = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const table = { width: "100%", borderCollapse: "collapse", minWidth: 720 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B", verticalAlign: "top" };
const codeStyle = { fontSize: 11, color: "#CBD5E1" };
const btnSmDanger = {
  padding: "4px 8px",
  borderRadius: 8,
  border: "1px solid #7f1d1d",
  background: "rgba(127,29,29,0.35)",
  color: "#FCA5A5",
  fontSize: 11,
  cursor: "pointer",
};
const backdrop = {
  position: "fixed",
  inset: 0,
  background: "rgba(15,23,42,0.72)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 50,
  padding: 16,
};
const modalCard = {
  background: "#111827",
  border: "1px solid #334155",
  borderRadius: 14,
  padding: 20,
  maxWidth: 480,
  width: "100%",
  boxSizing: "border-box",
  display: "grid",
  gap: 10,
  maxHeight: "90vh",
  overflowY: "auto",
};
const h2 = { margin: 0, fontSize: 18, color: "#F8FAFC" };
const lbl = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inp = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
