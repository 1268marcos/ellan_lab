import React, { useState } from "react";
import { buttonGhostStyle, buttonPrimaryStyle, healthLocalFilterInputStyle } from "../../styles/opsShellStyles";

const API_BASE = import.meta.env.VITE_PAYMENTS_ADMIN_BASE_URL || "/api/pya";
const API = `${API_BASE}/v1/payments-admin`;

const empty = {
  rule_code: "",
  country_code: "BR",
  payment_method: "PIX",
  primary_player_code: "MERCADOPAGO",
  fallback_player_code: "",
  priority: "100",
  rationale: "",
  is_active: true,
};

export default function PaymentsRoutingCrud({ headers, rows, onRefresh, onOk, onErr }) {
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);

  const reset = () => {
    setEditingId(null);
    setForm(empty);
  };

  const save = async () => {
    if (!editingId && !form.rule_code.trim()) {
      onErr("rule_code obrigatorio");
      return;
    }
    setBusy(true);
    try {
      const url = editingId
        ? `${API}/routing-rules/${encodeURIComponent(editingId)}`
        : `${API}/routing-rules`;
      const method = editingId ? "PATCH" : "POST";
      const body = editingId
        ? {
            country_code: form.country_code.toUpperCase(),
            payment_method: form.payment_method.toUpperCase(),
            primary_player_code: form.primary_player_code.toUpperCase(),
            fallback_player_code: form.fallback_player_code
              ? form.fallback_player_code.toUpperCase()
              : null,
            priority: Number(form.priority),
            rationale: form.rationale || undefined,
            is_active: form.is_active,
          }
        : {
            rule_code: form.rule_code.toUpperCase(),
            country_code: form.country_code.toUpperCase(),
            payment_method: form.payment_method.toUpperCase(),
            primary_player_code: form.primary_player_code.toUpperCase(),
            fallback_player_code: form.fallback_player_code
              ? form.fallback_player_code.toUpperCase()
              : undefined,
            priority: Number(form.priority),
            rationale: form.rationale || undefined,
            is_active: form.is_active,
          };
      const r = await fetch(url, { method, headers, body: JSON.stringify(body) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.detail || "Falha ao salvar");
      onOk(editingId ? "Regra atualizada." : "Regra criada.");
      reset();
      onRefresh();
    } catch (e) {
      onErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Excluir regra?")) return;
    setBusy(true);
    try {
      const r = await fetch(`${API}/routing-rules/${encodeURIComponent(id)}`, {
        method: "DELETE",
        headers,
      });
      if (!r.ok && r.status !== 204) throw new Error("Falha ao excluir");
      onOk("Regra excluida.");
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
      <h4 style={{ margin: "0 0 8px" }}>{editingId ? "Editar regra" : "Nova regra"}</h4>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
        <input
          style={healthLocalFilterInputStyle}
          placeholder="rule_code"
          value={form.rule_code}
          disabled={!!editingId}
          onChange={(e) => setForm({ ...form, rule_code: e.target.value })}
        />
        <input
          style={healthLocalFilterInputStyle}
          placeholder="pais"
          value={form.country_code}
          onChange={(e) => setForm({ ...form, country_code: e.target.value })}
        />
        <input
          style={healthLocalFilterInputStyle}
          placeholder="metodo"
          value={form.payment_method}
          onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
        />
        <input
          style={healthLocalFilterInputStyle}
          placeholder="PSP primario"
          value={form.primary_player_code}
          onChange={(e) => setForm({ ...form, primary_player_code: e.target.value })}
        />
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
            <span>{r.rule_code}</span>
            <span>
              <button
                type="button"
                style={{ fontSize: 11 }}
                onClick={() => {
                  setEditingId(r.id);
                  setForm({
                    rule_code: r.rule_code,
                    country_code: r.country_code,
                    payment_method: r.payment_method,
                    primary_player_code: r.primary_player_code,
                    fallback_player_code: r.fallback_player_code || "",
                    priority: String(r.priority),
                    rationale: r.rationale || "",
                    is_active: r.is_active,
                  });
                }}
              >
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
