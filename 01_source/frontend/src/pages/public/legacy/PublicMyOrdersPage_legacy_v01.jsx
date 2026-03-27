import React, { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import PublicHeader from "../../components/public/PublicHeader";
import { useAuth } from "../../context/AuthContext";
import { fetchMyOrders } from "../../services/publicApi";

export default function PublicMyOrdersPage() {
  const { token, isAuthenticated } = useAuth();
  const [data, setData] = useState({ items: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function run() {
      try {
        const result = await fetchMyOrders(token);
        setData(result);
      } catch (err) {
        setError(err.message || "Falha ao carregar pedidos");
      } finally {
        setLoading(false);
      }
    }

    if (token) run();
  }, [token]);

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <div>
      <PublicHeader />
      <main style={{ maxWidth: 960, margin: "24px auto" }}>
        <h1>Meus pedidos</h1>

        {loading ? <p>Carregando...</p> : null}
        {error ? <p style={{ color: "red" }}>{error}</p> : null}

        {!loading && !error && data.items?.length === 0 ? <p>Nenhum pedido encontrado.</p> : null}

        <div style={{ display: "grid", gap: 12 }}>
          {data.items?.map((item) => (
            <div key={item.id} style={{ border: "1px solid #ddd", padding: 16 }}>
              <div><strong>Pedido:</strong> {item.id}</div>
              <div><strong>Status:</strong> {item.status}</div>
              <div><strong>Produto:</strong> {item.sku_id}</div>
              <div><strong>Locker:</strong> {item.totem_id}</div>
              <div><strong>Valor:</strong> {item.amount_cents}</div>
              <Link to={`/meus-pedidos/${item.id}`}>Ver detalhe</Link>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}