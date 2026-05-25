import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import RevenueChart from "../../components/financial/RevenueChart";
import ROICards from "../../components/financial/ROICards";
import { financialExecutiveApi } from "../../api/financialExecutiveApi";
import { brlFromReais, normalizeFinancialError, pct } from "./financialOpsShared";
import {
  buttonGhostStyle,
  buttonPrimaryStyle,
  criticalBannerStyle,
  healthLocalFilterRowStyle,
  okBannerStyle,
  summary24hHeaderStyle,
  summary24hHintStyle,
  toolbarStyle,
} from "../../styles/opsShellStyles";

const REFRESH_MS = 5 * 60 * 1000;

export default function ExecutiveDashboard() {
  const { token, hasRole } = useAuth();
  const isAdmin =
    hasRole("admin.operacao") || hasRole("admin.financeiro") || hasRole("admin_operacao");
  const [kpis, setKpis] = useState(null);
  const [trend, setTrend] = useState([]);
  const [roi, setRoi] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    if (!token) {
      setLoading(false);
      setError("Login OPS necessário para carregar KPIs.");
      return;
    }
    setError("");
    try {
      const [k, t, r] = await Promise.all([
        financialExecutiveApi.kpis(token),
        financialExecutiveApi.revenueTrend(12, token),
        financialExecutiveApi.lockerRoi({ viability: "HIGH_PERFORMANCE" }, token),
      ]);
      setKpis(k);
      setTrend(t.items || []);
      setRoi(r.items || []);
    } catch (err) {
      setError(normalizeFinancialError(err));
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
    const id = window.setInterval(() => void load(), REFRESH_MS);
    return () => window.clearInterval(id);
  }, [load]);

  const cards = useMemo(
    () => [
      { label: "Receita MTD", value: brlFromReais(kpis?.revenue_mtd_brl), hint: "Mês corrente" },
      { label: "Lucro MTD", value: brlFromReais(kpis?.profit_mtd_brl), hint: "Consolidado" },
      { label: "Margem MTD", value: pct(kpis?.margin_mtd_pct), hint: "Sobre receita" },
      { label: "Receita LTM", value: brlFromReais(kpis?.revenue_ltm_brl), hint: "12 meses" },
      { label: "Lockers ativos", value: String(kpis?.total_active_lockers ?? "—"), hint: "Rede" },
      { label: "% Underperforming", value: pct(kpis?.pct_underperforming), hint: "ROI baixo" },
    ],
    [kpis],
  );

  async function exportFile(format) {
    if (!token) return;
    try {
      const res = await fetch(financialExecutiveApi.exportUrl(format, "kpis"), {
        headers: { Authorization: `Bearer ${token}`, "X-Actor-Roles": "admin_operacao" },
      });
      if (!res.ok) throw new Error(`Export HTTP ${res.status}`);
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `financial-kpis.${format}`;
      a.click();
      URL.revokeObjectURL(a.href);
      setMessage(`Export ${format.toUpperCase()} gerado.`);
    } catch (err) {
      setError(normalizeFinancialError(err));
    }
  }

  return (
    <div>
      <div style={summary24hHeaderStyle}>
        <h3 style={{ margin: 0, fontSize: 15 }}>Executive Dashboard</h3>
        <div style={toolbarStyle}>
          <button type="button" style={buttonGhostStyle} disabled={loading || !token} onClick={() => void load()}>
            {loading ? "Carregando…" : "Atualizar"}
          </button>
          <button type="button" style={buttonGhostStyle} disabled={!token} onClick={() => void exportFile("csv")}>
            Export CSV
          </button>
          <button type="button" style={buttonGhostStyle} disabled={!token} onClick={() => void exportFile("pdf")}>
            Export PDF
          </button>
        </div>
      </div>

      <p style={summary24hHintStyle}>
        Auto-refresh 5 min · {isAdmin ? "perfil admin" : "somente leitura"} · meta EBITDA{" "}
        {kpis?.target_ebitda_margin_pct ?? 40}%
      </p>

      {error ? <div style={criticalBannerStyle}>{error}</div> : null}
      {message ? <div style={okBannerStyle}>{message}</div> : null}

      <div style={healthLocalFilterRowStyle}>
        {cards.map((c) => (
          <div
            key={c.label}
            style={{
              background: "rgba(15,23,42,0.55)",
              border: "1px solid rgba(148,163,184,0.25)",
              borderRadius: 12,
              padding: 12,
            }}
          >
            <div style={{ fontSize: 12, color: "#94a3b8" }}>{c.label}</div>
            <div style={{ fontSize: 22, fontWeight: 700, marginTop: 4 }}>{loading ? "…" : c.value}</div>
            <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>{c.hint}</div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 14 }}>
        <RevenueChart data={trend} />
      </div>

      <section style={{ marginTop: 16 }}>
        <h3 style={{ margin: "0 0 10px", fontSize: 14 }}>Top ROI — alta performance</h3>
        <ROICards items={roi} />
      </section>
    </div>
  );
}
