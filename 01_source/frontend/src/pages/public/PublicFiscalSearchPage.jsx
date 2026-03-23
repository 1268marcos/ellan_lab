// 01_source/frontend/src/pages/public/PublicFiscalSearchPage.jsx
import React, { useState } from "react";

const API_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

function toAbsoluteApiUrl(path) {
  if (!path) return "#";
  if (String(path).startsWith("http://") || String(path).startsWith("https://")) {
    return path;
  }
  return `${API_BASE}${path}`;
}

export default function PublicFiscalSearchPage() {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  function normalize(value) {
    return String(value || "").trim().toUpperCase();
  }

  async function handleSearch() {
    const normalized = normalize(code);
    setCode(normalized);

    if (!normalized) {
      setError("Informe um código de comprovante.");
      setData(null);
      return;
    }

    setLoading(true);
    setError("");
    setData(null);

    try {
      const res = await fetch(
        `${API_BASE}/public/fiscal/by-code/${encodeURIComponent(normalized)}`
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
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
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
        <h2>Comprovante</h2>

        <div style={codeStyle}>{data.receipt_code}</div>

        <table style={tableStyle}>
          <tbody>
            <tr><td>Pedido</td><td>{order.id}</td></tr>
            <tr><td>Canal</td><td>{order.channel}</td></tr>
            <tr><td>Região</td><td>{order.region}</td></tr>
            <tr><td>Valor</td><td>{doc.currency} {amount}</td></tr>
            <tr><td>Método pagamento</td><td>{order.payment_method}</td></tr>
            <tr><td>Gateway ID</td><td>{order.gateway_transaction_id}</td></tr>

            <tr><td>SKU</td><td>{order.sku_id}</td></tr>
            <tr><td>Totem</td><td>{order.totem_id}</td></tr>
            <tr><td>Allocation</td><td>{allocation.id}</td></tr>
            <tr><td>Pickup</td><td>{pickup.id}</td></tr>
            <tr><td>Locker</td><td>{pickup.locker_id || allocation.locker_id}</td></tr>
            <tr><td>Machine</td><td>{pickup.machine_id}</td></tr>
            <tr><td>Slot</td><td>{pickup.slot || allocation.slot}</td></tr>
          </tbody>
        </table>

        <div style={{ marginTop: 16, display: "flex", gap: 10, flexWrap: "wrap" }}>
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
            style={btnStyle}
            onClick={() => window.open(printUrl, "_blank", "noopener,noreferrer")}
          >
            Imprimir / PDF
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <h1>Buscar comprovante</h1>

      <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Ex: KSK-XXXXX"
          style={inputStyle}
        />

        <button onClick={handleSearch} style={btnPrimary}>
          {loading ? "Buscando..." : "Buscar"}
        </button>
      </div>

      {error && <div style={errorStyle}>{error}</div>}

      {renderResult()}
    </div>
  );
}

/* ================= STYLES ================= */

const pageStyle = {
  padding: 24,
  maxWidth: 800,
  margin: "0 auto",
};

const inputStyle = {
  flex: 1,
  padding: 10,
  borderRadius: 8,
  border: "1px solid #ccc",
};

const btnPrimary = {
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
  background: "#fff",
};

const cardStyle = {
  marginTop: 20,
  padding: 16,
  border: "1px solid #ddd",
  borderRadius: 12,
  background: "rgba(255,255,255,0.06)",
};

const codeStyle = {
  fontWeight: "bold",
  margin: "10px 0",
};

const tableStyle = {
  width: "100%",
  borderCollapse: "collapse",
};

const errorStyle = {
  marginTop: 16,
  color: "red",
};