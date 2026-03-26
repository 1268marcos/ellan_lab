// 01_source/frontend/src/components/PickupQRCodePanel.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

/**
 * Pickup QR Panel
 * - Busca QR rotativo do backend:
 *   POST /me/pickups/{pickupId}/qr  -> { qr: {...}, refresh_in_sec }
 * - Mostra contagem regressiva e validade total (exp)
 * - Exibe manual_code (fallback sem QR) via endpoint:
 *   POST /orders/{order_id}/pickup-token -> { manual_code, expires_at, ... }
 *
 * Observação:
 * - pickupId aqui deve ser o pickup_id real
 * - o fluxo atual de redeem manual fica em ManualPickupPanel
 * - este componente não faz redeem; ele apenas gera/mostra QR e código manual
 */

function nowSec() {
  return Math.floor(Date.now() / 1000);
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function formatRemaining(sec) {
  sec = Math.max(0, Math.floor(sec));
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h > 0) return `${h}:${pad2(m)}:${pad2(s)}`;
  return `${m}:${pad2(s)}`;
}

function formatTimeFromEpoch(epochSec) {
  try {
    const d = new Date(epochSec * 1000);
    return d.toLocaleTimeString();
  } catch {
    return "-";
  }
}

const btn = {
  padding: "9px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.18)",
  background: "rgba(255,255,255,0.06)",
  color: "white",
  cursor: "pointer",
  fontSize: 12,
  fontWeight: 800,
};

const label = { fontSize: 12, opacity: 0.9, display: "grid", gap: 6 };

const input = {
  width: "100%",
  padding: "10px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.06)",
  color: "white",
  outline: "none",
};

