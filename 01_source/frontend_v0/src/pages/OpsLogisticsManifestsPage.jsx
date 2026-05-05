
import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsActionButton from "../components/OpsActionButton";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsScenarioPresets from "../components/OpsScenarioPresets";
import { formatOpsTimeShort } from "../utils/opsDateTimeFormat";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const ACTION_STATUS_STORAGE_KEY = "ops_logistics_manifests:action_status_v1";

function parseError(payload, fallback = "Nao foi possivel executar a operacao de manifestos.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

export default function LogisticsManifestsPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const [manifestId, setManifestId] = useState("");
  const [itemId, setItemId] = useState("");
  const [exceptionReason, setExceptionReason] = useState("etiqueta ilegivel no recebimento");
  const [closePayload, setClosePayload] = useState('{\n  "actual_parcel_count": 0,\n  "carrier_note": "fechamento operacional D2"\n}');
  const [result, setResult] = useState("");
  const [loadingAction, setLoadingAction] = useState("");
  const [focusMode, setFocusMode] = useState("inspect");
  const [manifestHeader, setManifestHeader] = useState(null);
  const [manifestList, setManifestList] = useState([]);
  const [manifestListTotal, setManifestListTotal] = useState(null);
  const [listFilters, setListFilters] = useState({ locker_id: "", logistics_partner_id: "", status: "" });
  const [itemsRows, setItemsRows] = useState([]);
  const [itemsListTotal, setItemsListTotal] = useState(null);
  const [actionStatus, setActionStatus] = useState({
    "get-manifest": { status: "idle", at: null, note: "Aguardando execução" },
    "get-items": { status: "idle", at: null, note: "Aguardando execução" },
    "list-manifests": { status: "idle", at: null, note: "Aguardando execução" },
    "post-close": { status: "idle", at: null, note: "Aguardando execução" },
    "post-exception": { status: "idle", at: null, note: "Aguardando execução" },
  });

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(ACTION_STATUS_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object") return;
      setActionStatus((prev) => ({
        ...prev,
        "get-manifest": {
          ...prev["get-manifest"],
          ...(parsed["get-manifest"] || {}),
        },
        "get-items": {
          ...prev["get-items"],
          ...(parsed["get-items"] || {}),
        },
        "list-manifests": {
          ...prev["list-manifests"],
          ...(parsed["list-manifests"] || {}),
        },
        "post-close": {
          ...prev["post-close"],
          ...(parsed["post-close"] || {}),
        },
        "post-exception": {
          ...prev["post-exception"],
          ...(parsed["post-exception"] || {}),
        },
      }));
    } catch (_) {
      // fallback silencioso em ambientes sem storage/JSON inválido
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(ACTION_STATUS_STORAGE_KEY, JSON.stringify(actionStatus));
    } catch (_) {
      // fallback silencioso para ambiente sem localStorage
    }
  }, [actionStatus]);

  function updateActionStatus(actionKey, status, note) {
    setActionStatus((prev) => ({
      ...prev,
      [actionKey]: {
        status,
        at: formatOpsTimeShort(new Date()),
        note,
      },
    }));
  }

  async function runAction({ endpoint, method, body, successLabel, actionKey, onSuccess }) {
    if (!token) return;
    setLoadingAction(successLabel);
    updateActionStatus(actionKey, "running", "Executando...");
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}${endpoint}`, {
        method,
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseError(data));
      }
      setResult(JSON.stringify(data, null, 2));
      if (typeof onSuccess === "function") onSuccess(data);
      updateActionStatus(actionKey, "success", "Executado com sucesso");
    } catch (err) {
      const message = String(err?.message || err || "falha desconhecida");
      setResult(`Erro: ${message}`);
      updateActionStatus(actionKey, "error", message);
    } finally {
      setLoadingAction("");
    }
  }

  async function handleLoadManifestHeader() {
    const id = String(manifestId || "").trim();
    if (!id) {
      setResult("Informe manifest_id para carregar cabeçalho (carga/descarga).");
      return;
    }
    await runAction({
      endpoint: `/logistics/manifests/${encodeURIComponent(id)}`,
      method: "GET",
      successLabel: "get-manifest",
      actionKey: "get-manifest",
      onSuccess: (data) => {
        if (data && typeof data === "object" && data.id) setManifestHeader(data);
      },
    });
  }

  async function handleListManifests() {
    const params = new URLSearchParams();
    params.set("limit", "80");
    params.set("offset", "0");
    const locker = String(listFilters.locker_id || "").trim();
    const partner = String(listFilters.logistics_partner_id || "").trim();
    const st = String(listFilters.status || "").trim();
    if (locker) params.set("locker_id", locker);
    if (partner) params.set("logistics_partner_id", partner);
    if (st) params.set("status", st);
    await runAction({
      endpoint: `/logistics/manifests?${params.toString()}`,
      method: "GET",
      successLabel: "list-manifests",
      actionKey: "list-manifests",
      onSuccess: (data) => {
        const items = Array.isArray(data?.items) ? data.items : [];
        setManifestList(items);
        setManifestListTotal(typeof data?.total === "number" ? data.total : items.length);
      },
    });
  }

  async function handleListItems() {
    const id = String(manifestId || "").trim();
    if (!id) {
      setResult("Informe manifest_id para listar itens.");
      return;
    }
    await runAction({
      endpoint: `/logistics/manifests/${encodeURIComponent(id)}/items?limit=200&offset=0`,
      method: "GET",
      successLabel: "list-items",
      actionKey: "get-items",
      onSuccess: (data) => {
        const rows = Array.isArray(data?.items) ? data.items : [];
        setItemsRows(rows);
        setItemsListTotal(typeof data?.total === "number" ? data.total : rows.length);
      },
    });
  }

  async function handleCloseManifest() {
    const id = String(manifestId || "").trim();
    if (!id) {
      setResult("Informe manifest_id para fechar manifesto.");
      return;
    }
    let parsedBody = {};
    try {
      parsedBody = JSON.parse(closePayload || "{}");
    } catch (_) {
      setResult("JSON de fechamento invalido.");
      return;
    }
    await runAction({
      endpoint: `/logistics/manifests/${encodeURIComponent(id)}/close`,
      method: "POST",
      body: parsedBody,
      successLabel: "close-manifest",
      actionKey: "post-close",
      onSuccess: (data) => {
        if (data && typeof data === "object" && data.id) setManifestHeader(data);
      },
    });
  }

  async function handleMarkException() {
    const id = String(manifestId || "").trim();
    const normalizedItemId = Number(itemId || 0);
    const reason = String(exceptionReason || "").trim();
    if (!id || !Number.isFinite(normalizedItemId) || normalizedItemId <= 0 || !reason) {
      setResult("Informe manifest_id, item_id e reason para registrar exception.");
      return;
    }
    await runAction({
      endpoint: `/logistics/manifests/${encodeURIComponent(id)}/items/${normalizedItemId}/exception`,
      method: "POST",
      body: { reason },
      successLabel: "mark-exception",
      actionKey: "post-exception",
    });
  }

  function applyQuickFlow(mode) {
    setFocusMode(mode);
    setResult("");
    if (mode === "inspect") {
      setExceptionReason("etiqueta ilegivel no recebimento");
      setClosePayload('{\n  "actual_parcel_count": 0,\n  "carrier_note": "fechamento operacional D2"\n}');
      return;
    }
    if (mode === "close") {
      setClosePayload('{\n  "actual_parcel_count": 22,\n  "carrier_note": "fechamento turno manha"\n}');
      return;
    }
    if (mode === "exception") {
      setExceptionReason("etiqueta ilegivel no recebimento");
    }
  }

  const itemStatusBreakdown = useMemo(() => {
    const acc = { EXPECTED: 0, STORED: 0, EXCEPTION: 0, MISSING: 0, other: 0 };
    for (const row of itemsRows) {
      const s = String(row?.status || "").toUpperCase();
      if (s in acc) acc[s] += 1;
      else acc.other += 1;
    }
    return acc;
  }, [itemsRows]);

  const loadUnloadModel = useMemo(() => {
    const h = manifestHeader;
    if (!h) return null;
    const expected = Number(h.expected_parcel_count ?? 0);
    const actual = Number(h.actual_parcel_count ?? 0);
    return {
      expected,
      actual,
      delta: actual - expected,
      status: h.status,
    };
  }, [manifestHeader]);

  function selectManifestFromList(row) {
    if (!row?.id) return;
    setManifestId(String(row.id));
    setManifestHeader(row);
    setItemsRows([]);
    setItemsListTotal(null);
    setResult("");
  }

  const contextGuide = {
    inspect: {
      title: "Inspeção do manifesto",
      objective: "Consultar itens antes de tomar ação operacional.",
      usage: "Preencha manifest_id e execute GET items para confirmar status dos itens.",
    },
    close: {
      title: "Fechamento idempotente",
      objective: "Fechar manifesto com reconciliação expected vs actual.",
      usage: "Ajuste o JSON de close e execute POST close. Reexecuções devem manter estado consolidado.",
    },
    exception: {
      title: "Tratamento de exceção",
      objective: "Marcar item problemático sem quebrar o lote.",
      usage: "Informe item_id e reason; reenvio no mesmo item deve ser idempotente.",
    },
  }[focusMode];

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS - Logistics Manifests (D2)" />
        <p style={mutedStyle}>
          Operação rápida para endpoints D2 de manifesto: visão de carga (declarada) vs descarga (registrada), listagem, itens por tracking e fechamento idempotente.
        </p>

        <section style={loadUnloadSectionStyle}>
          <h3 style={{ margin: "0 0 8px 0", fontSize: 15 }}>Carga / descarga (manifesto)</h3>
          <p style={{ ...mutedStyle, marginTop: 0 }}>
            Carga = <code style={codeInlineStyle}>expected_parcel_count</code> no manifesto. Descarga ={" "}
            <code style={codeInlineStyle}>actual_parcel_count</code> após conferência/fechamento. Itens abaixo refletem{" "}
            <code style={codeInlineStyle}>logistics_manifest_items</code> (tracking + status).
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
            <OpsActionButton type="button" variant="primary" onClick={() => void handleLoadManifestHeader()} disabled={Boolean(loadingAction)}>
              {loadingAction === "get-manifest" ? "Carregando..." : "GET manifest (cabeçalho)"}
            </OpsActionButton>
          </div>
          {loadUnloadModel ? (
            <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
              <div style={kpiRowStyle}>
                <KpiPill label="Status" value={String(loadUnloadModel.status || "-")} tone="neutral" />
                <KpiPill label="Carga (esperado)" value={String(loadUnloadModel.expected)} tone="load" />
                <KpiPill label="Descarga (actual)" value={String(loadUnloadModel.actual)} tone="unload" />
                <KpiPill label="Delta" value={String(loadUnloadModel.delta >= 0 ? `+${loadUnloadModel.delta}` : loadUnloadModel.delta)} tone={loadUnloadModel.delta === 0 ? "neutral" : "warn"} />
              </div>
              <LoadUnloadBar expected={loadUnloadModel.expected} actual={loadUnloadModel.actual} />
              <small style={{ color: "#64748B" }}>Manifest ID: {manifestHeader?.id || "-"} · Locker: {manifestHeader?.locker_id || "-"}</small>
            </div>
          ) : (
            <p style={{ ...mutedStyle, marginBottom: 0 }}>Informe manifest_id e use GET manifest ou escolha uma linha na listagem.</p>
          )}
        </section>

        <section style={subCardStyle}>
          <h3 style={{ margin: "0 0 8px 0", fontSize: 15 }}>Listagem de manifestos</h3>
          <div style={gridStyle}>
            <label style={labelStyle}>
              locker_id (opcional)
              <input
                value={listFilters.locker_id}
                onChange={(e) => setListFilters((p) => ({ ...p, locker_id: e.target.value }))}
                style={inputStyle}
                placeholder="filtrar por armário"
              />
            </label>
            <label style={labelStyle}>
              logistics_partner_id (opcional)
              <input
                value={listFilters.logistics_partner_id}
                onChange={(e) => setListFilters((p) => ({ ...p, logistics_partner_id: e.target.value }))}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              status (opcional)
              <select
                value={listFilters.status}
                onChange={(e) => setListFilters((p) => ({ ...p, status: e.target.value }))}
                style={inputStyle}
              >
                <option value="">(todos)</option>
                <option value="PENDING">PENDING</option>
                <option value="IN_TRANSIT">IN_TRANSIT</option>
                <option value="DELIVERED">DELIVERED</option>
                <option value="PARTIAL">PARTIAL</option>
                <option value="FAILED">FAILED</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>
            </label>
          </div>
          <OpsActionButton type="button" variant="primary" style={{ marginTop: 10 }} onClick={() => void handleListManifests()} disabled={Boolean(loadingAction)}>
            {loadingAction === "list-manifests" ? "Listando..." : "GET /logistics/manifests"}
          </OpsActionButton>
          {manifestList.length > 0 ? (
            <div style={{ marginTop: 12, overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>Ação</th>
                    <th style={thStyle}>status</th>
                    <th style={thStyle}>carga</th>
                    <th style={thStyle}>descarga</th>
                    <th style={thStyle}>data</th>
                    <th style={thStyle}>locker</th>
                    <th style={thStyle}>id</th>
                  </tr>
                </thead>
                <tbody>
                  {manifestList.map((row) => (
                    <tr key={row.id} style={manifestId === row.id ? selectedRowStyle : undefined}>
                      <td style={tdStyle}>
                        <button type="button" style={tableButtonStyle} onClick={() => selectManifestFromList(row)}>
                          Usar
                        </button>
                      </td>
                      <td style={tdStyle}>{row.status}</td>
                      <td style={tdStyle}>{row.expected_parcel_count}</td>
                      <td style={tdStyle}>{row.actual_parcel_count}</td>
                      <td style={tdStyle}>{row.manifest_date}</td>
                      <td style={tdStyle}>{row.locker_id}</td>
                      <td style={{ ...tdStyle, fontFamily: "ui-monospace, monospace", fontSize: 11 }}>{row.id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <small style={{ color: "#64748B" }}>Total no filtro: {manifestListTotal ?? manifestList.length}</small>
            </div>
          ) : null}
        </section>

        {itemsRows.length > 0 ? (
          <section style={subCardStyle}>
            <h3 style={{ margin: "0 0 8px 0", fontSize: 15 }}>Itens (descarga por etiqueta)</h3>
            <div style={kpiRowStyle}>
              <KpiPill label="EXPECTED" value={String(itemStatusBreakdown.EXPECTED)} tone="load" />
              <KpiPill label="STORED" value={String(itemStatusBreakdown.STORED)} tone="unload" />
              <KpiPill label="EXCEPTION" value={String(itemStatusBreakdown.EXCEPTION)} tone="warn" />
              <KpiPill label="MISSING" value={String(itemStatusBreakdown.MISSING)} tone="error" />
            </div>
            <div style={{ marginTop: 10, overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>id</th>
                    <th style={thStyle}>tracking_code</th>
                    <th style={thStyle}>status</th>
                    <th style={thStyle}>seq</th>
                  </tr>
                </thead>
                <tbody>
                  {itemsRows.map((row) => (
                    <tr key={row.id}>
                      <td style={tdStyle}>{row.id}</td>
                      <td style={{ ...tdStyle, fontFamily: "ui-monospace, monospace", fontSize: 12 }}>{row.tracking_code}</td>
                      <td style={tdStyle}>{row.status}</td>
                      <td style={tdStyle}>{row.sequence_number ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <small style={{ color: "#64748B" }}>Linhas: {itemsRows.length} · total API: {itemsListTotal ?? itemsRows.length}</small>
            </div>
          </section>
        ) : null}

        <div style={playbookStyle}>
          <h3 style={{ margin: 0 }}>Guia rápido</h3>
          <ol style={playbookListStyle}>
            <li>Inspecione itens do manifesto com <b>GET items</b>.</li>
            <li>Se necessário, marque item com <b>POST exception</b>.</li>
            <li>Finalize com <b>POST close</b> e valide idempotência no replay.</li>
          </ol>
          <OpsScenarioPresets
            style={quickActionsStyle}
            disabled={Boolean(loadingAction)}
            items={[
              { id: "inspect", tone: "success", label: "Preset verde: inspecionar", onClick: () => applyQuickFlow("inspect") },
              { id: "close", tone: "warn", label: "Preset âmbar: fechamento parcial", onClick: () => applyQuickFlow("close") },
              { id: "exception", tone: "error", label: "Preset vermelho: exception crítica", onClick: () => applyQuickFlow("exception") },
            ]}
          />
        </div>

        <div style={contextHelpStyle}>
          <div><b>Contexto atual:</b> {contextGuide.title}</div>
          <div><b>Objetivo:</b> {contextGuide.objective}</div>
          <div><b>Como usar:</b> {contextGuide.usage}</div>
        </div>

        <div style={chipsRowStyle}>
          <ActionChip label="GET manifest" data={actionStatus["get-manifest"]} />
          <ActionChip label="GET manifests" data={actionStatus["list-manifests"]} />
          <ActionChip label="GET items" data={actionStatus["get-items"]} />
          <ActionChip label="POST close" data={actionStatus["post-close"]} />
          <ActionChip label="POST exception" data={actionStatus["post-exception"]} />
        </div>

        <div style={gridStyle}>
          <label style={labelStyle}>
            Manifest ID
            <input value={manifestId} onChange={(e) => setManifestId(e.target.value)} placeholder="ex.: a9f8d0a6-..." style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Item ID (exception)
            <input value={itemId} onChange={(e) => setItemId(e.target.value)} placeholder="ex.: 101" style={inputStyle} />
          </label>
        </div>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Reason (exception)
          <input value={exceptionReason} onChange={(e) => setExceptionReason(e.target.value)} style={inputStyle} />
          <div style={presetRowStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => setExceptionReason("etiqueta ilegivel no recebimento")} disabled={Boolean(loadingAction)}>
              Preset: etiqueta ilegível
            </button>
            <button type="button" style={buttonGhostStyle} onClick={() => setExceptionReason("pacote avariado no recebimento")} disabled={Boolean(loadingAction)}>
              Preset: pacote avariado
            </button>
            <button type="button" style={buttonGhostStyle} onClick={() => setExceptionReason("item não encontrado no lote")} disabled={Boolean(loadingAction)}>
              Preset: item não encontrado
            </button>
          </div>
        </label>

        <label style={{ ...labelStyle, marginTop: 10 }}>
          Payload close (JSON)
          <textarea value={closePayload} onChange={(e) => setClosePayload(e.target.value)} style={textareaStyle} />
          <div style={presetRowStyle}>
            <button
              type="button"
              style={buttonGhostStyle}
              onClick={() =>
                setClosePayload('{\n  "actual_parcel_count": 24,\n  "carrier_note": "fechamento com entrega total"\n}')
              }
              disabled={Boolean(loadingAction)}
            >
              Preset: DELIVERED
            </button>
            <button
              type="button"
              style={buttonGhostStyle}
              onClick={() =>
                setClosePayload('{\n  "actual_parcel_count": 22,\n  "carrier_note": "fechamento parcial do lote"\n}')
              }
              disabled={Boolean(loadingAction)}
            >
              Preset: PARTIAL
            </button>
            <button
              type="button"
              style={buttonGhostStyle}
              onClick={() =>
                setClosePayload('{\n  "actual_parcel_count": 0,\n  "carrier_note": "falha operacional no fechamento"\n}')
              }
              disabled={Boolean(loadingAction)}
            >
              Preset: FAILED
            </button>
          </div>
        </label>

        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleListItems()} disabled={Boolean(loadingAction)}>
            {loadingAction === "list-items" ? "Listando..." : "GET items"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleCloseManifest()} disabled={Boolean(loadingAction)}>
            {loadingAction === "close-manifest" ? "Fechando..." : "POST close"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="primary" onClick={() => void handleMarkException()} disabled={Boolean(loadingAction)}>
            {loadingAction === "mark-exception" ? "Marcando..." : "POST exception"}
          </OpsActionButton>
        </div>

        <pre style={resultStyle}>{result || "Execute uma acao para visualizar resposta tecnica."}</pre>
      </section>
    </div>
  );
}

function LoadUnloadBar({ expected, actual }) {
  const max = Math.max(Number(expected) || 0, Number(actual) || 0, 1);
  const wExp = Math.round((Number(expected) / max) * 100);
  const wAct = Math.round((Number(actual) / max) * 100);
  return (
    <div style={{ display: "grid", gap: 6 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "#94A3B8" }}>
        <span style={{ minWidth: 72 }}>Carga</span>
        <div style={{ flex: 1, height: 10, borderRadius: 6, background: "#0f172a", border: "1px solid #1e293b", overflow: "hidden" }}>
          <div style={{ width: `${wExp}%`, height: "100%", background: "rgba(59,130,246,0.7)" }} />
        </div>
        <span style={{ fontVariantNumeric: "tabular-nums" }}>{expected}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "#94A3B8" }}>
        <span style={{ minWidth: 72 }}>Descarga</span>
        <div style={{ flex: 1, height: 10, borderRadius: 6, background: "#0f172a", border: "1px solid #1e293b", overflow: "hidden" }}>
          <div style={{ width: `${wAct}%`, height: "100%", background: "rgba(16,185,129,0.75)" }} />
        </div>
        <span style={{ fontVariantNumeric: "tabular-nums" }}>{actual}</span>
      </div>
    </div>
  );
}

function KpiPill({ label, value, tone }) {
  const border =
    tone === "load"
      ? "rgba(59,130,246,0.45)"
      : tone === "unload"
        ? "rgba(16,185,129,0.45)"
        : tone === "warn"
          ? "rgba(245,158,11,0.45)"
          : tone === "error"
            ? "rgba(239,68,68,0.45)"
            : "rgba(148,163,184,0.4)";
  const bg =
    tone === "load"
      ? "rgba(59,130,246,0.12)"
      : tone === "unload"
        ? "rgba(16,185,129,0.12)"
        : tone === "warn"
          ? "rgba(245,158,11,0.12)"
          : tone === "error"
            ? "rgba(239,68,68,0.12)"
            : "rgba(148,163,184,0.1)";
  return (
    <div style={{ border: `1px solid ${border}`, background: bg, borderRadius: 10, padding: "8px 10px", minWidth: 120 }}>
      <div style={{ fontSize: 11, color: "#94A3B8" }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: "#F8FAFC" }}>{value}</div>
    </div>
  );
}

function ActionChip({ label, data }) {
  const normalized = String(data?.status || "idle");
  const palette =
    normalized === "success"
      ? { border: "rgba(16,185,129,0.45)", bg: "rgba(16,185,129,0.12)", color: "#6EE7B7", text: "OK" }
      : normalized === "error"
        ? { border: "rgba(239,68,68,0.45)", bg: "rgba(239,68,68,0.12)", color: "#FCA5A5", text: "ERRO" }
        : normalized === "running"
          ? { border: "rgba(59,130,246,0.45)", bg: "rgba(59,130,246,0.12)", color: "#93C5FD", text: "RUN" }
          : { border: "rgba(148,163,184,0.4)", bg: "rgba(148,163,184,0.1)", color: "#CBD5E1", text: "IDLE" };

  return (
    <article
      style={{
        border: `1px solid ${palette.border}`,
        background: palette.bg,
        borderRadius: 10,
        padding: "8px 10px",
        minWidth: 180,
        display: "grid",
        gap: 4,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 6 }}>
        <strong style={{ fontSize: 12 }}>{label}</strong>
        <span style={{ color: palette.color, fontWeight: 800, fontSize: 11 }}>{palette.text}</span>
      </div>
      <small style={{ color: "#94A3B8" }}>{data?.note || "-"}</small>
      <small style={{ color: "#64748B" }}>Última execução: {data?.at || "-"}</small>
    </article>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8 };
const playbookStyle = {
  marginTop: 12,
  padding: 12,
  borderRadius: 12,
  background: "rgba(29,78,216,0.12)",
  border: "1px solid rgba(29,78,216,0.35)",
  display: "grid",
  gap: 8,
};
const playbookListStyle = { margin: 0, paddingLeft: 18, display: "grid", gap: 4 };
const quickActionsStyle = { display: "flex", gap: 8, flexWrap: "wrap" };
const contextHelpStyle = {
  marginTop: 10,
  padding: 10,
  borderRadius: 10,
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.10)",
  display: "grid",
  gap: 4,
  fontSize: 13,
};
const loadUnloadSectionStyle = {
  marginTop: 14,
  padding: 12,
  borderRadius: 12,
  background: "rgba(15,118,110,0.08)",
  border: "1px solid rgba(45,212,191,0.25)",
};
const subCardStyle = {
  marginTop: 14,
  padding: 12,
  borderRadius: 12,
  background: "rgba(15,23,42,0.6)",
  border: "1px solid #334155",
};
const kpiRowStyle = { display: "flex", gap: 8, flexWrap: "wrap" };
const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 12 };
const thStyle = { textAlign: "left", padding: "8px 6px", borderBottom: "1px solid #334155", color: "#94A3B8" };
const tdStyle = { padding: "8px 6px", borderBottom: "1px solid #1e293b", verticalAlign: "top" };
const tableButtonStyle = {
  padding: "4px 8px",
  borderRadius: 6,
  border: "1px solid #475569",
  background: "#0B1220",
  color: "#E2E8F0",
  cursor: "pointer",
  fontSize: 11,
  fontWeight: 600,
};
const selectedRowStyle = { background: "rgba(59,130,246,0.12)" };
const codeInlineStyle = { color: "#7DD3FC", fontSize: 12 };
const chipsRowStyle = { marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" };
const gridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const textareaStyle = { minHeight: 120, padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" };
const presetRowStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 6 };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 };
const buttonGhostStyle = { padding: "6px 10px", borderRadius: 999, border: "1px solid #334155", background: "#0B1220", color: "#CBD5E1", fontWeight: 600, cursor: "pointer", fontSize: 12 };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };

/** Alias OPS para importações nomeadas; o default export é `LogisticsManifestsPage`. */
export { LogisticsManifestsPage as OpsLogisticsManifestsPage };

