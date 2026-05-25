import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { lockersOpsApi } from "../api/lockersOpsApi";
import { buttonPrimaryStyle, cardStyle, pageStyle } from "../styles/opsShellStyles";

const COLS = ["OPEN", "IN_PROGRESS", "WAITING_PARTS", "RESOLVED"];

export default function OpsMaintenanceTicketsPage() {
  const [byLocker, setByLocker] = useState({});
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try {
      const data = await lockersOpsApi.listLockers({ limit: 80 });
      const map = {};
      await Promise.all(
        (data.items || []).slice(0, 40).map(async (lk) => {
          const r = await lockersOpsApi.getMaintenance(lk.id);
          map[lk.id] = r.items || [];
        }),
      );
      setByLocker(map);
    } catch (e) {
      setErr(String(e.message || e));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const all = useMemo(() => Object.values(byLocker).flat(), [byLocker]);

  return (
    <div style={pageStyle}>
      <OpsPageTitleHeader title="Maintenance" />
      {err ? <p style={{ color: "#f87171" }}>{err}</p> : null}
      <button type="button" style={buttonPrimaryStyle} onClick={load}>
        Atualizar
      </button>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginTop: 16 }}>
        {COLS.map((col) => (
          <div key={col} style={cardStyle}>
            <h3 style={{ fontSize: 11, textTransform: "uppercase", color: "#94a3b8" }}>{col}</h3>
            {all
              .filter((t) => t.status === col)
              .map((t) => (
                <div key={t.id} style={{ marginTop: 8, padding: 8, border: "1px solid #334155", borderRadius: 8 }}>
                  <strong>{t.title}</strong>
                  <br />
                  <Link to={`/ops/lockers/${t.locker_id}?tab=maintenance`}>{t.locker_id.slice(0, 8)}…</Link>
                </div>
              ))}
          </div>
        ))}
      </div>
    </div>
  );
}
