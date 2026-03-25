// 01_source/frontend/src/pages/RegionPage.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

import ManualPickupPanel from "../components/ManualPickupPanel.jsx";

import EmailReceiptModal from "../components/EmailReceiptModal.jsx";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const BACKEND_SP =
  import.meta.env.VITE_BACKEND_SP_BASE_URL || "http://localhost:8201";

const BACKEND_PT =
  import.meta.env.VITE_BACKEND_PT_BASE_URL || "http://localhost:8202";

const GATEWAY_BASE =
  import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";

const LOCKER_REGISTRY_FALLBACK = {
  "SP-OSASCO-CENTRO-LK-001": {
    region: "SP",
    site_id: "SP-OSASCO-CENTRO",
    display_name: "ELLAN Locker Osasco Centro 001",
    backend_region: "SP",
    slots: 24,
    channels: ["ONLINE", "KIOSK"],
    payment_methods: ["PIX", "CARTAO", "NFC"],
    address: {
      address: "Rua Primitiva Vianco",
      number: "77",
      additional_information: "Sala 21",
      locality: "Centro",
      city: "Osasco",
      federative_unit: "SP",
      postal_code: "06001-000",
      country: "BR",
    },
    active: true,
  },
  "SP-CARAPICUIBA-JDMARILU-LK-001": {
    region: "SP",
    site_id: "SP-CARAPICUIBA-JDMARILU",
    display_name: "ELLAN Locker Carapicuíba Jardim Marilu 001",
    backend_region: "SP",
    slots: 24,
    channels: ["ONLINE", "KIOSK"],
    payment_methods: ["PIX", "CARTAO", "NFC"],
    address: {
      address: "Estrada Aldeinha",
      number: "7509",
      additional_information: "Apto 45",
      locality: "Jardim Marilu",
      city: "Carapicuíba",
      federative_unit: "SP",
      postal_code: "06343-040",
      country: "BR",
    },
    active: true,
  },
  "PT-MAIA-CENTRO-LK-001": {
    region: "PT",
    site_id: "PT-MAIA-CENTRO",
    display_name: "ELLAN Locker Maia Centro 001",
    backend_region: "PT",
    slots: 24,
    channels: ["ONLINE", "KIOSK"],
    payment_methods: ["CARTAO", "MBWAY", "MULTIBANCO_REFERENCE", "NFC"],
    address: {
      address: "Rua Padre Antonio",
      number: "12",
      additional_information: "",
      locality: "Centro",
      city: "Maia",
      federative_unit: "Porto",
      postal_code: "4400-001",
      country: "PT",
    },
    active: true,
  },
  "PT-GUIMARAES-AZUREM-LK-001": {
    region: "PT",
    site_id: "PT-GUIMARAES-AZUREM",
    display_name: "ELLAN Locker Guimarães Azurém 001",
    backend_region: "PT",
    slots: 24,
    channels: ["ONLINE", "KIOSK"],
    payment_methods: ["CARTAO", "MBWAY", "MULTIBANCO_REFERENCE", "NFC"],
    address: {
      address: "Rua Dona Maria",
      number: "258",
      additional_information: "Sub-cave",
      locality: "Azurém",
      city: "Guimarães",
      federative_unit: "Braga",
      postal_code: "4582-052",
      country: "PT",
    },
    active: true,
  },
};

const initialIdentify = {
  phone: "",
  email: "",
};

const initialPaymentExtras = {
  cardType: "",
  customerPhone: "",
};

function extractReceiptCodeFromPaymentResp(paymentResp) {
  if (!paymentResp) return null;

  return (
    paymentResp?.fiscal?.receipt_code ||
    paymentResp?.receipt_code ||
    null
  );
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

  return {
    locker_id: String(locker?.locker_id || "").trim(),
    region: String(locker?.region || "").toUpperCase(),
    site_id: locker?.site_id || "",
    display_name: locker?.display_name || locker?.locker_id || "",
    backend_region: String(locker?.backend_region || locker?.region || "").toUpperCase(),
    slots: Number(locker?.slots || 24),
    channels: Array.isArray(locker?.channels) ? locker.channels.map(String) : [],
    payment_methods: Array.isArray(locker?.payment_methods)
      ? locker.payment_methods.map((item) => String(item).toUpperCase())
      : [],
    address,
    active: Boolean(locker?.active),
  };
}

