import React, { useEffect, useState } from "react";
import { fetchOrderPickup } from "../../services/publicApi";
import { useAuth } from "../../context/AuthContext";

export default function PickupPanel({ orderId }) {
  const { token } = useAuth();
  const [pickup, setPickup] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchOrderPickup(token, orderId);
        setPickup(data);
        setError("");
      } catch (err) {
        setPickup(null);
        setError(err.message || "pickup_not_available");
      }
    }

    if (token && orderId) {
      load();
    }
  }, [token, orderId]);

  if (!orderId) return <p>Nenhum pedido selecionado.</p>;
  if (error) return <p>{error}</p>;
  if (!pickup) return <p>Carregando pickup...</p>;

  return (
    <div style={{ border: "1px solid #ccc", padding: 16, marginTop: 16 }}>
      <h3>Retirada</h3>
      <p><strong>Status:</strong> {pickup.status}</p>
      <p><strong>Expira em:</strong> {pickup.expires_at || "-"}</p>
      <p><strong>Código manual:</strong> {pickup.manual_code_masked || "-"}</p>

      <div>
        <strong>QR payload</strong>
        <textarea
          readOnly
          value={pickup.qr_value || ""}
          style={{ width: "100%", minHeight: 120 }}
        />
      </div>
    </div>
  );
}