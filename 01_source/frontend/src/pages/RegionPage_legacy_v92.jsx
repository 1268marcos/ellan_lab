// 01_source/frontend/src/pages/RegionPage.jsx
// 07/04/2026 - resposta JSON rico para rejected - extractGatewayDebugInfo 
// 09/04/2026 - COM VALIDAÇÃO DE CAMPOS E FLUXO UX PROGRESSIVO

import React, { useEffect, useMemo, useRef, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

import EmailReceiptModal from "../components/EmailReceiptModal.jsx";

import { extractGatewayDebugInfo } from "../features/locker-dashboard/utils/dashboardPaymentUtils.js";

import {
  buildGatewayPaymentPayload,
  buildKioskOrderPayload,
  getDefaultPaymentMethod,
  paymentMethodLabel,
  requiresCustomerPhone,
} from "../utils/paymentProfile";

import CardVirtualKeyboard from "../components/CardVirtualKeyboard.jsx";
import CvvVirtualKeyboard from "../components/CvvVirtualKeyboard.jsx";


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
      ? locker.payment_methods.map((item) => String(item).trim())
      : [],
    address,
    active: Boolean(locker?.active),
  };
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


// Função auxiliar para detectar bandeira
const detectCardBrandGlobal = (cardNumber) => {
  const cleaned = cardNumber.replace(/\D/g, "");
  if (!cleaned) return "";
  
  if (/^62/.test(cleaned) || /^81/.test(cleaned)) return "UNIONPAY";
  if (/^(4011|4312|4389|4514|4576|5041|5067|5090|6277|6362|6363|6504|6505|6506|6507|6508|6509|6516|6550)/.test(cleaned)) return "ELO";
  if (/^(3841|6062|6370|6372|6376|6388|6390|6399)/.test(cleaned)) return "HIPERCARD";
  if (/^50[0-9]/.test(cleaned)) return "AURA";
  if (/^4/.test(cleaned)) return "VISA";
  if (/^5[1-5]/.test(cleaned) || /^2[2-7]/.test(cleaned)) return "MASTERCARD";
  if (/^3[47]/.test(cleaned)) return "AMEX";
  if (/^6(011|5|4[4-9]|22[1-9])/.test(cleaned)) return "DISCOVER";
  if (/^3(0[0-5]|[68])/.test(cleaned)) return "DINERS";
  if (/^35(2[8-9]|[3-8][0-9])/.test(cleaned)) return "JCB";
  if (/^(50|56|57|58|6[0-9])/.test(cleaned)) return "MAESTRO";
  if (/^(60|65|81|82|508|509)/.test(cleaned)) return "RUPAY";
  if (/^([1-9][0-9]{3})/.test(cleaned) && cleaned.length === 16) return "CB";
  if (/^6799/.test(cleaned)) return "GIROCARD";
  if (/^(60|61|62|63|64|65)/.test(cleaned)) return "EFTPOS";
  if (/^45/.test(cleaned)) return "INTERAC";
  if (/^9792/.test(cleaned)) return "TROY";
  if (/^1/.test(cleaned)) return "UATP";
  
  return "";
};



