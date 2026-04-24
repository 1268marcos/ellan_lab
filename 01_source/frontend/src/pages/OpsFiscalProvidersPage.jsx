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
const buttonGhostStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.16)", background: "transparent", color: "#e2e8f0", cursor: "pointer", fontWeight: 600 };
const buttonPrimaryStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid rgba(31,122,63,0.50)", background: "#1f7a3f", color: "#fff", cursor: "pointer", fontWeight: 700 };
const errorStyle = { marginTop: 12, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12, overflow: "auto" };
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
