import React from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { getOrderLifecycleBase } from "../utils/orderLifecycleInternalApi";

const PAGE_VERSION = "ops/order/deadlines v0.1";

/**
 * Gap de produto: o backend expõe apenas POST /internal/deadlines e POST /internal/deadlines/cancel
 * (sem GET para listar). Ver `order_lifecycle_service/app/routers/internal.py`.
 */
export default function OrderDeadlinesPage() {
  return (
    <div className="ops-page" style={{ padding: "1rem", maxWidth: 1200 }}>
      <OpsPageTitleHeader title="OPS — Order / deadlines (lifecycle)" versionLabel={PAGE_VERSION} />
      <p style={{ opacity: 0.85, marginBottom: 12 }}>
        Base do serviço: <code>{getOrderLifecycleBase()}</code>. Criação/cancelamento usam{" "}
        <code>X-Internal-Token</code> (<code>VITE_INTERNAL_TOKEN</code>) nos POST internos.
      </p>
      <p style={{ lineHeight: 1.55 }}>
        Não existe <code>GET /internal/deadlines</code> no <code>order_lifecycle_service</code>. Hoje só há{" "}
        <code>POST /internal/deadlines</code> e <code>POST /internal/deadlines/cancel</code> em{" "}
        <code>app/routers/internal.py</code>. Quando existir um GET de listagem, esta página pode seguir o mesmo padrão
        das outras telas Order/Pickup (<code>olFetch</code> + tabela rolável).
      </p>
    </div>
  );
}
