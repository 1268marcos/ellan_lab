
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

const PROMO_TYPES = ["PERCENT_OFF", "FIXED_OFF", "BUY_X_GET_Y", "FREE_ITEM", "BUNDLE_DISCOUNT"];

function parseError(payload, fallback = "Falha ao processar resposta da API.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
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
    return new Date(iso).toLocaleString();
  } catch (_) {
    return String(iso);
  }
}

/**
 * OPS Marketing — promoções (`public.promotions`) e exclusões (`promotion_product_exclusions`).
 */
export default function OpsPromotionsPage() {
  const { token } = useAuth();
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
  const [listPayload, setListPayload] = useState(null);
  const [patchingId, setPatchingId] = useState("");

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
      return;
    }
    void loadExclusions();
  }, [selectedPromotion?.id, loadExclusions]);

  const loadList = useCallback(async (overrides = {}) => {
    if (!token) return;
    const effLimit = overrides.limit != null ? overrides.limit : limit;
    const effOffset = overrides.offset != null ? overrides.offset : offset;
    setLoading(true);
    setError("");
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

  const rawItems = Array.isArray(listPayload?.items) ? listPayload.items : [];
  const typeNeedle = String(typeLocalFilter || "").trim().toUpperCase();
  const items = typeNeedle ? rawItems.filter((row) => String(row?.type || "").toUpperCase() === typeNeedle) : rawItems;
  const total = Number(listPayload?.total || 0);

  async function patchStatus(promotionId, nextActive) {
    if (!token) return;
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

  async function handleCreate(e) {
    e.preventDefault();
    if (!token) return;
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
    if (!token || !pid) return;
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
    if (!token || !pid) return;
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

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Marketing / Promoções" versionLabel="/ops/marketing/promotions" />
        <p style={mutedStyle}>
          Colunas principais: <code style={codeInline}>code</code>, <code style={codeInline}>type</code>,{" "}
          <code style={codeInline}>discount_pct</code>, <code style={codeInline}>valid_from</code>,{" "}
          <code style={codeInline}>valid_until</code>. API: <code style={codeInline}>GET/POST /promotions</code>,{" "}
          <code style={codeInline}>PATCH /promotions/:id/status</code>,{" "}
          <code style={codeInline}>GET/POST /promotions/:id/product-exclusions</code>,{" "}
          <code style={codeInline}>DELETE .../product-exclusions/:product_id</code>. Papel no backend:{" "}
          <code style={codeInline}>admin_operacao</code> ou <code style={codeInline}>auditoria</code>.
        </p>
        <aside style={calloutStyle}>
          Selecione uma promoção na tabela e use o painel <strong>Exclusões de produtos</strong> para SKUs que não devem receber o desconto (tabela{" "}
          <code style={codeInline}>promotion_product_exclusions</code>).
        </aside>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            Código (exato)
            <input value={codeFilter} onChange={(e) => setCodeFilter(e.target.value)} placeholder="PR3-PROMO-001" style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Ativa
            <select value={isActiveFilter} onChange={(e) => setIsActiveFilter(e.target.value)} style={inputStyle}>
              <option value="">Todas</option>
              <option value="true">Sim</option>
              <option value="false">Não</option>
            </select>
          </label>
          <label style={labelStyle}>
            Tipo (filtro local na página)
            <select value={typeLocalFilter} onChange={(e) => setTypeLocalFilter(e.target.value)} style={inputStyle}>
              <option value="">Todos</option>
              {PROMO_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Criado desde (opcional)
            <input type="datetime-local" value={fromCreated} onChange={(e) => setFromCreated(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Criado até (opcional)
            <input type="datetime-local" value={toCreated} onChange={(e) => setToCreated(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Limite
            <input
              type="number"
              min={1}
              max={500}
              value={limit}
              onChange={(e) => setLimit(Math.max(1, Math.min(500, Number(e.target.value) || 25)))}
              style={inputStyle}
            />
          </label>
        </div>

        <div style={actionsRowStyle}>
          <button type="button" style={buttonStyle} onClick={() => void loadList({ offset: 0 })} disabled={loading || !token}>
            {loading ? "Carregando…" : "Listar"}
          </button>
          <button type="button" style={secondaryButtonStyle} onClick={() => setShowCreate((v) => !v)} disabled={!token}>
            {showCreate ? "Fechar formulário" : "Nova promoção"}
          </button>
          <button
            type="button"
            style={secondaryButtonStyle}
            onClick={() => void loadList({ offset: Math.max(0, offset - limit) })}
            disabled={loading || offset <= 0}
          >
            Página anterior
          </button>
          <button
            type="button"
            style={secondaryButtonStyle}
            onClick={() => void loadList({ offset: offset + limit })}
            disabled={loading || offset + limit >= total}
          >
            Próxima página
          </button>
          <span style={mutedStyleSmall}>
            offset={offset} total={total}
            {typeLocalFilter ? ` · exibindo ${items.length} na página (filtro tipo)` : ""}
          </span>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {showCreate ? (
          <form onSubmit={handleCreate} style={formCardStyle}>
            <h3 style={h3Style}>Criar promoção (POST)</h3>
            {createError ? <pre style={errorStyle}>{createError}</pre> : null}
            <div style={filtersGridStyle}>
              <label style={labelStyle}>
                Código
                <input value={formCode} onChange={(e) => setFormCode(e.target.value)} style={inputStyle} maxLength={32} />
              </label>
              <label style={labelStyle}>
                Nome *
                <input value={formName} onChange={(e) => setFormName(e.target.value)} style={inputStyle} maxLength={128} required />
              </label>
              <label style={labelStyle}>
                Tipo *
                <select value={formType} onChange={(e) => setFormType(e.target.value)} style={inputStyle}>
                  {PROMO_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label style={labelStyle}>
                discount_pct
                <input value={formDiscountPct} onChange={(e) => setFormDiscountPct(e.target.value)} style={inputStyle} />
              </label>
              <label style={labelStyle}>
                discount_cents (FIXED_OFF etc.)
                <input value={formDiscountCents} onChange={(e) => setFormDiscountCents(e.target.value)} style={inputStyle} />
              </label>
              <label style={labelStyle}>
                min_order_cents
                <input value={formMinOrderCents} onChange={(e) => setFormMinOrderCents(e.target.value)} style={inputStyle} />
              </label>
              <label style={labelStyle}>
                valid_from *
                <input type="datetime-local" value={formValidFrom} onChange={(e) => setFormValidFrom(e.target.value)} style={inputStyle} required />
              </label>
              <label style={labelStyle}>
                valid_until (opcional)
                <input type="datetime-local" value={formValidUntil} onChange={(e) => setFormValidUntil(e.target.value)} style={inputStyle} />
              </label>
            </div>
            <label style={{ ...labelStyle, marginTop: 10 }}>
              conditions_json
              <textarea value={formConditionsJson} onChange={(e) => setFormConditionsJson(e.target.value)} rows={4} style={{ ...inputStyle, fontFamily: "monospace" }} />
            </label>
            <div style={actionsRowStyle}>
              <button type="submit" style={buttonStyle} disabled={createBusy}>
                {createBusy ? "Enviando…" : "Criar"}
              </button>
            </div>
          </form>
        ) : null}

        {!listPayload && !loading && !error ? (
          <p style={mutedStyle}>Clique em &quot;Listar&quot; para carregar promoções.</p>
        ) : !items.length && listPayload ? (
          <p style={mutedStyle}>Nenhuma linha para os filtros atuais.</p>
        ) : items.length ? (
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>exclusões</th>
                  <th style={thStyle}>code</th>
                  <th style={thStyle}>type</th>
                  <th style={thStyle}>discount_pct</th>
                  <th style={thStyle}>valid_from</th>
                  <th style={thStyle}>valid_until</th>
                  <th style={thStyle}>ativa</th>
                  <th style={thStyle}>nome</th>
                  <th style={thStyle}>ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.id} style={selectedPromotion?.id === row.id ? rowSelectedStyle : undefined}>
                    <td style={tdStyle}>
                      <button
                        type="button"
                        style={selectedPromotion?.id === row.id ? smallBtnActiveStyle : smallBtnStyle}
                        onClick={() =>
                          setSelectedPromotion((cur) =>
                            cur?.id === row.id ? null : { id: row.id, code: row.code || "", name: row.name || "" }
                          )
                        }
                      >
                        {selectedPromotion?.id === row.id ? "Selecionada" : "Selecionar"}
                      </button>
                    </td>
                    <td style={tdStyle}>{row.code || "—"}</td>
                    <td style={tdStyle}>{row.type}</td>
                    <td style={tdStyle}>{row.discount_pct != null ? String(row.discount_pct) : "—"}</td>
                    <td style={tdStyle}>{formatShortIso(row.valid_from)}</td>
                    <td style={tdStyle}>{row.valid_until ? formatShortIso(row.valid_until) : "—"}</td>
                    <td style={tdStyle}>{row.is_active ? "sim" : "não"}</td>
                    <td style={tdStyle}>{row.name}</td>
                    <td style={tdStyle}>
                      {row.is_active ? (
                        <button
                          type="button"
                          style={smallBtnStyle}
                          disabled={patchingId === row.id}
                          onClick={() => void patchStatus(row.id, false)}
                        >
                          {patchingId === row.id ? "…" : "Desativar"}
                        </button>
                      ) : (
                        <button
                          type="button"
                          style={smallBtnStyle}
                          disabled={patchingId === row.id}
                          onClick={() => void patchStatus(row.id, true)}
                        >
                          {patchingId === row.id ? "…" : "Ativar"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {selectedPromotion ? (
          <section style={exclusionPanelStyle}>
            <div style={exclusionPanelHeadStyle}>
              <h3 style={h3Style}>Exclusões de produtos</h3>
              <p style={exclusionPanelMetaStyle}>
                <code style={codeInline}>{selectedPromotion.id}</code>
                {selectedPromotion.code ? (
                  <>
                    {" "}
                    · <span>{selectedPromotion.code}</span>
                  </>
                ) : null}
                {selectedPromotion.name ? (
                  <>
                    {" "}
                    — {selectedPromotion.name}
                  </>
                ) : null}
              </p>
              <button type="button" style={secondaryButtonStyle} onClick={() => setSelectedPromotion(null)}>
                Fechar painel
              </button>
            </div>
            {exclusionsError ? <pre style={errorStyle}>{exclusionsError}</pre> : null}
            {exclusionsLoading ? (
              <p style={mutedStyleSmall}>Carregando exclusões…</p>
            ) : exclusionsPayload ? (
              <p style={mutedStyleSmall}>
                Total no servidor: <strong>{Number(exclusionsPayload.total || 0)}</strong>
                {Number(exclusionsPayload.limit) ? ` (limite listagem ${exclusionsPayload.limit})` : ""}
              </p>
            ) : null}
            <form onSubmit={handleAddExclusion} style={exclusionFormRowStyle}>
              <label style={{ ...labelStyle, flex: "1 1 220px", minWidth: 180 }}>
                product_id (SKU existente)
                <input
                  value={exclusionProductId}
                  onChange={(e) => setExclusionProductId(e.target.value)}
                  placeholder="ex.: sku_123"
                  style={inputStyle}
                  autoComplete="off"
                />
              </label>
              <button type="submit" style={{ ...buttonStyle, alignSelf: "end" }} disabled={exclusionBusy || !token}>
                {exclusionBusy ? "Enviando…" : "Adicionar exclusão"}
              </button>
              <button
                type="button"
                style={{ ...secondaryButtonStyle, alignSelf: "end" }}
                onClick={() => void loadExclusions()}
                disabled={exclusionsLoading || !token}
              >
                Atualizar lista
              </button>
            </form>
            {Array.isArray(exclusionsPayload?.items) && exclusionsPayload.items.length ? (
              <div style={{ ...tableWrapStyle, marginTop: 10 }}>
                <table style={{ ...tableStyle, minWidth: 400 }}>
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
                          <code style={codeInline}>{ex.product_id}</code>
                        </td>
                        <td style={tdStyle}>
                          <button
                            type="button"
                            style={smallBtnStyle}
                            disabled={deletingProductId === ex.product_id}
                            onClick={() => void handleRemoveExclusion(ex.product_id)}
                          >
                            {deletingProductId === ex.product_id ? "…" : "Remover"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : exclusionsPayload && !exclusionsLoading ? (
              <p style={mutedStyleSmall}>Nenhuma exclusão cadastrada para esta promoção.</p>
            ) : null}
          </section>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8, fontSize: 13, lineHeight: 1.5 };
const mutedStyleSmall = { color: "#94A3B8", fontSize: 12 };
const codeInline = { color: "#93C5FD", fontSize: 12 };
const calloutStyle = {
  marginTop: 12,
  padding: 10,
  borderRadius: 10,
  border: "1px solid #334155",
  background: "#0B1220",
  color: "#CBD5E1",
  fontSize: 12,
  lineHeight: 1.5,
};
const filtersGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10, marginTop: 12 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const secondaryButtonStyle = { padding: "10px 12px", borderRadius: 10, border: "1px solid #334155", background: "#0B1220", color: "#E2E8F0", fontWeight: 600, cursor: "pointer" };
const actionsRowStyle = { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginTop: 12 };
const errorStyle = { marginTop: 12, background: "rgba(220, 38, 38, 0.12)", color: "#FCA5A5", border: "1px solid rgba(220, 38, 38, 0.45)", borderRadius: 10, padding: 10, whiteSpace: "pre-wrap" };
const tableWrapStyle = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 720 };
const thStyle = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
const formCardStyle = { marginTop: 16, padding: 12, borderRadius: 12, border: "1px solid #1E293B", background: "#0B1220" };
const h3Style = { margin: "0 0 8px", fontSize: 15, color: "#F1F5F9" };
const smallBtnStyle = { ...secondaryButtonStyle, padding: "6px 10px", fontSize: 11 };
const smallBtnActiveStyle = { ...smallBtnStyle, border: "1px solid #1D4ED8", background: "rgba(29,78,216,0.25)", color: "#BFDBFE" };
const rowSelectedStyle = { background: "rgba(29, 78, 216, 0.12)" };
const exclusionPanelStyle = {
  marginTop: 20,
  padding: 14,
  borderRadius: 12,
  border: "1px solid #1E3A5F",
  background: "#0B1220",
};
const exclusionPanelHeadStyle = { display: "flex", flexWrap: "wrap", alignItems: "flex-start", gap: 10, justifyContent: "space-between" };
const exclusionPanelMetaStyle = { margin: "4px 0 0", fontSize: 12, color: "#94A3B8", flex: "1 1 200px" };
const exclusionFormRowStyle = { display: "flex", flexWrap: "wrap", gap: 10, alignItems: "flex-end", marginTop: 12 };

