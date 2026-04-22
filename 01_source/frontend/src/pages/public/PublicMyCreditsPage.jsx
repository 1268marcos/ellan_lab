import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { fetchMyCredits } from "../../services/publicApi";

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

export default function PublicMyCreditsPage() {
  const { token, loading: authLoading, isAuthenticated } = useAuth();
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

  return (
    <main style={{ padding: 24, maxWidth: 980, margin: "0 auto" }}>
      <header style={{ marginBottom: 20 }}>
        <h1 style={{ margin: 0 }}>Meus Créditos</h1>
        <p style={{ marginTop: 8, color: "#475569" }}>
          Acompanhe seu saldo, validade e histórico de créditos.
        </p>
      </header>

      <section style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginBottom: 24 }}>
        <article style={cardStyle}>
          <small style={mutedStyle}>Saldo disponível</small>
          <div style={valueStyle}>
            {formatMoney(summary.available_balance_cents, summary.currency || "BRL")}
          </div>
        </article>
        <article style={cardStyle}>
          <small style={mutedStyle}>Créditos disponíveis</small>
          <div style={valueStyle}>{summary.available_count}</div>
        </article>
        <article style={cardStyle}>
          <small style={mutedStyle}>Próximos de vencer (7 dias)</small>
          <div style={valueStyle}>{summary.expiring_soon_count}</div>
        </article>
      </section>

      <div style={{ marginBottom: 16, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
        <label htmlFor="credit-status-filter">Filtrar status:</label>
        <select
          id="credit-status-filter"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
          style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #cbd5e1" }}
        >
          <option value="ALL">Todos</option>
          <option value="AVAILABLE">Disponível</option>
          <option value="USED">Usado</option>
          <option value="EXPIRED">Expirado</option>
          <option value="REVOKED">Revogado</option>
        </select>
      </div>

      {(authLoading || loading) && <p>Carregando créditos...</p>}

      {!authLoading && !loading && error ? (
        <div style={{ ...cardStyle, borderColor: "#fecaca", background: "#fff1f2" }}>
          <strong>Falha ao carregar créditos</strong>
          <p style={{ marginBottom: 0 }}>{error}</p>
        </div>
      ) : null}

      {!authLoading && !loading && !error && filteredItems.length === 0 ? (
        <div style={cardStyle}>
          <p style={{ marginTop: 0 }}>Nenhum crédito encontrado para o filtro selecionado.</p>
          <Link to="/comprar">Ir para catálogo</Link>
        </div>
      ) : null}

      {!authLoading && !loading && !error && filteredItems.length > 0 ? (
        <div style={{ display: "grid", gap: 12 }}>
          {filteredItems.map((credit) => (
            <article key={credit.id} style={cardStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                <strong>{formatMoney(credit.amount_cents, summary.currency || "BRL")}</strong>
                <span style={badgeStyle(credit.status)}>{statusLabel(credit.status)}</span>
              </div>
              <p style={{ margin: "8px 0 0", color: "#334155" }}>
                Origem: {credit.source_type || "—"} / {credit.source_reason || "—"}
              </p>
              <p style={{ margin: "6px 0 0", color: "#334155" }}>
                Validade: {formatDate(credit.expires_at)}
                {typeof credit.days_to_expiration === "number" && credit.status === "AVAILABLE"
                  ? ` (${credit.days_to_expiration} dia(s))`
                  : ""}
              </p>
              {credit.notes ? <p style={{ margin: "6px 0 0", color: "#0f172a" }}>{credit.notes}</p> : null}
            </article>
          ))}
        </div>
      ) : null}
    </main>
  );
}

const cardStyle = {
  border: "1px solid #e2e8f0",
  borderRadius: 12,
  background: "#ffffff",
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
