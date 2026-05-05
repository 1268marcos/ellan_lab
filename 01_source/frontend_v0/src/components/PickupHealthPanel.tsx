
import React, { useEffect, useMemo, useState, type CSSProperties } from "react";

type SeverityKey = "normal" | "attention" | "critical" | "incident";

const severityMeta: Record<
  SeverityKey,
  { label: string; color: string; bg: string; border: string }
> = {
  normal: {
    label: "Normal",
    color: "#2e7d32",
    bg: "rgba(46,125,50,0.16)",
    border: "rgba(46,125,50,0.55)",
  },
  attention: {
    label: "Atenção",
    color: "#f9a825",
    bg: "rgba(249,168,37,0.16)",
    border: "rgba(249,168,37,0.55)",
  },
  critical: {
    label: "Crítico",
    color: "#ef6c00",
    bg: "rgba(239,108,0,0.16)",
    border: "rgba(239,108,0,0.55)",
  },
  incident: {
    label: "Incidente",
    color: "#b71c1c",
    bg: "rgba(183,28,28,0.18)",
    border: "rgba(183,28,28,0.65)",
  },
};

const entityTypeOptions = [
  { value: "all", label: "Todos" },
  { value: "locker", label: "Lockers" },
  { value: "machine", label: "Máquinas" },
  { value: "site", label: "Sites" },
  { value: "region", label: "Regiões" },
] as const;

type BadgeMeta = { bg: string; border: string };

function badgeStyle(meta?: Partial<BadgeMeta>): CSSProperties {
  const m: BadgeMeta = {
    bg: meta?.bg ?? "rgba(255,255,255,0.08)",
    border: meta?.border ?? "rgba(255,255,255,0.18)",
  };

  return {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "4px 8px",
    borderRadius: 999,
    border: `1px solid ${m.border}`,
    background: m.bg,
    fontSize: 11,
    fontWeight: 700,
    whiteSpace: "nowrap",
  };
}

type PickupHealthRankingItem = {
  entity_type?: string;
  entity_id?: string;
  severity_bucket?: string;
  priority_score?: number;
  health_score?: number;
  suggested_playbook?: string;
  tenant_id?: string;
  operator_id?: string;
  region?: string;
  locker_id?: string;
  machine_id?: string;
  site_id?: string;
  alerts?: string[];
  anomaly?: {
    alerts?: string[];
    predictive_risk?: boolean;
    abrupt_drop?: boolean;
    out_of_pattern?: boolean;
  };
  trend?: {
    direction?: string;
    delta?: number;
    current_rate?: number;
    previous_rate?: number;
  };
  signals?: { trend_direction?: string };
  metrics?: {
    total_terminal_pickups?: number;
    expiration_rate?: number;
    cancellation_rate?: number;
    avg_minutes_ready_to_redeemed?: number;
  };
};

function formatScore(value: unknown): string {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return n.toFixed(2);
}

function formatSlotEquipmentLine(item: PickupHealthRankingItem): string {
  if (String(item?.entity_type || "").toLowerCase() !== "slot") return "";
  const locker = item?.locker_id;
  const machine = item?.machine_id;
  const site = item?.site_id;
  const bits: string[] = [];
  if (locker) bits.push(`armário ${locker}`);
  if (machine) bits.push(`máquina ${machine}`);
  if (site) bits.push(`site ${site}`);
  if (!bits.length) return "sem vínculo nos fatos deste período";
  return bits.join(" · ");
}

function buildInternalHeaders(internalToken: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-Internal-Token": internalToken,
  };
}

export type PickupHealthPanelProps = {
  lifecycleBaseUrl: string;
  internalToken: string;
  region?: string;
  defaultEntityType?: string;
};

type PickupHealthPayload = {
  ranking?: PickupHealthRankingItem[];
  summary?: {
    total_entities?: number;
    healthy_count?: number;
    attention_count?: number;
    critical_count?: number;
    collapsed_count?: number;
  };
};

function isSeverityKey(s: string): s is SeverityKey {
  return s in severityMeta;
}

