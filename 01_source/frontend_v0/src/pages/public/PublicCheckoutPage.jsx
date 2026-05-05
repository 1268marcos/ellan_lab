
// 01_source/frontend/src/pages/public/PublicCheckoutPage.jsx
// ONLINE real usando gateway + runtime + order_pickup_service
// 11/04/2026 - alteração de:  const res = await fetch(`${ORDER_PICKUP_BASE}/public/orders/`, {
//   em uso, motivo: próprio router: faz assim - /public/orders  → fluxo público (resolve payment)
//                                               /public/orders/ → fluxo interno (CreateOrderIn)
//   bug é clássico FastAPI - A barra final muda o handler no FastAPI

import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import FiscalProfileCheckoutPanel from "../../components/public/FiscalProfileCheckoutPanel";
import "../../styles/publicCheckoutChrome.css";

import {
  buildOnlineOrderPayload,
  paymentMethodLabel,
} from "../../utils/paymentProfile";
import { previewCheckoutCredit } from "../../services/publicApi";


const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const GATEWAY_BASE =
  import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";

const RUNTIME_BASE =
  import.meta.env.VITE_RUNTIME_BASE_URL || "http://localhost:8200";

function TrustSignals() {
  return (
    <div className="public-checkout-chrome__trust-strip">
      <div className="public-checkout-chrome__trust-item">
        <span className="public-checkout-chrome__trust-icon">🔒</span>
        <span className="public-checkout-chrome__trust-text">Pagamento Seguro</span>
      </div>
      <div className="public-checkout-chrome__trust-item">
        <span className="public-checkout-chrome__trust-icon">⚡</span>
        <span className="public-checkout-chrome__trust-text">Confirmação Imediata</span>
      </div>
      <div className="public-checkout-chrome__trust-item">
        <span className="public-checkout-chrome__trust-icon">📦</span>
        <span className="public-checkout-chrome__trust-text">Retirada após confirmação</span>
      </div>
    </div>
  );
}

