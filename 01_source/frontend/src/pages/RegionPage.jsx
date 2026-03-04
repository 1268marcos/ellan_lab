import React, { useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";

export default function RegionPage({ region }) {
  const [payment, setPayment] = useState("PIX");
  const [porta, setPorta] = useState(1);
  const [valor, setValor] = useState(100);
  const [resp, setResp] = useState(null);
  const [err, setErr] = useState(null);

  const url = useMemo(() => `${API_BASE}/gateway/pagamento`, []);

  async function sendPayment() {
    setErr(null);
    setResp(null);

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Só adicione se o backend exigir token (caso do /internal, não do gateway normal):
          // "X-Internal-Token": import.meta.env.VITE_INTERNAL_TOKEN || "",
        },
        body: JSON.stringify({
          regiao: region,
          metodo: payment,
          valor: Number(valor),
          porta: Number(porta), // <- isso evita o erro "Field required"
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }
      setResp(data);
    } catch (e) {
      setErr(String(e?.message || e));
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 720, margin: "0 auto", fontFamily: "system-ui" }}>
      <h1>Pagamento / Região {region}</h1>

      <div style={{ display: "grid", gap: 12, marginTop: 16 }}>
        <label>
          Método:
          <select value={payment} onChange={(e) => setPayment(e.target.value)} style={{ marginLeft: 8 }}>
            <option value="PIX">PIX</option>
            <option value="CARTAO">CARTÃO</option>
            <option value="MBWAY">MBWAY</option>
            <option value="NFC">Proximidade</option>
          </select>
        </label>

        <label>
          Porta (slot):
          <input
            type="number"
            min="1"
            max="24"
            value={porta}
            onChange={(e) => setPorta(e.target.value)}
            style={{ marginLeft: 8, width: 120 }}
          />
        </label>

        <label>
          Valor:
          <input
            type="number"
            min="1"
            step="1"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            style={{ marginLeft: 8, width: 120 }}
          />
        </label>

        <button onClick={sendPayment} style={{ padding: "10px 14px", cursor: "pointer" }}>
          Enviar pagamento
        </button>

        <div style={{ fontSize: 12, opacity: 0.75 }}>
          Gateway: <code>{url}</code>
        </div>

        {err && (
          <pre style={{ background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 8, overflow: "auto" }}>
            {err}
          </pre>
        )}

        {resp && (
          <pre style={{ background: "#111", color: "#b7ffb7", padding: 12, borderRadius: 8, overflow: "auto" }}>
            {JSON.stringify(resp, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}