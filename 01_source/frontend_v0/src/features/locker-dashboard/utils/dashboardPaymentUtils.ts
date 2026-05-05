
import { DIGITAL_WALLET_PROVIDER_BY_METHOD } from "./dashboardConstants";

type UnknownRecord = Record<string, unknown>;

function asRecord(v: unknown): UnknownRecord {
  return v && typeof v === "object" ? (v as UnknownRecord) : {};
}

export function buildAuthHeaders(token: unknown): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${String(token)}`;
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

const WALLET_BY_METHOD = DIGITAL_WALLET_PROVIDER_BY_METHOD as Record<string, string | undefined>;

export function getWalletProviderForMethod(method: unknown) {
  return WALLET_BY_METHOD[String(method || "")] || "";
}

export function isDigitalWalletMethod(method: unknown) {
  return Boolean(getWalletProviderForMethod(method));
}

export function pickGatewayTransactionId(respObj: unknown) {
  if (!respObj || typeof respObj !== "object") {
    return generateClientTransactionId();
  }

  const o = respObj as UnknownRecord;
  const payment = asRecord(o.payment);

  return (
    (payment.transaction_id as string | undefined) ||
    (o.transaction_id as string | undefined) ||
    (o.sale_id as string | undefined) ||
    (o.payment_id as string | undefined) ||
    (o.id as string | undefined) ||
    (o.request_id as string | undefined) ||
    generateClientTransactionId()
  );
}

export function extractPendingPaymentData(gatewayData: unknown) {
  const root = asRecord(gatewayData);
  const payment = asRecord(root.payment);
  const payload = asRecord(payment.payload);

  return {
    result: (root.result as string | null) ?? null,
    status: (payment.status as string | null) ?? null,
    gatewayStatus: (payment.gateway_status as string | null) ?? null,
    method: (payment.metodo as string | null) ?? null,
    amount: payment.valor ?? null,
    currency: (payment.currency as string | null) ?? null,
    transactionId: (payment.transaction_id as string | null) ?? null,
    instructionType: (payment.instruction_type as string | null) ?? null,
    instruction: payload.instruction ?? null,
    expiresInSec: payload.expires_in_sec ?? null,
    expiresAtEpoch: payload.expires_at_epoch ?? null,
    qrCodeText: (payload.qr_code_text as string | null) ?? null,
    qrCodeImageBase64: (payload.qr_code_image_base64 as string | null) ?? null,
    copyPasteCode: (payload.copy_paste_code as string | null) ?? null,
    raw: gatewayData,
  };
}

export function extractGatewayDebugInfo(gatewayData: unknown) {
  const root = asRecord(gatewayData);
  const error = asRecord(root.error);
  const antiReplay = asRecord(root.anti_replay);
  const risk = asRecord(root.risk);
  const locker = asRecord(root.locker);
  const reasons = Array.isArray(risk.reasons) ? risk.reasons : [];

  return {
    errorType: (error.type as string | null) ?? null,
    errorMessage: (error.message as string | null) ?? null,
    retryable: typeof error.retryable === "boolean" ? error.retryable : null,

    antiReplayStatus: (antiReplay.status as string | null) ?? null,
    idempotencyKey: (antiReplay.idempotency_key as string | null) ?? null,
    payloadHash: (antiReplay.payload_hash as string | null) ?? null,
    originalPayloadHash: (antiReplay.original_payload_hash as string | null) ?? null,

    riskDecision: (risk.decision as string | null) ?? null,
    riskScore: typeof risk.score === "number" ? risk.score : null,
    riskReasons: reasons.map((item: unknown) => {
      const it = asRecord(item);
      return {
        code: (it.code as string) || "-",
        weight: it.weight ?? "-",
        detail: (it.detail as string) || "",
      };
    }),

    severity: (root.severity as string | null) ?? null,
    severityCode: (root.severity_code as string | null) ?? null,

    lockerId: (locker.locker_id as string | null) ?? null,
    requestId: (root.request_id as string | null) ?? null,

    raw: gatewayData || {},
  };
}