export default function RegionPage({ region, mode = "kiosk" }) {
  const [isCardKeyboardOpen, setIsCardKeyboardOpen] = useState(false);
  
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

  // Estados para controle de fluxo UX
  const [hasSelectedProduct, setHasSelectedProduct] = useState(false);
  const [hasCreatedOrder, setHasCreatedOrder] = useState(false);
  const [hasCompletedPayment, setHasCompletedPayment] = useState(false);
  const [isFormValid, setIsFormValid] = useState(false);

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

  const gatewayDebug = useMemo(
    () => (gatewayPaymentResp ? extractGatewayDebugInfo(gatewayPaymentResp) : null),
    [gatewayPaymentResp]
  );

  const pendingSecondsRemaining = displayedPendingContext?.expires_at_epoch
    ? Math.max(0, Number(displayedPendingContext.expires_at_epoch) - nowEpochSec())
    : null;

  const pendingExpired =
    pendingSecondsRemaining != null && Number(pendingSecondsRemaining) <= 0;

  const [cardData, setCardData] = useState({
    card_number: "",
    cvv: "",
    card_type: "",
    bin: "",
    issuer: "",
  });

  const [isCvvKeyboardOpen, setIsCvvKeyboardOpen] = useState(false);

  // Função de validação do formulário
  const validateForm = useMemo(() => {
    if (!selectedLocker) return false;
    if (!selectedCatalogItem?.sku_id || !selectedCatalogItem?.slot) return false;
    if (!paymentMethod) return false;
    
    switch(paymentMethod) {
      case "PIX":
        return true;
      case "MBWAY":
        return Boolean(paymentExtras.customerPhone && paymentExtras.customerPhone.trim().length > 0);
      case "creditCard":
      case "debitCard":
        return Boolean(cardData.card_number && cardData.card_number.length >= 15 && cardData.cvv && cardData.cvv.length >= 3);
      default:
        return true;
    }
  }, [selectedLocker, selectedCatalogItem, paymentMethod, paymentExtras.customerPhone, cardData.card_number, cardData.cvv]);

  useEffect(() => {
    setIsFormValid(validateForm);
  }, [validateForm]);

  const getValidationMessage = () => {
    if (!selectedLocker) return "Selecione um locker";
    if (!selectedCatalogItem?.sku_id) return "Selecione um produto na vitrine";
    if (!paymentMethod) return "Selecione um método de pagamento";
    
    if (paymentMethod === "MBWAY" && !paymentExtras.customerPhone) {
      return "Digite o telefone para MBWAY";
    }
    
    if ((paymentMethod === "creditCard" || paymentMethod === "debitCard")) {
      if (!cardData.card_number) return "Digite o número do cartão";
      if (!cardData.cvv) return "Digite o CVV do cartão";
      if (cardData.card_number.length < 15) return "Número do cartão incompleto";
      if (cardData.cvv.length < 3) return "CVV incompleto";
    }
    
    return "";
  };


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
    setHasSelectedProduct(false);
    setHasCreatedOrder(false);
    setHasCompletedPayment(false);
    setCreateResp(null);
    setPaymentResp(null);
    setGatewayPaymentResp(null);
    setPendingPaymentContext(null);
    setIdentifyResp(null);
    setIdentifyForm(initialIdentify);
    setPaymentExtras(initialPaymentExtras);
    setErr(null);
  }, [selectedLockerId, selectedLocker, region]);

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
    setHasSelectedProduct(true);
    setHasCreatedOrder(false);
    setHasCompletedPayment(false);
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

    if (!paymentMethod) {
      setErr("Selecione um método de pagamento.");
      return;
    }

    setErr(null);
    setLoadingCreate(true);

    try {
      const payload = {
        region,
        totem_id: totemId,
        sku_id: selectedCatalogItem.sku_id,
        desired_slot: selectedCatalogItem.slot,
        payment_method: paymentMethod,
        customer_phone: paymentExtras.customerPhone || null,
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
      setHasCreatedOrder(true);
      await fetchCatalogSlots(true);
    } catch (e) {
      setErr(String(e?.message || e));
      setHasCreatedOrder(false);
    } finally {
      setLoadingCreate(false);
    }
  }

  async function initiateKioskPayment() {
    if (!currentOrderId) {
      setErr("Crie primeiro um pedido KIOSK.");
      return;
    }

    setErr(null);
    setLoadingGatewayPayment(true);

    try {
      const payload = {
        region,
        order_id: currentOrderId,
        locker_id: totemId,
        slot: selectedCatalogItem.slot,
        payment_method: paymentMethod,
        amount_cents: selectedCatalogItem.amount_cents,
        customer_phone: paymentExtras.customerPhone || null,
        card_type: cardData.card_type || null,
        bin: cardData.bin || null,
        issuer: cardData.issuer || null,
      };

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
        setHasCompletedPayment(false);
        return;
      }

      if (data?.result === "approved" || data?.payment?.status === "APPROVED") {
        await approveKioskPayment();
        setHasCompletedPayment(true);
      }
    } catch (e) {
      setErr(String(e?.message || e));
      setHasCompletedPayment(false);
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
      setHasCompletedPayment(true);
      await fetchCatalogSlots(true);
    } catch (e) {
      setErr(String(e?.message || e));
      setHasCompletedPayment(false);
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
          Tela operacional usando gateway + runtime. Sem backend_sp/backend_pt e sem fallback local no frontend.
        </div>
      </div>

      {/* Indicador de Progresso */}
      <div style={progressBarStyle}>
        <div style={progressStepStyle(hasSelectedProduct)}>
          <span style={progressNumberStyle}>1</span>
          <span style={progressLabelStyle}>Selecionar Produto</span>
          {hasSelectedProduct && <span style={progressCheckStyle}>✓</span>}
        </div>
        <div style={progressLineStyle(hasSelectedProduct)}></div>
        
        <div style={progressStepStyle(hasCreatedOrder)}>
          <span style={progressNumberStyle}>2</span>
          <span style={progressLabelStyle}>Criar Pedido</span>
          {hasCreatedOrder && <span style={progressCheckStyle}>✓</span>}
        </div>
        <div style={progressLineStyle(hasCreatedOrder)}></div>
        
        <div style={progressStepStyle(hasCompletedPayment)}>
          <span style={progressNumberStyle}>3</span>
          <span style={progressLabelStyle}>Pagamento</span>
          {hasCompletedPayment && <span style={progressCheckStyle}>✓</span>}
        </div>
        <div style={progressLineStyle(hasCompletedPayment)}></div>
        
        <div style={progressStepStyle(hasCompletedPayment)}>
          <span style={progressNumberStyle}>4</span>
          <span style={progressLabelStyle}>Comprovante</span>
        </div>
      </div>

      <section style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={h2Style}>0. Seleção da unidade física</h2>
          <button onClick={fetchLockersOnce} disabled={lockersLoading} style={buttonSecondaryStyle}>
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
              <select value={selectedLockerId} onChange={(e) => setSelectedLockerId(e.target.value)} style={inputStyle}>
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
              <div><b>métodos permitidos:</b> {(selectedLocker?.payment_methods || []).join(", ") || "-"}</div>
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
                    border: isSelected ? "2px solid rgba(255,255,255,0.85)" : "1px solid rgba(255,255,255,0.12)",
                    background: isSelected ? "linear-gradient(135deg, rgba(27,88,131,0.35), rgba(27,88,131,0.18))" : isDisabled ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.05)",
                    opacity: isDisabled ? 0.55 : 1,
                    cursor: isDisabled ? "not-allowed" : "pointer",
                  }}
                >
                  <div style={slotTopRowStyle}>
                    <span style={slotBadgeStyle}>Gaveta {item.slot}</span>
                    <span style={miniStatusStyle(isSelectable)}>
                      {item.is_active ? (isSelectable ? "Disponível" : item.locker_state || "Indisponível") : "Inativa"}
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
        {/* SEÇÃO 2 - CRIAR PEDIDO */}
        <section style={{...cardStyle, opacity: hasSelectedProduct ? 1 : 0.6, transition: "opacity 0.3s ease"}}>
          <div style={sectionHeaderStyle}>
            <h2 style={h2Style}>
              2. Criar pedido KIOSK
              {!hasSelectedProduct && <span style={blockedBadgeStyle}>🔒 Selecione um produto primeiro</span>}
            </h2>
          </div>

          {!hasSelectedProduct ? (
            <div style={infoNoticeStyle}>⚠️ Selecione um produto na vitrine acima para liberar esta seção</div>
          ) : (
            <>
              <div style={fieldGridStyle}>
                <label style={labelStyle}>Região <input value={region} disabled style={inputStyleDisabled} /></label>
                <label style={labelStyle}>Locker / Totem ID <input value={totemId} onChange={(e) => setTotemId(e.target.value)} style={inputStyle} /></label>
                <label style={labelStyle}>Gaveta escolhida <input value={selectedCatalogItem?.slot ?? ""} disabled style={inputStyleDisabled} placeholder="Selecione na vitrine" /></label>
                <label style={labelStyle}>SKU escolhido <input value={selectedCatalogItem?.sku_id ?? ""} disabled style={inputStyleDisabled} placeholder="Selecione na vitrine" /></label>
                <label style={labelStyle}>Produto <input value={selectedCatalogItem?.name ?? ""} disabled style={inputStyleDisabled} placeholder="Selecione na vitrine" /></label>
                <label style={labelStyle}>Preço <input value={selectedCatalogItem ? formatMoney(selectedCatalogItem.amount_cents, selectedCatalogItem.currency) : ""} disabled style={inputStyleDisabled} placeholder="Selecione na vitrine" /></label>

                <label style={labelStyle}>
                  Método de pagamento
                  <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} style={inputStyle}>
                    {allowedPaymentMethods.map((method) => (
                      <option key={method} value={method}>{paymentMethodLabel(method)}</option>
                    ))}
                  </select>
                </label>

                {["creditCard", "debitCard"].includes(paymentMethod) && (
                  <div style={cardSectionStyle}>
                    <label style={labelStyle}>💳 Dados do Cartão</label>
                    
                    <button onClick={() => setIsCardKeyboardOpen(true)} style={cardSummaryButton} type="button">
                      <div style={cardSummaryContent}>
                        <div style={cardIconContainer}>
                          {cardData.card_type ? <span style={cardTypeIcon(cardData.card_type)}>{cardData.card_type}</span> : <span style={cardPlaceholderIcon}>💳</span>}
                        </div>
                        <div style={cardDetailsContainer}>
                          <div style={cardNumberDisplay}>
                            {cardData.card_number && cardData.card_number.length > 0 ? (
                              <><span style={cardMaskText}>**** **** **** </span><span style={cardLastDigits}>{cardData.card_number.slice(-4)}</span></>
                            ) : (<span style={cardPlaceholderText}>Digitar número do cartão</span>)}
                          </div>
                          <div style={cardCvvDisplay}>
                            {cardData.cvv && cardData.cvv.length > 0 ? (<><span style={cvvLabel}>CVV:</span><span style={cvvMaskText}>***</span></>) : (<span style={cvvPlaceholder}>Digitar CVV</span>)}
                          </div>
                        </div>
                        <div style={editIconContainer}><span style={editIcon}>✏️</span></div>
                      </div>
                    </button>

                    {cardData.card_number && cardData.card_number.length > 0 && (
                      <button onClick={() => setIsCvvKeyboardOpen(true)} style={{display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", backgroundColor: "rgba(255, 255, 255, 0.05)", border: `1px solid ${cardData.cvv ? "rgba(16, 185, 129, 0.3)" : "rgba(255, 255, 255, 0.15)"}`, borderRadius: "12px", cursor: "pointer", width: "100%"}} type="button">
                        <span style={{fontSize: "18px"}}>🔐</span>
                        <span style={{fontSize: "14px", fontWeight: 600, color: cardData.cvv ? "#10b981" : "#b0b8c5", flex: 1, textAlign: "left", marginLeft: "12px"}}>CVV: {cardData.cvv ? "***" : "Digitar"}</span>
                        <span style={{fontSize: "20px", opacity: 0.6}}>✏️</span>
                      </button>
                    )}

                    {(cardData.card_number || cardData.cvv) && (
                      <div style={cardStatusContainer}>
                        <span style={cardStatusIcon(cardData.card_number && cardData.cvv)}>{cardData.card_number && cardData.cvv ? "✅" : "⚠️"}</span>
                        <span style={cardStatusText}>{cardData.card_number && cardData.cvv ? "Dados do cartão preenchidos" : cardData.card_number ? "Falta o CVV" : "Falta o número do cartão"}</span>
                      </div>
                    )}
                  </div>
                )}

                {paymentMethod === "MBWAY" && (
                  <label style={labelStyle}>
                    Telefone MB WAY
                    <input value={paymentExtras.customerPhone} onChange={(e) => setPaymentExtras((prev) => ({...prev, customerPhone: e.target.value}))} style={inputStyle} placeholder="+351912345678" />
                  </label>
                )}
              </div>

              <button onClick={createKioskOrder} disabled={loadingCreate || !isFormValid} style={{...buttonPrimaryStyle, opacity: (!isFormValid && !loadingCreate) ? 0.5 : 1, cursor: (!isFormValid && !loadingCreate) ? "not-allowed" : "pointer"}}>
                {loadingCreate ? "Criando..." : "Criar pedido KIOSK"}
              </button>

              {!isFormValid && !loadingCreate && getValidationMessage() && (
                <div style={validationMessageStyle}>⚠️ {getValidationMessage()}</div>
              )}

              {createResp && (
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
                  {createResp.payment_payload && Object.keys(createResp.payment_payload).length > 0 && (<pre style={jsonBoxStyle}>{JSON.stringify(createResp.payment_payload, null, 2)}</pre>)}
                  <div style={messageStyle}>{createResp.message}</div>
                </div>
              )}
            </>
          )}
        </section>

        {/* SEÇÃO 3 - PAGAMENTO */}
        <section style={{...cardStyle, opacity: hasCreatedOrder ? 1 : 0.6, transition: "opacity 0.3s ease"}}>
          <div style={sectionHeaderStyle}>
            <h2 style={h2Style}>
              3. Pagamento KIOSK
              {!hasCreatedOrder && hasSelectedProduct && <span style={blockedBadgeStyle}>🔒 Crie o pedido primeiro</span>}
              {!hasSelectedProduct && <span style={blockedBadgeStyle}>🔒 Selecione um produto primeiro</span>}
            </h2>
          </div>

          {!hasCreatedOrder ? (
            <div style={infoNoticeStyle}>⚠️ Crie o pedido no bloco 2 para liberar as opções de pagamento</div>
          ) : (
            <>
              <div style={subtleStyle}>
                Fluxo operacional:<br />1. criar pedido KIOSK<br />2. iniciar pagamento no gateway<br />3. se ficar pendente, mostrar QR/código<br />4. simular conclusão do pagamento
              </div>

              <div style={{marginTop: 12, display: "grid", gap: 6}}>
                <div><b>Pedido atual:</b> {currentOrderId || "nenhum"}</div>
                <div><b>Método atual:</b> {paymentMethod || "-"}</div>
                <div><b>Locker:</b> {totemId || "-"}</div>
                <div><b>Gaveta:</b> {selectedCatalogItem?.slot ?? "-"}</div>
              </div>

              <div style={{display: "flex", gap: 12, flexWrap: "wrap", marginTop: 14}}>
                <button onClick={initiateKioskPayment} disabled={loadingGatewayPayment || !currentOrderId || !isFormValid} style={{...buttonSecondaryStyle, opacity: (!currentOrderId || !isFormValid) ? 0.5 : 1, cursor: (!currentOrderId || !isFormValid) ? "not-allowed" : "pointer"}}>
                  {loadingGatewayPayment ? "Iniciando..." : "Iniciar pagamento no gateway"}
                </button>
                <button onClick={approveKioskPayment} disabled={loadingPayment || !currentOrderId} style={buttonPrimaryStyle}>
                  {loadingPayment ? "Confirmando..." : "Simular pagamento concluído"}
                </button>
              </div>

              {gatewayPaymentResp && (
                <div style={gatewayPaymentResp.result === "rejected" ? rejectedBoxStyle : okBoxStyle}>
                  <strong>Resposta do gateway</strong>
                  <div style={summaryListStyle}>
                    <div><b>result:</b> {gatewayPaymentResp.result || "-"}</div>
                    <div><b>status:</b> {gatewayPaymentResp.payment?.status || "-"}</div>
                    <div><b>gateway_status:</b> {gatewayPaymentResp.payment?.gateway_status || "-"}</div>
                    <div><b>metodo:</b> {gatewayPaymentResp.payment?.metodo || "-"}</div>
                    <div><b>transaction_id:</b> {gatewayPaymentResp.payment?.transaction_id || "-"}</div>
                  </div>
                </div>
              )}

              {displayedPendingContext && (
                <div style={pendingCardStyle}>
                  <strong>{pendingExpired ? "Pagamento pendente expirado" : "Pagamento pendente de ação do cliente"}</strong>
                  <div style={summaryListStyle}>
                    <div><b>origem:</b> {pendingPaymentContext ? "gateway" : "preview local do create_order"}</div>
                    <div><b>método:</b> {displayedPendingContext.method || "-"}</div>
                    <div><b>status:</b> {displayedPendingContext.status || "-"}</div>
                    <div><b>instruction_type:</b> {displayedPendingContext.instruction_type || "-"}</div>
                    <div><b>expira em:</b> {formatEpochDateTime(displayedPendingContext.expires_at_epoch, region)}</div>
                    <div><b>tempo restante:</b> {pendingSecondsRemaining == null ? "-" : formatRemaining(pendingSecondsRemaining)}</div>
                  </div>
                  {displayedPendingContext.instruction && <div style={infoNoticeStyle}>{displayedPendingContext.instruction}</div>}
                  {displayedPendingContext.qr_code_image_base64 && (
                    <div style={pendingPaymentGridStyle}>
                      <div style={pendingQrPanelStyle}><img src={`data:image/png;base64,${displayedPendingContext.qr_code_image_base64}`} alt="QR Code de pagamento" style={{width: 180, height: 180, objectFit: "contain"}} /></div>
                      <div style={{display: "grid", gap: 10}}>
                        <label style={labelStyle}>Código copia-e-cola<textarea readOnly value={displayedPendingContext.copy_paste_code || displayedPendingContext.qr_code_text || ""} style={textAreaStyle} /></label>
                        <button onClick={async () => {await copyText(displayedPendingContext.copy_paste_code || displayedPendingContext.qr_code_text || "");}} style={buttonSecondaryStyle}>Copiar código</button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {paymentResp && (
                <div style={okBoxStyle}>
                  <strong>Pagamento confirmado</strong>
                  <pre style={jsonBoxStyle}>{JSON.stringify(paymentResp, null, 2)}</pre>
                </div>
              )}
            </>
          )}
        </section>
      </div>

      {/* SEÇÃO 4 - IDENTIFICAÇÃO */}
      <section style={{...cardStyle, opacity: hasCompletedPayment ? 1 : 0.6, transition: "opacity 0.3s ease"}}>
        <div style={sectionHeaderStyle}>
          <h2 style={h2Style}>
            4. Identificação / envio de comprovante
            {!hasCompletedPayment && hasCreatedOrder && <span style={blockedBadgeStyle}>🔒 Conclua o pagamento primeiro</span>}
            {!hasCreatedOrder && <span style={blockedBadgeStyle}>🔒 Crie o pedido primeiro</span>}
          </h2>
        </div>

        {!hasCompletedPayment ? (
          <div style={infoNoticeStyle}>⚠️ Finalize o pagamento no bloco 3 para liberar a identificação e envio do comprovante</div>
        ) : (
          <>
            <div style={fieldGridStyle}>
              <label style={labelStyle}>Telefone<input value={identifyForm.phone} onChange={(e) => setIdentifyForm((prev) => ({...prev, phone: e.target.value}))} style={inputStyle} placeholder="+5511999999999 / +351912345678" /></label>
              <label style={labelStyle}>Email<input value={identifyForm.email} onChange={(e) => setIdentifyForm((prev) => ({...prev, email: e.target.value}))} style={inputStyle} placeholder="cliente@email.com" /></label>
            </div>

            <div style={{display: "flex", gap: 12, flexWrap: "wrap"}}>
              <button onClick={identifyCustomer} disabled={loadingIdentify || !currentOrderId} style={buttonSecondaryStyle}>{loadingIdentify ? "Salvando..." : "Salvar identificação"}</button>
              <button onClick={() => setEmailModalOpen(true)} disabled={!currentOrderId} style={buttonPrimaryStyle}>Enviar comprovante por email</button>
            </div>

            {identifyResp && (
              <div style={okBoxStyle}>
                <strong>Identificação salva</strong>
                <pre style={jsonBoxStyle}>{JSON.stringify(identifyResp, null, 2)}</pre>
              </div>
            )}

            {receiptCode && (
              <div style={okBoxStyle}>
                <strong>Receipt Code</strong>
                <div style={{fontSize: 20, fontWeight: 800}}>{receiptCode}</div>
              </div>
            )}
          </>
        )}
      </section>

      {err && (
        <section style={cardStyle}>
          <h2 style={h2Style}>Erro</h2>
          <pre style={errorBoxStyle}>{String(err)}</pre>
        </section>
      )}

      <CardVirtualKeyboard isOpen={isCardKeyboardOpen} value={cardData.card_number} onChange={(formattedNumber) => {
        const cleanNumber = formattedNumber.replace(/\D/g, "");
        const cardType = detectCardBrandGlobal(cleanNumber);
        setCardData(prev => ({...prev, card_number: cleanNumber, bin: cleanNumber.slice(0, 6), card_type: cardType}));
      }} onClose={() => setIsCardKeyboardOpen(false)} />

      <CvvVirtualKeyboard isOpen={isCvvKeyboardOpen} value={cardData.cvv} onChange={(cvvNumber) => {setCardData(prev => ({...prev, cvv: cvvNumber}));}} onClose={() => setIsCvvKeyboardOpen(false)} cardBrand={(() => {const brand = detectCardBrandGlobal(cardData.card_number); return brand ? {cvvLength: brand === "AMEX" ? 4 : 3} : null;})()} />

      <EmailReceiptModal isOpen={emailModalOpen} onClose={() => {setEmailModalOpen(false); setEmailModalError(""); setEmailModalSuccess("");}} onSubmit={handleSendReceiptEmail} receiptCode={receiptCode} orderId={currentOrderId} isLoading={sendingEmail} successMessage={emailModalSuccess} errorMessage={emailModalError} />
    </div>
  );
}

/* =========================
   Styles
========================= */

const pageStyle = { minHeight: "100vh", background: "#0f172a", color: "#f8fafc", padding: 20, display: "grid", gap: 16 };
const cardStyle = { background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 16, padding: 18, display: "grid", gap: 14 };
const headerCardStyle = { ...cardStyle, background: "linear-gradient(135deg, rgba(27,88,131,0.32), rgba(15,23,42,0.85))" };
const sectionHeaderStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" };
const h2Style = { margin: 0, fontSize: 18 };
const subtleStyle = { opacity: 0.8, lineHeight: 1.5, fontSize: 14 };
const fieldGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 };
const infoGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10, fontSize: 13, opacity: 0.95 };
const labelStyle = { display: "grid", gap: 8, fontSize: 13, fontWeight: 600 };
const inputStyle = { width: "100%", padding: "12px 14px", borderRadius: 12, border: "1px solid rgba(255,255,255,0.22)", background: "#ffffff", color: "#0f172a", outline: "none" };
const inputStyleDisabled = { ...inputStyle, opacity: 0.75, cursor: "not-allowed" };
const textAreaStyle = { minHeight: 100, width: "100%", padding: 12, borderRadius: 12, border: "1px solid rgba(255,255,255,0.14)", background: "rgba(255,255,255,0.08)", color: "#fff", resize: "vertical" };
const buttonPrimaryStyle = { padding: "12px 16px", borderRadius: 12, border: "1px solid rgba(27,88,131,0.44)", background: "#1b5883", color: "#fff", fontWeight: 700, cursor: "pointer" };
const buttonSecondaryStyle = { padding: "12px 16px", borderRadius: 12, border: "1px solid rgba(255,255,255,0.18)", background: "rgba(255,255,255,0.08)", color: "#fff", fontWeight: 700, cursor: "pointer" };
const lockerSummaryCardStyle = { borderRadius: 14, border: "1px solid rgba(255,255,255,0.12)", padding: 14, background: "rgba(255,255,255,0.04)", display: "grid", gap: 6, fontSize: 13 };
const slotsGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 12 };
const slotCardStyle = { borderRadius: 14, padding: 14, display: "grid", gap: 10, textAlign: "left" };
const slotTopRowStyle = { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 };
const slotBadgeStyle = { fontSize: 12, fontWeight: 800, letterSpacing: 0.3 };
const miniStatusStyle = (isSelectable) => ({ fontSize: 11, padding: "4px 8px", borderRadius: 999, background: isSelectable ? "rgba(16,185,129,0.18)" : "rgba(239,68,68,0.18)", color: isSelectable ? "#86efac" : "#fca5a5", fontWeight: 700 });
const slotNameStyle = { fontSize: 15, fontWeight: 700 };
const slotMetaStyle = { display: "grid", gap: 4, fontSize: 12, opacity: 0.9 };
const gridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 };
const okBoxStyle = { padding: 14, borderRadius: 12, background: "rgba(16,185,129,0.16)", border: "1px solid rgba(16,185,129,0.34)", display: "grid", gap: 10 };
const rejectedBoxStyle = { padding: 14, borderRadius: 12, background: "rgba(239,68,68,0.16)", border: "1px solid rgba(239,68,68,0.34)", display: "grid", gap: 10 };
const gatewayDebugCardStyle = { padding: 12, borderRadius: 12, background: "rgba(15,23,42,0.42)", border: "1px solid rgba(255,255,255,0.10)", display: "grid", gap: 12 };
const gatewayReasonItemStyle = { padding: 10, borderRadius: 10, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", display: "grid", gap: 4, fontSize: 13 };
const errorBoxStyle = { padding: 14, borderRadius: 12, background: "rgba(239,68,68,0.16)", border: "1px solid rgba(239,68,68,0.34)", color: "#fecaca", whiteSpace: "pre-wrap", wordBreak: "break-word" };
const jsonBoxStyle = { margin: 0, padding: 12, borderRadius: 12, background: "rgba(15,23,42,0.78)", overflowX: "auto", fontSize: 12 };
const summaryListStyle = { display: "grid", gap: 4, fontSize: 13 };
const messageStyle = { fontSize: 13, opacity: 0.95 };
const pendingCardStyle = { padding: 14, borderRadius: 12, background: "rgba(250,204,21,0.12)", border: "1px solid rgba(250,204,21,0.34)", display: "grid", gap: 12 };
const infoNoticeStyle = { padding: 12, borderRadius: 12, background: "rgba(255,255,255,0.06)", fontSize: 13 };
const pendingPaymentGridStyle = { display: "grid", gridTemplateColumns: "220px 1fr", gap: 16 };
const pendingQrPanelStyle = { display: "grid", placeItems: "center", padding: 16, borderRadius: 12, background: "#fff" };
const cardSectionStyle = { gridColumn: "1 / -1", display: "flex", flexDirection: "column", gap: "12px" };
const cardSummaryButton = { width: "100%", padding: "16px", backgroundColor: "rgba(255, 255, 255, 0.05)", border: "2px solid rgba(255, 255, 255, 0.15)", borderRadius: "16px", cursor: "pointer", transition: "all 0.2s ease", textAlign: "left", position: "relative", overflow: "hidden" };
const cardSummaryContent = { display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" };
const cardIconContainer = { flexShrink: 0 };
const cardTypeIcon = (type) => { const colors = { VISA: "#1a73e8", MASTERCARD: "#eb001b", AMEX: "#006fcf", ELO: "#ff6600", HIPERCARD: "#b31b1b", UNIONPAY: "#e60012", JCB: "#1d9a3a", DISCOVER: "#ff6000", DINERS: "#0079c1", AURA: "#f39c12", MAESTRO: "#0099cc", RUPAY: "#6f42c1" }; return { display: "inline-block", padding: "8px 12px", backgroundColor: colors[type] || "#6c757d", borderRadius: "10px", fontSize: "12px", fontWeight: 700, color: "#fff", letterSpacing: "0.5px" }; };
const cardPlaceholderIcon = { display: "inline-block", padding: "8px 12px", backgroundColor: "rgba(255, 255, 255, 0.1)", borderRadius: "10px", fontSize: "20px" };
const cardDetailsContainer = { flex: 1, display: "flex", flexDirection: "column", gap: "8px" };
const cardNumberDisplay = { fontSize: "16px", fontWeight: 600, fontFamily: "monospace", letterSpacing: "1px" };
const cardMaskText = { color: "#b0b8c5" };
const cardLastDigits = { color: "#f5f7fa", fontSize: "18px", fontWeight: 800 };
const cardPlaceholderText = { color: "#8b95a5", fontSize: "14px", fontWeight: 400 };
const cardCvvDisplay = { display: "flex", alignItems: "center", gap: "8px", fontSize: "14px" };
const cvvLabel = { color: "#8b95a5", fontWeight: 600 };
const cvvMaskText = { color: "#f5f7fa", fontWeight: 700, letterSpacing: "1px" };
const cvvPlaceholder = { color: "#8b95a5", fontSize: "13px" };
const editIconContainer = { flexShrink: 0 };
const editIcon = { fontSize: "20px", opacity: 0.6, transition: "opacity 0.2s" };
const cardStatusContainer = { display: "flex", alignItems: "center", gap: "8px", padding: "8px 12px", backgroundColor: "rgba(255, 193, 7, 0.1)", borderRadius: "10px", fontSize: "12px" };
const cardStatusIcon = (isComplete) => ({ fontSize: "14px", color: isComplete ? "#10b981" : "#f59e0b" });
const cardStatusText = { color: "#b0b8c5", fontSize: "12px" };
const validationMessageStyle = { padding: "10px 12px", borderRadius: "10px", background: "rgba(239, 68, 68, 0.16)", border: "1px solid rgba(239, 68, 68, 0.34)", color: "#fecaca", fontSize: "12px", marginTop: "8px" };
const blockedBadgeStyle = { display: "inline-block", marginLeft: "12px", padding: "4px 10px", fontSize: "11px", fontWeight: 500, borderRadius: "20px", background: "rgba(239, 68, 68, 0.2)", color: "#fca5a5", letterSpacing: "0.3px" };
const progressBarStyle = { display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(255,255,255,0.05)", padding: "16px 24px", borderRadius: "12px", marginBottom: "16px", flexWrap: "wrap", gap: "8px" };
const progressStepStyle = (isActive) => ({ display: "flex", alignItems: "center", gap: "8px", padding: "8px 12px", borderRadius: "8px", background: isActive ? "rgba(27, 88, 131, 0.3)" : "rgba(255,255,255,0.05)", border: isActive ? "1px solid rgba(27, 88, 131, 0.5)" : "1px solid rgba(255,255,255,0.1)", position: "relative" });
const progressNumberStyle = { width: "24px", height: "24px", display: "flex", alignItems: "center", justifyContent: "center", background: "#1b5883", borderRadius: "50%", fontSize: "12px", fontWeight: "bold", color: "#fff" };
const progressLabelStyle = { fontSize: "13px", fontWeight: 600, color: "#f8fafc" };
const progressCheckStyle = { color: "#10b981", fontSize: "14px", fontWeight: "bold", marginLeft: "4px" };
const progressLineStyle = (isActive) => ({ flex: 1, height: "2px", background: isActive ? "#1b5883" : "rgba(255,255,255,0.1)", minWidth: "20px" });