function buildFallbackLockersByRegion(region) {
  return Object.entries(LOCKER_REGISTRY_FALLBACK)
    .map(([lockerId, config]) =>
      normalizeLockerItem({
        locker_id: lockerId,
        ...config,
      })
    )
    .filter((item) => item.region === region && item.active)
    .sort((a, b) => a.display_name.localeCompare(b.display_name));
}

function getBackendBaseByRegion(region) {
  return region === "SP" ? BACKEND_SP : BACKEND_PT;
}

function getDefaultPaymentMethod(locker, region) {
  const methods = Array.isArray(locker?.payment_methods) ? locker.payment_methods : [];
  if (methods.length > 0) return methods[0];
  return region === "PT" ? "MBWAY" : "PIX";
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
  if (gatewayPendingContext) {
    return gatewayPendingContext;
  }

  const preview = createResp?.payment_payload || null;
  const instructionType = createResp?.payment_instruction_type || null;
  const paymentStatus = createResp?.payment_status || null;

  if (!preview || !instructionType) {
    return null;
  }

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

  const [printModalOpen, setPrintModalOpen] = useState(false);
  const [printCountdown, setPrintCountdown] = useState(10);
  const [printPhase, setPrintPhase] = useState("idle"); // idle | printing | ready
  const printTimerRef = useRef(null);
  const printCloseTimerRef = useRef(null);

  const backendBase = getBackendBaseByRegion(selectedLocker?.backend_region || region);

  const createUrl = useMemo(() => `${ORDER_PICKUP_BASE}/kiosk/orders`, []);
  const identifyUrl = useMemo(() => `${ORDER_PICKUP_BASE}/kiosk/identify`, []);
  const gatewayPaymentUrl = useMemo(() => `${GATEWAY_BASE}/gateway/pagamento`, []);
  const catalogSlotsUrl = useMemo(() => `${backendBase}/catalog/slots`, [backendBase]);
  const lockerSlotsUrl = useMemo(() => `${backendBase}/locker/slots`, [backendBase]);

  const currentOrderId = createResp?.order_id || null;
  const allowedPaymentMethods = selectedLocker?.payment_methods || [];

  const receiptCode = extractReceiptCodeFromPaymentResp(paymentResp);

  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailModalSuccess, setEmailModalSuccess] = useState("");
  const [emailModalError, setEmailModalError] = useState("");

  // Adicione esta função para lidar com o envio do email
  const handleSendReceiptEmail = async (email) => {
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
          email: email,
        }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(
          data?.detail
            ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))
            : JSON.stringify(data)
        );
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
  };





  const displayedPendingContext = useMemo(
    () => resolveDisplayedPendingContext(pendingPaymentContext, createResp, paymentMethod),
    [pendingPaymentContext, createResp, paymentMethod]
  );

  const pendingSecondsRemaining = displayedPendingContext?.expires_at_epoch
    ? Math.max(0, Number(displayedPendingContext.expires_at_epoch) - nowEpochSec())
    : null;

  const pendingExpired =
    pendingSecondsRemaining != null && Number(pendingSecondsRemaining) <= 0;

  const hasQrLikeContent = Boolean(
    displayedPendingContext?.qr_code_text ||
      displayedPendingContext?.copy_paste_code ||
      displayedPendingContext?.qr_code_image_base64
  );

  async function fetchLockersOnce() {
    setLockersLoading(true);
    setLockersError("");

    try {
      const res = await fetch(
        `${GATEWAY_BASE}/lockers?region=${encodeURIComponent(region)}&active_only=true`
      );
      const text = await res.text();

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const data = JSON.parse(text);
      const items = Array.isArray(data?.items) ? data.items.map(normalizeLockerItem) : [];

      if (!items.length) {
        throw new Error(`Nenhum locker ativo retornado pelo gateway para a região ${region}.`);
      }

      setAvailableLockers(items);
      setLockersSource("gateway");
    } catch (e) {
      const fallbackItems = buildFallbackLockersByRegion(region);
      setAvailableLockers(fallbackItems);
      setLockersSource("fallback");
      setLockersError(`Falha ao carregar lockers do gateway: ${String(e?.message || e)}`);
    } finally {
      setLockersLoading(false);
    }
  }

  useEffect(() => {
    return () => {
      clearPrintSimulationTimers();
    };
  }, []);

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
      if (prev && allowedPaymentMethods.includes(prev)) {
        return prev;
      }
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

      if (paymentMethod !== "CARTAO") {
        next.cardType = "";
      }

      if (paymentMethod !== "MBWAY") {
        next.customerPhone = "";
      }

      return next;
    });
  }, [paymentMethod]);

  useEffect(() => {
    fetchCatalogSlots();

    if (pollRef.current) {
      clearInterval(pollRef.current);
    }

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
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [catalogSlotsUrl, lockerSlotsUrl, selectedLockerId]);

  useEffect(() => {
    if (!displayedPendingContext?.expires_at_epoch) return;

    const interval = setInterval(() => {
      setTick((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [displayedPendingContext?.expires_at_epoch]);

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
      const [catalogRes, lockerRes] = await Promise.all([
        fetch(catalogSlotsUrl, {
          headers: { "X-Locker-Id": selectedLocker.locker_id },
        }),
        fetch(lockerSlotsUrl, {
          headers: { "X-Locker-Id": selectedLocker.locker_id },
        }),
      ]);

      const catalogData = await catalogRes.json().catch(() => []);
      const lockerData = await lockerRes.json().catch(() => []);

      if (!catalogRes.ok) {
        throw new Error(
          typeof catalogData?.detail !== "undefined"
            ? JSON.stringify(catalogData.detail)
            : JSON.stringify(catalogData)
        );
      }

      if (!lockerRes.ok) {
        throw new Error(
          typeof lockerData?.detail !== "undefined"
            ? JSON.stringify(lockerData.detail)
            : JSON.stringify(lockerData)
        );
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
    if (!isCatalogItemSelectable(item)) {
      return;
    }

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
      setErr(
        "A gaveta selecionada não está disponível operacionalmente. Escolha uma gaveta AVAILABLE."
      );
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
      const payload = {
        region,
        totem_id: totemId,
        sku_id: selectedCatalogItem.sku_id,
        desired_slot: Number(selectedCatalogItem.slot),
        payment_method: paymentMethod,
        card_type: paymentMethod === "CARTAO" ? paymentExtras.cardType : undefined,
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
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
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

    if (paymentMethod === "CARTAO" && !paymentExtras.cardType) {
      setErr("Escolha se o cartão é crédito ou débito.");
      return;
    }

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
      const payload = {
        regiao: region,
        canal: "KIOSK",
        metodo: paymentMethod,
        valor: Number((Number(selectedCatalogItem.amount_cents || 0) / 100).toFixed(2)),
        porta: Number(selectedCatalogItem.slot),
        locker_id: totemId,
        order_id: currentOrderId,
      };

      if (paymentMethod === "CARTAO") {
        payload.card_type = paymentExtras.cardType;
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

      const deviceFp = getOrCreateDeviceFingerprint();
      const idemKey = generateIdempotencyKey();

      const res = await fetch(gatewayPaymentUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idemKey,
          "X-Device-Fingerprint": deviceFp,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
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
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
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
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }

      setIdentifyResp(data);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingIdentify(false);
    }
  }

  function clearPrintSimulationTimers() {
    if (printTimerRef.current) {
      clearInterval(printTimerRef.current);
      printTimerRef.current = null;
    }

    if (printCloseTimerRef.current) {
      clearTimeout(printCloseTimerRef.current);
      printCloseTimerRef.current = null;
    }
  }

  function closePrintSimulation() {
    clearPrintSimulationTimers();
    setPrintModalOpen(false);
    setPrintCountdown(10);
    setPrintPhase("idle");
  }

  function startPrintSimulation() {
    if (!receiptCode) {
      setErr("Comprovante fiscal indisponível para impressão.");
      return;
    }

    clearPrintSimulationTimers();
    setErr(null);
    setPrintCountdown(10);
    setPrintPhase("printing");
    setPrintModalOpen(true);

    printTimerRef.current = setInterval(() => {
      setPrintCountdown((prev) => {
        if (prev <= 1) {
          clearPrintSimulationTimers();
          setPrintPhase("ready");

          printCloseTimerRef.current = setTimeout(() => {
            closePrintSimulation();
          }, 2000);

          return 0;
        }

        return prev - 1;
      });
    }, 1000);
  }

  return (
    <div style={pageStyle}>
      <div style={headerCardStyle}>
        <h1 style={{ margin: 0 }}>Simulador KIOSK — {region}</h1>
        <div style={subtleStyle}>
          Esta tela continua como simulador operacional de KIOSK. Agora ela busca
          a lista de unidades no endpoint real do gateway e usa fallback local apenas se houver falha.
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
            Nenhum locker ativo foi encontrado para a região {region}.
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
              <div><b>fonte:</b> {lockersSource === "gateway" ? "gateway /lockers" : "fallback local"}</div>
              <div><b>locker_id:</b> {selectedLocker?.locker_id || "-"}</div>
              <div><b>site_id:</b> {selectedLocker?.site_id || "-"}</div>
              <div><b>backend_region:</b> {selectedLocker?.backend_region || "-"}</div>
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
          <h2 style={h2Style}>1. Vitrine KIOSK — 24 gavetas</h2>
          <button onClick={fetchCatalogSlots} disabled={catalogLoading} style={buttonSecondaryStyle}>
            {catalogLoading ? "Atualizando..." : "Atualizar vitrine"}
          </button>
        </div>

        <div style={infoGridStyle}>
          <div><b>Região:</b> {region}</div>
          <div><b>Locker selecionado:</b> {selectedLocker?.locker_id || "-"}</div>
          <div><b>Backend catálogo:</b> {backendBase}</div>
          <div><b>Endpoint catálogo:</b> {catalogSlotsUrl}</div>
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
              <input
                value={totemId}
                onChange={(e) => setTotemId(e.target.value)}
                style={inputStyle}
              />
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
                    {method === "CARTAO"
                      ? "CARTÃO"
                      : method === "MULTIBANCO_REFERENCE"
                        ? "REFERÊNCIA MULTIBANCO"
                        : method}
                  </option>
                ))}
              </select>
            </label>

            {paymentMethod === "CARTAO" ? (
              <label style={labelStyle}>
                Tipo do cartão
                <select
                  value={paymentExtras.cardType}
                  onChange={(e) =>
                    setPaymentExtras((prev) => ({ ...prev, cardType: e.target.value }))
                  }
                  style={inputStyle}
                >
                  <option value="">Selecione</option>
                  <option value="creditCard">Crédito</option>
                  <option value="debitCard">Débito</option>
                </select>
              </label>
            ) : null}

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

              {createResp.payment_payload &&
              Object.keys(createResp.payment_payload).length > 0 ? (
                <pre style={jsonBoxStyle}>
                  {JSON.stringify(createResp.payment_payload, null, 2)}
                </pre>
              ) : null}

              <div style={messageStyle}>{createResp.message}</div>
            </div>
          )}
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
            <div
              style={{
                ...pendingCardStyle,
                ...(pendingExpired ? expiredPendingCardStyle : null),
              }}
            >
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
                <div style={infoNoticeStyle}>
                  {displayedPendingContext.instruction}
                </div>
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
                          try {
                            await copyText(
                              displayedPendingContext.copy_paste_code ||
                                displayedPendingContext.qr_code_text ||
                                ""
                            );
                            setErr(null);
                          } catch (e) {
                            setErr(`Falha ao copiar código: ${String(e?.message || e)}`);
                          }
                        }}
                        style={buttonSecondaryStyle}
                      >
                        Copiar código
                      </button>

                      <button
                        onClick={() => {
                          setErr(JSON.stringify(displayedPendingContext.raw, null, 2));
                        }}
                        style={buttonSecondaryStyle}
                      >
                        Ver JSON bruto
                      </button>
                    </div>
                  </div>
                </div>
              ) : displayedPendingContext.qr_code_text ? (
                <div style={pendingPaymentGridStyle}>
                  <div style={pendingQrPanelStyle}>
                    <QRCodeCanvas
                      value={displayedPendingContext.qr_code_text}
                      size={180}
                      includeMargin={true}
                    />
                  </div>

                  <div style={{ display: "grid", gap: 10 }}>
                    <label style={labelStyle}>
                      Código copia-e-cola
                      <textarea
                        readOnly
                        value={
                          displayedPendingContext.copy_paste_code ||
                          displayedPendingContext.qr_code_text
                        }
                        style={textAreaStyle}
                      />
                    </label>

                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                      <button
                        onClick={async () => {
                          try {
                            await copyText(
                              displayedPendingContext.copy_paste_code ||
                                displayedPendingContext.qr_code_text
                            );
                            setErr(null);
                          } catch (e) {
                            setErr(`Falha ao copiar código: ${String(e?.message || e)}`);
                          }
                        }}
                        style={buttonSecondaryStyle}
                      >
                        Copiar código
                      </button>

                      <button
                        onClick={() => {
                          setErr(JSON.stringify(displayedPendingContext.raw, null, 2));
                        }}
                        style={buttonSecondaryStyle}
                      >
                        Ver JSON bruto
                      </button>
                    </div>
                  </div>
                </div>
              ) : displayedPendingContext.copy_paste_code ? (
                <div style={{ display: "grid", gap: 10 }}>
                  <label style={labelStyle}>
                    Código / referência
                    <textarea
                      readOnly
                      value={displayedPendingContext.copy_paste_code}
                      style={textAreaStyle}
                    />
                  </label>

                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <button
                      onClick={async () => {
                        try {
                          await copyText(displayedPendingContext.copy_paste_code);
                          setErr(null);
                        } catch (e) {
                          setErr(`Falha ao copiar código: ${String(e?.message || e)}`);
                        }
                      }}
                      style={buttonSecondaryStyle}
                    >
                      Copiar código
                    </button>

                    <button
                      onClick={() => {
                        setErr(JSON.stringify(displayedPendingContext.raw, null, 2));
                      }}
                      style={buttonSecondaryStyle}
                    >
                      Ver JSON bruto
                    </button>
                  </div>
                </div>
              ) : displayedPendingContext.instruction_type === "DISPLAY_QR" ? (
                <div style={warningNoticeStyle}>
                  O gateway indicou fluxo de QR, mas ainda não devolveu
                  `qr_code_text` / `qr_code_image_base64` / `copy_paste_code`.
                  Isso indica inconsistência do payload retornado.
                </div>
              ) : null}

              {displayedPendingContext.instruction_type === "PHONE_APPROVAL" &&
              displayedPendingContext.customer_phone ? (
                <div style={infoNoticeStyle}>
                  Telefone informado para aprovação: {displayedPendingContext.customer_phone}
                </div>
              ) : null}

              {displayedPendingContext.instruction_type === "DISPLAY_REFERENCE" &&
              displayedPendingContext.amount_cents != null ? (
                <div style={infoNoticeStyle}>
                  Valor associado à referência:{" "}
                  {formatMoney(
                    displayedPendingContext.amount_cents,
                    region === "SP" ? "BRL" : "EUR"
                  )}
                </div>
              ) : null}

              {!pendingExpired ? (
                <div style={warningNoticeStyle}>
                  Enquanto o pagamento estiver pendente, a gaveta deve permanecer reservada.
                  A liberação automática deve ocorrer no backend ao fim do prazo.
                </div>
              ) : (
                <div style={expiredNoticeStyle}>
                  O prazo exibido para este pagamento já expirou. A gaveta deve ser liberada
                  automaticamente pelo backend/lifecycle. Atualize a vitrine e valide se o slot
                  voltou para `AVAILABLE`.
                </div>
              )}

              {!hasQrLikeContent && !displayedPendingContext.instruction ? (
                <div style={warningNoticeStyle}>
                  O pagamento entrou em estado pendente, mas sem dados suficientes para exibição
                  operacional ao cliente.
                </div>
              ) : null}
            </div>
          ) : null}

          {paymentResp && (
            <div style={okBoxStyle}>
              <strong>Pagamento aprovado</strong>

              <div style={summaryListStyle}>
                <div><b>order_id:</b> {paymentResp.order_id}</div>
                <div><b>allocation_id:</b> {paymentResp.allocation_id}</div>
                <div><b>slot:</b> {paymentResp.slot}</div>
                <div><b>status:</b> {paymentResp.status}</div>
                <div><b>payment_method:</b> {paymentResp.payment_method || "-"}</div>
                <div><b>comprovante:</b> {receiptCode || "-"}</div>
              </div>

              {receiptCode ? (
                <div style={{ marginTop: 16, display: "grid", gap: 16 }}>
                  <div style={receiptTerminalBoxStyle}>
                    <div style={receiptTerminalTitleStyle}>Comprovante fiscal</div>

                    <div style={receiptCodeBigStyle}>
                      {receiptCode}
                    </div>

                    <div style={receiptQrPanelStyle}>
                      <QRCodeCanvas
                        value={receiptCode}
                        size={180}
                        includeMargin={true}
                      />
                    </div>

                    <div style={receiptTerminalHelpStyle}>
                      Fotografe este código ou o QRCode para consultar o comprovante depois.
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <button
                      type="button"
                      onClick={startPrintSimulation}
                      style={buttonPrimaryStyle}
                      disabled={printModalOpen}
                    >
                      {printModalOpen ? "Imprimindo..." : "Imprimir comprovante"}
                    </button>

                    {/*<button
                      type="button"
                      onClick={() =>
                        setIdentifyResp({
                          ok: true,
                          message:
                            "Informe email ou telefone abaixo para receber o comprovante depois.",
                        })
                      }
                      style={buttonSecondaryStyle}
                    >
                      Receber por email/SMS
                    </button> */}

                    <button
                      type="button"
                      onClick={() => {
                        setEmailModalError("");
                        setEmailModalSuccess("");
                        setEmailModalOpen(true);
                      }}
                      style={buttonSecondaryStyle}
                    >
                      Receber por email/SMS
                    </button>




                    <button
                      type="button"
                      onClick={() =>
                        window.open(
                          `${ORDER_PICKUP_BASE}/public/fiscal/by-code/${encodeURIComponent(receiptCode)}`,
                          "_blank",
                          "noopener,noreferrer"
                        )
                      }
                      style={buttonSecondaryStyle}
                    >
                      Ver JSON
                    </button>
                  </div>
                </div>
              ) : null}

              <div style={messageStyle}>{paymentResp.message}</div>
            </div>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={h2Style}>4. Identificação opcional</h2>

          <div style={subtleStyle}>
            Informe telefone ou email se desejar receber depois o código do comprovante fiscal
            para consulta e impressão posterior. Esta etapa é opcional e não deve bloquear a operação.
          </div>

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
            {loadingIdentify ? "Registrando..." : "Registrar identificação / receber comprovante fiscal depois"}
          </button>

          {identifyResp && (
            <div style={okBoxStyle}>
              <strong>Identificação registrada</strong>
              <div style={messageStyle}>{identifyResp.message}</div>
            </div>
          )}
        </section>


        <section style={cardStyle}>
          <h2 style={h2Style}>Retirada por código manual</h2>
          <div style={summaryListStyle}>
            <ManualPickupPanel
              region={region}
              lockerId={selectedLockerId}
              apiBase="/api/op"
              onRedeemed={(data) => {
                console.log("Retirada manual concluída:", data);
              }}
            />
          </div>
        </section>

      </div>

      <section style={cardStyle}>
        <h2 style={h2Style}>Configuração desta tela</h2>
        <div style={summaryListStyle}>
          <div><b>mode:</b> {mode}</div>
          <div><b>ORDER_PICKUP_BASE:</b> {ORDER_PICKUP_BASE}</div>
          <div><b>GATEWAY_BASE:</b> {GATEWAY_BASE}</div>
          <div><b>gatewayPaymentUrl:</b> {gatewayPaymentUrl}</div>
          <div><b>backendBase:</b> {backendBase}</div>
          <div><b>catalogSlotsUrl:</b> {catalogSlotsUrl}</div>
          <div><b>createUrl:</b> {createUrl}</div>
          <div><b>identifyUrl:</b> {identifyUrl}</div>
          <div><b>locker selecionado:</b> {selectedLocker?.locker_id || "-"}</div>
          <div><b>fonte dos lockers:</b> {lockersSource === "gateway" ? "gateway /lockers" : "fallback local"}</div>
        </div>
      </section>


      {printModalOpen ? (
        <div style={printModalOverlayStyle}>
          <div style={printModalCardStyle}>
            <div style={printModalHeaderStyle}>
              <div style={printModalTitleStyle}>Simulação de impressão</div>

              <button
                type="button"
                onClick={closePrintSimulation}
                style={printModalCloseButtonStyle}
              >
                Fechar
              </button>
            </div>

            <div style={printTicketStyle}>
              <div style={printTicketBrandStyle}>ELLAN LAB LOCKER</div>
              <div style={printTicketLineStyle}>COMPROVANTE FISCAL</div>
              <div style={printTicketDividerStyle} />

              <div style={printTicketRowStyle}>
                <span>Região</span>
                <strong>{region}</strong>
              </div>

              <div style={printTicketRowStyle}>
                <span>Locker</span>
                <strong>{totemId || "-"}</strong>
              </div>

              <div style={printTicketRowStyle}>
                <span>Pedido</span>
                <strong>{paymentResp?.order_id || "-"}</strong>
              </div>

              <div style={printTicketRowStyle}>
                <span>Slot</span>
                <strong>{paymentResp?.slot ?? "-"}</strong>
              </div>

              <div style={printTicketRowStyle}>
                <span>Método</span>
                <strong>{paymentResp?.payment_method || "-"}</strong>
              </div>

              <div style={printTicketRowStyle}>
                <span>Valor</span>
                <strong>
                  {selectedCatalogItem
                    ? formatMoney(selectedCatalogItem.amount_cents, selectedCatalogItem.currency)
                    : "-"}
                </strong>
              </div>

              <div style={printTicketRowStyle}>
                <span>Data/hora</span>
                <strong>{new Date().toLocaleString(region === "SP" ? "pt-BR" : "pt-PT")}</strong>
              </div>

              <div style={printTicketDividerStyle} />

              <div style={printTicketReceiptLabelStyle}>CÓDIGO DO COMPROVANTE</div>
              <div style={printTicketReceiptCodeStyle}>{receiptCode}</div>

              <div style={printTicketQrBoxStyle}>
                <QRCodeCanvas
                  value={receiptCode}
                  size={120}
                  includeMargin={true}
                />
              </div>
            </div>

            {printPhase === "printing" ? (
              <div style={printStatusBoxStyle}>
                <div style={printStatusTitleStyle}>
                  Imprimindo comprovante...
                </div>
                <div style={printStatusCountdownStyle}>
                  {printCountdown}s
                </div>
              </div>
            ) : (
              <div style={printReadyBoxStyle}>
                RETIRE O COMPROVANTE IMPRESSO
              </div>
            )}
          </div>
        </div>
      ) : null}


      {/* Modal para envio de email do comprovante */}
      <EmailReceiptModal
        isOpen={emailModalOpen}
        onClose={() => {
          setEmailModalOpen(false);
          setSendingEmail(false);
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

      {err && <pre style={errorBoxStyle}>{err}</pre>}
    </div>
  );
}

const pageStyle = {
  padding: 24,
  maxWidth: 1200,
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

const infoGridStyle = {
  display: "grid",
  gap: 8,
  fontSize: 13,
  marginBottom: 14,
  opacity: 0.88,
};

const slotsGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
  gap: 12,
};

const slotCardStyle = {
  borderRadius: 14,
  padding: 12,
  textAlign: "left",
  color: "#f5f7fa",
  minHeight: 150,
};

const slotTopRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  marginBottom: 10,
};

const slotBadgeStyle = {
  display: "inline-flex",
  padding: "4px 8px",
  borderRadius: 999,
  background: "rgba(255,255,255,0.10)",
  border: "1px solid rgba(255,255,255,0.12)",
  fontSize: 12,
  fontWeight: 700,
};

function miniStatusStyle(active) {
  return {
    display: "inline-flex",
    padding: "4px 8px",
    borderRadius: 999,
    background: active ? "rgba(31,122,63,0.18)" : "rgba(179,38,30,0.18)",
    border: active ? "1px solid rgba(31,122,63,0.38)" : "1px solid rgba(179,38,30,0.38)",
    fontSize: 11,
    fontWeight: 700,
  };
}

const slotNameStyle = {
  fontSize: 16,
  fontWeight: 700,
  marginBottom: 10,
  lineHeight: 1.3,
};

const slotMetaStyle = {
  display: "grid",
  gap: 6,
  fontSize: 13,
  opacity: 0.92,
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

const lockerSummaryCardStyle = {
  padding: 12,
  borderRadius: 12,
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.08)",
  display: "grid",
  gap: 6,
  fontSize: 14,
};

const sectionHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  flexWrap: "wrap",
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

const pendingCardStyle = {
  marginTop: 16,
  padding: 12,
  borderRadius: 12,
  background: "rgba(27,88,131,0.12)",
  border: "1px solid rgba(27,88,131,0.35)",
  display: "grid",
  gap: 12,
};

const expiredPendingCardStyle = {
  background: "rgba(179,38,30,0.12)",
  border: "1px solid rgba(179,38,30,0.35)",
};

const pendingPaymentGridStyle = {
  display: "grid",
  gridTemplateColumns: "minmax(180px, 220px) 1fr",
  gap: 12,
  alignItems: "start",
};

const pendingQrPanelStyle = {
  padding: 12,
  borderRadius: 12,
  background: "#ffffff",
  display: "grid",
  placeItems: "center",
};

const infoNoticeStyle = {
  padding: 10,
  borderRadius: 10,
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.10)",
  fontSize: 13,
};

