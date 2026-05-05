
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsActionButton from "../components/OpsActionButton";
import RuntimeOpsSubnav from "../components/RuntimeOpsSubnav";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const PAGE_VERSION = "ops/runtime/sync v1.1";

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const muted = { color: "#94A3B8", marginTop: 8, fontSize: 13, lineHeight: 1.5 };
const toolbar = { display: "flex", flexWrap: "wrap", gap: 12, marginTop: 14, alignItems: "center" };
const tableWrap = { marginTop: 14, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const table = { width: "100%", borderCollapse: "collapse", minWidth: 520 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const td = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
const errBox = { marginTop: 12, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10, whiteSpace: "pre-wrap" };
const okBox = { marginTop: 12, background: "rgba(22,163,74,0.12)", color: "#BBF7D0", border: "1px solid rgba(34,197,94,0.35)", borderRadius: 10, padding: 10, whiteSpace: "pre-wrap" };
const codeInline = { color: "#CBD5E1", fontSize: 12 };

const metricCard = {
  background: "#0B1220",
  border: "1px solid #1E293B",
  borderRadius: 12,
  padding: "12px 14px",
  minWidth: 0,
};
const metricLabel = { fontSize: 11, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.04em" };
const metricValue = { fontSize: 18, fontWeight: 800, color: "#F8FAFC", marginTop: 6 };

function parseTs(s) {
  if (!s || s === "—") return NaN;
  const t = Date.parse(String(s));
  return Number.isFinite(t) ? t : NaN;
}

export default function OpsRuntimeSyncPage() {
  const { token, hasRole } = useAuth();
  const canWrite = hasRole("admin_operacao");
  const headers = useMemo(
    () => ({ Accept: "application/json", "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token]
  );
  const [statusPayload, setStatusPayload] = useState(null);
  const [divPayload, setDivPayload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [lastFetchMs, setLastFetchMs] = useState(null);
  const [lastFetchAt, setLastFetchAt] = useState(null);
  const [clock, setClock] = useState(0);
  const divsPositiveSinceRef = useRef(null);
  const pollSamplesRef = useRef([]);

  useEffect(() => {
    const id = setInterval(() => setClock((c) => c + 1), 15000);
    return () => clearInterval(id);
  }, []);

  const loadAll = useCallback(async () => {
    if (!token) return;
    const t0 = typeof performance !== "undefined" ? performance.now() : Date.now();
    setLoading(true);
    setErr("");
    setMsg("");
    try {
      const [s, d] = await Promise.all([
        fetch(`${BASE}/ops/runtime-sync/status`, { headers }),
        fetch(`${BASE}/ops/runtime-sync/divergences`, { headers }),
      ]);
      const sj = await s.json().catch(() => ({}));
      const dj = await d.json().catch(() => ({}));
      if (!s.ok) throw new Error(typeof sj?.detail?.message === "string" ? sj.detail.message : s.statusText);
      if (!d.ok) throw new Error(typeof dj?.detail?.message === "string" ? dj.detail.message : d.statusText);
      setStatusPayload(sj);
      setDivPayload(dj);
      const lastBy = Array.isArray(sj?.last_by_locker) ? sj.last_by_locker : [];
      const okC = lastBy.filter((r) => String(r.status || "").toUpperCase() === "SUCCESS").length;
      const failC = lastBy.filter((r) => String(r.status || "").toUpperCase() === "FAILED").length;
      const t1 = typeof performance !== "undefined" ? performance.now() : Date.now();
      setLastFetchMs(Math.round(t1 - t0));
      setLastFetchAt(Date.now());
      pollSamplesRef.current = [...pollSamplesRef.current, { t: Date.now(), ok: okC, err: failC }].slice(-480);
    } catch (e) {
      setErr(String(e.message || e));
      setStatusPayload(null);
      setDivPayload(null);
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const divByLocker = useMemo(() => {
    const m = new Map();
    const items = Array.isArray(divPayload?.items) ? divPayload.items : [];
    for (const it of items) {
      m.set(String(it.locker_id || ""), Number(it.divergences_count) || 0);
    }
    return m;
  }, [divPayload]);

  const totalDivergences = useMemo(() => {
    let n = 0;
    divByLocker.forEach((v) => {
      if (typeof v === "number" && v > 0) n += v;
    });
    return n;
  }, [divByLocker]);

  useEffect(() => {
    if (totalDivergences > 0) {
      if (divsPositiveSinceRef.current == null) divsPositiveSinceRef.current = Date.now();
    } else {
      divsPositiveSinceRef.current = null;
    }
  }, [totalDivergences]);

  const divergencesRedAlert = useMemo(() => {
    if (totalDivergences <= 0 || divsPositiveSinceRef.current == null) return false;
    return Date.now() - divsPositiveSinceRef.current > 5 * 60 * 1000;
  }, [totalDivergences, lastFetchAt, clock]);

  const rows = useMemo(() => {
    const last = Array.isArray(statusPayload?.last_by_locker) ? statusPayload.last_by_locker : [];
    const lastMap = new Map(last.map((r) => [String(r.locker_id || ""), r]));
    const ids = new Set([...lastMap.keys(), ...divByLocker.keys()]);
    return [...ids]
      .sort()
      .map((lid) => {
        const r = lastMap.get(lid);
        const dc = divByLocker.has(lid) ? divByLocker.get(lid) : "—";
        return {
          locker_id: lid,
          last_sync_at: r?.processed_at || r?.created_at || "—",
          status: r ? String(r.status || "—") : "—",
          divergences_count: dc,
        };
      });
  }, [statusPayload, divByLocker]);

  const pending = Array.isArray(statusPayload?.pending) ? statusPayload.pending : [];

  const latestGlobal = useMemo(() => {
    const last = Array.isArray(statusPayload?.last_by_locker) ? statusPayload.last_by_locker : [];
    let best = null;
    let bestTs = -1;
    for (const r of last) {
      const ts = parseTs(r.processed_at || r.created_at);
      if (Number.isFinite(ts) && ts >= bestTs) {
        bestTs = ts;
        best = r;
      }
    }
    return best;
  }, [statusPayload]);

  const lastSyncLabel = latestGlobal?.processed_at || latestGlobal?.created_at || "—";
  const lastSyncFailed = String(latestGlobal?.status || "").toUpperCase() === "FAILED";

  const successRate1h = useMemo(() => {
    const last = Array.isArray(statusPayload?.last_by_locker) ? statusPayload.last_by_locker : [];
    const cutoff = Date.now() - 60 * 60 * 1000;
    let ok = 0;
    let bad = 0;
    for (const r of last) {
      const ts = parseTs(r.processed_at || r.created_at);
      if (!Number.isFinite(ts) || ts < cutoff) continue;
      const st = String(r.status || "").toUpperCase();
      if (st === "SUCCESS") ok += 1;
      else if (st === "FAILED") bad += 1;
    }
    const tot = ok + bad;
    if (!tot) return null;
    return Math.round((100 * ok) / tot);
  }, [statusPayload]);

  const hourlyBars = useMemo(() => {
    const now = Date.now();
    const buckets = Array.from({ length: 24 }, (_, i) => {
      const hourEnd = now - (23 - i) * 3600000;
      const hourStart = hourEnd - 3600000;
      let ok = 0;
      let err = 0;
      for (const s of pollSamplesRef.current) {
        if (s.t < hourStart || s.t > hourEnd) continue;
        ok += s.ok;
        err += s.err;
      }
      return { ok, err, label: `${i}` };
    });
    const max = Math.max(1, ...buckets.map((b) => b.ok + b.err));
    return buckets.map((b) => ({ ...b, hOk: (b.ok / max) * 48, hErr: (b.err / max) * 48 }));
  }, [lastFetchAt, clock]);

  const perLockerDivLines = useMemo(() => {
    const lines = [];
    divByLocker.forEach((v, lid) => {
      if (typeof v === "number" && v > 0) lines.push(`${lid}: ${v}`);
    });
    return lines.slice(0, 12);
  }, [divByLocker]);

  const syncOne = async (lockerId) => {
    if (!token || !canWrite) return;
    setErr("");
    setMsg("");
    try {
      const path = encodeURIComponent(lockerId);
      const r = await fetch(`${BASE}/ops/runtime-sync/run/${path}`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail?.message === "string" ? j.detail.message : JSON.stringify(j.detail || j));
      setMsg(`Sync OK: ${lockerId} — updated_rows=${j.updated_rows ?? 0}`);
      await loadAll();
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const reconcileAll = async () => {
    if (!token || !canWrite) return;
    setErr("");
    setMsg("");
    try {
      const r = await fetch(`${BASE}/ops/runtime-sync/reconcile-all`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail?.message === "string" ? j.detail.message : JSON.stringify(j.detail || j));
      setMsg(`Reconcile-all: success=${j.success ?? 0} failed=${j.failed ?? 0}`);
      await loadAll();
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const wrapStyle = divergencesRedAlert
    ? { ...pageStyle, background: "rgba(127,29,29,0.22)", borderRadius: 16, padding: 12, boxSizing: "border-box" }
    : pageStyle;

  return (
    <div style={wrapStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Runtime / sync (Postgres)" versionLabel={PAGE_VERSION} />
        <RuntimeOpsSubnav />
        <p style={muted}>
          Reconcilia <code style={codeInline}>public.locker_slots</code> com{" "}
          <code style={codeInline}>GET /locker/slots</code> do runtime regional. Worker em background (intervalo padrão 30s,
          configurável via <code style={codeInline}>RUNTIME_SLOT_SYNC_POLL_SEC</code> no backend). Role de escrita:{" "}
          <code style={codeInline}>admin_operacao</code>.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 10,
            marginTop: 14,
          }}
        >
          <div style={metricCard}>
            <div style={metricLabel}>Última sincronização (fila)</div>
            <div style={metricValue}>
              {lastSyncFailed ? <span title="Último registro FAILED">⚠ </span> : null}
              {lastSyncLabel}
            </div>
            <div style={{ ...muted, marginTop: 4, fontSize: 11 }}>
              Duração refresh API: {lastFetchMs != null ? `${lastFetchMs} ms` : "—"}
            </div>
          </div>
          <div style={metricCard}>
            <div style={metricLabel}>Divergências ativas</div>
            <div style={metricValue}>{totalDivergences}</div>
            <pre style={{ ...muted, marginTop: 4, fontSize: 10, whiteSpace: "pre-wrap", maxHeight: 64, overflow: "hidden" }}>
              {perLockerDivLines.length ? perLockerDivLines.join("\n") : "—"}
            </pre>
          </div>
          <div style={metricCard}>
            <div style={{ ...metricLabel, display: "flex", alignItems: "center", gap: 8 }}>
              Fila pendente
              {pending.length > 10 ? (
                <span
                  style={{
                    background: "rgba(234,88,12,0.35)",
                    color: "#FFEDD5",
                    fontSize: 10,
                    fontWeight: 800,
                    padding: "2px 8px",
                    borderRadius: 999,
                    border: "1px solid rgba(251,146,60,0.6)",
                  }}
                >
                  {pending.length}
                </span>
              ) : null}
            </div>
            <div style={metricValue}>{pending.length}</div>
            <div style={{ ...muted, marginTop: 4, fontSize: 11 }}>PENDING + PROCESSING</div>
          </div>
          <div style={metricCard}>
            <div style={metricLabel}>Taxa sucesso (1h, fila)</div>
            <div style={metricValue}>{successRate1h != null ? `${successRate1h}%` : "—"}</div>
            <div style={{ ...muted, marginTop: 4, fontSize: 11 }}>Por locker com processed_at na última hora</div>
          </div>
        </div>

        {divergencesRedAlert ? (
          <div style={{ ...errBox, marginTop: 12 }}>Divergências &gt; 0 há mais de 5 minutos — verificar runtime vs Postgres.</div>
        ) : null}

        <div style={{ marginTop: 16 }}>
          <div style={{ ...metricLabel, marginBottom: 6 }}>Amostras por hora (24h, agregado dos refreshes deste painel)</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 56, padding: "4px 0" }}>
            {hourlyBars.map((b, i) => (
              <div key={i} title={`ok=${b.ok} err=${b.err}`} style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: 1 }}>
                <div style={{ height: b.hErr, background: "rgba(239,68,68,0.75)", borderRadius: 2 }} />
                <div style={{ height: b.hOk, background: "rgba(34,197,94,0.75)", borderRadius: 2 }} />
              </div>
            ))}
          </div>
        </div>

        <div style={toolbar}>
          <OpsActionButton type="button" variant="secondary" onClick={() => void loadAll()} disabled={loading || !token}>
            {loading ? "Carregando…" : "Atualizar painel"}
          </OpsActionButton>
          {canWrite ? (
            <OpsActionButton type="button" variant="primary" onClick={() => void reconcileAll()} disabled={loading || !token}>
              Reconciliar todos
            </OpsActionButton>
          ) : null}
        </div>
        {!token ? <p style={muted}>Faça login (OPS) para ver o painel.</p> : null}
        {err ? <div style={errBox}>{err}</div> : null}
        {msg ? <div style={okBox}>{msg}</div> : null}

        <h3 style={{ fontSize: 14, color: "#BFDBFE", marginTop: 20 }}>Lockers — última sync registrada</h3>
        <div style={tableWrap}>
          <table style={table}>
            <thead>
              <tr>
                {["locker_id", "last_sync_at", "divergences_count", "status", "ações"].map((h) => (
                  <th key={h} style={th}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ ...td, color: "#94A3B8" }}>
                    Nenhum registro em <code style={codeInline}>runtime_sync_queue</code> ainda — rode um sync manual ou aguarde o worker.
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.locker_id}>
                    <td style={td}>
                      <code style={codeInline}>{row.locker_id}</code>
                    </td>
                    <td style={td}>{row.last_sync_at}</td>
                    <td style={td}>{row.divergences_count}</td>
                    <td style={td}>
                      {String(row.status || "").toUpperCase() === "FAILED" ? <span title="Falhou">⚠ </span> : null}
                      {row.status}
                    </td>
                    <td style={td}>
                      {canWrite ? (
                        <OpsActionButton type="button" variant="secondary" onClick={() => void syncOne(row.locker_id)} disabled={loading}>
                          Sync agora
                        </OpsActionButton>
                      ) : (
                        <span style={{ color: "#64748B", fontSize: 11 }}>somente leitura</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <h3 style={{ fontSize: 14, color: "#BFDBFE", marginTop: 24 }}>
          Fila pendente (PENDING / PROCESSING)
          {pending.length > 10 ? (
            <span
              style={{
                marginLeft: 10,
                background: "rgba(234,88,12,0.35)",
                color: "#FFEDD5",
                fontSize: 11,
                fontWeight: 800,
                padding: "3px 10px",
                borderRadius: 999,
                border: "1px solid rgba(251,146,60,0.6)",
              }}
            >
              fila {pending.length}
            </span>
          ) : null}
        </h3>
        <div style={tableWrap}>
          <table style={table}>
            <thead>
              <tr>
                {["id", "locker_id", "operation", "status", "created_at", "last_error"].map((h) => (
                  <th key={h} style={th}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pending.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ ...td, color: "#94A3B8" }}>
                    Nenhum item pendente.
                  </td>
                </tr>
              ) : (
                pending.map((p) => (
                  <tr key={p.id}>
                    <td style={td}>
                      <code style={codeInline}>{String(p.id || "").slice(0, 8)}…</code>
                    </td>
                    <td style={td}>{p.locker_id}</td>
                    <td style={td}>{p.operation}</td>
                    <td style={td}>{p.status}</td>
                    <td style={td}>{p.created_at || "—"}</td>
                    <td style={td}>{p.last_error || "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

