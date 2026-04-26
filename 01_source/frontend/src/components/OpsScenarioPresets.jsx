import React from "react";

const TONE_STYLE = {
  success: {
    border: "1px solid rgba(22,163,74,0.45)",
    background: "rgba(22,163,74,0.2)",
    color: "#86EFAC",
  },
  warn: {
    border: "1px solid rgba(217,119,6,0.45)",
    background: "rgba(217,119,6,0.2)",
    color: "#FDE68A",
  },
  error: {
    border: "1px solid rgba(220,38,38,0.45)",
    background: "rgba(220,38,38,0.18)",
    color: "#FCA5A5",
  },
};

function buttonStyle(tone) {
  return {
    padding: "8px 12px",
    borderRadius: 999,
    ...TONE_STYLE[tone],
    fontWeight: 700,
    cursor: "pointer",
    fontSize: 12,
  };
}

/**
 * Grupo de presets de cenário da camada OPS com cores padronizadas.
 *
 * Cores/tom:
 * - `success`: cenário saudável/fluxo esperado (verde)
 * - `warn`: cenário de atenção/revisão (âmbar)
 * - `error`: cenário crítico/diagnóstico (vermelho)
 *
 * Estrutura esperada em `items`:
 * - `{ id: string, tone: "success"|"warn"|"error", label: string, onClick: () => void }`
 *
 * Exemplo:
 * `<OpsScenarioPresets
 *   items={[
 *     { id: "ok", tone: "success", label: "Preset verde", onClick: onHealthy },
 *     { id: "review", tone: "warn", label: "Preset âmbar", onClick: onReview },
 *     { id: "critical", tone: "error", label: "Preset vermelho", onClick: onCritical },
 *   ]}
 * />`
 *
 * Dicas de uso:
 * - Use `style` para encaixe de layout local (margem/grid/flex), sem redefinir as cores.
 * - Use `disabled` para bloquear interação durante chamadas em andamento.
 */
export default function OpsScenarioPresets({ items, disabled = false, style }) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) return null;

  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", ...style }}>
      {list.map((item) => (
        <button
          key={item.id}
          type="button"
          style={buttonStyle(item.tone)}
          onClick={item.onClick}
          disabled={disabled}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
