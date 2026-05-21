
import React, { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const BASE = import.meta.env.VITE_LOCKER_CREATE_BASE_URL || "/api/lc";
const PAGE_VERSION = "ops/lockers/create v0.2-health-shell";

const DEFAULT_SLOTS = [
  { slot_size: "P", slot_count: 10, available_count: 10, width_mm: 100, height_mm: 100, depth_mm: 400, max_weight_g: 2000 },
  { slot_size: "M", slot_count: 10, available_count: 10, width_mm: 200, height_mm: 200, depth_mm: 400, max_weight_g: 5000 },
  { slot_size: "G", slot_count: 10, available_count: 10, width_mm: 300, height_mm: 400, depth_mm: 400, max_weight_g: 10000 },
];

const emptyForm = () => ({
  id: "",
  display_name: "",
  region: "PR",
  city: "",
  state: "PR",
  country: "BR",
  timezone: "America/Sao_Paulo",
  operator_id: "OP-ELLAN-001",
  temperature_zone: "AMBIENT",
  security_level: "STANDARD",
  has_camera: false,
  has_alarm: false,
  has_kiosk: true,
  has_printer: false,
  has_card_reader: true,
  has_nfc: false,
  copy_product_configs_from: "SP-OSASCO-CENTRO-LK-001",
});

function parseError(payload, fallback = "Falha na API locker-create.") {
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
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8015).`;
  }
  return raw;
}

const LOCKERS_API = `${BASE}/v1/locker-create/lockers`;

export default function OpsLockerCreatePage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [form, setForm] = useState(emptyForm);
  const [bulkJson, setBulkJson] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [lastApiKey, setLastApiKey] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const headers = useMemo(
    () => ({
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }),
    [token],
  );

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const r = await fetch(LOCKERS_API, { headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setItems(Array.isArray(j.lockers) ? j.lockers : []);
    } catch (e) {
      setErr(normalizeNetworkError(e, LOCKERS_API));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [token, headers]);

  const createOne = async () => {
    if (!token || !canMutate) return;
    const id = String(form.id || "").trim();
    const display_name = String(form.display_name || "").trim();
    const city = String(form.city || "").trim();
    if (!id || !display_name || !city) {
      setErr("id, display_name e city sao obrigatorios.");
      return;
    }
    setErr("");
    setOk("");
    setLoading(true);
    try {
      const body = {
        ...form,
        id,
        display_name,
        city,
        state: String(form.state || "").trim(),
        region: String(form.region || "").trim(),
        slot_configs: DEFAULT_SLOTS,
      };
      const r = await fetch(LOCKERS_API, { method: "POST", headers, body: JSON.stringify(body) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Locker ${j.id} criado (${j.slots_count} slots).`);
      setSelectedId(j.id);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, LOCKERS_API));
    } finally {
      setLoading(false);
    }
  };

  const bulkCreate = async () => {
    if (!token || !canMutate) return;
    setErr("");
    setOk("");
    setLoading(true);
    try {
      const lockers = JSON.parse(String(bulkJson || "[]"));
      if (!Array.isArray(lockers)) throw new Error("JSON deve ser um array de lockers.");
      const r = await fetch(`${LOCKERS_API}/bulk`, {
        method: "POST",
        headers,
        body: JSON.stringify({ lockers }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Bulk: ${(j.created || []).length} criados, ${(j.failed || []).length} falhas.`);
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const saveWebhook = async () => {
    const lid = String(selectedId || "").trim();
    const url = String(webhookUrl || "").trim();
    if (!token || !canMutate || !lid || !url) return;
    setErr("");
    setOk("");
    setLoading(true);
    try {
      const r = await fetch(`${LOCKERS_API}/${encodeURIComponent(lid)}/webhook`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          url,
          secret: webhookSecret || undefined,
          events: ["locker.created", "locker.updated", "locker.slot_changed"],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Webhook configurado para ${lid}.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${LOCKERS_API}/{id}/webhook`));
    } finally {
      setLoading(false);
    }
  };

  const rotateKey = async () => {
    const lid = String(selectedId || "").trim();
    if (!token || !canMutate || !lid) return;
    setErr("");
    setOk("");
    setLoading(true);
    try {
      const r = await fetch(`${LOCKERS_API}/${encodeURIComponent(lid)}/api-keys/rotate`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${LOCKERS_API}/{id}/api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const totalSlots = DEFAULT_SLOTS.reduce((acc, s) => acc + (s.slot_count || 0), 0);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={crossShortcutStyle}>
          <Link to="/ops/lockers/product-configs" style={crossShortcutLinkStyle}>
            Locker × categoria
          </Link>
          <Link to="/ops/health" style={{ ...crossShortcutLinkStyle, marginLeft: 8 }}>
            Saude operacional
          </Link>
        </div>
        <div style={headerRowStyle}>
          <div>
            <OpsPageTitleHeader
              title="OPS — Criar locker(s)"
              versionLabel={PAGE_VERSION}
              versionTo="/ops/auth/policy/versioning"
              containerStyle={{ marginBottom: 0 }}
              titleStyle={{ margin: 0 }}
            />
            <p style={mutedTextStyle}>
              CRUD + bulk + webhook + rotacao API key — <code style={{ color: "#e2e8f0" }}>{LOCKERS_API}</code> — role{" "}
              <code style={{ color: "#e2e8f0" }}>admin_operacao</code> para escrita.
            </p>
          </div>
        </div>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Novo equipamento</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              id
              <input
                value={form.id}
                onChange={(e) => setForm((f) => ({ ...f, id: e.target.value }))}
                style={healthLocalFilterInputStyle}
                placeholder="PR-CAPITAL-SANTAFELICIDADE-LK-001"
              />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              display_name
              <input
                value={form.display_name}
                onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
                style={healthLocalFilterInputStyle}
              />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              region
              <input value={form.region} onChange={(e) => setForm((f) => ({ ...f, region: e.target.value }))} style={healthLocalFilterInputStyle} />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              city
              <input value={form.city} onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))} style={healthLocalFilterInputStyle} />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              state
              <input value={form.state} onChange={(e) => setForm((f) => ({ ...f, state: e.target.value }))} style={healthLocalFilterInputStyle} />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              operator_id
              <input
                value={form.operator_id}
                onChange={(e) => setForm((f) => ({ ...f, operator_id: e.target.value }))}
                style={healthLocalFilterInputStyle}
              />
            </label>
            <label style={{ ...healthLocalFilterFieldStyle, gridColumn: "1 / -1" }}>
              copy_product_configs_from
              <input
                value={form.copy_product_configs_from}
                onChange={(e) => setForm((f) => ({ ...f, copy_product_configs_from: e.target.value }))}
                style={healthLocalFilterInputStyle}
              />
            </label>
          </div>
          <p style={summary24hHintStyle}>Slots padrao P/M/G: {totalSlots} gavetas (modelo_dados.txt).</p>
          <div style={flagsRowStyle}>
            {[
              ["has_kiosk", "kiosk"],
              ["has_card_reader", "card_reader"],
              ["has_camera", "camera"],
              ["has_alarm", "alarm"],
              ["has_printer", "printer"],
              ["has_nfc", "nfc"],
            ].map(([key, label]) => (
              <label key={key} style={flagLabelStyle}>
                <input
                  type="checkbox"
                  checked={Boolean(form[key])}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.checked }))}
                />
                {label}
              </label>
            ))}
          </div>
          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !token}>
              {loading ? "Atualizando..." : "Listar"}
            </button>
            <button type="button" style={buttonPrimaryStyle} onClick={() => void createOne()} disabled={loading || !token || !canMutate}>
              Criar locker
            </button>
          </div>
        </section>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Bulk (JSON array)</h3>
          </div>
          <textarea
            value={bulkJson}
            onChange={(e) => setBulkJson(e.target.value)}
            style={bulkTextStyle}
            placeholder={'[{"id":"LK-002","display_name":"…","region":"SP","city":"Osasco","state":"SP"}]'}
          />
          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void bulkCreate()} disabled={!bulkJson.trim() || !canMutate}>
              Enviar bulk
            </button>
          </div>
        </section>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Webhook e API key</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              locker_id
              <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} style={healthLocalFilterInputStyle}>
                <option value="">— selecione —</option>
                {items.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.id}
                  </option>
                ))}
              </select>
            </label>
            <label style={healthLocalFilterFieldStyle}>
              webhook URL
              <input value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} style={healthLocalFilterInputStyle} />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              secret (opcional)
              <input value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} style={healthLocalFilterInputStyle} />
            </label>
          </div>
          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void saveWebhook()} disabled={!selectedId || !webhookUrl || !canMutate}>
              Salvar webhook
            </button>
            <button type="button" style={buttonGhostStyle} onClick={() => void rotateKey()} disabled={!selectedId || !canMutate}>
              Rotacionar API key
            </button>
          </div>
          {lastApiKey ? (
            <p style={apiKeyBannerStyle}>
              API key: <code>{lastApiKey}</code>
            </p>
          ) : null}
        </section>

        {err ? (
          <div style={criticalBannerStyle} role="alert">
            {err}
          </div>
        ) : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}

        {!token ? <p style={summary24hHintStyle}>Faca login com perfil admin_operacao.</p> : null}
        {token && !canMutate ? <p style={summary24hHintStyle}>Escrita exige admin_operacao.</p> : null}
        {token && !loading && !items.length && !err ? <p style={summary24hHintStyle}>Nenhum locker listado.</p> : null}

        {items.length > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Lockers ({items.length})</h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["id", "display_name", "region", "city", "slots", "disp.", "ativo", "temp", "operador"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((r) => (
                    <tr key={r.id}>
                      <td style={tdStyle}>
                        <code>{r.id}</code>
                      </td>
                      <td style={tdStyle}>{r.display_name}</td>
                      <td style={tdStyle}>{r.region}</td>
                      <td style={tdStyle}>{r.city || "—"}</td>
                      <td style={tdStyle}>{r.slots_count}</td>
                      <td style={tdStyle}>{r.slots_available}</td>
                      <td style={tdStyle}>{r.active ? "Y" : "N"}</td>
                      <td style={tdStyle}>{r.temperature_zone}</td>
                      <td style={tdStyle}>{r.operator_id || "—"}</td>
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
  flexWrap: "wrap",
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

const buttonPrimaryStyle = {
  ...buttonGhostStyle,
  border: "1px solid rgba(34,197,94,0.55)",
  background: "rgba(22,101,52,0.35)",
  color: "#bbf7d0",
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

const okBannerStyle = {
  ...summary24hHintStyle,
  color: "#86efac",
  fontWeight: 600,
  marginTop: 8,
};

const apiKeyBannerStyle = {
  ...summary24hHintStyle,
  wordBreak: "break-all",
  padding: 8,
  borderRadius: 8,
  border: "1px solid rgba(251,191,36,0.5)",
  background: "rgba(120,53,15,0.25)",
};

const bulkTextStyle = {
  width: "100%",
  minHeight: 100,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.5)",
  background: "#0b0f14",
  color: "#e2e8f0",
  fontFamily: "ui-monospace, monospace",
  fontSize: 11,
  boxSizing: "border-box",
};

const flagsRowStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: 12,
};

const flagLabelStyle = {
  display: "flex",
  alignItems: "center",
  gap: 6,
  fontSize: 12,
  color: "#cbd5e1",
};

const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 720, fontSize: 12 };
const thStyle = { textAlign: "left", borderBottom: "1px solid #444", padding: 8, color: "#cbd5e1" };
const tdStyle = { padding: 8, borderTop: "1px solid #333", color: "#e2e8f0", verticalAlign: "top" };