function CheckoutSteps({ currentStep }) {
  const steps = [
    { id: 1, label: "Produto", icon: "🛒" },
    { id: 2, label: "Pagamento", icon: "💳" },
    { id: 3, label: "Confirmação", icon: "✅" },
  ];

  return (
    <div className="public-checkout-chrome__steps" data-testid="public-checkout-steps">
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          <div
            className={
              "public-checkout-chrome__step" +
              (currentStep >= step.id ? " public-checkout-chrome__step--active" : "")
            }
          >
            <div className="public-checkout-chrome__step-icon">{step.icon}</div>
            <div className="public-checkout-chrome__step-label">{step.label}</div>
          </div>
          {index < steps.length - 1 && (
            <div
              className={
                "public-checkout-chrome__step-connector" +
                (currentStep > step.id ? " public-checkout-chrome__step-connector--active" : "")
              }
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

function formatMoney(cents, currency, locale = undefined) {
  const value = Number(cents);
  if (!Number.isFinite(value)) return "-";

  const amount = value / 100;
  const safeCurrency = String(currency || "").trim().toUpperCase();

  try {
    if (safeCurrency) {
      return new Intl.NumberFormat(locale || undefined, {
        style: "currency",
        currency: safeCurrency,
      }).format(amount);
    }

    return new Intl.NumberFormat(locale || undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return safeCurrency
      ? `${amount.toFixed(2)} ${safeCurrency}`.trim()
      : amount.toFixed(2);
  }
}

// function paymentMethodLabel(method) {
//   const labels = {
//     PIX: "PIX",
//     CARTAO_CREDITO: "Cartão de Crédito",
//     CARTAO_DEBITO: "Cartão de Débito",
//     CARTAO_PRESENTE: "Cartão Presente",
//     CARTAO: "Cartão",
//     MBWAY: "MB WAY",
//     MULTIBANCO_REFERENCE: "Referência Multibanco",
//     NFC: "NFC",
//     APPLE_PAY: "Apple Pay",
//     GOOGLE_PAY: "Google Pay",
//     MERCADO_PAGO_WALLET: "Mercado Pago Wallet",
//   };
//   return labels[method] || method || "-";
// }

function walletProviderForMethod(method) {
  const providers = {
    APPLE_PAY: "applePay",
    GOOGLE_PAY: "googlePay",
    MERCADO_PAGO_WALLET: "mercadoPago",
  };
  return providers[method] || undefined;
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

// 15/04/2026
function isDevBypassEnabled() {
  return String(import.meta.env.VITE_DEV_BYPASS_AUTH || "")
    .trim()
    .toLowerCase() === "true";
}

async function parseRichErrorResponse(res) {
  const rawText = await res.text().catch(() => "");
  let parsed = null;

  try {
    parsed = rawText ? JSON.parse(rawText) : null;
  } catch {
    parsed = null;
  }

  return {
    status: res.status,
    statusText: res.statusText,
    rawText,
    parsed,
    detail: parsed?.detail ?? parsed?.message ?? rawText ?? `HTTP ${res.status}`,
  };
}

function parseLockersResponse(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  return [];
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
    region: String(locker?.region || "").trim().toUpperCase(),
    site_id: locker?.site_id || "",
    display_name: locker?.display_name || locker?.locker_id || "",
    channels: Array.isArray(locker?.channels) ? locker.channels.map(String) : [],
    payment_methods: Array.isArray(locker?.payment_methods)
      ? locker.payment_methods.map((item) => String(item).trim()) //.toUpperCase()
      : [],
    active: Boolean(locker?.active),
    address,
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

function resolveDisplayedRegion(value) {
  return String(value || "").trim().toUpperCase() || "SP";
}

export default function PublicCheckoutPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const region = resolveDisplayedRegion(searchParams.get("region") || "SP");
  const lockerId = String(searchParams.get("locker_id") || "").trim();
  const skuId = String(searchParams.get("sku_id") || "").trim();
  const slot = Number(searchParams.get("slot") || 0);

  const [product, setProduct] = useState(null);
  const [locker, setLocker] = useState(null);

  const [productLoading, setProductLoading] = useState(false);
  const [lockerLoading, setLockerLoading] = useState(false);

  const [productError, setProductError] = useState("");
  const [lockerError, setLockerError] = useState("");

  const [paymentMethod, setPaymentMethod] = useState("");
  // const [cardType, setCardType] = useState("creditCard");
  const [customerPhone, setCustomerPhone] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [currentStep, setCurrentStep] = useState(1);
  const [useCredit, setUseCredit] = useState(false);
  const [creditPreview, setCreditPreview] = useState(null);
  const [loadingCreditPreview, setLoadingCreditPreview] = useState(false);

  const invalidParams = !lockerId || !skuId || !slot;

  const { token, isAuthenticated, user, hasRole, refreshUser } = useAuth();

  const checkoutFiscalCountry = region === "PT" ? "PT" : "BR";
  const requiresFiscalProfile = checkoutFiscalCountry === "BR" || checkoutFiscalCountry === "PT";
  const fiscalProfileComplete = Number(user?.fiscal_profile_completeness ?? 0) >= 100;
  const fiscalReadyForCheckout = !requiresFiscalProfile || fiscalProfileComplete;

  const runtimeSkuUrl = useMemo(
    () => `${RUNTIME_BASE}/catalog/skus/${encodeURIComponent(skuId)}`,
    [skuId]
  );

  const allowedPaymentMethods = useMemo(() => {
    return Array.isArray(locker?.payment_methods) ? locker.payment_methods : [];
  }, [locker]);
  const displayLocale = region === "PT" ? "pt-PT" : "pt-BR";
  const catalogCurrency = String(product?.currency || "").trim().toUpperCase();
  const previewCurrency = String(creditPreview?.currency || "").trim().toUpperCase();
  const displayCurrency = useMemo(() => {
    if (previewCurrency) return previewCurrency;
    if (catalogCurrency && catalogCurrency !== "BRL") return catalogCurrency;
    if (region === "PT") return "EUR";
    return catalogCurrency || "BRL";
  }, [previewCurrency, catalogCurrency, region]);

  // 15/04/2026
  const [loadingSimulatePayment, setLoadingSimulatePayment] = useState(false);
  const [simulateResult, setSimulateResult] = useState(null);

  const canShowDevSimulateButton = useMemo(() => {
    const hasDevRole = hasRole("admin_operacao") || hasRole("auditoria");
    return isDevBypassEnabled() && Boolean(lockerId) && Boolean(region) && hasDevRole;
  }, [lockerId, region, hasRole]);
  const emailVerified = Boolean(user?.email_verified);





  useEffect(() => {
    if (!isAuthenticated && !invalidParams) {
      const redirectUrl = encodeURIComponent(window.location.pathname + window.location.search);
      navigate(`/login?redirect=${redirectUrl}`);
    }
  }, [isAuthenticated, invalidParams, navigate]);

  useEffect(() => {
    async function loadLocker() {
      if (invalidParams) return;

      setLockerLoading(true);
      setLockerError("");

      try {
        const res = await fetch(
          `${GATEWAY_BASE}/lockers?region=${encodeURIComponent(region)}&active_only=true`
        );
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          throw new Error(
            typeof data?.detail !== "undefined"
              ? JSON.stringify(data.detail, null, 2)
              : JSON.stringify(data, null, 2)
          );
        }

        const items = parseLockersResponse(data).map(normalizeLockerItem);
        const found = items.find((item) => item.locker_id === lockerId) || null;

        if (!found) {
          throw new Error(
            JSON.stringify(
              {
                type: "LOCKER_NOT_FOUND_IN_GATEWAY",
                message: "Locker não encontrado no gateway para a região selecionada.",
                region,
                locker_id: lockerId,
              },
              null,
              2
            )
          );
        }

        setLocker(found);
      } catch (e) {
        setLockerError(String(e?.message || e));
        setLocker(null);
      } finally {
        setLockerLoading(false);
      }
    }

    loadLocker();
  }, [invalidParams, lockerId, region]);

  useEffect(() => {
    if (!allowedPaymentMethods.length) {
      setPaymentMethod("");
      return;
    }

    setPaymentMethod((prev) =>
      allowedPaymentMethods.includes(prev) ? prev : allowedPaymentMethods[0]
    );
  }, [allowedPaymentMethods]);

  useEffect(() => {
    async function loadProduct() {
      if (invalidParams) return;

      setProductLoading(true);
      setProductError("");

      try {
        const res = await fetch(runtimeSkuUrl, {
          headers: { "X-Locker-Id": lockerId },
        });
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          throw new Error(
            typeof data?.detail !== "undefined"
              ? JSON.stringify(data.detail, null, 2)
              : JSON.stringify(data, null, 2)
          );
        }

        setProduct(data);
        setCurrentStep(1);
      } catch (e) {
        setProductError(String(e?.message || e));
        setProduct(null);
      } finally {
        setProductLoading(false);
      }
    }

    loadProduct();
  }, [invalidParams, lockerId, runtimeSkuUrl]);

  useEffect(() => {
    let active = true;

    async function loadCreditPreview() {
      if (!isAuthenticated || !token || !product?.amount_cents) {
        if (!active) return;
        setCreditPreview(null);
        setLoadingCreditPreview(false);
        return;
      }

      if (!useCredit) {
        if (!active) return;
        setCreditPreview(null);
        setLoadingCreditPreview(false);
        return;
      }

      try {
        if (active) setLoadingCreditPreview(true);
        const data = await previewCheckoutCredit(token, {
          amount_cents: Number(product.amount_cents),
          use_credit: true,
          region,
        });
        if (!active) return;
        setCreditPreview(data || null);
      } catch (error) {
        if (!active) return;
        setCreditPreview({
          eligible: false,
          reason: "preview_error",
          requested_use_credit: true,
          base_amount_cents: Number(product.amount_cents || 0),
          final_amount_cents: Number(product.amount_cents || 0),
          discount_cents: 0,
          currency: product.currency || "BRL",
          error_message: error?.message || "Falha ao simular crédito.",
        });
      } finally {
        if (active) setLoadingCreditPreview(false);
      }
    }

    loadCreditPreview();
    return () => {
      active = false;
    };
  }, [isAuthenticated, token, product?.amount_cents, product?.currency, useCredit, region]);

  async function handleCreateOrder() {
    if (invalidParams || !product || !locker) {
      setSubmitError("Dados do checkout incompletos.");
      return;
    }

    if (!paymentMethod) {
      setSubmitError("Nenhum método de pagamento disponível para este locker.");
      return;
    }

    if (!allowedPaymentMethods.includes(paymentMethod)) {
      setSubmitError("Método de pagamento inválido para este locker.");
      return;
    }

    setSubmitting(true);
    setSubmitError("");
    setCurrentStep(2);


    const payload = buildOnlineOrderPayload({
      region,
      totemId: lockerId,
      // sku_id: skuId,
      // desired_slot: slot,
      skuId: skuId,
      slot: slot,
      uiMethod: paymentMethod,
      customerPhone,
      amountCents: product.amount_cents,
    });

    // 🔥 FIX OBRIGATÓRIO
    if (!payload.payment_interface) {
      payload.payment_interface = "web_token";
    }

    if (paymentMethod === "MBWAY") {
      payload.customer_phone = customerPhone.trim();
    }

    const walletProvider = walletProviderForMethod(paymentMethod);
    if (walletProvider) {
      payload.wallet_provider = walletProvider;
    }
    payload.use_credit = Boolean(useCredit);
    if (creditPreview?.eligible && creditPreview?.credit_id) {
      payload.credit_id = creditPreview.credit_id;
    }

    try {
      const deviceFp = getOrCreateDeviceFingerprint();
      const idempotencyKey = generateIdempotencyKey();

      const res = await fetch(`${ORDER_PICKUP_BASE}/public/orders/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-Device-Fingerprint": deviceFp,
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const richError = await parseRichErrorResponse(res);
        throw new Error(
          JSON.stringify(
            {
              error: "Falha ao criar pedido online",
              http_status: richError.status,
              http_status_text: richError.statusText,
              backend_detail: richError.detail,
              response_json: richError.parsed,
              response_raw: richError.rawText,
              request_payload: payload,
            },
            null,
            2
          )
        );
      }

      const data = await res.json().catch(() => ({}));
      const orderId = data?.order_id;

      if (!orderId) {
        throw new Error(
          JSON.stringify(
            {
              error: "Resposta sem order_id",
              response_json: data,
              request_payload: payload,
            },
            null,
            2
          )
        );
      }

      setCurrentStep(3);

      setTimeout(() => {
        navigate(`/meus-pedidos/${encodeURIComponent(orderId)}`, { replace: true });
      }, 1500);
    } catch (e) {
      setSubmitError(String(e?.message || e));
      setCurrentStep(1);
    } finally {
      setSubmitting(false);
    }
  }


  // 15/04/2026
  async function handleSimulateOnlinePaymentDev() {
    if (!canShowDevSimulateButton) {
      setSubmitError("A simulação DEV só pode ser usada com VITE_DEV_BYPASS_AUTH=true.");
      return;
    }

    if (invalidParams || !product || !locker) {
      setSubmitError("Dados do checkout incompletos para simulação DEV.");
      return;
    }

    const confirmed = window.confirm(
      `ATENÇÃO: isso vai criar um pedido ONLINE real para o locker ${lockerId}, slot ${slot}, e depois simular a aprovação do pagamento em ambiente DEV. Deseja continuar?`
    );
    if (!confirmed) return;

    setLoadingSimulatePayment(true);
    setSubmitError("");
    setSimulateResult(null);
    setCurrentStep(2);

    const payload = buildOnlineOrderPayload({
      region,
      totemId: lockerId,
      skuId,
      slot,
      uiMethod: paymentMethod,
      customerPhone,
      amountCents: product.amount_cents,
    });

    if (!payload.payment_interface) {
      payload.payment_interface = "web_token";
    }

    if (paymentMethod === "MBWAY") {
      payload.customer_phone = customerPhone.trim();
    }

    const walletProvider = walletProviderForMethod(paymentMethod);
    if (walletProvider) {
      payload.wallet_provider = walletProvider;
    }

    payload.use_credit = Boolean(useCredit);
    if (creditPreview?.eligible && creditPreview?.credit_id) {
      payload.credit_id = creditPreview.credit_id;
    }

    try {
      const deviceFp = getOrCreateDeviceFingerprint();
      const idempotencyKey = generateIdempotencyKey();

      const createRes = await fetch(`${ORDER_PICKUP_BASE}/public/orders/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-Device-Fingerprint": deviceFp,
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify(payload),
      });

      if (!createRes.ok) {
        const richError = await parseRichErrorResponse(createRes);
        throw new Error(
          JSON.stringify(
            {
              error: "Falha ao criar pedido online para simulação DEV",
              http_status: richError.status,
              http_status_text: richError.statusText,
              backend_detail: richError.detail,
              response_json: richError.parsed,
              response_raw: richError.rawText,
              request_payload: payload,
            },
            null,
            2
          )
        );
      }

      const created = await createRes.json().catch(() => ({}));
      const orderId = created?.order_id;

      if (!orderId) {
        throw new Error(
          JSON.stringify(
            {
              error: "Resposta sem order_id na criação do pedido DEV",
              response_json: created,
              request_payload: payload,
            },
            null,
            2
          )
        );
      }

      const simulateRes = await fetch(
        `${ORDER_PICKUP_BASE}/dev-admin/simulate-online-payment?order_id=${encodeURIComponent(orderId)}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const simulateData = await simulateRes.json().catch(() => ({}));

      if (!simulateRes.ok) {
        let cancelAttempt = null;
        const roleRequired = simulateData?.detail?.type === "ROLE_REQUIRED";

        if (roleRequired) {
          const cancelRes = await fetch(
            `${ORDER_PICKUP_BASE}/public/orders/${encodeURIComponent(orderId)}/cancel`,
            {
              method: "POST",
              headers: {
                Authorization: `Bearer ${token}`,
                "X-Device-Fingerprint": deviceFp,
              },
            }
          );
          cancelAttempt = await cancelRes.json().catch(() => ({}));
        }

        throw new Error(
          JSON.stringify(
            {
              error: "Falha ao simular pagamento ONLINE DEV",
              order_id: orderId,
              response_json: simulateData,
              compensation_cancel_attempt: cancelAttempt,
            },
            null,
            2
          )
        );
      }

      setSimulateResult(simulateData);
      setCurrentStep(3);

      setTimeout(() => {
        navigate(`/meus-pedidos/${encodeURIComponent(orderId)}`, { replace: true });
      }, 1200);
    } catch (e) {
      setSubmitError(String(e?.message || e));
      setCurrentStep(1);
    } finally {
      setLoadingSimulatePayment(false);
    }
  }
  







  if (invalidParams) {
    return (
      <main className="public-checkout-chrome__page">
        <div className="public-checkout-chrome">
          <div className="public-checkout-chrome__page-inner">
          <h1 className="sr-only">Checkout</h1>
          <CheckoutSteps currentStep={0} />
          <section
            data-testid="public-checkout-invalid"
            className="public-checkout-chrome__card public-checkout-chrome__card--invalid"
          >
            <div className="public-checkout-chrome__card-icon-lg">⚠️</div>
            <h2 className="public-checkout-chrome__card-title">Checkout inválido</h2>
            <p className="public-checkout-chrome__card-text">
              Faltam dados obrigatórios da seleção. Volte ao catálogo e escolha uma gaveta.
            </p>
            <Link
              to={`/comprar?region=${encodeURIComponent(region)}&locker_id=${encodeURIComponent(
                lockerId
              )}`}
              className="public-checkout-chrome__btn-primary"
            >
              Voltar ao catálogo
            </Link>
          </section>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="public-checkout-chrome__page">
      <div className="public-checkout-chrome">
        <div className="public-checkout-chrome__page-inner">
        <CheckoutSteps currentStep={currentStep} />

        <section className="public-checkout-chrome__hero-card">
          <div className="public-checkout-chrome__hero-head">
            <h1 className="public-checkout-chrome__page-title">Finalizar Reserva</h1>
            <p className="public-checkout-chrome__subtitle">
              Confira os dados do seu pedido, escolha a forma de pagamento e confirme sua
              reserva para retirada no locker selecionado.
            </p>
          </div>
          <TrustSignals />
        </section>

        <div className="public-checkout-chrome__layout-grid">
          <section className="public-checkout-chrome__card" data-testid="public-checkout-summary-card">
            <h2 className="public-checkout-chrome__card-title">📦 Resumo do Pedido</h2>

            {lockerLoading ? (
              <div className="public-checkout-chrome__loading-state">
                <div className="public-checkout-chrome__spinner" />
                <p>Carregando locker...</p>
              </div>
            ) : lockerError ? (
              <pre className="public-checkout-chrome__error-box">{lockerError}</pre>
            ) : locker ? (
              <div className="public-checkout-chrome__summary-grid public-checkout-chrome__summary-grid--locker-gap">
                <div className="public-checkout-chrome__summary-row">
                  <span className="public-checkout-chrome__summary-label">Locker</span>
                  <span className="public-checkout-chrome__summary-value">{locker.display_name || lockerId}</span>
                </div>
                <div className="public-checkout-chrome__summary-row">
                  <span className="public-checkout-chrome__summary-label">Endereço</span>
                  <span className="public-checkout-chrome__summary-value">{formatAddress(locker)}</span>
                </div>
                <div className="public-checkout-chrome__summary-row">
                  <span className="public-checkout-chrome__summary-label">Métodos permitidos</span>
                  <span className="public-checkout-chrome__summary-value">
                    {allowedPaymentMethods.length
                      ? allowedPaymentMethods.map(paymentMethodLabel).join(", ")
                      : "-"}
                  </span>
                </div>
              </div>
            ) : null}

            {productLoading ? (
              <div className="public-checkout-chrome__loading-state">
                <div className="public-checkout-chrome__spinner" />
                <p>Carregando produto...</p>
              </div>
            ) : productError ? (
              <pre className="public-checkout-chrome__error-box">{productError}</pre>
            ) : product ? (
              <div className="public-checkout-chrome__summary-grid">
                <div className="public-checkout-chrome__summary-highlight">
                  <small className="public-checkout-chrome__summary-highlight-label">Produto selecionado</small>
                  <div className="public-checkout-chrome__summary-highlight-row">
                    <div className="public-checkout-chrome__summary-highlight-product">{product.name || "-"}</div>
                    <span className="public-checkout-chrome__summary-meta-chip">Gaveta {slot}</span>
                    <div className="public-checkout-chrome__summary-highlight-price">
                      {formatMoney(product.amount_cents, displayCurrency, displayLocale)}
                    </div>
                  </div>
                  <small className="public-checkout-chrome__summary-highlight-hint">
                    Retirada liberada após confirmação do pagamento.
                  </small>
                </div>
                <div className="public-checkout-chrome__summary-row">
                  <span className="public-checkout-chrome__summary-label">Região</span>
                  <span className="public-checkout-chrome__summary-value">{region}</span>
                </div>
                <div className="public-checkout-chrome__summary-row">
                  <span className="public-checkout-chrome__summary-label">Identificador do locker</span>
                  <span className="public-checkout-chrome__summary-value">{lockerId}</span>
                </div>
                <div className="public-checkout-chrome__summary-row">
                  <span className="public-checkout-chrome__summary-label">Identificador do SKU</span>
                  <span className="public-checkout-chrome__summary-value">{product.sku_id || skuId}</span>
                </div>
                {useCredit ? (
                  <div className="public-checkout-chrome__summary-row">
                    <span className="public-checkout-chrome__summary-label">Total com crédito</span>
                    <span className="public-checkout-chrome__price-accent">
                      {formatMoney(
                        creditPreview?.final_amount_cents ?? product.amount_cents,
                        displayCurrency,
                        displayLocale
                      )}
                    </span>
                  </div>
                ) : null}
                <div className="public-checkout-chrome__summary-row">
                  <span className="public-checkout-chrome__summary-label">Moeda exibida</span>
                  <span className="public-checkout-chrome__summary-value">
                    {displayCurrency || "-"}
                    {catalogCurrency && catalogCurrency !== displayCurrency
                      ? ` (catálogo: ${catalogCurrency})`
                      : ""}
                  </span>
                </div>
              </div>
            ) : (
              <p className="public-checkout-chrome__card-text">Produto indisponível.</p>
            )}
          </section>

          <section className="public-checkout-chrome__card" data-testid="public-checkout-payment-card">
            <h2 className="public-checkout-chrome__card-title">💳 Pagamento</h2>

            <div className="public-checkout-chrome__field-grid">
              <label className="public-checkout-chrome__field-label">
                Método de pagamento
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="public-checkout-chrome__field-input"
                  disabled={submitting || !allowedPaymentMethods.length}
                >
                  {!allowedPaymentMethods.length ? (
                    <option value="">Nenhum método disponível</option>
                  ) : (
                    allowedPaymentMethods.map((method) => (
                      <option key={method} value={method}>
                        {paymentMethodLabel(method)}
                      </option>
                    ))
                  )}
                </select>
              </label>



              {paymentMethod === "MBWAY" && (
                <label className="public-checkout-chrome__field-label">
                  Telefone MB WAY
                  <input
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    className="public-checkout-chrome__field-input"
                    placeholder="+351912345678"
                    disabled={submitting}
                  />
                </label>
              )}
            </div>

            <div className="public-checkout-chrome__credit-panel">
              <label className="public-checkout-chrome__field-label public-checkout-chrome__field-label--inline">
                <input
                  type="checkbox"
                  className="public-checkout-chrome__checkbox"
                  checked={useCredit}
                  onChange={(event) => setUseCredit(event.target.checked)}
                  disabled={submitting || loadingCreditPreview}
                />
                Usar crédito (aplica automaticamente o que vence primeiro)
              </label>

              {useCredit ? (
                <div className="public-checkout-chrome__credit-detail">
                  {loadingCreditPreview ? (
                    <small className="public-checkout-chrome__credit-hint-muted">Simulando crédito disponível...</small>
                  ) : creditPreview?.eligible ? (
                    <small className="public-checkout-chrome__credit-hint-ok">
                      Crédito selecionado: {formatMoney(creditPreview.discount_cents, displayCurrency, displayLocale)}.
                      Total final: {formatMoney(creditPreview.final_amount_cents, displayCurrency, displayLocale)}.
                    </small>
                  ) : (
                    <small className="public-checkout-chrome__credit-hint-warn">
                      Nenhum crédito elegível no momento.
                      {creditPreview?.error_message ? ` (${creditPreview.error_message})` : ""}
                    </small>
                  )}
                </div>
              ) : null}
            </div>

            <div className="public-checkout-chrome__notice">
              <span className="public-checkout-chrome__notice-icon">ℹ️</span>
              <div>
                <strong>Antes de confirmar:</strong>
                <p className="public-checkout-chrome__notice-text">
                  O valor final e a disponibilidade são validados novamente no servidor no momento
                  da confirmação para garantir segurança e consistência do pedido.
                </p>
              </div>
            </div>

            {!emailVerified ? (
              <div className="public-checkout-chrome__error-box">
                <strong>E-mail não verificado.</strong>
                <p className="public-checkout-chrome__error-box-intro">
                  Para criar pedidos, confirme seu e-mail em{" "}
                  <Link to="/seguranca">Segurança da conta</Link>.
                </p>
              </div>
            ) : null}

            {emailVerified && requiresFiscalProfile && !fiscalProfileComplete && token ? (
              <FiscalProfileCheckoutPanel
                token={token}
                user={user}
                fiscalCountry={checkoutFiscalCountry}
                onSaved={refreshUser}
              />
            ) : null}

            {submitError ? (
              <div className="public-checkout-chrome__error-box" data-testid="public-checkout-order-error">
                <strong>Erro ao processar:</strong>
                <pre className="public-checkout-chrome__error-pre">{submitError}</pre>
              </div>
            ) : null}


            {/* 15/04/2026 */}
            {simulateResult ? (
              <pre className="public-checkout-chrome__dev-json-box">
                {JSON.stringify(simulateResult, null, 2)}
              </pre>
            ) : null}




            <button
              type="button"
              data-testid="public-checkout-confirm-order"
              className="public-checkout-chrome__btn-primary"
              onClick={handleCreateOrder}
              disabled={
                submitting ||
                productLoading ||
                lockerLoading ||
                !product ||
                !locker ||
                !paymentMethod ||
                !allowedPaymentMethods.length ||
                (paymentMethod === "MBWAY" && !customerPhone.trim()) ||
                (useCredit && loadingCreditPreview) ||
                !emailVerified ||
                !fiscalReadyForCheckout
              }
            >
              {submitting ? (
                <>
                  <span className="public-checkout-chrome__spinner public-checkout-chrome__spinner--sm" />
                  Processando...
                </>
              ) : currentStep === 3 ? (
                <>
                  <span className="public-checkout-chrome__icon-success">✓</span>
                  Pedido Criado! Redirecionando...
                </>
              ) : (
                "Confirmar reserva e pagar"
              )}
            </button>




            {/* 15/04/2026 */}
            {canShowDevSimulateButton ? (
              <button
                type="button"
                data-testid="public-checkout-dev-simulate"
                className="public-checkout-chrome__btn-danger-dev"
                onClick={handleSimulateOnlinePaymentDev}
                disabled={
                  loadingSimulatePayment ||
                  submitting ||
                  productLoading ||
                  lockerLoading ||
                  !product ||
                  !locker ||
                  !paymentMethod ||
                  !allowedPaymentMethods.length ||
                  (paymentMethod === "MBWAY" && !customerPhone.trim()) ||
                  !emailVerified ||
                  !fiscalReadyForCheckout
                }
              >
                {loadingSimulatePayment
                  ? "Simulando pagamento DEV..."
                  : "DEV — Criar pedido e simular pagamento"}
              </button>
            ) : null}










            <div className="public-checkout-chrome__actions-row">
              <Link
                to={`/comprar?region=${encodeURIComponent(region)}&locker_id=${encodeURIComponent(
                  lockerId
                )}`}
                className="public-checkout-chrome__btn-secondary"
              >
                ← Voltar
              </Link>
              <Link to="/meus-pedidos" className="public-checkout-chrome__btn-secondary">
                Meus pedidos
              </Link>
            </div>
          </section>
        </div>
        </div>
      </div>
    </main>
  );
}


