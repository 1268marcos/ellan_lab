// 01_source/frontend/src/pages/public/PublicCatalogPage.jsx
// UX Mobile-First
// Otimizado para SEO
import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const BACKEND_SP = import.meta.env.VITE_BACKEND_SP_BASE_URL || "http://localhost:8201";
const BACKEND_PT = import.meta.env.VITE_BACKEND_PT_BASE_URL || "http://localhost:8202";

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
  const [expandedCards, setExpandedCards] = useState(new Set());
  
  const backendBase = useMemo(() => resolveBackendBase(region), [region]);

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
  }, [region, lockerId, searchParams]);

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
          headers: { "X-Locker-Id": lockerId },
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
    if (!item?.sku_id || !item?.slot || !lockerId) return;
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

  const SkeletonCard = () => (
    <article 
      className="card skeleton-card"
      aria-label="Carregando produto"
      style={{ animation: 'pulse 1.5s ease-in-out infinite' }}
    >
      <div style={{ display: 'flex', gap: 'var(--spacing-4)', alignItems: 'center' }}>
        <div style={{ 
          width: 60, 
          height: 60, 
          background: '#e5e7eb', 
          borderRadius: 'var(--radius-lg)' 
        }}></div>
        <div style={{ flex: 1 }}>
          <div style={{ 
            width: '60%', 
            height: 20, 
            background: '#e5e7eb', 
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--spacing-2)'
          }}></div>
          <div style={{ 
            width: '40%', 
            height: 16, 
            background: '#e5e7eb', 
            borderRadius: 'var(--radius-md)' 
          }}></div>
        </div>
      </div>
    </article>
  );

  return (
    <main className="catalog-page" style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: 'var(--spacing-4)'
    }}>
      <div className="container" style={{ maxWidth: '1200px', margin: '0 auto' }}>
        
        {/* HERO - Mobile First */}
        <section 
          className="card card--hero"
          aria-labelledby="catalog-title"
          style={{
            borderRadius: 'var(--radius-2xl)',
            padding: 'var(--spacing-6)',
            marginBottom: 'var(--spacing-6)',
            background: 'rgba(255,255,255,0.95)',
            boxShadow: 'var(--shadow-xl)'
          }}
        >
          <span className="eyebrow" style={{
            display: 'inline-block',
            marginBottom: 'var(--spacing-2)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 600,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            color: 'var(--color-primary)'
          }}>
            📦 Catálogo Público
          </span>
          
          <h1 
            id="catalog-title"
            style={{
              margin: 0,
              fontSize: 'var(--font-size-3xl)',
              fontWeight: 800,
              lineHeight: 1.2,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            Escolha sua gaveta
          </h1>
          
          <p style={{
            marginTop: 'var(--spacing-3)',
            marginBottom: 0,
            fontSize: 'var(--font-size-base)',
            lineHeight: 1.6,
            color: 'var(--color-text-muted)',
            maxWidth: '600px'
          }}>
            Cada gaveta contém um produto único com preço já definido.
          </p>

          {/* Filtros - Mobile Optimized */}
          <div 
            className="filters-toolbar"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--spacing-3)',
              marginTop: 'var(--spacing-5)'
            }}
            role="group"
            aria-label="Filtros de catálogo"
          >
            <div className="form-group">
              <label htmlFor="region-select" className="form-label">
                🌎 Região
              </label>
              <select
                id="region-select"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="form-input"
                aria-describedby="region-help"
              >
                <option value="SP">🇧🇷 São Paulo</option>
                <option value="PT">🇵🇹 Portugal</option>
              </select>
              <span id="region-help" className="form-help">Selecione sua região</span>
            </div>

            <div className="form-group">
              <label htmlFor="locker-select" className="form-label">
                📍 Ponto de retirada
              </label>
              <select
                id="locker-select"
                value={lockerId}
                onChange={(e) => setLockerId(e.target.value)}
                className="form-input"
                aria-describedby="locker-help"
              >
                {(LOCKER_OPTIONS[region] || []).map((item) => (
                  <option key={item.locker_id} value={item.locker_id}>
                    {item.label}
                  </option>
                ))}
              </select>
              {selectedLockerDetails && (
                <span id="locker-help" className="form-help">
                  📮 {selectedLockerDetails.address}
                </span>
              )}
            </div>
          </div>

          {/* Ações Rápidas */}
          <div 
            style={{
              display: 'flex',
              gap: 'var(--spacing-3)',
              marginTop: 'var(--spacing-5)',
              paddingTop: 'var(--spacing-4)',
              borderTop: '1px solid var(--color-border)',
              flexWrap: 'wrap'
            }}
          >
            <Link to="/" className="btn btn--secondary">
              ← Voltar
            </Link>
            <Link to="/meus-pedidos" className="btn btn--secondary">
              📋 Meus Pedidos
            </Link>
          </div>
        </section>

        {/* Erro - Feedback claro */}
        {error && (
          <div 
            className="error-banner"
            role="alert"
            style={{
              marginBottom: 'var(--spacing-4)',
              padding: 'var(--spacing-4)',
              borderRadius: 'var(--radius-lg)',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-3)',
              flexWrap: 'wrap'
            }}
          >
            <span style={{ fontSize: '20px' }}>⚠️</span>
            <div style={{ flex: 1, color: '#991b1b', fontSize: 'var(--font-size-sm)' }}>
              <strong>Ops!</strong> {error}
            </div>
            <button 
              onClick={() => window.location.reload()} 
              className="btn btn--danger"
              style={{ padding: 'var(--spacing-2) var(--spacing-4)', fontSize: 'var(--font-size-sm)' }}
            >
              Tentar novamente
            </button>
          </div>
        )}

        {/* Lista de Produtos */}
        {loading ? (
          <div className="products-grid" style={{ 
            display: 'grid', 
            gap: 'var(--spacing-3)',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))'
          }}>
            {[1, 2, 3, 4, 5, 6].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : (
          <>
            {/* Header de Resultados */}
            <div 
              className="results-header"
              style={{
                marginBottom: 'var(--spacing-4)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 'var(--spacing-3)'
              }}
            >
              <h2 style={{
                fontSize: 'var(--font-size-xl)',
                fontWeight: 700,
                color: 'white',
                margin: 0
              }}>
                Gavetas disponíveis
                {items.length > 0 && (
                  <span style={{
                    fontSize: 'var(--font-size-base)',
                    fontWeight: 500,
                    color: '#e0e7ff',
                    marginLeft: 'var(--spacing-2)'
                  }}>
                    ({items.length})
                  </span>
                )}
              </h2>
            </div>

            {/* Grid de Produtos */}
            <div 
              className="products-grid"
              style={{
                display: 'grid',
                gap: 'var(--spacing-3)',
                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))'
              }}
              role="list"
              aria-label="Lista de produtos disponíveis"
            >
              {items.length === 0 ? (
                <article 
                  className="card empty-state"
                  style={{
                    gridColumn: '1 / -1',
                    textAlign: 'center',
                    padding: 'var(--spacing-10)',
                    background: 'white'
                  }}
                >
                  <div style={{ fontSize: '48px', marginBottom: 'var(--spacing-4)' }}>🔍</div>
                  <h3 style={{
                    fontSize: 'var(--font-size-xl)',
                    fontWeight: 600,
                    color: 'var(--color-text)',
                    marginBottom: 'var(--spacing-3)'
                  }}>
                    Nenhuma gaveta disponível
                  </h3>
                  <p style={{
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--color-text-muted)',
                    marginBottom: 'var(--spacing-4)'
                  }}>
                    Não encontramos produtos ativos para este locker.
                    Tente selecionar outro ponto de retirada.
                  </p>
                  <button
                    onClick={() => setLockerId(LOCKER_OPTIONS[region]?.[0]?.locker_id || "")}
                    className="btn btn--secondary"
                  >
                    Ver outro locker
                  </button>
                </article>
              ) : (
                items.map((item) => {
                  const isExpanded = expandedCards.has(item.slot);
                  return (
                    <article 
                      key={`${item.locker_id}-${item.slot}`}
                      className="card product-card"
                      style={{
                        background: 'white',
                        borderRadius: 'var(--radius-xl)',
                        padding: 'var(--spacing-4)',
                        boxShadow: 'var(--shadow-md)',
                        transition: 'all var(--transition-base)',
                        animation: 'slideDown 0.3s ease-out'
                      }}
                      role="listitem"
                    >
                      {/* Conteúdo Principal */}
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        gap: 'var(--spacing-3)' 
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-3)', flex: 1 }}>
                          <div style={{
                            width: 50,
                            height: 50,
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            borderRadius: 'var(--radius-lg)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 'var(--font-size-xl)',
                            fontWeight: 800,
                            color: 'white',
                            flexShrink: 0
                          }}>
                            {item.slot}
                          </div>
                          <div style={{ flex: 1 }}>
                            <div style={{
                              fontSize: 'var(--font-size-base)',
                              fontWeight: 700,
                              color: 'var(--color-text)',
                              marginBottom: 'var(--spacing-1)',
                              lineHeight: 1.3
                            }}>
                              {item.name}
                            </div>
                            <div style={{
                              fontSize: 'var(--font-size-lg)',
                              fontWeight: 800,
                              color: 'var(--color-primary)'
                            }}>
                              {formatMoney(item.amount_cents, item.currency)}
                            </div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', gap: 'var(--spacing-2)', alignItems: 'center' }}>
                          <button
                            onClick={() => handleReserve(item)}
                            disabled={submittingSlot === item.slot}
                            className="btn btn--primary"
                            style={{
                              width: 50,
                              height: 50,
                              borderRadius: 'var(--radius-lg)',
                              padding: 0,
                              fontSize: '20px'
                            }}
                            aria-label={`Reservar gaveta ${item.slot}`}
                          >
                            {submittingSlot === item.slot ? '⏳' : '🛒'}
                          </button>
                          <button
                            onClick={() => toggleExpand(item.slot)}
                            className="btn btn--secondary"
                            style={{
                              width: 40,
                              height: 40,
                              borderRadius: 'var(--radius-md)',
                              padding: 0,
                              fontSize: 'var(--font-size-sm)'
                            }}
                            aria-label={isExpanded ? 'Recolher detalhes' : 'Expandir detalhes'}
                            aria-expanded={isExpanded}
                          >
                            {isExpanded ? '▲' : '▼'}
                          </button>
                        </div>
                      </div>

                      {/* Conteúdo Expandido */}
                      {isExpanded && (
                        <div 
                          style={{
                            marginTop: 'var(--spacing-4)',
                            paddingTop: 'var(--spacing-4)',
                            borderTop: '1px solid var(--color-border)',
                            animation: 'slideDown 0.3s ease-out'
                          }}
                        >
                          <div style={{ display: 'grid', gap: 'var(--spacing-2)', fontSize: 'var(--font-size-sm)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                              <span style={{ fontWeight: 600, color: 'var(--color-text-muted)' }}>SKU:</span>
                              <span>{item.sku_id}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                              <span style={{ fontWeight: 600, color: 'var(--color-text-muted)' }}>Moeda:</span>
                              <span>{item.currency}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                              <span style={{ fontWeight: 600, color: 'var(--color-text-muted)' }}>Atualizado:</span>
                              <span>
                                {item.updated_at
                                  ? new Date(item.updated_at).toLocaleDateString(
                                      region === "SP" ? "pt-BR" : "pt-PT",
                                      { day: '2-digit', month: 'short', year: 'numeric' }
                                    )
                                  : "-"}
                              </span>
                            </div>
                            {item.description && (
                              <div style={{ marginTop: 'var(--spacing-2)' }}>
                                <span style={{ fontWeight: 600, color: 'var(--color-text-muted)' }}>Descrição:</span>
                                <p style={{ margin: 'var(--spacing-1) 0 0', color: 'var(--color-text)' }}>
                                  {item.description}
                                </p>
                              </div>
                            )}
                            {item.imageURL && (
                              <div style={{
                                marginTop: 'var(--spacing-3)',
                                width: '100%',
                                maxHeight: 120,
                                borderRadius: 'var(--radius-lg)',
                                overflow: 'hidden'
                              }}>
                                <img
                                  src={item.imageURL}
                                  alt={item.name}
                                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                  onError={(e) => e.target.style.display = 'none'}
                                  loading="lazy"
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

            {/* Hint de Scroll */}
            {items.length > 0 && (
              <div 
                className="scroll-hint"
                style={{
                  textAlign: 'center',
                  padding: 'var(--spacing-4)',
                  color: '#e0e7ff',
                  fontSize: 'var(--font-size-xs)',
                  marginTop: 'var(--spacing-4)'
                }}
              >
                {items.length} gavetas disponíveis • Role para ver mais
              </div>
            )}
          </>
        )}
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </main>
  );
}