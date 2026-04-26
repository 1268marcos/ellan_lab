import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsActionButton from "../components/OpsActionButton";
import OpsScenarioPresets from "../components/OpsScenarioPresets";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const STORAGE_KEY = "ops_products_pricing_fiscal_actions_v1";

const ACTIONS = [
  { key: "overview", label: "GET overview" },
  { key: "promotions", label: "GET promotions" },
  { key: "bundles", label: "GET bundles" },
  { key: "fiscalLog", label: "GET fiscal log" },
  { key: "createBundle", label: "POST bundle" },
  { key: "createPromotion", label: "POST promotion" },
  { key: "validatePromotion", label: "POST promotion validate" },
  { key: "upsertFiscal", label: "PUT fiscal config" },
];

function defaultActionStatus() {
  const nowIso = new Date().toISOString();
  return ACTIONS.reduce((acc, item) => {
    acc[item.key] = { status: "idle", note: "Aguardando execução", updatedAt: nowIso };
    return acc;
  }, {});
}

function parseError(payload, fallback = "Falha operacional.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

function toIsoOrNull(localValue) {
  const raw = String(localValue || "").trim();
  if (!raw) return null;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString();
}

function ActionChip({ label, state }) {
  const tone = state?.status === "success" ? chipSuccessStyle : state?.status === "error" ? chipErrorStyle : state?.status === "running" ? chipRunningStyle : chipIdleStyle;
  return (
    <article style={{ ...chipBaseStyle, ...tone }}>
      <strong style={{ fontSize: 12 }}>{label}</strong>
      <small style={{ fontSize: 11 }}>{state?.note || "-"}</small>
      <small style={{ fontSize: 10, opacity: 0.9 }}>{state?.updatedAt ? new Date(state.updatedAt).toLocaleString() : "-"}</small>
    </article>
  );
}

export default function OpsProductsPricingFiscalPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [limit, setLimit] = useState("20");
  const [productId, setProductId] = useState("sku_123");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState("");
  const [actionStatus, setActionStatus] = useState(defaultActionStatus);
  const [validationState, setValidationState] = useState({ tone: "idle", label: "Sem validação recente", detail: "Execute POST /promotions/validate." });

  const [bundlePayload, setBundlePayload] = useState(`{
  "name": "Bundle teste PR3",
  "code": "PR3-BUNDLE-001",
  "description": "Pacote promocional de teste",
  "amount_cents": 1990,
  "currency": "BRL",
  "bundle_type": "FIXED"
}`);
  const [promotionPayload, setPromotionPayload] = useState(`{
  "code": "PR3-PROMO-001",
  "name": "Promo teste PR3",
  "type": "PERCENT_OFF",
  "discount_pct": 10,
  "min_order_cents": 1000,
  "conditions_json": {}
}`);
  const [fiscalPayload, setFiscalPayload] = useState(`{
  "ncm_code": "22030000",
  "icms_cst": "00",
  "pis_cst": "01",
  "cofins_cst": "01",
  "iva_category": "GENERAL",
  "is_active": true,
  "unit_of_measure": "UN",
  "origin_type": "0",
  "cfop": "5102",
  "tax_rate_pct": 18.0,
  "is_service": false
}`);
  const [validatePayload, setValidatePayload] = useState(`{
  "order_id": "order_pr3_001",
  "promotion_code": "PR3-PROMO-001",
  "total_amount_cents": 12000,
  "items": [
    { "product_id": "sku_123", "quantity": 2, "unit_price_cents": 6000 }
  ]
}`);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") setActionStatus((prev) => ({ ...prev, ...parsed }));
    } catch (_) {
      // no-op
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(actionStatus));
    } catch (_) {
      // no-op
    }
  }, [actionStatus]);

  function setAction(key, status, note) {
    setActionStatus((prev) => ({
      ...prev,
      [key]: { status, note, updatedAt: new Date().toISOString() },
    }));
  }

  async function run({ actionKey, method, endpoint, body }) {
    if (!token) return;
    setLoading(actionKey);
    setAction(actionKey, "running", "Executando...");
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}${endpoint}`, {
        method,
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setResult(JSON.stringify(data, null, 2));
      setAction(actionKey, "success", "Sucesso");
      return data;
    } catch (err) {
      const message = String(err?.message || err || "erro desconhecido");
      setResult(`Erro: ${message}`);
      setAction(actionKey, "error", message);
      return null;
    } finally {
      setLoading("");
    }
  }

  function applyPromotionPreset(presetKey) {
    if (presetKey === "BUY_X_GET_Y") {
      setPromotionPayload(`{
  "code": "PR3-BUYXGETY-001",
  "name": "Compre 2 leve 1",
  "type": "BUY_X_GET_Y",
  "min_order_cents": 1000,
  "conditions_json": {
    "buy_qty": 2,
    "get_qty": 1,
    "free_item_price_cents": 3000
  }
}`);
      return;
    }
    if (presetKey === "FREE_ITEM") {
      setPromotionPayload(`{
  "code": "PR3-FREEITEM-001",
  "name": "Item grátis na compra",
  "type": "FREE_ITEM",
  "min_order_cents": 1000,
  "conditions_json": {
    "free_qty": 1,
    "free_item_price_cents": 2500
  }
}`);
      return;
    }
    setPromotionPayload(`{
  "code": "PR3-BUNDLEDISC-001",
  "name": "Bundle com preço especial",
  "type": "BUNDLE_DISCOUNT",
  "min_order_cents": 1000,
  "conditions_json": {
    "bundle_size": 3,
    "bundle_price_cents": 12000
  }
}`);
  }

  function applyOpsPreset(kind) {
    if (kind === "green") {
      setProductId("sku_123");
      setValidatePayload(`{
  "order_id": "order_pr3_healthy_001",
  "promotion_code": "PR3-PROMO-001",
  "total_amount_cents": 12000,
  "items": [
    { "product_id": "sku_123", "quantity": 2, "unit_price_cents": 6000 }
  ]
}`);
      return;
    }
    if (kind === "amber") {
      applyPromotionPreset("BUY_X_GET_Y");
      setValidatePayload(`{
  "order_id": "order_pr3_attention_001",
  "promotion_code": "PR3-BUYXGETY-001",
  "total_amount_cents": 9000,
  "items": [
    { "product_id": "sku_123", "quantity": 2, "unit_price_cents": 4500 }
  ]
}`);
      return;
    }
    setProductId("sku_problematic_001");
    setValidatePayload(`{
  "order_id": "order_pr3_error_001",
  "promotion_code": "PROMO_INEXISTENTE",
  "total_amount_cents": 1000,
  "items": [
    { "product_id": "sku_problematic_001", "quantity": 1, "unit_price_cents": 1000 }
  ]
}`);
  }

  async function handleGetOverview() {
    const params = new URLSearchParams();
    const fromIso = toIsoOrNull(from);
    const toIso = toIsoOrNull(to);
    if (fromIso) params.set("period_from", fromIso);
    if (toIso) params.set("period_to", toIso);
    params.set("top_limit", String(Math.max(1, Math.min(20, Number(limit || 5)))));
    await run({ actionKey: "overview", method: "GET", endpoint: `/ops/products/pricing-fiscal/overview?${params.toString()}` });
  }

  async function handleGetPromotions() {
    await run({ actionKey: "promotions", method: "GET", endpoint: "/promotions?limit=50" });
  }

  async function handleGetBundles() {
    await run({ actionKey: "bundles", method: "GET", endpoint: "/products/bundles?limit=50" });
  }

  async function handleGetFiscalLog() {
    await run({ actionKey: "fiscalLog", method: "GET", endpoint: "/fiscal/auto-classification-log?limit=50" });
  }

  async function handleCreateBundle() {
    let payload = {};
    try {
      payload = JSON.parse(bundlePayload || "{}");
    } catch (_) {
      setResult("JSON inválido em bundle payload.");
      return;
    }
    await run({ actionKey: "createBundle", method: "POST", endpoint: "/products/bundles", body: payload });
  }

  async function handleCreatePromotion() {
    let payload = {};
    try {
      payload = JSON.parse(promotionPayload || "{}");
    } catch (_) {
      setResult("JSON inválido em promotion payload.");
      return;
    }
    await run({ actionKey: "createPromotion", method: "POST", endpoint: "/promotions", body: payload });
  }

  async function handleValidatePromotion() {
    let payload = {};
    try {
      payload = JSON.parse(validatePayload || "{}");
    } catch (_) {
      setResult("JSON inválido em validate payload.");
      setValidationState({ tone: "error", label: "Payload inválido", detail: "Corrija o JSON de validação." });
      return;
    }
    const data = await run({ actionKey: "validatePromotion", method: "POST", endpoint: "/promotions/validate", body: payload });
    if (!data) {
      setValidationState({ tone: "error", label: "Erro na validação", detail: "Verifique token/permissão e payload." });
      return;
    }
    if (data.valid) {
      if (data.idempotent) {
        setValidationState({
          tone: "idempotent",
          label: "Validação idempotente",
          detail: `discount=${data.discount_cents ?? 0} cents`,
        });
      } else {
        setValidationState({
          tone: "success",
          label: "Promoção válida",
          detail: `discount=${data.discount_cents ?? 0} cents`,
        });
      }
      return;
    }
    setValidationState({
      tone: "warning",
      label: "Promoção não aplicada",
      detail: String(data.reason || "Regra não elegível no cenário atual."),
    });
  }

  async function handleUpsertFiscal() {
    const skuId = String(productId || "").trim();
    if (!skuId) {
      setResult("Informe Product ID para fiscal config.");
      return;
    }
    let payload = {};
    try {
      payload = JSON.parse(fiscalPayload || "{}");
    } catch (_) {
      setResult("JSON inválido em fiscal payload.");
      return;
    }
    await run({
      actionKey: "upsertFiscal",
      method: "PUT",
      endpoint: `/products/${encodeURIComponent(skuId)}/fiscal-config`,
      body: payload,
    });
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Products Pricing/Fiscal (Pr-3)</h1>
        <p style={mutedStyle}>Guia rápido: 1) consultar overview; 2) validar bundles/promotions; 3) confirmar fiscal config e log técnico.</p>

        <OpsScenarioPresets
          style={quickActionsStyle}
          disabled={Boolean(loading)}
          items={[
            { id: "green", tone: "success", label: "Preset verde: validação saudável", onClick: () => applyOpsPreset("green") },
            { id: "amber", tone: "warn", label: "Preset âmbar: revisão promocional", onClick: () => applyOpsPreset("amber") },
            { id: "red", tone: "error", label: "Preset vermelho: diagnóstico de erro", onClick: () => applyOpsPreset("red") },
          ]}
        />

        <div style={quickActionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleGetOverview()} disabled={Boolean(loading)}>
            {loading === "overview" ? "Carregando..." : "GET overview"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => void handleGetPromotions()} disabled={Boolean(loading)}>
            {loading === "promotions" ? "Carregando..." : "GET promotions"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => void handleGetBundles()} disabled={Boolean(loading)}>
            {loading === "bundles" ? "Carregando..." : "GET bundles"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => void handleGetFiscalLog()} disabled={Boolean(loading)}>
            {loading === "fiscalLog" ? "Carregando..." : "GET fiscal log"}
          </OpsActionButton>
        </div>

        <div style={filtersStyle}>
          <label style={labelStyle}>
            Period from
            <input type="datetime-local" value={from} onChange={(e) => setFrom(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Period to
            <input type="datetime-local" value={to} onChange={(e) => setTo(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            top_limit (overview)
            <input value={limit} onChange={(e) => setLimit(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Product ID (fiscal config)
            <input value={productId} onChange={(e) => setProductId(e.target.value)} style={inputStyle} />
          </label>
        </div>

        <div style={chipsGridStyle}>
          {ACTIONS.map((item) => (
            <ActionChip key={item.key} label={item.label} state={actionStatus[item.key]} />
          ))}
        </div>
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Mutações rápidas</h2>

        <label style={labelStyle}>
          Payload bundle (POST /products/bundles)
          <textarea value={bundlePayload} onChange={(e) => setBundlePayload(e.target.value)} style={textareaStyle} />
        </label>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleCreateBundle()} disabled={Boolean(loading)}>
            {loading === "createBundle" ? "Enviando..." : "POST bundle"}
          </OpsActionButton>
        </div>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload promotion (POST /promotions)
          <textarea value={promotionPayload} onChange={(e) => setPromotionPayload(e.target.value)} style={textareaStyle} />
        </label>
        <div style={quickActionsStyle}>
          <OpsActionButton type="button" variant="secondary" onClick={() => applyPromotionPreset("BUY_X_GET_Y")} disabled={Boolean(loading)}>
            Preset BUY_X_GET_Y
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => applyPromotionPreset("FREE_ITEM")} disabled={Boolean(loading)}>
            Preset FREE_ITEM
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => applyPromotionPreset("BUNDLE_DISCOUNT")} disabled={Boolean(loading)}>
            Preset BUNDLE_DISCOUNT
          </OpsActionButton>
        </div>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleCreatePromotion()} disabled={Boolean(loading)}>
            {loading === "createPromotion" ? "Enviando..." : "POST promotion"}
          </OpsActionButton>
        </div>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload validate (POST /promotions/validate)
          <textarea value={validatePayload} onChange={(e) => setValidatePayload(e.target.value)} style={textareaStyle} />
        </label>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleValidatePromotion()} disabled={Boolean(loading)}>
            {loading === "validatePromotion" ? "Validando..." : "POST promotion validate"}
          </OpsActionButton>
        </div>
        <div
          style={{
            ...validationBadgeStyle,
            ...(validationState.tone === "success"
              ? validationSuccessStyle
              : validationState.tone === "warning"
                ? validationWarningStyle
                : validationState.tone === "idempotent"
                  ? validationIdempotentStyle
                  : validationState.tone === "error"
                    ? validationErrorStyle
                    : validationIdleStyle),
          }}
        >
          <strong>{validationState.label}</strong>
          <small>{validationState.detail}</small>
        </div>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload fiscal (PUT /products/&lt;productId&gt;/fiscal-config)
          <textarea value={fiscalPayload} onChange={(e) => setFiscalPayload(e.target.value)} style={textareaStyle} />
        </label>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleUpsertFiscal()} disabled={Boolean(loading)}>
            {loading === "upsertFiscal" ? "Enviando..." : "PUT fiscal config"}
          </OpsActionButton>
        </div>

        <pre style={resultStyle}>{result || "Execute uma ação para visualizar resposta técnica."}</pre>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif", display: "grid", gap: 12 };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8" };
const quickActionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 };
const filtersStyle = { display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0" };
const textareaStyle = { minHeight: 110, padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };
const chipsGridStyle = { display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", marginTop: 10 };
const chipBaseStyle = { borderRadius: 10, border: "1px solid #334155", padding: "8px 10px", display: "grid", gap: 2 };
const chipIdleStyle = { background: "#0B1220", color: "#CBD5E1" };
const chipRunningStyle = { background: "rgba(217,119,6,0.2)", border: "1px solid rgba(217,119,6,0.45)", color: "#FDE68A" };
const chipSuccessStyle = { background: "rgba(22,163,74,0.2)", border: "1px solid rgba(22,163,74,0.45)", color: "#86EFAC" };
const chipErrorStyle = { background: "rgba(220,38,38,0.18)", border: "1px solid rgba(220,38,38,0.45)", color: "#FCA5A5" };
const validationBadgeStyle = { marginTop: 10, borderRadius: 10, border: "1px solid #334155", padding: "10px 12px", display: "grid", gap: 2 };
const validationIdleStyle = { background: "#0B1220", color: "#CBD5E1" };
const validationSuccessStyle = { background: "rgba(22,163,74,0.2)", border: "1px solid rgba(22,163,74,0.45)", color: "#86EFAC" };
const validationWarningStyle = { background: "rgba(217,119,6,0.2)", border: "1px solid rgba(217,119,6,0.45)", color: "#FDE68A" };
const validationIdempotentStyle = { background: "rgba(59,130,246,0.2)", border: "1px solid rgba(59,130,246,0.45)", color: "#93C5FD" };
const validationErrorStyle = { background: "rgba(220,38,38,0.18)", border: "1px solid rgba(220,38,38,0.45)", color: "#FCA5A5" };
