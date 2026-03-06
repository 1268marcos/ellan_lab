import React, { useEffect, useMemo, useState } from "react";

const btn = {
  padding: "10px 12px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.18)",
  background: "#7a5f1f",
  color: "white",
  cursor: "pointer",
  fontWeight: 800,
};

const input = {
  width: "100%",
  padding: "10px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.06)",
  color: "white",
  outline: "none",
};

const label = {
  fontSize: 12,
  opacity: 0.9,
  display: "grid",
  gap: 6,
};

export default function ManualPickupPanel({
  region = "PT",
  apiBase = "/api/op",
  onRedeemed,
}) {
  const [manualCode, setManualCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState("");
  const [error, setError] = useState("");

  const endpoint = useMemo(() => `${apiBase}/totem/pickups/redeem-manual`, [apiBase]);

  useEffect(() => {
    setManualCode("");
    setResp("");
    setError("");
  }, [region]);

  async function redeemManualCode() {
    const cleanCode = String(manualCode).trim();

    if (!cleanCode) {
      setError("Digite o código manual.");
      setResp("");
      return;
    }

    setLoading(true);
    setError("");
    setResp("");

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region,
          manual_code: cleanCode,
        }),
      });

      const text = await res.text();

      if (!res.ok) {
        setError(`HTTP ${res.status}: ${text}`);
        return;
      }

      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { raw: text };
      }

      setResp(JSON.stringify(data, null, 2));
      setManualCode("");

      if (onRedeemed) {
        onRedeemed(data);
      }
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.12)",
        background: "rgba(0,0,0,0.18)",
        padding: 12,
        display: "grid",
        gap: 10,
      }}
    >
      <div style={{ fontWeight: 800 }}>Retirada por código manual</div>

      <div style={{ fontSize: 12, opacity: 0.75 }}>
        Endpoint: <code>{endpoint}</code>
      </div>

      <div style={{ fontSize: 12, opacity: 0.75 }}>
        Região atual: <b>{region}</b>
      </div>

      <label style={label}>
        Código manual
        <input
          value={manualCode}
          onChange={(e) => setManualCode(e.target.value)}
          placeholder="ex.: 482931"
          style={input}
          maxLength={8}
        />
      </label>

      <button
        onClick={redeemManualCode}
        disabled={loading}
        style={{
          ...btn,
          background: loading ? "rgba(255,255,255,0.08)" : "#2d8a4a",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "Validando..." : "Retirar com código"}
      </button>

      <div style={{ fontSize: 11, opacity: 0.7 }}>
        Use este painel para simular o totem sem precisar de leitor de QR.
      </div>

      {error ? (
        <pre
          style={{
            margin: 0,
            padding: 10,
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "#2b1d1d",
            color: "#ffb4b4",
            overflow: "auto",
            maxHeight: 180,
            fontSize: 11,
          }}
        >
          {error}
        </pre>
      ) : null}

      {resp ? (
        <pre
          style={{
            margin: 0,
            padding: 10,
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "#0b0d10",
            color: "white",
            overflow: "auto",
            maxHeight: 220,
            fontSize: 11,
          }}
        >
          {resp}
        </pre>
      ) : null}
    </div>
  );
}