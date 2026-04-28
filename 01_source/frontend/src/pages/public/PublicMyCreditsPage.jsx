import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { fetchMyCredits } from "../../services/publicApi";
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
  emptyStateStyle,
  emptyStateIconStyle,
  emptyStateTitleStyle,
  emptyStateTextStyle,
  emptyStateButtonStyle,
  skeletonListStyle,
  skeletonCardStyle,
  skeletonHeaderStyle,
  skeletonBodyStyle,
  skeletonLineStyle,
  skeletonLineShortStyle,
  skeletonBadgeStyle,
} from "./myAreaSharedStyles";
import {
  sectionCardBaseStyle,
  elevatedCardBaseStyle,
  filterCardBaseStyle,
  errorCardBaseStyle,
  errorIconBaseStyle,
  errorTextBaseStyle,
} from "./myAreaSharedCardStyles";

function formatMoney(cents, currency = "BRL") {
  const value = Number(cents || 0);
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: currency || "BRL",
  }).format(value / 100);
}

function formatDate(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium", timeStyle: "short" }).format(parsed);
}

function statusLabel(status) {
  const labels = {
    AVAILABLE: "Disponível",
    USED: "Usado",
    EXPIRED: "Expirado",
    REVOKED: "Revogado",
  };
  return labels[status] || status;
}

function renderCreditNotes(notes) {
  const text = String(notes || "");
  const pattern = /(order_id=)([0-9a-fA-F-]{36})/g;
  const parts = [];
  let lastIndex = 0;
  let match;
  let key = 0;

  while ((match = pattern.exec(text)) !== null) {
    const [fullMatch, prefix, orderId] = match;
    const start = match.index;
    if (start > lastIndex) {
      parts.push(<React.Fragment key={`text-${key++}`}>{text.slice(lastIndex, start)}</React.Fragment>);
    }
    parts.push(<React.Fragment key={`prefix-${key++}`}>{prefix}</React.Fragment>);
    parts.push(<React.Fragment key={`id-${key++}`}>{orderId}</React.Fragment>);
    parts.push(<React.Fragment key={`space-${key++}`}> </React.Fragment>);
    parts.push(
      <Link key={`link-${key++}`} to={`/meus-pedidos/${encodeURIComponent(orderId)}`}>
        Ver pedido
      </Link>
    );
    lastIndex = start + fullMatch.length;
  }

  if (lastIndex < text.length) {
    parts.push(<React.Fragment key={`text-${key++}`}>{text.slice(lastIndex)}</React.Fragment>);
  }

  return parts;
}

function extractOrderIdsFromNotes(notes) {
  const text = String(notes || "");
  const pattern = /order_id=([0-9a-fA-F-]{36})/g;
  const found = [];
  let match;
  while ((match = pattern.exec(text)) !== null) {
    const orderId = String(match[1] || "").trim();
    if (orderId) found.push(orderId);
  }
  return [...new Set(found)];
}

function renderCreditOrderLinks(credit) {
  const primaryOrderId = String(credit?.order_id || "").trim();
  const fromNotes = extractOrderIdsFromNotes(credit?.notes);
  const ids = primaryOrderId ? [primaryOrderId, ...fromNotes] : fromNotes;
  const uniqueIds = [...new Set(ids)];

  if (uniqueIds.length === 0) return null;

  return (
    <p style={{ margin: "6px 0 0", color: "#0f172a" }}>
      Pedido relacionado:{" "}
      {uniqueIds.map((orderId, index) => (
        <React.Fragment key={orderId}>
          {index > 0 ? " | " : ""}
          <Link to={`/meus-pedidos/${encodeURIComponent(orderId)}`}>Ver pedido</Link>
          {" "}
          <span style={{ color: "#64748b" }}>({orderId})</span>
        </React.Fragment>
      ))}
    </p>
  );
}

function creditAccentColor(status) {
  const palette = {
    AVAILABLE: "#22c55e",
    USED: "#3b82f6",
    EXPIRED: "#ef4444",
    REVOKED: "#94a3b8",
  };
  return palette[String(status || "").toUpperCase()] || "#cbd5e1";
}

function CreditSkeleton() {
  return (
    <SkeletonCard
      containerStyle={skeletonCardStyle}
      headerStyle={skeletonHeaderStyle}
      bodyStyle={skeletonBodyStyle}
      lineStyle={skeletonLineStyle}
      headerLeftStyle={skeletonLineShortStyle}
      headerRightStyle={skeletonBadgeStyle}
      lineCount={3}
    />
  );
}

