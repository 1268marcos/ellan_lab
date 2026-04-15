// 01_source/frontend/src/pages/public/PublicCheckoutPage.jsx
// ONLINE real usando gateway + runtime + order_pickup_service
// 11/04/2026 - alteração de:  const res = await fetch(`${ORDER_PICKUP_BASE}/public/orders/`, {
//   em uso, motivo: próprio router: faz assim - /public/orders  → fluxo público (resolve payment)
//                                               /public/orders/ → fluxo interno (CreateOrderIn)
//   bug é clássico FastAPI - A barra final muda o handler no FastAPI

import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

import {
  buildOnlineOrderPayload,
  paymentMethodLabel,
} from "../../utils/paymentProfile";


const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const GATEWAY_BASE =
  import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";

const RUNTIME_BASE =
  import.meta.env.VITE_RUNTIME_BASE_URL || "http://localhost:8200";

function TrustSignals() {
  return (
    <div style={trustSignalsStyle}>
      <div style={trustItemStyle}>
        <span style={trustIconStyle}>🔒</span>
        <span style={trustTextStyle}>Pagamento Seguro</span>
      </div>
      <div style={trustItemStyle}>
        <span style={trustIconStyle}>⚡</span>
        <span style={trustTextStyle}>Confirmação Imediata</span>
      </div>
      <div style={trustItemStyle}>
        <span style={trustIconStyle}>📦</span>
        <span style={trustTextStyle}>Retirada em 2 horas 24/7</span>
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
    <div style={stepsContainerStyle}>
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          <div
            style={{
              ...stepStyle,
              ...(currentStep >= step.id ? stepActiveStyle : {}),
            }}
          >
            <div style={stepIconStyle}>{step.icon}</div>
            <div style={stepLabelStyle}>{step.label}</div>
          </div>
          {index < steps.length - 1 && (
            <div
              style={{
                ...stepConnectorStyle,
                ...(currentStep > step.id ? stepConnectorActiveStyle : {}),
              }}
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

  const invalidParams = !lockerId || !skuId || !slot;

  const { token, isAuthenticated } = useAuth();

  const runtimeSkuUrl = useMemo(
    () => `${RUNTIME_BASE}/catalog/skus/${encodeURIComponent(skuId)}`,
    [skuId]
  );

  const allowedPaymentMethods = useMemo(() => {
    return Array.isArray(locker?.payment_methods) ? locker.payment_methods : [];
  }, [locker]);

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

  if (invalidParams) {
    return (
      <main style={pageStyle}>
        <div style={containerStyle}>
          <CheckoutSteps currentStep={0} />
          <section style={errorCardStyle}>
            <div style={errorIconStyle}>⚠️</div>
            <h2 style={cardTitleStyle}>Checkout inválido</h2>
            <p style={cardTextStyle}>
              Faltam dados obrigatórios da seleção. Volte ao catálogo e escolha uma gaveta.
            </p>
            <Link
              to={`/comprar?region=${encodeURIComponent(region)}&locker_id=${encodeURIComponent(
                lockerId
              )}`}
              style={primaryButtonStyle}
            >
              Voltar ao catálogo
            </Link>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <CheckoutSteps currentStep={currentStep} />

        <section style={heroCardStyle}>
          <div style={heroContentStyle}>
            <h1 style={titleStyle}>Finalizar Reserva</h1>
            <p style={subtitleStyle}>
              Você está reservando uma gaveta real do locker selecionado. O pedido será criado
              no canal ONLINE usando runtime central.
            </p>
          </div>
          <TrustSignals />
        </section>

        <div style={layoutStyle}>
          <section style={cardStyle}>
            <h2 style={cardTitleStyle}>📦 Resumo do Pedido</h2>

            {lockerLoading ? (
              <div style={loadingStyle}>
                <div style={spinnerStyle} />
                <p>Carregando locker...</p>
              </div>
            ) : lockerError ? (
              <pre style={errorBoxStyle}>{lockerError}</pre>
            ) : locker ? (
              <div style={{ ...summaryGridStyle, marginBottom: 18 }}>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>Locker</span>
                  <span style={summaryValueStyle}>{locker.display_name || lockerId}</span>
                </div>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>Endereço</span>
                  <span style={summaryValueStyle}>{formatAddress(locker)}</span>
                </div>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>Métodos permitidos</span>
                  <span style={summaryValueStyle}>
                    {allowedPaymentMethods.length
                      ? allowedPaymentMethods.map(paymentMethodLabel).join(", ")
                      : "-"}
                  </span>
                </div>
              </div>
            ) : null}

            {productLoading ? (
              <div style={loadingStyle}>
                <div style={spinnerStyle} />
                <p>Carregando produto...</p>
              </div>
            ) : productError ? (
              <pre style={errorBoxStyle}>{productError}</pre>
            ) : product ? (
              <div style={summaryGridStyle}>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>Região</span>
                  <span style={summaryValueStyle}>{region}</span>
                </div>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>Locker ID</span>
                  <span style={summaryValueStyle}>{lockerId}</span>
                </div>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>Gaveta</span>
                  <span style={summaryValueStyle}>{slot}</span>
                </div>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>SKU</span>
                  <span style={summaryValueStyle}>{product.sku_id || skuId}</span>
                </div>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>Produto</span>
                  <span style={summaryValueStyle}>{product.name || "-"}</span>
                </div>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>Preço</span>
                  <span style={priceStyle}>
                    {formatMoney(product.amount_cents, product.currency)}
                  </span>
                </div>
                <div style={summaryItemStyle}>
                  <span style={summaryLabelStyle}>Moeda</span>
                  <span style={summaryValueStyle}>{product.currency || "-"}</span>
                </div>
              </div>
            ) : (
              <p style={cardTextStyle}>Produto indisponível.</p>
            )}
          </section>

          <section style={cardStyle}>
            <h2 style={cardTitleStyle}>💳 Pagamento</h2>

            <div style={fieldGridStyle}>
              <label style={labelStyle}>
                Método de pagamento
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  style={inputStyle}
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
                <label style={labelStyle}>
                  Telefone MB WAY
                  <input
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    style={inputStyle}
                    placeholder="+351912345678"
                    disabled={submitting}
                  />
                </label>
              )}
            </div>

            <div style={noticeStyle}>
              <span style={noticeIconStyle}>ℹ️</span>
              <div>
                <strong>Informação importante:</strong>
                <p style={{ margin: "4px 0 0 0" }}>
                  O pedido criado aqui entra no fluxo ONLINE real, respeitando locker, gaveta,
                  SKU e método de pagamento. O preço final não é confiado ao frontend.
                </p>
              </div>
            </div>

            {submitError ? (
              <div style={errorBoxStyle}>
                <strong>Erro ao processar:</strong>
                <pre style={{ margin: "8px 0 0 0", fontSize: 12 }}>{submitError}</pre>
              </div>
            ) : null}

            <button
              onClick={handleCreateOrder}
              disabled={
                submitting ||
                productLoading ||
                lockerLoading ||
                !product ||
                !locker ||
                !paymentMethod ||
                !allowedPaymentMethods.length ||
                (paymentMethod === "MBWAY" && !customerPhone.trim())
              }
              style={{
                ...primaryButtonStyle,
                ...(submitting ? buttonDisabledStyle : {}),
              }}
            >
              {submitting ? (
                <>
                  <span style={spinnerSmallStyle} />
                  Processando...
                </>
              ) : currentStep === 3 ? (
                <>
                  <span style={successIconStyle}>✓</span>
                  Pedido Criado! Redirecionando...
                </>
              ) : (
                "Criar Pedido Online"
              )}
            </button>

            <div style={actionsStyle}>
              <Link
                to={`/comprar?region=${encodeURIComponent(region)}&locker_id=${encodeURIComponent(
                  lockerId
                )}`}
                style={secondaryButtonStyle}
              >
                ← Voltar
              </Link>
              <Link to="/meus-pedidos" style={secondaryButtonStyle}>
                Meus pedidos
              </Link>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

const pageStyle = {
  minHeight: "100vh",
  background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
  padding: "24px 16px",
};

const containerStyle = {
  maxWidth: 900,
  margin: "0 auto",
};

const heroCardStyle = {
  borderRadius: 20,
  padding: 28,
  marginBottom: 24,
  background: "white",
  boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
};

const heroContentStyle = {
  marginBottom: 20,
};

const titleStyle = {
  margin: "0 0 12px 0",
  fontSize: 32,
  fontWeight: 800,
  color: "#1a202c",
};

const subtitleStyle = {
  margin: 0,
  fontSize: 16,
  lineHeight: 1.6,
  color: "#4a5568",
};

const trustSignalsStyle = {
  display: "flex",
  gap: 24,
  flexWrap: "wrap",
  paddingTop: 20,
  borderTop: "1px solid #e2e8f0",
};

const trustItemStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: 14,
  color: "#4a5568",
};

const trustIconStyle = {
  fontSize: 20,
};

const trustTextStyle = {
  fontWeight: 500,
};

const stepsContainerStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 0,
  marginBottom: 32,
  padding: "24px 16px",
  background: "white",
  borderRadius: 16,
  boxShadow: "0 2px 4px rgba(0, 0, 0, 0.05)",
};

const stepStyle = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: 8,
  padding: "12px 20px",
  borderRadius: 12,
  background: "#e2e8f0",
  transition: "all 0.3s ease",
};

const stepActiveStyle = {
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
};

const stepIconStyle = {
  fontSize: 24,
  fontWeight: 700,
};

const stepLabelStyle = {
  fontSize: 13,
  fontWeight: 600,
};

const stepConnectorStyle = {
  width: 60,
  height: 3,
  background: "#e2e8f0",
  margin: "0 8px",
  transition: "all 0.3s ease",
};

const stepConnectorActiveStyle = {
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
};

const layoutStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  gap: 20,
};

