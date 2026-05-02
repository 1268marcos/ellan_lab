import React, { useCallback, useEffect, useState } from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsActionButton from "../components/OpsActionButton";
import RuntimeOpsSubnav from "../components/RuntimeOpsSubnav";
import { fetchRuntimeJson, formatRuntimeFetchError } from "../utils/runtimeOpsApi";
import {
  actionsStyle,
  cardStyle,
  errorStyle,
  metaLineStyle,
  mutedStyle,
  pageStyle,
  preJsonStyle,
} from "../utils/runtimeOpsPageChrome";

const PAGE_VERSION = "ops/runtime/health v0.2";

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
      setError(formatRuntimeFetchError(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Runtime / health" versionLabel={PAGE_VERSION} />
        <RuntimeOpsSubnav />
        <p style={mutedStyle}>
          <strong>GET</strong> <code style={{ color: "#E2E8F0" }}>/api/rt/health</code> — proxy Vite para{" "}
          <code>backend_runtime</code> (porta 8200).
        </p>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void load()} disabled={loading}>
            {loading ? "Atualizando…" : "Atualizar"}
          </OpsActionButton>
        </div>
        {error ? <div style={errorStyle}>{error}</div> : null}
        {data && !error ? (
          <p style={metaLineStyle}>
            ok={String(data.ok)} service={String(data.service || "—")}
          </p>
        ) : null}
        {data ? <pre style={preJsonStyle}>{JSON.stringify(data, null, 2)}</pre> : null}
      </section>
    </div>
  );
}
