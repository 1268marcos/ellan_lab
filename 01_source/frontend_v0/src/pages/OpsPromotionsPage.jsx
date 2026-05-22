
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
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
  summary24hHintStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const PAGE_VERSION = "ops/marketing/promotions v0.3-players";
const FEATURED_LOCKER_PLAYERS = [
  "INPOST",
  "DHL",
  "MAGALU",
  "MERCADO_LIVRE",
  "AMAZON",
  "DPD",
  "CORREIOS",
  "CTT",
  "WORTEN",
  "EL_CORTE_INGLES",
];

const PROMO_TYPES = ["PERCENT_OFF", "FIXED_OFF", "BUY_X_GET_Y", "FREE_ITEM", "BUNDLE_DISCOUNT"];

function parseError(payload, fallback = "Falha ao processar resposta da API.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) {
    if (payload.detail.trim() === "Not Found") {
      return "Rota não encontrada no backend. Reinicie o order_pickup_service (porta 8003) e confira POST /promotions/{id}/clone.";
    }
    return payload.detail.trim();
  }
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

function promotionRef(row) {
  const id = String(row?.id || "").trim();
  if (id) return id;
  return String(row?.code || "").trim();
}

function toLocalInputValue(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${d}T${hh}:${mm}`;
}

function toIsoOrNull(localDateTimeValue) {
  const raw = String(localDateTimeValue || "").trim();
  if (!raw) return null;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString();
}

function formatShortIso(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch (_) {
    return String(iso);
  }
}

function formatMoney(cents) {
  const n = Number(cents);
  if (cents == null || cents === "" || Number.isNaN(n)) return "—";
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n / 100);
  } catch {
    return `${(n / 100).toFixed(2)}`;
  }
}

const chipStyle = {
  display: "inline-block",
  padding: "2px 8px",
  borderRadius: 999,
  fontSize: 11,
  fontWeight: 700,
};

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

const emptyBoxStyle = {
  marginTop: 12,
  padding: 16,
  borderRadius: 12,
  border: "1px dashed rgba(148,163,184,0.45)",
  background: "rgba(15,23,42,0.35)",
  textAlign: "center",
  color: "#94a3b8",
  fontSize: 13,
};

export default function OpsPromotionsPage({ embedded = false }) {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const [codeFilter, setCodeFilter] = useState("");
  const [isActiveFilter, setIsActiveFilter] = useState("");
  const [typeLocalFilter, setTypeLocalFilter] = useState("");
  const [fromCreated, setFromCreated] = useState("");
  const [toCreated, setToCreated] = useState("");
  const [limit, setLimit] = useState(25);
  const [offset, setOffset] = useState(0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [okMsg, setOkMsg] = useState("");
  const [listPayload, setListPayload] = useState(null);
  const [patchingId, setPatchingId] = useState("");
  const [cloningId, setCloningId] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [createBusy, setCreateBusy] = useState(false);
  const [createError, setCreateError] = useState("");
  const [formCode, setFormCode] = useState("");
  const [formName, setFormName] = useState("");
  const [formType, setFormType] = useState("PERCENT_OFF");
  const [formDiscountPct, setFormDiscountPct] = useState("10");
  const [formDiscountCents, setFormDiscountCents] = useState("");
  const [formMinOrderCents, setFormMinOrderCents] = useState("0");
  const [formValidFrom, setFormValidFrom] = useState(() => toLocalInputValue(new Date()));
  const [formValidUntil, setFormValidUntil] = useState("");
  const [formConditionsJson, setFormConditionsJson] = useState("{}");

  const [selectedPromotion, setSelectedPromotion] = useState(null);
  const [exclusionsPayload, setExclusionsPayload] = useState(null);
  const [exclusionsLoading, setExclusionsLoading] = useState(false);
  const [exclusionsError, setExclusionsError] = useState("");
  const [exclusionProductId, setExclusionProductId] = useState("");
  const [exclusionBusy, setExclusionBusy] = useState(false);
  const [deletingProductId, setDeletingProductId] = useState("");
  const [scopesPayload, setScopesPayload] = useState(null);
  const [scopesLoading, setScopesLoading] = useState(false);
  const [scopesError, setScopesError] = useState("");
  const [scopeType, setScopeType] = useState("PLAYER");
  const [scopeValue, setScopeValue] = useState("");
  const [scopeBusy, setScopeBusy] = useState(false);
  const [playerCatalog, setPlayerCatalog] = useState([]);

  const loadPlayerCatalog = useCallback(async () => {
    if (!token) return;
    try {
      const url = `${ORDER_PICKUP_BASE}/promotions/locker-players-catalog`;
      const response = await fetch(url, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (response.ok && Array.isArray(data.items)) setPlayerCatalog(data.items);
    } catch {
      setPlayerCatalog([]);
    }
  }, [token, authHeaders]);

  const loadScopes = useCallback(async () => {
    const pid = selectedPromotion?.id;
    if (!token || !pid) return;
    setScopesLoading(true);
    setScopesError("");
    try {
      const url = `${ORDER_PICKUP_BASE}/promotions/${encodeURIComponent(pid)}/scopes`;
      const response = await fetch(url, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setScopesPayload(data);
    } catch (err) {
      setScopesPayload(null);
      setScopesError(String(err?.message || err || "Erro ao carregar escopos."));
    } finally {
      setScopesLoading(false);
    }
  }, [token, authHeaders, selectedPromotion?.id]);

  const loadExclusions = useCallback(async () => {
    const pid = selectedPromotion?.id;
    if (!token || !pid) return;
    setExclusionsLoading(true);
    setExclusionsError("");
    try {
      const url = `${ORDER_PICKUP_BASE}/promotions/${encodeURIComponent(pid)}/product-exclusions`;
      const response = await fetch(url, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setExclusionsPayload(data);
    } catch (err) {
      setExclusionsPayload(null);
      setExclusionsError(String(err?.message || err || "Erro ao carregar exclusões."));
    } finally {
      setExclusionsLoading(false);
    }
  }, [token, authHeaders, selectedPromotion?.id]);

  useEffect(() => {
    if (!selectedPromotion?.id) {
      setExclusionsPayload(null);
      setExclusionsError("");
      setScopesPayload(null);
      setScopesError("");
      return;
    }
    void loadExclusions();
    void loadScopes();
  }, [selectedPromotion?.id, loadExclusions, loadScopes]);

  const loadList = useCallback(async (overrides = {}) => {
    if (!token) return;
    const effLimit = overrides.limit != null ? overrides.limit : limit;
    const effOffset = overrides.offset != null ? overrides.offset : offset;
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      const params = new URLSearchParams();
      params.set("limit", String(Math.max(1, Math.min(500, Number(effLimit) || 25))));
      params.set("offset", String(Math.max(0, Number(effOffset) || 0)));
      const c = String(codeFilter || "").trim();
      if (c) params.set("code", c);
      if (isActiveFilter === "true") params.set("is_active", "true");
      if (isActiveFilter === "false") params.set("is_active", "false");
      const fromIso = toIsoOrNull(fromCreated);
      const toIso = toIsoOrNull(toCreated);
      if (fromIso) params.set("from_date", fromIso);
      if (toIso) params.set("to_date", toIso);
      const url = `${ORDER_PICKUP_BASE}/promotions?${params.toString()}`;
      const response = await fetch(url, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setListPayload(data);
      if (overrides.offset != null) setOffset(overrides.offset);
      if (overrides.limit != null) setLimit(overrides.limit);
    } catch (err) {
      setListPayload(null);
      setError(String(err?.message || err || "Erro ao listar promoções."));
    } finally {
      setLoading(false);
    }
  }, [token, authHeaders, codeFilter, isActiveFilter, fromCreated, toCreated, limit, offset]);

  useEffect(() => {
    if (embedded && token) void loadList({ offset: 0 });
  }, [embedded, token]); // eslint-disable-line react-hooks/exhaustive-deps -- carga inicial na aba Promoções

  useEffect(() => {
    if (token) void loadPlayerCatalog();
  }, [token, loadPlayerCatalog]);

  const rawItems = Array.isArray(listPayload?.items) ? listPayload.items : [];
  const typeNeedle = String(typeLocalFilter || "").trim().toUpperCase();
  const items = typeNeedle ? rawItems.filter((row) => String(row?.type || "").toUpperCase() === typeNeedle) : rawItems;
  const total = Number(listPayload?.total || 0);

  async function runSeed() {
    if (!token || !canMutate) return;
    setLoading(true);
    setError("");
    setOkMsg("");
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}/promotions/seed-world`, {
        method: "POST",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setOkMsg(
        `Seed mundial: ${data.promotions_inserted ?? 0} promoções, ${data.scopes_inserted ?? 0} escopos, ${data.campaigns_inserted ?? 0} campanhas.`,
      );
      await loadList({ offset: 0 });
    } catch (err) {
      setError(String(err?.message || err || "Erro no seed."));
    } finally {
      setLoading(false);
    }
  }

  async function patchStatus(promotionId, nextActive) {
    if (!token || !canMutate) return;
    setPatchingId(promotionId);
    setError("");
    try {
      const url = `${ORDER_PICKUP_BASE}/promotions/${encodeURIComponent(promotionId)}/status`;
      const response = await fetch(url, {
        method: "PATCH",
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({ is_active: Boolean(nextActive), reason: "OpsPromotionsPage" }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      await loadList();
    } catch (err) {
      setError(String(err?.message || err || "Erro ao atualizar status."));
    } finally {
      setPatchingId("");
    }
  }

  async function clonePromotion(row) {
    if (!token || !canMutate) return;
    const base = String(row.code || row.id)
      .trim()
      .toUpperCase()
      .replace(/-COPY\d*$/i, "");
    const suggested = `${base}-COPY`;
    const newCode = window.prompt("Código da cópia:", suggested)?.trim().toUpperCase();
    if (!newCode) return;
    const ref = promotionRef(row);
    if (!ref) {
      setError("Promoção sem id/código — recarregue a lista.");
      return;
    }
    setCloningId(row.id || ref);
    setError("");
    setOkMsg("");
    try {
      const url = `${ORDER_PICKUP_BASE}/promotions/${encodeURIComponent(ref)}/clone`;
      const response = await fetch(url, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({
          new_code: newCode,
          new_name: row.name ? `${row.name} (cópia)` : undefined,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setOkMsg(`Promoção clonada: ${data.promotion_code || newCode}`);
      setOffset(0);
      await loadList();
    } catch (err) {
      setError(String(err?.message || err || "Erro ao clonar promoção."));
    } finally {
      setCloningId("");
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!token || !canMutate) return;
    setCreateBusy(true);
    setCreateError("");
    let conditionsJson = {};
    try {
      conditionsJson = JSON.parse(String(formConditionsJson || "").trim() || "{}");
      if (conditionsJson === null || typeof conditionsJson !== "object" || Array.isArray(conditionsJson)) {
        throw new Error("conditions_json deve ser um objeto JSON.");
      }
    } catch (err) {
      setCreateBusy(false);
      setCreateError(String(err?.message || "JSON inválido em conditions_json."));
      return;
    }
    const validFromIso = toIsoOrNull(formValidFrom);
    if (!validFromIso) {
      setCreateBusy(false);
      setCreateError("Informe valid_from (data/hora válida).");
      return;
    }
    const body = {
      code: String(formCode || "").trim() || null,
      name: String(formName || "").trim(),
      type: String(formType || "").trim(),
      min_order_cents: Math.max(0, Number(formMinOrderCents) || 0),
      conditions_json: conditionsJson,
      valid_from: validFromIso,
    };
    if (!body.name) {
      setCreateBusy(false);
      setCreateError("Nome é obrigatório.");
      return;
    }
    const pct = String(formDiscountPct || "").trim();
    if (pct !== "") body.discount_pct = Number(pct);
    const dc = String(formDiscountCents || "").trim();
    if (dc !== "") body.discount_cents = Math.max(0, Number(dc));
    const vu = toIsoOrNull(formValidUntil);
    if (vu) body.valid_until = vu;

    try {
      const url = `${ORDER_PICKUP_BASE}/promotions`;
      const response = await fetch(url, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify(body),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setShowCreate(false);
      setFormName("");
      setFormCode("");
      setOkMsg("Promoção criada.");
      await loadList({ offset: 0 });
    } catch (err) {
      setCreateError(String(err?.message || err || "Erro ao criar promoção."));
    } finally {
      setCreateBusy(false);
    }
  }

  async function handleAddExclusion(e) {
    e.preventDefault();
    const pid = selectedPromotion?.id;
    if (!token || !pid || !canMutate) return;
    const productId = String(exclusionProductId || "").trim();
    if (!productId) {
      setExclusionsError("Informe o product_id (SKU) a excluir da promoção.");
      return;
    }
    setExclusionBusy(true);
    setExclusionsError("");
    try {
      const url = `${ORDER_PICKUP_BASE}/promotions/${encodeURIComponent(pid)}/product-exclusions`;
      const response = await fetch(url, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({ product_id: productId }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setExclusionProductId("");
      await loadExclusions();
    } catch (err) {
      setExclusionsError(String(err?.message || err || "Erro ao adicionar exclusão."));
    } finally {
      setExclusionBusy(false);
    }
  }

  async function handleRemoveExclusion(productId) {
    const pid = selectedPromotion?.id;
    if (!token || !pid || !canMutate) return;
    setDeletingProductId(productId);
    setExclusionsError("");
    try {
      const url = `${ORDER_PICKUP_BASE}/promotions/${encodeURIComponent(pid)}/product-exclusions/${encodeURIComponent(productId)}`;
      const response = await fetch(url, { method: "DELETE", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      await loadExclusions();
    } catch (err) {
      setExclusionsError(String(err?.message || err || "Erro ao remover exclusão."));
    } finally {
      setDeletingProductId("");
    }
  }

  async function handleAddScope(e) {
    e.preventDefault();
    const pid = selectedPromotion?.id;
    if (!token || !pid || !canMutate) return;
    const sv = String(scopeValue || "").trim();
    if (!sv) {
      setScopesError("Informe scope_value (ex.: INPOST, MAGALU, BR).");
      return;
    }
    setScopeBusy(true);
    setScopesError("");
    try {
      const url = `${ORDER_PICKUP_BASE}/promotions/${encodeURIComponent(pid)}/scopes`;
      const response = await fetch(url, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({ scope_type: scopeType, scope_value: sv, mode: "INCLUDE" }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setScopeValue("");
      await loadScopes();
    } catch (err) {
      setScopesError(String(err?.message || err || "Erro ao adicionar escopo."));
    } finally {
      setScopeBusy(false);
    }
  }

  async function handleRemoveScope(scopeId) {
    const pid = selectedPromotion?.id;
    if (!token || !pid || !canMutate) return;
    setScopeBusy(true);
    try {
      const url = `${ORDER_PICKUP_BASE}/promotions/${encodeURIComponent(pid)}/scopes/${encodeURIComponent(scopeId)}`;
      const response = await fetch(url, { method: "DELETE", headers: { Accept: "application/json", ...authHeaders } });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(parseError(data));
      }
      await loadScopes();
    } catch (err) {
      setScopesError(String(err?.message || err || "Erro ao remover escopo."));
    } finally {
      setScopeBusy(false);
    }
  }

  const inner = (
      <section style={embedded ? { padding: 0, border: "none", background: "transparent" } : cardStyle}>
        {!embedded ? (
          <>
        <OpsPageTitleHeader title="OPS — Marketing / Promoções" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>
          Domínio <code>promotions</code>, <code>promotion_scopes</code>, <code>promotion_product_exclusions</code>.
        </p>
          </>
        ) : null}
        <div style={toolbarStyle}>
          {!embedded ? (
            <Link to="/ops/products/pricing-fiscal" style={crossShortcutLinkStyle}>
              Pricing & fiscal lab
            </Link>
          ) : null}
          <button type="button" style={buttonGhostStyle} onClick={() => void loadList({ offset: 0 })} disabled={loading || !token}>
            {loading ? "Atualizando…" : embedded ? "Atualizar lista" : "Listar"}
          </button>
          {!embedded && canMutate ? (
            <button type="button" style={buttonGhostStyle} onClick={() => void runSeed()} disabled={loading || !token}>
              Seed mundial
            </button>
          ) : null}
          {canMutate ? (
            <button type="button" style={buttonPrimaryStyle} onClick={() => setShowCreate((v) => !v)} disabled={!token}>
              {showCreate ? "Fechar formulário" : "Nova promoção"}
            </button>
          ) : null}
        </div>
        {okMsg ? <p style={okBannerStyle}>{okMsg}</p> : null}
        {error ? (
          <div style={{ ...criticalBannerStyle, marginTop: 10 }} role="alert">
            {error}
          </div>
        ) : null}
        {embedded && token && !canMutate ? (
          <p style={{ ...apiKeyBannerStyle, marginTop: 8 }}>Somente leitura — alterações exigem admin_operacao.</p>
        ) : null}

        <section style={{ ...opsSanityCardStyle, marginTop: 10 }}>
          <p style={{ ...summary24hHintStyle, margin: "0 0 8px" }}>Filtros da listagem (servidor + tipo local).</p>
        <div style={healthLocalFilterRowStyle}>
          <label style={healthLocalFilterFieldStyle}>
            Código (exato)
            <input value={codeFilter} onChange={(e) => setCodeFilter(e.target.value)} placeholder="PR3-PROMO-001" style={healthLocalFilterInputStyle} />
          </label>
          <label style={healthLocalFilterFieldStyle}>
            Ativa
            <select value={isActiveFilter} onChange={(e) => setIsActiveFilter(e.target.value)} style={healthLocalFilterInputStyle}>
              <option value="">Todas</option>
              <option value="true">Sim</option>
              <option value="false">Não</option>
            </select>
          </label>
          <label style={healthLocalFilterFieldStyle}>
            Tipo (filtro local)
            <select value={typeLocalFilter} onChange={(e) => setTypeLocalFilter(e.target.value)} style={healthLocalFilterInputStyle}>
              <option value="">Todos</option>
              {PROMO_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label style={healthLocalFilterFieldStyle}>
            Criado desde
            <input type="datetime-local" value={fromCreated} onChange={(e) => setFromCreated(e.target.value)} style={healthLocalFilterInputStyle} />
          </label>
          <label style={healthLocalFilterFieldStyle}>
            Criado até
            <input type="datetime-local" value={toCreated} onChange={(e) => setToCreated(e.target.value)} style={healthLocalFilterInputStyle} />
          </label>
          <label style={healthLocalFilterFieldStyle}>
            Limite
            <input
              type="number"
              min={1}
              max={500}
              value={limit}
              onChange={(e) => setLimit(Math.max(1, Math.min(500, Number(e.target.value) || 25)))}
              style={healthLocalFilterInputStyle}
            />
          </label>
        </div>
        </section>

        <div style={toolbarStyle}>
          <button
            type="button"
            style={buttonGhostStyle}
            onClick={() => void loadList({ offset: Math.max(0, offset - limit) })}
            disabled={loading || offset <= 0}
          >
            Página anterior
          </button>
          <button
            type="button"
            style={buttonGhostStyle}
            onClick={() => void loadList({ offset: offset + limit })}
            disabled={loading || offset + limit >= total}
          >
            Próxima página
          </button>
          <span style={{ ...mutedTextStyle, marginTop: 0, fontSize: 12 }}>
            offset={offset} total={total}
            {typeLocalFilter ? ` · exibindo ${items.length} na página` : ""}
          </span>
        </div>

        {showCreate ? (
          <form onSubmit={handleCreate} style={{ ...opsSanityCardStyle, marginTop: 12 }}>
            <h3 style={{ margin: "0 0 8px", fontSize: 15 }}>Criar promoção</h3>
            {createError ? (
              <div style={{ ...criticalBannerStyle, marginBottom: 8 }} role="alert">
                {createError}
              </div>
            ) : null}
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                Código
                <input value={formCode} onChange={(e) => setFormCode(e.target.value)} style={healthLocalFilterInputStyle} maxLength={32} />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                Nome *
                <input value={formName} onChange={(e) => setFormName(e.target.value)} style={healthLocalFilterInputStyle} required />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                Tipo *
                <select value={formType} onChange={(e) => setFormType(e.target.value)} style={healthLocalFilterInputStyle}>
                  {PROMO_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                discount_pct
                <input value={formDiscountPct} onChange={(e) => setFormDiscountPct(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                discount_cents
                <input value={formDiscountCents} onChange={(e) => setFormDiscountCents(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                min_order_cents
                <input value={formMinOrderCents} onChange={(e) => setFormMinOrderCents(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                valid_from *
                <input type="datetime-local" value={formValidFrom} onChange={(e) => setFormValidFrom(e.target.value)} style={healthLocalFilterInputStyle} required />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                valid_until
                <input type="datetime-local" value={formValidUntil} onChange={(e) => setFormValidUntil(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
            </div>
            <label style={{ ...healthLocalFilterFieldStyle, marginTop: 10 }}>
              conditions_json
              <textarea value={formConditionsJson} onChange={(e) => setFormConditionsJson(e.target.value)} rows={4} style={{ ...healthLocalFilterInputStyle, fontFamily: "monospace" }} />
            </label>
            <button type="submit" style={{ ...buttonPrimaryStyle, marginTop: 10 }} disabled={createBusy}>
              {createBusy ? "Enviando…" : "Criar"}
            </button>
          </form>
        ) : null}

        {!listPayload && !loading && !error ? (
          <div style={emptyBoxStyle}>
            {embedded ? "Carregando catálogo…" : "Clique em Listar ou use Seed mundial na barra superior."}
          </div>
        ) : !items.length && listPayload ? (
          <div style={emptyBoxStyle}>Nenhuma promoção para os filtros atuais. Ajuste código, status ou datas.</div>
        ) : items.length ? (
          <div style={{ marginTop: 16, overflowX: "auto" }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Selecionar</th>
                  <th style={thStyle}>Código</th>
                  <th style={thStyle}>Tipo</th>
                  <th style={thStyle}>% / valor</th>
                  <th style={thStyle}>Válida de</th>
                  <th style={thStyle}>Até</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Nome</th>
                  <th style={thStyle}>Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.id} style={selectedPromotion?.id === row.id ? { background: "rgba(29, 78, 216, 0.12)" } : undefined}>
                    <td style={tdStyle}>
                      <button
                        type="button"
                        style={buttonGhostStyle}
                        onClick={() =>
                          setSelectedPromotion((cur) =>
                            cur?.id === row.id ? null : { id: row.id, code: row.code || "", name: row.name || "" }
                          )
                        }
                      >
                        {selectedPromotion?.id === row.id ? "Selecionada" : "Selecionar"}
                      </button>
                    </td>
                    <td style={tdStyle}>
                      <code>{row.code || "—"}</code>
                    </td>
                    <td style={tdStyle}>{row.type}</td>
                    <td style={tdStyle}>
                      {row.discount_pct != null
                        ? `${row.discount_pct}%`
                        : row.discount_cents != null
                          ? formatMoney(row.discount_cents)
                          : "—"}
                    </td>
                    <td style={tdStyle}>{formatShortIso(row.valid_from)}</td>
                    <td style={tdStyle}>{row.valid_until ? formatShortIso(row.valid_until) : "—"}</td>
                    <td style={tdStyle}>
                      <StatusPill active={row.is_active} />
                    </td>
                    <td style={tdStyle}>{row.name}</td>
                    <td style={tdStyle}>
                      {canMutate ? (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                          {row.is_active ? (
                            <button type="button" style={buttonGhostStyle} disabled={patchingId === row.id || cloningId === row.id} onClick={() => void patchStatus(row.id, false)}>
                              {patchingId === row.id ? "…" : "Desativar"}
                            </button>
                          ) : (
                            <button type="button" style={buttonGhostStyle} disabled={patchingId === row.id || cloningId === row.id} onClick={() => void patchStatus(row.id, true)}>
                              {patchingId === row.id ? "…" : "Ativar"}
                            </button>
                          )}
                          <button
                            type="button"
                            style={{ ...buttonGhostStyle, borderColor: "rgba(129,140,248,0.55)", color: "#c7d2fe" }}
                            disabled={cloningId === row.id || patchingId === row.id}
                            title="Duplica promoção, escopos e exclusões"
                            onClick={() => void clonePromotion(row)}
                          >
                            {cloningId === row.id ? "…" : "Clonar"}
                          </button>
                        </div>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {selectedPromotion ? (
          <section style={{ ...opsSanityCardStyle, marginTop: 16, borderColor: "rgba(96,165,250,0.5)" }}>
            <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 8, alignItems: "flex-start" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 15, color: "#e2e8f0" }}>Configuração da promoção</h3>
                <p style={{ ...summary24hHintStyle, margin: "4px 0 0" }}>
                  <code>{selectedPromotion.code || selectedPromotion.id}</code>
                  {selectedPromotion.name ? ` — ${selectedPromotion.name}` : ""}
                </p>
              </div>
              <button type="button" style={buttonGhostStyle} onClick={() => setSelectedPromotion(null)}>
                Fechar painel
              </button>
            </div>
            {exclusionsError ? (
              <div style={{ ...criticalBannerStyle, marginTop: 10 }} role="alert">
                {exclusionsError}
              </div>
            ) : null}
            <h4 style={{ margin: "14px 0 6px", fontSize: 13, color: "#cbd5e1" }}>Exclusões de SKU</h4>
            {exclusionsLoading ? (
              <p style={mutedTextStyle}>Carregando exclusões…</p>
            ) : exclusionsPayload ? (
              <p style={{ ...mutedTextStyle, fontSize: 12 }}>
                Total: <strong>{Number(exclusionsPayload.total || 0)}</strong>
              </p>
            ) : null}
            <form onSubmit={handleAddExclusion} style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "flex-end", marginTop: 12 }}>
              <label style={{ ...healthLocalFilterFieldStyle, flex: "1 1 220px" }}>
                product_id (SKU)
                <input value={exclusionProductId} onChange={(e) => setExclusionProductId(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
              <button type="submit" style={buttonPrimaryStyle} disabled={exclusionBusy || !canMutate}>
                {exclusionBusy ? "Enviando…" : "Adicionar exclusão"}
              </button>
              <button type="button" style={buttonGhostStyle} onClick={() => void loadExclusions()} disabled={exclusionsLoading}>
                Atualizar lista
              </button>
            </form>
            {Array.isArray(exclusionsPayload?.items) && exclusionsPayload.items.length ? (
              <table style={{ ...tableStyle, marginTop: 10, minWidth: 400 }}>
                <thead>
                  <tr>
                    <th style={thStyle}>product_id</th>
                    <th style={thStyle}>ação</th>
                  </tr>
                </thead>
                <tbody>
                  {exclusionsPayload.items.map((ex) => (
                    <tr key={`${ex.promotion_id}:${ex.product_id}`}>
                      <td style={tdStyle}>
                        <code>{ex.product_id}</code>
                      </td>
                      <td style={tdStyle}>
                        <button
                          type="button"
                          style={buttonGhostStyle}
                          disabled={deletingProductId === ex.product_id || !canMutate}
                          onClick={() => void handleRemoveExclusion(ex.product_id)}
                        >
                          {deletingProductId === ex.product_id ? "…" : "Remover"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : exclusionsPayload && !exclusionsLoading ? (
              <p style={summary24hHintStyle}>Nenhum SKU excluído — todos os produtos elegíveis dentro do escopo.</p>
            ) : null}
            <section style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid rgba(148,163,184,0.25)" }}>
              <h4 style={{ margin: "0 0 8px", fontSize: 13, color: "#cbd5e1" }}>Escopos (player, país, marketplace…)</h4>
              <p style={{ ...summary24hHintStyle, margin: "0 0 8px" }}>
                Players locker mundial: InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT, Worten, El Corte Inglés…
                {playerCatalog.length ? ` (${playerCatalog.length} no catálogo)` : ""}
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 8 }}>
                {FEATURED_LOCKER_PLAYERS.map((code) => (
                  <button
                    key={code}
                    type="button"
                    style={{ ...buttonGhostStyle, fontSize: 11, padding: "2px 8px" }}
                    onClick={() => {
                      setScopeType("PLAYER");
                      setScopeValue(code);
                    }}
                  >
                    {code}
                  </button>
                ))}
              </div>
              {scopesError ? (
                <div style={{ ...criticalBannerStyle, marginBottom: 8 }} role="alert">
                  {scopesError}
                </div>
              ) : null}
              <form onSubmit={handleAddScope} style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "flex-end" }}>
                <label style={healthLocalFilterFieldStyle}>
                  scope_type
                  <select value={scopeType} onChange={(e) => setScopeType(e.target.value)} style={healthLocalFilterInputStyle}>
                    {["PLAYER", "COUNTRY", "CHANNEL", "PARTNER", "MARKETPLACE", "LOCKER_OPERATOR", "REGION"].map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </label>
                <label style={{ ...healthLocalFilterFieldStyle, flex: "1 1 160px" }}>
                  scope_value
                  <input
                    list="locker-players-datalist"
                    value={scopeValue}
                    onChange={(e) => setScopeValue(e.target.value)}
                    placeholder="INPOST, CORREIOS, MERCADO_LIVRE…"
                    style={healthLocalFilterInputStyle}
                  />
                  <datalist id="locker-players-datalist">
                    {playerCatalog.map((p) => (
                      <option key={p.code} value={p.code}>
                        {p.display_name}
                      </option>
                    ))}
                  </datalist>
                </label>
                <button type="submit" style={buttonPrimaryStyle} disabled={scopeBusy || !canMutate}>Adicionar escopo</button>
              </form>
              {scopesLoading ? <p style={mutedTextStyle}>Carregando escopos…</p> : null}
              {Array.isArray(scopesPayload?.items) && scopesPayload.items.length ? (
                <table style={{ ...tableStyle, marginTop: 10 }}>
                  <thead>
                    <tr>
                      <th style={thStyle}>type</th>
                      <th style={thStyle}>value</th>
                      <th style={thStyle}>mode</th>
                      <th style={thStyle}>ação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scopesPayload.items.map((sc) => (
                      <tr key={sc.id}>
                        <td style={tdStyle}>{sc.scope_type}</td>
                        <td style={tdStyle}>{sc.scope_value}</td>
                        <td style={tdStyle}>{sc.mode}</td>
                        <td style={tdStyle}>
                          <button type="button" style={buttonGhostStyle} disabled={scopeBusy} onClick={() => void handleRemoveScope(sc.id)}>Remover</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : scopesPayload && !scopesLoading ? (
                <p style={summary24hHintStyle}>Sem escopo INCLUDE — elegível em qualquer player/país (salvo regras do motor).</p>
              ) : null}
            </section>
          </section>
        ) : embedded && listPayload?.items?.length ? (
          <p style={{ ...summary24hHintStyle, marginTop: 12 }}>Selecione uma linha na tabela para configurar escopos e exclusões.</p>
        ) : null}
      </section>
  );

  if (embedded) return inner;
  return <div style={pageStyle}>{inner}</div>;
}
