import React from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import OpsPageTitleHeader from "../../components/OpsPageTitleHeader";
import {
  ANALYTICS_API,
  FINANCIAL_API,
  PAGE_VERSION,
  TAB_ITEMS,
} from "./financialOpsShared";
import {
  apiKeyBannerStyle,
  cardStyle,
  crossShortcutLinkStyle,
  mutedTextStyle,
  opsSanityCardStyle,
  pageStyle,
  summary24hHeaderStyle,
  summary24hHintStyle,
  tabButtonStyle,
  toolbarStyle,
} from "../../styles/opsShellStyles";

export default function FinancialShell() {
  const { token } = useAuth();
  const { pathname } = useLocation();

  return (
    <div style={pageStyle}>
      <div style={toolbarStyle}>
        <Link to="/ops/finance/admin?tab=pnl" style={crossShortcutLinkStyle}>
          Finance PnL
        </Link>
        <Link to="/ops/finance/admin?tab=settlements" style={crossShortcutLinkStyle}>
          Settlements
        </Link>
        <Link to="/ops/analytics/financial" style={crossShortcutLinkStyle}>
          Analytics MV
        </Link>
      </div>

      <OpsPageTitleHeader
        title="Financial — dashboards executivos"
        versionLabel={PAGE_VERSION}
        versionTo="/ops/auth/policy/versioning"
        containerStyle={{ marginBottom: 0 }}
        titleStyle={{ margin: 0 }}
      />

      <p style={mutedTextStyle}>
        KPIs consolidados (<code style={{ color: "#e2e8f0" }}>v_financial_dashboard</code>), ROI por locker, P&amp;L mensal (
        <code style={{ color: "#e2e8f0" }}>mv_locker_monthly_pnl</code>), simulação de expansão e receita de parceiros. API{" "}
        <code style={{ color: "#e2e8f0" }}>{FINANCIAL_API}</code> · cache Redis 5 min · refresh pg_cron.
      </p>

      {!token ? (
        <div style={apiKeyBannerStyle}>
          Faça login OPS para autenticar nas rotas <code>/api/v1/financial</code> (Bearer + papéis admin).
        </div>
      ) : null}

      <section style={{ ...opsSanityCardStyle, marginTop: 10 }}>
        <div style={summary24hHeaderStyle}>
          <h3 style={{ margin: 0, fontSize: 14 }}>Navegação Financial</h3>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {TAB_ITEMS.map((t) => (
              <NavLink
                key={t.id}
                to={t.to}
                end={t.end}
                style={({ isActive }) => ({
                  ...tabButtonStyle(isActive),
                  textDecoration: "none",
                  display: "inline-block",
                })}
              >
                {t.label}
              </NavLink>
            ))}
          </div>
        </div>
        <p style={summary24hHintStyle}>
          Rota atual: <code>{pathname}</code> · analytics legado: <code>{ANALYTICS_API}</code>
        </p>
      </section>

      <div style={{ ...cardStyle, marginTop: 12 }}>
        <Outlet />
      </div>
    </div>
  );
}
