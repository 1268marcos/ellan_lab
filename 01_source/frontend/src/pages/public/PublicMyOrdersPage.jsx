// 01_source/frontend/src/pages/public/PublicMyOrdersPage.jsx
// Área - Melhoria
// UX - Cards informativos com ícones, hierarquia visual clara
// CX - Feedback de carregamento, empty states amigáveis
// Acessibilidade - ARIA labels, navegação por teclado, contraste WCAG AA
// Performance - Skeleton loading, useMemo para filtros
// Conversão - CTA "Novo Pedido" visível, links claros para detalhes
// Responsivo - Mobile-first, grid adaptativo
// Funcional - Filtro por status com contagem em tempo real

import React, { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { fetchMyOrders } from "../../services/publicApi";

// Componente de Badge de Status
function OrderStatusBadge({ status }) {
  const statusConfig = {
    PAYMENT_PENDING: { bg: "#fef3c7", color: "#92400e", label: "Pagamento Pendente" },
    PAID_PENDING_PICKUP: { bg: "#dbeafe", color: "#1e40af", label: "Aguardando Retirada" },
    PICKED_UP: { bg: "#d1fae5", color: "#065f46", label: "Retirado" }, // sem evidência por: sensor OU comprovação humana
    EXPIRED: { bg: "#fee2e2", color: "#991b1b", label: "Expirado" },
    CANCELLED: { bg: "#f3f4f6", color: "#374151", label: "Cancelado" },
    DISPENSED: { bg: "rgba(95,61,196,0.22)", color: "rgba(95,61,196,0.45)", label: "Máquina Liberou" },
    // DISPENSED: { bg: "#d1fae5", color: "#065f46", label: "Retirado" },  // só quando for possível ter evidência
  };

  const config = statusConfig[status] || { bg: "#f3f4f6", color: "#374151", label: status };

  return (
    <span
      style={{
        display: "inline-flex",
        padding: "4px 12px",
        borderRadius: 999,
        background: config.bg,
        color: config.color,
        fontSize: 12,
        fontWeight: 600,
        whiteSpace: "nowrap",
      }}
    >
      {config.label}
    </span>
  );
}

// Componente de Card de Pedido
function OrderCard({ order }) {
  const formatDateTime = (value) => {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat("pt-BR", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(date);
  };

  const formatAmount = (cents) => {
    if (cents == null) return "—";
    const numeric = Number(cents);
    if (Number.isNaN(numeric)) return String(cents);
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(numeric / 100);
  };

  return (
    <Link
      to={`/meus-pedidos/${order.id}`}
      style={orderCardLinkStyle}
      aria-label={`Ver detalhes do pedido ${order.id}`}
    >
      <article style={orderCardStyle}>
        {/* Header do Card */}
        <div style={cardHeaderStyle}>
          <div style={orderIdContainerStyle}>
            <span style={orderIconStyle}>📦</span>
            <strong style={orderIdStyle}>{order.id}</strong>
          </div>
          <OrderStatusBadge status={order.status} />
        </div>

        {/* Corpo do Card */}
        <div style={cardBodyStyle}>
          <div style={infoGridStyle}>
            <div style={infoItemStyle}>
              <span style={infoLabelStyle}>Produto</span>
              <span style={infoValueStyle}>{order.sku_id || "—"}</span>
            </div>
            <div style={infoItemStyle}>
              <span style={infoLabelStyle}>Valor</span>
              <span style={infoValueStyle}>{formatAmount(order.amount_cents)}</span>
            </div>
            <div style={infoItemStyle}>
              <span style={infoLabelStyle}>Locker</span>
              <span style={infoValueStyle}>{order.totem_id || "—"}</span>
            </div>
            <div style={infoItemStyle}>
              <span style={infoLabelStyle}>Gaveta</span>
              <span style={infoValueStyle}>{order.slot ?? "—"}</span>
            </div>
          </div>

          {/* Comprovante Fiscal (se disponível) */}
          {order.receipt_code && (
            <div style={receiptSectionStyle}>
              <span style={receiptIconStyle}>🧾</span>
              <div>
                <span style={receiptLabelStyle}>Comprovante fiscal</span>
                <div style={receiptCodeStyle}>{order.receipt_code}</div>
              </div>
            </div>
          )}

          {/* Data de Criação */}
          <div style={dateSectionStyle}>
            <span style={dateIconStyle}>📅</span>
            <span style={dateTextStyle}>
              Criado em {formatDateTime(order.created_at)}
            </span>
          </div>
        </div>

        {/* Footer do Card */}
        <div style={cardFooterStyle}>
          <span style={viewDetailsStyle}>Ver detalhes →</span>
        </div>
      </article>
    </Link>
  );
}

// Componente de Filtro
function OrdersFilter({ filter, onFilterChange, searchQuery, onSearchQueryChange, totalOrders, matchedOrders }) {
  return (
    <div style={filterContainerStyle}>
      <div style={filterLeftStyle}>
        <span style={filterIconStyle}>🔍</span>
        <select
          value={filter}
          onChange={(e) => onFilterChange(e.target.value)}
          style={filterSelectStyle}
          aria-label="Filtrar pedidos por status"
        >
          <option value="all">Todos os pedidos ({totalOrders})</option>
          <option value="PAYMENT_PENDING">Pagamento Pendente</option>
          <option value="PAID_PENDING_PICKUP">Aguardando Retirada</option>
          <option value="PICKED_UP">Retirados</option> {/*  provalvemente bug - isso depende de sensor OU confirmação humana */}
          <option value="DISPENSED">Liberados na Máquina</option>
          <option value="EXPIRED">Expirados</option>
          <option value="CANCELLED">Cancelados</option>
        </select>
      </div>
      <input
        value={searchQuery}
        onChange={(e) => onSearchQueryChange(e.target.value)}
        style={searchInputStyle}
        placeholder="Buscar por pedido/ref parceiro"
        aria-label="Buscar por order_id ou partner_order_ref"
      />
      <div style={filterHintStyle}>
        {matchedOrders} de {totalOrders} {totalOrders === 1 ? "pedido" : "pedidos"}
      </div>
    </div>
  );
}

// Componente de Empty State
function EmptyState() {
  return (
    <div style={emptyStateStyle}>
      <div style={emptyStateIconStyle}>📭</div>
      <h3 style={emptyStateTitleStyle}>Nenhum pedido encontrado</h3>
      <p style={emptyStateTextStyle}>
        Você ainda não realizou nenhum pedido. Comece comprando no nosso catálogo.
      </p>
      <Link to="/comprar" style={emptyStateButtonStyle}>
        🛒 Ir para o catálogo
      </Link>
    </div>
  );
}

// Componente de Loading Skeleton
function OrderSkeleton() {
  return (
    <div style={skeletonCardStyle}>
      <div style={skeletonHeaderStyle}>
        <div style={skeletonBadgeStyle}></div>
        <div style={skeletonBadgeStyle}></div>
      </div>
      <div style={skeletonBodyStyle}>
        <div style={skeletonLineStyle}></div>
        <div style={skeletonLineStyle}></div>
        <div style={skeletonLineStyle}></div>
      </div>
    </div>
  );
}

// Página Principal
export default function PublicMyOrdersPage() {
  const { token, loading: authLoading, isAuthenticated } = useAuth();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [pageLoading, setPageLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Carregar pedidos
  useEffect(() => {
    let active = true;

    async function load() {
      if (authLoading) return;

      if (!isAuthenticated || !token) {
        if (!active) return;
        setItems([]);
        setError("");
        setPageLoading(false);
        return;
      }

      try {
        if (active) {
          setPageLoading(true);
          setError("");
        }

        const data = await fetchMyOrders(token);
        if (!active) return;
        setItems(Array.isArray(data?.items) ? data.items : []);
        setError("");
      } catch (err) {
        if (!active) return;
        setItems([]);
        setError(err?.message || "Erro ao carregar pedidos");
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
  }, [token, authLoading, isAuthenticated]);

  // Filtrar pedidos
  const filteredItems = useMemo(() => {
    const statusFiltered = filter === "all" ? items : items.filter((item) => item.status === filter);
    const normalizedSearch = String(searchQuery || "").trim().toLowerCase();
    if (!normalizedSearch) return statusFiltered;
    return statusFiltered.filter((item) => {
      const orderId = String(item?.id || item?.order_id || "").toLowerCase();
      const partnerRef = String(item?.partner_order_ref || "").toLowerCase();
      return orderId.includes(normalizedSearch) || partnerRef.includes(normalizedSearch);
    });
  }, [items, filter, searchQuery]);

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        {/* Header da Página */}
        <header style={pageHeaderStyle}>
          <div>
            <h1 style={titleStyle}>Meus Pedidos</h1>
            <p style={subtitleStyle}>
              Acompanhe aqui todos os seus pedidos realizados no fluxo público.
            </p>
          </div>
          <Link to="/comprar" style={newOrderButtonStyle}>
            ✨ Novo Pedido
          </Link>
        </header>

        {/* Estado de Carregamento */}
        {authLoading || pageLoading ? (
          <div style={skeletonListStyle}>
            {[1, 2, 3].map((i) => (
              <OrderSkeleton key={i} />
            ))}
          </div>
        ) : null}

        {/* Estado de Erro */}
        {!authLoading && !pageLoading && error ? (
          <div style={errorCardStyle}>
            <div style={errorIconStyle}>⚠️</div>
            <div>
              <strong>Não foi possível carregar seus pedidos</strong>
              <p style={errorTextStyle}>{error}</p>
              <button
                onClick={() => window.location.reload()}
                style={retryButtonStyle}
              >
                🔄 Tentar novamente
              </button>
            </div>
          </div>
        ) : null}

        {/* Estado Vazio */}
        {!authLoading && !pageLoading && !error && items.length === 0 ? (
          <EmptyState />
        ) : null}

        {/* Lista de Pedidos */}
        {!authLoading && !pageLoading && !error && items.length > 0 ? (
          <>
            {/* Filtro */}
            <OrdersFilter
              filter={filter}
              onFilterChange={setFilter}
              searchQuery={searchQuery}
              onSearchQueryChange={setSearchQuery}
              totalOrders={items.length}
              matchedOrders={filteredItems.length}
            />

            {/* Lista */}
            {filteredItems.length === 0 ? (
              <div style={noResultsStyle}>
                <span style={noResultsIconStyle}>🔍</span>
                <p>Nenhum pedido encontrado com este filtro.</p>
                <button
                  onClick={() => setFilter("all")}
                  style={clearFilterButtonStyle}
                >
                  Limpar filtro
                </button>
              </div>
            ) : (
              <div style={listWrapperStyle}>
                {filteredItems.map((item) => (
                  <OrderCard key={item.id} order={item} />
                ))}
              </div>
            )}
          </>
        ) : null}

        {/* Footer Informativo */}
        {!authLoading && !pageLoading && items.length > 0 && (
          <footer style={pageFooterStyle}>
            <p style={footerTextStyle}>
              💡 Dica: Clique em qualquer pedido para ver detalhes completos e
              informações de retirada.
            </p>
          </footer>
        )}
      </div>

      {/* Estilos CSS Inline */}
      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @media (max-width: 768px) {
          .page-header {
            flex-direction: column;
            gap: 16px;
          }
          .order-card {
            padding: 16px;
          }
        }
      `}</style>
    </main>
  );
}

// ============================================
// ESTILOS
// ============================================

const pageStyle = {
  minHeight: "100vh",
  background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
  padding: "24px 16px",
};

const containerStyle = {
  maxWidth: 960,
  margin: "0 auto",
};

const pageHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 16,
  marginBottom: 24,
  flexWrap: "wrap",
};

const titleStyle = {
  margin: "0 0 8px 0",
  fontSize: 32,
  fontWeight: 800,
  color: "#1a202c",
};

const subtitleStyle = {
  margin: 0,
  fontSize: 16,
  color: "#4a5568",
  lineHeight: 1.5,
};

const newOrderButtonStyle = {
  textDecoration: "none",
  padding: "12px 20px",
  borderRadius: 12,
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  fontWeight: 700,
  fontSize: 14,
  boxShadow: "0 4px 6px -1px rgba(102, 126, 234, 0.4)",
  transition: "all 0.2s",
  whiteSpace: "nowrap",
};

const listWrapperStyle = {
  display: "grid",
  gap: 16,
};

const orderCardLinkStyle = {
  textDecoration: "none",
  color: "inherit",
  display: "block",
};

const orderCardStyle = {
  padding: 20,
  borderRadius: 16,
  border: "1px solid #e2e8f0",
  background: "white",
  boxShadow: "0 2px 4px rgba(0, 0, 0, 0.05)",
  transition: "all 0.2s",
};

const cardHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  marginBottom: 16,
  flexWrap: "wrap",
};

const orderIdContainerStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
};

const orderIconStyle = {
  fontSize: 20,
};

const orderIdStyle = {
  fontSize: 18,
  color: "#1a202c",
  wordBreak: "break-all",
};

const cardBodyStyle = {
  display: "grid",
  gap: 16,
};

const infoGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
  gap: 12,
};

const infoItemStyle = {
  display: "grid",
  gap: 4,
};

const infoLabelStyle = {
  fontSize: 12,
  color: "#718096",
  fontWeight: 500,
};

const infoValueStyle = {
  fontSize: 14,
  color: "#1a202c",
  fontWeight: 600,
};

const receiptSectionStyle = {
  display: "flex",
  alignItems: "flex-start",
  gap: 10,
  padding: 12,
  borderRadius: 12,
  background: "#f7fafc",
  border: "1px dashed #e2e8f0",
};

const receiptIconStyle = {
  fontSize: 18,
  flexShrink: 0,
};

const receiptLabelStyle = {
  display: "block",
  fontSize: 12,
  color: "#718096",
  marginBottom: 4,
};

const receiptCodeStyle = {
  fontSize: 14,
  fontWeight: 700,
  color: "#2d3748",
  fontFamily: "monospace",
};

const dateSectionStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: 13,
  color: "#718096",
};

const dateIconStyle = {
  fontSize: 16,
};

const dateTextStyle = {
  fontWeight: 500,
};

const cardFooterStyle = {
  marginTop: 8,
  paddingTop: 16,
  borderTop: "1px solid #e2e8f0",
};

const viewDetailsStyle = {
  fontSize: 14,
  fontWeight: 600,
  color: "#667eea",
};

const filterContainerStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 16,
  marginBottom: 20,
  padding: 16,
  background: "white",
  borderRadius: 12,
  border: "1px solid #e2e8f0",
  flexWrap: "wrap",
};

const filterLeftStyle = {
  display: "flex",
  alignItems: "center",
  gap: 10,
};

const filterIconStyle = {
  fontSize: 18,
};

const filterSelectStyle = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #e2e8f0",
  background: "#f7fafc",
  color: "#1a202c",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
  outline: "none",
  minWidth: 200,
};

const filterHintStyle = {
  fontSize: 13,
  color: "#718096",
  fontWeight: 500,
};

const searchInputStyle = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #e2e8f0",
  background: "#f7fafc",
  color: "#1a202c",
  fontSize: 14,
  fontWeight: 600,
  outline: "none",
  minWidth: 220,
};

const emptyStateStyle = {
  textAlign: "center",
  padding: 48,
  background: "white",
  borderRadius: 16,
  border: "1px solid #e2e8f0",
};

const emptyStateIconStyle = {
  fontSize: 64,
  marginBottom: 16,
};

const emptyStateTitleStyle = {
  margin: "0 0 8px 0",
  fontSize: 20,
  fontWeight: 700,
  color: "#1a202c",
};

const emptyStateTextStyle = {
  margin: "0 0 24px 0",
  fontSize: 14,
  color: "#718096",
  lineHeight: 1.5,
};

const emptyStateButtonStyle = {
  display: "inline-block",
  textDecoration: "none",
  padding: "12px 24px",
  borderRadius: 12,
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  fontWeight: 700,
  fontSize: 14,
  transition: "all 0.2s",
};

const errorCardStyle = {
  padding: 20,
  borderRadius: 16,
  border: "1px solid #fecaca",
  background: "#fff1f2",
  display: "flex",
  gap: 16,
  alignItems: "flex-start",
  marginBottom: 20,
};

const errorIconStyle = {
  fontSize: 24,
  flexShrink: 0,
};

const errorTextStyle = {
  margin: "8px 0 0 0",
  fontSize: 14,
  color: "#991b1b",
};

const retryButtonStyle = {
  marginTop: 12,
  padding: "10px 16px",
  borderRadius: 10,
  border: "none",
  background: "#dc2626",
  color: "white",
  fontWeight: 600,
  fontSize: 14,
  cursor: "pointer",
  transition: "all 0.2s",
};

const noResultsStyle = {
  textAlign: "center",
  padding: 40,
  background: "white",
  borderRadius: 16,
  border: "1px solid #e2e8f0",
};

const noResultsIconStyle = {
  fontSize: 40,
  display: "block",
  marginBottom: 12,
};

const clearFilterButtonStyle = {
  marginTop: 12,
  padding: "10px 20px",
  borderRadius: 10,
  border: "1px solid #e2e8f0",
  background: "#f7fafc",
  color: "#1a202c",
  fontWeight: 600,
  fontSize: 14,
  cursor: "pointer",
  transition: "all 0.2s",
};

const pageFooterStyle = {
  marginTop: 32,
  padding: 20,
  textAlign: "center",
  background: "white",
  borderRadius: 12,
  border: "1px solid #e2e8f0",
};

const footerTextStyle = {
  margin: 0,
  fontSize: 13,
  color: "#718096",
};

// Skeleton Styles
const skeletonListStyle = {
  display: "grid",
  gap: 16,
};

const skeletonCardStyle = {
  padding: 20,
  borderRadius: 16,
  border: "1px solid #e2e8f0",
  background: "white",
};

const skeletonHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  marginBottom: 16,
};

const skeletonBadgeStyle = {
  width: 120,
  height: 28,
  borderRadius: 14,
  background: "linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)",
  backgroundSize: "200% 100%",
  animation: "shimmer 1.5s infinite",
};

const skeletonBodyStyle = {
  display: "grid",
  gap: 12,
};

const skeletonLineStyle = {
  height: 16,
  borderRadius: 8,
  background: "linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)",
  backgroundSize: "200% 100%",
  animation: "shimmer 1.5s infinite",
};