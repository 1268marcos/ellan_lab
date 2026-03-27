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
    { locker_id: "SP-OSASCO-CENTRO-LK-001", label: "Osasco Centro", address: "Av. dos Autonomistas, 1234" },
    { locker_id: "SP-CARAPICUIBA-JDMARILU-LK-001", label: "Carapicuíba Jardim Marilu", address: "Rua Bahia, 567" },
  ],
  PT: [
    { locker_id: "PT-MAIA-CENTRO-LK-001", label: "Maia Centro", address: "Rua do Comércio, 89" },
    { locker_id: "PT-GUIMARAES-AZUREM-LK-001", label: "Guimarães Azurém", address: "Avenida da Liberdade, 234" },
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
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
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
    searchParams.get("locker_id") || LOCKER_OPTIONS[initialRegion]?.[0]?.locker_id || ""
  );

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submittingSlot, setSubmittingSlot] = useState(null);
  const [error, setError] = useState("");
  const [selectedLockerDetails, setSelectedLockerDetails] = useState(null);

  const backendBase = useMemo(() => resolveBackendBase(region), [region]);

  // Atualiza detalhes do locker selecionado
  useEffect(() => {
    const locker = LOCKER_OPTIONS[region]?.find(l => l.locker_id === lockerId);
    setSelectedLockerDetails(locker || null);
  }, [region, lockerId]);

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
            description: item.description || "",
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
        )}&product_name=${encodeURIComponent(item.name)}&price=${encodeURIComponent(item.amount_cents)}`
      );
    } finally {
      setSubmittingSlot(null);
    }
  }

  // Componente de skeleton loading
  const SkeletonCard = () => (
    <article style={{ ...slotCardStyle, animation: "pulse 1.5s ease-in-out infinite" }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <div style={{ width: 80, height: 28, background: "#e5e7eb", borderRadius: 20 }}></div>
        <div style={{ width: 100, height: 28, background: "#e5e7eb", borderRadius: 20 }}></div>
      </div>
      <div style={{ width: "70%", height: 28, background: "#e5e7eb", borderRadius: 8, marginTop: 8 }}></div>
      <div style={{ width: "40%", height: 32, background: "#e5e7eb", borderRadius: 8 }}></div>
      <div style={{ display: "grid", gap: 8 }}>
        {[1, 2, 3].map(i => (
          <div key={i} style={{ width: "100%", height: 20, background: "#e5e7eb", borderRadius: 4 }}></div>
        ))}
      </div>
      <div style={{ width: "100%", height: 44, background: "#e5e7eb", borderRadius: 12 }}></div>
    </article>
  );

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        {/* Seção Hero */}
        <section style={heroCardStyle}>
          <span style={eyebrowStyle}>📦 Catálogo Público</span>

          <h1 style={titleStyle}>Encontre seu produto</h1>

          <p style={subtitleStyle}>
            Escolha uma gaveta disponível no locker mais próximo de você. 
            Cada gaveta contém um produto único com preço já definido.
          </p>

          {/* Filtros com feedback visual */}
          <div style={toolbarStyle}>
            <div style={filterGroupStyle}>
              <label style={labelStyle}>
                🌎 Região
                <select
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  style={selectStyle}
                >
                  <option value="SP">🇧🇷 São Paulo (Brasil)</option>
                  <option value="PT">🇵🇹 Portugal</option>
                </select>
              </label>
            </div>

            <div style={filterGroupStyle}>
              <label style={labelStyle}>
                📍 Ponto de retirada
                <select
                  value={lockerId}
                  onChange={(e) => setLockerId(e.target.value)}
                  style={selectStyle}
                >
                  {(LOCKER_OPTIONS[region] || []).map((item) => (
                    <option key={item.locker_id} value={item.locker_id}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              {selectedLockerDetails && (
                <div style={addressHintStyle}>
                  📮 {selectedLockerDetails.address}
                </div>
              )}
            </div>
          </div>

          {/* Ações rápidas */}
          <div style={actionsStyle}>
            <Link to="/" style={secondaryActionStyle}>
              ← Voltar ao início
            </Link>
            <Link to="/meus-pedidos" style={secondaryActionStyle}>
              📋 Meus pedidos
            </Link>
          </div>
        </section>

        {/* Mensagem de erro com tratamento visual amigável */}
        {error && (
          <div style={errorContainerStyle}>
            <span style={errorIconStyle}>⚠️</span>
            <div style={errorContentStyle}>
              <strong>Ops! Algo deu errado</strong>
              <p style={{ margin: 0, fontSize: 14 }}>{error}</p>
            </div>
            <button 
              onClick={() => window.location.reload()} 
              style={retryButtonStyle}
            >
              Tentar novamente
            </button>
          </div>
        )}

        {/* Seção de produtos */}
        {loading ? (
          <div style={gridStyle}>
            {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : (
          <>
            {/* Indicador de resultados */}
            <div style={resultsHeaderStyle}>
              <h2 style={resultsTitleStyle}>
                Gavetas disponíveis
                {items.length > 0 && <span style={resultsCountStyle}> ({items.length})</span>}
              </h2>
              {items.length > 0 && (
                <p style={resultsSubtitleStyle}>
                  Selecione uma gaveta para prosseguir com a compra
                </p>
              )}
            </div>

            <div style={gridStyle}>
              {items.length === 0 ? (
                <article style={emptyStateStyle}>
                  <div style={emptyStateIconStyle}>🔍</div>
                  <h3 style={emptyStateTitleStyle}>Nenhuma gaveta disponível</h3>
                  <p style={emptyStateTextStyle}>
                    Não encontramos produtos ativos para este locker. 
                    Tente selecionar outro ponto de retirada.
                  </p>
                  <button 
                    onClick={() => setLockerId(LOCKER_OPTIONS[region]?.[0]?.locker_id || "")}
                    style={secondaryButtonStyle}
                  >
                    Ver outro locker
                  </button>
                </article>
              ) : (
                items.map((item) => (
                  <article key={`${item.locker_id}-${item.slot}`} style={slotCardStyle}>
                    {/* Imagem do produto (se disponível) */}
                    {item.imageURL && (
                      <div style={imageContainerStyle}>
                        <img 
                          src={item.imageURL} 
                          alt={item.name}
                          style={productImageStyle}
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      </div>
                    )}
                    
                    <div style={slotTopStyle}>
                      <span style={slotBadgeStyle}>
                        📦 Gaveta {item.slot}
                      </span>
                      <span style={lockerBadgeStyle}>
                        {selectedLockerDetails?.label || item.locker_id}
                      </span>
                    </div>

                    <h2 style={cardTitleStyle}>{item.name}</h2>
                    
                    {item.description && (
                      <p style={descriptionStyle}>{item.description}</p>
                    )}

                    <div style={priceContainerStyle}>
                      <span style={priceStyle}>
                        {formatMoney(item.amount_cents, item.currency)}
                      </span>
                      {item.amount_cents > 0 && (
                        <span style={installmentStyle}>
                          ou em até 3x sem juros
                        </span>
                      )}
                    </div>

                    <div style={metaListStyle}>
                      <div>
                        <span style={metaLabelStyle}>SKU:</span> {item.sku_id}
                      </div>
                      <div>
                        <span style={metaLabelStyle}>Moeda:</span> {item.currency}
                      </div>
                      <div>
                        <span style={metaLabelStyle}>Atualizado:</span>{" "}
                        {item.updated_at
                          ? new Date(item.updated_at).toLocaleDateString(
                              region === "SP" ? "pt-BR" : "pt-PT",
                              { day: '2-digit', month: 'short', year: 'numeric' }
                            )
                          : "-"}
                      </div>
                    </div>

                    <button
                      onClick={() => handleReserve(item)}
                      disabled={submittingSlot === item.slot}
                      style={{
                        ...primaryButtonStyle,
                        ...(submittingSlot === item.slot && buttonDisabledStyle)
                      }}
                    >
                      {submittingSlot === item.slot ? (
                        <>
                          <span style={spinnerStyle}></span>
                          Redirecionando...
                        </>
                      ) : (
                        "🛒 Comprar esta gaveta"
                      )}
                    </button>
                  </article>
                ))
              )}
            </div>
          </>
        )}
      </div>

      {/* Adicionar keyframes para animação */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </main>
  );
}

// Estilos otimizados e consistentes
const pageStyle = {
  minHeight: "100vh",
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  padding: 24,
};

const containerStyle = {
  maxWidth: 1200,
  margin: "0 auto",
};

const heroCardStyle = {
  borderRadius: 24,
  padding: 32,
  marginBottom: 32,
  background: "rgba(255,255,255,0.95)",
  boxShadow: "0 10px 25px -5px rgba(0,0,0,0.1)",
  backdropFilter: "blur(10px)",
};

const eyebrowStyle = {
  display: "inline-block",
  marginBottom: 12,
  fontSize: 13,
  fontWeight: 600,
  letterSpacing: "0.05em",
  textTransform: "uppercase",
  color: "#667eea",
};

const titleStyle = {
  margin: 0,
  fontSize: 38,
  fontWeight: 800,
  lineHeight: 1.2,
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

const subtitleStyle = {
  marginTop: 16,
  marginBottom: 0,
  fontSize: 16,
  lineHeight: 1.6,
  color: "#4b5563",
  maxWidth: 760,
};

const toolbarStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
  gap: 20,
  marginTop: 28,
};

const filterGroupStyle = {
  display: "grid",
  gap: 8,
};

const labelStyle = {
  display: "grid",
  gap: 8,
  fontWeight: 600,
  color: "#374151",
  fontSize: 14,
};

const selectStyle = {
  padding: "12px 16px",
  borderRadius: 12,
  border: "2px solid #e5e7eb",
  background: "#fff",
  color: "#111827",
  fontSize: 15,
  cursor: "pointer",
  transition: "all 0.2s",
  outline: "none",
};

const addressHintStyle = {
  fontSize: 13,
  color: "#6b7280",
  padding: "4px 8px",
  background: "#f3f4f6",
  borderRadius: 8,
  marginTop: 4,
};

const actionsStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: 12,
  marginTop: 24,
  paddingTop: 16,
  borderTop: "1px solid #e5e7eb",
};

const secondaryActionStyle = {
  textDecoration: "none",
  padding: "10px 20px",
  borderRadius: 12,
  border: "1px solid #d1d5db",
  background: "#fff",
  color: "#374151",
  fontWeight: 600,
  fontSize: 14,
  transition: "all 0.2s",
  cursor: "pointer",
};

const errorContainerStyle = {
  marginBottom: 24,
  padding: 16,
  borderRadius: 16,
  background: "#fef2f2",
  border: "1px solid #fecaca",
  display: "flex",
  alignItems: "center",
  gap: 12,
  flexWrap: "wrap",
};

const errorIconStyle = {
  fontSize: 24,
};

const errorContentStyle = {
  flex: 1,
  color: "#991b1b",
};

const retryButtonStyle = {
  padding: "8px 16px",
  borderRadius: 8,
  background: "#dc2626",
  color: "#fff",
  border: "none",
  cursor: "pointer",
  fontWeight: 600,
  fontSize: 14,
};

const resultsHeaderStyle = {
  marginBottom: 24,
};

const resultsTitleStyle = {
  fontSize: 24,
  fontWeight: 700,
  color: "#fff",
  margin: 0,
};

const resultsCountStyle = {
  fontSize: 18,
  fontWeight: 500,
  color: "#e0e7ff",
};

const resultsSubtitleStyle = {
  fontSize: 14,
  color: "#e0e7ff",
  marginTop: 4,
  marginBottom: 0,
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
  gap: 24,
};

const slotCardStyle = {
  borderRadius: 20,
  padding: 20,
  background: "#fff",
  boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
  transition: "transform 0.2s, box-shadow 0.2s",
  cursor: "pointer",
  display: "grid",
  gap: 12,
};

const imageContainerStyle = {
  width: "100%",
  height: 180,
  background: "#f9fafb",
  borderRadius: 12,
  overflow: "hidden",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const productImageStyle = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
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
  padding: "6px 12px",
  borderRadius: 20,
  background: "#667eea",
  color: "#fff",
  fontSize: 12,
  fontWeight: 700,
};

const lockerBadgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  padding: "6px 12px",
  borderRadius: 20,
  background: "#f3f4f6",
  color: "#374151",
  fontSize: 12,
  fontWeight: 600,
};

const cardTitleStyle = {
  margin: 0,
  fontSize: 20,
  fontWeight: 700,
  color: "#111827",
};

const descriptionStyle = {
  margin: 0,
  fontSize: 14,
  color: "#6b7280",
  lineHeight: 1.5,
};

const priceContainerStyle = {
  display: "flex",
  alignItems: "baseline",
  gap: 8,
  flexWrap: "wrap",
};

const priceStyle = {
  margin: 0,
  fontSize: 28,
  fontWeight: 800,
  color: "#667eea",
};

const installmentStyle = {
  fontSize: 13,
  color: "#10b981",
  fontWeight: 500,
};

const metaListStyle = {
  display: "grid",
  gap: 6,
  padding: "12px 0",
  borderTop: "1px solid #f3f4f6",
  borderBottom: "1px solid #f3f4f6",
  fontSize: 13,
};

const metaLabelStyle = {
  fontWeight: 600,
  color: "#6b7280",
};

const primaryButtonStyle = {
  padding: "12px 20px",
  borderRadius: 12,
  border: "none",
  background: "#667eea",
  color: "#fff",
  fontWeight: 700,
  fontSize: 15,
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

const spinnerStyle = {
  display: "inline-block",
  width: 16,
  height: 16,
  border: "2px solid rgba(255,255,255,0.3)",
  borderTopColor: "#fff",
  borderRadius: "50%",
  animation: "spin 0.6s linear infinite",
};

const emptyStateStyle = {
  gridColumn: "1 / -1",
  textAlign: "center",
  padding: 48,
  background: "#fff",
  borderRadius: 24,
};

const emptyStateIconStyle = {
  fontSize: 48,
  marginBottom: 16,
};

const emptyStateTitleStyle = {
  fontSize: 20,
  fontWeight: 600,
  color: "#374151",
  marginBottom: 8,
};

const emptyStateTextStyle = {
  fontSize: 14,
  color: "#6b7280",
  marginBottom: 24,
};

const secondaryButtonStyle = {
  padding: "10px 20px",
  borderRadius: 12,
  border: "1px solid #e5e7eb",
  background: "#f9fafb",
  color: "#374151",
  fontWeight: 600,
  cursor: "pointer",
  fontSize: 14,
};