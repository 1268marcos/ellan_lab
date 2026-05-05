
import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { getOrderLifecycleBase, olFetch } from "../utils/orderLifecycleInternalApi";

const PAGE_VERSION = "ops/order/executive-summary v0.4.0-health-shell";

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

const predictiveReviewStatusStyle = {
  color: "#e2e8f0",
  fontSize: 12,
  fontWeight: 700,
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

const summary24hGridStyle = {
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
};

const summary24hItemStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.3)",
  background: "rgba(15,23,42,0.35)",
  padding: "8px 10px",
  display: "grid",
  gap: 2,
};

const summary24hValueStyle = {
  color: "#f8fafc",
  fontSize: 18,
  fontWeight: 800,
};

const summary24hLabelStyle = {
  color: "#cbd5e1",
  fontSize: 12,
};

const summary24hHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const gateDrilldownLinkStyle = {
  marginTop: 8,
  width: "fit-content",
  color: "#93c5fd",
  textDecoration: "underline",
  fontSize: 12,
  fontWeight: 600,
};

const inlineDrilldownLinkStyle = {
  ...gateDrilldownLinkStyle,
  marginTop: 0,
  display: "inline",
};

const healthCollapsibleStyle = {
  marginTop: 8,
  borderRadius: 10,
  border: "1px dashed rgba(148,163,184,0.35)",
  background: "rgba(2,6,23,0.24)",
  padding: 8,
};

const healthCollapsibleSummaryStyle = {
  cursor: "pointer",
  color: "#bfdbfe",
  fontSize: 13,
  fontWeight: 700,
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

const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 12 };
const thStyle = { textAlign: "left", borderBottom: "1px solid #444", padding: 8, color: "#cbd5e1" };
const tdStyle = { padding: 8, borderTop: "1px solid #333", color: "#e2e8f0" };

const preBlockStyle = {
  background: "#0b0f14",
  border: "1px solid rgba(255,255,255,0.14)",
  borderRadius: 10,
  padding: 12,
  overflow: "auto",
  margin: 0,
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
  fontSize: 12,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  color: "#e2e8f0",
};

function fmtPct(v, digits = 2) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return `${n.toFixed(digits)}%`;
}

function fmtInt(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return String(Math.round(n));
}

function fmtMin(v, digits = 2) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return `${n.toFixed(digits)} min`;
}

function fmtMetricValue(metric, value) {
  const m = String(metric || "");
  if (m.includes("rate") || m.endsWith("_rate")) return fmtPct(value);
  if (m.includes("minutes") || m.includes("minute")) return fmtMin(value);
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return String(n);
}

const badgeBase = {
  display: "inline-flex",
  padding: "4px 8px",
  borderRadius: 999,
  fontSize: 11,
  fontWeight: 700,
};

function badgeStyleForSeverity(severity) {
  const s = String(severity || "").toUpperCase();
  if (s === "HIGH" || s === "CRITICAL" || s === "INCIDENT") {
    return { ...badgeBase, background: "rgba(239,68,68,0.22)", border: "1px solid rgba(248,113,113,0.55)", color: "#fecaca" };
  }
  if (s === "MEDIUM" || s === "MED" || s === "WARN" || s === "WARNING") {
    return { ...badgeBase, background: "rgba(245,158,11,0.18)", border: "1px solid rgba(251,191,36,0.5)", color: "#fde68a" };
  }
  return { ...badgeBase, background: "rgba(34,197,94,0.16)", border: "1px solid rgba(74,222,128,0.45)", color: "#bbf7d0" };
}

function actionCardStyle(severity) {
  const s = String(severity || "").toUpperCase();
  const border =
    s === "HIGH" || s === "CRITICAL"
      ? "1px solid rgba(248,113,113,0.45)"
      : s === "MEDIUM" || s === "WARN" || s === "WARNING"
        ? "1px solid rgba(251,191,36,0.45)"
        : "1px solid rgba(148,163,184,0.3)";
  return { ...summary24hItemStyle, border, display: "grid", gap: 10 };
}