export default function PickupHealthPanel({
  lifecycleBaseUrl,
  internalToken,
  region,
  defaultEntityType = "locker",
}: PickupHealthPanelProps) {
  const [entityType, setEntityType] = useState(defaultEntityType);
  const [trendDaysWindow, setTrendDaysWindow] = useState(7);
  const [rankingLimit, setRankingLimit] = useState(20);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState<PickupHealthPayload | null>(null);

  const apiBase = useMemo(() => String(lifecycleBaseUrl || "").replace(/\/+$/, ""), [lifecycleBaseUrl]);

  async function load() {
    if (!apiBase) {
      setError("Base URL do order_lifecycle_service não informada.");
      return;
    }

    if (!internalToken) {
      setError("VITE_INTERNAL_TOKEN não configurado no frontend.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();
      params.set("entity_type", entityType);
      params.set("ranking_limit", String(rankingLimit));
      params.set("trend_days_window", String(trendDaysWindow));
      params.set("include_alerts", "true");

      if (region) {
        params.set("region", region);
      }

      const url = `${apiBase}/internal/analytics/pickup-health?${params.toString()}`;

      const res = await fetch(url, {
        method: "GET",
        headers: buildInternalHeaders(internalToken),
      });

      const text = await res.text();

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const json = (text ? JSON.parse(text) : {}) as PickupHealthPayload;
      setPayload(json);
    } catch (err: unknown) {
      setError(String(err instanceof Error ? err.message : err));
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload when query inputs change
  }, [apiBase, internalToken, region, entityType, rankingLimit, trendDaysWindow]);

  const ranking = Array.isArray(payload?.ranking) ? payload.ranking : [];
  const summary = payload?.summary ?? {};

  return (
    <section
      style={{
        marginTop: 16,
        padding: 14,
        borderRadius: 16,
        border: "1px solid rgba(255,255,255,0.12)",
        background: "rgba(255,255,255,0.03)",
        display: "grid",
        gap: 12,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800 }}>Pickup Health</div>
          <div style={{ fontSize: 12, opacity: 0.72 }}>
            Priorização operacional automática com tendência, baseline e anomalias.
          </div>
        </div>

        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          style={{
            padding: "8px 12px",
            borderRadius: 10,
            border: "1px solid rgba(255,255,255,0.20)",
            background: "rgba(255,255,255,0.08)",
            color: "white",
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.65 : 1,
          }}
        >
          {loading ? "Atualizando..." : "Atualizar pickup-health"}
        </button>
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "end" }}>
        <label style={{ display: "grid", gap: 6, fontSize: 12 }}>
          Entidade
          <select
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            style={{
              minWidth: 150,
              borderRadius: 10,
              padding: "8px 10px",
              background: "#2d2d3a",
              color: "white",
              border: "1px solid rgba(255,255,255,0.16)",
            }}
          >
            {entityTypeOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "grid", gap: 6, fontSize: 12 }}>
          Janela de tendência (dias)
          <input
            type="number"
            min={1}
            max={90}
            value={trendDaysWindow}
            onChange={(e) => setTrendDaysWindow(Number(e.target.value || 7))}
            style={{
              width: 140,
              borderRadius: 10,
              padding: "8px 10px",
              background: "#2d2d3a",
              color: "white",
              border: "1px solid rgba(255,255,255,0.16)",
            }}
          />
        </label>

        <label style={{ display: "grid", gap: 6, fontSize: 12 }}>
          Limite
          <input
            type="number"
            min={1}
            max={100}
            value={rankingLimit}
            onChange={(e) => setRankingLimit(Number(e.target.value || 20))}
            style={{
              width: 110,
              borderRadius: 10,
              padding: "8px 10px",
              background: "#2d2d3a",
              color: "white",
              border: "1px solid rgba(255,255,255,0.16)",
            }}
          />
        </label>
      </div>

      {error ? (
        <pre
          style={{
            margin: 0,
            padding: 12,
            borderRadius: 12,
            border: "1px solid rgba(179,38,30,0.42)",
            background: "rgba(179,38,30,0.16)",
            color: "#ffd7d4",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            fontSize: 12,
          }}
        >
          {error}
        </pre>
      ) : null}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10 }}>
        <div style={summaryCardStyle}>
          <div style={summaryTitleStyle}>Entidades</div>
          <div style={summaryValueStyle}>{summary.total_entities ?? "-"}</div>
        </div>
        <div style={summaryCardStyle}>
          <div style={summaryTitleStyle}>Healthy</div>
          <div style={summaryValueStyle}>{summary.healthy_count ?? "-"}</div>
        </div>
        <div style={summaryCardStyle}>
          <div style={summaryTitleStyle}>Attention</div>
          <div style={summaryValueStyle}>{summary.attention_count ?? "-"}</div>
        </div>
        <div style={summaryCardStyle}>
          <div style={summaryTitleStyle}>Critical</div>
          <div style={summaryValueStyle}>{summary.critical_count ?? "-"}</div>
        </div>
        <div style={summaryCardStyle}>
          <div style={summaryTitleStyle}>Collapsed</div>
          <div style={summaryValueStyle}>{summary.collapsed_count ?? "-"}</div>
        </div>
      </div>

      {loading ? (
        <div style={{ fontSize: 12, opacity: 0.76 }}>Carregando pickup-health...</div>
      ) : ranking.length === 0 ? (
        <div style={{ fontSize: 12, opacity: 0.76 }}>Nenhum item retornado.</div>
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {ranking.map((item, idx) => {
            const severityRaw = item?.severity_bucket || "normal";
            const meta = isSeverityKey(severityRaw) ? severityMeta[severityRaw] : severityMeta.normal;
            const alerts = Array.isArray(item?.alerts) ? item.alerts : [];
            const anomalyAlerts = Array.isArray(item?.anomaly?.alerts) ? item.anomaly.alerts : [];

            return (
              <div
                key={`${item.entity_type}-${item.entity_id || idx}`}
                style={{
                  padding: 12,
                  borderRadius: 14,
                  border: `1px solid ${meta.border}`,
                  borderLeft: `6px solid ${meta.color}`,
                  background: meta.bg,
                  display: "grid",
                  gap: 8,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                  <div style={{ display: "grid", gap: 4 }}>
                    <div style={{ fontSize: 15, fontWeight: 800 }}>
                      {item.entity_type} • {item.entity_id || "N/D"}
                    </div>
                    {String(item.entity_type || "").toLowerCase() === "slot" ? (
                      <div style={{ fontSize: 12, fontWeight: 700, color: "#93c5fd", marginTop: 4 }}>
                        Equipamento:{" "}
                        <span style={{ fontWeight: 600, color: "#e0f2fe" }}>{formatSlotEquipmentLine(item)}</span>
                      </div>
                    ) : null}
                    <div style={{ fontSize: 12, opacity: 0.74 }}>
                      tenant: <b>{item.tenant_id || "-"}</b> • operator: <b>{item.operator_id || "-"}</b> • region:{" "}
                      <b>{item.region || "-"}</b>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                    <span style={badgeStyle(meta)}>{meta.label}</span>
                    <span style={badgeStyle()}>
                      prioridade <b>{formatScore(item.priority_score)}</b>
                    </span>
                    <span style={badgeStyle()}>
                      health <b>{formatScore(item.health_score)}</b>
                    </span>
                  </div>
                </div>

                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <span style={badgeStyle()}>
                    playbook <b>{item.suggested_playbook || "-"}</b>
                  </span>

                  {item.anomaly?.predictive_risk ? (
                    <span style={badgeStyle(severityMeta.incident)}>alerta preditivo</span>
                  ) : null}

                  {item.anomaly?.abrupt_drop ? (
                    <span style={badgeStyle(severityMeta.critical)}>queda abrupta</span>
                  ) : null}

                  {item.anomaly?.out_of_pattern ? (
                    <span style={badgeStyle(severityMeta.attention)}>fora do padrão</span>
                  ) : null}
                </div>

                <div style={{ fontSize: 12, opacity: 0.86 }}>
                  tendência: <b>{item?.trend?.direction || item?.signals?.trend_direction || "-"}</b>
                  {" • "}
                  delta: <b>{formatScore(item?.trend?.delta)}</b>
                  {" • "}
                  redemption atual: <b>{formatScore(item?.trend?.current_rate)}</b>
                  {" • "}
                  redemption anterior: <b>{formatScore(item?.trend?.previous_rate)}</b>
                </div>

                <div style={{ fontSize: 12, opacity: 0.86 }}>
                  volume: <b>{item?.metrics?.total_terminal_pickups ?? "-"}</b>
                  {" • "}
                  expiração: <b>{formatScore(item?.metrics?.expiration_rate)}</b>
                  {" • "}
                  cancelamento: <b>{formatScore(item?.metrics?.cancellation_rate)}</b>
                  {" • "}
                  SLA ready→redeemed: <b>{formatScore(item?.metrics?.avg_minutes_ready_to_redeemed)}</b>
                </div>

                {(alerts.length > 0 || anomalyAlerts.length > 0) && (
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {[...alerts, ...anomalyAlerts]
                      .filter((v, i, arr) => arr.indexOf(v) === i)
                      .map((alert) => (
                        <span key={alert} style={badgeStyle()}>
                          {alert}
                        </span>
                      ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

const summaryCardStyle: CSSProperties = {
  padding: 12,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.04)",
};

const summaryTitleStyle: CSSProperties = {
  fontSize: 12,
  opacity: 0.72,
};

const summaryValueStyle: CSSProperties = {
  fontSize: 22,
  fontWeight: 800,
  marginTop: 4,
};

