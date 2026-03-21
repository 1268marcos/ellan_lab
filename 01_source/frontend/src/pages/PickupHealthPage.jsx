// 01_source/frontend/src/pages/PickupHealthPage.jsx
import React, { useEffect, useState } from "react";

const ORDER_LIFECYCLE_BASE =
  import.meta.env.VITE_ORDER_LIFECYCLE_BASE_URL || "http://localhost:8010";

const INTERNAL_TOKEN =
  import.meta.env.VITE_INTERNAL_TOKEN || "";

export default function PickupHealthPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  async function fetchHealth() {
    setLoading(true);
    setErr("");

    try {
      const res = await fetch(
        `${ORDER_LIFECYCLE_BASE}/internal/analytics/pickup-health?entity_type=locker&ranking_limit=20`,
        {
          headers: {
            "Content-Type": "application/json",
            "X-Internal-Token": INTERNAL_TOKEN,
          },
        }
      );

      const text = await res.text();

      let parsed;
      try {
        parsed = JSON.parse(text);
      } catch {
        parsed = { raw: text };
      }

      if (!res.ok) {
        throw new Error(
          JSON.stringify({
            status: res.status,
            response: parsed,
          }, null, 2)
        );
      }

      setData(parsed);
    } catch (e) {
      setErr(String(e?.message || e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div style={pageStyle}>
      <h1>Pickup Health — Operacional</h1>

      <div style={{ marginBottom: 12 }}>
        <b>BASE:</b> {ORDER_LIFECYCLE_BASE}
      </div>

      <button onClick={fetchHealth} style={buttonStyle}>
        {loading ? "Carregando..." : "Atualizar"}
      </button>

      {err && <pre style={errorStyle}>{err}</pre>}

      {!loading && data?.ranking && (
        <div style={{ marginTop: 16 }}>
          {data.ranking.map((item) => (
            <div key={item.entity_id} style={cardStyle}>
              <b>{item.entity_id}</b>

              <div>
                priority: {item.priority_score} | health: {item.health_score}
              </div>

              <div>
                severity: <b>{item.severity_bucket}</b>
              </div>

              <div>
                playbook: <b>{item.suggested_playbook}</b>
              </div>

              {item.anomaly?.predictive_risk && (
                <div style={{ color: "red" }}>⚠ predictive risk</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const pageStyle = {
  padding: 24,
  color: "white",
};

const cardStyle = {
  padding: 12,
  border: "1px solid rgba(255,255,255,0.1)",
  marginBottom: 10,
  borderRadius: 8,
};

const buttonStyle = {
  padding: 10,
  cursor: "pointer",
};

const errorStyle = {
  marginTop: 16,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
};