// 01_source/frontend/src/pages/public/PublicCatalogPage.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API_SP = "http://localhost:8201";
const API_PT = "http://localhost:8202";

export default function PublicCatalogPage() {
  const navigate = useNavigate();

  const [region, setRegion] = useState("SP");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const API = region === "SP" ? API_SP : API_PT;

  useEffect(() => {
    loadCatalog();
  }, [region]);

  const loadCatalog = async () => {
    setLoading(true);

    try {
      const res = await fetch(`${API}/catalog/slots`);
      const data = await res.json();

      // 🔥 SÓ slots vendáveis
      const valid = data.filter(
        (i) => i.sku_id && i.is_active && i.amount_cents > 0
      );

      setItems(valid);
    } catch (err) {
      console.error(err);
      alert("Erro ao carregar catálogo");
    } finally {
      setLoading(false);
    }
  };

  const handleBuy = async (item) => {
    try {
      const res = await fetch("http://localhost:8003/orders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          region,
          // 🔥 aqui está a mudança conceitual
          slot: item.slot,
          locker_id: item.locker_id,

          items: [
            {
              sku_id: item.sku_id,
              quantity: 1,
              unit_price_cents: item.amount_cents,
            },
          ],
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        alert("Erro ao criar pedido");
        return;
      }

      navigate(`/checkout?order_id=${data.order_id}`);
    } catch (err) {
      console.error(err);
      alert("Erro de conexão");
    }
  };

  return (
    <main style={{ padding: 24 }}>
      <h1>Escolha seu produto no locker</h1>

      <select value={region} onChange={(e) => setRegion(e.target.value)}>
        <option value="SP">São Paulo</option>
        <option value="PT">Portugal</option>
      </select>

      {loading && <p>Carregando...</p>}

      <div style={{ display: "grid", gap: 12, marginTop: 16 }}>
        {items.map((item) => (
          <div
            key={`${item.locker_id}-${item.slot}`}
            style={{
              border: "1px solid #ccc",
              padding: 16,
              borderRadius: 12,
            }}
          >
            <h3>{item.name}</h3>

            <p>
              {(item.amount_cents / 100).toFixed(2)} {item.currency}
            </p>

            <p>
              Locker: <b>{item.locker_id}</b> | Slot: <b>{item.slot}</b>
            </p>

            <button onClick={() => handleBuy(item)}>
              Comprar este slot
            </button>
          </div>
        ))}
      </div>
    </main>
  );
}