// 01_source/frontend/src/features/locker-dashboard/components/PaymentPanel.jsx

import React from "react";

function paymentMethodLabel(method) {
  const labels = {
    PIX: "PIX",
    CARTAO: "Cartão",
    MBWAY: "MB WAY",
    MULTIBANCO_REFERENCE: "Referência Multibanco",
    NFC: "NFC",
    APPLE_PAY: "Apple Pay",
    GOOGLE_PAY: "Google Pay",
    MERCADO_PAGO_WALLET: "Mercado Pago Wallet",
  };

  return labels[method] || method || "-";
}

export default function PaymentPanel({
  availablePaymentMethods,
  payMethod,
  setPayMethod,
  payValue,
  setPayValue,
  cardType,
  setCardType,
  customerPhone,
  setCustomerPhone,
  walletProvider,
  isWalletMethodSelected,
  orderLoading,
  payLoading,
  payResp,
  onCreateOnlineOrder,
  onSimulatePayment,
  onConfirmPendingCustomerAction,
  pendingPaymentContext,
  currentOrder,
}) {
  return (
    <section
      style={{
        background: "rgba(255,255,255,0.08)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 16,
        padding: 16,
        display: "grid",
        gap: 12,
      }}
    >
      <div>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Pagamento Operacional</div>
        <div style={{ fontSize: 12, opacity: 0.72 }}>
          Criação do pedido e simulação/confirmação do pagamento.
        </div>
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        <label style={{ display: "grid", gap: 6, fontSize: 13 }}>
          <span style={{ fontWeight: 700 }}>Método de pagamento</span>
          <select
            value={payMethod}
            onChange={(e) => setPayMethod(e.target.value)}
            style={{
              width: "100%",
              padding: 12,
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.18)",
              background: "rgba(255,255,255,0.08)",
              color: "white",
            }}
          >
            {(availablePaymentMethods || []).map((method) => (
              <option key={method} value={method}>
                {paymentMethodLabel(method)}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "grid", gap: 6, fontSize: 13 }}>
          <span style={{ fontWeight: 700 }}>Valor visual</span>
          <input
            value={payValue}
            onChange={(e) => setPayValue(e.target.value)}
            type="number"
            step="0.01"
            style={{
              width: "100%",
              padding: 12,
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.18)",
              background: "rgba(255,255,255,0.08)",
              color: "white",
            }}
          />
        </label>

        {payMethod === "CARTAO" ? (
          <label style={{ display: "grid", gap: 6, fontSize: 13 }}>
            <span style={{ fontWeight: 700 }}>Tipo do cartão</span>
            <select
              value={cardType}
              onChange={(e) => setCardType(e.target.value)}
              style={{
                width: "100%",
                padding: 12,
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.18)",
                background: "rgba(255,255,255,0.08)",
                color: "white",
              }}
            >
              <option value="creditCard">Crédito</option>
              <option value="debitCard">Débito</option>
            </select>
          </label>
        ) : null}

        {payMethod === "MBWAY" ? (
          <label style={{ display: "grid", gap: 6, fontSize: 13 }}>
            <span style={{ fontWeight: 700 }}>Telefone MB WAY</span>
            <input
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              placeholder="+351912345678"
              style={{
                width: "100%",
                padding: 12,
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.18)",
                background: "rgba(255,255,255,0.08)",
                color: "white",
              }}
            />
          </label>
        ) : null}

        {isWalletMethodSelected ? (
          <div
            style={{
              fontSize: 12,
              borderRadius: 10,
              padding: 10,
              background: "rgba(27,88,131,0.22)",
              border: "1px solid rgba(27,88,131,0.35)",
            }}
          >
            Wallet provider: <b>{walletProvider || "-"}</b>
          </div>
        ) : null}
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button
          onClick={onCreateOnlineOrder}
          disabled={orderLoading}
          style={{
            padding: "12px 14px",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.18)",
            background: "rgba(95,61,196,0.22)",
            color: "white",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          {orderLoading ? "Criando..." : "Criar pedido online"}
        </button>

        <button
          onClick={onSimulatePayment}
          disabled={payLoading || !currentOrder?.order_id}
          style={{
            padding: "12px 14px",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.18)",
            background: "rgba(27,88,131,0.22)",
            color: "white",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          {payLoading ? "Processando..." : "Simular pagamento"}
        </button>

        {pendingPaymentContext ? (
          <button
            onClick={onConfirmPendingCustomerAction}
            disabled={payLoading}
            style={{
              padding: "12px 14px",
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.18)",
              background: "rgba(199,146,0,0.22)",
              color: "white",
              cursor: "pointer",
              fontWeight: 700,
            }}
          >
            Confirmar pagamento pendente
          </button>
        ) : null}
      </div>

      {pendingPaymentContext ? (
        <div
          style={{
            fontSize: 12,
            borderRadius: 10,
            padding: 10,
            background: "rgba(199,146,0,0.18)",
            border: "1px solid rgba(199,146,0,0.35)",
            whiteSpace: "pre-wrap",
          }}
        >
          <b>Pagamento pendente de ação do cliente</b>
          {"\n"}Método: {pendingPaymentContext.payment_method || "-"}
          {"\n"}Instruction type: {pendingPaymentContext.instructionType || "-"}
          {"\n"}Instruction: {pendingPaymentContext.instruction || "-"}
          {"\n"}Transaction ID: {pendingPaymentContext.transaction_id || "-"}
        </div>
      ) : null}

      {payResp ? (
        <pre
          style={{
            margin: 0,
            fontSize: 12,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            borderRadius: 10,
            padding: 12,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.12)",
          }}
        >
          {payResp}
        </pre>
      ) : null}
    </section>
  );
}