export default function PickupQRCodePanel({
  region = "PT",
  lockerId = "",
  pickupId = "",
  orderId = "",
  apiBase = "http://localhost:8003",
}) {
  const [qrResp, setQrResp] = useState(null); // { qr, refresh_in_sec }
  const [qrError, setQrError] = useState("");
  const [loadingQr, setLoadingQr] = useState(false);

  const [manualCode, setManualCode] = useState("");
  const [manualCodeError, setManualCodeError] = useState("");
  const [loadingManual, setLoadingManual] = useState(false);

  const refreshTimerRef = useRef(null);

  const [testMode, setTestMode] = useState(false);

  useEffect(() => {
    if (!pickupId) return;
    const storageKey = `ellan_manual_code_${lockerId || "NO_LOCKER"}_${pickupId}`;
    const saved = localStorage.getItem(storageKey);
    if (saved) setManualCode(saved);
  }, [pickupId, lockerId]);

  useEffect(() => {
    if (!pickupId) return;
    const storageKey = `ellan_manual_code_${lockerId || "NO_LOCKER"}_${pickupId}`;
    if (manualCode) {
      localStorage.setItem(storageKey, manualCode);
    } else {
      localStorage.removeItem(storageKey);
    }
  }, [pickupId, lockerId, manualCode]);

  const qrEndpoint = useMemo(() => {
    if (!pickupId) return null;
    return `${apiBase}/me/pickups/${encodeURIComponent(pickupId)}/qr`;
  }, [apiBase, pickupId]);

  const legacyManualEndpoint = useMemo(() => {
    const effectiveOrderId = orderId || pickupId;
    if (!effectiveOrderId) return null;
    return `${apiBase}/orders/${encodeURIComponent(effectiveOrderId)}/pickup-token`;
  }, [apiBase, orderId, pickupId]);

  async function fetchQrOnce() {
    if (!qrEndpoint) return;
    setLoadingQr(true);
    setQrError("");

    try {
      const res = await fetch(qrEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const text = await res.text();
      if (!res.ok) {
        setQrError(`HTTP ${res.status}: ${text}`);
        setQrResp(null);
        return;
      }
      const data = JSON.parse(text);
      setQrResp(data);
    } catch (e) {
      setQrError(String(e?.message || e));
      setQrResp(null);
    } finally {
      setLoadingQr(false);
    }
  }

  useEffect(() => {
    if (!pickupId) return;

    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }

    fetchQrOnce();

    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pickupId, qrEndpoint]);

  useEffect(() => {
    if (!qrResp?.refresh_in_sec) return;

    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }

    const margin = 1;
    const waitSec = testMode ? 5 : Math.max(1, Number(qrResp.refresh_in_sec) - margin);

    refreshTimerRef.current = setTimeout(() => {
      fetchQrOnce();
    }, waitSec * 1000);

    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qrResp, testMode]);

  async function fetchManualCode() {
    if (!legacyManualEndpoint) return;
    setLoadingManual(true);
    setManualCodeError("");

    try {
      const res = await fetch(legacyManualEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const text = await res.text();
      if (!res.ok) {
        setManualCodeError(`HTTP ${res.status}: ${text}`);
        return;
      }
      const data = JSON.parse(text);
      const code = data?.manual_code || "";
      if (!code) {
        setManualCodeError("Resposta não trouxe manual_code");
        return;
      }
      setManualCode(code);
    } catch (e) {
      setManualCodeError(String(e?.message || e));
    } finally {
      setLoadingManual(false);
    }
  }

  const qrPayloadObj = qrResp?.qr || null;
  const qrValue = qrPayloadObj ? JSON.stringify(qrPayloadObj) : "";

  const qrVersion = qrPayloadObj?.v ?? "-";
  const qrLockerId = qrPayloadObj?.locker_id || "-";
  const qrRegion = qrPayloadObj?.region || "-";

  const expEpoch = qrPayloadObj?.exp ? Number(qrPayloadObj.exp) : null;
  const secsToExpire = expEpoch ? expEpoch - nowSec() : null;

  const refreshIn = qrResp?.refresh_in_sec != null ? Number(qrResp.refresh_in_sec) : null;

  const statusBadge =
    expEpoch && secsToExpire != null && secsToExpire > 0
      ? { text: "ATIVO", bg: "#1f7a3f" }
      : { text: "EXPIRADO", bg: "#b3261e" };

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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
        <div style={{ fontWeight: 800 }}>Retirada online (QR + código manual)</div>
        <span
          style={{
            padding: "4px 10px",
            borderRadius: 999,
            background: statusBadge.bg,
            color: "white",
            fontSize: 12,
            fontWeight: 900,
          }}
        >
          {statusBadge.text}
        </span>
      </div>

      <div style={{ fontSize: 12, opacity: 0.8 }}>
        {pickupId ? (
          <>
            Pickup ID: <b>{pickupId}</b> • Região: <b>{region}</b> • Locker: <b>{lockerId || "-"}</b>
          </>
        ) : (
          <span style={{ color: "#ffb4b4" }}>
            ⚠️ Selecione um pickup_id válido para gerar QR.
          </span>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 12, alignItems: "start" }}>
        <div
          style={{
            padding: 10,
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "#0b0d10",
            display: "grid",
            placeItems: "center",
          }}
        >
          {qrValue ? (
            <QRCodeCanvas value={qrValue} size={120} includeMargin={true} />
          ) : (
            <div style={{ fontSize: 12, opacity: 0.7 }}>
              {loadingQr ? "Carregando QR…" : "Sem QR (ainda)"}
            </div>
          )}

          <div style={{ marginTop: 8, fontSize: 11, opacity: 0.85 }}>
            versão: <b>{qrVersion}</b>
          </div>

          <div style={{ marginTop: 4, fontSize: 11, opacity: 0.85 }}>
            ctr: <b>{qrPayloadObj?.ctr ?? "-"}</b>
          </div>

          <button onClick={fetchQrOnce} style={{ ...btn, marginTop: 8 }} disabled={!pickupId || loadingQr}>
            {loadingQr ? "Atualizando…" : "Atualizar QR"}
          </button>
        </div>

        <div style={{ display: "grid", gap: 10 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div style={{ fontSize: 12, opacity: 0.9 }}>
              Atualiza em: <b>{refreshIn == null ? "-" : formatRemaining(refreshIn)}</b>
            </div>
            <div style={{ fontSize: 12, opacity: 0.9 }}>
              Válido até: <b>{expEpoch ? formatTimeFromEpoch(expEpoch) : "-"}</b>
            </div>
          </div>

          {secsToExpire != null ? (
            <div style={{ fontSize: 12, opacity: 0.9 }}>
              Expira em: <b>{formatRemaining(secsToExpire)}</b>
            </div>
          ) : null}

          <div
            style={{
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.04)",
              padding: 10,
              display: "grid",
              gap: 6,
              fontSize: 12,
            }}
          >
            <div><b>versão do QR:</b> {qrVersion}</div>
            <div><b>locker_id no QR:</b> {qrLockerId}</div>
            <div><b>region no QR:</b> {qrRegion}</div>
            <div><b>locker selecionado na tela:</b> {lockerId || "-"}</div>
            <div><b>order_id:</b> {orderId || "-"}</div>
          </div>

          {qrError ? (
            <pre
              style={{
                margin: 0,
                padding: 10,
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.12)",
                background: "#2b1d1d",
                color: "#ffb4b4",
                overflow: "auto",
                maxHeight: 160,
                fontSize: 11,
              }}
            >
              {qrError}
            </pre>
          ) : null}

          <div
            style={{
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.04)",
              padding: 10,
              display: "grid",
              gap: 8,
            }}
          >
            <div style={{ fontWeight: 800, fontSize: 12 }}>Código manual (fallback sem QR)</div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 10, alignItems: "end" }}>
              <label style={label}>
                manual_code
                <input
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value)}
                  placeholder="ex.: 482931"
                  style={input}
                />
              </label>

              <button onClick={fetchManualCode} style={btn} disabled={!pickupId || loadingManual}>
                {loadingManual ? "Gerando…" : "Gerar/Atualizar"}
              </button>
            </div>

            <div style={{ fontSize: 11, opacity: 0.7 }}>
              Se estiver sem bateria/QR, toque em <b>“Digitar código”</b> no totem e informe este código.
            </div>

            {manualCodeError ? (
              <pre
                style={{
                  margin: 0,
                  padding: 10,
                  borderRadius: 12,
                  border: "1px solid rgba(255,255,255,0.12)",
                  background: "#2b1d1d",
                  color: "#ffb4b4",
                  overflow: "auto",
                  maxHeight: 120,
                  fontSize: 11,
                }}
              >
                {manualCodeError}
              </pre>
            ) : null}
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, opacity: 0.9 }}>
            <input type="checkbox" checked={testMode} onChange={(e) => setTestMode(e.target.checked)} />
            Test mode (auto refresh rápido)
          </label>

          <details>
            <summary style={{ cursor: "pointer", fontSize: 12, opacity: 0.85 }}>
              Ver payload do QR (JSON)
            </summary>
            <pre
              style={{
                marginTop: 8,
                marginBottom: 0,
                padding: 10,
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.12)",
                background: "#0b0d10",
                color: "white",
                overflow: "auto",
                maxHeight: 180,
                fontSize: 11,
              }}
            >
              {qrPayloadObj ? JSON.stringify(qrPayloadObj, null, 2) : "—"}
            </pre>
          </details>
        </div>
      </div>
    </div>
  );
}