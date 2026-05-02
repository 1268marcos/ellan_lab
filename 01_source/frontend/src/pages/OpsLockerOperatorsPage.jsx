import React, { useCallback, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

function parseError(payload, fallback = "Nao foi possivel carregar operadores.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique o proxy /api/op (porta 8010).`;
  }
  return raw;
}

function toDatetimeLocal(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromDatetimeLocal(s) {
  const t = String(s || "").trim();
  if (!t) return null;
  const d = new Date(t);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

const emptyForm = () => ({
  id: "",
  name: "",
  document: "",
  email: "",
  phone: "",
  operator_type: "LOGISTICS",
  country: "BR",
  commission_rate: "",
  currency: "BRL",
  status: "DRAFT",
  contract_start_at: "",
  contract_end_at: "",
});

export default function OpsLockerOperatorsPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [modal, setModal] = useState(null);
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${ORDER_PICKUP_BASE}/operators`, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(data));
      setItems(Array.isArray(data.items) ? data.items : []);
    } catch (e) {
      setError(normalizeNetworkError(e, `${ORDER_PICKUP_BASE}/operators`));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [token, authHeaders]);

  const openCreate = () => setModal({ mode: "create", ...emptyForm() });
  const openEdit = (row) =>
    setModal({
      mode: "edit",
      id: row.id,
      name: row.name || "",
      document: row.document || "",
      email: row.email || "",
      phone: row.phone || "",
      operator_type: row.operator_type || "LOGISTICS",
      country: row.country || "BR",
      commission_rate: row.commission_rate != null ? String(row.commission_rate) : "",
      currency: row.currency || "BRL",
      status: row.status || "DRAFT",
      active: Boolean(row.active),
      contract_start_at: toDatetimeLocal(row.contract_start_at),
      contract_end_at: toDatetimeLocal(row.contract_end_at),
    });
  const closeModal = () => setModal(null);

  const saveModal = async () => {
    if (!token || !modal || !canMutate) return;
    setError("");
    try {
      const cr = String(modal.commission_rate || "").trim();
      const commission_rate = cr === "" ? null : Number(cr);
      if (cr !== "" && Number.isNaN(commission_rate)) {
        setError("commission_rate invalido.");
        return;
      }
      if (modal.mode === "create") {
        const id = String(modal.id || "").trim();
        const name = String(modal.name || "").trim();
        if (!id || !name) {
          setError("id e name sao obrigatorios.");
          return;
        }
        const body = {
          id,
          name,
          document: modal.document?.trim() || null,
          email: modal.email?.trim() || null,
          phone: modal.phone?.trim() || null,
          operator_type: modal.operator_type || "LOGISTICS",
          country: (modal.country || "BR").slice(0, 2).toUpperCase(),
          commission_rate,
          currency: modal.currency || "BRL",
          status: modal.status || "DRAFT",
          contract_start_at: fromDatetimeLocal(modal.contract_start_at),
          contract_end_at: fromDatetimeLocal(modal.contract_end_at),
        };
        const r = await fetch(`${ORDER_PICKUP_BASE}/operators`, {
          method: "POST",
          headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
          body: JSON.stringify(body),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(parseError(data, "Falha ao criar operador."));
      } else {
        const nm = String(modal.name || "").trim();
        if (!nm) {
          setError("name e obrigatorio.");
          return;
        }
        const body = {
          name: nm,
          document: modal.document?.trim() ? modal.document.trim() : null,
          email: modal.email?.trim() ? modal.email.trim() : null,
          phone: modal.phone?.trim() ? modal.phone.trim() : null,
          operator_type: modal.operator_type || undefined,
          country: (modal.country || "").slice(0, 2).toUpperCase() || undefined,
          active: modal.active,
          commission_rate,
          currency: modal.currency || undefined,
          status: modal.status || undefined,
          contract_start_at: fromDatetimeLocal(modal.contract_start_at),
          contract_end_at: fromDatetimeLocal(modal.contract_end_at),
        };
        const r = await fetch(`${ORDER_PICKUP_BASE}/operators/${encodeURIComponent(modal.id)}`, {
          method: "PATCH",
          headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
          body: JSON.stringify(body),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(parseError(data, "Falha ao atualizar operador."));
      }
      closeModal();
      await load();
    } catch (e) {
      setError(normalizeNetworkError(e, ORDER_PICKUP_BASE));
    }
  };

  const onDelete = async (row) => {
    if (!token || !row?.id || !canMutate) return;
    if (!window.confirm(`Excluir operador ${row.id}?`)) return;
    setError("");
    try {
      const r = await fetch(`${ORDER_PICKUP_BASE}/operators/${encodeURIComponent(row.id)}`, {
        method: "DELETE",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(data, "Falha ao excluir."));
      await load();
    } catch (e) {
      setError(normalizeNetworkError(e, ORDER_PICKUP_BASE));
    }
  };

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Locker operators" />
        <p style={muted}>
          Gestao de <code>locker_operators</code> (comissao / contrato). API: <code>{ORDER_PICKUP_BASE}/operators</code> — listagem e escrita exigem{" "}
          <code>admin_operacao</code>.
        </p>
        <div style={rowActions}>
          <button type="button" style={btnPrimary} disabled={loading || !token || !canMutate} onClick={() => void load()}>
            {loading ? "Carregando…" : "Atualizar"}
          </button>
          <button type="button" style={btnSecondary} disabled={!token || !canMutate} onClick={openCreate}>
            Novo operador
          </button>
        </div>
        {error ? <pre style={errBox}>{error}</pre> : null}
        {!token ? <p style={muted}>Faça login.</p> : null}
        {token && !canMutate ? <p style={muted}>Listagem e alteracoes exigem perfil admin_operacao.</p> : null}
        {token && !loading && !items.length && !error ? <p style={muted}>Nenhum operador retornado.</p> : null}
        {items.length > 0 ? (
          <div style={tableWrap}>
            <table style={table}>
              <thead>
                <tr>
                  <th style={th}>ID</th>
                  <th style={th}>Nome</th>
                  <th style={th}>Doc / email</th>
                  <th style={th}>Tipo / pais</th>
                  <th style={th}>Comissao</th>
                  <th style={th}>Contrato</th>
                  <th style={th}>Status</th>
                  <th style={th}>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}><code>{row.id}</code></td>
                    <td style={tdStyle}>{row.name}</td>
                    <td style={tdStyle}>
                      {row.document || "—"}
                      <br />
                      <span style={{ color: "#94A3B8" }}>{row.email || "—"}</span>
                    </td>
                    <td style={tdStyle}>
                      {row.operator_type}
                      <br />
                      {row.country}
                    </td>
                    <td style={tdStyle}>
                      {row.commission_rate != null ? row.commission_rate : "—"} {row.currency ? `(${row.currency})` : ""}
                    </td>
                    <td style={tdStyle}>
                      {row.contract_start_at?.slice?.(0, 10) || "—"} → {row.contract_end_at?.slice?.(0, 10) || "—"}
                    </td>
                    <td style={tdStyle}>
                      {row.status}
                      <br />
                      <span style={{ color: row.active ? "#86efac" : "#fca5a5" }}>{row.active ? "active" : "inactive"}</span>
                    </td>
                    <td style={tdStyle}>
                      <button type="button" style={btnSm} disabled={!canMutate} onClick={() => openEdit(row)}>Editar</button>{" "}
                      <button type="button" style={btnSmDanger} disabled={!canMutate} onClick={() => void onDelete(row)}>Excluir</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {modal ? (
        <div style={backdrop} role="presentation" onClick={closeModal}>
          <div style={modalCard} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <h2 style={h2}>{modal.mode === "create" ? "Novo operador" : `Editar ${modal.id}`}</h2>
            {modal.mode === "create" ? (
              <label style={lbl}>
                id
                <input style={inp} value={modal.id} onChange={(e) => setModal({ ...modal, id: e.target.value })} placeholder="ex.: OP_SP_01" />
              </label>
            ) : (
              <p style={muted}>id: <code>{modal.id}</code></p>
            )}
            <label style={lbl}>name<input style={inp} value={modal.name} onChange={(e) => setModal({ ...modal, name: e.target.value })} /></label>
            <label style={lbl}>document<input style={inp} value={modal.document} onChange={(e) => setModal({ ...modal, document: e.target.value })} /></label>
            <label style={lbl}>email<input style={inp} value={modal.email} onChange={(e) => setModal({ ...modal, email: e.target.value })} /></label>
            <label style={lbl}>phone<input style={inp} value={modal.phone} onChange={(e) => setModal({ ...modal, phone: e.target.value })} /></label>
            <label style={lbl}>
              operator_type
              <input style={inp} value={modal.operator_type} onChange={(e) => setModal({ ...modal, operator_type: e.target.value })} />
            </label>
            <div style={grid2}>
              <label style={lbl}>country<input style={inp} maxLength={2} value={modal.country} onChange={(e) => setModal({ ...modal, country: e.target.value.toUpperCase() })} /></label>
              <label style={lbl}>currency<input style={inp} value={modal.currency} onChange={(e) => setModal({ ...modal, currency: e.target.value })} /></label>
            </div>
            <label style={lbl}>
              commission_rate (numero, ex. 0.05 ou 15)
              <input style={inp} value={modal.commission_rate} onChange={(e) => setModal({ ...modal, commission_rate: e.target.value })} placeholder="vazio = null" />
            </label>
            <label style={lbl}>
              status
              <input style={inp} value={modal.status} onChange={(e) => setModal({ ...modal, status: e.target.value })} />
            </label>
            {modal.mode === "edit" ? (
              <label style={{ ...lbl, flexDirection: "row", alignItems: "center", gap: 8 }}>
                <input type="checkbox" checked={modal.active} onChange={(e) => setModal({ ...modal, active: e.target.checked })} />
                active
              </label>
            ) : null}
            <div style={grid2}>
              <label style={lbl}>contract_start<input type="datetime-local" style={inp} value={modal.contract_start_at} onChange={(e) => setModal({ ...modal, contract_start_at: e.target.value })} /></label>
              <label style={lbl}>contract_end<input type="datetime-local" style={inp} value={modal.contract_end_at} onChange={(e) => setModal({ ...modal, contract_end_at: e.target.value })} /></label>
            </div>
            <div style={rowActions}>
              <button type="button" style={btnPrimary} disabled={!canMutate} onClick={() => void saveModal()}>Salvar</button>
              <button type="button" style={btnSecondary} onClick={closeModal}>Cancelar</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const muted = { color: "#94A3B8", marginTop: 8 };
const rowActions = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 };
const btnPrimary = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const btnSecondary = { padding: "10px 14px", borderRadius: 10, border: "1px solid #334155", background: "#0B1220", color: "#E2E8F0", fontWeight: 600, cursor: "pointer" };
const errBox = { marginTop: 12, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10 };
const tableWrap = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const table = { width: "100%", borderCollapse: "collapse", minWidth: 880 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B", verticalAlign: "top" };
const btnSm = { padding: "4px 8px", borderRadius: 8, border: "1px solid #475569", background: "#1E293B", color: "#E2E8F0", fontSize: 11, cursor: "pointer" };
const btnSmDanger = { ...btnSm, borderColor: "#7f1d1d", background: "rgba(127,29,29,0.35)" };
const backdrop = { position: "fixed", inset: 0, background: "rgba(15,23,42,0.72)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50, padding: 16 };
const modalCard = { background: "#111827", border: "1px solid #334155", borderRadius: 14, padding: 20, maxWidth: 520, width: "100%", boxSizing: "border-box", display: "grid", gap: 10 };
const h2 = { margin: 0, fontSize: 18, color: "#F8FAFC" };
const lbl = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inp = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const grid2 = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 };
