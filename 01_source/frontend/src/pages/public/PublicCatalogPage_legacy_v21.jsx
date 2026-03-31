
































// 01_source/frontend/src/pages/public/PublicCatalogPage.jsx
// UX Mobile-First
// Otimizado para SEO
// Filtros: Ordem Gaveta, Ordem Sabor (destaque no nome), Menor Preço, Maior Preço
// Busca: Filtro por nome do produto/sabor com busca em tempo real
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const BACKEND_SP = import.meta.env.VITE_BACKEND_SP_BASE_URL || "http://localhost:8201";
const BACKEND_PT = import.meta.env.VITE_BACKEND_PT_BASE_URL || "http://localhost:8202";

const LOCKER_OPTIONS = {
  ES: [
    { locker_id: "ES-MADRID-CENTRO-LK-001", label: "Madrid Centro", address: "Puerta del Sol, 13" },
  ],
  PR: [
    { locker_id: "PR-CAPITAL-SANTAFELICIDADE-LK-001", label: "Curitiba Santa Felicidade", address: "Avenida Manuel Ribas, 500" },
  ],
  RJ: [
    { locker_id: "RJ-CAPITAL-CENTRO-LK-001", label: "Rio de Janeiro Centro", address: "Praça Mauá, 51-A" },
  ],
  SP: [
    { locker_id: "SP-OSASCO-CENTRO-LK-001", label: "Osasco Centro", address: "Av. dos Autonomistas, 1234" },
    { locker_id: "SP-CARAPICUIBA-JDMARILU-LK-001", label: "Carapicuíba Jardim Marilu - I", address: "Rua Bahia, 567" },
    { locker_id: "SP-CARAPICUIBA-JDMARILU-LK-002", label: "Carapicuíba Jardim Marilu - II", address: "Rua Vereador Isaias, 651" },
    { locker_id: "CACIFO-SP-001", label: "Araraquara Centro", address: "Rua XV de Novembro, 1888" },
    { locker_id: "SP-ALPHAVILLE-SHOP-LK-001", label: "Barueri Alphaville", address: "Alphaville Shopping, Loja 20 Piso Amazonas" },
    { locker_id: "SP-VILAOLIMPIA-FOOD-LK-001", label: "São Paulo Vila Olímpia", address: "Rua Alvorada, 119" },
  ],
  PT: [
    { locker_id: "PT-MAIA-CENTRO-LK-001", label: "Maia Centro", address: "Rua do Comércio, 89" },
    { locker_id: "PT-GUIMARAES-AZUREM-LK-001", label: "Guimarães Azurém", address: "Avenida da Liberdade, 234" },
    { locker_id: "CACIFO-PT-001", label: "Porto Trindade", address: "Rua de Cedofeita, 1" },
    { locker_id: "PT-LISBOA-PHARMA-LK-001", label: "Lisboa Praça do Comércio", address: "Praça do Comércio, 2-B" },
  ],
};

// Tipos de ordenação disponíveis
const SORT_TYPES = {
  SLOT: "slot",
  NAME: "name",
  PRICE_ASC: "price_asc",
  PRICE_DESC: "price_desc",
};

