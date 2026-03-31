// 01_source/frontend/src/features/locker-dashboard/utils/dashboardPaymentUtils.js

import { DIGITAL_WALLET_PROVIDER_BY_METHOD } from "./dashboardConstants.js";

export function buildAuthHeaders(token) {
  const headers = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  } else {
    headers["X-Dev-Bypass-Auth"] = "1";
  }

  return headers;
}

export function getOrCreateDeviceFingerprint() {
  const key = "ellan_device_fp_v1";
  let fp = localStorage.getItem(key);

  if (!fp) {
    fp = crypto.randomUUID();
    localStorage.setItem(key, fp);
  }

  return fp;
}

export function generateIdempotencyKey() {
  return crypto.randomUUID();
}

export function generateClientTransactionId() {
  return `txn_${crypto.randomUUID()}`;
}

export function getWalletProviderForMethod(method) {
  return DIGITAL_WALLET_PROVIDER_BY_METHOD[method] || "";
}

export function isDigitalWalletMethod(method) {
  return Boolean(getWalletProviderForMethod(method));
}

export function pickGatewayTransactionId(respObj) {
  if (!respObj || typeof respObj !== "object") {
    return generateClientTransactionId();
  }

  return (
    respObj?.payment?.transaction_id ||
    respObj?.transaction_id ||
    respObj?.sale_id ||
    respObj?.payment_id ||
    respObj?.id ||
    respObj?.request_id ||
    generateClientTransactionId()
  );
}

export function extractPendingPaymentData(gatewayData) {
  const payment = gatewayData?.payment || {};
  const payload = payment?.payload || {};

  return {
    result: gatewayData?.result || null,
    status: payment?.status || null,
    gatewayStatus: payment?.gateway_status || null,
    method: payment?.metodo || null,
    amount: payment?.valor ?? null,
    currency: payment?.currency || null,
    transactionId: payment?.transaction_id || null,
    instructionType: payment?.instruction_type || null,
    instruction: payload?.instruction || null,
    expiresInSec: payload?.expires_in_sec ?? null,
    expiresAtEpoch: payload?.expires_at_epoch ?? null,
    qrCodeText: payload?.qr_code_text || null,
    qrCodeImageBase64: payload?.qr_code_image_base64 || null,
    copyPasteCode: payload?.copy_paste_code || null,
    raw: gatewayData,
  };
}