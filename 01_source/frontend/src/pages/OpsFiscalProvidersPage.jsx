import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const BILLING_BASE =
  import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";

const INTERNAL_TOKEN =
  import.meta.env.VITE_INTERNAL_TOKEN || "";
const LATENCY_ALERT_MS = 1500;

function headersJson() {
  return {
    "Content-Type": "application/json",
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

export default function OpsFiscalProvidersPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState("");
  const [error, setError] = useState("");
  const [invoiceId, setInvoiceId] = useState("");
  const [orderId, setOrderId] = useState("");
  const [danfeBusy, setDanfeBusy] = useState(false);
  const [forceBusy, setForceBusy] = useState(false);
  const [danfeResult, setDanfeResult] = useState(null);

  async function loadStatus() {
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${BILLING_BASE}/admin/fiscal/providers/status`, {
        method: "GET",
        headers: headersJson(),
      });
      const payload = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(payload?.detail || "Falha ao carregar status dos providers.");
      setItems(Array.isArray(payload?.items) ? payload.items : []);
    } catch (err) {
      const raw = String(err?.message || err);
      if (raw.toLowerCase().includes("failed to fetch")) {
        setError(
          `Falha de rede/CORS ao acessar ${BILLING_BASE}. Verifique VITE_BILLING_FISCAL_BASE_URL e se o backend está no ar.`
        );
      } else {
        setError(raw);
      }
    } finally {
      setLoading(false);
    }
  }

  async function runTest(country) {
    setTesting(country);
    setError("");
    try {
      const qs = new URLSearchParams({ country }).toString();
      const r = await fetch(`${BILLING_BASE}/admin/fiscal/providers/test-connectivity?${qs}`, {
        method: "POST",
        headers: headersJson(),
      });
      const payload = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(payload?.detail || "Falha no teste de conectividade.");
      await loadStatus();
    } catch (err) {
      const raw = String(err?.message || err);
      if (raw.toLowerCase().includes("failed to fetch")) {
        setError(
          `Falha de rede/CORS ao acessar ${BILLING_BASE}. Verifique VITE_BILLING_FISCAL_BASE_URL e se o backend está no ar.`
        );
      } else {
        setError(raw);
      }
    } finally {
      setTesting("");
    }
  }

  function downloadBase64Pdf(base64Content, filename) {
    const byteChars = atob(base64Content);
    const byteNumbers = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i += 1) {
      byteNumbers[i] = byteChars.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "danfe-stub.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  async function handleGenerateDanfePdf() {
    const normalized = String(invoiceId || "").trim();
    if (!normalized) {
      setError("Informe um invoice_id válido para gerar DANFE PDF stub.");
      return;
    }
    setDanfeBusy(true);
    setDanfeResult(null);
    setError("");
    try {
      const r = await fetch(`${BILLING_BASE}/admin/fiscal/danfe/${encodeURIComponent(normalized)}/pdf`, {
        method: "GET",
        headers: headersJson(),
      });
      const payload = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(payload?.detail || "Falha ao gerar DANFE PDF stub.");
      if (!payload?.content_base64) throw new Error("Resposta sem content_base64.");
      downloadBase64Pdf(payload.content_base64, payload.filename || `danfe-${normalized}.pdf`);
      setDanfeResult({
        ok: true,
        invoice_id: payload.invoice_id,
        filename: payload.filename,
        format: payload.format,
        payload,
      });
    } catch (err) {
      const raw = String(err?.message || err);
      if (raw.toLowerCase().includes("failed to fetch")) {
        setError(
          `Falha de rede/CORS ao acessar ${BILLING_BASE}. Verifique VITE_BILLING_FISCAL_BASE_URL e se o backend está no ar.`
        );
      } else {
        setError(raw);
      }
    } finally {
      setDanfeBusy(false);
    }
  }

  async function handleCopyDanfeJson() {
    const normalized = String(invoiceId || "").trim();
    if (!normalized) {
      setError("Informe um invoice_id válido para copiar JSON do DANFE.");
      return;
    }
    setDanfeBusy(true);
    setError("");
    try {
      const r = await fetch(`${BILLING_BASE}/admin/fiscal/danfe/${encodeURIComponent(normalized)}/pdf`, {
        method: "GET",
        headers: headersJson(),
      });
      const payload = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(payload?.detail || "Falha ao carregar JSON do DANFE.");
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      setDanfeResult({
        ok: true,
        invoice_id: payload.invoice_id,
        filename: payload.filename,
        format: payload.format,
        payload,
        copied_json: true,
      });
    } catch (err) {
      const raw = String(err?.message || err);
      if (raw.toLowerCase().includes("failed to fetch")) {
        setError(
          `Falha de rede/CORS ao acessar ${BILLING_BASE}. Verifique VITE_BILLING_FISCAL_BASE_URL e se o backend está no ar.`
        );
      } else {
        setError(raw);
      }
    } finally {
      setDanfeBusy(false);
    }
  }

  async function handleForceIssueByOrderId() {
    const normalized = String(orderId || "").trim();
    if (!normalized) {
      setError("Informe um order_id válido para gerar invoice.");
      return;
    }
    setForceBusy(true);
    setError("");
    setDanfeResult(null);
    try {
      const r = await fetch(
        `${BILLING_BASE}/admin/fiscal/force-issue/${encodeURIComponent(normalized)}`,
        {
          method: "POST",
          headers: headersJson(),
        }
      );
      const payload = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(payload?.detail || "Falha ao gerar invoice por order_id.");
      setDanfeResult({
        ok: true,
        order_id: normalized,
        invoice_id: payload?.invoice?.id || payload?.invoice_id || "-",
        message: "Invoice gerada/garantida com sucesso para o pedido.",
        payload,
      });
    } catch (err) {
      const raw = String(err?.message || err);
      if (raw.toLowerCase().includes("failed to fetch")) {
        setError(
          `Falha de rede/CORS ao acessar ${BILLING_BASE}. Verifique VITE_BILLING_FISCAL_BASE_URL e se o backend está no ar.`
        );
      } else {
        setError(raw);
      }
    } finally {
      setForceBusy(false);
    }
  }

  useEffect(() => {
    void loadStatus();
  }, []);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={crossShortcutStyle}>
          <Link to="/ops/health" style={crossShortcutLinkStyle}>
            Voltar para ops/health
          </Link>
        </div>
        <div style={headerRowStyle}>
          <div>
            <h1 style={{ margin: 0 }}>OPS - Fiscal Providers (BR/PT)</h1>
            <p style={mutedTextStyle}>
              Status do provider real por país, último erro e teste de conectividade.
            </p>
          </div>
          <div style={toolbarStyle}>
            <button onClick={() => void loadStatus()} style={buttonGhostStyle} disabled={loading}>
              {loading ? "Atualizando..." : "Atualizar status"}
            </button>
            <button onClick={() => void runTest("ALL")} style={buttonPrimaryStyle} disabled={testing !== ""}>
              {testing === "ALL" ? "Testando..." : "Testar BR + PT"}
            </button>
          </div>
        </div>

        <div style={danfeBoxStyle}>
          <h3 style={{ marginTop: 0, marginBottom: 8 }}>Gerar DANFE PDF (stub)</h3>
          <p style={{ ...mutedTextStyle, marginTop: 0 }}>
            Operação rápida por `invoice_id` para baixar PDF simplificado base64.
          </p>
          <div style={toolbarStyle}>
            <input
              value={invoiceId}
              onChange={(e) => setInvoiceId(e.target.value)}
              placeholder="invoice_id (ex.: inv_abc123)"
              style={inputStyle}
            />
            <button onClick={() => void handleGenerateDanfePdf()} style={buttonPrimaryStyle} disabled={danfeBusy}>
              {danfeBusy ? "Gerando..." : "Gerar DANFE PDF stub"}
            </button>
            <button onClick={() => void handleCopyDanfeJson()} style={buttonGhostStyle} disabled={danfeBusy}>
              {danfeBusy ? "Copiando..." : "Copiar JSON do DANFE"}
            </button>
          </div>
          {danfeResult ? (
            <div style={danfeResultStyle}>
              {danfeResult.filename ? (
                <>
                  Download iniciado: <b>{danfeResult.filename}</b> ({danfeResult.format})
                  {danfeResult.copied_json ? " • JSON copiado para área de transferência." : ""}
                </>
              ) : (
                <>
                  {danfeResult.message || "Operação concluída."}{" "}
                  {danfeResult.order_id ? `order_id=${danfeResult.order_id}` : ""}{" "}
                  {danfeResult.invoice_id ? `invoice_id=${danfeResult.invoice_id}` : ""}
                </>
              )}
            </div>
          ) : null}
        </div>

        <div style={danfeBoxStyle}>
          <h3 style={{ marginTop: 0, marginBottom: 8 }}>Gerar invoice por order_id</h3>
          <p style={{ ...mutedTextStyle, marginTop: 0 }}>
            Operação de suporte: força emissão/garantia da invoice para um pedido.
          </p>
          <div style={toolbarStyle}>
            <input
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
              placeholder="order_id (ex.: 1b9a54e8-...)"
              style={inputStyle}
            />
            <button onClick={() => void handleForceIssueByOrderId()} style={buttonPrimaryStyle} disabled={forceBusy}>
              {forceBusy ? "Gerando..." : "Gerar invoice por order_id"}
            </button>
          </div>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        <div style={tableWrapStyle}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>País</th>
                <th style={thStyle}>Provider</th>
                <th style={thStyle}>Modo</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Health</th>
                <th style={thStyle}>Último erro</th>
                <th style={thStyle}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.country}>
                  <td style={tdStyle}>{item.country}</td>
                  <td style={tdStyle}>{item.provider_name}</td>
                  <td style={tdStyle}>{item.mode}</td>
                  <td style={tdStyle}>{item.enabled ? "enabled" : "disabled"}</td>
                  <td style={tdStyle}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                      <span>{item.last_status}</span>
                      {buildAlertBadge(item)}
                    </div>
                    <small style={smallStyle}>
                      {item.last_http_status ? `HTTP ${item.last_http_status}` : "-"} |{" "}
                      {item.last_latency_ms != null ? `${item.last_latency_ms}ms` : "-"}
                    </small>
                  </td>
                  <td style={tdStyle}>
                    <small style={smallStyle}>{item.last_error || "-"}</small>
                  </td>
                  <td style={tdStyle}>
                    <button
                      onClick={() => void runTest(item.country)}
                      style={buttonGhostStyle}
                      disabled={testing !== ""}
                    >
                      {testing === item.country ? "Testando..." : `Testar ${item.country}`}
                    </button>
                  </td>
                </tr>
              ))}
              {!loading && items.length === 0 ? (
                <tr>
                  <td style={tdStyle} colSpan={7}>
                    Nenhum provider encontrado.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function buildAlertBadge(item) {
  const status = String(item?.last_status || "").toUpperCase();
  const latency = Number(item?.last_latency_ms);
  if (status === "ERROR") {
    return <span style={badgeDangerStyle}>ALERTA: ERROR</span>;
  }
  if (Number.isFinite(latency) && latency > LATENCY_ALERT_MS) {
    return <span style={badgeWarnStyle}>ALERTA: LATÊNCIA {latency}ms</span>;
  }
  return <span style={badgeOkStyle}>OK</span>;
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#f5f7fa", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#11161c", border: "1px solid rgba(255,255,255,0.10)", borderRadius: 16, padding: 16 };
const headerRowStyle = { display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" };
const mutedTextStyle = { color: "rgba(245,247,250,0.8)", marginTop: 8, marginBottom: 0 };
const toolbarStyle = { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" };
const inputStyle = {
  minWidth: 260,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};
const buttonGhostStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.16)", background: "transparent", color: "#e2e8f0", cursor: "pointer", fontWeight: 600 };
const buttonPrimaryStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid rgba(31,122,63,0.50)", background: "#1f7a3f", color: "#fff", cursor: "pointer", fontWeight: 700 };
const errorStyle = { marginTop: 12, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12, overflow: "auto" };
const danfeBoxStyle = {
  marginTop: 14,
  marginBottom: 10,
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 12,
  background: "rgba(255,255,255,0.03)",
  padding: 12,
};
const danfeResultStyle = {
  marginTop: 8,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(22,163,74,0.55)",
  background: "rgba(22,163,74,0.18)",
  color: "#bbf7d0",
  fontSize: 13,
};
const tableWrapStyle = { marginTop: 14, overflowX: "auto" };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 900 };
const thStyle = { textAlign: "left", borderBottom: "1px solid rgba(255,255,255,0.14)", padding: "8px 10px", fontSize: 13 };
const tdStyle = { borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "8px 10px", verticalAlign: "top" };
const smallStyle = { color: "rgba(226,232,240,0.8)" };
const badgeBaseStyle = { display: "inline-flex", borderRadius: 999, padding: "2px 8px", fontSize: 11, fontWeight: 800 };
const badgeDangerStyle = { ...badgeBaseStyle, color: "#fecaca", border: "1px solid rgba(185,28,28,0.65)", background: "rgba(185,28,28,0.2)" };
const badgeWarnStyle = { ...badgeBaseStyle, color: "#fde68a", border: "1px solid rgba(202,138,4,0.65)", background: "rgba(202,138,4,0.2)" };
const badgeOkStyle = { ...badgeBaseStyle, color: "#86efac", border: "1px solid rgba(22,163,74,0.65)", background: "rgba(22,163,74,0.2)" };
const crossShortcutStyle = { display: "flex", justifyContent: "flex-end", marginBottom: 10 };
const crossShortcutLinkStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid rgba(96,165,250,0.55)", background: "rgba(96,165,250,0.15)", color: "#bfdbfe", textDecoration: "none", fontWeight: 700, fontSize: 13 };
