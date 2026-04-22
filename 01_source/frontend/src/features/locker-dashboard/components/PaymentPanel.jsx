// 01_source/frontend/src/features/locker-dashboard/components/PaymentPanel.jsx
// 05/04/2026

import React from "react";
import {
  actionButtonStyle,
  fieldStyle,
  panelStyle,
} from "../utils/dashboardUiStyles.js";

function paymentMethodLabel(method) {
  // Mapeamento baseado nos codes do banco
  const labels = {
    PIX: "PIX",
    CARTAO: "Cartão",
    CREDIT_CARD: "Cartão de Crédito",
    DEBIT_CARD: "Cartão de Débito",
    creditCard: "Cartão de Crédito",
    debitCard: "Cartão de Débito",
    MBWAY: "MB WAY",
    MULTIBANCO_REFERENCE: "Referência Multibanco",
    NFC: "NFC",
    APPLE_PAY: "Apple Pay",
    GOOGLE_PAY: "Google Pay",
    MERCADO_PAGO_WALLET: "Mercado Pago Wallet",
    PAYPAL: "PayPal",
    BOLETO: "Boleto",
  };

  return labels[method] || method || "-";
}

function isWalletPayment(paymentMethod) {
  // Verifica se é wallet (is_wallet = true no banco)
  const walletMethods = ["MERCADO_PAGO_WALLET", "PAYPAL", "APPLE_PAY", "GOOGLE_PAY"];
  return walletMethods.includes(paymentMethod);
}

function isMBWayPayment(paymentMethod) {
  return paymentMethod === "MBWAY";
}

const selectStyle = {
  ...fieldStyle,
  color: "#eef4ff",
  background: "rgba(20,28,44,0.95)",
};

const optionStyle = {
  color: "#101828",
  background: "#ffffff",
};

export default function PaymentPanel({
  availablePaymentMethods,
  payMethod,
  setPayMethod,
  selectedSlotPriceCents,
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
  const slotPriceText =
    Number.isFinite(Number(selectedSlotPriceCents)) && Number(selectedSlotPriceCents) > 0
      ? (Number(selectedSlotPriceCents) / 100).toFixed(2)
      : null;

  return (
    <section style={panelStyle}>
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
            style={selectStyle}
          >
            {(availablePaymentMethods || []).map((method) => (
              <option
                key={method.code || method}
                value={method.code || method}
                style={optionStyle}
              >
                {paymentMethodLabel(method.code || method)}
              </option>
            ))}
          </select>
        </label>

        {slotPriceText ? (
          <div
            style={{
              fontSize: 12,
              borderRadius: 10,
              padding: 10,
              background: "rgba(31,122,63,0.16)",
              border: "1px solid rgba(31,122,63,0.35)",
            }}
          >
            Valor real da gaveta selecionada: <b>{slotPriceText}</b>
          </div>
        ) : null}

        {/* MB WAY */}
        {isMBWayPayment(payMethod) ? (
          <label style={{ display: "grid", gap: 6, fontSize: 13 }}>
            <span style={{ fontWeight: 700 }}>Telefone MB WAY</span>
            <input
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              placeholder="+351912345678"
              style={fieldStyle}
            />
          </label>
        ) : null}

        {/* Wallets */}
        {isWalletPayment(payMethod) ? (
          <div
            style={{
              fontSize: 12,
              borderRadius: 10,
              padding: 10,
              background: "rgba(27,88,131,0.22)",
              border: "1px solid rgba(27,88,131,0.35)",
            }}
          >
            Wallet provider: <b>{walletProvider || payMethod || "-"}</b>
          </div>
        ) : null}
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button
          onClick={onCreateOnlineOrder}
          disabled={orderLoading}
          style={actionButtonStyle({ tone: "accent", disabled: orderLoading })}
        >
          {orderLoading ? "Criando..." : "Criar pedido online"}
        </button>

        <button
          onClick={onSimulatePayment}
          disabled={payLoading || !currentOrder?.order_id}
          style={actionButtonStyle({
            tone: "primary",
            disabled: payLoading || !currentOrder?.order_id,
          })}
        >
          {payLoading ? "Processando..." : "Simular pagamento"}
        </button>

        {pendingPaymentContext ? (
          <button
            onClick={onConfirmPendingCustomerAction}
            disabled={payLoading}
            style={actionButtonStyle({ tone: "warning", disabled: payLoading })}
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