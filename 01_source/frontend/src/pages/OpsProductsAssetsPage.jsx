import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const MEDIA_FEEDBACK_STORAGE_KEY = "ops_products_assets_media_feedback_v1";
const BARCODE_FEEDBACK_STORAGE_KEY = "ops_products_assets_barcode_feedback_v1";

export default function OpsProductsAssetsPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);
  const [productId, setProductId] = useState("");
  const [mediaPayload, setMediaPayload] = useState('{\n  "media_type": "IMAGE",\n  "url": "https://cdn.exemplo/item.jpg",\n  "is_primary": true\n}');
  const [barcodePayload, setBarcodePayload] = useState('{\n  "barcode_type": "EAN13",\n  "barcode_value": "7890000000001",\n  "is_primary": true\n}');
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState("");
  const [mediaItems, setMediaItems] = useState([]);
  const [barcodeItems, setBarcodeItems] = useState([]);
  const [editingMediaId, setEditingMediaId] = useState("");
  const [editingBarcodeId, setEditingBarcodeId] = useState("");
  const [editingMediaForm, setEditingMediaForm] = useState({ media_type: "IMAGE", url: "", sort_order: 0, is_primary: false });
  const [editingBarcodeForm, setEditingBarcodeForm] = useState({ barcode_type: "EAN13", barcode_value: "", is_primary: false });
  const [mediaRowFeedback, setMediaRowFeedback] = useState({});
  const [barcodeRowFeedback, setBarcodeRowFeedback] = useState({});

  useEffect(() => {
    try {
      const raw = localStorage.getItem(MEDIA_FEEDBACK_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object") setMediaRowFeedback(parsed);
      }
    } catch (_) {
      // no-op
    }
    try {
      const raw = localStorage.getItem(BARCODE_FEEDBACK_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object") setBarcodeRowFeedback(parsed);
      }
    } catch (_) {
      // no-op
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(MEDIA_FEEDBACK_STORAGE_KEY, JSON.stringify(mediaRowFeedback));
    } catch (_) {
      // no-op
    }
  }, [mediaRowFeedback]);

  useEffect(() => {
    try {
      localStorage.setItem(BARCODE_FEEDBACK_STORAGE_KEY, JSON.stringify(barcodeRowFeedback));
    } catch (_) {
      // no-op
    }
  }, [barcodeRowFeedback]);

  async function run(method, endpoint, body, action) {
    if (!token) return;
    setLoading(action);
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}${endpoint}`, {
        method,
        headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail?.message || data?.detail?.type || data?.detail || "falha operacional");
      }
      setResult(JSON.stringify(data, null, 2));
      return data;
    } catch (err) {
      setResult(`Erro: ${String(err?.message || err || "falha desconhecida")}`);
      return null;
    } finally {
      setLoading("");
    }
  }

  async function handlePostMedia() {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    let payload = {};
    try {
      payload = JSON.parse(mediaPayload || "{}");
    } catch (_) {
      return setResult("JSON inválido para media.");
    }
    const data = await run("POST", `/products/${encodeURIComponent(pid)}/media`, payload, "post-media");
    if (data) await handleListMedia();
  }

  async function handleListMedia() {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    const data = await run("GET", `/products/${encodeURIComponent(pid)}/media?limit=100`, null, "get-media");
    if (data?.ok && Array.isArray(data.items)) setMediaItems(data.items);
  }

  async function handlePostBarcode() {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    let payload = {};
    try {
      payload = JSON.parse(barcodePayload || "{}");
    } catch (_) {
      return setResult("JSON inválido para barcode.");
    }
    const data = await run("POST", `/products/${encodeURIComponent(pid)}/barcodes`, payload, "post-barcode");
    if (data) await handleListBarcodes();
  }

  async function handleListBarcodes() {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    const data = await run("GET", `/products/${encodeURIComponent(pid)}/barcodes?limit=100`, null, "get-barcodes");
    if (data?.ok && Array.isArray(data.items)) setBarcodeItems(data.items);
  }

  async function handleDeleteMedia(mediaId) {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    const data = await run("DELETE", `/products/${encodeURIComponent(pid)}/media/${encodeURIComponent(mediaId)}`, null, `delete-media-${mediaId}`);
    if (data) await handleListMedia();
  }

  function startEditMedia(item) {
    setEditingMediaId(item.id);
    setEditingMediaForm({
      media_type: String(item.media_type || "IMAGE"),
      url: String(item.url || ""),
      sort_order: Number(item.sort_order || 0),
      is_primary: Boolean(item.is_primary),
    });
  }

  async function handlePatchMedia(mediaId) {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    const payload = {
      media_type: String(editingMediaForm.media_type || "").trim().toUpperCase(),
      url: String(editingMediaForm.url || "").trim(),
      sort_order: Number(editingMediaForm.sort_order || 0),
      is_primary: Boolean(editingMediaForm.is_primary),
    };
    setMediaRowFeedback((prev) => ({ ...prev, [mediaId]: { status: "running", message: "Salvando..." } }));
    const data = await run("PATCH", `/products/${encodeURIComponent(pid)}/media/${encodeURIComponent(mediaId)}`, payload, `patch-media-${mediaId}`);
    if (data) {
      setMediaRowFeedback((prev) => ({ ...prev, [mediaId]: { status: "success", message: "Salvo com sucesso." } }));
      setEditingMediaId("");
      await handleListMedia();
    } else {
      setMediaRowFeedback((prev) => ({ ...prev, [mediaId]: { status: "error", message: "Erro ao salvar." } }));
    }
  }

  async function handleDeleteBarcode(barcodeId) {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    const data = await run("DELETE", `/products/${encodeURIComponent(pid)}/barcodes/${encodeURIComponent(barcodeId)}`, null, `delete-barcode-${barcodeId}`);
    if (data) await handleListBarcodes();
  }

  function startEditBarcode(item) {
    setEditingBarcodeId(item.id);
    setEditingBarcodeForm({
      barcode_type: String(item.barcode_type || "EAN13"),
      barcode_value: String(item.barcode_value || ""),
      is_primary: Boolean(item.is_primary),
    });
  }

  async function handlePatchBarcode(barcodeId) {
    const pid = String(productId || "").trim();
    if (!pid) return setResult("Informe product_id.");
    const payload = {
      barcode_type: String(editingBarcodeForm.barcode_type || "").trim().toUpperCase(),
      barcode_value: String(editingBarcodeForm.barcode_value || "").trim().toUpperCase(),
      is_primary: Boolean(editingBarcodeForm.is_primary),
    };
    setBarcodeRowFeedback((prev) => ({ ...prev, [barcodeId]: { status: "running", message: "Salvando..." } }));
    const data = await run(
      "PATCH",
      `/products/${encodeURIComponent(pid)}/barcodes/${encodeURIComponent(barcodeId)}`,
      payload,
      `patch-barcode-${barcodeId}`,
    );
    if (data) {
      setBarcodeRowFeedback((prev) => ({ ...prev, [barcodeId]: { status: "success", message: "Salvo com sucesso." } }));
      setEditingBarcodeId("");
      await handleListBarcodes();
    } else {
      setBarcodeRowFeedback((prev) => ({ ...prev, [barcodeId]: { status: "error", message: "Erro ao salvar." } }));
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS - Products Assets (Pr-1)" />
        <p style={mutedStyle}>Operação mínima para media/barcodes por produto.</p>

        <label style={labelStyle}>
          Product ID
          <input value={productId} onChange={(e) => setProductId(e.target.value)} style={inputStyle} placeholder="ex.: sku_123" />
        </label>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload media (JSON)
          <textarea value={mediaPayload} onChange={(e) => setMediaPayload(e.target.value)} style={textareaStyle} />
        </label>
        <div style={actionsStyle}>
          <button type="button" style={buttonStyle} onClick={() => void handlePostMedia()} disabled={Boolean(loading)}>
            {loading === "post-media" ? "Salvando..." : "POST media"}
          </button>
          <button type="button" style={buttonSecondaryStyle} onClick={() => void handleListMedia()} disabled={Boolean(loading)}>
            {loading === "get-media" ? "Consultando..." : "GET media"}
          </button>
        </div>

        <section style={subCardStyle}>
          <div style={subCardHeaderStyle}>
            <h3 style={{ margin: 0 }}>Mídias cadastradas</h3>
            <button type="button" style={buttonSecondaryStyle} onClick={() => void handleListMedia()} disabled={Boolean(loading)}>
              Recarregar
            </button>
          </div>
          {!mediaItems.length ? (
            <p style={mutedStyle}>Sem mídias carregadas para o produto informado.</p>
          ) : (
            <div style={tableWrapStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>ID</th>
                    <th style={thStyle}>Tipo</th>
                    <th style={thStyle}>URL</th>
                    <th style={thStyle}>Primary</th>
                    <th style={thStyle}>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {mediaItems.map((item) => (
                    <tr key={item.id}>
                      <td style={tdStyle}>{item.id}</td>
                      <td style={tdStyle}>
                        {editingMediaId === item.id ? (
                          <input
                            value={editingMediaForm.media_type}
                            onChange={(e) => setEditingMediaForm((prev) => ({ ...prev, media_type: e.target.value }))}
                            style={inlineInputStyle}
                            placeholder="IMAGE|VIDEO|PDF|3D"
                          />
                        ) : (
                          item.media_type
                        )}
                      </td>
                      <td style={tdStyle}>
                        {editingMediaId === item.id ? (
                          <input
                            value={editingMediaForm.url}
                            onChange={(e) => setEditingMediaForm((prev) => ({ ...prev, url: e.target.value }))}
                            style={inlineInputStyle}
                            placeholder="https://..."
                          />
                        ) : (
                          item.url
                        )}
                      </td>
                      <td style={tdStyle}>
                        {editingMediaId === item.id ? (
                          <label style={inlineCheckLabelStyle}>
                            <input
                              type="checkbox"
                              checked={Boolean(editingMediaForm.is_primary)}
                              onChange={(e) => setEditingMediaForm((prev) => ({ ...prev, is_primary: e.target.checked }))}
                            />
                            primary
                          </label>
                        ) : (
                          String(item.is_primary)
                        )}
                      </td>
                      <td style={tdStyle}>
                        <div style={inlineActionsStyle}>
                          {editingMediaId === item.id ? (
                            <>
                              <button
                                type="button"
                                style={buttonWarnStyle}
                                onClick={() => void handlePatchMedia(item.id)}
                                disabled={Boolean(loading)}
                              >
                                Salvar
                              </button>
                              <button
                                type="button"
                                style={buttonSecondarySmallStyle}
                                onClick={() => setEditingMediaId("")}
                                disabled={Boolean(loading)}
                              >
                                Cancelar
                              </button>
                            </>
                          ) : (
                            <button
                              type="button"
                              style={buttonSecondarySmallStyle}
                              onClick={() => startEditMedia(item)}
                              disabled={Boolean(loading)}
                            >
                              Editar
                            </button>
                          )}
                          <button
                            type="button"
                            style={buttonDangerStyle}
                            onClick={() => void handleDeleteMedia(item.id)}
                            disabled={Boolean(loading)}
                          >
                            Delete
                          </button>
                          {mediaRowFeedback[item.id]?.message ? (
                            <span
                              style={{
                                ...rowChipStyle,
                                ...(mediaRowFeedback[item.id]?.status === "success"
                                  ? rowChipSuccessStyle
                                  : mediaRowFeedback[item.id]?.status === "error"
                                    ? rowChipErrorStyle
                                    : rowChipRunningStyle),
                              }}
                            >
                              {mediaRowFeedback[item.id]?.message}
                            </span>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload barcode (JSON)
          <textarea value={barcodePayload} onChange={(e) => setBarcodePayload(e.target.value)} style={textareaStyle} />
        </label>
        <div style={actionsStyle}>
          <button type="button" style={buttonStyle} onClick={() => void handlePostBarcode()} disabled={Boolean(loading)}>
            {loading === "post-barcode" ? "Salvando..." : "POST barcode"}
          </button>
          <button type="button" style={buttonSecondaryStyle} onClick={() => void handleListBarcodes()} disabled={Boolean(loading)}>
            {loading === "get-barcodes" ? "Consultando..." : "GET barcodes"}
          </button>
        </div>

        <section style={subCardStyle}>
          <div style={subCardHeaderStyle}>
            <h3 style={{ margin: 0 }}>Barcodes cadastrados</h3>
            <button type="button" style={buttonSecondaryStyle} onClick={() => void handleListBarcodes()} disabled={Boolean(loading)}>
              Recarregar
            </button>
          </div>
          {!barcodeItems.length ? (
            <p style={mutedStyle}>Sem barcodes carregados para o produto informado.</p>
          ) : (
            <div style={tableWrapStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>ID</th>
                    <th style={thStyle}>Tipo</th>
                    <th style={thStyle}>Valor</th>
                    <th style={thStyle}>Primary</th>
                    <th style={thStyle}>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {barcodeItems.map((item) => (
                    <tr key={item.id}>
                      <td style={tdStyle}>{item.id}</td>
                      <td style={tdStyle}>
                        {editingBarcodeId === item.id ? (
                          <input
                            value={editingBarcodeForm.barcode_type}
                            onChange={(e) => setEditingBarcodeForm((prev) => ({ ...prev, barcode_type: e.target.value }))}
                            style={inlineInputStyle}
                            placeholder="EAN13|EAN8|GTIN14|QR|CODE128|DATAMATRIX"
                          />
                        ) : (
                          item.barcode_type
                        )}
                      </td>
                      <td style={tdStyle}>
                        {editingBarcodeId === item.id ? (
                          <input
                            value={editingBarcodeForm.barcode_value}
                            onChange={(e) => setEditingBarcodeForm((prev) => ({ ...prev, barcode_value: e.target.value }))}
                            style={inlineInputStyle}
                            placeholder="valor do barcode"
                          />
                        ) : (
                          item.barcode_value
                        )}
                      </td>
                      <td style={tdStyle}>
                        {editingBarcodeId === item.id ? (
                          <label style={inlineCheckLabelStyle}>
                            <input
                              type="checkbox"
                              checked={Boolean(editingBarcodeForm.is_primary)}
                              onChange={(e) => setEditingBarcodeForm((prev) => ({ ...prev, is_primary: e.target.checked }))}
                            />
                            primary
                          </label>
                        ) : (
                          String(item.is_primary)
                        )}
                      </td>
                      <td style={tdStyle}>
                        <div style={inlineActionsStyle}>
                          {editingBarcodeId === item.id ? (
                            <>
                              <button
                                type="button"
                                style={buttonWarnStyle}
                                onClick={() => void handlePatchBarcode(item.id)}
                                disabled={Boolean(loading)}
                              >
                                Salvar
                              </button>
                              <button
                                type="button"
                                style={buttonSecondarySmallStyle}
                                onClick={() => setEditingBarcodeId("")}
                                disabled={Boolean(loading)}
                              >
                                Cancelar
                              </button>
                            </>
                          ) : (
                            <button
                              type="button"
                              style={buttonSecondarySmallStyle}
                              onClick={() => startEditBarcode(item)}
                              disabled={Boolean(loading)}
                            >
                              Editar
                            </button>
                          )}
                          <button
                            type="button"
                            style={buttonDangerStyle}
                            onClick={() => void handleDeleteBarcode(item.id)}
                            disabled={Boolean(loading)}
                          >
                            Delete
                          </button>
                          {barcodeRowFeedback[item.id]?.message ? (
                            <span
                              style={{
                                ...rowChipStyle,
                                ...(barcodeRowFeedback[item.id]?.status === "success"
                                  ? rowChipSuccessStyle
                                  : barcodeRowFeedback[item.id]?.status === "error"
                                    ? rowChipErrorStyle
                                    : rowChipRunningStyle),
                              }}
                            >
                              {barcodeRowFeedback[item.id]?.message}
                            </span>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <pre style={resultStyle}>{result || "Execute uma ação para visualizar resposta técnica."}</pre>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const subCardStyle = { marginTop: 12, background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const subCardHeaderStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap" };
const mutedStyle = { color: "#94A3B8" };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0" };
const textareaStyle = { minHeight: 110, padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const buttonSecondaryStyle = { padding: "10px 14px", borderRadius: 10, border: "1px solid #334155", background: "#0B1220", color: "#E2E8F0", fontWeight: 700, cursor: "pointer" };
const buttonSecondarySmallStyle = { padding: "6px 10px", borderRadius: 8, border: "1px solid #334155", background: "#0B1220", color: "#E2E8F0", fontWeight: 700, cursor: "pointer" };
const buttonWarnStyle = { padding: "6px 10px", borderRadius: 8, border: "1px solid rgba(217,119,6,0.45)", background: "rgba(217,119,6,0.2)", color: "#FDE68A", fontWeight: 700, cursor: "pointer" };
const buttonDangerStyle = { padding: "6px 10px", borderRadius: 8, border: "1px solid rgba(220,38,38,0.45)", background: "rgba(220,38,38,0.15)", color: "#FCA5A5", fontWeight: 700, cursor: "pointer" };
const tableWrapStyle = { overflowX: "auto", marginTop: 8 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 720 };
const thStyle = { textAlign: "left", padding: "8px 10px", borderBottom: "1px solid #334155", color: "#94A3B8", fontSize: 12 };
const tdStyle = { padding: "8px 10px", borderBottom: "1px solid #1E293B", color: "#E2E8F0", fontSize: 12, verticalAlign: "top" };
const inlineInputStyle = { width: "100%", padding: "6px 8px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0", fontSize: 12 };
const inlineActionsStyle = { display: "flex", gap: 6, flexWrap: "wrap" };
const inlineCheckLabelStyle = { display: "inline-flex", alignItems: "center", gap: 6, color: "#E2E8F0", fontSize: 12 };
const rowChipStyle = { display: "inline-flex", alignItems: "center", padding: "4px 8px", borderRadius: 999, fontSize: 11, fontWeight: 700 };
const rowChipSuccessStyle = { color: "#86EFAC", background: "rgba(22,163,74,0.2)", border: "1px solid rgba(22,163,74,0.5)" };
const rowChipErrorStyle = { color: "#FCA5A5", background: "rgba(220,38,38,0.18)", border: "1px solid rgba(220,38,38,0.45)" };
const rowChipRunningStyle = { color: "#FDE68A", background: "rgba(217,119,6,0.2)", border: "1px solid rgba(217,119,6,0.45)" };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };
