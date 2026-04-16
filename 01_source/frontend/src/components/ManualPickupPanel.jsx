// 01_source/frontend/src/components/ManualPickupPanel.jsx
// 16/04/2026 - versão FINAL limpa

import React, { useEffect, useMemo, useRef, useState } from "react";
import PickupCodeVirtualKeyboard from "./PickupCodeVirtualKeyboard.jsx";

const panelStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(0,0,0,0.18)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const btnStyle = {
  padding: "10px 12px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.18)",
  background: "#2d8a4a",
  color: "white",
  cursor: "pointer",
  fontWeight: 800,
};

const inputStyle = {
  width: "100%",
  padding: "10px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.06)",
  color: "white",
};

const toastStyle = {
  padding: 10,
  borderRadius: 12,
  border: "1px solid rgba(245, 158, 11, 0.35)",
  background: "rgba(245, 158, 11, 0.16)",
  color: "#fde68a",
  fontSize: 12,
  fontWeight: 700,
};

export default function ManualPickupPanel({
  region = "PT",
  lockerId = "",
  apiBase = "/api/op",
  onRedeemed,
  pickupCodeLength = 6,
}) {
  const [keyboardOpen, setKeyboardOpen] = useState(false);
  const [manualCode, setManualCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState("");
  const [error, setError] = useState("");

  const [toastMessage, setToastMessage] = useState("");
  const toastTimerRef = useRef(null);

  const endpoint = useMemo(() => {
    return `${apiBase}/totem/pickups/redeem-manual`;
  }, [apiBase]);

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, []);

  function showToast(message) {
    setToastMessage(message);

    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
    }

    toastTimerRef.current = setTimeout(() => {
      setToastMessage("");
    }, 2500);
  }

  useEffect(() => {
    setManualCode("");
    setResp("");
    setError("");
  }, [region, lockerId]);

  async function redeemManualCode() {
    const cleanCode = manualCode.trim();

    if (!lockerId) {
      setError("Locker não selecionado.");
      return;
    }

    if (!cleanCode) {
      setError("Digite o código manual.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region,
          locker_id: lockerId,
          manual_code: cleanCode,
        }),
      });

      const data = await res.json();

      // ✅ DEPOIS — garante sempre string
      if (!res.ok) {
        const detail = data?.detail;
        const message =
          typeof detail === "string"
            ? detail
            : detail
            ? JSON.stringify(detail, null, 2)
            : "Erro ao validar código.";
        setError(message);
        return;
      }

      setResp(JSON.stringify(data, null, 2));
      setManualCode("");

      onRedeemed?.(data);
    } catch (e) {
      setError(e?.message ? String(e.message) : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={panelStyle}>
      <div style={{ fontWeight: 800 }}>Retirada por código manual</div>

      <button onClick={() => setKeyboardOpen(true)} style={inputStyle}>
        {manualCode || "Digite o código"}
      </button>

      <button
        onClick={redeemManualCode}
        disabled={loading || !lockerId}
        style={btnStyle}
      >
        {loading ? "Validando..." : "Retirar com código"}
      </button>

      {toastMessage && <div style={toastStyle}>{toastMessage}</div>}

      <PickupCodeVirtualKeyboard
        isOpen={keyboardOpen}
        value={manualCode}
        onChange={setManualCode}
        onClose={() => setKeyboardOpen(false)}
        onDiscardIncompleteCode={({ message, enteredLength, expectedLength }) => {
          showToast(
            message ||
              `Código incompleto descartado (${enteredLength}/${expectedLength})`
          );
        }}
        codeLength={pickupCodeLength}
      />

      {error && <pre>{error}</pre>}
      {resp && <pre>{resp}</pre>}
    </div>
  );
}