const cardStyle = {
  borderRadius: 16,
  padding: 24,
  background: "white",
  boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
};

const errorCardStyle = {
  ...cardStyle,
  textAlign: "center",
  padding: 48,
};

const errorIconStyle = {
  fontSize: 48,
  marginBottom: 16,
};

const cardTitleStyle = {
  margin: "0 0 20px 0",
  fontSize: 20,
  fontWeight: 700,
  color: "#1a202c",
};

const cardTextStyle = {
  margin: 0,
  color: "#4a5568",
  lineHeight: 1.6,
};

const summaryGridStyle = {
  display: "grid",
  gap: 12,
};

const summaryItemStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "12px 0",
  borderBottom: "1px solid #e2e8f0",
  gap: 12,
};

const summaryLabelStyle = {
  fontSize: 14,
  color: "#718096",
  fontWeight: 500,
};

const summaryValueStyle = {
  fontSize: 14,
  color: "#1a202c",
  fontWeight: 600,
  textAlign: "right",
};

const priceStyle = {
  fontSize: 24,
  fontWeight: 800,
  color: "#667eea",
};

const fieldGridStyle = {
  display: "grid",
  gap: 16,
  marginBottom: 20,
};

const labelStyle = {
  display: "grid",
  gap: 8,
  fontWeight: 600,
  color: "#1a202c",
  fontSize: 14,
};

