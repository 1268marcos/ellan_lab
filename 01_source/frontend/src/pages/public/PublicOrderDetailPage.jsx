// 01_source/frontend/src/pages/public/PublicOrderDetailPage.jsx
// 18/04/2026 - atualização : function getPickupMessage()
// 18/04/2026 - melhoramento UX/CX para localização locker
// 19/04/2026 - ajuste em datas apresentadas com formatDateTimeByRegion()
// 21/04/2026 - nova function getPickupMessage(order, pickup) {}
// 21/04/2026 - ajuste UX/CX retirada concluída + data real de retirada

import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import {
  fetchOrderDetail,
  fetchOrderInvoicePdf,
  fetchOrderPickup,
  resendOrderInvoiceEmail,
} from "../../services/publicApi";

import { formatDateTimeByRegion } from "../../utils/datetime";

const API_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const FRONTEND_BASE =
  import.meta.env.VITE_FRONTEND_BASE_URL || window.location.origin;

function normalize(value) {
  return String(value || "").trim().toUpperCase();
}

function formatLockerAddress(locker) {
  if (!locker || typeof locker !== "object") return "-";

  const parts = [
    locker.address_line,
    locker.address_number,
    locker.address_extra,
    locker.district,
    locker.city,
    locker.state,
    locker.postal_code,
    locker.country,
  ]
    .map((item) => String(item || "").trim())
    .filter(Boolean);

  if (parts.length === 0) return "-";

  return parts.join(" • ");
}

function getLockerDisplayName(order) {
  const locker = order?.locker;
  if (locker?.display_name) return locker.display_name;
  return order?.totem_id || "-";
}

function getLockerTechnicalId(order) {
  const locker = order?.locker;
  return locker?.locker_id || order?.totem_id || "-";
}

function getLockerFullAddress(order) {
  const locker = order?.locker;
  return formatLockerAddress(locker);
}

function getPickedUpAt(order, pickup) {
  return (
    order?.picked_up_at ||
    order?.redeemed_at ||
    order?.pickup_redeemed_at ||
    order?.item_removed_at ||
    order?.pickup_item_removed_at ||
    order?.door_closed_at ||
    order?.pickup_door_closed_at ||
    order?.door_opened_at ||
    order?.pickup_door_opened_at ||
    order?.pickup?.redeemed_at ||
    order?.pickup?.item_removed_at ||
    order?.pickup?.door_closed_at ||
    order?.pickup?.door_opened_at ||
    pickup?.redeemed_at ||
    pickup?.item_removed_at ||
    pickup?.door_closed_at ||
    pickup?.door_opened_at ||
    "-"
  );
}

