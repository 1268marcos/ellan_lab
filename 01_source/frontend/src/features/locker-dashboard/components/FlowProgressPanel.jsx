// 01_source/frontend/src/features/locker-dashboard/components/FlowProgressPanel.jsx

import React from "react";
import { panelStyle } from "../utils/dashboardUiStyles.js";

const stepBaseStyle = {
  borderRadius: 10,
  padding: "8px 10px",
  border: "1px solid rgba(255,255,255,0.16)",
  fontSize: 12,
};

function getStepStyle(state) {
  if (state === "done") {
    return {
      ...stepBaseStyle,
      background: "rgba(31,122,63,0.20)",
      border: "1px solid rgba(31,122,63,0.45)",
    };
  }

  if (state === "active") {
    return {
      ...stepBaseStyle,
      background: "rgba(199,146,0,0.20)",
      border: "1px solid rgba(199,146,0,0.45)",
    };
  }

  return {
    ...stepBaseStyle,
    background: "rgba(255,255,255,0.05)",
    opacity: 0.8,
  };
}

export default function FlowProgressPanel({
  steps = [],
  actionHint = "",
  onStepClick,
}) {
  if (!steps.length) return null;

  return (
    <section style={panelStyle}>
      <div>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Progresso do Fluxo</div>
        <div style={{ fontSize: 12, opacity: 0.72 }}>
          Selecao de gaveta, pedido, pagamento e retirada.
        </div>
      </div>

      <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
        {steps.map((step) => (
          <button
            key={step.key}
            onClick={() => onStepClick?.(step.key)}
            type="button"
            style={{
              ...getStepStyle(step.state),
              textAlign: "left",
              width: "100%",
              cursor: onStepClick ? "pointer" : "default",
            }}
          >
            <div style={{ fontWeight: 700 }}>
              {step.state === "done" ? "✓" : step.state === "active" ? "→" : "○"} {step.label}
            </div>
            {step.detail ? (
              <div style={{ marginTop: 4, opacity: 0.9 }}>{step.detail}</div>
            ) : null}
          </button>
        ))}
      </div>

      {actionHint ? (
        <div
          style={{
            fontSize: 12,
            borderRadius: 10,
            padding: 10,
            background: "rgba(27,88,131,0.16)",
            border: "1px solid rgba(27,88,131,0.35)",
          }}
        >
          <b>Próxima ação sugerida:</b> {actionHint}
        </div>
      ) : null}
    </section>
  );
}
