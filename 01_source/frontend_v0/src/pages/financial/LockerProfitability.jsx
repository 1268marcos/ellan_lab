import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import ProfitabilityHeatmap from "../../components/financial/ProfitabilityHeatmap";
import { financialExecutiveApi } from "../../api/financialExecutiveApi";
import { brlCents, normalizeFinancialError, pct } from "./financialOpsShared";
import {
  buttonGhostStyle,
  buttonPrimaryStyle,
  criticalBannerStyle,
  healthLocalFilterFieldStyle,
  healthLocalFilterInputStyle,
  healthLocalFilterRowStyle,
  summary24hHeaderStyle,
  summary24hHintStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../../styles/opsShellStyles";

export default function LockerProfitability() {
  const { token } = useAuth();
  const [lockerId, setLockerId] = useState("");
  const [monthFrom, setMonthFrom] = useState("");
  const [monthTo, setMonthTo] = useState("");
  const [sort, setSort] = useState("month_ref");
  const [order, setOrder] = useState("desc");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token) {
      setLoading(false);
      setError("Login OPS necessário.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await financialExecutiveApi.lockerPnl(
        {
          locker_id: lockerId || undefined,
          month_from: monthFrom || undefined,
          month_to: monthTo || undefined,
          sort,
          order,
        },
        token,
      );
      setRows(data.items || []);
    } catch (err) {
      setError(normalizeFinancialError(err));
    } finally {
      setLoading(false);
    }
  }, [token, lockerId, monthFrom, monthTo, sort, order]);

  useEffect(() => {
    void load();
  }, [load]);

  function toggleSort(key) {
    if (sort === key) setOrder((o) => (o === "asc" ? "desc" : "asc"));
    else {
      setSort(key);
      setOrder("desc");
    }
  }

  async function exportFile(format) {
    if (!token) return;
    try {
      const res = await fetch(financialExecutiveApi.exportUrl(format, "locker-pnl"), {
        headers: { Authorization: `Bearer ${token}`, "X-Actor-Roles": "admin_operacao" },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `locker-pnl.${format}`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      setError(normalizeFinancialError(err));
    }
  }

  const thBtn = (key, label) => (
    <button type="button" onClick={() => toggleSort(key)} style={{ background: "none", border: "none", color: "inherit", cursor: "pointer", fontWeight: 700 }}>
      {label}
      {sort === key ? (order === "asc" ? " ↑" : " ↓") : ""}
    </button>
  );

  return (
    <div>
      <div style={summary24hHeaderStyle}>
        <h3 style={{ margin: 0, fontSize: 15 }}>Locker P&amp;L</h3>
        <div style={toolbarStyle}>
          <button type="button" style={buttonGhostStyle} disabled={!token} onClick={() => void exportFile("csv")}>
            CSV
          </button>
          <button type="button" style={buttonGhostStyle} disabled={!token} onClick={() => void exportFile("pdf")}>
            PDF
          </button>
        </div>
      </div>
      <p style={summary24hHintStyle}>Materialized view <code>mv_locker_monthly_pnl</code> — ordenação e filtros server-side.</p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void load();
        }}
        style={healthLocalFilterRowStyle}
      >
        <label style={healthLocalFilterFieldStyle}>
          locker_id
          <input
            style={healthLocalFilterInputStyle}
            value={lockerId}
            onChange={(e) => setLockerId(e.target.value)}
            placeholder="opcional"
          />
        </label>
        <label style={healthLocalFilterFieldStyle}>
          mês de
          <input type="date" style={healthLocalFilterInputStyle} value={monthFrom} onChange={(e) => setMonthFrom(e.target.value)} />
        </label>
        <label style={healthLocalFilterFieldStyle}>
          mês até
          <input type="date" style={healthLocalFilterInputStyle} value={monthTo} onChange={(e) => setMonthTo(e.target.value)} />
        </label>
        <button type="submit" style={buttonPrimaryStyle}>
          Filtrar
        </button>
      </form>

      {error ? <div style={criticalBannerStyle}>{error}</div> : null}

      <ProfitabilityHeatmap rows={rows} />

      <table style={{ ...tableStyle, marginTop: 14 }}>
        <thead>
          <tr>
            <th style={thStyle}>{thBtn("month_ref", "Mês")}</th>
            <th style={thStyle}>{thBtn("locker_id", "Locker")}</th>
            <th style={thStyle}>{thBtn("revenue_cents", "Receita")}</th>
            <th style={thStyle}>Opex</th>
            <th style={thStyle}>Deprec.</th>
            <th style={thStyle}>{thBtn("net_profit_cents", "Lucro")}</th>
            <th style={thStyle}>{thBtn("margin_pct", "Margem")}</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={7} style={tdStyle}>
                Carregando…
              </td>
            </tr>
          ) : rows.length ? (
            rows.map((r) => (
              <tr key={`${r.month_ref}-${r.locker_id}`}>
                <td style={tdStyle}>{String(r.month_ref).slice(0, 10)}</td>
                <td style={tdStyle}>{r.locker_id}</td>
                <td style={tdStyle}>{brlCents(r.revenue_cents)}</td>
                <td style={tdStyle}>{brlCents(r.opex_cents)}</td>
                <td style={tdStyle}>{brlCents(r.depreciation_cents)}</td>
                <td style={tdStyle}>{brlCents(r.net_profit_cents)}</td>
                <td style={tdStyle}>{pct(r.margin_pct)}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={7} style={tdStyle}>
                Nenhum registro no período.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