const warningNoticeStyle = {
  padding: 10,
  borderRadius: 10,
  background: "rgba(199,146,0,0.14)",
  border: "1px solid rgba(199,146,0,0.30)",
  fontSize: 13,
};

const expiredNoticeStyle = {
  padding: 10,
  borderRadius: 10,
  background: "rgba(179,38,30,0.14)",
  border: "1px solid rgba(179,38,30,0.30)",
  fontSize: 13,
};

const textAreaStyle = {
  minHeight: 120,
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
  resize: "vertical",
};

const errorBoxStyle = {
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};

const jsonBoxStyle = {
  marginTop: 12,
  background: "#0b0f14",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 12,
  padding: 12,
  overflow: "auto",
  fontSize: 12,
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

const receiptTerminalBoxStyle = {
  padding: 14,
  borderRadius: 12,
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.10)",
  display: "grid",
  justifyItems: "center",
  textAlign: "center",
  gap: 12,
};

const receiptTerminalTitleStyle = {
  fontSize: 16,
  fontWeight: 700,
};

const receiptCodeBigStyle = {
  fontSize: 22,
  fontWeight: 800,
  letterSpacing: 1,
  padding: "10px 14px",
  borderRadius: 10,
  background: "rgba(255,255,255,0.08)",
  border: "1px dashed rgba(255,255,255,0.25)",
  wordBreak: "break-word",
};

