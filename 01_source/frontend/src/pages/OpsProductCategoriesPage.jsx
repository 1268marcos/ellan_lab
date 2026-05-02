import React, { useCallback, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

function parseError(payload, fallback = "Nao foi possivel carregar categorias.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) {
      return payload.detail.message.trim();
    }
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) {
      return payload.detail.type.trim();
    }
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

function buildTree(items) {
  const list = Array.isArray(items) ? items : [];
  const byId = new Map();
  for (const raw of list) {
    byId.set(raw.id, { ...raw, children: [] });
  }
  const roots = [];
  for (const node of byId.values()) {
    const pid = node.parent_category ? String(node.parent_category) : "";
    if (pid && byId.has(pid)) {
      byId.get(pid).children.push(node);
    } else {
      roots.push(node);
    }
  }
  const sortRec = (nodes) => {
    nodes.sort((a, b) => String(a.name).localeCompare(String(b.name), "pt-BR"));
    for (const n of nodes) sortRec(n.children);
  };
  sortRec(roots);
  return roots;
}

function metadataToForm(meta) {
  const m = meta && typeof meta === "object" ? meta : {};
  return {
    temperature_zone: String(m.temperature_zone ?? m.default_temperature_zone ?? "AMBIENT"),
    security_level: String(m.security_level ?? m.default_security_level ?? "STANDARD"),
    is_hazardous: Boolean(m.is_hazardous),
  };
}

function TreeRows({ nodes, depth, onEdit, onDelete }) {
  if (!nodes?.length) return null;
  return (
    <>
      {nodes.map((node) => (
        <React.Fragment key={node.id}>
          <tr>
            <td style={{ ...tdStyle, paddingLeft: 10 + depth * 18 }}>{node.id}</td>
            <td style={tdStyle}>{node.name}</td>
            <td style={tdStyle}>{node.parent_category || "—"}</td>
            <td style={tdStyle}>
              <code style={codeStyle}>{JSON.stringify(node.metadata_json || {})}</code>
            </td>
            <td style={tdStyle}>{node.created_at?.slice?.(0, 19) || "—"}</td>
            <td style={tdStyle}>
              <button type="button" style={btnSm} onClick={() => onEdit(node)}>
                Editar
              </button>{" "}
              <button type="button" style={btnSmDanger} onClick={() => onDelete(node)}>
                Excluir
              </button>
            </td>
          </tr>
          <TreeRows nodes={node.children} depth={depth + 1} onEdit={onEdit} onDelete={onDelete} />
        </React.Fragment>
      ))}
    </>
  );
}

