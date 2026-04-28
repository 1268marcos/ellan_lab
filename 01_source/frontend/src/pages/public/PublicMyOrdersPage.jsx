// 01_source/frontend/src/pages/public/PublicMyOrdersPage.jsx
// Área - Melhoria
// UX - Cards informativos com ícones, hierarquia visual clara
// CX - Feedback de carregamento, empty states amigáveis
// Acessibilidade - ARIA labels, navegação por teclado, contraste WCAG AA
// Performance - Skeleton loading, useMemo para filtros
// Conversão - CTA "Novo Pedido" visível, links claros para detalhes
// Responsivo - Mobile-first, grid adaptativo
// Funcional - Filtro por status com contagem em tempo real

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { fetchMyOrders } from "../../services/publicApi";
import { PageHeader, StatusChips, SkeletonCard, ErrorCard, EmptyStateBlock, SummaryMetrics } from "./myAreaSharedComponents";
import { resolvePersonalGreeting } from "./myAreaDisplayName";
import {
  pageStyle,
  containerStyle,
  pageHeaderStyle,
  titleStyle,
  subtitleStyle,
  newOrderButtonStyle,
  filterLeftStyle,
  filterIconStyle,
  filterSelectStyle,
  chipsWrapStyle,
  statusChipStyle,
  statusChipActiveStyle,
} from "./myAreaSharedStyles";
import {
  sectionCardBaseStyle,
  elevatedCardBaseStyle,
  filterCardBaseStyle,
  errorCardBaseStyle,
  errorIconBaseStyle,
  errorTextBaseStyle,
} from "./myAreaSharedCardStyles";

const STATUS_CONFIG = {
  PAYMENT_PENDING: { bg: "#fef3c7", color: "#92400e", label: "Pagamento Pendente", accent: "#f59e0b" },
  PAID_PENDING_PICKUP: { bg: "#dbeafe", color: "#1e40af", label: "Aguardando Retirada", accent: "#3b82f6" },
  PICKED_UP: { bg: "#d1fae5", color: "#065f46", label: "Retirado", accent: "#10b981" },
  EXPIRED: { bg: "#fee2e2", color: "#991b1b", label: "Expirado", accent: "#ef4444" },
  CANCELLED: { bg: "#f3f4f6", color: "#374151", label: "Cancelado", accent: "#9ca3af" },
  DISPENSED: { bg: "#ede9fe", color: "#4c1d95", label: "Máquina Liberou", accent: "#8b5cf6" },
};

const ORDERS_PREFS_STORAGE_KEY = "ellan_public_my_orders_prefs_v1";

const DEFAULT_ORDERS_PREFS = {
  filter: "all",
  sortBy: "recent",
  searchQuery: "",
  page: 1,
};

function readStoredOrdersPrefs() {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(ORDERS_PREFS_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    return parsed;
  } catch {
    return null;
  }
}