export default function PublicOrderDetailPage() {
  const { orderId } = useParams();
  const { token, loading, isAuthenticated } = useAuth();

  const [order, setOrder] = useState(null);
  const [pickup, setPickup] = useState(null);
  const [error, setError] = useState("");
  const [pageLoading, setPageLoading] = useState(true);
  const [resendBusy, setResendBusy] = useState(false);
  const [resendMessage, setResendMessage] = useState("");
  const [pdfBusy, setPdfBusy] = useState(false);

  useEffect(() => {
    let active = true;

    async function load() {
      if (loading) {
        return;
      }

      if (!isAuthenticated || !token || !orderId) {
        if (!active) return;
        setOrder(null);
        setPickup(null);
        setError("");
        setPageLoading(false);
        return;
      }

      try {
        if (active) {
          setPageLoading(true);
          setError("");
          setOrder(null);
          setPickup(null);
        }

        const orderData = await fetchOrderDetail(token, orderId);
        if (!active) return;

        setOrder(orderData);

        try {
          const pickupData = await fetchOrderPickup(token, orderId);
          if (!active) return;
          setPickup(pickupData);
        } catch {
          if (!active) return;
          setPickup(null);
        }
      } catch (err) {
        if (!active) return;
        setOrder(null);
        setPickup(null);
        setError(err?.message || "Erro ao carregar pedido");
      } finally {
        if (active) {
          setPageLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [token, loading, isAuthenticated, orderId]);

  const pickupMessage = useMemo(() => {
    return getPickupMessage(order, pickup);
  }, [order, pickup]);

  const receiptCode = useMemo(() => normalize(order?.receipt_code), [order?.receipt_code]);
  const hasOrderForInvoiceActions = Boolean(order?.id);

  const receiptPrintUrl = useMemo(() => {
    if (!receiptCode) return "";
    return `${API_BASE}/public/fiscal/print/${encodeURIComponent(receiptCode)}`;
  }, [receiptCode]);

  const receiptJsonUrl = useMemo(() => {
    if (!receiptCode) return "";
    return `${API_BASE}/public/fiscal/by-code/${encodeURIComponent(receiptCode)}`;
  }, [receiptCode]);

  const receiptDeepLink = useMemo(() => {
    if (!receiptCode) return "";
    return `${FRONTEND_BASE}/comprovante?code=${encodeURIComponent(receiptCode)}`;
  }, [receiptCode]);

  const rawExpiresAt =
    order?.expires_at ||
    order?.pickup_deadline_at ||
    pickup?.expires_at ||
    null;

  const expiresAtDate = rawExpiresAt ? new Date(rawExpiresAt) : null;
  const expiredByTime =
    expiresAtDate instanceof Date &&
    !Number.isNaN(expiresAtDate.getTime()) &&
    Date.now() > expiresAtDate.getTime();

  const pickupStatusNormalized = String(
    pickup?.status || order?.pickup_status || ""
  ).toUpperCase();

  const pickupLifecycleNormalized = String(
    pickup?.lifecycle_stage || order?.pickup_lifecycle_stage || ""
  ).toUpperCase();

  const orderStatusNormalized = String(order?.status || "").toUpperCase();

  const pickupExpiredEffective =
    orderStatusNormalized === "EXPIRED" ||
    orderStatusNormalized === "EXPIRED_CREDIT_50" ||
    pickupStatusNormalized === "EXPIRED" ||
    expiredByTime ||
    order?.pickup_expired_effective === true;

  const pickupRedeemedEffective =
    pickupStatusNormalized === "REDEEMED" ||
    pickupLifecycleNormalized === "COMPLETED" ||
    orderStatusNormalized === "PICKED_UP" ||
    orderStatusNormalized === "DISPENSED";

  const canShowPickupCredentials =
    !!order && !pickupExpiredEffective && !pickupRedeemedEffective;

  const pickedUpAtValue = useMemo(() => {
    return getPickedUpAt(order, pickup);
  }, [order, pickup]);

  function copyReceiptLink() {
    if (!receiptDeepLink) return;
    navigator.clipboard?.writeText(receiptDeepLink);
    window.alert("Link do comprovante copiado.");
  }

  async function handleResendInvoiceEmail() {
    if (!token || !order?.id) return;
    setResendBusy(true);
    setResendMessage("");
    try {
      const out = await resendOrderInvoiceEmail(token, order.id);
      setResendMessage(out?.message || "Reenvio solicitado com sucesso.");
    } catch (err) {
      setResendMessage(String(err?.message || err));
    } finally {
      setResendBusy(false);
    }
  }

  function downloadBase64Pdf(base64Content, filename) {
    const byteChars = atob(base64Content);
    const byteNumbers = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i += 1) {
      byteNumbers[i] = byteChars.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "invoice.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  async function handleDownloadInvoicePdf() {
    if (!token || !order?.id) return;
    setPdfBusy(true);
    setResendMessage("");
    try {
      const out = await fetchOrderInvoicePdf(token, order.id);
      if (!out?.content_base64) {
        throw new Error("PDF da invoice ainda não disponível.");
      }
      downloadBase64Pdf(out.content_base64, out.filename || `invoice-${order.id}.pdf`);
      setResendMessage("Download do PDF da invoice iniciado.");
    } catch (err) {
      setResendMessage(String(err?.message || err));
    } finally {
      setPdfBusy(false);
    }
  }

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <div style={headerRowStyle}>
          <div>
            <h1 style={titleStyle}>Detalhe do pedido</h1>
            <p style={subtitleStyle}>
              Consulte os dados do pedido e as informações de retirada.
            </p>
          </div>

          <Link to="/meus-pedidos" style={backLinkStyle}>
            Voltar para meus pedidos
          </Link>
        </div>

        {loading || pageLoading ? (
          <section style={cardStyle}>
            <p style={mutedStyle}>Carregando pedido...</p>
          </section>
        ) : null}

        {!loading && !pageLoading && error ? (
          <section style={errorCardStyle}>
            <strong>Não foi possível carregar este pedido.</strong>
            <p style={{ marginTop: 8, marginBottom: 0 }}>{error}</p>
          </section>
        ) : null}

        {!loading && !pageLoading && !error && !order ? (
          <section style={cardStyle}>
            <p style={mutedStyle}>Pedido não encontrado.</p>
          </section>
        ) : null}

        {!loading && !pageLoading && !error && order ? (
          <>
            <section style={cardStyle}>
              <div style={sectionHeaderStyle}>
                <h2 style={sectionTitleStyle}>Pedido</h2>
                <p style={sectionMetaStyle}>
                  Realizado em {formatDateTime(order.created_at)} - ID {order.id}
                </p>
              </div>

              {order.credit_application?.applied ? (
                <div style={creditAppliedBannerStyle}>
                  <strong style={{ display: "block", marginBottom: 6 }}>
                    Crédito aplicado neste pedido
                  </strong>
                  <span style={{ fontSize: 14, lineHeight: 1.5 }}>
                    O valor cobrado já inclui o desconto do crédito de loja. Os detalhes aparecem abaixo na
                    seção &quot;Crédito no checkout&quot;.
                  </span>
                </div>
              ) : null}

              <div style={detailsGridStyle}>
                <Field label="Método" value={order.payment_method} />
                <Field label="Status" value={order.status} />
                <Field label="Canal" value={order.channel} />
                <Field label="Locker" value={getLockerDisplayName(order)} />
                <Field label="ID técnico do locker" value={getLockerTechnicalId(order)} />
                <Field label="Endereço do locker" value={getLockerFullAddress(order)} />
                <Field label="Gaveta/Slot" value={order.slot} />
                <Field label="Produto" value={order.sku_id} />
                <Field
                  label={
                    order.credit_application?.applied
                      ? "Valor cobrado (após crédito)"
                      : "Valor"
                  }
                  value={formatMoneyCents(order.amount_cents, order.currency || "BRL")}
                />
                <Field label="Pago em" value={formatDateTimeByRegion(order.paid_at, order.region)} />

                <Field
                  label="Retirado em"
                  value={formatDateTimeByRegion(order.picked_up_at, order.region)}
                />

                {/* <Field
                  label="Retirado em"
                  value={formatDateTimeByRegion(
                    pickedUpAtValue === "-" ? null : pickedUpAtValue,
                    order?.region
                  )}
                /> */}

                {!pickupRedeemedEffective ? (
                  <Field
                    label="Expira a retirada em"
                    value={formatDateTimeByRegion(order.expires_at || pickup?.expires_at, order.region)}
                  />
                ) : null}
              </div>

              {hasCheckoutCreditSection(order.credit_application) ? (
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #e5e7eb" }}>
                  <h3 style={{ margin: "0 0 10px", fontSize: 16 }}>Crédito no checkout</h3>
                  <div style={detailsGridStyle}>
                    <Field
                      label="Status do crédito"
                      value={order.credit_application.applied ? "Aplicado" : "Não aplicado"}
                    />
                    <Field
                      label="Motivo"
                      value={creditReasonLabel(order.credit_application.reason)}
                    />
                    {order.credit_application.applied && order.credit_application.credit_id ? (
                      <Field label="ID do crédito" value={String(order.credit_application.credit_id)} />
                    ) : null}
                    {typeof order.credit_application.base_amount_cents === "number" ? (
                      <Field
                        label="Valor base (checkout)"
                        value={formatMoneyCents(
                          order.credit_application.base_amount_cents,
                          order.credit_application.currency || order.currency || "BRL"
                        )}
                      />
                    ) : null}
                    {order.credit_application.applied ? (
                      <Field
                        label="Desconto (crédito)"
                        value={formatMoneyCents(
                          order.credit_application.discount_cents,
                          order.credit_application.currency || order.currency || "BRL"
                        )}
                      />
                    ) : null}
                    {typeof order.credit_application.final_amount_cents === "number" ? (
                      <Field
                        label="Valor final cobrado (checkout)"
                        value={formatMoneyCents(
                          order.credit_application.final_amount_cents,
                          order.credit_application.currency || order.currency || "BRL"
                        )}
                      />
                    ) : null}
                  </div>
                </div>
              ) : null}
            </section>

            {hasOrderForInvoiceActions ? (
              <section style={cardStyle}>
                <div style={sectionHeaderStyle}>
                  <h2 style={sectionTitleStyle}>Invoice / comprovante fiscal</h2>
                  <p style={sectionMetaStyle}>
                    Ações fiscais do pedido (consulta e reenvio por e-mail).
                  </p>
                </div>

                <div style={detailsGridStyle}>
                  <Field label="Código" value={receiptCode || "Ainda não disponível"} />
                  <Field label="Página pública" value={receiptCode ? receiptDeepLink : "-"} />
                </div>

                <div style={actionsRowStyle}>
                  {receiptCode ? (
                    <a
                      href={receiptDeepLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={actionButtonStyle}
                    >
                      Abrir página do comprovante
                    </a>
                  ) : null}

                  {receiptCode ? (
                    <button
                      type="button"
                      onClick={copyReceiptLink}
                      style={actionButtonStyle}
                    >
                      Copiar link
                    </button>
                  ) : null}

                  {receiptCode ? (
                    <a
                      href={receiptPrintUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={actionButtonStyle}
                    >
                      Abrir impressão
                    </a>
                  ) : null}

                  {receiptCode ? (
                    <a
                      href={receiptJsonUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={actionButtonStyle}
                    >
                      Ver invoice associada (JSON)
                    </a>
                  ) : null}

                  {receiptCode ? (
                    <button
                      type="button"
                      onClick={() =>
                        window.open(
                          receiptPrintUrl,
                          "_blank",
                          "noopener,noreferrer"
                        )
                      }
                      style={actionButtonStyle}
                    >
                      Imprimir / PDF
                    </button>
                  ) : null}

                  <button
                    type="button"
                    onClick={() => void handleResendInvoiceEmail()}
                    style={actionButtonStyle}
                    disabled={resendBusy}
                  >
                    {resendBusy ? "Solicitando..." : "Reenviar invoice por e-mail"}
                  </button>

                  <button
                    type="button"
                    onClick={() => void handleDownloadInvoicePdf()}
                    style={actionButtonStyle}
                    disabled={pdfBusy}
                  >
                    {pdfBusy ? "Preparando..." : "Baixar PDF da invoice"}
                  </button>
                </div>

                <div style={invoiceHintStyle}>
                  <strong>Invoice associada ao pedido:</strong>{" "}
                  use os botões acima para consultar JSON/print da invoice vinculada.
                  {order?.channel === "ONLINE" ? (
                    <>
                      {" "}
                      Para pedidos online, o envio de e-mail fiscal é disparado no fluxo de emissão (quando
                      `receipt_email`/`guest_email` está disponível).
                    </>
                  ) : null}
                </div>
                {resendMessage ? <p style={invoiceResendMsgStyle}>{resendMessage}</p> : null}
              </section>
            ) : null}

            <section style={cardStyle}>
              <div style={sectionHeaderStyle}>
                <h2 style={sectionTitleStyle}>
                  {pickupRedeemedEffective ? "Retirada concluída" : "Retirada"}
                </h2>
                <p style={sectionMetaStyle}>
                  {pickupRedeemedEffective
                    ? "Registro da retirada realizada com sucesso."
                    : "Informações para uso no kiosk/totem"}
                </p>
              </div>

              {order ? (
                <>
                  <div style={detailsGridStyle}>
                    <Field
                      label="Status"
                      value={pickup?.status || order?.pickup_status || order?.status}
                    />

                    {pickupRedeemedEffective ? (
                      <Field
                        label="Retirado em"
                        value={formatDateTimeByRegion(
                          pickedUpAtValue === "-" ? null : pickedUpAtValue,
                          order?.region
                        )}
                      />
                    ) : (
                      <Field
                        label="Expira em"
                        value={formatDateTimeByRegion(order.expires_at || pickup?.expires_at, order.region)}
                      />
                    )}

                    <Field
                      label="Código de retirada manual"
                      value={
                        canShowPickupCredentials
                          ? (order?.manual_code || pickup?.manual_code_masked || "-")
                          : "-"
                      }
                    />
                  </div>

                  {canShowPickupCredentials ? (
                    <div style={{ marginTop: 16 }}>
                      <label style={labelStyle}>QR payload</label>
                      <textarea
                        readOnly
                        value={order?.qr_payload || pickup?.qr_value || ""}
                        style={textAreaStyle}
                      />
                    </div>
                  ) : null}

                  <div style={{ marginTop: 12 }}>
                    <p style={infoTextStyle}>{pickupMessage}</p>
                  </div>
                </>
              ) : (
                <div style={infoCardStyle}>
                  <strong style={infoTitleStyle}>Retirada indisponível no momento</strong>
                  <p style={infoTextStyle}>{pickupMessage}</p>
                </div>
              )}
            </section>
          </>
        ) : null}
      </div>
    </main>
  );
}

function Field({ label, value }) {
  return (
    <div style={fieldStyle}>
      <span style={fieldLabelStyle}>{label}</span>
      <div style={fieldValueStyle}>{value || "-"}</div>
    </div>
  );
}

function getPickupMessage(order, pickup) {
  if (!order) {
    return "Não foi possível determinar o estado da retirada deste pedido.";
  }

  const status = String(order.status || "").toUpperCase();
  const paymentStatus = String(order.payment_status || "").toUpperCase();
  const pickupStatus = String(pickup?.status || order.pickup_status || "").toUpperCase();

  const rawExpiresAt =
    order?.expires_at ||
    order?.pickup_deadline_at ||
    pickup?.expires_at ||
    null;

  let expiredByTime = false;
  if (rawExpiresAt) {
    const exp = new Date(rawExpiresAt);
    expiredByTime = !Number.isNaN(exp.getTime()) && Date.now() > exp.getTime();
  }

  const isExpired =
    status === "EXPIRED" ||
    status === "EXPIRED_CREDIT_50" ||
    pickupStatus === "EXPIRED" ||
    expiredByTime;

  if (isExpired) {
    return "O prazo de retirada expirou. Este pedido não está mais disponível no locker.";
  }

  if (status === "CANCELLED" || status === "CANCELED") {
    return "Este pedido foi cancelado. A retirada não está disponível.";
  }

  if (status === "PAYMENT_PENDING" || paymentStatus === "PENDING_CUSTOMER_ACTION") {
    return "A retirada será liberada somente após a confirmação do pagamento.";
  }

  if (paymentStatus === "FAILED" || paymentStatus === "DECLINED") {
    return "O pagamento não foi aprovado. Por isso, a retirada não foi liberada.";
  }

  // if (pickupStatus === "REDEEMED" || status === "PICKED_UP" || status === "DISPENSED") {
  //  return "Este pedido já foi retirado com sucesso.";
  // }


  if (status === "DISPENSED") {
    return "A máquina foi liberada para retirada. Se você não conseguiu retirar, entre em contato com a Central de Suporte.";
  }

  if (pickupStatus === "REDEEMED" || status === "PICKED_UP") {
    return "Retirada registrada com sucesso.";
  }


  if (status === "PAID_PENDING_PICKUP") {
    return "O pedido foi pago e está disponível para retirada no kiosk/totem.";
  }

  return "Os dados de retirada ainda não estão disponíveis para o estado atual deste pedido.";
}

function formatDateTime(value) {
  if (!value) return "-";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function formatMoneyCents(amountCents, currency = "BRL") {
  if (amountCents == null || amountCents === "") return "-";

  const numeric = Number(amountCents);
  if (Number.isNaN(numeric)) return String(amountCents);

  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: currency || "BRL",
  }).format(numeric / 100);
}

function hasCheckoutCreditSection(cap) {
  if (!cap || typeof cap !== "object") return false;
  return (
    cap.requested === true ||
    cap.applied === true ||
    cap.credit_id != null ||
    (typeof cap.discount_cents === "number" && cap.discount_cents > 0)
  );
}

function creditReasonLabel(reason) {
  const map = {
    applied: "Crédito aplicado com sucesso.",
    not_requested: "Crédito não solicitado no checkout.",
    missing_user: "Usuário não identificado para aplicar crédito.",
    currency_mismatch: "Moeda da carteira não compatível com o pedido; crédito não aplicado.",
    no_eligible_credit: "Nenhum crédito elegível no momento do checkout.",
  };
  return map[reason] || reason || "—";
}

const creditAppliedBannerStyle = {
  marginBottom: 16,
  padding: "12px 14px",
  borderRadius: 12,
  border: "1px solid #bfdbfe",
  background: "#eff6ff",
  color: "#1e3a8a",
};

const pageStyle = {
  padding: 24,
};

const containerStyle = {
  maxWidth: 960,
  margin: "0 auto",
};

const headerRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 16,
  flexWrap: "wrap",
  marginBottom: 20,
};

const titleStyle = {
  margin: 0,
  fontSize: 28,
};

const subtitleStyle = {
  marginTop: 8,
  marginBottom: 0,
  color: "#555",
};

const backLinkStyle = {
  textDecoration: "none",
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #d1d5db",
  background: "#f9fafb",
  color: "#111827",
  fontWeight: 600,
};

const cardStyle = {
  padding: 16,
  borderRadius: 14,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.06)",
  marginBottom: 16,
};

const errorCardStyle = {
  padding: 16,
  borderRadius: 14,
  border: "1px solid #fecaca",
  background: "#fff1f2",
  color: "#991b1b",
};

const infoCardStyle = {
  padding: 14,
  borderRadius: 12,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.04)",
};

const infoTitleStyle = {
  display: "block",
  marginBottom: 8,
};

const infoTextStyle = {
  margin: 0,
  color: "#666",
  lineHeight: 1.5,
};

const mutedStyle = {
  margin: 0,
  color: "#666",
};

const sectionHeaderStyle = {
  marginBottom: 16,
};

const sectionTitleStyle = {
  margin: 0,
  fontSize: 20,
};

const sectionMetaStyle = {
  marginTop: 6,
  marginBottom: 0,
  color: "#666",
  fontSize: 14,
};

const detailsGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: 12,
};

const fieldStyle = {
  padding: 12,
  borderRadius: 12,
  border: "1px solid #f0f0f0",
  background: "rgba(255,255,255,0.06)",
};

const fieldLabelStyle = {
  display: "block",
  fontSize: 12,
  color: "#666",
  marginBottom: 6,
};

const fieldValueStyle = {
  wordBreak: "break-word",
};

const labelStyle = {
  display: "block",
  fontSize: 12,
  color: "#666",
  marginBottom: 6,
};

const textAreaStyle = {
  width: "100%",
  minHeight: 120,
  borderRadius: 10,
  border: "1px solid #d1d5db",
  padding: 12,
  resize: "vertical",
  boxSizing: "border-box",
  fontFamily: "inherit",
};

const actionsRowStyle = {
  marginTop: 16,
  display: "flex",
  gap: 10,
  flexWrap: "wrap",
};

const actionButtonStyle = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #d1d5db",
  background: "#f9fafb",
  color: "#111827",
  textDecoration: "none",
  fontWeight: 600,
  cursor: "pointer",
};

const invoiceHintStyle = {
  marginTop: 12,
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid #bfdbfe",
  background: "#eff6ff",
  color: "#1e3a8a",
  fontSize: 13,
  lineHeight: 1.5,
};

const invoiceResendMsgStyle = {
  marginTop: 8,
  marginBottom: 0,
  fontSize: 13,
  color: "#334155",
};