export default function PublicMyCreditsPage() {
  const { token, user, loading: authLoading, isAuthenticated } = useAuth();
  const greeting = resolvePersonalGreeting(user);
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    let active = true;

    async function loadCredits() {
      if (authLoading) return;

      if (!token || !isAuthenticated) {
        if (!active) return;
        setPayload(null);
        setError("");
        setLoading(false);
        return;
      }

      try {
        if (active) {
          setLoading(true);
          setError("");
        }

        const data = await fetchMyCredits(token);
        if (!active) return;
        setPayload(data || null);
      } catch (err) {
        if (!active) return;
        setPayload(null);
        setError(err?.message || "Não foi possível carregar seus créditos.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadCredits();
    return () => {
      active = false;
    };
  }, [authLoading, isAuthenticated, token]);

  useEffect(() => {
    let active = true;

    async function silentRefetch() {
      if (document.visibilityState !== "visible") return;
      if (authLoading || !token || !isAuthenticated) return;

      try {
        const data = await fetchMyCredits(token);
        if (!active) return;
        setPayload(data || null);
      } catch {
        if (!active) return;
      }
    }

    function onVisibleOrFocus() {
      void silentRefetch();
    }

    document.addEventListener("visibilitychange", onVisibleOrFocus);
    window.addEventListener("focus", onVisibleOrFocus);
    return () => {
      active = false;
      document.removeEventListener("visibilitychange", onVisibleOrFocus);
      window.removeEventListener("focus", onVisibleOrFocus);
    };
  }, [authLoading, isAuthenticated, token]);

  const summary = payload?.summary || {
    available_balance_cents: 0,
    available_count: 0,
    expiring_soon_count: 0,
    currency: "BRL",
  };
  const items = Array.isArray(payload?.items) ? payload.items : [];

  const filteredItems = useMemo(() => {
    if (statusFilter === "ALL") return items;
    return items.filter((item) => item.status === statusFilter);
  }, [items, statusFilter]);

  const statusCounts = useMemo(() => {
    const counts = {
      ALL: items.length,
      AVAILABLE: 0,
      USED: 0,
      EXPIRED: 0,
      REVOKED: 0,
    };
    for (const item of items) {
      const key = String(item?.status || "").toUpperCase();
      if (counts[key] != null) counts[key] += 1;
    }
    return counts;
  }, [items]);

  const statusOptions = [
    { key: "ALL", label: "Todos" },
    { key: "AVAILABLE", label: "Disponíveis" },
    { key: "USED", label: "Usados" },
    { key: "EXPIRED", label: "Expirados" },
    { key: "REVOKED", label: "Revogados" },
  ];

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <PageHeader
          title="Meus Créditos"
          subtitle={`${greeting}Acompanhe saldo, validade e histórico dos créditos recebidos.`}
          ctaTo="/comprar"
          ctaLabel="✨ Novo Pedido"
          headerStyle={pageHeaderStyle}
          titleStyle={titleStyle}
          subtitleStyle={subtitleStyle}
          ctaStyle={newOrderButtonStyle}
        />

        {!authLoading && !loading ? (
          <SummaryMetrics
            sectionAriaLabel="Resumo dos créditos"
            sectionStyle={summaryBarStyle}
            cardStyle={summaryCardStyle}
            labelStyle={mutedStyle}
            valueStyle={valueStyle}
            items={[
              {
                key: "available_balance",
                label: "Saldo disponível",
                value: formatMoney(summary.available_balance_cents, summary.currency || "BRL"),
              },
              { key: "available_count", label: "Créditos disponíveis", value: summary.available_count },
              { key: "expiring_soon", label: "Próximos de vencer (7 dias)", value: summary.expiring_soon_count },
            ]}
          />
        ) : null}

        {!authLoading && !loading && !error ? (
          <section style={filterContainerStyle}>
            <div style={filterLeftStyle}>
              <span style={filterIconStyle}>🔍</span>
              <label htmlFor="credit-status-filter" style={filterLabelStyle}>
                Filtrar status:
              </label>
              <select
                id="credit-status-filter"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                style={filterSelectStyle}
              >
                <option value="ALL">Todos</option>
                <option value="AVAILABLE">Disponível</option>
                <option value="USED">Usado</option>
                <option value="EXPIRED">Expirado</option>
                <option value="REVOKED">Revogado</option>
              </select>
            </div>
            <StatusChips
              options={statusOptions}
              activeKey={statusFilter}
              counts={statusCounts}
              onSelect={setStatusFilter}
              wrapStyle={chipsWrapStyle}
              chipStyle={statusChipStyle}
              activeChipStyle={statusChipActiveStyle}
            />
          </section>
        ) : null}

        {(authLoading || loading) ? (
          <div style={skeletonListStyle}>
            {[1, 2, 3].map((entry) => (
              <CreditSkeleton key={entry} />
            ))}
          </div>
        ) : null}

        {!authLoading && !loading && error ? (
          <ErrorCard
            title="Falha ao carregar créditos"
            message={error}
            icon="⚠️"
            containerStyle={errorCardStyle}
            iconStyle={errorIconStyle}
            textStyle={errorTextStyle}
          />
        ) : null}

        {!authLoading && !loading && !error && filteredItems.length === 0 ? (
          <EmptyStateBlock
            title="Nenhum crédito encontrado"
            description="Não encontramos créditos para o filtro selecionado."
            icon="💳"
            ctaTo="/comprar"
            ctaLabel="🛒 Ir para catálogo"
            containerStyle={emptyStateStyle}
            iconStyle={emptyStateIconStyle}
            titleStyle={emptyStateTitleStyle}
            descriptionStyle={emptyStateTextStyle}
            buttonStyle={emptyStateButtonStyle}
          />
        ) : null}

        {!authLoading && !loading && !error && filteredItems.length > 0 ? (
          <div style={listWrapperStyle}>
            {filteredItems.map((credit) => (
              <article
                key={credit.id}
                style={{
                  ...creditCardStyle,
                  borderLeft: `5px solid ${creditAccentColor(credit.status)}`,
                }}
              >
                <div style={creditCardHeaderStyle}>
                  <strong style={creditAmountStyle}>
                    {formatMoney(credit.amount_cents, summary.currency || "BRL")}
                  </strong>
                  <span style={badgeStyle(credit.status)}>{statusLabel(credit.status)}</span>
                </div>
                <div style={creditMetaGridStyle}>
                  <p style={creditInfoStyle}>
                    <span style={creditInfoLabelStyle}>Origem</span>
                    <span>{credit.source_type || "—"} / {credit.source_reason || "—"}</span>
                  </p>
                  <p style={creditInfoStyle}>
                    <span style={creditInfoLabelStyle}>Validade</span>
                    <span>
                      {formatDate(credit.expires_at)}
                      {typeof credit.days_to_expiration === "number" && credit.status === "AVAILABLE"
                        ? ` (${credit.days_to_expiration} dia(s))`
                        : ""}
                    </span>
                  </p>
                </div>
                {renderCreditOrderLinks(credit)}
                {credit.notes ? (
                  <p style={creditNotesStyle}>{renderCreditNotes(credit.notes)}</p>
                ) : null}
              </article>
            ))}
          </div>
        ) : null}
      </div>
    </main>
  );
}

