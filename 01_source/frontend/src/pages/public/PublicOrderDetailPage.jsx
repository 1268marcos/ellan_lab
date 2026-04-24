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
  generateOrderInvoiceNow,
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

const INVOICE_OPS_ROLES = ["admin_operacao", "suporte", "auditoria"];

export default function PublicOrderDetailPage() {
  const { orderId } = useParams();
  const { token, loading, isAuthenticated, hasRole } = useAuth();

  const [order, setOrder] = useState(null);
  const [pickup, setPickup] = useState(null);
  const [error, setError] = useState("");
  const [pageLoading, setPageLoading] = useState(true);
  const [resendBusy, setResendBusy] = useState(false);
  const [resendMessage, setResendMessage] = useState("");
  const [pdfBusy, setPdfBusy] = useState(false);
  const [forceBusy, setForceBusy] = useState(false);
  const [showFiscalLegend, setShowFiscalLegend] = useState(false);

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
  const canForceGenerateInvoice = INVOICE_OPS_ROLES.some((role) => hasRole(role));
  const receiptLookupSupported = Boolean(order?.receipt_lookup_supported);
  const invoiceManualFallback = Boolean(order?.invoice_manual_fallback);
  const isBillingInvoice = Boolean(order?.is_billing_invoice);
  const invoiceId = String(order?.invoice_id || "").trim();
  const hasInvoiceGenerated = Boolean(invoiceId || receiptCode);
  const hasEmailTarget = Boolean(String(order?.guest_email || "").trim());
  const fiscalState = useMemo(() => {
    if (invoiceManualFallback) {
      return {
        code: "GERADO_MANUALMENTE",
        label: "Gerado manualmente",
        detail: "Invoice gerada por ação operacional (fallback sem domain_event).",
      };
    }
    if (hasInvoiceGenerated) {
      return {
        code: "GERADO",
        label: "Gerado",
        detail: "Documento fiscal já associado ao pedido.",
      };
    }
    if (!hasEmailTarget) {
      return {
        code: "SEM_DESTINATARIO_EMAIL",
        label: "Pendente (sem destinatário de e-mail)",
        detail: "Não há e-mail de destinatário no pedido para envio automático.",
      };
    }
    return {
      code: "PENDENTE",
      label: "Pendente",
      detail: "Aguardando materialização da invoice no billing fiscal.",
    };
  }, [hasEmailTarget, hasInvoiceGenerated, invoiceManualFallback]);
  const fiscalStateVisual = useMemo(() => getFiscalStateVisual(fiscalState.code), [fiscalState.code]);

  const receiptPrintUrl = useMemo(() => {
    const fromOrder = String(order?.receipt_print_path || "").trim();
    if (fromOrder) {
      return `${API_BASE}${fromOrder.startsWith("/") ? "" : "/"}${fromOrder}`;
    }
    if (!receiptCode || !receiptLookupSupported) return "";
    return `${API_BASE}/public/fiscal/print/${encodeURIComponent(receiptCode)}`;
  }, [order?.receipt_print_path, receiptCode, receiptLookupSupported]);

  const receiptJsonUrl = useMemo(() => {
    const fromOrder = String(order?.receipt_json_path || "").trim();
    if (fromOrder) {
      return `${API_BASE}${fromOrder.startsWith("/") ? "" : "/"}${fromOrder}`;
    }
    if (!receiptCode || !receiptLookupSupported) return "";
    return `${API_BASE}/public/fiscal/by-code/${encodeURIComponent(receiptCode)}`;
  }, [order?.receipt_json_path, receiptCode, receiptLookupSupported]);

  const receiptDeepLink = useMemo(() => {
    if (!receiptCode || !receiptLookupSupported) return "";
    return `${FRONTEND_BASE}/comprovante?code=${encodeURIComponent(receiptCode)}`;
  }, [receiptCode, receiptLookupSupported]);

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

  async function copyInvoiceId() {
    if (!invoiceId) return;
    try {
      await navigator.clipboard?.writeText(invoiceId);
      setResendMessage(`invoice_id copiado: ${invoiceId}`);
    } catch {
      setResendMessage("Não foi possível copiar o invoice_id.");
    }
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

  async function handleGenerateInvoiceNow() {
    if (!token || !order?.id) return;
    setForceBusy(true);
    setResendMessage("");
    try {
      const out = await generateOrderInvoiceNow(token, order.id);
      const generatedInvoiceId = out?.billing?.invoice?.id;
      setResendMessage(
        generatedInvoiceId
          ? `Invoice gerada com sucesso (invoice_id=${generatedInvoiceId}).`
          : (out?.message || "Invoice gerada com sucesso.")
      );
      const orderData = await fetchOrderDetail(token, order.id);
      setOrder(orderData);
    } catch (err) {
      setResendMessage(String(err?.message || err));
    } finally {
      setForceBusy(false);
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
                  <Field
                    label="Estado fiscal"
                    value={
                      <span
                        style={{
                          ...fiscalStateBadgeStyleBase,
                          ...fiscalStateVisual.style,
                        }}
                        aria-label={`Estado fiscal ${fiscalState.label}`}
                      >
                        <span aria-hidden="true">{fiscalStateVisual.icon}</span>
                        <span>{fiscalState.label}</span>
                      </span>
                    }
                  />
                  <Field label="Código" value={receiptCode || "Ainda não disponível"} />
                  <Field label="Invoice ID" value={invoiceId || "Ainda não disponível"} />
                  <Field label="Página pública" value={receiptDeepLink || "-"} />
                </div>
                <div
                  style={{
                    ...fiscalStateHintStyle,
                    borderColor: fiscalStateVisual.style.borderColor,
                    background: fiscalStateVisual.hintBackground,
                    color: fiscalStateVisual.hintColor,
                  }}
                >
                  <strong>Estado atual:</strong> {fiscalState.code} - {fiscalState.detail}
                </div>
                {invoiceManualFallback ? (
                  <div style={invoiceManualBadgeStyle}>
                    Invoice gerada manualmente (fallback sem domain_event)
                  </div>
                ) : null}
                {isBillingInvoice ? (
                  <div style={invoiceSourceBadgeStyle}>
                    Fonte: billing fiscal
                    {invoiceId ? ` • invoice_id=${invoiceId}` : ""}
                  </div>
                ) : null}

                <div style={actionsRowStyle}>
                  {receiptDeepLink ? (
                    <a
                      href={receiptDeepLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={actionButtonStyle}
                    >
                      Abrir página do comprovante
                    </a>
                  ) : null}

                  {receiptDeepLink ? (
                    <button
                      type="button"
                      onClick={copyReceiptLink}
                      style={actionButtonStyle}
                    >
                      Copiar link
                    </button>
                  ) : null}

                  {receiptPrintUrl ? (
                    <a
                      href={receiptPrintUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={actionButtonStyle}
                    >
                      Abrir impressão
                    </a>
                  ) : null}

                  {receiptJsonUrl ? (
                    <a
                      href={receiptJsonUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={actionButtonStyle}
                    >
                      Ver invoice associada (JSON)
                    </a>
                  ) : null}

                  {receiptPrintUrl ? (
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

                  {canForceGenerateInvoice ? (
                    <button
                      type="button"
                      onClick={() => void handleGenerateInvoiceNow()}
                      style={actionButtonStyle}
                      disabled={forceBusy}
                    >
                      {forceBusy ? "Gerando..." : "Gerar invoice agora"}
                    </button>
                  ) : null}

                  {invoiceId ? (
                    <button
                      type="button"
                      onClick={() => void copyInvoiceId()}
                      style={actionButtonStyle}
                    >
                      Copiar invoice_id
                    </button>
                  ) : null}
                </div>

                <div style={invoiceHintStyle}>
                  <strong>Invoice associada ao pedido:</strong>{" "}
                  use os botões acima para consultar JSON/print da invoice vinculada.
                  {isBillingInvoice && !receiptLookupSupported ? (
                    <>
                      {" "}
                      Para invoice do billing, os links de comprovante legado
                      (`/public/fiscal/by-code`) podem não existir para esse código.
                    </>
                  ) : null}
                  {order?.channel === "ONLINE" ? (
                    <>
                      {" "}
                      Para pedidos online, o envio de e-mail fiscal é disparado no fluxo de emissão (quando
                      `receipt_email`/`guest_email` está disponível).
                    </>
                  ) : null}
                </div>
                <div style={fiscalLegendStyle}>
                  <button
                    type="button"
                    onClick={() => setShowFiscalLegend((prev) => !prev)}
                    style={fiscalLegendToggleButtonStyle}
                    aria-expanded={showFiscalLegend}
                  >
                    {showFiscalLegend ? "Ocultar legenda" : "Mostrar legenda"}
                  </button>
                  {showFiscalLegend ? (
                    <div style={{ marginTop: 8 }}>
                      <strong style={{ display: "block", marginBottom: 8 }}>Legenda de estados fiscais</strong>
                      <div style={fiscalLegendRowStyle}>
                        <span style={{ ...fiscalStateBadgeStyleBase, ...getFiscalStateVisual("GERADO").style }}>
                          <span aria-hidden="true">{getFiscalStateVisual("GERADO").icon}</span>
                          <span>Gerado</span>
                        </span>
                        <span style={fiscalLegendTextStyle}>Documento fiscal disponível e associado ao pedido.</span>
                      </div>
                      <div style={fiscalLegendRowStyle}>
                        <span
                          style={{
                            ...fiscalStateBadgeStyleBase,
                            ...getFiscalStateVisual("GERADO_MANUALMENTE").style,
                          }}
                        >
                          <span aria-hidden="true">{getFiscalStateVisual("GERADO_MANUALMENTE").icon}</span>
                          <span>Gerado manualmente</span>
                        </span>
                        <span style={fiscalLegendTextStyle}>Emitido por ação operacional (fallback de suporte).</span>
                      </div>
                      <div style={fiscalLegendRowStyle}>
                        <span
                          style={{
                            ...fiscalStateBadgeStyleBase,
                            ...getFiscalStateVisual("SEM_DESTINATARIO_EMAIL").style,
                          }}
                        >
                          <span aria-hidden="true">{getFiscalStateVisual("SEM_DESTINATARIO_EMAIL").icon}</span>
                          <span>Sem destinatário de e-mail</span>
                        </span>
                        <span style={fiscalLegendTextStyle}>Pedido sem e-mail para envio automático da invoice.</span>
                      </div>
                      <div style={fiscalLegendRowStyle}>
                        <span style={{ ...fiscalStateBadgeStyleBase, ...getFiscalStateVisual("PENDENTE").style }}>
                          <span aria-hidden="true">{getFiscalStateVisual("PENDENTE").icon}</span>
                          <span>Pendente</span>
                        </span>
                        <span style={fiscalLegendTextStyle}>Aguardando geração/materialização no billing fiscal.</span>
                      </div>
                    </div>
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

function getFiscalStateVisual(code) {
  const normalized = String(code || "").trim().toUpperCase();
  if (normalized === "GERADO") {
    return {
      icon: "✔",
      style: {
        color: "#14532d",
        borderColor: "rgba(22,163,74,0.65)",
        background: "rgba(22,163,74,0.18)",
      },
      hintBackground: "rgba(22,163,74,0.13)",
      hintColor: "#14532d",
    };
  }
  if (normalized === "GERADO_MANUALMENTE") {
    return {
      icon: "⚠",
      style: {
        color: "#854d0e",
        borderColor: "rgba(217,119,6,0.65)",
        background: "rgba(217,119,6,0.18)",
      },
      hintBackground: "rgba(217,119,6,0.13)",
      hintColor: "#854d0e",
    };
  }
  if (normalized === "SEM_DESTINATARIO_EMAIL") {
    return {
      icon: "ℹ",
      style: {
        color: "#0c4a6e",
        borderColor: "rgba(14,116,144,0.65)",
        background: "rgba(14,116,144,0.16)",
      },
      hintBackground: "rgba(14,116,144,0.13)",
      hintColor: "#0c4a6e",
    };
  }
  return {
    icon: "…",
    style: {
      color: "#374151",
      borderColor: "rgba(107,114,128,0.65)",
      background: "rgba(107,114,128,0.16)",
    },
    hintBackground: "rgba(107,114,128,0.12)",
    hintColor: "#374151",
  };
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

const invoiceManualBadgeStyle = {
  marginTop: 10,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(245,158,11,0.65)",
  background: "rgba(245,158,11,0.18)",
  color: "#92400e",
  fontSize: 13,
  fontWeight: 700,
};

const fiscalStateHintStyle = {
  marginTop: 10,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(100,116,139,0.45)",
  background: "rgba(100,116,139,0.12)",
  color: "#334155",
  fontSize: 13,
  lineHeight: 1.4,
};

const fiscalStateBadgeStyleBase = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "4px 10px",
  borderRadius: 999,
  border: "1px solid transparent",
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: 0.2,
};

const fiscalLegendStyle = {
  marginTop: 12,
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.45)",
  background: "rgba(148,163,184,0.1)",
  color: "#334155",
  fontSize: 12,
};

const fiscalLegendRowStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
  marginBottom: 6,
};

const fiscalLegendTextStyle = {
  color: "#475569",
  fontSize: 12,
};

const fiscalLegendToggleButtonStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid rgba(100,116,139,0.45)",
  background: "rgba(255,255,255,0.7)",
  color: "#334155",
  fontSize: 12,
  fontWeight: 700,
  cursor: "pointer",
};

const invoiceSourceBadgeStyle = {
  marginTop: 8,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(14,116,144,0.65)",
  background: "rgba(14,116,144,0.16)",
  color: "#0c4a6e",
  fontSize: 13,
  fontWeight: 700,
};