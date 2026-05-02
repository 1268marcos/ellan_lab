import React, { useCallback, useEffect, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { fetchRuntimeJson } from "../utils/runtimeOpsApi";

export default function OpsRuntimeHealthPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await fetchRuntimeJson("/health"));
    } catch (e) {
      setError(e?.message || "Falha ao consultar runtime");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="ops-page" style={{ padding: "1rem", maxWidth: 960 }}>
      <OpsPageTitleHeader title="OPS — Runtime / health" versionLabel="ops/runtime/health v0.1" />
      <p style={{ opacity: 0.85, marginBottom: 12 }}>GET via proxy <code>/api/rt/health</code> (runtime :8200).</p>
      <button type="button" onClick={load} disabled={loading}>
        {loading ? "Atualizando…" : "Atualizar"}
      </button>
      {error ? <p style={{ color: "#f87171", marginTop: 12 }}>{error}</p> : null}
      {data ? (
        <pre style={{ marginTop: 16, overflow: "auto", fontSize: 13 }}>{JSON.stringify(data, null, 2)}</pre>
      ) : null}
    </div>
  );
}