export default function OpsProductCategoriesPage() {
  const { token } = useAuth();
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
      const r = await fetch(`${ORDER_PICKUP_BASE}/product-categories`, {
        method: "GET",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(data));
      setItems(Array.isArray(data.items) ? data.items : []);
    } catch (e) {
      setError(normalizeNetworkError(e, `${ORDER_PICKUP_BASE}/product-categories`));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [token, authHeaders]);

  const tree = useMemo(() => buildTree(items), [items]);

  const openCreate = () => {
    setModal({
      mode: "create",
      id: "",
      name: "",
      description: "",
      parent_category: "",
      meta: { temperature_zone: "AMBIENT", security_level: "STANDARD", is_hazardous: false },
    });
  };

  const openEdit = (row) => {
    const m = metadataToForm(row.metadata_json);
    setModal({
      mode: "edit",
      id: row.id,
      name: row.name || "",
      description: row.description || "",
      parent_category: row.parent_category || "",
      meta: m,
    });
  };

  const closeModal = () => setModal(null);

  const saveModal = async () => {
    if (!token || !modal) return;
    setError("");
    try {
      if (modal.mode === "create") {
        const id = String(modal.id || "").trim();
        const name = String(modal.name || "").trim();
        if (!id || !name) {
          setError("id e name sao obrigatorios.");
          return;
        }
        const r = await fetch(`${ORDER_PICKUP_BASE}/product-categories`, {
          method: "POST",
          headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
          body: JSON.stringify({
            id,
            name,
            description: modal.description?.trim() || null,
            parent_category: modal.parent_category?.trim() || null,
            metadata_json: {
              temperature_zone: modal.meta.temperature_zone,
              security_level: modal.meta.security_level,
              is_hazardous: modal.meta.is_hazardous,
            },
          }),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(parseError(data, "Falha ao criar categoria."));
      } else {
        const r = await fetch(`${ORDER_PICKUP_BASE}/product-categories/${encodeURIComponent(modal.id)}`, {
          method: "PATCH",
          headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders },
          body: JSON.stringify({
            name: String(modal.name || "").trim() || undefined,
            description: modal.description?.trim() ? modal.description.trim() : null,
            parent_category: modal.parent_category?.trim() ? modal.parent_category.trim() : null,
            metadata_json: {
              temperature_zone: modal.meta.temperature_zone,
              security_level: modal.meta.security_level,
              is_hazardous: modal.meta.is_hazardous,
            },
          }),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(parseError(data, "Falha ao atualizar categoria."));
      }
      closeModal();
      await load();
    } catch (e) {
      setError(normalizeNetworkError(e, ORDER_PICKUP_BASE));
    }
  };

  const onDelete = async (row) => {
    if (!token || !row?.id) return;
    if (!window.confirm(`Excluir categoria ${row.id}?`)) return;
    setError("");
    try {
      const r = await fetch(`${ORDER_PICKUP_BASE}/product-categories/${encodeURIComponent(row.id)}`, {
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
        <OpsPageTitleHeader title="OPS — Product categories" />
        <p style={muted}>
          Hierarquia via <code>parent_category</code>. API: <code>{ORDER_PICKUP_BASE}/product-categories</code> (role{" "}
          <code>admin_operacao</code>).
        </p>
        <div style={rowActions}>
          <button type="button" style={btnPrimary} disabled={loading || !token} onClick={() => void load()}>
            {loading ? "Carregando…" : "Atualizar"}
          </button>
          <button type="button" style={btnSecondary} disabled={!token} onClick={openCreate}>
            Nova categoria
          </button>
        </div>
        {error ? <pre style={errBox}>{error}</pre> : null}
        {!token ? <p style={muted}>Faça login com perfil admin_operacao.</p> : null}
        {token && !loading && !items.length && !error ? <p style={muted}>Nenhuma categoria retornada.</p> : null}
        {items.length > 0 ? (
          <div style={tableWrap}>
            <table style={table}>
              <thead>
                <tr>
                  <th style={th}>ID</th>
                  <th style={th}>Nome</th>
                  <th style={th}>Pai</th>
                  <th style={th}>metadata_json (zonas / segurança)</th>
                  <th style={th}>created_at</th>
                  <th style={th}>Ações</th>
                </tr>
              </thead>
              <tbody>
                <TreeRows nodes={tree} depth={0} onEdit={openEdit} onDelete={onDelete} />
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {modal ? (
        <div style={backdrop} role="presentation" onClick={closeModal}>
          <div style={modalCard} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <h2 style={h2}>{modal.mode === "create" ? "Nova categoria" : `Editar ${modal.id}`}</h2>
            {modal.mode === "create" ? (
              <label style={lbl}>
                id
                <input style={inp} value={modal.id} onChange={(e) => setModal({ ...modal, id: e.target.value })} placeholder="ex.: MEDICAL_EQUIPMENT" />
              </label>
            ) : (
              <p style={muted}>
                id: <code>{modal.id}</code>
              </p>
            )}
            <label style={lbl}>
              name
              <input style={inp} value={modal.name} onChange={(e) => setModal({ ...modal, name: e.target.value })} />
            </label>
            <label style={lbl}>
              parent_category (opcional)
              <input
                style={inp}
                value={modal.parent_category}
                onChange={(e) => setModal({ ...modal, parent_category: e.target.value })}
                placeholder="id da categoria pai"
              />
            </label>
            <label style={lbl}>
              description
              <textarea style={{ ...inp, minHeight: 64 }} value={modal.description} onChange={(e) => setModal({ ...modal, description: e.target.value })} />
            </label>
            <div style={metaGrid}>
              <label style={lbl}>
                temperature_zone
                <select
                  style={inp}
                  value={modal.meta.temperature_zone}
                  onChange={(e) => setModal({ ...modal, meta: { ...modal.meta, temperature_zone: e.target.value } })}
                >
                  {["AMBIENT", "REFRIGERATED", "FROZEN"].map((z) => (
                    <option key={z} value={z}>
                      {z}
                    </option>
                  ))}
                </select>
              </label>
              <label style={lbl}>
                security_level
                <select
                  style={inp}
                  value={modal.meta.security_level}
                  onChange={(e) => setModal({ ...modal, meta: { ...modal.meta, security_level: e.target.value } })}
                >
                  {["STANDARD", "HIGH", "VAULT"].map((z) => (
                    <option key={z} value={z}>
                      {z}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ ...lbl, flexDirection: "row", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={modal.meta.is_hazardous}
                  onChange={(e) => setModal({ ...modal, meta: { ...modal.meta, is_hazardous: e.target.checked } })}
                />
                is_hazardous
              </label>
            </div>
            <div style={rowActions}>
              <button type="button" style={btnPrimary} onClick={() => void saveModal()}>
                Salvar
              </button>
              <button type="button" style={btnSecondary} onClick={closeModal}>
                Cancelar
              </button>
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
const table = { width: "100%", borderCollapse: "collapse", minWidth: 720 };
const th = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B", verticalAlign: "top" };
const codeStyle = { fontSize: 11, color: "#CBD5E1", whiteSpace: "pre-wrap", wordBreak: "break-all" };
const btnSm = { padding: "4px 8px", borderRadius: 8, border: "1px solid #475569", background: "#1E293B", color: "#E2E8F0", fontSize: 11, cursor: "pointer" };
const btnSmDanger = { ...btnSm, borderColor: "#7f1d1d", background: "rgba(127,29,29,0.35)" };
const backdrop = {
  position: "fixed",
  inset: 0,
  background: "rgba(15,23,42,0.72)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 50,
  padding: 16,
};
const modalCard = {
  background: "#111827",
  border: "1px solid #334155",
  borderRadius: 14,
  padding: 20,
  maxWidth: 480,
  width: "100%",
  boxSizing: "border-box",
  display: "grid",
  gap: 10,
};
const h2 = { margin: 0, fontSize: 18, color: "#F8FAFC" };
const lbl = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inp = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const metaGrid = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 4 };
