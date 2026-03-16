import React, { useEffect, useMemo, useRef, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

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

// Utilitários (mantidos iguais)
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

  const backendBase = getBackendBaseByRegion(selectedLocker?.backend_region || region);

  const createUrl = useMemo(() => `${ORDER_PICKUP_BASE}/kiosk/orders`, []);
  const identifyUrl = useMemo(() => `${ORDER_PICKUP_BASE}/kiosk/identify`, []);
  const gatewayPaymentUrl = useMemo(() => `${GATEWAY_BASE}/gateway/pagamento`, []);
  const catalogSlotsUrl = useMemo(() => `${backendBase}/catalog/slots`, [backendBase]);
  const lockerSlotsUrl = useMemo(() => `${backendBase}/locker/slots`, [backendBase]);

  const currentOrderId = createResp?.order_id || null;
  const allowedPaymentMethods = selectedLocker?.payment_methods || [];

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
  }, [selectedLockerId, selectedLocker, region]);

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

  return (
    <div style={responsiveStyles.page}>
      {/* Header */}
      <div style={responsiveStyles.header}>
        <h1 style={responsiveStyles.title}>ELLAN KIOSK — {region}</h1>
        <p style={responsiveStyles.subtitle}>
          Autoatendimento 24h • Toque na tela para começar
        </p>
      </div>

      {/* Seção de Unidade */}
      <section style={responsiveStyles.card}>
        <div style={responsiveStyles.cardHeader}>
          <h2 style={responsiveStyles.cardTitle}>📍 0. Unidade</h2>
          <button
            onClick={fetchLockersOnce}
            disabled={lockersLoading}
            style={responsiveStyles.secondaryButton}
          >
            {lockersLoading ? "⏳" : "↻"}
          </button>
        </div>

        {availableLockers.length === 0 ? (
          <div style={responsiveStyles.errorBox}>
            Nenhum locker ativo encontrado
          </div>
        ) : (
          <div style={responsiveStyles.lockerSection}>
            <select
              value={selectedLockerId}
              onChange={(e) => setSelectedLockerId(e.target.value)}
              style={responsiveStyles.select}
            >
              {availableLockers.map((locker) => (
                <option key={locker.locker_id} value={locker.locker_id}>
                  {locker.display_name}
                </option>
              ))}
            </select>

            <div style={responsiveStyles.lockerInfo}>
              <div><b>ID:</b> {selectedLocker?.locker_id || "-"}</div>
              <div><b>Site:</b> {selectedLocker?.site_id || "-"}</div>
              <div><b>Slots:</b> {selectedLocker?.slots || "-"}</div>
              <div><b>Métodos:</b> {(selectedLocker?.payment_methods || []).join(", ")}</div>
              <div style={responsiveStyles.address}>
                📍 {formatAddress(selectedLocker)}
              </div>
            </div>

            {lockersError && <pre style={responsiveStyles.errorBox}>{lockersError}</pre>}
          </div>
        )}
      </section>

      {/* Vitrine de Produtos */}
      <section style={responsiveStyles.card}>
        <div style={responsiveStyles.cardHeader}>
          <h2 style={responsiveStyles.cardTitle}>📦 1. Escolha seu produto</h2>
          <button
            onClick={fetchCatalogSlots}
            disabled={catalogLoading}
            style={responsiveStyles.secondaryButton}
          >
            {catalogLoading ? "⏳" : "↻"}
          </button>
        </div>

        {catalogLoading ? (
          <div style={responsiveStyles.loading}>Carregando produtos...</div>
        ) : (
          <div style={responsiveStyles.slotsGrid}>
            {catalogSlots.map((item) => {
              const isSelected = selectedSlot === item.slot;
              const isAvailable = item.is_active && item.is_operationally_available;

              return (
                <button
                  key={item.slot}
                  onClick={() => isAvailable && handleSelectCatalogItem(item)}
                  disabled={!isAvailable}
                  style={{
                    ...responsiveStyles.slotCard,
                    ...(isSelected && responsiveStyles.slotSelected),
                    ...(!isAvailable && responsiveStyles.slotDisabled),
                  }}
                >
                  <div style={responsiveStyles.slotHeader}>
                    <span style={responsiveStyles.slotNumber}>#{item.slot}</span>
                    <span style={{
                      ...responsiveStyles.slotStatus,
                      background: isAvailable ? 'rgba(31,122,63,0.2)' : 'rgba(179,38,30,0.2)',
                    }}>
                      {isAvailable ? 'Disponível' : 'Indisponível'}
                    </span>
                  </div>
                  <div style={responsiveStyles.slotName}>{item.name}</div>
                  <div style={responsiveStyles.slotPrice}>
                    {formatMoney(item.amount_cents, item.currency)}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* Formulário de Pedido */}
      {selectedCatalogItem && (
        <section style={responsiveStyles.card}>
          <h2 style={responsiveStyles.cardTitle}>💰 2. Finalizar compra</h2>

          <div style={responsiveStyles.selectedProduct}>
            <div style={responsiveStyles.selectedProductInfo}>
              <span style={responsiveStyles.selectedProductName}>
                {selectedCatalogItem.name}
              </span>
              <span style={responsiveStyles.selectedProductPrice}>
                {formatMoney(selectedCatalogItem.amount_cents, selectedCatalogItem.currency)}
              </span>
            </div>
          </div>

          <div style={responsiveStyles.formGroup}>
            <label style={responsiveStyles.label}>Pagamento</label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              style={responsiveStyles.select}
            >
              {allowedPaymentMethods.map((method) => (
                <option key={method} value={method}>
                  {method === "CARTAO" ? "💳 Cartão" :
                   method === "PIX" ? "📱 PIX" :
                   method === "MBWAY" ? "📲 MB WAY" :
                   method === "MULTIBANCO_REFERENCE" ? "🏦 Multibanco" :
                   method}
                </option>
              ))}
            </select>
          </div>

          {paymentMethod === "CARTAO" && (
            <div style={responsiveStyles.rowGroup}>
              <button
                onClick={() => setPaymentExtras(prev => ({ ...prev, cardType: "creditCard" }))}
                style={{
                  ...responsiveStyles.halfButton,
                  ...(paymentExtras.cardType === "creditCard" && responsiveStyles.buttonSelected),
                }}
              >
                💳 Crédito
              </button>
              <button
                onClick={() => setPaymentExtras(prev => ({ ...prev, cardType: "debitCard" }))}
                style={{
                  ...responsiveStyles.halfButton,
                  ...(paymentExtras.cardType === "debitCard" && responsiveStyles.buttonSelected),
                }}
              >
                💳 Débito
              </button>
            </div>
          )}

          {paymentMethod === "MBWAY" && (
            <div style={responsiveStyles.formGroup}>
              <label style={responsiveStyles.label}>Telefone</label>
              <input
                type="tel"
                value={paymentExtras.customerPhone}
                onChange={(e) =>
                  setPaymentExtras(prev => ({ ...prev, customerPhone: e.target.value }))
                }
                placeholder="+351 912 345 678"
                style={responsiveStyles.input}
              />
            </div>
          )}

          <button
            onClick={createKioskOrder}
            disabled={loadingCreate}
            style={responsiveStyles.primaryButton}
          >
            {loadingCreate ? "⏳ Processando..." : "💰 Continuar para pagamento"}
          </button>

          {createResp && (
            <div style={responsiveStyles.successBox}>
              ✅ Pedido criado! ID: {createResp.order_id}
            </div>
          )}
        </section>
      )}

      {/* Seção de Pagamento */}
      {currentOrderId && (
        <section style={responsiveStyles.card}>
          <h2 style={responsiveStyles.cardTitle}>⏱️ 3. Pagamento</h2>

          <div style={responsiveStyles.paymentActions}>
            <button
              onClick={initiateKioskPayment}
              disabled={loadingGatewayPayment}
              style={responsiveStyles.primaryButton}
            >
              {loadingGatewayPayment ? "⏳ Iniciando..." : "💳 Iniciar pagamento"}
            </button>
            
            <button
              onClick={approveKioskPayment}
              disabled={loadingPayment}
              style={responsiveStyles.secondaryButton}
            >
              {loadingPayment ? "⏳ Confirmando..." : "✅ Simular pagamento"}
            </button>
          </div>

          {gatewayPaymentResp && (
            <div style={responsiveStyles.infoBox}>
              <b>Status:</b> {gatewayPaymentResp.result}
            </div>
          )}

          {/* Pagamento Pendente */}
          {displayedPendingContext && (
            <div style={{
              ...responsiveStyles.pendingBox,
              ...(pendingExpired && responsiveStyles.expiredBox)
            }}>
              <h3 style={responsiveStyles.pendingTitle}>
                {pendingExpired ? "⏰ Expirado" : "⌛ Aguardando pagamento"}
              </h3>

              {!pendingExpired && pendingSecondsRemaining !== null && (
                <div style={responsiveStyles.timer}>
                  ⏱️ {formatRemaining(pendingSecondsRemaining)}
                </div>
              )}

              {/* QR Code */}
              {(displayedPendingContext.qr_code_text || displayedPendingContext.qr_code_image_base64) && (
                <div style={responsiveStyles.qrContainer}>
                  <div style={responsiveStyles.qrWrapper}>
                    {displayedPendingContext.qr_code_image_base64 ? (
                      <img
                        src={`data:image/png;base64,${displayedPendingContext.qr_code_image_base64}`}
                        alt="QR Code"
                        style={responsiveStyles.qrImage}
                      />
                    ) : (
                      <QRCodeCanvas
                        value={displayedPendingContext.qr_code_text}
                        size={200}
                        includeMargin={true}
                      />
                    )}
                  </div>
                  
                  {displayedPendingContext.copy_paste_code && (
                    <div style={responsiveStyles.copySection}>
                      <textarea
                        readOnly
                        value={displayedPendingContext.copy_paste_code}
                        style={responsiveStyles.textarea}
                        rows="2"
                      />
                      <button
                        onClick={() => copyText(displayedPendingContext.copy_paste_code)}
                        style={responsiveStyles.smallButton}
                      >
                        📋 Copiar
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Instruções */}
              {displayedPendingContext.instruction && (
                <div style={responsiveStyles.instruction}>
                  ℹ️ {displayedPendingContext.instruction}
                </div>
              )}
            </div>
          )}

          {/* Pagamento Aprovado */}
          {paymentResp && (
            <div style={responsiveStyles.successBox}>
              <h3 style={responsiveStyles.successTitle}>✅ Pagamento confirmado!</h3>
              <p>Gaveta {paymentResp.slot} será aberta</p>
            </div>
          )}
        </section>
      )}

      {/* Identificação Opcional */}
      {currentOrderId && paymentResp && (
        <section style={responsiveStyles.card}>
          <h2 style={responsiveStyles.cardTitle}>👤 4. Identificação (opcional)</h2>

          <div style={responsiveStyles.formGroup}>
            <input
              type="tel"
              value={identifyForm.phone}
              onChange={(e) => setIdentifyForm(prev => ({ ...prev, phone: e.target.value }))}
              placeholder="📱 Telefone"
              style={responsiveStyles.input}
            />
          </div>

          <div style={responsiveStyles.formGroup}>
            <input
              type="email"
              value={identifyForm.email}
              onChange={(e) => setIdentifyForm(prev => ({ ...prev, email: e.target.value }))}
              placeholder="✉️ E-mail"
              style={responsiveStyles.input}
            />
          </div>

          <div style={responsiveStyles.rowGroup}>
            <button
              onClick={identifyCustomer}
              disabled={loadingIdentify}
              style={responsiveStyles.primaryButton}
            >
              {loadingIdentify ? "⏳" : "💾 Salvar"}
            </button>
            
            <button
              onClick={() => {
                setSelectedSlot(null);
                setSelectedCatalogItem(null);
                setCreateResp(null);
                setPaymentResp(null);
                setPendingPaymentContext(null);
              }}
              style={responsiveStyles.secondaryButton}
            >
              🔄 Nova compra
            </button>
          </div>

          {identifyResp && (
            <div style={responsiveStyles.successBox}>✅ Dados salvos</div>
          )}
        </section>
      )}

      {/* Mensagem de Erro */}
      {err && (
        <div style={responsiveStyles.errorBox}>
          ❌ {err}
        </div>
      )}
    </div>
  );
}

// Estilos responsivos
const responsiveStyles = {
  // Container principal - fluido e responsivo
  page: {
    minHeight: '100vh',
    backgroundColor: '#0a0e12',
    color: '#f5f7fa',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    padding: 'clamp(12px, 3vw, 24px)',
    maxWidth: '1400px',
    margin: '0 auto',
    width: '100%',
    boxSizing: 'border-box',
  },

  // Header adaptativo
  header: {
    marginBottom: 'clamp(16px, 4vw, 32px)',
    padding: 'clamp(12px, 3vw, 24px)',
    background: '#11161c',
    borderRadius: 'clamp(12px, 3vw, 24px)',
    border: '1px solid rgba(255,255,255,0.1)',
    textAlign: 'center',
  },

  title: {
    fontSize: 'clamp(24px, 6vw, 36px)',
    fontWeight: 700,
    margin: '0 0 8px 0',
    color: '#fff',
  },

  subtitle: {
    fontSize: 'clamp(14px, 3vw, 18px)',
    color: '#a0a8b3',
    margin: 0,
  },

  // Cards
  card: {
    background: '#11161c',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 'clamp(12px, 3vw, 20px)',
    padding: 'clamp(12px, 3vw, 24px)',
    marginBottom: 'clamp(12px, 3vw, 20px)',
    boxShadow: '0 8px 24px rgba(0,0,0,0.22)',
  },

  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 'clamp(12px, 3vw, 20px)',
    flexWrap: 'wrap',
    gap: '12px',
  },

  cardTitle: {
    fontSize: 'clamp(18px, 4vw, 24px)',
    fontWeight: 600,
    margin: 0,
    color: '#fff',
  },

  // Grid de slots - responsivo
  slotsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 180px), 1fr))',
    gap: 'clamp(8px, 2vw, 16px)',
  },

  slotCard: {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 'clamp(8px, 2vw, 14px)',
    padding: 'clamp(10px, 2.5vw, 16px)',
    cursor: 'pointer',
    color: '#f5f7fa',
    minHeight: 'clamp(100px, 25vw, 140px)',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    transition: 'all 0.2s',
    width: '100%',
  },

  slotSelected: {
    borderColor: '#1f7a3f',
    background: 'rgba(31,122,63,0.15)',
  },

  slotDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },

  slotHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '8px',
    flexWrap: 'wrap',
  },

  slotNumber: {
    fontSize: 'clamp(14px, 3vw, 16px)',
    fontWeight: 700,
    color: '#1b5883',
  },

  slotStatus: {
    fontSize: 'clamp(11px, 2.5vw, 12px)',
    padding: '4px 8px',
    borderRadius: '999px',
    whiteSpace: 'nowrap',
  },

  slotName: {
    fontSize: 'clamp(14px, 3vw, 16px)',
    fontWeight: 600,
    lineHeight: 1.3,
    wordBreak: 'break-word',
  },

  slotPrice: {
    fontSize: 'clamp(16px, 3.5vw, 18px)',
    fontWeight: 700,
    color: '#4caf50',
    marginTop: 'auto',
  },

  // Formulários
  formGroup: {
    marginBottom: 'clamp(12px, 3vw, 20px)',
  },

  rowGroup: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 'clamp(8px, 2vw, 12px)',
    marginBottom: 'clamp(12px, 3vw, 20px)',
  },

  label: {
    display: 'block',
    fontSize: 'clamp(14px, 3vw, 16px)',
    color: '#a0a8b3',
    marginBottom: '6px',
  },

  input: {
    width: '100%',
    padding: 'clamp(12px, 3vw, 16px)',
    background: '#0b0f14',
    border: '1px solid rgba(255,255,255,0.14)',
    borderRadius: 'clamp(8px, 2vw, 12px)',
    color: '#f5f7fa',
    fontSize: 'clamp(16px, 3.5vw, 18px)',
    minHeight: 'clamp(44px, 8vh, 56px)',
    boxSizing: 'border-box',
  },

  select: {
    width: '100%',
    padding: 'clamp(12px, 3vw, 16px)',
    background: '#0b0f14',
    border: '1px solid rgba(255,255,255,0.14)',
    borderRadius: 'clamp(8px, 2vw, 12px)',
    color: '#f5f7fa',
    fontSize: 'clamp(16px, 3.5vw, 18px)',
    minHeight: 'clamp(44px, 8vh, 56px)',
    cursor: 'pointer',
  },

  // Botões
  primaryButton: {
    width: '100%',
    padding: 'clamp(14px, 3.5vw, 20px)',
    background: '#1f7a3f',
    border: 'none',
    borderRadius: 'clamp(8px, 2vw, 12px)',
    color: '#fff',
    fontSize: 'clamp(16px, 3.5vw, 20px)',
    fontWeight: 600,
    cursor: 'pointer',
    minHeight: 'clamp(48px, 8vh, 64px)',
    transition: 'opacity 0.2s',
  },

  secondaryButton: {
    width: '100%',
    padding: 'clamp(12px, 3vw, 16px)',
    background: '#1b5883',
    border: 'none',
    borderRadius: 'clamp(8px, 2vw, 12px)',
    color: '#fff',
    fontSize: 'clamp(14px, 3vw, 16px)',
    fontWeight: 600,
    cursor: 'pointer',
    minHeight: 'clamp(44px, 7vh, 56px)',
  },

  halfButton: {
    flex: 1,
    padding: 'clamp(12px, 2.5vw, 14px)',
    background: '#0b0f14',
    border: '1px solid rgba(255,255,255,0.14)',
    borderRadius: 'clamp(8px, 2vw, 12px)',
    color: '#f5f7fa',
    fontSize: 'clamp(14px, 3vw, 16px)',
    cursor: 'pointer',
    minHeight: 'clamp(44px, 7vh, 52px)',
  },

  buttonSelected: {
    borderColor: '#1f7a3f',
    background: 'rgba(31,122,63,0.2)',
  },

  smallButton: {
    padding: 'clamp(8px, 2vw, 10px) clamp(12px, 3vw, 16px)',
    background: '#1b5883',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    fontSize: 'clamp(12px, 2.5vw, 14px)',
    cursor: 'pointer',
    minHeight: '36px',
  },

  // Áreas de informação
  lockerInfo: {
    display: 'grid',
    gap: '8px',
    padding: 'clamp(10px, 2.5vw, 16px)',
    background: 'rgba(255,255,255,0.05)',
    borderRadius: 'clamp(8px, 2vw, 12px)',
    fontSize: 'clamp(13px, 2.8vw, 15px)',
    marginTop: '12px',
  },

  address: {
    fontSize: 'clamp(12px, 2.5vw, 14px)',
    color: '#a0a8b3',
    wordBreak: 'break-word',
  },

  selectedProduct: {
    padding: 'clamp(12px, 3vw, 20px)',
    background: 'rgba(255,255,255,0.05)',
    borderRadius: 'clamp(8px, 2vw, 12px)',
    marginBottom: 'clamp(12px, 3vw, 20px)',
  },

  selectedProductName: {
    display: 'block',
    fontSize: 'clamp(16px, 3.5vw, 20px)',
    fontWeight: 600,
    marginBottom: '4px',
  },

  selectedProductPrice: {
    fontSize: 'clamp(18px, 4vw, 24px)',
    fontWeight: 700,
    color: '#4caf50',
  },

  paymentActions: {
    display: 'grid',
    gap: 'clamp(8px, 2vw, 12px)',
    marginBottom: 'clamp(12px, 3vw, 20px)',
  },

  // QR Code e áreas de pagamento
  pendingBox: {
    marginTop: 'clamp(12px, 3vw, 20px)',
    padding: 'clamp(12px, 3vw, 20px)',
    background: 'rgba(27,88,131,0.12)',
    border: '1px solid rgba(27,88,131,0.35)',
    borderRadius: 'clamp(8px, 2vw, 12px)',
  },

  expiredBox: {
    background: 'rgba(179,38,30,0.12)',
    border: '1px solid rgba(179,38,30,0.35)',
  },

  pendingTitle: {
    fontSize: 'clamp(16px, 3.5vw, 20px)',
    margin: '0 0 12px 0',
  },

  timer: {
    fontSize: 'clamp(24px, 5vw, 32px)',
    fontWeight: 700,
    textAlign: 'center',
    marginBottom: '16px',
    color: '#ff9800',
  },

  qrContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 250px), 1fr))',
    gap: 'clamp(12px, 3vw, 20px)',
    alignItems: 'center',
    marginBottom: '12px',
  },

  qrWrapper: {
    background: '#fff',
    padding: 'clamp(12px, 3vw, 16px)',
    borderRadius: '12px',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
  },

  qrImage: {
    width: '100%',
    maxWidth: '200px',
    height: 'auto',
    aspectRatio: '1',
    objectFit: 'contain',
  },

  copySection: {
    display: 'grid',
    gap: '8px',
  },

  textarea: {
    width: '100%',
    padding: 'clamp(8px, 2vw, 12px)',
    background: '#0b0f14',
    border: '1px solid rgba(255,255,255,0.14)',
    borderRadius: '8px',
    color: '#f5f7fa',
    fontSize: 'clamp(12px, 2.5vw, 14px)',
    resize: 'vertical',
    minHeight: '60px',
  },

  instruction: {
    padding: 'clamp(10px, 2.5vw, 14px)',
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    fontSize: 'clamp(13px, 2.8vw, 15px)',
    marginTop: '12px',
  },

  // Boxes de status
  successBox: {
    marginTop: 'clamp(12px, 3vw, 16px)',
    padding: 'clamp(12px, 3vw, 16px)',
    background: 'rgba(31,122,63,0.15)',
    border: '1px solid rgba(31,122,63,0.35)',
    borderRadius: 'clamp(8px, 2vw, 12px)',
    fontSize: 'clamp(14px, 3vw, 16px)',
  },

  infoBox: {
    marginTop: '12px',
    padding: '12px',
    background: 'rgba(27,88,131,0.12)',
    border: '1px solid rgba(27,88,131,0.35)',
    borderRadius: '8px',
  },

  errorBox: {
    marginTop: '12px',
    padding: 'clamp(10px, 2.5vw, 14px)',
    background: '#2b1d1d',
    border: '1px solid #ff4d4d',
    borderRadius: 'clamp(8px, 2vw, 12px)',
    color: '#ffb4b4',
    fontSize: 'clamp(13px, 2.8vw, 15px)',
    overflow: 'auto',
  },

  loading: {
    textAlign: 'center',
    padding: 'clamp(24px, 6vw, 40px)',
    color: '#a0a8b3',
    fontSize: 'clamp(14px, 3vw, 16px)',
  },
};