
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

function formatBrlFromCents(amountCents) {
  const n = Number(amountCents);
  if (!Number.isFinite(n)) return "—";
  return (n / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function parseError(payload, fallback = "Falha ao processar resposta da API.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
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

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique o proxy /api/op (porta 8010).`;
  }
  return raw;
}

export default function OpsProductBundlesPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [bundles, setBundles] = useState([]);
  const [total, setTotal] = useState(0);
  const [expandedId, setExpandedId] = useState(null);
  const [itemsByBundle, setItemsByBundle] = useState({});
  const [itemsLoadingId, setItemsLoadingId] = useState(null);
  const [statusPatchingId, setStatusPatchingId] = useState(null);

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const loadBundles = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${ORDER_PICKUP_BASE}/products/bundles?limit=200&offset=0`, {
        method: "GET",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(data));
      setBundles(Array.isArray(data.items) ? data.items : []);
      setTotal(Number(data.total || 0));
    } catch (e) {
      setError(normalizeNetworkError(e, `${ORDER_PICKUP_BASE}/products/bundles`));
      setBundles([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [token, authHeaders]);

  useEffect(() => {
    if (token) void loadBundles();
  }, [token, loadBundles]);

  const toggleExpand = async (bundleId) => {
    if (!token || !bundleId) return;
    if (expandedId === bundleId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(bundleId);
    if (itemsByBundle[bundleId]) return;
    setItemsLoadingId(bundleId);
    setError("");
    try {
      const r = await fetch(`${ORDER_PICKUP_BASE}/products/bundles/${encodeURIComponent(bundleId)}/items`, {
        method: "GET",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(data, "Nao foi possivel carregar itens do bundle."));
      setItemsByBundle((prev) => ({ ...prev, [bundleId]: Array.isArray(data.items) ? data.items : [] }));
    } catch (e) {
      setError(normalizeNetworkError(e, ORDER_PICKUP_BASE));
      setItemsByBundle((prev) => ({ ...prev, [bundleId]: [] }));
    } finally {
      setItemsLoadingId(null);
    }
  };

  const patchStatus = async (bundleId, isActive) => {
    if (!token || !bundleId) return;
    setStatusPatchingId(bundleId);
    setError("");
    try {
      const r = await fetch(`${ORDER_PICKUP_BASE}/products/bundles/${encodeURIComponent(bundleId)}/status`, {
        method: "PATCH",
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: JSON.stringify({ is_active: Boolean(isActive) }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(data, "Nao foi possivel atualizar status."));
      await loadBundles();
    } catch (e) {
      setError(normalizeNetworkError(e, ORDER_PICKUP_BASE));
    } finally {
      setStatusPatchingId(null);
    }
  };

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Product bundles" />
        <p style={muted}>
          <code>product_bundles</code> + <code>product_bundle_items</code>. API:{" "}
          <code>{ORDER_PICKUP_BASE}/products/bundles</code> (PR3 / pricing-fiscal).
        </p>
        <div style={rowActions}>
          <button type="button" style={btnPrimary} disabled={loading || !token} onClick={() => void loadBundles()}>
            {loading ? "Carregando…" : "Atualizar"}
          </button>
          <span style={mutedSmall}>total={total}</span>
        </div>
        {error ? <pre style={errBox}>{error}</pre> : null}
        {!token ? <p style={muted}>Faça login (admin_operacao ou auditoria).</p> : null}
        {token && !loading && !bundles.length && !error ? <p style={muted}>Nenhum bundle encontrado.</p> : null}
        {bundles.length > 0 ? (
          <div style={tableWrap}>
            <table style={table}>
              <thead>
                <tr>
                  <th style={thNarrow} />
                  <th style={th}>code</th>
                  <th style={th}>name</th>
                  <th style={th}>amount</th>
                  <th style={th}>valid_from / valid_until</th>
                  <th style={th}>status</th>
                  <th style={th}>Ações</th>
                </tr>
              </thead>
              <tbody>
                {bundles.map((b) => {
                  const open = expandedId === b.id;
                  const busy = statusPatchingId === b.id;
                  const items = itemsByBundle[b.id];
                  return (
                    <React.Fragment key={b.id}>
                      <tr>
                        <td style={tdNarrow}>
                          <button type="button" style={chevronBtn} onClick={() => void toggleExpand(b.id)} aria-expanded={open}>
                            {open ? "▼" : "▶"}
                          </button>
                        </td>
                        <td style={td}>
                          <code>{b.code}</code>
                        </td>
                        <td style={td}>{b.name}</td>
                        <td style={td}>{formatBrlFromCents(b.amount_cents)}</td>
                        <td style={td}>
                          <span style={mutedSmall}>{b.valid_from?.slice?.(0, 16) || "—"}</span>
                          <br />
                          <span style={mutedSmall}>{b.valid_until?.slice?.(0, 16) || "—"}</span>
                        </td>
                        <td style={td}>
                          <span style={badgeStyle(!!b.is_active)}>{b.is_active ? "ativo" : "inativo"}</span>
                        </td>
                        <td style={td}>
                          <button type="button" style={btnSm} disabled={busy || !!b.is_active} onClick={() => void patchStatus(b.id, true)}>
                            Ativar
                          </button>{" "}
                          <button type="button" style={btnSm} disabled={busy || !b.is_active} onClick={() => void patchStatus(b.id, false)}>
                            Desativar
                          </button>
                        </td>
                      </tr>
                      {open ? (
                        <tr>
                          <td colSpan={7} style={nestedCell}>
                            {itemsLoadingId === b.id ? (
                              <span style={mutedSmall}>Carregando itens…</span>
                            ) : (
                              <div>
                                <div style={nestedTitle}>product_bundle_items</div>
                                {!items || !items.length ? (
                                  <span style={mutedSmall}>Nenhum item.</span>
                                ) : (
                                  <table style={nestedTable}>
                                    <thead>
                                      <tr>
                                        <th style={nth}>product_id</th>
                                        <th style={nth}>quantity</th>
                                        <th style={nth}>unit_price_cents</th>
                                        <th style={nth}>sort_order</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {items.map((it) => (
                                        <tr key={it.id}>
                                          <td style={ntd}>
                                            <code>{it.product_id}</code>
                                          </td>
                                          <td style={ntd}>{it.quantity}</td>
                                          <td style={ntd}>{it.unit_price_cents ?? "—"}</td>
                                          <td style={ntd}>{it.sort_order}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                )}
                              </div>
                            )}
                          </td>
                        </tr>
                      ) : null}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const muted = { color: "#94A3B8", marginTop: 8 };
const mutedSmall = { color: "#94A3B8", fontSize: 12 };
const rowActions = { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginTop: 12 };
const btnPrimary = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const errBox = { marginTop: 12, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10 };
const tableWrap = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const table = { width: "100%", borderCollapse: "collapse", minWidth: 720 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const thNarrow = { ...th, width: 40 };
const td = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B", verticalAlign: "middle" };
const tdNarrow = { ...td, textAlign: "center" };
const chevronBtn = { border: "none", background: "transparent", color: "#94A3B8", cursor: "pointer", fontSize: 12 };
const btnSm = { padding: "4px 8px", borderRadius: 8, border: "1px solid #475569", background: "#1E293B", color: "#E2E8F0", fontSize: 11, cursor: "pointer" };
const nestedCell = { padding: "12px 16px 16px 48px", background: "#0B1220", borderBottom: "1px solid #1E293B" };
const nestedTitle = { fontSize: 11, color: "#64748B", marginBottom: 8, fontWeight: 700 };
const nestedTable = { width: "100%", borderCollapse: "collapse" };
const nth = { textAlign: "left", padding: "6px 8px", fontSize: 11, color: "#64748B", borderBottom: "1px solid #1E293B" };
const ntd = { padding: "6px 8px", fontSize: 11, color: "#CBD5E1", borderBottom: "1px solid #1E293B" };

function badgeStyle(active) {
  return {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: 999,
    fontSize: 11,
    fontWeight: 700,
    background: active ? "rgba(22,163,74,0.2)" : "rgba(100,116,139,0.25)",
    color: active ? "#86EFAC" : "#94A3B8",
  };
}

