
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsPromotionsPage from "./OpsPromotionsPage";
import OpsPromotionsLabPage from "./OpsPromotionsLabPage";
import {
  apiKeyBannerStyle,
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

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const PAGE_VERSION = "ops/marketing/promotions-admin v1.1-ux";
const TABS = ["overview", "campaigns", "promotions", "redemptions", "lab"];

const TAB_META = {
  overview: {
    label: "Visão geral",
    hint: "KPIs de campanhas, promoções ativas e volume de resgates (24h e total).",
  },
  campaigns: {
    label: "Campanhas",
    hint: "Agrupe promoções por marketplace, carrier, rede locker ou agregador (Magalu, InPost, DHL…).",
  },
  promotions: {
    label: "Promoções",
    hint: "Selecione uma linha para configurar escopos mundiais, exclusões de SKU e status.",
  },
  redemptions: {
    label: "Resgates",
    hint: "Trilha de validações com desconto aplicado por pedido e player.",
  },
  lab: {
    label: "Laboratório",
    hint: "Simular desconto, match de elegíveis, conflitos de escopo e matriz por player (dry-run).",
  },
};

const kpiCardStyle = {
  padding: "12px 14px",
  borderRadius: 12,
  border: "1px solid rgba(96,165,250,0.35)",
  background: "rgba(15,23,42,0.55)",
  display: "grid",
  gap: 4,
};

const chipStyle = {
  display: "inline-block",
  padding: "2px 8px",
  borderRadius: 999,
  fontSize: 11,
  fontWeight: 700,
};

const emptyBoxStyle = {
  marginTop: 12,
  padding: 20,
  borderRadius: 12,
  border: "1px dashed rgba(148,163,184,0.45)",
  background: "rgba(15,23,42,0.35)",
  textAlign: "center",
  color: "#94a3b8",
  fontSize: 13,
  lineHeight: 1.5,
};

function parseError(payload, fallback = "Falha na API.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail?.message) return String(payload.detail.message);
  return fallback;
}

function formatMoney(cents, currency = "BRL") {
  const n = Number(cents);
  if (Number.isNaN(n)) return "—";
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(n / 100);
  } catch {
    return `${(n / 100).toFixed(2)} ${currency}`;
  }
}

function StatusPill({ active }) {
  const on = Boolean(active);
  return (
    <span
      style={{
        ...chipStyle,
        border: on ? "1px solid rgba(34,197,94,0.55)" : "1px solid rgba(248,113,113,0.55)",
        background: on ? "rgba(22,101,52,0.4)" : "rgba(127,29,29,0.35)",
        color: on ? "#86efac" : "#fca5a5",
      }}
    >
      {on ? "Ativa" : "Inativa"}
    </span>
  );
}

function KpiCard({ label, value, sub }) {
  return (
    <div style={kpiCardStyle}>
      <span style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</span>
      <strong style={{ fontSize: 22, color: "#f1f5f9", fontWeight: 700 }}>{value}</strong>
      {sub ? <span style={{ fontSize: 11, color: "#64748b" }}>{sub}</span> : null}
    </div>
  );
}

