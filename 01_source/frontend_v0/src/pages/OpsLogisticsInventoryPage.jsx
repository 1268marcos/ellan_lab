
import React, { useCallback, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#0f172a", border: "1px solid #334155", borderRadius: 12, padding: 16, marginBottom: 16 };
const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 13 };
const thtd = { borderBottom: "1px solid #334155", padding: "8px 6px", textAlign: "left" };
const inputStyle = { marginRight: 8, marginBottom: 8, padding: "6px 8px", borderRadius: 6, border: "1px solid #475569", background: "#1e293b", color: "#e2e8f0" };
const btnStyle = { padding: "8px 14px", borderRadius: 8, border: "none", background: "#2563eb", color: "#fff", cursor: "pointer" };
const tabBtn = (active) => ({
  ...btnStyle,
  marginRight: 8,
  background: active ? "#1d4ed8" : "#334155",
});

async function readJson(response) {
  return response.json().catch(() => ({}));
}

export default function OpsLogisticsInventoryPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);
  const [tab, setTab] = useState("stock");

  const [threshold, setThreshold] = useState(5);
  const [lockerFilter, setLockerFilter] = useState("");
  const [productFilter, setProductFilter] = useState("");
  const [lowStock, setLowStock] = useState(null);
  const [lockerIdView, setLockerIdView] = useState("");
  const [lockerRows, setLockerRows] = useState(null);

  const [resStatus, setResStatus] = useState("");
  const [resLocker, setResLocker] = useState("");
  const [reservations, setReservations] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchLowStock = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams();
      q.set("threshold", String(threshold));
      q.set("limit", "100");
      q.set("offset", "0");
      if (lockerFilter.trim()) q.set("locker_id", lockerFilter.trim());
      if (productFilter.trim()) q.set("product_id", productFilter.trim());
      const url = `${ORDER_PICKUP_BASE}/ops/inventory/low-stock?${q}`;
      const res = await fetch(url, { headers: { Accept: "application/json", ...authHeaders } });
      const data = await readJson(res);
      if (!res.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar low-stock.");
      setLowStock(data);
    } catch (e) {
      setError(String(e.message || e));
      setLowStock(null);
    } finally {
      setLoading(false);
    }
  }, [authHeaders, lockerFilter, productFilter, threshold, token]);

  const fetchLockerInventory = useCallback(async () => {
    if (!token || !lockerIdView.trim()) {
      setError("Informe locker_id para consulta por armário.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const id = encodeURIComponent(lockerIdView.trim());
      const url = `${ORDER_PICKUP_BASE}/inventory/${id}?limit=100&offset=0`;
      const res = await fetch(url, { headers: { Accept: "application/json", ...authHeaders } });
      const data = await readJson(res);
      if (!res.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar inventário do locker.");
      setLockerRows(data);
    } catch (e) {
      setError(String(e.message || e));
      setLockerRows(null);
    } finally {
      setLoading(false);
    }
  }, [authHeaders, lockerIdView, token]);

  const fetchReservations = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams({ limit: "100", offset: "0" });
      if (resStatus.trim()) q.set("status", resStatus.trim());
      if (resLocker.trim()) q.set("locker_id", resLocker.trim());
      const url = `${ORDER_PICKUP_BASE}/ops/inventory/reservations?${q}`;
      const res = await fetch(url, { headers: { Accept: "application/json", ...authHeaders } });
      const data = await readJson(res);
      if (!res.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar reservas.");
      setReservations(data);
    } catch (e) {
      setError(String(e.message || e));
      setReservations(null);
    } finally {
      setLoading(false);
    }
  }, [authHeaders, resLocker, resStatus, token]);

  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader title="OPS — Logística / Inventário" />
      <p style={{ color: "#94a3b8", marginTop: 0 }}>
        Dados de <code style={{ color: "#cbd5e1" }}>product_inventory</code> e{" "}
        <code style={{ color: "#cbd5e1" }}>inventory_reservations</code> via{" "}
        <code style={{ color: "#cbd5e1" }}>{ORDER_PICKUP_BASE}</code> (order_pickup).
      </p>
      <div style={{ marginBottom: 16 }}>
        <button type="button" style={tabBtn(tab === "stock")} onClick={() => setTab("stock")}>
          Estoque (SKU / locker)
        </button>
        <button type="button" style={tabBtn(tab === "res")} onClick={() => setTab("res")}>
          Reservas
        </button>
      </div>
      {error ? <div style={{ color: "#f87171", marginBottom: 12 }}>{error}</div> : null}

      {tab === "stock" ? (
        <>
          <section style={cardStyle}>
            <h2 style={{ marginTop: 0, fontSize: 16 }}>Low stock (quantity_on_hand / reserved / available)</h2>
            <div>
              <input style={inputStyle} type="number" min={0} value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} title="threshold" />
              <input style={inputStyle} placeholder="locker_id (opcional)" value={lockerFilter} onChange={(e) => setLockerFilter(e.target.value)} />
              <input style={inputStyle} placeholder="product_id (opcional)" value={productFilter} onChange={(e) => setProductFilter(e.target.value)} />
              <button type="button" style={btnStyle} disabled={loading || !token} onClick={() => void fetchLowStock()}>
                {loading ? "…" : "Consultar"}
              </button>
            </div>
            {lowStock?.items?.length ? (
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["product_id", "locker_id", "slot", "on_hand", "reserved", "available", "updated_at"].map((h) => (
                      <th key={h} style={thtd}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {lowStock.items.map((row) => (
                    <tr key={row.id}>
                      <td style={thtd}>{row.product_id}</td>
                      <td style={thtd}>{row.locker_id}</td>
                      <td style={thtd}>{row.slot_size}</td>
                      <td style={thtd}>{row.quantity_on_hand}</td>
                      <td style={thtd}>{row.quantity_reserved}</td>
                      <td style={thtd}>{row.quantity_available}</td>
                      <td style={thtd}>{row.updated_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : lowStock ? (
              <p style={{ color: "#94a3b8" }}>Nenhum registro (total={lowStock.total}).</p>
            ) : null}
          </section>
          <section style={cardStyle}>
            <h2 style={{ marginTop: 0, fontSize: 16 }}>Inventário completo por locker</h2>
            <input style={{ ...inputStyle, width: 280 }} placeholder="locker_id" value={lockerIdView} onChange={(e) => setLockerIdView(e.target.value)} />
            <button type="button" style={btnStyle} disabled={loading || !token} onClick={() => void fetchLockerInventory()}>
              Carregar locker
            </button>
            {lockerRows?.items?.length ? (
              <table style={{ ...tableStyle, marginTop: 12 }}>
                <thead>
                  <tr>
                    {["product_id", "slot", "on_hand", "reserved", "available"].map((h) => (
                      <th key={h} style={thtd}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {lockerRows.items.map((row) => (
                    <tr key={row.id}>
                      <td style={thtd}>{row.product_id}</td>
                      <td style={thtd}>{row.slot_size}</td>
                      <td style={thtd}>{row.quantity_on_hand}</td>
                      <td style={thtd}>{row.quantity_reserved}</td>
                      <td style={thtd}>{row.quantity_available}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </section>
        </>
      ) : (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0, fontSize: 16 }}>Reservas (status, expires_at)</h2>
          <div>
            <input style={inputStyle} placeholder="status (ex: ACTIVE)" value={resStatus} onChange={(e) => setResStatus(e.target.value)} />
            <input style={inputStyle} placeholder="locker_id (opcional)" value={resLocker} onChange={(e) => setResLocker(e.target.value)} />
            <button type="button" style={btnStyle} disabled={loading || !token} onClick={() => void fetchReservations()}>
              {loading ? "…" : "Listar"}
            </button>
          </div>
          {reservations?.items?.length ? (
            <table style={{ ...tableStyle, marginTop: 12 }}>
              <thead>
                <tr>
                  {["order_id", "product_id", "locker_id", "qty", "status", "expires_at", "updated_at"].map((h) => (
                    <th key={h} style={thtd}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {reservations.items.map((row) => (
                  <tr key={row.id}>
                    <td style={thtd}>{row.order_id}</td>
                    <td style={thtd}>{row.product_id}</td>
                    <td style={thtd}>{row.locker_id}</td>
                    <td style={thtd}>{row.quantity}</td>
                    <td style={thtd}>{row.status}</td>
                    <td style={thtd}>{row.expires_at}</td>
                    <td style={thtd}>{row.updated_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : reservations ? (
            <p style={{ color: "#94a3b8" }}>Nenhuma reserva (total={reservations.total}).</p>
          ) : null}
        </section>
      )}
    </div>
  );
}

