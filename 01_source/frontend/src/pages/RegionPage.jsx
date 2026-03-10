import React, { useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const initialIdentify = {
  phone: "",
  email: "",
};

export default function RegionPage({ region, mode = "kiosk" }) {
  const [paymentMethod, setPaymentMethod] = useState(region === "PT" ? "MBWAY" : "PIX");
  const [skuId, setSkuId] = useState("BOLO_LARANJA");
  const [totemId, setTotemId] = useState(region === "PT" ? "CACIFO-PT-001" : "CACIFO-SP-001");

  const [createResp, setCreateResp] = useState(null);
  const [paymentResp, setPaymentResp] = useState(null);
  const [identifyResp, setIdentifyResp] = useState(null);

  const [identifyForm, setIdentifyForm] = useState(initialIdentify);

  const [loadingCreate, setLoadingCreate] = useState(false);
  const [loadingPayment, setLoadingPayment] = useState(false);
  const [loadingIdentify, setLoadingIdentify] = useState(false);

  const [err, setErr] = useState(null);

  const createUrl = useMemo(() => `${API_BASE}/kiosk/orders`, []);
  const identifyUrl = useMemo(() => `${API_BASE}/kiosk/identify`, []);

  const currentOrderId = createResp?.order_id || null;

  async function createKioskOrder() {
    setErr(null);
    setCreateResp(null);
    setPaymentResp(null);
    setIdentifyResp(null);

    setLoadingCreate(true);
    try {
      const res = await fetch(createUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          region,
          totem_id: totemId,
          sku_id: skuId,
          payment_method: paymentMethod,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }

      setCreateResp(data);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingCreate(false);
    }
  }

  async function approveKioskPayment() {
    if (!currentOrderId) {
      setErr("Crie primeiro um pedido KIOSK.");
      return;
    }

    setErr(null);
    setPaymentResp(null);

    setLoadingPayment(true);
    try {
      const url = `${API_BASE}/kiosk/orders/${currentOrderId}/payment-approved`;

      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }

      setPaymentResp(data);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingPayment(false);
    }
  }

  async function identifyCustomer() {
    if (!currentOrderId) {
      setErr("Crie primeiro um pedido KIOSK.");
      return;
    }

    setErr(null);
    setIdentifyResp(null);

    setLoadingIdentify(true);
    try {
      const res = await fetch(identifyUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          order_id: currentOrderId,
          phone: identifyForm.phone || null,
          email: identifyForm.email || null,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }

      setIdentifyResp(data);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingIdentify(false);
    }
  }

  return (
    <div style={pageStyle}>
      <div style={headerCardStyle}>
        <h1 style={{ margin: 0 }}>
          Simulador KIOSK — {region}
        </h1>
        <div style={subtleStyle}>
          Fluxo separado do dashboard online. Nesta tela você cria pedido KIOSK, aprova pagamento e registra identificação opcional.
        </div>
      </div>

      <div style={gridStyle}>
        <section style={cardStyle}>
          <h2 style={h2Style}>1. Criar pedido KIOSK</h2>

          <div style={fieldGridStyle}>
            <label style={labelStyle}>
              Região
              <input value={region} disabled style={inputStyleDisabled} />
            </label>

            <label style={labelStyle}>
              Totem ID
              <input
                value={totemId}
                onChange={(e) => setTotemId(e.target.value)}
                style={inputStyle}
              />
            </label>

            <label style={labelStyle}>
              SKU
              <input
                value={skuId}
                onChange={(e) => setSkuId(e.target.value)}
                style={inputStyle}
              />
            </label>

            <label style={labelStyle}>
              Método de pagamento
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                style={inputStyle}
              >
                <option value="PIX">PIX</option>
                <option value="CARTAO">CARTÃO</option>
                <option value="MBWAY">MBWAY</option>
                <option value="NFC">NFC</option>
              </select>
            </label>
          </div>

          <button onClick={createKioskOrder} disabled={loadingCreate} style={buttonPrimaryStyle}>
            {loadingCreate ? "Criando..." : "Criar pedido KIOSK"}
          </button>

          {createResp && (
            <div style={okBoxStyle}>
              <strong>Pedido criado com sucesso</strong>
              <div style={summaryListStyle}>
                <div><b>order_id:</b> {createResp.order_id}</div>
                <div><b>allocation_id:</b> {createResp.allocation_id}</div>
                <div><b>slot:</b> {createResp.slot}</div>
                <div><b>amount_cents:</b> {createResp.amount_cents}</div>
                <div><b>payment_method:</b> {createResp.payment_method}</div>
                <div><b>ttl_sec:</b> {createResp.ttl_sec}</div>
                <div><b>status:</b> {createResp.status}</div>
              </div>
              <div style={messageStyle}>{createResp.message}</div>
            </div>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={h2Style}>2. Aprovar pagamento KIOSK</h2>

          <div style={subtleStyle}>
            Usa o endpoint operacional do KIOSK para commitar a allocation, ligar luz, abrir gaveta e marcar o pedido como <code>DISPENSED</code>.
          </div>

          <div style={{ marginTop: 12 }}>
            <div><b>Pedido atual:</b> {currentOrderId || "nenhum"}</div>
          </div>

          <button
            onClick={approveKioskPayment}
            disabled={loadingPayment || !currentOrderId}
            style={buttonPrimaryStyle}
          >
            {loadingPayment ? "Aprovando..." : "Aprovar pagamento"}
          </button>

          {paymentResp && (
            <div style={okBoxStyle}>
              <strong>Pagamento aprovado</strong>
              <div style={summaryListStyle}>
                <div><b>order_id:</b> {paymentResp.order_id}</div>
                <div><b>allocation_id:</b> {paymentResp.allocation_id}</div>
                <div><b>slot:</b> {paymentResp.slot}</div>
                <div><b>status:</b> {paymentResp.status}</div>
                <div><b>payment_method:</b> {paymentResp.payment_method || "-"}</div>
              </div>
              <div style={messageStyle}>{paymentResp.message}</div>
            </div>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={h2Style}>3. Identificação opcional</h2>

          <div style={fieldGridStyle}>
            <label style={labelStyle}>
              Telefone
              <input
                value={identifyForm.phone}
                onChange={(e) =>
                  setIdentifyForm((prev) => ({ ...prev, phone: e.target.value }))
                }
                style={inputStyle}
                placeholder="+351912345678"
              />
            </label>

            <label style={labelStyle}>
              Email
              <input
                value={identifyForm.email}
                onChange={(e) =>
                  setIdentifyForm((prev) => ({ ...prev, email: e.target.value }))
                }
                style={inputStyle}
                placeholder="cliente@exemplo.com"
              />
            </label>
          </div>

          <button
            onClick={identifyCustomer}
            disabled={loadingIdentify || !currentOrderId}
            style={buttonSecondaryStyle}
          >
            {loadingIdentify ? "Registrando..." : "Registrar identificação"}
          </button>

          {identifyResp && (
            <div style={okBoxStyle}>
              <strong>Identificação registrada</strong>
              <div style={messageStyle}>{identifyResp.message}</div>
            </div>
          )}
        </section>
      </div>

      <section style={cardStyle}>
        <h2 style={h2Style}>Configuração desta tela</h2>
        <div style={summaryListStyle}>
          <div><b>mode:</b> {mode}</div>
          <div><b>API_BASE:</b> {API_BASE}</div>
          <div><b>createUrl:</b> {createUrl}</div>
          <div><b>identifyUrl:</b> {identifyUrl}</div>
        </div>
      </section>

      {err && (
        <pre style={errorBoxStyle}>
          {err}
        </pre>
      )}
    </div>
  );
}

const pageStyle = {
  padding: 24,
  maxWidth: 1100,
  margin: "0 auto",
  fontFamily: "system-ui, sans-serif",
  color: "#f5f7fa",
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
  gap: 16,
  marginTop: 16,
  marginBottom: 16,
};

const cardStyle = {
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxShadow: "0 8px 24px rgba(0,0,0,0.22)",
};

const headerCardStyle = {
  ...cardStyle,
  marginBottom: 16,
};

const h2Style = {
  marginTop: 0,
  marginBottom: 12,
  fontSize: 18,
};

const fieldGridStyle = {
  display: "grid",
  gap: 12,
  marginBottom: 16,
};

const labelStyle = {
  display: "grid",
  gap: 6,
  fontSize: 14,
};

const inputStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const inputStyleDisabled = {
  ...inputStyle,
  opacity: 0.7,
};

const buttonPrimaryStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#1f7a3f",
  color: "white",
  fontWeight: 600,
};

const buttonSecondaryStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#1b5883",
  color: "white",
  fontWeight: 600,
};

const okBoxStyle = {
  marginTop: 16,
  padding: 12,
  borderRadius: 12,
  background: "rgba(31,122,63,0.15)",
  border: "1px solid rgba(31,122,63,0.35)",
};

const errorBoxStyle = {
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};

const subtleStyle = {
  fontSize: 13,
  opacity: 0.82,
  lineHeight: 1.45,
};

const summaryListStyle = {
  display: "grid",
  gap: 6,
  marginTop: 10,
  fontSize: 14,
};

const messageStyle = {
  marginTop: 10,
  fontSize: 14,
};