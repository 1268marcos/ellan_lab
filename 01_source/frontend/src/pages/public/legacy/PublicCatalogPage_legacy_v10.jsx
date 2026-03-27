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
  const [expandedCards, setExpandedCards] = useState(new Set()); // Controle de cards expandidos

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
        // Resetar expandidos ao carregar novos itens
        setExpandedCards(new Set());
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

  const toggleExpand = (slotId) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(slotId)) {
        newSet.delete(slotId);
      } else {
        newSet.add(slotId);
      }
      return newSet;
    });
  };

  // Componente de skeleton loading otimizado para mobile
  const SkeletonCard = () => (
    <article style={{ ...compactCardStyle, animation: "pulse 1.5s ease-in-out infinite" }}>
      <div style={compactContentStyle}>
        <div style={compactLeftStyle}>
          <div style={{ width: 50, height: 50, background: "#e5e7eb", borderRadius: 12 }}></div>
          <div style={compactInfoStyle}>
            <div style={{ width: 40, height: 24, background: "#e5e7eb", borderRadius: 6 }}></div>
            <div style={{ width: 100, height: 20, background: "#e5e7eb", borderRadius: 4, marginTop: 4 }}></div>
          </div>
        </div>
        <div style={compactRightStyle}>
          <div style={{ width: 80, height: 28, background: "#e5e7eb", borderRadius: 6 }}></div>
          <div style={{ width: 100, height: 36, background: "#e5e7eb", borderRadius: 8, marginTop: 8 }}></div>
        </div>
      </div>
    </article>
  );

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        {/* Seção Hero - Otimizada para mobile */}
        <section style={heroCardStyle}>
          <span style={eyebrowStyle}>📦 Catálogo Público</span>
          <h1 style={titleStyle}>Escolha sua gaveta</h1>

          {/* Filtros em linha para mobile */}
          <div style={toolbarStyle}>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              style={compactSelectStyle}
            >
              <option value="SP">🇧🇷 SP</option>
              <option value="PT">🇵🇹 PT</option>
            </select>

            <select
              value={lockerId}
              onChange={(e) => setLockerId(e.target.value)}
              style={compactSelectStyle}
            >
              {(LOCKER_OPTIONS[region] || []).map((item) => (
                <option key={item.locker_id} value={item.locker_id}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          {selectedLockerDetails && (
            <div style={addressHintStyle}>
              📍 {selectedLockerDetails.address}
            </div>
          )}

          <div style={actionsStyle}>
            <Link to="/" style={compactSecondaryActionStyle}>
              ← Voltar
            </Link>
            <Link to="/meus-pedidos" style={compactSecondaryActionStyle}>
              📋 Meus Pedidos
            </Link>
          </div>
        </section>

        {/* Mensagem de erro */}
        {error && (
          <div style={errorContainerStyle}>
            <span style={errorIconStyle}>⚠️</span>
            <div style={errorContentStyle}>
              <strong>Ops!</strong>
              <p style={{ margin: 0, fontSize: 13 }}>{error}</p>
            </div>
            <button onClick={() => window.location.reload()} style={retryButtonStyle}>
              Tentar
            </button>
          </div>
        )}

        {/* Lista de gavetas - Otimizada para mobile com 24+ itens */}
        {loading ? (
          <div style={listStyle}>
            {[1, 2, 3, 4, 5, 6].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : (
          <>
            <div style={resultsHeaderStyle}>
              <h2 style={resultsTitleStyle}>
                Gavetas disponíveis
                {items.length > 0 && <span style={resultsCountStyle}> ({items.length})</span>}
              </h2>
            </div>

            <div style={listStyle}>
              {items.length === 0 ? (
                <div style={emptyStateStyle}>
                  <div style={emptyStateIconStyle}>🔍</div>
                  <h3 style={emptyStateTitleStyle}>Nenhuma gaveta disponível</h3>
                  <p style={emptyStateTextStyle}>Tente selecionar outro ponto de retirada.</p>
                </div>
              ) : (
                items.map((item) => {
                  const isExpanded = expandedCards.has(item.slot);
                  return (
                    <article key={`${item.locker_id}-${item.slot}`} style={compactCardStyle}>
                      {/* Conteúdo principal sempre visível */}
                      <div style={compactContentStyle}>
                        <div style={compactLeftStyle}>
                          <div style={slotNumberStyle}>
                            {item.slot}
                          </div>
                          <div style={compactInfoStyle}>
                            <div style={productNameStyle}>{item.name}</div>
                            <div style={productPriceStyle}>
                              {formatMoney(item.amount_cents, item.currency)}
                            </div>
                          </div>
                        </div>
                        
                        <div style={compactRightStyle}>
                          <button
                            onClick={() => handleReserve(item)}
                            disabled={submittingSlot === item.slot}
                            style={compactBuyButtonStyle}
                          >
                            {submittingSlot === item.slot ? "⏳" : "🛒"}
                          </button>
                          <button
                            onClick={() => toggleExpand(item.slot)}
                            style={expandButtonStyle}
                            aria-label={isExpanded ? "Recolher detalhes" : "Expandir detalhes"}
                          >
                            {isExpanded ? "▲" : "▼"}
                          </button>
                        </div>
                      </div>

                      {/* Conteúdo expandido - visível apenas quando expandido */}
                      {isExpanded && (
                        <div style={expandedContentStyle}>
                          <div style={expandedGridStyle}>
                            <div style={expandedItemStyle}>
                              <span style={expandedLabelStyle}>SKU:</span>
                              <span style={expandedValueStyle}>{item.sku_id}</span>
                            </div>
                            <div style={expandedItemStyle}>
                              <span style={expandedLabelStyle}>Moeda:</span>
                              <span style={expandedValueStyle}>{item.currency}</span>
                            </div>
                            <div style={expandedItemStyle}>
                              <span style={expandedLabelStyle}>Atualizado:</span>
                              <span style={expandedValueStyle}>
                                {item.updated_at
                                  ? new Date(item.updated_at).toLocaleDateString(
                                      region === "SP" ? "pt-BR" : "pt-PT",
                                      { day: '2-digit', month: 'short', year: 'numeric' }
                                    )
                                  : "-"}
                              </span>
                            </div>
                            {item.description && (
                              <div style={expandedItemStyle}>
                                <span style={expandedLabelStyle}>Descrição:</span>
                                <span style={expandedValueStyle}>{item.description}</span>
                              </div>
                            )}
                            {item.imageURL && (
                              <div style={expandedImageContainerStyle}>
                                <img 
                                  src={item.imageURL} 
                                  alt={item.name}
                                  style={expandedImageStyle}
                                  onError={(e) => e.target.style.display = 'none'}
                                />
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </article>
                  );
                })
              )}
            </div>

            {/* Indicador de quantidade para mobile */}
            {items.length > 0 && (
              <div style={scrollHintStyle}>
                {items.length} gavetas disponíveis • Role para ver mais
              </div>
            )}
          </>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @media (max-width: 768px) {
          .compact-card {
            margin: 8px 0;
          }
        }
      `}</style>
    </main>
  );
}

// Estilos otimizados para mobile
const pageStyle = {
  minHeight: "100vh",
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  padding: "12px",
  "@media (min-width: 768px)": {
    padding: 24,
  },
};

const containerStyle = {
  maxWidth: 1200,
  margin: "0 auto",
};

const heroCardStyle = {
  borderRadius: 20,
  padding: "20px",
  marginBottom: "20px",
  background: "rgba(168, 192, 235, 0.95)",
  boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
  "@media (min-width: 768px)": {
    padding: 32,
    marginBottom: 32,
  },
};

const eyebrowStyle = {
  display: "inline-block",
  marginBottom: 8,
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: "0.05em",
  textTransform: "uppercase",
  color: "#667eea",
  "@media (min-width: 768px)": {
    fontSize: 13,
    marginBottom: 12,
  },
};

const titleStyle = {
  margin: 0,
  fontSize: 24,
  fontWeight: 800,
  lineHeight: 1.2,
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
  "@media (min-width: 768px)": {
    fontSize: 38,
  },
};

const toolbarStyle = {
  display: "flex",
  gap: "10px",
  marginTop: "20px",
  flexDirection: "column",
  "@media (min-width: 640px)": {
    flexDirection: "row",
  },
};

const compactSelectStyle = {
  flex: 1,
  padding: "10px 12px",
  borderRadius: 12,
  border: "1px solid #e5e7eb",
  background: "rgba(44,78,122,1)",
  fontSize: 14,
  fontWeight: 500,
  cursor: "pointer",
  outline: "none",
  "@media (min-width: 768px)": {
    padding: "12px 16px",
    fontSize: 15,
  },
};

const addressHintStyle = {
  fontSize: 12,
  color: "#fff",
  padding: "8px 10px",
  background: "rgba(44, 78, 122, .45)",
  borderRadius: 10,
  marginTop: 12,
  "@media (min-width: 768px)": {
    fontSize: 13,
    padding: "4px 8px",
  },
};

const actionsStyle = {
  display: "flex",
  gap: 10,
  marginTop: 16,
  paddingTop: 12,
  borderTop: "1px solid #e5e7eb",
};

const compactSecondaryActionStyle = {
  textDecoration: "none",
  padding: "8px 16px",
  borderRadius: 10,
  border: "1px solid #d1d5db",
  background: "#fff",
  color: "#374151",
  fontWeight: 600,
  fontSize: 13,
  cursor: "pointer",
  "@media (min-width: 768px)": {
    padding: "10px 20px",
    fontSize: 14,
  },
};

const errorContainerStyle = {
  marginBottom: 16,
  padding: 12,
  borderRadius: 12,
  background: "#fef2f2",
  border: "1px solid #fecaca",
  display: "flex",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const errorIconStyle = {
  fontSize: 20,
};

const errorContentStyle = {
  flex: 1,
  color: "#991b1b",
  fontSize: 13,
};

const retryButtonStyle = {
  padding: "6px 12px",
  borderRadius: 8,
  background: "#dc2626",
  color: "#fff",
  border: "none",
  cursor: "pointer",
  fontWeight: 600,
  fontSize: 12,
};

const resultsHeaderStyle = {
  marginBottom: 16,
  padding: "0 4px",
};

const resultsTitleStyle = {
  fontSize: 18,
  fontWeight: 700,
  color: "#fff",
  margin: 0,
  "@media (min-width: 768px)": {
    fontSize: 24,
  },
};

const resultsCountStyle = {
  fontSize: 14,
  fontWeight: 500,
  color: "#e0e7ff",
};

// Estilo de lista para rolagem suave com muitos itens
const listStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "10px",
  marginBottom: "20px",
};

// Card compacto otimizado para mobile
const compactCardStyle = {
  background: "#fff",
  borderRadius: 16,
  padding: "12px",
  boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
  transition: "all 0.2s",
  animation: "slideDown 0.3s ease-out",
};

const compactContentStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
};

const compactLeftStyle = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  flex: 1,
};

const slotNumberStyle = {
  width: 44,
  height: 44,
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  borderRadius: 12,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: 18,
  fontWeight: 800,
  color: "#fff",
  flexShrink: 0,
};

const compactInfoStyle = {
  flex: 1,
};

const productNameStyle = {
  fontSize: 14,
  fontWeight: 700,
  color: "#111827",
  marginBottom: 4,
  lineHeight: 1.3,
};

const productPriceStyle = {
  fontSize: 16,
  fontWeight: 800,
  color: "#667eea",
};

const compactRightStyle = {
  display: "flex",
  gap: 8,
  alignItems: "center",
};

const compactBuyButtonStyle = {
  width: 44,
  height: 44,
  borderRadius: 12,
  border: "none",
  background: "#667eea",
  color: "#fff",
  fontSize: 20,
  cursor: "pointer",
  transition: "all 0.2s",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: 700,
};

const expandButtonStyle = {
  width: 36,
  height: 36,
  borderRadius: 10,
  border: "1px solid #e5e7eb",
  background: "#f9fafb",
  color: "#6b7280",
  fontSize: 14,
  cursor: "pointer",
  transition: "all 0.2s",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

// Conteúdo expandido
const expandedContentStyle = {
  marginTop: 12,
  paddingTop: 12,
  borderTop: "1px solid #f3f4f6",
  animation: "slideDown 0.3s ease-out",
};

const expandedGridStyle = {
  display: "grid",
  gap: 8,
  fontSize: 13,
};

const expandedItemStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "6px 0",
};

const expandedLabelStyle = {
  fontWeight: 600,
  color: "#6b7280",
  fontSize: 12,
};

const expandedValueStyle = {
  color: "#374151",
  fontSize: 12,
  textAlign: "right",
  wordBreak: "break-word",
  maxWidth: "60%",
};

const expandedImageContainerStyle = {
  marginTop: 8,
  width: "100%",
  maxHeight: 120,
  borderRadius: 8,
  overflow: "hidden",
};

const expandedImageStyle = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
};

const emptyStateStyle = {
  textAlign: "center",
  padding: 32,
  background: "#fff",
  borderRadius: 16,
};

const emptyStateIconStyle = {
  fontSize: 40,
  marginBottom: 12,
};

const emptyStateTitleStyle = {
  fontSize: 16,
  fontWeight: 600,
  color: "#374151",
  marginBottom: 8,
};

const emptyStateTextStyle = {
  fontSize: 13,
  color: "#6b7280",
  marginBottom: 0,
};

const scrollHintStyle = {
  textAlign: "center",
  padding: "12px",
  color: "#e0e7ff",
  fontSize: 12,
  marginTop: 8,
};