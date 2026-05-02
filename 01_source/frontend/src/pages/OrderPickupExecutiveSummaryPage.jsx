import React, { useCallback, useEffect, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { olFetch } from "../utils/orderLifecycleInternalApi";

export default function OrderPickupExecutiveSummaryPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const q = new URLSearchParams();
      const j = await olFetch(`/internal/analytics/pickup-executive-summary?${q.toString()}`);
      setData(j);
    } catch (e) {
      setErr(e?.message || String(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div style={{ padding: 24, maxWidth: 1100 }}>
      <OpsPageTitleHeader title="Pickup — resumo executivo" subtitle="GET /internal/analytics/pickup-executive-summary" />
      <button type="button" onClick={load} disabled={loading} style={{ marginTop: 12 }}>
        {loading ? "Carregando…" : "Atualizar"}
      </button>
      {err ? <p style={{ color: "#f87171", marginTop: 12 }}>{err}</p> : null}
      {data ? (
        <pre style={{ marginTop: 16, fontSize: 12, overflow: "auto", background: "#111", color: "#e2e8f0", padding: 12 }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}
