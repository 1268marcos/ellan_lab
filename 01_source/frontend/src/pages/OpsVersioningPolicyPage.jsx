import React from "react";
import { Link } from "react-router-dom";

const VERSIONING_EXAMPLES = [
  {
    version: "v1.4.2-sprint2",
    reason: "Ajustes incrementais de UX + comparativo semanal no histórico de snapshots.",
  },
  {
    version: "v1.5.0-sprint3",
    reason: "Nova capacidade funcional sem quebra de fluxo anterior.",
  },
  {
    version: "v2.0.0-sprint4",
    reason: "Mudança estrutural relevante com impacto de fluxo/contrato.",
  },
];

export default function OpsVersioningPolicyPage() {
  return (
    <main style={pageStyle}>
      <header style={{ marginBottom: 14 }}>
        <h1 style={{ margin: 0 }}>OPS — Política de versionamento (ops/health)</h1>
        <p style={subtitleStyle}>
          Referência operacional para rastrear evoluções da página de saúde operacional em suporte, auditoria e incidentes.
        </p>
      </header>

      <section style={cardStyle}>
        <h2 style={sectionTitleStyle}>Formato oficial</h2>
        <p style={paragraphStyle}>
          Usar sempre: <strong>`major.minor.patch + sprint`</strong>, exibido como <strong>`ops/health vX.Y.Z-sprintN`</strong>.
        </p>
      </section>

      <section style={cardStyle}>
        <h2 style={sectionTitleStyle}>Regra de incremento</h2>
        <ul style={listStyle}>
          <li><strong>major</strong>: quebra de fluxo/contrato ou mudança estrutural relevante.</li>
          <li><strong>minor</strong>: nova capacidade funcional sem quebrar o fluxo anterior.</li>
          <li><strong>patch</strong>: ajuste incremental (layout, microcopy, bugfix pontual).</li>
          <li><strong>sprint</strong>: sufixo informativo do ciclo em andamento.</li>
        </ul>
      </section>

      <section style={cardStyle}>
        <h2 style={sectionTitleStyle}>Exemplos práticos</h2>
        <div style={examplesWrapStyle}>
          {VERSIONING_EXAMPLES.map((item) => (
            <article key={item.version} style={exampleItemStyle}>
              <strong style={exampleVersionStyle}>{item.version}</strong>
              <small style={exampleReasonStyle}>{item.reason}</small>
            </article>
          ))}
        </div>
      </section>

      <section style={cardStyle}>
        <h2 style={sectionTitleStyle}>Checklist por release</h2>
        <ul style={listStyle}>
          <li>Atualizar badge da versão na página `ops/health`.</li>
          <li>Registrar versão e entregas no documento de sprint.</li>
          <li>Atualizar board visual (`docs/ellan_lab_sprint_board.html`) mantendo consistência ELLAN LAB.</li>
          <li>Anexar evidência operacional (snapshot/export/runbook/ticket).</li>
        </ul>
      </section>

      <div style={linksRowStyle}>
        <Link to="/ops/health">Voltar para ops/health</Link>
        <Link to="/ops/auth/policy">Voltar para política de autorização</Link>
        <Link to="/ops/updates">Abrir registro de atualizações OPS</Link>
        <a href="/docs/ellan_lab_sprint_board.html">Abrir board visual de sprint</a>
      </div>
    </main>
  );
}

const pageStyle = {
  maxWidth: 980,
  margin: "0 auto",
  padding: 24,
  display: "grid",
  gap: 12,
};

const cardStyle = {
  borderRadius: 12,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.22)",
  padding: 12,
  display: "grid",
  gap: 8,
};

const subtitleStyle = {
  marginTop: 8,
  color: "#475569",
};

const sectionTitleStyle = {
  margin: 0,
  fontSize: 16,
};

const paragraphStyle = {
  margin: 0,
  color: "#334155",
};

const listStyle = {
  margin: 0,
  paddingLeft: 18,
  color: "#334155",
  display: "grid",
  gap: 4,
};

const examplesWrapStyle = {
  display: "grid",
  gap: 8,
};

const exampleItemStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.18)",
  padding: "8px 10px",
  display: "grid",
  gap: 2,
};

const exampleVersionStyle = {
  color: "#0f172a",
};

const exampleReasonStyle = {
  color: "#475569",
};

const linksRowStyle = {
  display: "flex",
  gap: 12,
  flexWrap: "wrap",
};