const inputStyle = {
  padding: "12px 14px",
  borderRadius: 10,
  border: "1px solid #cdb5e0",
  background: "#ffffff",
  color: "#1a202c",
  fontSize: 15,
  outline: "none",
  transition: "all 0.2s",
};

const noticeStyle = {
  padding: 16,
  borderRadius: 12,
  background: "#ebf8ff",
  border: "1px solid #bee3f8",
  display: "flex",
  gap: 12,
  alignItems: "flex-start",
  marginBottom: 20,
};

const noticeIconStyle = {
  fontSize: 20,
  flexShrink: 0,
};

const primaryButtonStyle = {
  width: "100%",
  padding: "16px 20px",
  borderRadius: 12,
  border: "none",
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  fontWeight: 700,
  fontSize: 16,
  cursor: "pointer",
  transition: "all 0.2s",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 8,
};

const buttonDisabledStyle = {
  opacity: 0.6,
  cursor: "not-allowed",
};

const secondaryButtonStyle = {
  textDecoration: "none",
  padding: "12px 16px",
  borderRadius: 10,
  border: "1px solid #e2e8f0",
  background: "#f7fafc",
  color: "#4a5568",
  fontWeight: 600,
  fontSize: 14,
  transition: "all 0.2s",
};

const actionsStyle = {
  display: "flex",
  gap: 12,
  marginTop: 16,
  flexWrap: "wrap",
};

const errorBoxStyle = {
  padding: 16,
  borderRadius: 12,
  background: "#fed7d7",
  border: "1px solid #feb2b2",
  color: "#c53030",
  marginBottom: 16,
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
};

const loadingStyle = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: 12,
  padding: 24,
  color: "#4a5568",
};

const spinnerStyle = {
  width: 40,
  height: 40,
  border: "3px solid #e2e8f0",
  borderTopColor: "#667eea",
  borderRadius: "50%",
  animation: "spin 0.8s linear infinite",
};

const spinnerSmallStyle = {
  width: 20,
  height: 20,
  border: "2px solid rgba(255,255,255,0.3)",
  borderTopColor: "white",
  borderRadius: "50%",
  animation: "spin 0.6s linear infinite",
};

const successIconStyle = {
  fontSize: 20,
};

if (typeof document !== "undefined") {
  const existingStyle = document.head.querySelector("#public-checkout-styles");
  if (!existingStyle) {
    const styleSheet = document.createElement("style");
    styleSheet.id = "public-checkout-styles";
    styleSheet.textContent = `
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(styleSheet);
  }
}