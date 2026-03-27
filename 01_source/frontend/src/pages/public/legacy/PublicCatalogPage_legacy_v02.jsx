// 01_source/frontend/src/pages/public/PublicCatalogPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

const BACKEND_SP =
  import.meta.env.VITE_BACKEND_SP_BASE_URL || "http://localhost:8201";

const BACKEND_PT =
  import.meta.env.VITE_BACKEND_PT_BASE_URL || "http://localhost:8202";

const LOCKER_OPTIONS = {
  SP: [
    {
      locker_id: "SP-OSASCO-CENTRO-LK-001",
      label: "Osasco Centro",
    },
    {
      locker_id: "SP-CARAPICUIBA-JDMARILU-LK-001",
      label: "Carapicuíba Jardim Marilu",
    },
  ],
  PT: [
    {
      locker_id: "PT-MAIA-CENTRO-LK-001",
      label: "Maia Centro",
    },
    {
      locker_id: "PT-GUIMARAES-AZUREM-LK-001",
      label: "Guimarães Azurém",
    },
  ],
};

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

export default function PublicCatalogPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const regionParam = String(searchParams.get("region") || "SP").toUpperCase();
  const initialRegion = regionParam === "PT" ? "PT" : "SP";

  const [region, setRegion] = useState(initialRegion);
  const [lockerId, setLockerId] = useState(
    searchParams.get("locker_id") ||
      LOCKER_OPTIONS[initialRegion]?.[0]?.locker_id ||
      ""
  );

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submittingSlot, setSubmittingSlot] = useState(null);
  const [error, setError] = useState("");

  const backendBase = useMemo(() => resolveBackendBase(region), [region]);

  useEffect(() => {
    const defaultLocker = LOCKER_OPTIONS[region]?.[0]?.locker_id || "";
    setLockerId((prev) => {
      if (!prev) return defaultLocker;
      const exists = LOCKER_OPTIONS[region]?.some((x) => x.locker_id === prev);
      return exists ? prev : defaultLocker;
    });
  }, [region]);

  useEffect(() => {
    const params = new URLSearchParams(searchParams);
    params.set("region", region);
    if (lockerId) {
      params.set("locker_id", lockerId);
    } else {
      params.delete("locker_id");
    }
    setSearchParams(params, { replace: true });
  }, [region, lockerId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    async function loadCatalog() {
      if (!lockerId) {
        setItems([]);
        return;
      }

      setLoading(true);
      setError("");

      try {
        const res = await fetch(`${backendBase}/catalog/slots`, {
          headers: {
            "X-Locker-Id": lockerId,
          },
        });

        const data = await res.json().catch(() => []);

        if (!res.ok) {
          throw new Error(
            typeof data?.detail !== "undefined"
              ? JSON.stringify(data.detail)
              : JSON.stringify(data)
          );
        }

        const normalized = (Array.isArray(data) ? data : [])
          .filter((item) => item && item.sku_id && item.is_active)
          .map((item) => ({
            locker_id: item.locker_id || lockerId,
            slot: Number(item.slot),
            sku_id: item.sku_id,
            name: item.name || "Produto sem nome",
            amount_cents: Number(item.amount_cents || 0),
            currency: item.currency || (region === "SP" ? "BRL" : "EUR"),
            imageURL: item.imageURL || "",
            is_active: Boolean(item.is_active),
            updated_at: item.updated_at || null,
          }))
          .sort((a, b) => a.slot - b.slot);

        setItems(normalized);
      } catch (e) {
        setError(String(e?.message || e));
        setItems([]);
      } finally {
        setLoading(false);
      }
    }

    loadCatalog();
  }, [backendBase, lockerId, region]);

  async function handleReserve(item) {
    if (!item?.sku_id || !item?.slot || !lockerId) {
      return;
    }

    setSubmittingSlot(item.slot);
    setError("");

    try {
      navigate(
        `/checkout?region=${encodeURIComponent(region)}&locker_id=${encodeURIComponent(
          lockerId
        )}&sku_id=${encodeURIComponent(item.sku_id)}&slot=${encodeURIComponent(
          item.slot
        )}`
      );
    } finally {
      setSubmittingSlot(null);
    }
  }

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <section style={heroCardStyle}>
          <span style={eyebrowStyle}>Catálogo público</span>

          <h1 style={titleStyle}>Escolha sua gaveta</h1>

          <p style={subtitleStyle}>
            No fluxo online, o cliente escolhe uma gaveta real disponível no
            locker/cacifo. O produto, o preço e a localização já vêm do catálogo
            operacional do equipamento.
          </p>

          <div style={toolbarStyle}>
            <label style={labelStyle}>
              Região
              <select
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                style={selectStyle}
              >
                <option value="SP">SP</option>
                <option value="PT">PT</option>
              </select>
            </label>

            <label style={labelStyle}>
              Locker / Cacifo
              <select
                value={lockerId}
                onChange={(e) => setLockerId(e.target.value)}
                style={selectStyle}
              >
                {(LOCKER_OPTIONS[region] || []).map((item) => (
                  <option key={item.locker_id} value={item.locker_id}>
                    {item.label} — {item.locker_id}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div style={actionsStyle}>
            <Link to="/" style={secondaryActionStyle}>
              Voltar ao início
            </Link>

            <Link to="/meus-pedidos" style={secondaryActionStyle}>
              Meus pedidos
            </Link>
          </div>
        </section>

        {error ? <pre style={errorBoxStyle}>{error}</pre> : null}

        {loading ? (
          <section style={infoCardStyle}>
            <p style={cardTextStyle}>Carregando catálogo real do locker...</p>
          </section>
        ) : (
          <section style={gridStyle}>
            {items.length === 0 ? (
              <article style={infoCardStyle}>
                <h2 style={cardTitleStyle}>Nenhuma gaveta vendável</h2>
                <p style={cardTextStyle}>
                  Não encontramos gavetas ativas para este locker/cacifo.
                </p>
              </article>
            ) : (
              items.map((item) => (
                <article key={`${item.locker_id}-${item.slot}`} style={slotCardStyle}>
                  <div style={slotTopStyle}>
                    <span style={slotBadgeStyle}>Gaveta {item.slot}</span>
                    <span style={lockerBadgeStyle}>{item.locker_id}</span>
                  </div>

                  <h2 style={cardTitleStyle}>{item.name}</h2>

                  <p style={priceStyle}>
                    {formatMoney(item.amount_cents, item.currency)}
                  </p>

                  <div style={metaListStyle}>
                    <div>
                      <b>SKU:</b> {item.sku_id}
                    </div>
                    <div>
                      <b>Moeda:</b> {item.currency}
                    </div>
                    <div>
                      <b>Atualizado em:</b>{" "}
                      {item.updated_at
                        ? new Date(item.updated_at).toLocaleString(
                            region === "SP" ? "pt-BR" : "pt-PT"
                          )
                        : "-"}
                    </div>
                  </div>

                  <button
                    onClick={() => handleReserve(item)}
                    disabled={submittingSlot === item.slot}
                    style={primaryButtonStyle}
                  >
                    {submittingSlot === item.slot
                      ? "Abrindo checkout..."
                      : "Escolher esta gaveta"}
                  </button>
                </article>
              ))
            )}
          </section>
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
  color: "#555",
  maxWidth: 760,
};

const toolbarStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
  gap: 12,
  marginTop: 22,
};

const labelStyle = {
  display: "grid",
  gap: 8,
  fontWeight: 700,
  color: "#374151",
};

const selectStyle = {
  padding: "12px 14px",
  borderRadius: 12,
  border: "1px solid #d1d5db",
  background: "#fff",
  color: "#111827",
};

const actionsStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: 12,
  marginTop: 22,
};

const primaryActionStyle = {
  textDecoration: "none",
  padding: "12px 16px",
  borderRadius: 12,
  border: "1px solid #111827",
  background: "#111827",
  color: "white",
  fontWeight: 700,
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

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
  gap: 14,
};

const infoCardStyle = {
  borderRadius: 16,
  padding: 18,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.06)",
};

const slotCardStyle = {
  borderRadius: 16,
  padding: 18,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.06)",
  display: "grid",
  gap: 12,
};

const slotTopStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  flexWrap: "wrap",
};

const slotBadgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  padding: "6px 10px",
  borderRadius: 999,
  background: "#111827",
  color: "#fff",
  fontSize: 12,
  fontWeight: 800,
};

const lockerBadgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  padding: "6px 10px",
  borderRadius: 999,
  background: "#eef2ff",
  color: "#3730a3",
  fontSize: 12,
  fontWeight: 700,
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

const metaListStyle = {
  display: "grid",
  gap: 6,
  color: "rgba(129, 135, 143, 0.9)",
  fontSize: 14,
};

const priceStyle = {
  margin: 0,
  fontSize: 24,
  fontWeight: 800,
  color: "#111827",
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
  margin: "0 0 20px 0",
  padding: 14,
  borderRadius: 12,
  background: "#2b1d1d",
  color: "#ffb4b4",
  border: "1px solid rgba(255,255,255,0.12)",
  overflow: "auto",
};
