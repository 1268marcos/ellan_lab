import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { fetchMyOrders } from "../../services/publicApi";

export default function PublicMyOrdersPage() {
  const { token, loading, isAuthenticated } = useAuth();

  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [pageLoading, setPageLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      if (loading) {
        return;
      }

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
  }, [token, loading, isAuthenticated]);

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <div style={headerBlockStyle}>
          <h1 style={titleStyle}>Meus pedidos</h1>
          <p style={subtitleStyle}>
            Acompanhe aqui os seus pedidos realizados no fluxo público.
          </p>
        </div>

        {loading || pageLoading ? (
          <div style={cardStyle}>
            <p style={mutedStyle}>Carregando pedidos...</p>
          </div>
        ) : null}

        {!loading && !pageLoading && error ? (
          <div style={errorCardStyle}>
            <strong>Não foi possível carregar seus pedidos.</strong>
            <p style={{ marginTop: 8, marginBottom: 0 }}>{error}</p>
          </div>
        ) : null}

        {!loading && !pageLoading && !error && items.length === 0 ? (
          <div style={cardStyle}>
            <p style={mutedStyle}>Nenhum pedido encontrado.</p>
            <div style={{ marginTop: 12 }}>
              <Link to="/comprar" style={primaryLinkStyle}>
                Ir para o catálogo
              </Link>
            </div>
          </div>
        ) : null}

        {!loading && !pageLoading && !error && items.length > 0 ? (
          <div style={listWrapperStyle}>
            {items.map((item) => (
              <Link
                key={item.id}
                to={`/meus-pedidos/${item.id}`}
                style={orderCardLinkStyle}
              >
                <article style={orderCardStyle}>
                  <div style={orderTopRowStyle}>
                    <strong style={orderIdStyle}>{item.id}</strong>
                    <span style={statusBadgeStyle}>{item.status || "—"}</span>
                  </div>

                  <div style={orderMetaStyle}>
                    <div>
                      <span style={metaLabelStyle}>SKU</span>
                      <div>{item.sku_id || "—"}</div>
                    </div>

                    {"region_code" in item ? (
                      <div>
                        <span style={metaLabelStyle}>Região</span>
                        <div>{item.region_code || "—"}</div>
                      </div>
                    ) : null}

                    {"created_at" in item ? (
                      <div>
                        <span style={metaLabelStyle}>Criado em</span>
                        <div>{formatDateTime(item.created_at)}</div>
                      </div>
                    ) : null}
                  </div>
                </article>
              </Link>
            ))}
          </div>
        ) : null}
      </div>
    </main>
  );
}

function formatDateTime(value) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

const pageStyle = {
  padding: 24,
};

const containerStyle = {
  maxWidth: 960,
  margin: "0 auto",
};

const headerBlockStyle = {
  marginBottom: 20,
};

const titleStyle = {
  margin: 0,
  fontSize: 28,
};

const subtitleStyle = {
  marginTop: 8,
  marginBottom: 0,
  color: "#555",
};

const cardStyle = {
  padding: 16,
  borderRadius: 14,
  border: "1px solid #e5e7eb",
  background: "#fff",
};

const errorCardStyle = {
  padding: 16,
  borderRadius: 14,
  border: "1px solid #fecaca",
  background: "#fff1f2",
  color: "#991b1b",
};

const mutedStyle = {
  margin: 0,
  color: "#666",
};

const listWrapperStyle = {
  display: "grid",
  gap: 12,
};

const orderCardLinkStyle = {
  textDecoration: "none",
  color: "inherit",
};

const orderCardStyle = {
  padding: 16,
  borderRadius: 14,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.06)",
};

const orderTopRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  flexWrap: "wrap",
  marginBottom: 12,
};

const orderIdStyle = {
  fontSize: 16,
  wordBreak: "break-word",
};

const statusBadgeStyle = {
  padding: "6px 10px",
  borderRadius: 999,
  background: "#272626",
  border: "1px solid #e5e7eb",
  fontSize: 12,
  fontWeight: 600,
};

const orderMetaStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
  gap: 12,
};

const metaLabelStyle = {
  display: "block",
  fontSize: 12,
  color: "#666",
  marginBottom: 4,
};

const primaryLinkStyle = {
  display: "inline-block",
  padding: "10px 14px",
  borderRadius: 10,
  textDecoration: "none",
  border: "1px solid #d1d5db",
  background: "#f9fafb",
  color: "#111827",
  fontWeight: 600,
};