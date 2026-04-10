// 01_source/frontend/src/pages/public/PublicFiscalSearchPage.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";

const API_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const FRONTEND_BASE =
  import.meta.env.VITE_FRONTEND_BASE_URL || window.location.origin;

function toAbsoluteApiUrl(path) {
  if (!path) return "#";
  if (String(path).startsWith("http://") || String(path).startsWith("https://")) {
    return path;
  }
  return `${API_BASE}${path}`;
}

function normalize(value) {
  return String(value || "").trim().toUpperCase();
}

export default function PublicFiscalSearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [code, setCode] = useState(searchParams.get("code") || "");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const hasAutoSearched = useRef(false);

  const normalizedCode = useMemo(() => normalize(code), [code]);

  const deepLink = useMemo(() => {
    if (!normalizedCode) return "";
    return `${FRONTEND_BASE}/comprovante?code=${encodeURIComponent(normalizedCode)}`;
  }, [normalizedCode]);

  async function handleSearch(explicitCode) {
    const nextCode = normalize(explicitCode ?? code);

    if (!nextCode) {
      setError("Informe um código de comprovante.");
      setData(null);
      return;
    }

    if (loading) return;

    setCode(nextCode);
    setLoading(true);
    setError("");
    setData(null);

    try {
      const res = await fetch(
        `${API_BASE}/public/fiscal/by-code/${encodeURIComponent(nextCode)}`
      );

      const json = await res.json();

      if (!res.ok) {
        throw new Error(
          json?.detail?.message ||
            json?.detail ||
            "Comprovante não encontrado"
        );
      }

      setData(json);
      setSearchParams({ code: nextCode }, { replace: true });
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (hasAutoSearched.current) return;

    const initialCode = normalize(searchParams.get("code"));
    if (!initialCode) return;

    hasAutoSearched.current = true;
    setCode(initialCode);
    handleSearch(initialCode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function copyDeepLink() {
    if (!deepLink) return;
    navigator.clipboard?.writeText(deepLink);
    window.alert("Link copiado.");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") {
      handleSearch(code);
    }
  }

  function renderResult() {
    if (!data) return null;

    const doc = data.document || {};
    const order = data.order || {};
    const allocation = data.allocation || {};
    const pickup = data.pickup || {};
    const links = data.links || {};
    const printUrl = toAbsoluteApiUrl(links.print_html);
    const jsonUrl = toAbsoluteApiUrl(links.json);

    const amount =
      ((doc.amount_cents || order.amount_cents || 0) / 100).toFixed(2);

    return (
      <div style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Comprovante</h2>

        <div style={codeStyle}>{data.receipt_code}</div>

        <div style={resultGridStyle}>
          <div>
            <table style={tableStyle}>
              <tbody>
                <tr><td>Pedido</td><td>{order.id || ""}</td></tr>
                <tr><td>Canal</td><td>{order.channel || ""}</td></tr>
                <tr><td>Região</td><td>{order.region || ""}</td></tr>
                <tr><td>Valor</td><td>{doc.currency || "BRL"} {amount}</td></tr>
                <tr><td>Método pagamento</td><td>{order.payment_method || ""}</td></tr>
                <tr><td>Gateway ID</td><td>{order.gateway_transaction_id || ""}</td></tr>
                <tr><td>SKU</td><td>{order.sku_id || ""}</td></tr>
                <tr><td>Totem</td><td>{order.totem_id || ""}</td></tr>
                <tr><td>Allocation</td><td>{allocation.id || ""}</td></tr>
                <tr><td>Pickup</td><td>{pickup.id || ""}</td></tr>
                <tr><td>Locker</td><td>{pickup.locker_id || allocation.locker_id || ""}</td></tr>
                <tr><td>Machine</td><td>{pickup.machine_id || ""}</td></tr>
                <tr><td>Slot</td><td>{pickup.slot || allocation.slot || ""}</td></tr>
              </tbody>
            </table>

            <div style={actionsStyle}>
              <a
                href={printUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={btnStyle}
              >
                Abrir impressão
              </a>

              <a
                href={jsonUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={btnStyle}
              >
                Ver JSON
              </a>

              <button
                type="button"
                style={btnStyle}
                onClick={() =>
                  window.open(printUrl, "_blank", "noopener,noreferrer")
                }
              >
                Imprimir / PDF
              </button>
            </div>
          </div>

          <div style={qrCardStyle}>
            <div style={{ fontWeight: 700, marginBottom: 12 }}>
              QRCode do comprovante
            </div>

            {deepLink ? (
              <>
                <div style={qrBoxStyle}>
                  <QRCodeSVG value={deepLink} size={180} />
                </div>

                <div style={smallMutedStyle}>Link público do comprovante</div>
                <div style={linkPreviewStyle}>{deepLink}</div>

                <div style={actionsStyle}>
                  <button type="button" style={btnStyle} onClick={copyDeepLink}>
                    Copiar link
                  </button>
                  <a
                    href={deepLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={btnStyle}
                  >
                    Abrir link
                  </a>
                </div>
              </>
            ) : (
              <div style={smallMutedStyle}>
                Busque um comprovante para gerar o QRCode.
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <h1 style={{ marginTop: 0 }}>Buscar comprovante</h1>
      <p style={mutedStyle}>
        Digite o código do comprovante ou use um link com <code>?code=...</code>.
      </p>

      <div style={searchRowStyle}>
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ex.: BR-KSK-57FC9258"
          style={inputStyle}
        />

        <button
          type="button"
          onClick={() => handleSearch(code)}
          style={btnPrimaryStyle}
          disabled={loading}
        >
          {loading ? "Buscando..." : "Buscar"}
        </button>
      </div>

      {error ? <div style={errorStyle}>{error}</div> : null}

      {renderResult()}
    </div>
  );
}

const pageStyle = {
  padding: 24,
  maxWidth: 1100,
  margin: "0 auto",
};

const mutedStyle = {
  color: "#666",
  marginTop: 6,
};

const searchRowStyle = {
  display: "flex",
  gap: 10,
  marginTop: 16,
  flexWrap: "wrap",
};

const inputStyle = {
  flex: 1,
  minWidth: 280,
  padding: 10,
  borderRadius: 8,
  border: "1px solid #ccc",
  textTransform: "uppercase",
};

const btnPrimaryStyle = {
  padding: "10px 16px",
  borderRadius: 8,
  border: "none",
  background: "#1f7a3f",
  color: "white",
  cursor: "pointer",
};

const btnStyle = {
  padding: "8px 12px",
  borderRadius: 8,
  border: "1px solid #ccc",
  textDecoration: "none",
  color: "#333",
  background: "rgba(255, 255, 255, 0.85)",
  cursor: "pointer",
};

const cardStyle = {
  marginTop: 20,
  padding: 16,
  border: "1px solid #ddd",
  borderRadius: 12,
  background: "rgba(255, 255, 255, 0.06)",
};

const codeStyle = {
  display: "inline-block",
  fontWeight: "bold",
  margin: "10px 0 16px 0",
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px dashed #bbb",
  background: "rgba(51, 59, 165, 0.75)",
};

const resultGridStyle = {
  display: "grid",
  gridTemplateColumns: "minmax(0, 1.7fr) minmax(280px, 0.9fr)",
  gap: 16,
};

const qrCardStyle = {
  border: "1px solid #e5e7eb",
  borderRadius: 12,
  padding: 16,
  background: "rgba(51, 59, 165, 0.75)",
  height: "fit-content",
};

const qrBoxStyle = {
  background: "white",
  padding: 12,
  borderRadius: 12,
  display: "inline-flex",
};

const linkPreviewStyle = {
  marginTop: 8,
  padding: 10,
  borderRadius: 8,
  background: "rgba(51, 59, 165, 0.75)",
  border: "1px solid #e5e7eb",
  fontSize: 12,
  wordBreak: "break-word",
};

const smallMutedStyle = {
  color: "#666",
  fontSize: 13,
  marginTop: 10,
};

const tableStyle = {
  width: "100%",
  borderCollapse: "collapse",
};

const actionsStyle = {
  marginTop: 16,
  display: "flex",
  gap: 10,
  flexWrap: "wrap",
};

const errorStyle = {
  marginTop: 16,
  color: "red",
};