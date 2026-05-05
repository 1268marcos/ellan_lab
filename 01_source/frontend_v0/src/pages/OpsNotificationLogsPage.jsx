
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsActionButton from "../components/OpsActionButton";
import {
  actionsStyle,
  cardStyle,
  errorStyle,
  filtersStyle,
  inputStyle,
  labelStyle,
  metaLineStyle,
  mutedStyle,
  pageStyle,
  tableStyle,
  tableWrapStyle,
  tdStyle,
  thStyle,
  monoTdStyle,
} from "../utils/runtimeOpsPageChrome";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const PAGE_VERSION = "ops/notifications/logs v0.1";

async function readJson(res) {
  const text = await res.text();
  let body = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { detail: text || res.statusText };
  }
  if (!res.ok) {
    const msg =
      (typeof body?.detail === "string" && body.detail) ||
      body?.message ||
      res.statusText ||
      "Erro na requisição";
    throw new Error(msg);
  }
  return body;
}

export default function OpsNotificationLogsPage() {
  const { token } = useAuth();
  const [status, setStatus] = useState("");
  const [channel, setChannel] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [retryingId, setRetryingId] = useState(null);

  const authHeaders = useMemo(() => {
    const h = { Accept: "application/json" };
    if (token) h.Authorization = `Bearer ${token}`;
    return h;
  }, [token]);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams();
      if (status) q.set("status", status);
      if (channel) q.set("channel", channel);
      if (dateFrom) q.set("date_from", dateFrom);
      if (dateTo) q.set("date_to", dateTo);
      q.set("limit", "100");
      const res = await fetch(`${ORDER_PICKUP_BASE}/notifications/logs?${q}`, {
        headers: authHeaders,
      });
      const data = await readJson(res);
      setRows(Array.isArray(data?.items) ? data.items : []);
      setTotal(Number(data?.total) || 0);
    } catch (e) {
      setError(e?.message || String(e));
      setRows([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [authHeaders, status, channel, dateFrom, dateTo]);

  useEffect(() => {
    void load();
  }, [load]);

  const retry = async (id) => {
    setRetryingId(id);
    setError("");
    try {
      const res = await fetch(`${ORDER_PICKUP_BASE}/notifications/logs/${id}/retry`, {
        method: "POST",
        headers: authHeaders,
      });
      await readJson(res);
      await load();
    } catch (e) {
      setError(e?.message || String(e));
    } finally {
      setRetryingId(null);
    }
  };

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Notification logs" versionLabel={PAGE_VERSION} />
        <p style={mutedStyle}>
          Diagnóstico de envio a clientes. API: <code style={{ color: "#E2E8F0" }}>GET /notifications/logs</code>,{" "}
          <code style={{ color: "#E2E8F0" }}>POST /notifications/logs/&lt;id&gt;/retry</code> (order_pickup_service).
          Filtro <strong>PENDING</strong> inclui QUEUED e PROCESSING no banco; <strong>FAILED</strong> inclui DEAD.
        </p>
        <div style={filtersStyle}>
          <label style={labelStyle}>
            status
            <select value={status} onChange={(e) => setStatus(e.target.value)} style={inputStyle}>
              <option value="">(todos)</option>
              <option value="PENDING">PENDING</option>
              <option value="SENT">SENT</option>
              <option value="FAILED">FAILED</option>
            </select>
          </label>
          <label style={labelStyle}>
            canal
            <select value={channel} onChange={(e) => setChannel(e.target.value)} style={inputStyle}>
              <option value="">(todos)</option>
              <option value="EMAIL">EMAIL</option>
              <option value="SMS">SMS</option>
              <option value="PUSH">PUSH</option>
            </select>
          </label>
          <label style={labelStyle}>
            date_from
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            date_to
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} style={inputStyle} />
          </label>
        </div>
        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void load()} disabled={loading}>
            {loading ? "Carregando…" : "Aplicar filtros"}
          </OpsActionButton>
        </div>
        {error ? <div style={errorStyle}>{error}</div> : null}
        <p style={metaLineStyle}>total={total} exibindo até 100</p>
        <div style={tableWrapStyle}>
          <table style={tableStyle}>
            <thead>
              <tr>
                {[
                  "id",
                  "user_id",
                  "order_id",
                  "channel",
                  "template",
                  "status",
                  "tent.",
                  "erro",
                  "sent_at",
                  "deliv.",
                  "prov_msg",
                  "prov_st",
                  "ação",
                ].map((h) => (
                  <th key={h} style={thStyle}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td style={tdStyle}>{r.id}</td>
                  <td style={monoTdStyle}>{r.user_id || "—"}</td>
                  <td style={monoTdStyle}>{r.order_id || "—"}</td>
                  <td style={tdStyle}>{r.channel}</td>
                  <td style={tdStyle}>{r.template_key}</td>
                  <td style={tdStyle}>{r.status}</td>
                  <td style={tdStyle}>{r.attempt_count}</td>
                  <td style={monoTdStyle} title={r.error_message || ""}>
                    {(r.error_message || "").slice(0, 48)}
                    {(r.error_message || "").length > 48 ? "…" : ""}
                  </td>
                  <td style={monoTdStyle}>{r.sent_at || "—"}</td>
                  <td style={monoTdStyle}>{r.delivered_at || "—"}</td>
                  <td style={monoTdStyle}>{(r.provider_message_id || "").slice(0, 14) || "—"}</td>
                  <td style={tdStyle}>{r.provider_status || "—"}</td>
                  <td style={tdStyle}>
                    {r.status === "FAILED" ? (
                      <OpsActionButton
                        type="button"
                        variant="secondary"
                        disabled={retryingId === r.id}
                        onClick={() => void retry(r.id)}
                      >
                        {retryingId === r.id ? "…" : "Reenviar"}
                      </OpsActionButton>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

