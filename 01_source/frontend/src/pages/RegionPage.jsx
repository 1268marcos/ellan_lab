// 01_source/frontend/src/pages/RegionPage.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

import EmailReceiptModal from "../components/EmailReceiptModal.jsx";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const GATEWAY_BASE =
  import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";

const RUNTIME_BASE =
  import.meta.env.VITE_RUNTIME_BASE_URL || "http://localhost:8200";

const initialIdentify = {
  phone: "",
  email: "",
};

const initialPaymentExtras = {
  customerPhone: "",
};

function extractReceiptCodeFromPaymentResp(paymentResp) {
  if (!paymentResp) return null;
  return paymentResp?.fiscal?.receipt_code || paymentResp?.receipt_code || null;
}

function formatMoney(cents, currency) {
  const value = Number(cents);
  if (!Number.isFinite(value)) return "-";

  const amount = value / 100;

  try {
    return new Intl.NumberFormat(currency === "BRL" ? "pt-BR" : "pt-PT", {
      style: "currency",
      currency: currency || "EUR",
    }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency || ""}`.trim();
  }
}

function normalizeLockerItem(locker) {
  const address =
    locker?.address && typeof locker.address === "object"
      ? locker.address
      : {
          address: locker?.address || "",
          number: locker?.number ?? "",
          additional_information: locker?.additional_information || "",
          locality: locker?.locality || "",
          city: locker?.city || "",
          federative_unit: locker?.federative_unit || "",
          postal_code: locker?.postal_code || "",
          country: locker?.country || "",
        };

  const slotCountFromRuntime = Array.isArray(locker?.slot_ids)
    ? locker.slot_ids.length
    : Number(locker?.slots || 0);

  return {
    locker_id: String(locker?.locker_id || "").trim(),
    region: String(locker?.region || "").toUpperCase(),
    site_id: locker?.site_id || "",
    display_name: locker?.display_name || locker?.locker_id || "",
    backend_region: String(locker?.backend_region || locker?.region || "").toUpperCase(),
    slots: Number(slotCountFromRuntime || 0),
    channels: Array.isArray(locker?.channels) ? locker.channels.map(String) : [],
    payment_methods: Array.isArray(locker?.payment_methods)
      ? locker.payment_methods.map((item) => String(item).toUpperCase())
      : [],
    address,
    active: Boolean(locker?.active),
  };
}

function getDefaultPaymentMethod(locker, region) {
  const methods = Array.isArray(locker?.payment_methods) ? locker.payment_methods : [];
  if (methods.length > 0) return methods[0];
  return region === "PT" ? "MBWAY" : "PIX";
}

function paymentMethodLabel(method) {
  const labels = {
    PIX: "PIX",
    CARTAO_CREDITO: "Cartão de Crédito",
    CARTAO_DEBITO: "Cartão de Débito",
    CARTAO_PRESENTE: "Cartão Presente",
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

function gatewayMethodForUiMethod(method) {
  if (method === "CARTAO_CREDITO") return "CARTAO";
  if (method === "CARTAO_DEBITO") return "CARTAO";
  if (method === "CARTAO_PRESENTE") return "CARTAO_PRESENTE";
  return method;
}

function cardTypeForUiMethod(method) {
  if (method === "CARTAO_CREDITO") return "creditCard";
  if (method === "CARTAO_DEBITO") return "debitCard";
  if (method === "CARTAO_PRESENTE") return "giftCard";
  return null;
}


function formatAddress(locker) {
  if (!locker) return "-";

  const address = locker.address || {};

  const parts = [
    [address.address, address.number].filter(Boolean).join(", "),
    address.additional_information || "",
    address.locality || "",
    [address.city, address.federative_unit].filter(Boolean).join(" / "),
    address.postal_code || "",
    address.country || "",
  ]
    .map((item) => String(item || "").trim())
    .filter(Boolean);

  return parts.join(" • ");
}

function nowEpochSec() {
  return Math.floor(Date.now() / 1000);
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function formatRemaining(sec) {
  const safe = Math.max(0, Math.floor(Number(sec || 0)));
  const h = Math.floor(safe / 3600);
  const m = Math.floor((safe % 3600) / 60);
  const s = safe % 60;

  if (h > 0) return `${h}:${pad2(m)}:${pad2(s)}`;
  return `${m}:${pad2(s)}`;
}

function formatEpochDateTime(epochSec, region) {
  if (!epochSec) return "-";

  try {
    const dt = new Date(Number(epochSec) * 1000);
    return dt.toLocaleString(region === "SP" ? "pt-BR" : "pt-PT", {
      timeZone: region === "SP" ? "America/Sao_Paulo" : "Europe/Lisbon",
      hour12: false,
    });
  } catch {
    return "-";
  }
}

function extractPendingPaymentContext(gatewayData) {
  const payment = gatewayData?.payment || {};
  const payload = payment?.payload || {};

  return {
    result: gatewayData?.result || null,
    status: payment?.status || null,
    gateway_status: payment?.gateway_status || null,
    method: payment?.metodo || null,
    value: payment?.valor ?? null,
    currency: payment?.currency || null,
    transaction_id: payment?.transaction_id || null,
    instruction_type: payment?.instruction_type || null,
    instruction: payload?.instruction || null,
    expires_in_sec: payload?.expires_in_sec ?? null,
    expires_at_epoch: payload?.expires_at_epoch ?? null,
    qr_code_text: payload?.qr_code_text || null,
    qr_code_image_base64: payload?.qr_code_image_base64 || null,
    copy_paste_code: payload?.copy_paste_code || null,
    customer_phone: payload?.customer_phone || null,
    amount_cents: payload?.amount_cents ?? null,
    raw: gatewayData,
  };
}

function getOrCreateDeviceFingerprint() {
  const key = "ellan_device_fp_v1";
  let fp = localStorage.getItem(key);
  if (!fp) {
    fp = crypto.randomUUID();
    localStorage.setItem(key, fp);
  }
  return fp;
}

function generateIdempotencyKey() {
  return crypto.randomUUID();
}

function copyText(text) {
  return navigator.clipboard.writeText(String(text || ""));
}

function resolveDisplayedPendingContext(gatewayPendingContext, createResp, paymentMethod) {
  if (gatewayPendingContext) return gatewayPendingContext;

  const preview = createResp?.payment_payload || null;
  const instructionType = createResp?.payment_instruction_type || null;
  const paymentStatus = createResp?.payment_status || null;

  if (!preview || !instructionType) return null;

  return {
    result: "local_preview",
    status: paymentStatus,
    gateway_status: null,
    method: paymentMethod || createResp?.payment_method || null,
    value: null,
    currency: null,
    transaction_id: null,
    instruction_type: instructionType,
    instruction: preview?.instruction || null,
    expires_in_sec: preview?.expires_in_sec ?? null,
    expires_at_epoch: preview?.expires_at_epoch ?? null,
    qr_code_text: preview?.qr_code_text || null,
    qr_code_image_base64: preview?.qr_code_image_base64 || null,
    copy_paste_code: preview?.copy_paste_code || null,
    customer_phone: preview?.customer_phone || null,
    amount_cents: preview?.amount_cents ?? null,
    raw: createResp,
  };
}

function isPendingPaymentResult(data) {
  return (
    data?.result === "pending_customer_action" ||
    data?.result === "pending_provider_confirmation" ||
    data?.result === "awaiting_integration"
  );
}

function isCatalogItemSelectable(item) {
  return Boolean(
    item &&
      item.is_active &&
      item.sku_id &&
      item.is_operationally_available &&
      item.locker_state === "AVAILABLE"
  );
}

function safeJsonStringify(value) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function parseErrorPayload(data) {
  if (typeof data?.detail === "string") return data.detail;
  if (typeof data?.detail === "object" && data?.detail) return safeJsonStringify(data.detail);
  return safeJsonStringify(data);
}

export default function RegionPage({ region, mode = "kiosk" }) {
  const [availableLockers, setAvailableLockers] = useState([]);
  const [lockersLoading, setLockersLoading] = useState(false);
  const [lockersError, setLockersError] = useState("");
  const [lockersSource, setLockersSource] = useState("loading");

  const [selectedLockerId, setSelectedLockerId] = useState("");
  const selectedLocker = useMemo(
    () =>
      availableLockers.find((item) => item.locker_id === selectedLockerId) ||
      availableLockers[0] ||
      null,
    [availableLockers, selectedLockerId]
  );

  const [paymentMethod, setPaymentMethod] = useState("");
  const [totemId, setTotemId] = useState("");

  const [catalogSlots, setCatalogSlots] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogRefreshing, setCatalogRefreshing] = useState(false);
  const [catalogError, setCatalogError] = useState("");
  const pollRef = useRef(null);

  const [selectedSlot, setSelectedSlot] = useState(null);
  const [selectedCatalogItem, setSelectedCatalogItem] = useState(null);

  const [createResp, setCreateResp] = useState(null);
  const [paymentResp, setPaymentResp] = useState(null);
  const [gatewayPaymentResp, setGatewayPaymentResp] = useState(null);
  const [pendingPaymentContext, setPendingPaymentContext] = useState(null);
  const [identifyResp, setIdentifyResp] = useState(null);

  const [identifyForm, setIdentifyForm] = useState(initialIdentify);
  const [paymentExtras, setPaymentExtras] = useState(initialPaymentExtras);

  const [loadingCreate, setLoadingCreate] = useState(false);
  const [loadingGatewayPayment, setLoadingGatewayPayment] = useState(false);
  const [loadingPayment, setLoadingPayment] = useState(false);
  const [loadingIdentify, setLoadingIdentify] = useState(false);

  const [err, setErr] = useState(null);
  const [, setTick] = useState(0);

  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailModalSuccess, setEmailModalSuccess] = useState("");
  const [emailModalError, setEmailModalError] = useState("");

  const createUrl = useMemo(() => `${ORDER_PICKUP_BASE}/kiosk/orders`, []);
  const identifyUrl = useMemo(() => `${ORDER_PICKUP_BASE}/kiosk/identify`, []);
  const gatewayPaymentUrl = useMemo(() => `${GATEWAY_BASE}/gateway/pagamento`, []);
  const runtimeCatalogSlotsUrl = useMemo(() => `${RUNTIME_BASE}/catalog/slots`, []);
  const runtimeLockerSlotsUrl = useMemo(() => `${RUNTIME_BASE}/locker/slots`, []);

  const currentOrderId = createResp?.order_id || null;
  const allowedPaymentMethods = selectedLocker?.payment_methods || [];
  const receiptCode = extractReceiptCodeFromPaymentResp(paymentResp);

  const displayedPendingContext = useMemo(
    () => resolveDisplayedPendingContext(pendingPaymentContext, createResp, paymentMethod),
    [pendingPaymentContext, createResp, paymentMethod]
  );

  const pendingSecondsRemaining = displayedPendingContext?.expires_at_epoch
    ? Math.max(0, Number(displayedPendingContext.expires_at_epoch) - nowEpochSec())
    : null;

  const pendingExpired =
    pendingSecondsRemaining != null && Number(pendingSecondsRemaining) <= 0;

  useEffect(() => {
    fetchLockersOnce();
  }, [region]);

  useEffect(() => {
    if (!availableLockers.length) {
      setSelectedLockerId("");
      setTotemId("");
      return;
    }

    setSelectedLockerId((prev) => {
      if (prev && availableLockers.some((locker) => locker.locker_id === prev)) {
        return prev;
      }
      return availableLockers[0].locker_id;
    });
  }, [availableLockers]);

  useEffect(() => {
    if (!selectedLocker) {
      setTotemId("");
      setPaymentMethod("");
      return;
    }

    setTotemId(selectedLocker.locker_id);

    setPaymentMethod((prev) => {
      if (prev && allowedPaymentMethods.includes(prev)) return prev;
      return getDefaultPaymentMethod(selectedLocker, region);
    });

    setSelectedSlot(null);
    setSelectedCatalogItem(null);
    setCreateResp(null);
    setPaymentResp(null);
    setGatewayPaymentResp(null);
    setPendingPaymentContext(null);
    setIdentifyResp(null);
    setIdentifyForm(initialIdentify);
    setPaymentExtras(initialPaymentExtras);
    setErr(null);
  }, [selectedLockerId, selectedLocker, region]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setPaymentExtras((prev) => {
      const next = { ...prev };

      if (paymentMethod !== "MBWAY") {
        next.customerPhone = "";
      }

      return next;
    });
  }, [paymentMethod]);

  useEffect(() => {
    fetchCatalogSlots();

    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(() => {
      fetchCatalogSlots(true);
    }, 3000);

    function handleVisibilityChange() {
      if (document.visibilityState === "visible") {
        fetchCatalogSlots(true);
      }
    }

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [selectedLockerId, runtimeCatalogSlotsUrl, runtimeLockerSlotsUrl]);

  useEffect(() => {
    if (!displayedPendingContext?.expires_at_epoch) return;

    const interval = setInterval(() => {
      setTick((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [displayedPendingContext?.expires_at_epoch]);

  async function fetchLockersOnce() {
    setLockersLoading(true);
    setLockersError("");

    try {
      const res = await fetch(
        `${GATEWAY_BASE}/lockers?region=${encodeURIComponent(region)}&active_only=true`
      );
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(parseErrorPayload(data));
      }

      const items = Array.isArray(data?.items) ? data.items.map(normalizeLockerItem) : [];

      if (!items.length) {
        throw new Error(`Nenhum locker ativo retornado pelo gateway para a região ${region}.`);
      }

      setAvailableLockers(items);
      setLockersSource("gateway");
    } catch (e) {
      setAvailableLockers([]);
      setLockersSource("error");
      setLockersError(`Falha ao carregar lockers do gateway: ${String(e?.message || e)}`);
    } finally {
      setLockersLoading(false);
    }
  }

  async function fetchCatalogSlots(silent = false) {
    if (!selectedLocker) {
      setCatalogSlots([]);
      return;
    }

    if (silent) {
      setCatalogRefreshing(true);
    } else {
      setCatalogLoading(true);
    }
    setCatalogError("");

    try {
      const headers = {
        "X-Locker-Id": selectedLocker.locker_id,
      };

      const [catalogRes, lockerRes] = await Promise.all([
        fetch(runtimeCatalogSlotsUrl, { headers }),
        fetch(runtimeLockerSlotsUrl, { headers }),
      ]);

      const catalogData = await catalogRes.json().catch(() => []);
      const lockerData = await lockerRes.json().catch(() => []);

      if (!catalogRes.ok) {
        throw new Error(parseErrorPayload(catalogData));
      }

      if (!lockerRes.ok) {
        throw new Error(parseErrorPayload(lockerData));
      }

      const lockerMap = {};
      for (const item of Array.isArray(lockerData) ? lockerData : []) {
        lockerMap[Number(item.slot)] = {
          state: item.state || "AVAILABLE",
          product_id: item.product_id ?? null,
          updated_at: item.updated_at ?? null,
        };
      }

      const normalized = (Array.isArray(catalogData) ? catalogData : [])
        .map((item) => {
          const slot = Number(item.slot);
          const lockerState = lockerMap[slot]?.state || "AVAILABLE";
          const isOperationallyAvailable = lockerState === "AVAILABLE";

          return {
            slot,
            sku_id: item.sku_id || null,
            name: item.name || "",
            amount_cents: item.amount_cents ?? null,
            currency: item.currency || (region === "SP" ? "BRL" : "EUR"),
            imageURL: item.imageURL || "",
            is_active: Boolean(item.is_active),
            locker_state: lockerState,
            is_operationally_available: isOperationallyAvailable,
          };
        })
        .sort((a, b) => a.slot - b.slot);

      setCatalogSlots(normalized);
    } catch (e) {
      setCatalogError(String(e?.message || e));
    } finally {
      if (silent) {
        setCatalogRefreshing(false);
      } else {
        setCatalogLoading(false);
      }
    }
  }

  function handleSelectCatalogItem(item) {
    if (!isCatalogItemSelectable(item)) return;

    setSelectedSlot(item.slot);
    setSelectedCatalogItem(item);
    setCreateResp(null);
    setPaymentResp(null);
    setGatewayPaymentResp(null);
    setPendingPaymentContext(null);
    setIdentifyResp(null);
    setErr(null);
  }

  async function createKioskOrder() {
    if (!selectedLocker) {
      setErr("Selecione um locker antes de criar o pedido KIOSK.");
      return;
    }

    if (!selectedCatalogItem?.sku_id || !selectedCatalogItem?.slot) {
      setErr("Selecione uma gaveta/produto antes de criar o pedido KIOSK.");
      return;
    }

    if (!isCatalogItemSelectable(selectedCatalogItem)) {
      setErr("A gaveta selecionada não está disponível operacionalmente.");
      return;
    }

    if (!paymentMethod) {
      setErr("Selecione um método de pagamento.");
      return;
    }

    if (paymentMethod === "CARTAO" && !paymentExtras.cardType) {
      setErr("Escolha se o cartão é crédito ou débito.");
      return;
    }

    if (paymentMethod === "MBWAY" && !paymentExtras.customerPhone.trim()) {
      setErr("Informe o telefone para o pagamento MB WAY.");
      return;
    }

    setErr(null);
    setCreateResp(null);
    setPaymentResp(null);
    setGatewayPaymentResp(null);
    setPendingPaymentContext(null);
    setIdentifyResp(null);

    setLoadingCreate(true);
    try {
      const mappedPaymentMethod = gatewayMethodForUiMethod(paymentMethod);
      const mappedCardType = cardTypeForUiMethod(paymentMethod);

      const payload = {
        region,
        totem_id: totemId,
        sku_id: selectedCatalogItem.sku_id,
        desired_slot: Number(selectedCatalogItem.slot),
        payment_method: mappedPaymentMethod,
        card_type: mappedCardType || undefined,
        customer_phone:
          paymentMethod === "MBWAY" ? paymentExtras.customerPhone.trim() : undefined,
      };

      const res = await fetch(createUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Device-Fingerprint": getOrCreateDeviceFingerprint(),
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(parseErrorPayload(data));
      }

      setCreateResp(data);
      await fetchCatalogSlots(true);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingCreate(false);
    }
  }

  async function initiateKioskPayment() {
    if (!currentOrderId) {
      setErr("Crie primeiro um pedido KIOSK.");
      return;
    }

    if (!selectedCatalogItem?.slot) {
      setErr("Selecione uma gaveta/produto antes de iniciar o pagamento.");
      return;
    }

    if (!selectedLocker) {
      setErr("Selecione um locker antes de iniciar o pagamento.");
      return;
    }

    const mappedCardType = cardTypeForUiMethod(paymentMethod);

    if (paymentMethod === "MBWAY" && !paymentExtras.customerPhone.trim()) {
      setErr("Informe o telefone para o pagamento MB WAY.");
      return;
    }

    setErr(null);
    setPaymentResp(null);
    setGatewayPaymentResp(null);
    setPendingPaymentContext(null);

    setLoadingGatewayPayment(true);
    try {
      const mappedPaymentMethod = gatewayMethodForUiMethod(paymentMethod);
      const mappedCardType = cardTypeForUiMethod(paymentMethod);

      const payload = {
        regiao: region,
        canal: "KIOSK",
        metodo: mappedPaymentMethod,
        valor: Number((Number(selectedCatalogItem.amount_cents || 0) / 100).toFixed(2)),
        porta: Number(selectedCatalogItem.slot),
        locker_id: totemId,
        order_id: currentOrderId,
      };

      if (mappedCardType) {
        payload.card_type = mappedCardType;
      }      

      if (paymentMethod === "MBWAY") {
        payload.customer_phone = paymentExtras.customerPhone.trim();
      }

      if (paymentMethod === "APPLE_PAY") {
        payload.wallet_provider = "applePay";
      }

      if (paymentMethod === "GOOGLE_PAY") {
        payload.wallet_provider = "googlePay";
      }

      if (paymentMethod === "MERCADO_PAGO_WALLET") {
        payload.wallet_provider = "mercadoPago";
      }

      const res = await fetch(gatewayPaymentUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": generateIdempotencyKey(),
          "X-Device-Fingerprint": getOrCreateDeviceFingerprint(),
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(parseErrorPayload(data));
      }

      setGatewayPaymentResp(data);

      if (isPendingPaymentResult(data)) {
        setPendingPaymentContext(extractPendingPaymentContext(data));
        return;
      }

      if (data?.result === "approved" || data?.payment?.status === "APPROVED") {
        await approveKioskPayment();
      }
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingGatewayPayment(false);
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
      const url = `${ORDER_PICKUP_BASE}/kiosk/orders/${currentOrderId}/payment-approved`;

      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(parseErrorPayload(data));
      }

      setPendingPaymentContext(null);
      setPaymentResp(data);
      await fetchCatalogSlots(true);
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
        throw new Error(parseErrorPayload(data));
      }

      setIdentifyResp(data);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingIdentify(false);
    }
  }

  async function handleSendReceiptEmail(email) {
    if (!currentOrderId) {
      setEmailModalError("Pedido não encontrado.");
      setEmailModalSuccess("");
      return;
    }

    setSendingEmail(true);
    setErr(null);
    setIdentifyResp(null);
    setEmailModalError("");
    setEmailModalSuccess("");

    try {
      const res = await fetch(identifyUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          order_id: currentOrderId,
          phone: null,
          email,
        }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(parseErrorPayload(data));
      }

      const successMessage =
        data?.message || `Comprovante fiscal enviado com sucesso para ${email}.`;

      setIdentifyResp(data);
      setEmailModalSuccess(successMessage);
      setEmailModalError("");
    } catch (e) {
      const msg = String(e?.message || e);
      setEmailModalError(msg);
      setEmailModalSuccess("");
      setErr(msg);
    } finally {
      setSendingEmail(false);
    }
  }

  return (
    <div style={pageStyle}>
      <div style={headerCardStyle}>
        <h1 style={{ margin: 0 }}>Simulador KIOSK — {region}</h1>
        <div style={subtleStyle}>
          Tela operacional usando gateway + runtime. Sem backend_sp/backend_pt e sem
          fallback local no frontend.
        </div>
      </div>

      <section style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={h2Style}>0. Seleção da unidade física</h2>
          <button
            onClick={fetchLockersOnce}
            disabled={lockersLoading}
            style={buttonSecondaryStyle}
          >
            {lockersLoading ? "Atualizando..." : "Atualizar lockers"}
          </button>
        </div>

        {availableLockers.length === 0 ? (
          <div style={errorBoxStyle}>
            {lockersError || `Nenhum locker ativo foi encontrado para a região ${region}.`}
          </div>
        ) : (
          <div style={fieldGridStyle}>
            <label style={labelStyle}>
              Locker
              <select
                value={selectedLockerId}
                onChange={(e) => setSelectedLockerId(e.target.value)}
                style={inputStyle}
              >
                {availableLockers.map((locker) => (
                  <option key={locker.locker_id} value={locker.locker_id}>
                    {locker.display_name}
                  </option>
                ))}
              </select>
            </label>

            <div style={lockerSummaryCardStyle}>
              <div><b>fonte:</b> {lockersSource}</div>
              <div><b>locker_id:</b> {selectedLocker?.locker_id || "-"}</div>
              <div><b>site_id:</b> {selectedLocker?.site_id || "-"}</div>
              <div><b>região:</b> {selectedLocker?.region || "-"}</div>
              <div><b>slots:</b> {selectedLocker?.slots || "-"}</div>
              <div><b>canais:</b> {(selectedLocker?.channels || []).join(", ") || "-"}</div>
              <div>
                <b>métodos permitidos:</b>{" "}
                {(selectedLocker?.payment_methods || []).join(", ") || "-"}
              </div>
              <div><b>endereço:</b> {formatAddress(selectedLocker)}</div>
            </div>

            {lockersError ? <pre style={errorBoxStyle}>{lockersError}</pre> : null}
          </div>
        )}
      </section>

      <section style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={h2Style}>1. Vitrine operacional do locker</h2>
          <button onClick={() => fetchCatalogSlots(false)} disabled={catalogLoading} style={buttonSecondaryStyle}>
            {catalogLoading ? "Atualizando..." : "Atualizar vitrine"}
          </button>
        </div>

        <div style={infoGridStyle}>
          <div><b>Região:</b> {region}</div>
          <div><b>Locker selecionado:</b> {selectedLocker?.locker_id || "-"}</div>
          <div><b>Runtime catálogo:</b> {runtimeCatalogSlotsUrl}</div>
          <div><b>Runtime estado:</b> {runtimeLockerSlotsUrl}</div>
          <div><b>Polling vitrine:</b> 3s {catalogRefreshing ? "• sincronizando..." : "• ativo"}</div>
        </div>

        {catalogError ? <pre style={errorBoxStyle}>{catalogError}</pre> : null}

        {catalogLoading ? (
          <div style={subtleStyle}>Carregando gavetas...</div>
        ) : (
          <div style={slotsGridStyle}>
            {catalogSlots.map((item) => {
              const isSelected = selectedSlot === item.slot;
              const isSelectable = isCatalogItemSelectable(item);
              const isDisabled = !isSelectable;

              return (
                <button
                  key={item.slot}
                  type="button"
                  onClick={() => handleSelectCatalogItem(item)}
                  disabled={isDisabled}
                  style={{
                    ...slotCardStyle,
                    border: isSelected
                      ? "2px solid rgba(255,255,255,0.85)"
                      : "1px solid rgba(255,255,255,0.12)",
                    background: isSelected
                      ? "linear-gradient(135deg, rgba(27,88,131,0.35), rgba(27,88,131,0.18))"
                      : isDisabled
                        ? "rgba(255,255,255,0.03)"
                        : "rgba(255,255,255,0.05)",
                    opacity: isDisabled ? 0.55 : 1,
                    cursor: isDisabled ? "not-allowed" : "pointer",
                  }}
                >
                  <div style={slotTopRowStyle}>
                    <span style={slotBadgeStyle}>Gaveta {item.slot}</span>
                    <span style={miniStatusStyle(isSelectable)}>
                      {item.is_active
                        ? isSelectable
                          ? "Disponível"
                          : item.locker_state || "Indisponível"
                        : "Inativa"}
                    </span>
                  </div>

                  <div style={slotNameStyle}>{item.name || "Sem produto"}</div>

                  <div style={slotMetaStyle}>
                    <div><b>SKU:</b> {item.sku_id || "-"}</div>
                    <div><b>Preço:</b> {formatMoney(item.amount_cents, item.currency)}</div>
                    <div><b>Moeda:</b> {item.currency || "-"}</div>
                    <div><b>Estado real:</b> {item.locker_state || "-"}</div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </section>

      <div style={gridStyle}>
        <section style={cardStyle}>
          <h2 style={h2Style}>2. Criar pedido KIOSK</h2>

          <div style={fieldGridStyle}>
            <label style={labelStyle}>
              Região
              <input value={region} disabled style={inputStyleDisabled} />
            </label>

            <label style={labelStyle}>
              Locker / Totem ID
              <input value={totemId} onChange={(e) => setTotemId(e.target.value)} style={inputStyle} />
            </label>

            <label style={labelStyle}>
              Gaveta escolhida
              <input
                value={selectedCatalogItem?.slot ?? ""}
                disabled
                style={inputStyleDisabled}
                placeholder="Selecione na vitrine"
              />
            </label>

            <label style={labelStyle}>
              SKU escolhido
              <input
                value={selectedCatalogItem?.sku_id ?? ""}
                disabled
                style={inputStyleDisabled}
                placeholder="Selecione na vitrine"
              />
            </label>

            <label style={labelStyle}>
              Produto
              <input
                value={selectedCatalogItem?.name ?? ""}
                disabled
                style={inputStyleDisabled}
                placeholder="Selecione na vitrine"
              />
            </label>

            <label style={labelStyle}>
              Preço
              <input
                value={
                  selectedCatalogItem
                    ? formatMoney(selectedCatalogItem.amount_cents, selectedCatalogItem.currency)
                    : ""
                }
                disabled
                style={inputStyleDisabled}
                placeholder="Selecione na vitrine"
              />
            </label>

            <label style={labelStyle}>
              Método de pagamento
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                style={inputStyle}
              >
                {allowedPaymentMethods.map((method) => (
                  <option key={method} value={method}>
                    {paymentMethodLabel(method)}
                  </option>
                ))}
              </select>
            </label>

            {paymentMethod === "MBWAY" ? (
              <label style={labelStyle}>
                Telefone MB WAY
                <input
                  value={paymentExtras.customerPhone}
                  onChange={(e) =>
                    setPaymentExtras((prev) => ({
                      ...prev,
                      customerPhone: e.target.value,
                    }))
                  }
                  style={inputStyle}
                  placeholder="+351912345678"
                />
              </label>
            ) : null}
          </div>

          <button onClick={createKioskOrder} disabled={loadingCreate} style={buttonPrimaryStyle}>
            {loadingCreate ? "Criando..." : "Criar pedido KIOSK"}
          </button>

          {createResp ? (
            <div style={okBoxStyle}>
              <strong>Pedido criado com sucesso</strong>
              <div style={summaryListStyle}>
                <div><b>order_id:</b> {createResp.order_id}</div>
                <div><b>allocation_id:</b> {createResp.allocation_id}</div>
                <div><b>slot:</b> {createResp.slot}</div>
                <div><b>amount_cents:</b> {createResp.amount_cents}</div>
                <div><b>payment_method:</b> {createResp.payment_method}</div>
                <div><b>payment_status:</b> {createResp.payment_status || "-"}</div>
                <div><b>instruction_type:</b> {createResp.payment_instruction_type || "-"}</div>
                <div><b>ttl_sec:</b> {createResp.ttl_sec}</div>
                <div><b>status:</b> {createResp.status}</div>
              </div>

              {createResp.payment_payload &&
              Object.keys(createResp.payment_payload).length > 0 ? (
                <pre style={jsonBoxStyle}>
                  {JSON.stringify(createResp.payment_payload, null, 2)}
                </pre>
              ) : null}

              <div style={messageStyle}>{createResp.message}</div>
            </div>
          ) : null}
        </section>

        <section style={cardStyle}>
          <h2 style={h2Style}>3. Pagamento KIOSK</h2>

          <div style={subtleStyle}>
            Fluxo operacional:
            <br />
            1. criar pedido KIOSK
            <br />
            2. iniciar pagamento no gateway
            <br />
            3. se ficar pendente, mostrar QR/código
            <br />
            4. simular conclusão do pagamento
          </div>

          <div style={{ marginTop: 12, display: "grid", gap: 6 }}>
            <div><b>Pedido atual:</b> {currentOrderId || "nenhum"}</div>
            <div><b>Método atual:</b> {paymentMethod || "-"}</div>
            <div><b>Locker:</b> {totemId || "-"}</div>
            <div><b>Gaveta:</b> {selectedCatalogItem?.slot ?? "-"}</div>
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 14 }}>
            <button
              onClick={initiateKioskPayment}
              disabled={loadingGatewayPayment || !currentOrderId}
              style={buttonSecondaryStyle}
            >
              {loadingGatewayPayment ? "Iniciando..." : "Iniciar pagamento no gateway"}
            </button>

            <button
              onClick={approveKioskPayment}
              disabled={loadingPayment || !currentOrderId}
              style={buttonPrimaryStyle}
            >
              {loadingPayment ? "Confirmando..." : "Simular pagamento concluído"}
            </button>
          </div>

          {gatewayPaymentResp ? (
            <div style={okBoxStyle}>
              <strong>Resposta do gateway</strong>
              <div style={summaryListStyle}>
                <div><b>result:</b> {gatewayPaymentResp.result || "-"}</div>
                <div><b>status:</b> {gatewayPaymentResp.payment?.status || "-"}</div>
                <div><b>gateway_status:</b> {gatewayPaymentResp.payment?.gateway_status || "-"}</div>
                <div><b>metodo:</b> {gatewayPaymentResp.payment?.metodo || "-"}</div>
                <div><b>transaction_id:</b> {gatewayPaymentResp.payment?.transaction_id || "-"}</div>
              </div>
            </div>
          ) : null}

          {displayedPendingContext ? (
            <div style={pendingCardStyle}>
              <strong>
                {pendingExpired
                  ? "Pagamento pendente expirado"
                  : "Pagamento pendente de ação do cliente"}
              </strong>

              <div style={summaryListStyle}>
                <div><b>origem:</b> {pendingPaymentContext ? "gateway" : "preview local do create_order"}</div>
                <div><b>método:</b> {displayedPendingContext.method || "-"}</div>
                <div><b>status:</b> {displayedPendingContext.status || "-"}</div>
                <div><b>instruction_type:</b> {displayedPendingContext.instruction_type || "-"}</div>
                <div><b>expira em:</b> {formatEpochDateTime(displayedPendingContext.expires_at_epoch, region)}</div>
                <div><b>tempo restante:</b> {pendingSecondsRemaining == null ? "-" : formatRemaining(pendingSecondsRemaining)}</div>
              </div>

              {displayedPendingContext.instruction ? (
                <div style={infoNoticeStyle}>{displayedPendingContext.instruction}</div>
              ) : null}

              {displayedPendingContext.qr_code_image_base64 ? (
                <div style={pendingPaymentGridStyle}>
                  <div style={pendingQrPanelStyle}>
                    <img
                      src={`data:image/png;base64,${displayedPendingContext.qr_code_image_base64}`}
                      alt="QR Code de pagamento"
                      style={{ width: 180, height: 180, objectFit: "contain" }}
                    />
                  </div>

                  <div style={{ display: "grid", gap: 10 }}>
                    <label style={labelStyle}>
                      Código copia-e-cola
                      <textarea
                        readOnly
                        value={
                          displayedPendingContext.copy_paste_code ||
                          displayedPendingContext.qr_code_text ||
                          ""
                        }
                        style={textAreaStyle}
                      />
                    </label>

                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                      <button
                        onClick={async () => {
                          await copyText(
                            displayedPendingContext.copy_paste_code ||
                              displayedPendingContext.qr_code_text ||
                              ""
                          );
                        }}
                        style={buttonSecondaryStyle}
                      >
                        Copiar código
                      </button>
                    </div>
                  </div>
                </div>
              ) : displayedPendingContext.qr_code_text ? (
                <div style={pendingPaymentGridStyle}>
                  <div style={pendingQrPanelStyle}>
                    <QRCodeCanvas value={displayedPendingContext.qr_code_text} size={180} />
                  </div>

                  <div style={{ display: "grid", gap: 10 }}>
                    <label style={labelStyle}>
                      QR / Código
                      <textarea
                        readOnly
                        value={
                          displayedPendingContext.copy_paste_code ||
                          displayedPendingContext.qr_code_text ||
                          ""
                        }
                        style={textAreaStyle}
                      />
                    </label>

                    <button
                      onClick={async () => {
                        await copyText(
                          displayedPendingContext.copy_paste_code ||
                            displayedPendingContext.qr_code_text ||
                            ""
                        );
                      }}
                      style={buttonSecondaryStyle}
                    >
                      Copiar
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {paymentResp ? (
            <div style={okBoxStyle}>
              <strong>Pagamento confirmado</strong>
              <pre style={jsonBoxStyle}>{JSON.stringify(paymentResp, null, 2)}</pre>
            </div>
          ) : null}
        </section>
      </div>

      <section style={cardStyle}>
        <h2 style={h2Style}>4. Identificação / envio de comprovante</h2>

        <div style={fieldGridStyle}>
          <label style={labelStyle}>
            Telefone
            <input
              value={identifyForm.phone}
              onChange={(e) => setIdentifyForm((prev) => ({ ...prev, phone: e.target.value }))}
              style={inputStyle}
              placeholder="+5511999999999 / +351912345678"
            />
          </label>

          <label style={labelStyle}>
            Email
            <input
              value={identifyForm.email}
              onChange={(e) => setIdentifyForm((prev) => ({ ...prev, email: e.target.value }))}
              style={inputStyle}
              placeholder="cliente@email.com"
            />
          </label>
        </div>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <button
            onClick={identifyCustomer}
            disabled={loadingIdentify || !currentOrderId}
            style={buttonSecondaryStyle}
          >
            {loadingIdentify ? "Salvando..." : "Salvar identificação"}
          </button>

          <button
            onClick={() => setEmailModalOpen(true)}
            disabled={!currentOrderId}
            style={buttonPrimaryStyle}
          >
            Enviar comprovante por email
          </button>
        </div>

        {identifyResp ? (
          <div style={okBoxStyle}>
            <strong>Identificação salva</strong>
            <pre style={jsonBoxStyle}>{JSON.stringify(identifyResp, null, 2)}</pre>
          </div>
        ) : null}

        {receiptCode ? (
          <div style={okBoxStyle}>
            <strong>Receipt Code</strong>
            <div style={{ fontSize: 20, fontWeight: 800 }}>{receiptCode}</div>
          </div>
        ) : null}
      </section>

      {err ? (
        <section style={cardStyle}>
          <h2 style={h2Style}>Erro</h2>
          <pre style={errorBoxStyle}>{String(err)}</pre>
        </section>
      ) : null}

      <EmailReceiptModal
        isOpen={emailModalOpen}
        onClose={() => {
          setEmailModalOpen(false);
          setEmailModalError("");
          setEmailModalSuccess("");
        }}
        onSubmit={handleSendReceiptEmail}
        receiptCode={receiptCode}
        orderId={currentOrderId}
        isLoading={sendingEmail}
        successMessage={emailModalSuccess}
        errorMessage={emailModalError}
      />
    </div>
  );
}

/* =========================
   Styles
========================= */

const pageStyle = {
  minHeight: "100vh",
  background: "#0f172a",
  color: "#f8fafc",
  padding: 20,
  display: "grid",
  gap: 16,
};

const cardStyle = {
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 16,
  padding: 18,
  display: "grid",
  gap: 14,
};

const headerCardStyle = {
  ...cardStyle,
  background: "linear-gradient(135deg, rgba(27,88,131,0.32), rgba(15,23,42,0.85))",
};

const sectionHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  flexWrap: "wrap",
};

const h2Style = {
  margin: 0,
  fontSize: 18,
};

const subtleStyle = {
  opacity: 0.8,
  lineHeight: 1.5,
  fontSize: 14,
};

const fieldGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12,
};

const infoGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
  gap: 10,
  fontSize: 13,
  opacity: 0.95,
};

const labelStyle = {
  display: "grid",
  gap: 8,
  fontSize: 13,
  fontWeight: 600,
};

const inputStyle = {
  width: "100%",
  padding: "12px 14px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.22)",
  background: "#ffffff",
  color: "#0f172a",
  outline: "none",
};

const inputStyleDisabled = {
  ...inputStyle,
  opacity: 0.75,
  cursor: "not-allowed",
};

const textAreaStyle = {
  minHeight: 100,
  width: "100%",
  padding: 12,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "rgba(255,255,255,0.08)",
  color: "#fff",
  resize: "vertical",
};

const buttonPrimaryStyle = {
  padding: "12px 16px",
  borderRadius: 12,
  border: "1px solid rgba(27,88,131,0.44)",
  background: "#1b5883",
  color: "#fff",
  fontWeight: 700,
  cursor: "pointer",
};

const buttonSecondaryStyle = {
  padding: "12px 16px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.18)",
  background: "rgba(255,255,255,0.08)",
  color: "#fff",
  fontWeight: 700,
  cursor: "pointer",
};

const lockerSummaryCardStyle = {
  borderRadius: 14,
  border: "1px solid rgba(255,255,255,0.12)",
  padding: 14,
  background: "rgba(255,255,255,0.04)",
  display: "grid",
  gap: 6,
  fontSize: 13,
};

const slotsGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
  gap: 12,
};

const slotCardStyle = {
  borderRadius: 14,
  padding: 14,
  display: "grid",
  gap: 10,
  textAlign: "left",
};

const slotTopRowStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 10,
};

const slotBadgeStyle = {
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: 0.3,
};

function miniStatusStyle(isSelectable) {
  return {
    fontSize: 11,
    padding: "4px 8px",
    borderRadius: 999,
    background: isSelectable ? "rgba(16,185,129,0.18)" : "rgba(239,68,68,0.18)",
    color: isSelectable ? "#86efac" : "#fca5a5",
    fontWeight: 700,
  };
}

const slotNameStyle = {
  fontSize: 15,
  fontWeight: 700,
};

const slotMetaStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  opacity: 0.9,
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  gap: 16,
};

const okBoxStyle = {
  padding: 14,
  borderRadius: 12,
  background: "rgba(16,185,129,0.16)",
  border: "1px solid rgba(16,185,129,0.34)",
  display: "grid",
  gap: 10,
};

const errorBoxStyle = {
  padding: 14,
  borderRadius: 12,
  background: "rgba(239,68,68,0.16)",
  border: "1px solid rgba(239,68,68,0.34)",
  color: "#fecaca",
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
};

const jsonBoxStyle = {
  margin: 0,
  padding: 12,
  borderRadius: 12,
  background: "rgba(15,23,42,0.78)",
  overflowX: "auto",
  fontSize: 12,
};

const summaryListStyle = {
  display: "grid",
  gap: 4,
  fontSize: 13,
};

const messageStyle = {
  fontSize: 13,
  opacity: 0.95,
};

const pendingCardStyle = {
  padding: 14,
  borderRadius: 12,
  background: "rgba(250,204,21,0.12)",
  border: "1px solid rgba(250,204,21,0.34)",
  display: "grid",
  gap: 12,
};

const infoNoticeStyle = {
  padding: 12,
  borderRadius: 12,
  background: "rgba(255,255,255,0.06)",
  fontSize: 13,
};

const pendingPaymentGridStyle = {
  display: "grid",
  gridTemplateColumns: "220px 1fr",
  gap: 16,
};

const pendingQrPanelStyle = {
  display: "grid",
  placeItems: "center",
  padding: 16,
  borderRadius: 12,
  background: "#fff",
};