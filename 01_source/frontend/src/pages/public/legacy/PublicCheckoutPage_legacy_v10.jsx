// 01_source/frontend/src/pages/public/PublicCheckoutPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const BACKEND_SP =
  import.meta.env.VITE_BACKEND_SP_BASE_URL || "http://localhost:8201";

const BACKEND_PT =
  import.meta.env.VITE_BACKEND_PT_BASE_URL || "http://localhost:8202";

function formatMoney(cents, currency) {
  const value = Number(cents);
  if (!Number.isFinite(value)) return "-";

  const amount = value / 100;
  const locale = currency === "BRL" ? "pt-BR" : "pt-PT";

  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: currency || "EUR",
    }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency || ""}`.trim();
  }
}

function resolveBackendBase(region) {
  return region === "PT" ? BACKEND_PT : BACKEND_SP;
}

function paymentMethodLabel(method) {
  switch (method) {
    case "PIX":
      return "PIX";
    case "CARTAO":
      return "Cartão";
    case "MBWAY":
      return "MB WAY";
    case "MULTIBANCO_REFERENCE":
      return "Referência Multibanco";
    case "NFC":
      return "NFC";
    case "APPLE_PAY":
      return "Apple Pay";
    case "GOOGLE_PAY":
      return "Google Pay";
    case "MERCADO_PAGO_WALLET":
      return "Mercado Pago Wallet";
    default:
      return method || "-";
  }
}

function regionPaymentOptions(region) {
  if (region === "PT") {
    return [
      "CARTAO",
      "MBWAY",
      "MULTIBANCO_REFERENCE",
      "NFC",
      "APPLE_PAY",
      "GOOGLE_PAY",
      "MERCADO_PAGO_WALLET",
    ];
  }

  return ["PIX", "CARTAO", "NFC", "APPLE_PAY", "GOOGLE_PAY", "MERCADO_PAGO_WALLET"];
}

function walletProviderForMethod(method) {
  switch (method) {
    case "APPLE_PAY":
      return "applePay";
    case "GOOGLE_PAY":
      return "googlePay";
    case "MERCADO_PAGO_WALLET":
      return "mercadoPago";
    default:
      return undefined;
  }
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
    detail:
      parsed?.detail ??
      parsed?.message ??
      rawText ??
      `HTTP ${res.status}`,
  };
}

export default function PublicCheckoutPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const region = String(searchParams.get("region") || "SP").toUpperCase() === "PT" ? "PT" : "SP";
  const lockerId = String(searchParams.get("locker_id") || "").trim();
  const skuId = String(searchParams.get("sku_id") || "").trim();
  const slot = Number(searchParams.get("slot") || 0);

  const backendBase = useMemo(() => resolveBackendBase(region), [region]);

  const [product, setProduct] = useState(null);
  const [productLoading, setProductLoading] = useState(false);
  const [productError, setProductError] = useState("");

  const [paymentMethod, setPaymentMethod] = useState(region === "PT" ? "CARTAO" : "PIX");
  const [cardType, setCardType] = useState("creditCard");
  const [customerPhone, setCustomerPhone] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const invalidParams = !lockerId || !skuId || !slot;

  useEffect(() => {
    async function loadProduct() {
      if (invalidParams) return;

      setProductLoading(true);
      setProductError("");

      try {
        const res = await fetch(`${backendBase}/catalog/skus/${encodeURIComponent(skuId)}`, {
          headers: {
            "X-Locker-Id": lockerId,
          },
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
      } catch (e) {
        setProductError(String(e?.message || e));
        setProduct(null);
      } finally {
        setProductLoading(false);
      }
    }

    loadProduct();
  }, [backendBase, invalidParams, lockerId, skuId]);

  async function handleCreateOrder() {
    if (invalidParams || !product) {
      setSubmitError("Dados do checkout incompletos.");
      return;
    }

    setSubmitting(true);
    setSubmitError("");

    const payload = {
      region,
      sku_id: skuId,
      totem_id: lockerId,
      payment_method: paymentMethod,
      desired_slot: slot,
      amount_cents: Number(product.amount_cents),
    };

    if (paymentMethod === "CARTAO") {
      payload.card_type = cardType;
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

      const res = await fetch(`${ORDER_PICKUP_BASE}/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Dev-Bypass-Auth": "1",
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
              request_headers_sent: {
                "Content-Type": "application/json",
                "X-Dev-Bypass-Auth": "1",
                "X-Device-Fingerprint": deviceFp,
                "Idempotency-Key": idempotencyKey,
              },
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

      navigate(`/public/orders/${encodeURIComponent(orderId)}`, { replace: true });
    } catch (e) {
      setSubmitError(String(e?.message || e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <section style={heroCardStyle}>
          <span style={eyebrowStyle}>Checkout público</span>

          <h1 style={titleStyle}>Finalizar reserva online</h1>

          <p style={subtitleStyle}>
            Você está reservando uma gaveta real do locker/cacifo selecionado. O pedido será
            criado no canal ONLINE.
          </p>

          <div style={actionsStyle}>
            <Link
              to={`/comprar?region=${encodeURIComponent(region)}&locker_id=${encodeURIComponent(
                lockerId
              )}`}
              style={secondaryActionStyle}
            >
              Voltar ao catálogo
            </Link>

            <Link to="/meus-pedidos" style={secondaryActionStyle}>
              Meus pedidos
            </Link>
          </div>
        </section>

        {invalidParams ? (
          <section style={errorCardStyle}>
            <h2 style={cardTitleStyle}>Checkout inválido</h2>
            <p style={cardTextStyle}>
              Faltam dados obrigatórios da seleção. Volte ao catálogo e escolha uma gaveta.
            </p>
          </section>
        ) : (
          <div style={layoutStyle}>
            <section style={cardStyle}>
              <h2 style={cardTitleStyle}>Resumo da escolha</h2>

              {productLoading ? (
                <p style={cardTextStyle}>Carregando produto...</p>
              ) : productError ? (
                <pre style={errorBoxStyle}>{productError}</pre>
              ) : product ? (
                <div style={summaryGridStyle}>
                  <div><b>Região:</b> {region}</div>
                  <div><b>Locker / Cacifo:</b> {lockerId}</div>
                  <div><b>Gaveta / Slot:</b> {slot}</div>
                  <div><b>SKU:</b> {product.sku_id || skuId}</div>
                  <div><b>Produto:</b> {product.name || "-"}</div>
                  <div><b>Preço:</b> {formatMoney(product.amount_cents, product.currency)}</div>
                  <div><b>Moeda:</b> {product.currency || "-"}</div>
                </div>
              ) : (
                <p style={cardTextStyle}>Produto indisponível.</p>
              )}
            </section>

            <section style={cardStyle}>
              <h2 style={cardTitleStyle}>Pagamento</h2>

              <div style={fieldGridStyle}>
                <label style={labelStyle}>
                  Método de pagamento
                  <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    style={inputStyle}
                    disabled={submitting}
                  >
                    {regionPaymentOptions(region).map((method) => (
                      <option key={method} value={method}>
                        {paymentMethodLabel(method)}
                      </option>
                    ))}
                  </select>
                </label>

                {paymentMethod === "CARTAO" ? (
                  <label style={labelStyle}>
                    Tipo do cartão
                    <select
                      value={cardType}
                      onChange={(e) => setCardType(e.target.value)}
                      style={inputStyle}
                      disabled={submitting}
                    >
                      <option value="creditCard">Crédito</option>
                      <option value="debitCard">Débito</option>
                    </select>
                  </label>
                ) : null}

                {paymentMethod === "MBWAY" ? (
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
                ) : null}
              </div>

              <div style={noticeStyle}>
                O pedido criado aqui entra no fluxo ONLINE real, respeitando locker, gaveta,
                SKU e método de pagamento.
              </div>

              {submitError ? <pre style={errorBoxStyle}>{submitError}</pre> : null}

              <button
                onClick={handleCreateOrder}
                disabled={
                  submitting ||
                  productLoading ||
                  !product ||
                  (paymentMethod === "MBWAY" && !customerPhone.trim())
                }
                style={primaryButtonStyle}
              >
                {submitting ? "Criando pedido..." : "Criar pedido online"}
              </button>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}

const pageStyle = {
  padding: 24,
};

const containerStyle = {
  maxWidth: 1120,
  margin: "0 auto",
};

const heroCardStyle = {
  borderRadius: 20,
  padding: 28,
  marginBottom: 20,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.06)",
};

const eyebrowStyle = {
  display: "inline-block",
  marginBottom: 10,
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "#666",
};

const titleStyle = {
  margin: 0,
  fontSize: 34,
  lineHeight: 1.1,
};

const subtitleStyle = {
  marginTop: 14,
  marginBottom: 0,
  fontSize: 16,
  lineHeight: 1.6,
  color: "rgba(82,238,5,1)",
  maxWidth: 760,
};

const actionsStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: 12,
  marginTop: 22,
};

const secondaryActionStyle = {
  textDecoration: "none",
  padding: "12px 16px",
  borderRadius: 12,
  border: "1px solid #d1d5db",
  background: "#f9fafb",
  color: "#111827",
  fontWeight: 700,
};

const layoutStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  gap: 16,
};

const cardStyle = {
  borderRadius: 16,
  padding: 18,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.06)",
  display: "grid",
  gap: 14,
};