function SectionRanking({ section }) {
  const title = section?.title || "Ranking";
  if (!section || !Array.isArray(section.items) || section.items.length === 0) {
    return (
      <p style={{ ...summary24hHintStyle, margin: 0 }} role="status">
        Sem linhas em «{title}».
      </p>
    );
  }
  return (
    <div style={{ overflow: "auto", maxHeight: "55vh" }}>
      <table style={tableStyle}>
        <thead>
          <tr>
            {["#", "Dimensão", "Rótulo", "Métrica", "Valor", "Resgate", "Expir.", "Sev."].map((h) => (
              <th key={h} style={thStyle}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {section.items.map((row) => (
            <tr key={`${section.title}-${row.rank}-${row.dimension_value ?? "x"}`}>
              <td style={tdStyle}>{row.rank}</td>
              <td style={tdStyle}>{row.dimension_value ?? "—"}</td>
              <td style={tdStyle}>{row.label}</td>
              <td style={{ ...tdStyle, fontFamily: "ui-monospace, monospace", fontSize: 11 }}>
                {row.metric}
              </td>
              <td style={tdStyle}>{fmtMetricValue(row.metric, row.metric_value)}</td>
              <td style={tdStyle}>{fmtPct(row.redemption_rate)}</td>
              <td style={tdStyle}>{fmtPct(row.expiration_rate)}</td>
              <td style={tdStyle}>
                <span style={badgeStyleForSeverity(row.severity)}>{row.severity}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function sectionGroupSlug(title) {
  return String(title || "group")
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "");
}

function SectionGroup({ groupTitle, sections }) {
  if (!Array.isArray(sections) || sections.length === 0) return null;
  const gid = `exec-group-${sectionGroupSlug(groupTitle)}`;
  return (
    <section style={opsSanityCardStyle} aria-labelledby={gid}>
      <div style={summary24hHeaderStyle}>
        <h3 style={{ margin: 0, fontSize: 14 }} id={gid}>
          {groupTitle}
        </h3>
      </div>
      {sections.map((sec, si) => (
        <div key={`${sectionGroupSlug(groupTitle)}-${sec.title}-${si}`}>
          <h3 style={{ marginTop: si === 0 ? 0 : 16, marginBottom: 8, fontSize: 14, color: "#e2e8f0" }}>{sec.title}</h3>
          <SectionRanking section={sec} />
        </div>
      ))}
    </section>
  );
}

function TrendColumn({ title, items }) {
  const list = Array.isArray(items) ? items : [];
  return (
    <div style={{ ...summary24hItemStyle, gap: 8 }}>
      <div style={{ fontWeight: 800, marginBottom: 8, fontSize: 13, color: "#f8fafc" }}>{title}</div>
      {list.length === 0 ? (
        <div style={summary24hHintStyle}>—</div>
      ) : (
        list.map((t, idx) => (
          <div key={`${title}-${String(t.region ?? "r")}-${idx}`} style={{ ...summary24hHintStyle, marginBottom: 8 }}>
            <strong style={{ color: "#f5f7fa" }}>{t.region ?? "—"}</strong>
            {t.label ? ` — ${t.label}` : ""}
            <br />
            Δ resgate: {fmtPct(t.delta_redemption_rate, 3)} · atual {fmtPct(t.current_redemption_rate)} · amostra{" "}
            {fmtInt(t.current_terminal_pickups)}{" "}
            <span style={{ ...badgeStyleForSeverity(t.severity), marginLeft: 6 }}>{t.severity}</span>
          </div>
        ))
      )}
    </div>
  );
}

export default function OrderPickupExecutiveSummaryPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [copyStatus, setCopyStatus] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams();
      const j = await olFetch(`/internal/analytics/pickup-executive-summary?${q.toString()}`);
      setData(j);
    } catch (e) {
      setError(e?.message || "Falha ao carregar resumo executivo");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- mount fetch for executive summary API
    void load();
  }, [load]);

  async function handleCopyJson() {
    if (!data) return;
    const text = JSON.stringify(data, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus("JSON copiado.");
    } catch {
      setCopyStatus("Falha ao copiar.");
    }
    window.setTimeout(() => setCopyStatus(""), 2400);
  }

  const overview = data?.overview;

  return (
    <div style={pageStyle} data-testid="ops-order-pickup-executive-page">
      <section style={cardStyle}>
        <div style={crossShortcutStyle}>
          <Link to="/ops/health" style={crossShortcutLinkStyle}>
            Ir para saúde operacional
          </Link>
        </div>
        <div style={headerRowStyle}>
          <div>
            <OpsPageTitleHeader
              title="OPS — Order / resumo executivo (pickup)"
              versionLabel={PAGE_VERSION}
              versionTo="/ops/auth/policy/versioning"
              containerStyle={{ marginBottom: 0 }}
              titleStyle={{ margin: 0 }}
            />
            <p style={mutedTextStyle}>
              Resumo executivo pickup — endpoint{" "}
              <code style={{ color: "#e2e8f0" }}>GET /internal/analytics/pickup-executive-summary</code>. Drill-down e filtros:{" "}
              <Link to="/ops/order/pickup-health" style={inlineDrilldownLinkStyle}>
                OPS / order / pickup-health
              </Link>
              .
            </p>
          </div>
          <div style={toolbarStyle}>
            <button type="button" onClick={() => void load()} style={buttonGhostStyle} disabled={loading}>
              {loading ? "Atualizando..." : "Atualizar agora"}
            </button>
            <button type="button" onClick={() => void handleCopyJson()} style={buttonGhostStyle} disabled={!data || Boolean(error)}>
              Copiar JSON
            </button>
          </div>
        </div>
        {copyStatus ? <small style={predictiveReviewStatusStyle}>{copyStatus}</small> : null}

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Contexto da API</h3>
          </div>
          <div style={summary24hGridStyle}>
            <article style={summary24hItemStyle}>
              <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{getOrderLifecycleBase()}</strong>
              <small style={summary24hLabelStyle}>Base</small>
            </article>
            <article style={summary24hItemStyle}>
              <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>VITE_INTERNAL_TOKEN</strong>
              <small style={summary24hLabelStyle}>Token (env)</small>
            </article>
            <article style={summary24hItemStyle}>
              <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>X-Internal-Token</strong>
              <small style={summary24hLabelStyle}>Header</small>
            </article>
            <article style={summary24hItemStyle}>
              <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{loading ? "Atualizando..." : "pronto"}</strong>
              <small style={summary24hLabelStyle}>Status</small>
            </article>
          </div>
        </section>

        {error ? (
          <div style={criticalBannerStyle} role="alert">
            {error}
          </div>
        ) : null}

        {data && !error ? (
          <>
            {data.window_start || data.window_end ? (
              <section style={opsSanityCardStyle}>
                <div style={summary24hHeaderStyle}>
                  <h3 style={{ margin: 0, fontSize: 14 }}>Janela</h3>
                </div>
                <p style={{ ...summary24hHintStyle, margin: 0 }}>
                  <strong style={{ color: "#f5f7fa" }}>{data.window_start ?? "—"}</strong> →{" "}
                  <strong style={{ color: "#f5f7fa" }}>{data.window_end ?? "—"}</strong>
                </p>
              </section>
            ) : null}

            {overview ? (
              <section style={opsSanityCardStyle}>
                <div style={summary24hHeaderStyle}>
                  <h3 style={{ margin: 0, fontSize: 14 }}>Panorama</h3>
                </div>
                <div style={summary24hGridStyle}>
                  {[
                    ["Pickups terminais", fmtInt(overview.total_terminal_pickups)],
                    ["Resgatados", fmtInt(overview.redeemed_pickups)],
                    ["Expirados", fmtInt(overview.expired_pickups)],
                    ["Cancelados", fmtInt(overview.cancelled_pickups)],
                    ["Taxa resgate", fmtPct(overview.redemption_rate)],
                    ["Taxa expiração", fmtPct(overview.expiration_rate)],
                    ["Taxa cancelamento", fmtPct(overview.cancellation_rate)],
                    ["Criado → pronto", fmtMin(overview.avg_minutes_created_to_ready)],
                    ["Pronto → resgate", fmtMin(overview.avg_minutes_ready_to_redeemed)],
                    ["Porta → resgate", fmtMin(overview.avg_minutes_door_opened_to_redeemed)],
                    ["Porta aberta → fechada", fmtMin(overview.avg_minutes_door_opened_to_door_closed)],
                  ].map(([label, val]) => (
                    <article key={label} style={summary24hItemStyle}>
                      <strong style={summary24hValueStyle}>{val}</strong>
                      <small style={summary24hLabelStyle}>{label}</small>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            <section style={opsSanityCardStyle}>
              <div style={summary24hHeaderStyle}>
                <h3 style={{ margin: 0, fontSize: 14 }}>Rankings principais</h3>
              </div>
              {data.worst_lockers?.title ? (
                <>
                  <h3 style={{ marginTop: 0, marginBottom: 8, fontSize: 14, color: "#e2e8f0" }}>{data.worst_lockers.title}</h3>
                  <SectionRanking section={data.worst_lockers} />
                </>
              ) : null}
              {data.best_sites?.title ? (
                <>
                  <h3 style={{ marginTop: 16, marginBottom: 8, fontSize: 14, color: "#e2e8f0" }}>{data.best_sites.title}</h3>
                  <SectionRanking section={data.best_sites} />
                </>
              ) : null}
              {data.critical_machines?.title ? (
                <>
                  <h3 style={{ marginTop: 16, marginBottom: 8, fontSize: 14, color: "#e2e8f0" }}>{data.critical_machines.title}</h3>
                  <SectionRanking section={data.critical_machines} />
                </>
              ) : null}
            </section>

            <SectionGroup groupTitle="Destaques positivos" sections={data.positive_highlights} />
            <SectionGroup groupTitle="Saturação" sections={data.saturation} />
            <SectionGroup groupTitle="Fiabilidade" sections={data.reliability} />

            <section style={opsSanityCardStyle}>
              <div style={summary24hHeaderStyle}>
                <h3 style={{ margin: 0, fontSize: 14 }}>Tendência por região</h3>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>
                <TrendColumn title="Em piora" items={data.worsening_regions_trend} />
                <TrendColumn title="Em melhoria" items={data.improving_regions_trend} />
                <TrendColumn title="Estáveis" items={data.stable_regions_trend} />
              </div>
            </section>

            {Array.isArray(data.actions) && data.actions.length > 0 ? (
              <section style={opsSanityCardStyle}>
                <div style={summary24hHeaderStyle}>
                  <h3 style={{ margin: 0, fontSize: 14 }}>Ações sugeridas</h3>
                </div>
                <div style={{ display: "grid", gap: 10 }}>
                  {data.actions.map((a, i) => (
                    <div key={`${a.title}-${i}`} style={actionCardStyle(a.severity)}>
                      <div style={{ fontWeight: 800, fontSize: 14, color: "#f8fafc" }}>{a.title}</div>
                      <div style={summary24hHintStyle}>
                        <span style={badgeStyleForSeverity(a.severity)}>{a.severity}</span>
                        {a.dimension ? ` · ${a.dimension}` : ""}
                        {a.dimension_value != null && a.dimension_value !== "" ? ` · ${a.dimension_value}` : ""}
                        {a.recommended_action ? ` · ${a.recommended_action}` : ""}
                      </div>
                      <p style={{ margin: 0, fontSize: 13, color: "#e2e8f0", lineHeight: 1.5 }}>{a.reason}</p>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            {Array.isArray(data.insights) && data.insights.length > 0 ? (
              <section style={opsSanityCardStyle}>
                <div style={summary24hHeaderStyle}>
                  <h3 style={{ margin: 0, fontSize: 14 }}>Insights</h3>
                </div>
                <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.55, color: "#e2e8f0" }}>
                  {data.insights.map((line, idx) => (
                    <li key={idx} style={{ marginBottom: 6 }}>
                      {line}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {data.filters && Object.keys(data.filters).length > 0 ? (
              <section style={opsSanityCardStyle}>
                <div style={summary24hHeaderStyle}>
                  <h3 style={{ margin: 0, fontSize: 14 }}>Filtros (API)</h3>
                </div>
                <pre style={{ ...preBlockStyle, maxHeight: "24vh" }}>{JSON.stringify(data.filters, null, 2)}</pre>
              </section>
            ) : null}

            <section style={opsSanityCardStyle}>
              <details style={healthCollapsibleStyle}>
                <summary style={healthCollapsibleSummaryStyle}>Payload bruto (JSON)</summary>
                <pre style={{ ...preBlockStyle, maxHeight: "50vh", marginTop: 8 }}>{JSON.stringify(data, null, 2)}</pre>
              </details>
            </section>
          </>
        ) : !loading && !error ? (
          <section style={opsSanityCardStyle}>
            <small style={{ ...summary24hHintStyle, display: "block", textAlign: "center" }}>
              Sem dados. Verifique o order lifecycle e o token interno.
            </small>
          </section>
        ) : null}
      </section>
    </div>
  );
}

