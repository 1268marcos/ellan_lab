import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { financialExecutiveApi } from "../../api/financialExecutiveApi";
import { normalizeFinancialError } from "./financialOpsShared";
import {
  buttonPrimaryStyle,
  criticalBannerStyle,
  healthLocalFilterFieldStyle,
  healthLocalFilterInputStyle,
  healthLocalFilterRowStyle,
  okBannerStyle,
  summary24hHeaderStyle,
  summary24hHintStyle,
  tableStyle,
  tdStyle,
  thStyle,
} from "../../styles/opsShellStyles";

export default function ExpansionSimulator() {
  const { token } = useAuth();
  const [targetCity, setTargetCity] = useState("São Paulo");
  const [lockersCount, setLockersCount] = useState(5);
  const [revenuePerLocker, setRevenuePerLocker] = useState(450000);
  const [opexPerLocker, setOpexPerLocker] = useState(120000);
  const [installCost, setInstallCost] = useState(80000);
  const [hardwareCost, setHardwareCost] = useState(350000);
  const [usefulLife, setUsefulLife] = useState(60);
  const [occupancy, setOccupancy] = useState(70);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    if (!token) {
      setError("Login OPS necessário.");
      return;
    }
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const data = await financialExecutiveApi.simulateExpansion(
        {
          target_city: targetCity,
          lockers_count: lockersCount,
          estimated_monthly_revenue_per_locker_cents: revenuePerLocker,
          estimated_monthly_opex_per_locker_cents: opexPerLocker,
          installation_cost_per_locker_cents: installCost,
          hardware_cost_per_locker_cents: hardwareCost,
          useful_life_months: usefulLife,
          expected_occupancy_rate_pct: occupancy,
        },
        token,
      );
      setResults(data.items || []);
      setMessage(`Cenário calculado para ${data.target_city || targetCity}.`);
    } catch (err) {
      setError(normalizeFinancialError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={summary24hHeaderStyle}>
        <h3 style={{ margin: 0, fontSize: 15 }}>Expansion Simulator</h3>
      </div>
      <p style={summary24hHintStyle}>
        Função <code>simulate_expansion_scenario_v2</code> — NPV 36m, IRR, payback e ocupação de breakeven.
      </p>

      <form onSubmit={onSubmit} style={healthLocalFilterRowStyle}>
        <label style={healthLocalFilterFieldStyle}>
          Cidade alvo
          <input style={healthLocalFilterInputStyle} value={targetCity} onChange={(e) => setTargetCity(e.target.value)} required />
        </label>
        <label style={healthLocalFilterFieldStyle}>
          Lockers ({lockersCount})
          <input type="range" min={1} max={50} value={lockersCount} onChange={(e) => setLockersCount(Number(e.target.value))} />
        </label>
        <label style={healthLocalFilterFieldStyle}>
          Ocupação esperada ({occupancy}%)
          <input type="range" min={10} max={100} value={occupancy} onChange={(e) => setOccupancy(Number(e.target.value))} />
        </label>
        <label style={healthLocalFilterFieldStyle}>
          Receita/mês/locker (centavos)
          <input type="number" style={healthLocalFilterInputStyle} value={revenuePerLocker} onChange={(e) => setRevenuePerLocker(Number(e.target.value))} />
        </label>
        <label style={healthLocalFilterFieldStyle}>
          Opex/mês/locker (centavos)
          <input type="number" style={healthLocalFilterInputStyle} value={opexPerLocker} onChange={(e) => setOpexPerLocker(Number(e.target.value))} />
        </label>
        <label style={healthLocalFilterFieldStyle}>
          Instalação/locker (centavos)
          <input type="number" style={healthLocalFilterInputStyle} value={installCost} onChange={(e) => setInstallCost(Number(e.target.value))} />
        </label>
        <label style={healthLocalFilterFieldStyle}>
          Hardware/locker (centavos)
          <input type="number" style={healthLocalFilterInputStyle} value={hardwareCost} onChange={(e) => setHardwareCost(Number(e.target.value))} />
        </label>
        <label style={healthLocalFilterFieldStyle}>
          Vida útil (meses)
          <input type="number" style={healthLocalFilterInputStyle} value={usefulLife} onChange={(e) => setUsefulLife(Number(e.target.value))} />
        </label>
        <button type="submit" style={buttonPrimaryStyle} disabled={loading || !token}>
          {loading ? "Simulando…" : "Simular expansão"}
        </button>
      </form>

      {error ? <div style={criticalBannerStyle}>{error}</div> : null}
      {message ? <div style={okBannerStyle}>{message}</div> : null}

      {results.length ? (
        <table style={{ ...tableStyle, marginTop: 14 }}>
          <thead>
            <tr>
              <th style={thStyle}>Métrica</th>
              <th style={thStyle}>Valor</th>
              <th style={thStyle}>Descrição</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.scenario_metric}>
                <td style={tdStyle}>{r.scenario_metric}</td>
                <td style={tdStyle}>{Number(r.value).toLocaleString("pt-BR")}</td>
                <td style={tdStyle}>{r.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
