import React from "react";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

/**
 * Gap de produto: o backend expõe apenas POST /internal/deadlines e POST /internal/deadlines/cancel
 * (sem GET para listar). Ver `order_lifecycle_service/app/routers/internal.py`.
 */
export default function OrderDeadlinesPage() {
  return (
    <div style={{ padding: 24, maxWidth: 720 }}>
      <OpsPageTitleHeader title="Deadlines (lifecycle)" subtitle="Listagem — endpoint em falta" />
      <p style={{ marginTop: 16, lineHeight: 1.5 }}>
        Não existe <code>GET /internal/deadlines</code> no serviço. Para criar/cancelar use os POST documentados no
        router interno. Quando existir um GET de listagem, esta página pode consumi-lo com o mesmo padrão de{" "}
        <code>X-Internal-Token</code> que as outras telas Order/Pickup.
      </p>
    </div>
  );
}
