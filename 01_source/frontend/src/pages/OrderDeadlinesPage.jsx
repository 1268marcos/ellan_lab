import React from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { getOrderLifecycleBase } from "../utils/orderLifecycleInternalApi";

const PAGE_VERSION = "ops/order/deadlines v0.2-health-shell";

/**
 * Gap de produto: o backend expõe apenas POST /internal/deadlines e POST /internal/deadlines/cancel
 * (sem GET para listar). Ver `order_lifecycle_service/app/routers/internal.py`.
 */
export default function OrderDeadlinesPage() {
  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={crossShortcutStyle}>
          <Link to="/ops/health" style={crossShortcutLinkStyle}>
            Ir para saúde operacional
          </Link>
        </div>
        <div style={headerRowStyle}>
          <div>
            <OpsPageTitleHeader
              title="OPS — Order / deadlines (lifecycle)"
              versionLabel={PAGE_VERSION}
              versionTo="/ops/auth/policy/versioning"
              containerStyle={{ marginBottom: 0 }}
              titleStyle={{ margin: 0 }}
            />
            <p style={mutedTextStyle}>
              Base do serviço: <code style={{ color: "#e2e8f0" }}>{getOrderLifecycleBase()}</code>. Criação/cancelamento usam{" "}
              <code style={{ color: "#e2e8f0" }}>X-Internal-Token</code> (<code style={{ color: "#e2e8f0" }}>VITE_INTERNAL_TOKEN</code>) nos POST
              internos.
            </p>
          </div>
        </div>
        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Listagem</h3>
          </div>
          <p style={{ ...summary24hHintStyle, margin: 0, lineHeight: 1.55 }}>
            Não existe <code style={{ color: "#e2e8f0" }}>GET /internal/deadlines</code> no <code style={{ color: "#e2e8f0" }}>order_lifecycle_service</code>.
            Hoje só há <code style={{ color: "#e2e8f0" }}>POST /internal/deadlines</code> e{" "}
            <code style={{ color: "#e2e8f0" }}>POST /internal/deadlines/cancel</code> em <code style={{ color: "#e2e8f0" }}>app/routers/internal.py</code>.
            Quando existir um GET de listagem, esta página pode seguir o mesmo padrão das outras telas Order/Pickup (<code style={{ color: "#e2e8f0" }}>olFetch</code>{" "}
            + tabela rolável).
          </p>
        </section>
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