export default function OpsPromotionsAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = TABS.includes(searchParams.get("tab") || "") ? searchParams.get("tab") : "overview";
  const setTab = (t) => {
    setErr("");
    setSearchParams({ tab: t }, { replace: true });
  };

  const headers = useMemo(
    () => ({
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }),
    [token],
  );

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [okMsg, setOkMsg] = useState("");
  const [overview, setOverview] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [redemptions, setRedemptions] = useState([]);
  const [campForm, setCampForm] = useState({
    code: "",
    name: "",
    channel_family: "MARKETPLACE",
    primary_country: "BR",
  });

  const loadOverview = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${BASE}/promotions/overview`, { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOverview(j);
    } catch (e) {
      setOverview(null);
      setErr(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  const loadCampaigns = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${BASE}/promotion-campaigns?limit=100`, { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setCampaigns(j.items || []);
    } catch (e) {
      setCampaigns([]);
      setErr(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  const loadRedemptions = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${BASE}/promotion-redemptions?limit=50`, { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setRedemptions(j.items || []);
    } catch (e) {
      setRedemptions([]);
      setErr(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  useEffect(() => {
    if (!token) return;
    if (tab === "overview") void loadOverview();
    if (tab === "campaigns") void loadCampaigns();
    if (tab === "redemptions") void loadRedemptions();
  }, [tab, token, loadOverview, loadCampaigns, loadRedemptions]);

  async function runWorldSeed() {
    if (!canMutate) return;
    setLoading(true);
    setErr("");
    setOkMsg("");
    try {
      const r = await fetch(`${BASE}/promotions/seed-world`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOkMsg(
        `Seed mundial aplicado: ${j.campaigns_inserted} campanhas, ${j.promotions_inserted} promoções, ${j.scopes_inserted} escopos.`,
      );
      await loadOverview();
      if (tab === "campaigns") await loadCampaigns();
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  async function createCampaign(e) {
    e.preventDefault();
    if (!canMutate) return;
    const body = {
      code: campForm.code.trim(),
      name: campForm.name.trim(),
      channel_family: campForm.channel_family,
      primary_country: campForm.primary_country || null,
      valid_from: new Date().toISOString(),
    };
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${BASE}/promotion-campaigns`, { method: "POST", headers, body: JSON.stringify(body) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOkMsg(`Campanha ${j.code} criada com sucesso.`);
      setCampForm({ code: "", name: "", channel_family: "MARKETPLACE", primary_country: "BR" });
      await loadCampaigns();
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  const meta = TAB_META[tab] || TAB_META.overview;

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
          <Link to="/ops/products/pricing-fiscal" style={crossShortcutLinkStyle}>
            API lab PR3
          </Link>
          <Link to="/ops/products/bundles" style={crossShortcutLinkStyle}>
            Bundles
          </Link>
          <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>
            Parceiros
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Marketing / Promoções"
          versionLabel={PAGE_VERSION}
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Hub mundial: campanhas, escopos por player/país (InPost, DHL, Magalu, Mercado Livre, Amazon…), promoções e
          resgates. API <code style={{ color: "#e2e8f0" }}>{BASE}</code> — escrita com{" "}
          <code style={{ color: "#e2e8f0" }}>admin_operacao</code>.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <div>
              <h3 style={{ margin: 0, fontSize: 14 }}>Área de trabalho</h3>
              <p style={{ ...summary24hHintStyle, margin: "4px 0 0" }}>{meta.hint}</p>
            </div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {TABS.map((t) => (
                <button key={t} type="button" style={tabButtonStyle(tab === t)} onClick={() => setTab(t)}>
                  {TAB_META[t].label}
                </button>
              ))}
            </div>
          </div>

          <div style={toolbarStyle}>
            {tab !== "promotions" ? (
              <button
                type="button"
                style={buttonGhostStyle}
                onClick={() => {
                  if (tab === "overview") void loadOverview();
                  if (tab === "campaigns") void loadCampaigns();
                  if (tab === "redemptions") void loadRedemptions();
                }}
                disabled={loading || !token}
              >
                {loading ? "Atualizando…" : "Atualizar"}
              </button>
            ) : null}
            {canMutate ? (
              <button type="button" style={buttonGhostStyle} onClick={() => void runWorldSeed()} disabled={loading}>
                Seed mundial
              </button>
            ) : null}
            {tab === "promotions" && (
              <button type="button" style={buttonPrimaryStyle} onClick={() => setTab("overview")}>
                Ver KPIs
              </button>
            )}
          </div>
        </section>

        {err ? (
          <div style={{ ...criticalBannerStyle, marginTop: 12 }} role="alert">
            {err}
          </div>
        ) : null}
        {okMsg ? <p style={okBannerStyle}>{okMsg}</p> : null}
        {!token ? (
          <p style={{ ...summary24hHintStyle, marginTop: 10 }}>Faça login com perfil que tenha acesso OPS.</p>
        ) : null}
        {token && !canMutate ? (
          <p style={{ ...apiKeyBannerStyle, marginTop: 10 }}>
            Modo leitura (auditoria). Escrita, seed e criação exigem <strong>admin_operacao</strong>.
          </p>
        ) : null}

        {tab === "overview" && (
          <section style={{ ...opsSanityCardStyle, marginTop: 12 }}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Painel operacional</h3>
              {loading ? <span style={summary24hHintStyle}>Carregando…</span> : null}
            </div>
            {overview ? (
              <>
                <div
                  style={{
                    display: "grid",
                    gap: 10,
                    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                  }}
                >
                  <KpiCard
                    label="Promoções ativas"
                    value={`${overview.promotions_active}`}
                    sub={`de ${overview.promotions_total} cadastradas`}
                  />
                  <KpiCard
                    label="Campanhas ativas"
                    value={`${overview.campaigns_active}`}
                    sub={`de ${overview.campaigns_total} no catálogo`}
                  />
                  <KpiCard label="Resgates 24h" value={String(overview.redemptions_24h)} sub="validações recentes" />
                  <KpiCard label="Resgates total" value={String(overview.redemptions_total)} sub="histórico acumulado" />
                </div>
                {overview.top_promotion_codes?.length ? (
                  <div style={{ marginTop: 14 }}>
                    <h4 style={{ margin: "0 0 8px", fontSize: 13, color: "#cbd5e1" }}>Top códigos (resgates)</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {overview.top_promotion_codes.map((row) => (
                        <span
                          key={row.code}
                          style={{
                            ...chipStyle,
                            border: "1px solid rgba(148,163,184,0.4)",
                            background: "rgba(30,41,59,0.6)",
                            color: "#e2e8f0",
                          }}
                        >
                          {row.code}: {row.redemptions}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {overview.player_segments?.length ? (
                  <div style={{ marginTop: 14 }}>
                    <h4 style={{ margin: "0 0 8px", fontSize: 13, color: "#cbd5e1" }}>Segmentos (catálogo global)</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {overview.player_segments.map((row) => (
                        <span
                          key={row.segment}
                          style={{
                            ...chipStyle,
                            border: "1px solid rgba(148,163,184,0.4)",
                            color: "#cbd5e1",
                          }}
                        >
                          {row.segment}: {row.count}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {overview.featured_locker_players?.length ? (
                  <div style={{ marginTop: 14 }}>
                    <h4 style={{ margin: "0 0 8px", fontSize: 13, color: "#cbd5e1" }}>
                      Players locker mundial (catálogo {overview.locker_players_catalog_size ?? "—"})
                    </h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {overview.featured_locker_players.map((code) => (
                        <span
                          key={code}
                          style={{
                            ...chipStyle,
                            border: "1px solid rgba(34,197,94,0.45)",
                            background: "rgba(22,101,52,0.25)",
                            color: "#bbf7d0",
                          }}
                        >
                          {code}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {overview.top_player_scopes?.length ? (
                  <div style={{ marginTop: 14 }}>
                    <h4 style={{ margin: "0 0 8px", fontSize: 13, color: "#cbd5e1" }}>Players com escopo ativo (seed)</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {overview.top_player_scopes.map((row) => (
                        <span
                          key={row.player_code}
                          style={{
                            ...chipStyle,
                            border: "1px solid rgba(96,165,250,0.45)",
                            background: "rgba(30,58,138,0.35)",
                            color: "#bfdbfe",
                          }}
                        >
                          {row.player_code} · {row.scopes}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {overview.player_promotion_matrix?.length ? (
                  <div style={{ marginTop: 14 }}>
                    <h4 style={{ margin: "0 0 8px", fontSize: 13, color: "#cbd5e1" }}>
                      Matriz player → promoções ativas
                    </h4>
                    <p style={{ ...summary24hHintStyle, margin: "0 0 8px" }}>
                      Escopos INCLUDE ativos. Abra a aba{" "}
                      <button type="button" style={{ ...buttonGhostStyle, fontSize: 11, padding: "0 4px" }} onClick={() => setTab("lab")}>
                        Laboratório
                      </button>{" "}
                      para simular e conflitos.
                    </p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {overview.player_promotion_matrix.map((row) => (
                        <span
                          key={row.player_code}
                          style={{
                            ...chipStyle,
                            border: "1px solid rgba(129,140,248,0.55)",
                            background: "rgba(49,46,129,0.45)",
                            color: "#c7d2fe",
                          }}
                        >
                          {row.player_code}: {row.active_promotions}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {!overview.promotions_total && !canMutate ? (
                  <div style={emptyBoxStyle}>
                    Nenhum dado ainda. Peça a um admin para executar <strong>Seed mundial</strong>.
                  </div>
                ) : null}
                {!overview.promotions_total && canMutate ? (
                  <div style={emptyBoxStyle}>
                    Catálogo vazio. Use <strong>Seed mundial</strong> para carregar campanhas demo (Magalu, InPost, DHL…).
                  </div>
                ) : null}
              </>
            ) : !loading && token ? (
              <div style={emptyBoxStyle}>
                Clique em <strong>Atualizar</strong> para carregar os KPIs ou execute o seed na primeira visita.
              </div>
            ) : null}
          </section>
        )}

        {tab === "campaigns" && (
          <section style={{ ...opsSanityCardStyle, marginTop: 12 }}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Campanhas ({campaigns.length})</h3>
            </div>
            {canMutate ? (
              <form onSubmit={createCampaign} style={{ ...healthLocalFilterRowStyle, marginTop: 8 }}>
                <label style={healthLocalFilterFieldStyle}>
                  Código
                  <input
                    value={campForm.code}
                    onChange={(e) => setCampForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
                    style={healthLocalFilterInputStyle}
                    placeholder="MARKETPLACE_BR"
                    required
                  />
                </label>
                <label style={healthLocalFilterFieldStyle}>
                  Nome
                  <input
                    value={campForm.name}
                    onChange={(e) => setCampForm((f) => ({ ...f, name: e.target.value }))}
                    style={healthLocalFilterInputStyle}
                    placeholder="Campanha marketplace BR"
                    required
                  />
                </label>
                <label style={healthLocalFilterFieldStyle}>
                  Família
                  <select
                    value={campForm.channel_family}
                    onChange={(e) => setCampForm((f) => ({ ...f, channel_family: e.target.value }))}
                    style={healthLocalFilterInputStyle}
                  >
                    {["GENERAL", "MARKETPLACE", "LOCKER_NETWORK", "CARRIER", "AGGREGATOR", "PUDO"].map((x) => (
                      <option key={x} value={x}>
                        {x}
                      </option>
                    ))}
                  </select>
                </label>
                <label style={healthLocalFilterFieldStyle}>
                  País
                  <input
                    value={campForm.primary_country}
                    onChange={(e) => setCampForm((f) => ({ ...f, primary_country: e.target.value.toUpperCase() }))}
                    style={healthLocalFilterInputStyle}
                    placeholder="BR"
                    maxLength={8}
                  />
                </label>
                <button type="submit" style={{ ...buttonPrimaryStyle, alignSelf: "end" }} disabled={loading}>
                  Criar campanha
                </button>
              </form>
            ) : null}
            {campaigns.length > 0 ? (
              <div style={{ marginTop: 12, overflowX: "auto" }}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Código</th>
                      <th style={thStyle}>Família</th>
                      <th style={thStyle}>Promoções</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>Nome</th>
                    </tr>
                  </thead>
                  <tbody>
                    {campaigns.map((c) => (
                      <tr key={c.id}>
                        <td style={tdStyle}>
                          <code>{c.code}</code>
                        </td>
                        <td style={tdStyle}>{c.channel_family}</td>
                        <td style={tdStyle}>{c.promotions_count}</td>
                        <td style={tdStyle}>
                          <StatusPill active={c.is_active} />
                        </td>
                        <td style={tdStyle}>{c.name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : !loading ? (
              <div style={emptyBoxStyle}>
                Nenhuma campanha listada. {canMutate ? "Crie acima ou use Seed mundial." : "Aguarde seed pelo admin."}
              </div>
            ) : null}
          </section>
        )}

        {tab === "promotions" && (
          <section style={{ ...opsSanityCardStyle, marginTop: 12, padding: 12 }}>
            <p style={{ ...summary24hHintStyle, margin: "0 0 10px" }}>
              <strong>Fluxo:</strong> 1) Listar promoções → 2) Selecionar linha → 3) Escopos e exclusões no painel inferior.
            </p>
            <OpsPromotionsPage embedded />
          </section>
        )}

        {tab === "lab" && (
          <section style={{ ...opsSanityCardStyle, marginTop: 12, padding: 12 }}>
            <OpsPromotionsLabPage embedded />
          </section>
        )}

        {tab === "redemptions" && (
          <section style={{ ...opsSanityCardStyle, marginTop: 12 }}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Resgates ({redemptions.length})</h3>
            </div>
            {redemptions.length > 0 ? (
              <div style={{ marginTop: 12, overflowX: "auto" }}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Pedido</th>
                      <th style={thStyle}>Player</th>
                      <th style={thStyle}>País</th>
                      <th style={thStyle}>Desconto</th>
                      <th style={thStyle}>Quando</th>
                    </tr>
                  </thead>
                  <tbody>
                    {redemptions.map((r) => (
                      <tr key={r.id}>
                        <td style={tdStyle}>
                          <code style={{ fontSize: 11 }}>{r.order_id}</code>
                        </td>
                        <td style={tdStyle}>{r.player_code || "—"}</td>
                        <td style={tdStyle}>{r.country_code || "—"}</td>
                        <td style={tdStyle}>{formatMoney(r.discount_cents, r.currency || "BRL")}</td>
                        <td style={tdStyle}>{r.redeemed_at ? new Date(r.redeemed_at).toLocaleString("pt-BR") : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : !loading ? (
              <div style={emptyBoxStyle}>
                Nenhum resgate registrado. Validações bem-sucedidas em <strong>POST /promotions/validate</strong> aparecem aqui.
              </div>
            ) : null}
          </section>
        )}
      </section>
    </div>
  );
}