const summaryBarStyle = {
  display: "grid",
  gap: 12,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  marginBottom: 16,
};

const summaryCardStyle = {
  ...sectionCardBaseStyle,
  padding: 16,
};

const mutedStyle = {
  color: "#64748b",
  display: "block",
  marginBottom: 6,
};

const valueStyle = {
  fontSize: 24,
  fontWeight: 700,
  color: "#0f172a",
};

const filterContainerStyle = {
  ...filterCardBaseStyle,
  display: "grid",
  gap: 12,
  marginBottom: 16,
};

const filterLabelStyle = {
  color: "#334155",
  fontWeight: 600,
  fontSize: 14,
};

const listWrapperStyle = {
  display: "grid",
  gap: 12,
};

const creditCardStyle = {
  ...elevatedCardBaseStyle,
  padding: 16,
};

const creditCardHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 8,
  flexWrap: "wrap",
  marginBottom: 10,
};

const creditAmountStyle = {
  fontSize: 20,
  color: "#0f172a",
};

const creditMetaGridStyle = {
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
};

const creditInfoStyle = {
  margin: 0,
  color: "#334155",
  display: "grid",
  gap: 4,
};

const creditInfoLabelStyle = {
  fontSize: 12,
  color: "#64748b",
  fontWeight: 600,
};

const creditNotesStyle = {
  margin: "8px 0 0",
  color: "#0f172a",
};

const errorCardStyle = {
  ...errorCardBaseStyle,
};

const errorIconStyle = {
  ...errorIconBaseStyle,
};

const errorTextStyle = {
  ...errorTextBaseStyle,
};

const badgeStyle = (status) => {
  const palette = {
    AVAILABLE: { bg: "#dcfce7", fg: "#166534" },
    USED: { bg: "#dbeafe", fg: "#1d4ed8" },
    EXPIRED: { bg: "#fee2e2", fg: "#991b1b" },
    REVOKED: { bg: "#f1f5f9", fg: "#334155" },
  };
  const selected = palette[status] || palette.REVOKED;
  return {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 700,
    background: selected.bg,
    color: selected.fg,
  };
};
