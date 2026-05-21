
import React, { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const PAGE_VERSION = "ops/lockers/product-configs v0.2-health-shell";

export default function OpsLockerProductConfigPage() {
  const { token } = useAuth();
  const [lockerId, setLockerId] = useState("");
  const [category, setCategory] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const headers = useMemo(
    () => ({ Accept: "application/json", "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token]
  );

  const load = useCallback(async () => {
    const lid = String(lockerId || "").trim();
    if (!token || !lid) return;
    setLoading(true);
    setErr("");
    try {
      const u = new URL(`${BASE}/locker/product-configs`, window.location.origin);
      u.searchParams.set("locker_id", lid);
      const r = await fetch(u.toString(), { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail?.message === "string" ? j.detail.message : r.statusText);
      setItems(Array.isArray(j.items) ? j.items : []);
    } catch (e) {
      setErr(String(e.message || e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [token, lockerId, headers]);

  const add = async () => {
    const lid = String(lockerId || "").trim();
    const cat = String(category || "").trim();
    if (!token || !lid || !cat) return;
    setErr("");
    try {
      const r = await fetch(`${BASE}/locker/product-configs`, {
        method: "POST",
        headers,
        body: JSON.stringify({ locker_id: lid, category: cat, allowed: true, temperature_zone: "ANY" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j?.detail?.message === "string" ? j.detail.message : JSON.stringify(j.detail || j));
      setCategory("");
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const del = async (id) => {
    if (!token) return;
    setErr("");
    try {
      const r = await fetch(`${BASE}/locker/product-configs/${id}`, { method: "DELETE", headers: { Authorization: headers.Authorization } });
      if (!r.ok && r.status !== 204) {
        const j = await r.json().catch(() => ({}));
        throw new Error(typeof j?.detail?.message === "string" ? j.detail.message : r.statusText);
      }
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={crossShortcutStyle}>
          <Link to="/ops/lockers/create" style={crossShortcutLinkStyle}>
            Criar locker(s)
          </Link>
          <Link to="/ops/health" style={{ ...crossShortcutLinkStyle, marginLeft: 8 }}>
            Ir para saúde operacional
          </Link>
        </div>
        <div style={headerRowStyle}>
          <div>
            <OpsPageTitleHeader
              title="OPS — Locker × categoria (product_locker_configs)"
              versionLabel={PAGE_VERSION}
              versionTo="/ops/auth/policy/versioning"
              containerStyle={{ marginBottom: 0 }}
              titleStyle={{ margin: 0 }}
            />
            <p style={mutedTextStyle}>
              GET/POST/DELETE <code style={{ color: "#e2e8f0" }}>{BASE}/locker/product-configs</code> — role{" "}
              <code style={{ color: "#e2e8f0" }}>admin_operacao</code>.
            </p>
          </div>
        </div>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Consulta e associação</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              locker_id
              <input value={lockerId} onChange={(e) => setLockerId(e.target.value)} style={healthLocalFilterInputStyle} />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              category (nova associação)
              <input value={category} onChange={(e) => setCategory(e.target.value)} style={healthLocalFilterInputStyle} />
            </label>
          </div>
          <div style={toolbarStyle}>
            <button
              type="button"
              style={buttonGhostStyle}
              onClick={() => void load()}
              disabled={loading || !lockerId.trim()}
            >
              {loading ? "Atualizando..." : "Listar"}
            </button>
            <button type="button" style={buttonGhostStyle} onClick={() => void add()} disabled={!lockerId.trim() || !category.trim()}>
              Associar
            </button>
          </div>
        </section>

        {err ? (
          <div style={criticalBannerStyle} role="alert">
            {err}
          </div>
        ) : null}

        {!token ? <p style={summary24hHintStyle}>Faça login com perfil admin_operacao.</p> : null}
        {token && !loading && !items.length && !err ? <p style={summary24hHintStyle}>Nenhuma config para este locker.</p> : null}

        {items.length > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Itens</h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["id", "category", "sub", "allowed", "temp", "sig", "idChk", "g", "mm W/H/D", "haz", "frag", "pri", ""].map((h) => (
                      <th key={h || "act"} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((r) => (
                    <tr key={r.id}>
                      <td style={tdStyle}>{r.id}</td>
                      <td style={tdStyle}>{r.category}</td>
                      <td style={tdStyle}>{r.subcategory || "—"}</td>
                      <td style={tdStyle}>{r.allowed ? "Y" : "N"}</td>
                      <td style={tdStyle}>{r.temperature_zone}</td>
                      <td style={tdStyle}>{r.requires_signature ? "Y" : "N"}</td>
                      <td style={tdStyle}>{r.requires_id_check ? "Y" : "N"}</td>
                      <td style={tdStyle}>{r.max_weight_g ?? "—"}</td>
                      <td style={tdStyle}>{[r.max_width_mm, r.max_height_mm, r.max_depth_mm].map((x) => x ?? "—").join("/")}</td>
                      <td style={tdStyle}>{r.is_hazardous ? "Y" : "N"}</td>
                      <td style={tdStyle}>{r.is_fragile ? "Y" : "N"}</td>
                      <td style={tdStyle}>{r.priority}</td>
                      <td style={tdStyle}>
                        <button type="button" style={dangerButtonStyle} onClick={() => void del(r.id)}>
                          Excluir
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

const cardStyle = {
  width: "100%",
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const headerRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  alignItems: "flex-start",
  flexWrap: "wrap",
};

const crossShortcutStyle = {
  display: "flex",
  justifyContent: "flex-end",
  marginBottom: 10,
};

const crossShortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const labelStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle = {
  width: 90,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const healthLocalFilterRowStyle = {
  marginTop: 10,
  marginBottom: 8,
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  alignItems: "end",
};

const healthLocalFilterFieldStyle = {
  ...labelStyle,
  color: "#cbd5e1",
};

const healthLocalFilterInputStyle = {
  ...inputStyle,
  width: "100%",
  border: "1px solid rgba(148,163,184,0.5)",
};

const toolbarStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-end",
  flexWrap: "wrap",
};

const buttonGhostStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const dangerButtonStyle = {
  ...buttonGhostStyle,
  border: "1px solid rgba(248,113,113,0.65)",
  background: "rgba(127,29,29,0.28)",
  color: "#fecaca",
  fontSize: 11,
  padding: "4px 8px",
};

const opsSanityCardStyle = {
  marginTop: 6,
  borderRadius: 12,
  border: "1px solid rgba(59,130,246,0.45)",
  background: "rgba(30,58,138,0.2)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const summary24hHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const summary24hHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const criticalBannerStyle = {
  borderRadius: 10,
  border: "1px solid rgba(248,113,113,0.72)",
  background: "linear-gradient(180deg, rgba(127,29,29,0.58) 0%, rgba(127,29,29,0.3) 100%)",
  color: "#fecaca",
  padding: "10px 12px",
  fontWeight: 700,
  fontSize: 13,
};

const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 720, fontSize: 12 };
const thStyle = { textAlign: "left", borderBottom: "1px solid #444", padding: 8, color: "#cbd5e1" };
const tdStyle = { padding: 8, borderTop: "1px solid #333", color: "#e2e8f0", verticalAlign: "top" };

