// 01_source/frontend/src/utils/paymentProfile.js
// 03/04/2026

export const PAYMENT_METHODS = {
  PIX: {
    uiCode: "PIX",
    label: "PIX",
    backendMethod: "pix",
    kioskInterface: "qr_code",
    onlineInterface: "qr_code",
    requiresPhone: false,
    walletProvider: null,
  },

  CARTAO_CREDITO: {
    uiCode: "CARTAO_CREDITO",
    label: "Cartão de Crédito",
    backendMethod: "creditCard",
    kioskInterface: "chip",
    onlineInterface: "web_token",
    requiresPhone: false,
    walletProvider: null,
  },

  CARTAO_DEBITO: {
    uiCode: "CARTAO_DEBITO",
    label: "Cartão de Débito",
    backendMethod: "debitCard",
    kioskInterface: "chip",
    onlineInterface: "web_token",
    requiresPhone: false,
    walletProvider: null,
  },

  CARTAO_PRESENTE: {
    uiCode: "CARTAO_PRESENTE",
    label: "Cartão Presente",
    backendMethod: "giftCard",
    kioskInterface: "manual",
    onlineInterface: "web_token",
    requiresPhone: false,
    walletProvider: null,
  },

  MBWAY: {
    uiCode: "MBWAY",
    label: "MB WAY",
    backendMethod: "mbway",
    kioskInterface: "qr_code",
    onlineInterface: "web_token",
    requiresPhone: true,
    walletProvider: null,
  },

  MULTIBANCO_REFERENCE: {
    uiCode: "MULTIBANCO_REFERENCE",
    label: "Referência Multibanco",
    backendMethod: "multibanco_reference",
    kioskInterface: "qr_code",
    onlineInterface: "web_token",
    requiresPhone: false,
    walletProvider: null,
  },

  NFC: {
    uiCode: "NFC",
    label: "NFC",
    backendMethod: "nfc",
    kioskInterface: "nfc",
    onlineInterface: "web_token",
    requiresPhone: false,
    walletProvider: null,
  },

  APPLE_PAY: {
    uiCode: "APPLE_PAY",
    label: "Apple Pay",
    backendMethod: "apple_pay",
    kioskInterface: "nfc",
    onlineInterface: "web_token",
    requiresPhone: false,
    walletProvider: "applePay",
  },

  GOOGLE_PAY: {
    uiCode: "GOOGLE_PAY",
    label: "Google Pay",
    backendMethod: "google_pay",
    kioskInterface: "nfc",
    onlineInterface: "web_token",
    requiresPhone: false,
    walletProvider: "googlePay",
  },

  MERCADO_PAGO_WALLET: {
    uiCode: "MERCADO_PAGO_WALLET",
    label: "Mercado Pago Wallet",
    backendMethod: "mercado_pago_wallet",
    kioskInterface: "qr_code",
    onlineInterface: "web_token",
    requiresPhone: false,
    walletProvider: "mercadoPago",
  },
};

export function getPaymentProfile(uiMethod) {
  return PAYMENT_METHODS[String(uiMethod || "").trim().toUpperCase()] || null;
}

export function paymentMethodLabel(uiMethod) {
  return getPaymentProfile(uiMethod)?.label || uiMethod || "-";
}

export function mapPaymentMethodToBackend(uiMethod) {
  return getPaymentProfile(uiMethod)?.backendMethod || String(uiMethod || "").trim();
}

export function mapPaymentInterface(uiMethod, mode = "kiosk") {
  const profile = getPaymentProfile(uiMethod);
  if (!profile) return "manual";
  return mode === "online" ? profile.onlineInterface : profile.kioskInterface;
}

export function requiresWalletProvider(uiMethod) {
  return Boolean(getPaymentProfile(uiMethod)?.walletProvider);
}

export function mapWalletProvider(uiMethod) {
  return getPaymentProfile(uiMethod)?.walletProvider || null;
}

export function requiresCustomerPhone(uiMethod) {
  return Boolean(getPaymentProfile(uiMethod)?.requiresPhone);
}

export function getDefaultPaymentMethod(locker, region) {
  const methods = Array.isArray(locker?.payment_methods) ? locker.payment_methods : [];
  if (methods.length > 0) return methods[0];
  return region === "PT" ? "MBWAY" : "PIX";
}

export function buildKioskOrderPayload({
  region,
  totemId,
  skuId,
  slot,
  uiMethod,
  customerPhone = "",
}) {
  const paymentMethod = mapPaymentMethodToBackend(uiMethod);
  const paymentInterface = mapPaymentInterface(uiMethod, "kiosk");
  const walletProvider = mapWalletProvider(uiMethod);

  const payload = {
    region,
    sales_channel: "kiosk",
    fulfillment_type: "instant",
    totem_id: totemId,
    sku_id: skuId,
    desired_slot: Number(slot),
    payment_method: paymentMethod,
    payment_interface: paymentInterface,
  };

  if (walletProvider) {
    payload.wallet_provider = walletProvider;
  }

  if (requiresCustomerPhone(uiMethod) && customerPhone.trim()) {
    payload.customer_phone = customerPhone.trim();
  }

  return payload;
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
  const paymentMethod = mapPaymentMethodToBackend(uiMethod);
  const paymentInterface = mapPaymentInterface(uiMethod, "kiosk");
  const walletProvider = mapWalletProvider(uiMethod);

  const payload = {
    regiao: region,
    canal: "KIOSK",
    metodo: paymentMethod,
    interface: paymentInterface,
    valor: Number((Number(amountCents || 0) / 100).toFixed(2)),
    porta: Number(slot),
    locker_id: lockerId,
    order_id: orderId,
  };

  if (walletProvider) {
    payload.wallet_provider = walletProvider;
  }

  if (requiresCustomerPhone(uiMethod) && customerPhone.trim()) {
    payload.customer_phone = customerPhone.trim();
  }

  return payload;
}

export function buildOnlineOrderPayload({
  region,
  totemId,
  skuId,
  slot,
  uiMethod,
  customerPhone = "",
}) {
  const paymentMethod = mapPaymentMethodToBackend(uiMethod);
  const paymentInterface = mapPaymentInterface(uiMethod, "online");
  const walletProvider = mapWalletProvider(uiMethod);

  const payload = {
    region,
    sku_id: skuId,
    totem_id: totemId,
    desired_slot: Number(slot),
    payment_method: paymentMethod,
    payment_interface: paymentInterface,
  };

  if (walletProvider) {
    payload.wallet_provider = walletProvider;
  }

  if (requiresCustomerPhone(uiMethod) && customerPhone.trim()) {
    payload.customer_phone = customerPhone.trim();
  }

  return payload;
}