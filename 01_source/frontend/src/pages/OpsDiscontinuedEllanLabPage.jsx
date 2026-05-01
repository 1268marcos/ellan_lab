import React from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

/**
 * Destino para rotas OPS que expunham protótipos legados (ex.: `/ops/00` — LockerDashboardFirst).
 * Não importar código legado aqui; manter esta página enxuta.
 */
export default function OpsDiscontinuedEllanLabPage() {
  return (
    <main
      style={{
        maxWidth: 640,
        margin: "0 auto",
        padding: 24,
        fontFamily: "system-ui, sans-serif",
        color: "#0f172a",
      }}
      data-testid="ops-discontinued-ellan-lab-page"
    >
      <OpsPageTitleHeader title="Rota descontinuada" versionLabel="ops/discontinued v1" />
      <p style={{ marginTop: 16, fontSize: 18, lineHeight: 1.5, fontWeight: 600 }}>
        Descontinuado para o estágio atual do projeto ELLAN LAB
      </p>
      <p style={{ marginTop: 12, color: "#475569", lineHeight: 1.55 }}>
        O protótipo associado a esta rota foi isolado do fluxo principal. Use o locker OPS atual ou o cockpit de modelos
        KIOSK conforme o plano Sprint 1.
      </p>
      <ul style={{ marginTop: 20, paddingLeft: 20, color: "#334155", lineHeight: 1.6 }}>
        <li>
          <Link to="/ops/sp">Locker OPS — SP</Link>
        </li>
        <li>
          <Link to="/ops/pt">Locker OPS — PT</Link>
        </li>
        <li>
          <Link to="/ops/kiosk-touch-models">KIOSK touch — modelos v1</Link>
        </li>
      </ul>
    </main>
  );
}
