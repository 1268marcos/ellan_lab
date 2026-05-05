
import React, { type CSSProperties } from "react";

type PresetTone = "success" | "warn" | "error";

export type OpsScenarioPresetItem = {
  id: string;
  tone: PresetTone;
  label: string;
  onClick: () => void;
};

export interface OpsScenarioPresetsProps {
  items: OpsScenarioPresetItem[];
  disabled?: boolean;
  style?: CSSProperties;
}

const TONE_STYLE: Record<PresetTone, CSSProperties> = {
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

function buttonStyle(tone: PresetTone): CSSProperties {
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
 */
export default function OpsScenarioPresets({ items, disabled = false, style }: OpsScenarioPresetsProps) {
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