const receiptQrPanelStyle = {
  padding: 12,
  borderRadius: 12,
  background: "#ffffff",
  display: "grid",
  placeItems: "center",
};

const receiptTerminalHelpStyle = {
  fontSize: 13,
  opacity: 0.85,
  maxWidth: 320,
  lineHeight: 1.4,
};

const printModalOverlayStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.78)",
  display: "grid",
  placeItems: "center",
  zIndex: 9999,
  padding: 24,
};

const printModalCardStyle = {
  width: "100%",
  maxWidth: 420,
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 18,
  boxShadow: "0 18px 48px rgba(0,0,0,0.45)",
  padding: 18,
  display: "grid",
  gap: 16,
};

const printModalHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
};

const printModalTitleStyle = {
  fontSize: 18,
  fontWeight: 700,
};

const printModalCloseButtonStyle = {
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#1b5883",
  color: "#fff",
  cursor: "pointer",
  fontWeight: 600,
};

const printTicketStyle = {
  background: "#ffffff",
  color: "#111",
  borderRadius: 12,
  padding: 14,
  display: "grid",
  gap: 8,
  fontFamily: '"Courier New", monospace',
  fontSize: 12,
};

const printTicketBrandStyle = {
  textAlign: "center",
  fontSize: 14,
  fontWeight: 700,
};

