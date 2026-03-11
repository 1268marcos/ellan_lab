import React, { useEffect, useMemo, useState } from "react";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const BACKEND_SP =
  import.meta.env.VITE_BACKEND_SP_BASE_URL || "http://localhost:8201";

const BACKEND_PT =
  import.meta.env.VITE_BACKEND_PT_BASE_URL || "http://localhost:8202";

const initialIdentify = {
  phone: "",
  email: "",
};

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

function buildTotemId(region) {
  return region === "SP" ? "CACIFO-SP-001" : "CACIFO-PT-001";
}

export default function RegionPage({ region, mode = "kiosk" }) {
  const [paymentMethod, setPaymentMethod] = useState(region === "PT" ? "MBWAY" : "PIX");
  const [totemId, setTotemId] = useState(buildTotemId(region));

  const [catalogSlots, setCatalogSlots] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState("");

  const [selectedSlot, setSelectedSlot] = useState(null);
  const [selectedCatalogItem, setSelectedCatalogItem] = useState(null);

  const [createResp, setCreateResp] = useState(null);
  const [paymentResp, setPaymentResp] = useState(null);
  const [identifyResp, setIdentifyResp] = useState(null);

  const [identifyForm, setIdentifyForm] = useState(initialIdentify);

  const [loadingCreate, setLoadingCreate] = useState(false);
  const [loadingPayment, setLoadingPayment] = useState(false);
  const [loadingIdentify, setLoadingIdentify] = useState(false);

  const [err, setErr] = useState(null);

  const backendBase = region === "SP" ? BACKEND_SP : BACKEND_PT;

  const createUrl = useMemo(() => `${ORDER_PICKUP_BASE}/kiosk/orders`, []);
  const identifyUrl = useMemo(() => `${ORDER_PICKUP_BASE}/kiosk/identify`, []);
  const catalogSlotsUrl = useMemo(() => `${backendBase}/catalog/slots`, [backendBase]);
  const lockerSlotsUrl = useMemo(() => `${backendBase}/locker/slots`, [backendBase]);

  const currentOrderId = createResp?.order_id || null;

  useEffect(() => {
    setTotemId(buildTotemId(region));
    setSelectedSlot(null);
    setSelectedCatalogItem(null);
    setCreateResp(null);
    setPaymentResp(null);
    setIdentifyResp(null);
    setIdentifyForm(initialIdentify);
    setErr(null);
  }, [region]);

  useEffect(() => {
    fetchCatalogSlots();
  }, [catalogSlotsUrl]);

  async function fetchCatalogSlots() {
    setCatalogLoading(true);
    setCatalogError("");

    try {
      const [catalogRes, lockerRes] = await Promise.all([
        fetch(catalogSlotsUrl),
        fetch(lockerSlotsUrl),
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
      setCatalogLoading(false);
    }
  }

  function handleSelectCatalogItem(item) {
    setSelectedSlot(item.slot);
    setSelectedCatalogItem(item);
    setCreateResp(null);
    setPaymentResp(null);
    setIdentifyResp(null);
    setErr(null);
  }

  async function createKioskOrder() {
    if (!selectedCatalogItem?.sku_id || !selectedCatalogItem?.slot) {
      setErr("Selecione uma gaveta/produto antes de criar o pedido KIOSK.");
      return;
    }

    setErr(null);
    setCreateResp(null);
    setPaymentResp(null);
    setIdentifyResp(null);

    setLoadingCreate(true);
    try {
      const res = await fetch(createUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          region,
          totem_id: totemId,
          sku_id: selectedCatalogItem.sku_id,
          desired_slot: Number(selectedCatalogItem.slot),
          payment_method: paymentMethod,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }

      setCreateResp(data);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingCreate(false);
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

      setPaymentResp(data);
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
    <div style={pageStyle}>
      <div style={headerCardStyle}>
        <h1 style={{ margin: 0 }}>Simulador KIOSK — {region}</h1>
        <div style={subtleStyle}>
          Vitrine de 24 gavetas. O cliente escolhe a gaveta/produto e o pedido KIOSK nasce com
          <code> desired_slot </code>
          + <code> sku_id </code>.
        </div>
      </div>

      <section style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={h2Style}>1. Vitrine KIOSK — 24 gavetas</h2>
          <button onClick={fetchCatalogSlots} disabled={catalogLoading} style={buttonSecondaryStyle}>
            {catalogLoading ? "Atualizando..." : "Atualizar vitrine"}
          </button>
        </div>

        <div style={infoGridStyle}>
          <div><b>Região:</b> {region}</div>
          <div><b>Backend catálogo:</b> {backendBase}</div>
          <div><b>Endpoint:</b> {catalogSlotsUrl}</div>
        </div>

        {catalogError ? <pre style={errorBoxStyle}>{catalogError}</pre> : null}

        {catalogLoading ? (
          <div style={subtleStyle}>Carregando gavetas...</div>
        ) : (
          <div style={slotsGridStyle}>
            {catalogSlots.map((item) => {
              const isSelected = selectedSlot === item.slot;
              const isDisabled =
                !item.is_active ||
                !item.sku_id ||
                !item.is_operationally_available;

              return (
                <button
                  key={item.slot}
                  type="button"
                  onClick={() => !isDisabled && handleSelectCatalogItem(item)}
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
                    <span
                      style={miniStatusStyle(item.is_active && item.is_operationally_available)}
                    >
                      {item.is_active
                        ? item.is_operationally_available
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
              Totem ID
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
                <option value="PIX">PIX</option>
                <option value="CARTAO">CARTÃO</option>
                <option value="MBWAY">MBWAY</option>
                <option value="NFC">NFC</option>
              </select>
            </label>
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
                <div><b>ttl_sec:</b> {createResp.ttl_sec}</div>
                <div><b>status:</b> {createResp.status}</div>
              </div>
              <div style={messageStyle}>{createResp.message}</div>
            </div>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={h2Style}>3. Aprovar pagamento KIOSK</h2>

          <div style={subtleStyle}>
            Confirma a allocation, liga a luz, abre a gaveta e marca o pedido como
            <code> DISPENSED </code>.
          </div>

          <div style={{ marginTop: 12 }}>
            <div><b>Pedido atual:</b> {currentOrderId || "nenhum"}</div>
          </div>

          <button
            onClick={approveKioskPayment}
            disabled={loadingPayment || !currentOrderId}
            style={buttonPrimaryStyle}
          >
            {loadingPayment ? "Aprovando..." : "Aprovar pagamento"}
          </button>

          {paymentResp && (
            <div style={okBoxStyle}>
              <strong>Pagamento aprovado</strong>
              <div style={summaryListStyle}>
                <div><b>order_id:</b> {paymentResp.order_id}</div>
                <div><b>allocation_id:</b> {paymentResp.allocation_id}</div>
                <div><b>slot:</b> {paymentResp.slot}</div>
                <div><b>status:</b> {paymentResp.status}</div>
                <div><b>payment_method:</b> {paymentResp.payment_method || "-"}</div>
              </div>
              <div style={messageStyle}>{paymentResp.message}</div>
            </div>
          )}
        </section>

        <section style={cardStyle}>
          <h2 style={h2Style}>4. Identificação opcional</h2>

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
            {loadingIdentify ? "Registrando..." : "Registrar identificação"}
          </button>

          {identifyResp && (
            <div style={okBoxStyle}>
              <strong>Identificação registrada</strong>
              <div style={messageStyle}>{identifyResp.message}</div>
            </div>
          )}
        </section>
      </div>

      <section style={cardStyle}>
        <h2 style={h2Style}>Configuração desta tela</h2>
        <div style={summaryListStyle}>
          <div><b>mode:</b> {mode}</div>
          <div><b>ORDER_PICKUP_BASE:</b> {ORDER_PICKUP_BASE}</div>
          <div><b>backendBase:</b> {backendBase}</div>
          <div><b>catalogSlotsUrl:</b> {catalogSlotsUrl}</div>
          <div><b>createUrl:</b> {createUrl}</div>
          <div><b>identifyUrl:</b> {identifyUrl}</div>
        </div>
      </section>

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

const errorBoxStyle = {
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
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