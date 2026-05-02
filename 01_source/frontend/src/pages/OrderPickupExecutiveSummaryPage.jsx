import React, { useCallback, useEffect, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { getOrderLifecycleBase, olFetch } from "../utils/orderLifecycleInternalApi";

const PAGE_VERSION = "ops/order/executive-summary v0.1";

export default function OrderPickupExecutiveSummaryPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams();
      const j = await olFetch(`/internal/analytics/pickup-executive-summary?${q.toString()}`);
      setData(j);
    } catch (e) {
      setError(e?.message || "Falha ao carregar resumo executivo");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="ops-page" style={{ padding: "1rem", maxWidth: 1200 }}>
      <OpsPageTitleHeader title="OPS — Order / resumo executivo (pickup)" versionLabel={PAGE_VERSION} />
      <p style={{ opacity: 0.85, marginBottom: 12 }}>
        <code>GET /internal/analytics/pickup-executive-summary</code> no order lifecycle (
        <code>{getOrderLifecycleBase()}</code>). Token interno: <code>VITE_INTERNAL_TOKEN</code> (header{" "}
        <code>X-Internal-Token</code>).
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <button type="button" onClick={load} disabled={loading}>
          {loading ? "Carregando…" : "Atualizar"}
        </button>
      </div>
      {error ? <p style={{ color: "#f87171" }}>{error}</p> : null}
      {data && !error ? (
        <div style={{ overflow: "auto", maxHeight: "70vh", border: "1px solid #333", borderRadius: 4 }}>
          <pre
            style={{
              margin: 0,
              padding: 12,
              fontSize: 12,
              fontFamily: "ui-monospace, monospace",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