const printTicketLineStyle = {
  textAlign: "center",
  fontSize: 12,
};

const printTicketDividerStyle = {
  borderTop: "1px dashed #999",
  margin: "4px 0",
};

const printTicketRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
};

const printTicketReceiptLabelStyle = {
  textAlign: "center",
  fontSize: 11,
  marginTop: 4,
};

const printTicketReceiptCodeStyle = {
  textAlign: "center",
  fontSize: 16,
  fontWeight: 700,
  letterSpacing: 1,
  wordBreak: "break-word",
};

const printTicketQrBoxStyle = {
  display: "grid",
  placeItems: "center",
  marginTop: 8,
};

const printStatusBoxStyle = {
  borderRadius: 12,
  padding: 14,
  background: "rgba(27,88,131,0.16)",
  border: "1px solid rgba(27,88,131,0.34)",
  textAlign: "center",
};

const printStatusTitleStyle = {
  fontSize: 16,
  fontWeight: 700,
};

const printStatusCountdownStyle = {
  marginTop: 6,
  fontSize: 26,
  fontWeight: 800,
};

const printReadyBoxStyle = {
  borderRadius: 12,
  padding: 16,
  background: "rgba(31,122,63,0.18)",
  border: "1px solid rgba(31,122,63,0.36)",
  textAlign: "center",
  fontSize: 18,
  fontWeight: 800,
  letterSpacing: 0.4,
};