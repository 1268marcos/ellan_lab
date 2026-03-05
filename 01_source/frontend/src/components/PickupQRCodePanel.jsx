import React, { useEffect, useMemo, useRef, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

/**
 * === PICKUP QR ROTATIVO (frontend mock / preview) ===
 * - Token base: válido por 2h
 * - QR rotativo: a cada 10 min (ctr)
 * - "sig" aqui é apenas um placeholder (não é segurança real no frontend)
 *   Quando o backend estiver pronto:
 *     - token_id vem do servidor
 *     - sig vem do servidor (HMAC/assinatura)
 *     - validação acontece no backend/locker
 */

const PICKUP_WINDOW_SEC_DEFAULT = 2 * 60 * 60; // 2h
const QR_ROTATE_SEC_DEFAULT = 10 * 60; // 10 min

function nowSec() {
  return Math.floor(Date.now() / 1000);
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function formatRemaining(sec) {
  sec = Math.max(0, sec);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h > 0) return `${h}:${pad2(m)}:${pad2(s)}`;
  return `${m}:${pad2(s)}`;
}

function randomId(prefix = "") {
  // compat: crypto.randomUUID em navegadores modernos; fallback simples
  const id = (globalThis.crypto?.randomUUID?.() || `id_${Math.random().toString(16).slice(2)}${Date.now()}`).replaceAll("-", "");
  return prefix ? `${prefix}${id}` : id;
}

function fakeSig({ order_id, token_id, ctr, exp }) {
  // Placeholder: NÃO é criptografia real.
  // Serve apenas para manter o shape do payload.
  const raw = `${order_id}|${token_id}|${ctr}|${exp}`;
  let hash = 0;
  for (let i = 0; i < raw.length; i++) hash = (hash * 31 + raw.charCodeAt(i)) >>> 0;
  return `sig_${hash.toString(16)}`;
}

export default function PickupQRCodePanel({
  region = "PT",
  selectedSlot = 1,
  rotateSec = QR_ROTATE_SEC_DEFAULT,
  windowSec = PICKUP_WINDOW_SEC_DEFAULT,
}) {
  const [orderId, setOrderId] = useState("");
  const [tokenId, setTokenId] = useState("");
  const [issuedAt, setIssuedAt] = useState(null); // epoch sec
  const [expiresAt, setExpiresAt] = useState(null); // epoch sec

  const [tick, setTick] = useState(0); // força re-render a cada 1s

  // aceleração de teste (opcional)
  const [testMode, setTestMode] = useState(false);
  const [testRotateSec, setTestRotateSec] = useState(10); // só usado no testMode

  const effectiveRotateSec = testMode ? Math.max(3, Number(testRotateSec) || 10) : rotateSec;

  // inicia com valores “mock” para facilitar
  useEffect(() => {
    if (!orderId) setOrderId(`ord_${region}_${randomId("").slice(0, 10)}`);
    if (!tokenId) setTokenId(`tok_${randomId("").slice(0, 14)}`);
    if (!issuedAt) {
      const n = nowSec();
      setIssuedAt(n);
      setExpiresAt(n + windowSec);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // relógio
  useEffect(() => {
    const t = setInterval(() => setTick((x) => x + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const n = nowSec();

  const isActive = issuedAt && expiresAt && n < expiresAt;

  // ctr (janela de 10 min)
  const ctr = useMemo(() => {
    if (!issuedAt) return 0;
    return Math.floor((n - issuedAt) / effectiveRotateSec);
  }, [issuedAt, n, effectiveRotateSec]);

  const secondsToNextRotate = useMemo(() => {
    if (!issuedAt) return 0;
    const elapsed = n - issuedAt;
    const into = elapsed % effectiveRotateSec;
    return effectiveRotateSec - into;
  }, [issuedAt, n, effectiveRotateSec]);

  const secondsToExpire = useMemo(() => {
    if (!expiresAt) return 0;
    return expiresAt - n;
  }, [expiresAt, n]);

  const payloadObj = useMemo(() => {
    if (!orderId || !tokenId || !issuedAt || !expiresAt) return null;

    const exp = expiresAt;
    const obj = {
      v: 1,
      region,
      order_id: orderId,
      token_id: tokenId,
      slot: Number(selectedSlot),
      ctr,
      exp, // epoch sec
      sig: fakeSig({ order_id: orderId, token_id: tokenId, ctr, exp }),
    };
    return obj;
  }, [region, orderId, tokenId, issuedAt, expiresAt, selectedSlot, ctr]);

  const qrValue = useMemo(() => {
    if (!payloadObj) return "";
    return JSON.stringify(payloadObj);
  }, [payloadObj]);

  function regenerate() {
    const n = nowSec();
    setOrderId(`ord_${region}_${randomId("").slice(0, 10)}`);
    setTokenId(`tok_${randomId("").slice(0, 14)}`);
    setIssuedAt(n);
    setExpiresAt(n + windowSec);
  }

  function resetSameOrderNewToken() {
    const n = nowSec();
    setTokenId(`tok_${randomId("").slice(0, 14)}`);
    setIssuedAt(n);
    setExpiresAt(n + windowSec);
  }

  const statusBadge = isActive
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
        <div style={{ fontWeight: 800 }}>Retirada (QR rotativo)</div>
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
        Token válido por <b>2h</b>; QR rotaciona a cada <b>10 min</b> (ctr).
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
            <div style={{ fontSize: 12, opacity: 0.7 }}>Gerando QR…</div>
          )}
          <div style={{ marginTop: 8, fontSize: 11, opacity: 0.75 }}>
            ctr: <b>{ctr}</b>
          </div>
        </div>

        <div style={{ display: "grid", gap: 8 }}>
          <label style={label}>
            order_id
            <input value={orderId} onChange={(e) => setOrderId(e.target.value)} style={input} />
          </label>

          <label style={label}>
            token_id
            <input value={tokenId} onChange={(e) => setTokenId(e.target.value)} style={input} />
          </label>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div style={{ fontSize: 12, opacity: 0.9 }}>
              Próxima rotação em: <b>{formatRemaining(secondsToNextRotate)}</b>
            </div>
            <div style={{ fontSize: 12, opacity: 0.9 }}>
              Expira em: <b>{formatRemaining(secondsToExpire)}</b>
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button onClick={regenerate} style={btn}>
              Novo pedido + token
            </button>
            <button onClick={resetSameOrderNewToken} style={btn}>
              Mesmo pedido, novo token
            </button>
          </div>

          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, opacity: 0.9 }}>
              <input type="checkbox" checked={testMode} onChange={(e) => setTestMode(e.target.checked)} />
              Test mode (rotaciona rápido)
            </label>

            {testMode ? (
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, opacity: 0.9 }}>
                rotate_sec:
                <input
                  type="number"
                  min="3"
                  value={testRotateSec}
                  onChange={(e) => setTestRotateSec(e.target.value)}
                  style={{ ...input, width: 80, padding: "8px 8px" }}
                />
              </label>
            ) : null}
          </div>

          <details style={{ marginTop: 2 }}>
            <summary style={{ cursor: "pointer", fontSize: 12, opacity: 0.85 }}>Ver payload do QR (JSON)</summary>
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
              {payloadObj ? JSON.stringify(payloadObj, null, 2) : "—"}
            </pre>
          </details>

          <div style={{ fontSize: 11, opacity: 0.65, lineHeight: 1.3 }}>
            Nota: aqui a assinatura <code>sig</code> é apenas um placeholder. Na integração real, o backend gera e valida
            (HMAC/assinatura) e o locker valida online/offline conforme política.
          </div>
        </div>
      </div>
    </div>
  );
}

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