// Componente de Badge de Status
function OrderStatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || { bg: "#f3f4f6", color: "#374151", label: status, accent: "#cbd5e1" };

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
  const statusVisual = STATUS_CONFIG[order?.status] || { accent: "#cbd5e1" };
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

  const formatShortDate = (value) => {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat("pt-BR", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(date);
  };

  return (
    <Link
      to={`/meus-pedidos/${order.id}`}
      style={orderCardLinkStyle}
      aria-label={`Ver detalhes do pedido ${order.id}`}
    >
      <article
        style={{
          ...orderCardStyle,
          borderLeft: `5px solid ${statusVisual.accent}`,
          boxShadow: "0 8px 20px rgba(15, 23, 42, 0.06)",
        }}
      >
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
            <div style={infoItemStyle}>
              <span style={infoLabelStyle}>Ref parceiro</span>
              <span style={infoValueStyle}>{order.partner_order_ref || "—"}</span>
            </div>
            <div style={infoItemStyle}>
              <span style={infoLabelStyle}>Expira em</span>
              <span style={infoValueStyle}>{formatShortDate(order.expires_at)}</span>
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
function OrdersFilter({
  filter,
  onFilterChange,
  sortBy,
  onSortByChange,
  searchQuery,
  onSearchQueryChange,
  onResetPreferences,
  totalOrders,
  matchedOrders,
  statusCounts,
}) {
  const statusOptions = [
    { key: "all", label: "Todos" },
    { key: "PAYMENT_PENDING", label: "Pagamento pendente" },
    { key: "PAID_PENDING_PICKUP", label: "Aguardando retirada" },
    { key: "PICKED_UP", label: "Retirados" },
    { key: "DISPENSED", label: "Liberados na máquina" },
    { key: "EXPIRED", label: "Expirados" },
    { key: "CANCELLED", label: "Cancelados" },
  ];

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
      <div style={filterLeftStyle}>
        <span style={filterIconStyle}>↕️</span>
        <select
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value)}
          style={filterSelectStyle}
          aria-label="Ordenar pedidos"
        >
          <option value="recent">Mais recente</option>
          <option value="oldest">Mais antigo</option>
          <option value="amount_desc">Maior valor</option>
          <option value="amount_asc">Menor valor</option>
          <option value="status">Status (A-Z)</option>
        </select>
      </div>
      <div style={searchWrapStyle}>
        <input
          value={searchQuery}
          onChange={(e) => onSearchQueryChange(e.target.value)}
          style={searchInputStyle}
          placeholder="Buscar por pedido/ref parceiro"
          aria-label="Buscar por order_id ou partner_order_ref"
        />
        {searchQuery ? (
          <button
            type="button"
            onClick={() => onSearchQueryChange("")}
            style={clearSearchButtonStyle}
            aria-label="Limpar busca"
          >
            Limpar
          </button>
        ) : null}
      </div>
      <div style={filterHintRowStyle}>
        <div style={filterHintStyle}>
          {matchedOrders} de {totalOrders} {totalOrders === 1 ? "pedido" : "pedidos"}
        </div>
        <button
          type="button"
          onClick={onResetPreferences}
          style={resetPrefsButtonStyle}
          aria-label="Resetar preferências de filtro, ordenação, busca e página"
        >
          Resetar preferências
        </button>
      </div>
      <StatusChips
        options={statusOptions}
        activeKey={filter}
        counts={statusCounts}
        onSelect={onFilterChange}
        wrapStyle={chipsWrapStyle}
        chipStyle={statusChipStyle}
        activeChipStyle={statusChipActiveStyle}
      />
    </div>
  );
}

// Componente de Loading Skeleton
function OrderSkeleton() {
  return (
    <SkeletonCard
      containerStyle={skeletonCardStyle}
      headerStyle={skeletonHeaderStyle}
      bodyStyle={skeletonBodyStyle}
      lineStyle={skeletonLineStyle}
      headerLeftStyle={skeletonBadgeStyle}
      headerRightStyle={skeletonBadgeStyle}
      lineCount={3}
    />
  );
}

