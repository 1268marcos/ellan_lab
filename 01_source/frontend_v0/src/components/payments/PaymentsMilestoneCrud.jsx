import React, { useState } from "react";
import { buttonGhostStyle, buttonPrimaryStyle, healthLocalFilterInputStyle } from "../../styles/opsShellStyles";

const API_BASE = import.meta.env.VITE_PAYMENTS_ADMIN_BASE_URL || "/api/pya";
const API = `${API_BASE}/v1/payments-admin`;

const empty = {
  player_code: "INPOST",
  phase: "PILOT",
  title: "",
  status: "PLANNED",
  owner_team: "platform-integrations",
  target_date: "",
};

export default function PaymentsMilestoneCrud({ headers, rows, onRefresh, onOk, onErr }) {
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);

  const reset = () => {
    setEditingId(null);
    setForm(empty);
  };

  const save = async () => {
    if (!form.title.trim()) {
      onErr("Titulo obrigatorio");
      return;
    }
    setBusy(true);
    try {
      const url = editingId
        ? `${API}/integration-milestones/${encodeURIComponent(editingId)}`
        : `${API}/integration-milestones`;
      const method = editingId ? "PATCH" : "POST";
      const body = editingId
        ? {
            phase: form.phase,
            title: form.title,
            status: form.status,
            owner_team: form.owner_team || undefined,
            target_date: form.target_date || null,
          }
        : {
            player_code: form.player_code.toUpperCase(),
            phase: form.phase,
            title: form.title,
            status: form.status,
            owner_team: form.owner_team || undefined,
            target_date: form.target_date || undefined,
          };
      const r = await fetch(url, {
        method,
        headers,
        body: JSON.stringify(body),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.detail || "Falha ao salvar");
      onOk(editingId ? "Marco atualizado." : "Marco criado.");
      reset();
      onRefresh();
    } catch (e) {
      onErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Excluir marco?")) return;
    setBusy(true);
    try {
      const r = await fetch(`${API}/integration-milestones/${encodeURIComponent(id)}`, {
        method: "DELETE",
        headers,
      });
      if (!r.ok && r.status !== 204) throw new Error("Falha ao excluir");
      onOk("Marco excluido.");
      if (editingId === id) reset();
      onRefresh();
    } catch (e) {
      onErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ marginBottom: 12, padding: 12, border: "1px solid rgba(148,163,184,0.2)", borderRadius: 8 }}>
      <h4 style={{ margin: "0 0 8px" }}>{editingId ? "Editar marco" : "Novo marco"}</h4>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
        <input
          style={healthLocalFilterInputStyle}
          placeholder="player"
          value={form.player_code}
          disabled={!!editingId}
          onChange={(e) => setForm({ ...form, player_code: e.target.value })}
        />
        <input
          style={healthLocalFilterInputStyle}
          placeholder="titulo"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
        />
        <select
          style={healthLocalFilterInputStyle}
          value={form.phase}
          onChange={(e) => setForm({ ...form, phase: e.target.value })}
        >
          {["DISCOVERY", "SANDBOX", "CERTIFICATION", "PILOT", "PRODUCTION"].map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <select
          style={healthLocalFilterInputStyle}
          value={form.status}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
        >
          {["PLANNED", "IN_PROGRESS", "DONE", "BLOCKED"].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button type="button" style={buttonPrimaryStyle} disabled={busy} onClick={() => void save()}>
          {editingId ? "Salvar" : "Criar"}
        </button>
        {editingId ? (
          <button type="button" style={buttonGhostStyle} onClick={reset}>
            Cancelar
          </button>
        ) : null}
      </div>
      <div style={{ marginTop: 8, fontSize: 12, maxHeight: 100, overflow: "auto" }}>
        {(rows || []).slice(0, 6).map((r) => (
          <div key={r.id} style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
            <span>
              {r.player_code} · {r.title?.slice(0, 30)}
            </span>
            <span>
              <button type="button" style={{ fontSize: 11 }} onClick={() => {
                setEditingId(r.id);
                setForm({
                  player_code: r.player_code,
                  phase: r.phase,
                  title: r.title,
                  status: r.status,
                  owner_team: r.owner_team || "",
                  target_date: r.target_date || "",
                });
              }}>
                editar
              </button>
              {" · "}
              <button type="button" style={{ fontSize: 11, color: "#f87171" }} onClick={() => void remove(r.id)}>
                excluir
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
