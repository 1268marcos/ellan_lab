import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const ep = `${BASE}/pricing/rules`;

function errMsg(d, fb) {
  if (!d) return fb;
  if (typeof d?.detail === "string" && d.detail.trim()) return d.detail.trim();
  if (d?.detail?.message) return String(d.detail.message);
  return fb;
}

export default function OpsPricingRulesPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [region, setRegion] = useState("");
  const [productCategory, setProductCategory] = useState("");
  const [isActive, setIsActive] = useState("");
  const filt = useRef({ region: "", productCategory: "", isActive: "" });
  filt.current = { region, productCategory, isActive };
  const [form, setForm] = useState({
    region: "",
    locker_id: "",
    product_category: "",
    valid_from: "",
    valid_until: "",
    base_amount_cents: "100",
    discount_pct: "0",
    min_amount_cents: "",
    max_amount_cents: "",
    metadata_json: "{}",
  });
  const auth = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const load = useCallback(async () => {
    if (!token) return;
    const { region: r0, productCategory: c0, isActive: a0 } = filt.current;
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams();
      if (r0.trim()) q.set("region", r0.trim());
      if (c0.trim()) q.set("product_category", c0.trim());
      if (a0 === "true" || a0 === "false") q.set("is_active", a0);
      const r = await fetch(`${ep}?${q}`, { headers: { Accept: "application/json", ...auth } });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errMsg(d, "Falha ao listar."));
      setItems(Array.isArray(d.items) ? d.items : []);
    } catch (e) {
      setError(String(e.message || e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [token, auth]);

  useEffect(() => {
    if (token) void load();
  }, [token, load]);

  const create = async () => {
    if (!token || !form.valid_from) return;
    setError("");
    try {
      const body = {
        region: form.region || null,
        locker_id: form.locker_id || null,
        product_category: form.product_category || null,
        valid_from: new Date(form.valid_from).toISOString(),
        valid_until: form.valid_until ? new Date(form.valid_until).toISOString() : null,
        base_amount_cents: Number(form.base_amount_cents),
        discount_pct: Number(form.discount_pct || 0),
        min_amount_cents: form.min_amount_cents ? Number(form.min_amount_cents) : null,
        max_amount_cents: form.max_amount_cents ? Number(form.max_amount_cents) : null,
        metadata_json: JSON.parse(form.metadata_json || "{}"),
      };
      const r = await fetch(ep, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json", ...auth },
        body: JSON.stringify(body),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errMsg(d, "Falha ao criar."));
      await load();
    } catch (e) {
      setError(String(e.message || e));
    }
  };

  const patchActive = async (id, next) => {
    if (!token) return;
    setError("");
    try {
      const r = await fetch(`${ep}/${encodeURIComponent(id)}`, {
        method: "PATCH",
        headers: { Accept: "application/json", "Content-Type": "application/json", ...auth },
        body: JSON.stringify({ is_active: next }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(errMsg(d, "Falha ao atualizar."));
      await load();
    } catch (e) {
      setError(String(e.message || e));
    }
  };

  return (
    <div style={S.page}>
      <section style={S.card}>
        <OpsPageTitleHeader title="OPS — Pricing rules" />
        <p style={S.muted}>
          <code>pricing_rules</code> · API <code>{ep}</code>
        </p>
        {!token ? <p style={S.muted}>Login necessário.</p> : null}
        <div style={S.row}>
          <input style={S.inp} placeholder="region" value={region} onChange={(e) => setRegion(e.target.value)} />
          <input style={S.inp} placeholder="product_category" value={productCategory} onChange={(e) => setProductCategory(e.target.value)} />
          <select style={S.inp} value={isActive} onChange={(e) => setIsActive(e.target.value)}>
            <option value="">is_active (todos)</option>
            <option value="true">ativo</option>
            <option value="false">inativo</option>
          </select>
          <button type="button" style={S.btn} disabled={!token || loading} onClick={() => void load()}>
            {loading ? "…" : "Filtrar"}
          </button>
        </div>
        {error ? <pre style={S.err}>{error}</pre> : null}
        <h4 style={S.h4}>Nova regra</h4>
        <div style={{ ...S.row, flexWrap: "wrap" }}>
          {["region", "locker_id", "product_category"].map((k) => (
            <input key={k} style={S.inp} placeholder={k} value={form[k]} onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.value }))} />
          ))}
          <input style={S.inp} type="datetime-local" value={form.valid_from} onChange={(e) => setForm((f) => ({ ...f, valid_from: e.target.value }))} />
          <input style={S.inp} type="datetime-local" value={form.valid_until} onChange={(e) => setForm((f) => ({ ...f, valid_until: e.target.value }))} />
          <input style={S.inpSm} placeholder="base_cents" value={form.base_amount_cents} onChange={(e) => setForm((f) => ({ ...f, base_amount_cents: e.target.value }))} />
          <input style={S.inpSm} placeholder="disc%" value={form.discount_pct} onChange={(e) => setForm((f) => ({ ...f, discount_pct: e.target.value }))} />
          <button type="button" style={S.btn} disabled={!token} onClick={() => void create()}>
            Criar
          </button>
        </div>
        <textarea style={{ ...S.inp, width: "100%", minHeight: 48 }} value={form.metadata_json} onChange={(e) => setForm((f) => ({ ...f, metadata_json: e.target.value }))} />
        <div style={{ overflowX: "auto", marginTop: 12 }}>
          <table style={S.tbl}>
            <thead>
              <tr>
                {["id", "region", "locker", "cat", "from→until", "base¢", "%", "active", ""].map((h) => (
                  <th key={h} style={S.th}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id}>
                  <td style={S.td}><code>{it.id.slice(0, 8)}…</code></td>
                  <td style={S.td}>{it.region || "—"}</td>
                  <td style={S.td}><code>{(it.locker_id || "").slice(0, 8) || "—"}</code></td>
                  <td style={S.td}>{it.product_category || "—"}</td>
                  <td style={S.td}>{String(it.valid_from).slice(0, 16)} → {it.valid_until ? String(it.valid_until).slice(0, 16) : "∞"}</td>
                  <td style={S.td}>{it.base_amount_cents}</td>
                  <td style={S.td}>{it.discount_pct}</td>
                  <td style={S.td}>{it.is_active ? "sim" : "não"}</td>
                  <td style={S.td}>
                    <button type="button" style={S.btnSm} onClick={() => void patchActive(it.id, !it.is_active)}>
                      {it.is_active ? "Off" : "On"}
                    </button>
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

const S = {
  page: { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui,sans-serif" },
  card: { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 },
  muted: { color: "#94A3B8", fontSize: 13 },
  row: { display: "flex", gap: 8, marginTop: 10, alignItems: "center" },
  inp: { padding: 8, borderRadius: 8, border: "1px solid #475569", background: "#0f172a", color: "#e2e8f0", minWidth: 120 },
  inpSm: { padding: 8, borderRadius: 8, border: "1px solid #475569", background: "#0f172a", color: "#e2e8f0", width: 72 },
  btn: { padding: "8px 12px", borderRadius: 8, border: "none", background: "#1d4ed8", color: "#fff", fontWeight: 700, cursor: "pointer" },
  btnSm: { padding: "4px 8px", borderRadius: 6, border: "1px solid #64748b", background: "#1e293b", color: "#e2e8f0", cursor: "pointer", fontSize: 11 },
  err: { marginTop: 8, padding: 8, background: "rgba(220,38,38,.12)", color: "#fca5a5", borderRadius: 8, fontSize: 12 },
  h4: { margin: "16px 0 0", fontSize: 13, color: "#94a3b8" },
  tbl: { width: "100%", borderCollapse: "collapse", fontSize: 12 },
  th: { textAlign: "left", padding: 8, borderBottom: "1px solid #334155", color: "#94a3b8" },
  td: { padding: 8, borderBottom: "1px solid #1e293b", verticalAlign: "top" },
};