// Página Principal
export default function PublicMyOrdersPage() {
  const { token, user, loading: authLoading, isAuthenticated } = useAuth();
  const greeting = resolvePersonalGreeting(user);
  const storedPrefs = readStoredOrdersPrefs();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [pageLoading, setPageLoading] = useState(true);
  const [filter, setFilter] = useState(() =>
    typeof storedPrefs?.filter === "string" ? storedPrefs.filter : DEFAULT_ORDERS_PREFS.filter
  );
  const [sortBy, setSortBy] = useState(() =>
    typeof storedPrefs?.sortBy === "string" ? storedPrefs.sortBy : DEFAULT_ORDERS_PREFS.sortBy
  );
  const [searchQuery, setSearchQuery] = useState(() =>
    typeof storedPrefs?.searchQuery === "string"
      ? storedPrefs.searchQuery
      : DEFAULT_ORDERS_PREFS.searchQuery
  );
  const [page, setPage] = useState(() =>
    Number.isInteger(storedPrefs?.page) && storedPrefs.page > 0
      ? storedPrefs.page
      : DEFAULT_ORDERS_PREFS.page
  );
  const pageSize = 6;

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

  const sortedItems = useMemo(() => {
    const list = [...filteredItems];
    const getAmount = (item) => Number(item?.amount_cents || 0);
    const getCreatedAt = (item) => {
      const t = new Date(item?.created_at || 0).getTime();
      return Number.isNaN(t) ? 0 : t;
    };
    if (sortBy === "oldest") {
      return list.sort((a, b) => getCreatedAt(a) - getCreatedAt(b));
    }
    if (sortBy === "amount_desc") {
      return list.sort((a, b) => getAmount(b) - getAmount(a));
    }
    if (sortBy === "amount_asc") {
      return list.sort((a, b) => getAmount(a) - getAmount(b));
    }
    if (sortBy === "status") {
      return list.sort((a, b) => String(a?.status || "").localeCompare(String(b?.status || "")));
    }
    return list.sort((a, b) => getCreatedAt(b) - getCreatedAt(a));
  }, [filteredItems, sortBy]);

  const totalPages = Math.max(1, Math.ceil(sortedItems.length / pageSize));
  const pagedItems = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sortedItems.slice(start, start + pageSize);
  }, [sortedItems, page]);

  useEffect(() => {
    setPage(1);
  }, [filter, searchQuery, sortBy]);

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const payload = {
      filter,
      sortBy,
      searchQuery,
      page,
    };
    try {
      window.localStorage.setItem(ORDERS_PREFS_STORAGE_KEY, JSON.stringify(payload));
    } catch {
      // ignora falhas de persistência (storage bloqueado/quota)
    }
  }, [filter, sortBy, searchQuery, page]);

  const handleResetPreferences = useCallback(() => {
    setFilter(DEFAULT_ORDERS_PREFS.filter);
    setSortBy(DEFAULT_ORDERS_PREFS.sortBy);
    setSearchQuery(DEFAULT_ORDERS_PREFS.searchQuery);
    setPage(DEFAULT_ORDERS_PREFS.page);
  }, []);

  const statusCounts = useMemo(() => {
    const counts = {
      all: items.length,
      PAYMENT_PENDING: 0,
      PAID_PENDING_PICKUP: 0,
      PICKED_UP: 0,
      DISPENSED: 0,
      EXPIRED: 0,
      CANCELLED: 0,
    };
    for (const item of items) {
      const status = String(item?.status || "").toUpperCase();
      if (counts[status] != null) counts[status] += 1;
    }
    return counts;
  }, [items]);

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        {/* Header da Página */}
        <PageHeader
          title="Meus Pedidos"
          subtitle={`${greeting}Acompanhe aqui todos os seus pedidos realizados no fluxo público.`}
          ctaTo="/comprar"
          ctaLabel="✨ Novo Pedido"
          headerStyle={pageHeaderStyle}
          titleStyle={titleStyle}
          subtitleStyle={subtitleStyle}
          ctaStyle={newOrderButtonStyle}
        />
        {!authLoading && !pageLoading && !error && items.length > 0 ? (
          <SummaryMetrics
            sectionAriaLabel="Resumo dos pedidos"
            sectionStyle={summaryBarStyle}
            cardStyle={summaryMetricStyle}
            labelStyle={summaryMetricLabelStyle}
            valueStyle={summaryMetricValueStyle}
            items={[
              { key: "all", label: "Total", value: statusCounts.all },
              { key: "pending_pickup", label: "Aguardando retirada", value: statusCounts.PAID_PENDING_PICKUP },
              { key: "payment_pending", label: "Pagamento pendente", value: statusCounts.PAYMENT_PENDING },
              { key: "expired", label: "Expirados", value: statusCounts.EXPIRED },
            ]}
          />
        ) : null}

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
          <ErrorCard
            title="Não foi possível carregar seus pedidos"
            message={error}
            icon="⚠️"
            containerStyle={errorCardStyle}
            iconStyle={errorIconStyle}
            textStyle={errorTextStyle}
            action={
              <button
                onClick={() => window.location.reload()}
                style={retryButtonStyle}
              >
                🔄 Tentar novamente
              </button>
            }
          />
        ) : null}

        {/* Estado Vazio */}
        {!authLoading && !pageLoading && !error && items.length === 0 ? (
          <EmptyStateBlock
            title="Nenhum pedido encontrado"
            description="Você ainda não realizou nenhum pedido. Comece comprando no nosso catálogo."
            icon="📭"
            ctaTo="/comprar"
            ctaLabel="🛒 Ir para o catálogo"
            containerStyle={emptyStateStyle}
            iconStyle={emptyStateIconStyle}
            titleStyle={emptyStateTitleStyle}
            descriptionStyle={emptyStateTextStyle}
            buttonStyle={emptyStateButtonStyle}
          />
        ) : null}

        {/* Lista de Pedidos */}
        {!authLoading && !pageLoading && !error && items.length > 0 ? (
          <>
            {/* Filtro */}
            <OrdersFilter
              filter={filter}
              onFilterChange={setFilter}
              sortBy={sortBy}
              onSortByChange={setSortBy}
              searchQuery={searchQuery}
              onSearchQueryChange={setSearchQuery}
              onResetPreferences={handleResetPreferences}
              totalOrders={items.length}
              matchedOrders={sortedItems.length}
              statusCounts={statusCounts}
            />

            {/* Lista */}
            {sortedItems.length === 0 ? (
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
                {pagedItems.map((item) => (
                  <OrderCard key={item.id} order={item} />
                ))}
                <div style={paginationWrapStyle}>
                  <button
                    type="button"
                    onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                    style={paginationButtonStyle}
                    disabled={page <= 1}
                  >
                    ← Anterior
                  </button>
                  <span style={paginationInfoStyle}>
                    Página {page} de {totalPages}
                  </span>
                  <button
                    type="button"
                    onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                    style={paginationButtonStyle}
                    disabled={page >= totalPages}
                  >
                    Próxima →
                  </button>
                </div>
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
  ...elevatedCardBaseStyle,
  padding: 20,
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
  ...filterCardBaseStyle,
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 16,
  marginBottom: 20,
  flexWrap: "wrap",
};

const searchWrapStyle = {
  display: "flex",
  gap: 8,
  alignItems: "center",
  flexWrap: "wrap",
};


const filterHintRowStyle = {
  width: "100%",
  display: "flex",
  flexWrap: "wrap",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 12,
};

const filterHintStyle = {
  fontSize: 13,
  color: "#718096",
  fontWeight: 500,
};

const resetPrefsButtonStyle = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #cbd5e1",
  background: "#ffffff",
  color: "#334155",
  fontWeight: 600,
  fontSize: 13,
  cursor: "pointer",
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

const clearSearchButtonStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid #cbd5e1",
  background: "#ffffff",
  color: "#334155",
  fontWeight: 600,
  fontSize: 13,
  cursor: "pointer",
};


const summaryBarStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
  gap: 10,
  marginBottom: 16,
};

const summaryMetricStyle = {
  ...sectionCardBaseStyle,
  padding: "10px 12px",
  display: "grid",
  gap: 4,
};

const summaryMetricLabelStyle = {
  fontSize: 12,
  color: "#64748b",
  fontWeight: 600,
};

const summaryMetricValueStyle = {
  fontSize: 20,
  lineHeight: 1,
  color: "#0f172a",
};

const paginationWrapStyle = {
  marginTop: 10,
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
  borderTop: "1px solid #e2e8f0",
  paddingTop: 10,
};

const paginationButtonStyle = {
  padding: "9px 12px",
  borderRadius: 10,
  border: "1px solid #cbd5e1",
  background: "#ffffff",
  color: "#0f172a",
  fontWeight: 600,
  fontSize: 13,
  cursor: "pointer",
};

const paginationInfoStyle = {
  fontSize: 13,
  color: "#475569",
  fontWeight: 600,
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
  ...errorCardBaseStyle,
  marginBottom: 20,
};

const errorIconStyle = {
  ...errorIconBaseStyle,
};

const errorTextStyle = {
  ...errorTextBaseStyle,
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