const SORT_LABELS = {
  [SORT_TYPES.SLOT]: "🔢 Ordem de Gaveta",
  [SORT_TYPES.NAME]: "🍽️ Ordem de Sabor",
  [SORT_TYPES.PRICE_ASC]: "💰 Menor Preço",
  [SORT_TYPES.PRICE_DESC]: "💰 Maior Preço",
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

// Hook personalizado para debounce
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
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
  const [sortType, setSortType] = useState(SORT_TYPES.SLOT);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Debounce da busca para evitar renderizações excessivas
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  
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

  // Função para filtrar itens baseado no termo de busca
  const filteredBySearch = useMemo(() => {
    if (!debouncedSearchTerm.trim()) return items;
    
    const searchLower = debouncedSearchTerm.toLowerCase().trim();
    return items.filter(item => 
      item.name.toLowerCase().includes(searchLower) ||
      (item.description && item.description.toLowerCase().includes(searchLower))
    );
  }, [items, debouncedSearchTerm]);

  // Função de ordenação baseada no tipo selecionado
  const sortedItems = useMemo(() => {
    if (!filteredBySearch.length) return [];
    
    const itemsCopy = [...filteredBySearch];
    
    switch (sortType) {
      case SORT_TYPES.SLOT:
        return itemsCopy.sort((a, b) => a.slot - b.slot);
        
      case SORT_TYPES.NAME:
        return itemsCopy.sort((a, b) => {
          // Ordenação case-insensitive por nome (sabor)
          return a.name.localeCompare(b.name, 'pt', { sensitivity: 'base' });
        });
        
      case SORT_TYPES.PRICE_ASC:
        return itemsCopy.sort((a, b) => a.amount_cents - b.amount_cents);
        
      case SORT_TYPES.PRICE_DESC:
        return itemsCopy.sort((a, b) => b.amount_cents - a.amount_cents);
        
      default:
        return itemsCopy;
    }
  }, [filteredBySearch, sortType]);

  // Função para limpar a busca
  const clearSearch = useCallback(() => {
    setSearchTerm("");
  }, []);

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
            Escolha seu produto
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

          {/* Campo de Busca por Nome do Produto/Sabor */}
          <div 
            className="search-bar"
            style={{
              marginTop: 'var(--spacing-5)',
              marginBottom: 'var(--spacing-3)'
            }}
          >
            <div style={{
              position: 'relative',
              width: '100%'
            }}>
              <div style={{
                position: 'absolute',
                left: 'var(--spacing-3)',
                top: '50%',
                transform: 'translateY(-50%)',
                fontSize: 'var(--font-size-lg)',
                pointerEvents: 'none',
                color: '#9ca3af'
              }}>
                🔍
              </div>
              <input
                type="text"
                id="search-product"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar por sabor ou descrição..."
                style={{
                  width: '100%',
                  padding: 'var(--spacing-3) var(--spacing-3) var(--spacing-3) calc(var(--spacing-3) + 32px)',
                  fontSize: 'var(--font-size-base)',
                  borderRadius: 'var(--radius-lg)',
                  border: '1px solid #e2e8f0',
                  background: 'white',
                  transition: 'all var(--transition-base)',
                  outline: 'none'
                }}
                aria-label="Buscar produtos por nome ou descrição"
                onFocus={(e) => e.target.style.borderColor = '#667eea'}
                onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
              />
              {searchTerm && (
                <button
                  onClick={clearSearch}
                  style={{
                    position: 'absolute',
                    right: 'var(--spacing-3)',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    fontSize: 'var(--font-size-lg)',
                    cursor: 'pointer',
                    padding: 'var(--spacing-1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 'var(--radius-full)',
                    transition: 'background var(--transition-base)'
                  }}
                  aria-label="Limpar busca"
                  onMouseEnter={(e) => e.currentTarget.style.background = '#f3f4f6'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  ✕
                </button>
              )}
            </div>
            {debouncedSearchTerm && (
              <p style={{
                marginTop: 'var(--spacing-2)',
                fontSize: 'var(--font-size-xs)',
                color: '#e0e7ff',
                textAlign: 'right'
              }}>
                {filteredBySearch.length} {filteredBySearch.length === 1 ? 'resultado' : 'resultados'} encontrados
              </p>
            )}
          </div>

          {/* Ações Rápidas */}
          <div 
            style={{
              display: 'flex',
              gap: 'var(--spacing-3)',
              marginTop: 'var(--spacing-4)',
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
            {/* Header de Resultados com Filtros de Ordenação */}
            <div 
              className="results-header"
              style={{
                marginBottom: 'var(--spacing-4)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 'var(--spacing-3)',
                background: 'rgba(255,255,255,0.1)',
                padding: 'var(--spacing-3)',
                borderRadius: 'var(--radius-lg)',
                backdropFilter: 'blur(10px)'
              }}
            >
              <div>
                <h2 style={{
                  fontSize: 'var(--font-size-xl)',
                  fontWeight: 700,
                  color: 'white',
                  margin: 0
                }}>
                  Produtos disponíveis
                  {sortedItems.length > 0 && (
                    <span style={{
                      fontSize: 'var(--font-size-base)',
                      fontWeight: 500,
                      color: '#e0e7ff',
                      marginLeft: 'var(--spacing-2)'
                    }}>
                      ({sortedItems.length})
                    </span>
                  )}
                </h2>
              </div>
              
              {/* Seletor de Ordenação */}
              <div 
                className="sort-selector"
                style={{
                  display: 'flex',
                  gap: 'var(--spacing-2)',
                  flexWrap: 'wrap',
                  alignItems: 'center'
                }}
              >
                <label 
                  htmlFor="sort-select" 
                  style={{
                    fontSize: 'var(--font-size-sm)',
                    fontWeight: 600,
                    color: 'white',
                    marginRight: 'var(--spacing-1)'
                  }}
                >
                  Ordenar por:
                </label>
                <select
                  id="sort-select"
                  value={sortType}
                  onChange={(e) => setSortType(e.target.value)}
                  style={{
                    padding: 'var(--spacing-2) var(--spacing-3)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid rgba(255,255,255,0.3)',
                    background: 'rgba(255,255,255,0.95)',
                    fontSize: 'var(--font-size-sm)',
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all var(--transition-base)',
                    outline: 'none'
                  }}
                  aria-label="Ordenar produtos"
                >
                  <option value={SORT_TYPES.SLOT}>{SORT_LABELS[SORT_TYPES.SLOT]}</option>
                  <option value={SORT_TYPES.NAME}>{SORT_LABELS[SORT_TYPES.NAME]}</option>
                  <option value={SORT_TYPES.PRICE_ASC}>{SORT_LABELS[SORT_TYPES.PRICE_ASC]}</option>
                  <option value={SORT_TYPES.PRICE_DESC}>{SORT_LABELS[SORT_TYPES.PRICE_DESC]}</option>
                </select>
              </div>
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
              {sortedItems.length === 0 ? (
                <article 
                  className="card empty-state"
                  style={{
                    gridColumn: '1 / -1',
                    textAlign: 'center',
                    padding: 'var(--spacing-10)',
                    background: 'white'
                  }}
                >
                  <div style={{ fontSize: '48px', marginBottom: 'var(--spacing-4)' }}>
                    {debouncedSearchTerm ? '🔍' : '📭'}
                  </div>
                  <h3 style={{
                    fontSize: 'var(--font-size-xl)',
                    fontWeight: 600,
                    color: 'var(--color-text)',
                    marginBottom: 'var(--spacing-3)'
                  }}>
                    {debouncedSearchTerm 
                      ? `Nenhum produto encontrado para "${debouncedSearchTerm}"`
                      : 'Nenhum produto disponível'}
                  </h3>
                  <p style={{
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--color-text-muted)',
                    marginBottom: 'var(--spacing-4)'
                  }}>
                    {debouncedSearchTerm
                      ? `Tente buscar por outro sabor ou verifique a ortografia.`
                      : 'Não encontramos produtos ativos para este locker. Tente selecionar outro ponto de retirada.'}
                  </p>
                  {debouncedSearchTerm ? (
                    <button
                      onClick={clearSearch}
                      className="btn btn--primary"
                      style={{
                        padding: 'var(--spacing-2) var(--spacing-6)'
                      }}
                    >
                      Limpar busca
                    </button>
                  ) : (
                    <button
                      onClick={() => setLockerId(LOCKER_OPTIONS[region]?.[0]?.locker_id || "")}
                      className="btn btn--secondary"
                    >
                      Ver outro locker
                    </button>
                  )}
                </article>
              ) : (
                sortedItems.map((item) => {
                  const isExpanded = expandedCards.has(item.slot);
                  // Destaque visual baseado no tipo de ordenação
                  const isNameHighlighted = sortType === SORT_TYPES.NAME;
                  const isPriceHighlighted = sortType === SORT_TYPES.PRICE_ASC || sortType === SORT_TYPES.PRICE_DESC;
                  
                  // Destacar termo de busca no nome do produto
                  const highlightSearchTerm = (text, search) => {
                    if (!search) return text;
                    const parts = text.split(new RegExp(`(${search})`, 'gi'));
                    return parts.map((part, i) => 
                      part.toLowerCase() === search.toLowerCase() ? 
                        <mark key={i} style={{
                          background: '#fef3c7',
                          color: '#92400e',
                          padding: '0 2px',
                          borderRadius: 'var(--radius-sm)'
                        }}>{part}</mark> : 
                        part
                    );
                  };

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
                        animation: 'slideDown 0.3s ease-out',
                        border: sortType === SORT_TYPES.NAME && isExpanded ? '2px solid #667eea' : 'none'
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
                          {/* Gaveta - visível mas não destacada quando ordenado por sabor */}
                          <div style={{
                            width: 50,
                            height: 50,
                            background: isNameHighlighted ? '#e5e7eb' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            borderRadius: 'var(--radius-lg)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 'var(--font-size-xl)',
                            fontWeight: 800,
                            color: isNameHighlighted ? '#4a5568' : 'white',
                            flexShrink: 0,
                            transition: 'all var(--transition-base)'
                          }}>
                            {item.slot}
                          </div>
                          <div style={{ flex: 1 }}>
                            {/* Nome do Produto/Sabor - com destaque quando ordenado por sabor e highlight da busca */}
                            <div style={{
                              fontSize: isNameHighlighted ? 'var(--font-size-lg)' : 'var(--font-size-base)',
                              fontWeight: isNameHighlighted ? 800 : 700,
                              color: isNameHighlighted ? '#667eea' : 'var(--color-text)',
                              marginBottom: 'var(--spacing-1)',
                              lineHeight: 1.3,
                              transition: 'all var(--transition-base)'
                            }}>
                              {debouncedSearchTerm 
                                ? highlightSearchTerm(item.name, debouncedSearchTerm)
                                : item.name}
                              {isNameHighlighted && (
                                <span style={{
                                  marginLeft: 'var(--spacing-2)',
                                  fontSize: 'var(--font-size-xs)',
                                  background: '#667eea',
                                  color: 'white',
                                  padding: '2px 6px',
                                  borderRadius: 'var(--radius-full)',
                                  display: 'inline-block'
                                }}>
                                  Destaque
                                </span>
                              )}
                            </div>
                            {/* Preço - com destaque quando ordenado por preço */}
                            <div style={{
                              fontSize: isPriceHighlighted ? 'var(--font-size-xl)' : 'var(--font-size-lg)',
                              fontWeight: isPriceHighlighted ? 900 : 800,
                              color: isPriceHighlighted ? '#f59e0b' : 'var(--color-primary)',
                              transition: 'all var(--transition-base)',
                              display: 'inline-block'
                            }}>
                              {formatMoney(item.amount_cents, item.currency)}
                              {isPriceHighlighted && (
                                <span style={{
                                  marginLeft: 'var(--spacing-2)',
                                  fontSize: 'var(--font-size-xs)',
                                  background: '#f59e0b',
                                  color: 'white',
                                  padding: '2px 6px',
                                  borderRadius: 'var(--radius-full)',
                                  display: 'inline-block',
                                  verticalAlign: 'middle'
                                }}>
                                  {sortType === SORT_TYPES.PRICE_ASC ? 'Menor Preço ↑' : 'Maior Preço ↓'}
                                </span>
                              )}
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
                              fontSize: '20px',
                              transition: 'transform var(--transition-base)'
                            }}
                            aria-label={`Reservar ${item.name} - Gaveta ${item.slot}`}
                            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
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
                              fontSize: 'var(--font-size-sm)',
                              transition: 'transform var(--transition-base)'
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
                              <span style={{ fontWeight: 600, color: 'var(--color-text-muted)' }}>Gaveta:</span>
                              <span style={{ fontWeight: 700 }}>{item.slot}</span>
                            </div>
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
                                  {debouncedSearchTerm 
                                    ? highlightSearchTerm(item.description, debouncedSearchTerm)
                                    : item.description}
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

            {/* Hint de Scroll e Ordenação Atual */}
            {sortedItems.length > 0 && (
              <div 
                className="scroll-hint"
                style={{
                  textAlign: 'center',
                  padding: 'var(--spacing-4)',
                  color: '#e0e7ff',
                  fontSize: 'var(--font-size-xs)',
                  marginTop: 'var(--spacing-4)',
                  background: 'rgba(0,0,0,0.2)',
                  borderRadius: 'var(--radius-lg)',
                  backdropFilter: 'blur(5px)'
                }}
              >
                {sortedItems.length} {sortedItems.length === 1 ? 'produto' : 'produtos'} • 
                Ordenado por: {SORT_LABELS[sortType]} • 
                {debouncedSearchTerm && ` Busca: "${debouncedSearchTerm}" • `}
                Role para ver mais
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
        
        /* Melhorias de hover e interação */
        .product-card {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .product-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
        }
        
        /* Responsividade */
        @media (max-width: 640px) {
          .results-header {
            flex-direction: column;
            align-items: stretch;
          }
          
          .sort-selector {
            justify-content: space-between;
          }
        }
        
        /* Foco acessível */
        button:focus-visible, select:focus-visible, a:focus-visible, input:focus-visible {
          outline: 2px solid #667eea;
          outline-offset: 2px;
        }
        
        /* Estilo para o mark de highlight */
        mark {
          background: #fef3c7;
          color: #92400e;
          padding: 0 2px;
          border-radius: 4px;
        }
      `}</style>
    </main>
  );
}