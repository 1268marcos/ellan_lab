import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { financialExecutiveApi } from "../../api/financialExecutiveApi";
import { brlCents, normalizeFinancialError } from "./financialOpsShared";
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

export default function PartnerRevenue() {
  const { token } = useAuth();
  const [partnerId, setPartnerId] = useState("");
  const [revenue, setRevenue] = useState([]);
  const [settlements, setSettlements] = useState([]);
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
      const data = await financialExecutiveApi.partnerRevenue({ partner_id: partnerId || undefined }, token);
      setRevenue(data.revenue || []);
      setSettlements(data.settlements || []);
    } catch (err) {
      setError(normalizeFinancialError(err));
    } finally {
      setLoading(false);
    }
  }, [token, partnerId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function exportFile(format) {
    if (!token) return;
    try {
      const res = await fetch(financialExecutiveApi.exportUrl(format, "partner-revenue"), {
        headers: { Authorization: `Bearer ${token}`, "X-Actor-Roles": "admin_operacao" },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `partner-revenue.${format}`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      setError(normalizeFinancialError(err));
    }
  }

  return (
    <div>
      <div style={summary24hHeaderStyle}>
        <h3 style={{ margin: 0, fontSize: 15 }}>Partner Settlements</h3>
        <div style={toolbarStyle}>
          <button type="button" style={buttonGhostStyle} disabled={!token} onClick={() => void exportFile("csv")}>
            CSV
          </button>
          <button type="button" style={buttonGhostStyle} disabled={!token} onClick={() => void exportFile("pdf")}>
            PDF
          </button>
        </div>
      </div>
      <p style={summary24hHintStyle}>
        <code>analytics_analytics.partner_revenue_monthly</code> + batches <code>partner_settlement_batches</code>.
      </p>

      <div style={healthLocalFilterRowStyle}>
        <label style={healthLocalFilterFieldStyle}>
          partner_id
          <input
            style={healthLocalFilterInputStyle}
            placeholder="opcional"
            value={partnerId}
            onChange={(e) => setPartnerId(e.target.value)}
          />
        </label>
        <button type="button" style={buttonPrimaryStyle} onClick={() => void load()}>
          Atualizar
        </button>
      </div>

      {error ? <div style={criticalBannerStyle}>{error}</div> : null}

      <h4 style={{ margin: "16px 0 8px", fontSize: 13, color: "#94a3b8" }}>Receita reconhecida (mensal)</h4>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Mês</th>
            <th style={thStyle}>Parceiro</th>
            <th style={thStyle}>Receita</th>
            <th style={thStyle}>Diferido</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={4} style={tdStyle}>
                Carregando…
              </td>
            </tr>
          ) : revenue.length ? (
            revenue.map((r, i) => (
              <tr key={`${r.month_ref}-${r.partner_id}-${i}`}>
                <td style={tdStyle}>{String(r.month_ref || "").slice(0, 10)}</td>
                <td style={tdStyle}>{r.partner_name || r.partner_id}</td>
                <td style={tdStyle}>{brlCents(r.revenue_recognized_cents)}</td>
                <td style={tdStyle}>{brlCents(r.deferred_amount_cents)}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={4} style={tdStyle}>
                Sem receita no filtro.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <h4 style={{ margin: "20px 0 8px", fontSize: 13, color: "#94a3b8" }}>Settlement batches</h4>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Período</th>
            <th style={thStyle}>Parceiro</th>
            <th style={thStyle}>Status</th>
            <th style={thStyle}>Líquido</th>
            <th style={thStyle}>Share %</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={5} style={tdStyle}>
                Carregando…
              </td>
            </tr>
          ) : settlements.length ? (
            settlements.map((s) => (
              <tr key={s.id}>
                <td style={tdStyle}>
                  {String(s.period_start || "").slice(0, 10)} — {String(s.period_end || "").slice(0, 10)}
                </td>
                <td style={tdStyle}>{s.partner_name || s.partner_id}</td>
                <td style={tdStyle}>{s.status}</td>
                <td style={tdStyle}>{brlCents(s.net_amount_cents)}</td>
                <td style={tdStyle}>{Number(s.revenue_share_pct ?? 0).toFixed(2)}%</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={5} style={tdStyle}>
                Sem settlements.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