const errorCardStyle = {
  borderRadius: 16,
  padding: 18,
  border: "1px solid rgba(255,0,0,0.15)",
  background: "#fff5f5",
};

const cardTitleStyle = {
  margin: 0,
  fontSize: 20,
};

const cardTextStyle = {
  margin: 0,
  color: "#666",
  lineHeight: 1.6,
};

const summaryGridStyle = {
  display: "grid",
  gap: 8,
  color: "#fff",
  fontSize: 15,
};

const fieldGridStyle = {
  display: "grid",
  gap: 12,
};

const labelStyle = {
  display: "grid",
  gap: 8,
  fontWeight: 700,
  color: "rgba(82,238,5,1)",
};

const inputStyle = {
  padding: "12px 14px",
  borderRadius: 12,
  border: "1px solid #d1d5db",
  background: "#fff",
  color: "#111827",
};

const noticeStyle = {
  padding: 12,
  borderRadius: 12,
  background: "#f3f4f6",
  color: "#374151",
  lineHeight: 1.5,
};

const primaryButtonStyle = {
  padding: "12px 16px",
  borderRadius: 12,
  border: "1px solid #111827",
  background: "#111827",
  color: "#fff",
  fontWeight: 800,
  cursor: "pointer",
};

const errorBoxStyle = {
  margin: 0,
  padding: 14,
  borderRadius: 12,
  background: "#2b1d1d",
  color: "#ffb4b4",
  border: "1px solid rgba(255,255,255,0.12)",
  overflow: "auto",
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
};