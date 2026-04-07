// 01_source/frontend/src/utils/paymentProfile.js
// 03/04/2026
// 05/04/2026 - CLEAN VERSION - ZERO REGRA DE PAGAMENTO
// 06/04/2026 - Ajustado para exibir corretamente métodos canônicos vindos do backend

export function paymentMethodLabel(method) {
  const key = String(method || "").trim();

  const labels = {
    // canônicos
    pix: "PIX",
    boleto: "Boleto",
    creditCard: "Cartão de Crédito",
    debitCard: "Cartão de Débito",
    giftCard: "Cartão Presente",
    prepaidCard: "Cartão Pré-pago",
    mbway: "MB WAY",
    multibanco_reference: "Referência Multibanco",
    nfc: "NFC",
    apple_pay: "Apple Pay",
    google_pay: "Google Pay",
    mercado_pago_wallet: "Mercado Pago Wallet",
    paypal: "PayPal",
    m_pesa: "M-Pesa",
    alipay: "Alipay",
    wechat_pay: "WeChat Pay",
    konbini: "Konbini",
    afterpay: "Afterpay",
    zip: "Zip",
    crypto: "Crypto",

    // legado / ui_code
    PIX: "PIX",
    BOLETO: "Boleto",
    CARTAO_CREDITO: "Cartão de Crédito",
    CARTAO_DEBITO: "Cartão de Débito",
    CARTAO_PRESENTE: "Cartão Presente",
    CARTAO_PRE_PAGO: "Cartão Pré-pago",
    MBWAY: "MB WAY",
    MULTIBANCO_REFERENCE: "Referência Multibanco",
    NFC: "NFC",
    APPLE_PAY: "Apple Pay",
    GOOGLE_PAY: "Google Pay",
    MERCADO_PAGO_WALLET: "Mercado Pago Wallet",
    PAYPAL: "PayPal",
    M_PESA: "M-Pesa",
    ALIPAY: "Alipay",
    WECHAT_PAY: "WeChat Pay",
    KONBINI: "Konbini",
    AFTERPAY: "Afterpay",
    ZIP: "Zip",
    CRYPTO: "Crypto",
  };

  return labels[key] || key || "-";
}

export function requiresCustomerPhone() {
  // Front não decide mais
  return false;
}

export function getDefaultPaymentMethod(locker, region) {
  const methods = Array.isArray(locker?.payment_methods)
    ? locker.payment_methods.map((item) => String(item).trim()).filter(Boolean)
    : [];

  if (methods.length > 0) return methods[0];

  return region === "PT" ? "mbway" : "pix";
}

export function buildKioskOrderPayload({
  region,
  totemId,
  skuId,
  slot,
  uiMethod,
  customerPhone = "",
}) {
  return {
    region,
    totem_id: totemId,
    sku_id: skuId,
    desired_slot: Number(slot),
    payment_method: String(uiMethod || "").trim(),
    customer_phone: customerPhone?.trim() || null,
  };
}

export function buildGatewayPaymentPayload({
  region,
  orderId,
  lockerId,
  slot,
  amountCents,
  uiMethod,
  customerPhone = "",
}) {
  return {
    region,
    order_id: orderId,
    locker_id: lockerId,
    slot: Number(slot),
    amount_cents: Number(amountCents),
    payment_method: String(uiMethod || "").trim(),
    customer_phone: customerPhone?.trim() || null,
  };
}

export function buildOnlineOrderPayload({
  region,
  totemId,
  skuId,
  slot,
  uiMethod,
  customerPhone = "",
}) {
  return {
    region,
    sku_id: skuId,
    totem_id: totemId,
    desired_slot: Number(slot),
    payment_method: String(uiMethod || "").trim(),
    customer_phone: customerPhone?.trim() || null,
  };
}