// 01_source/frontend/src/features/locker-dashboard/utils/dashboardUiStyles.js

export const panelStyle = {
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 16,
  padding: 16,
  display: "grid",
  gap: 12,
};

export const fieldStyle = {
  width: "100%",
  padding: 12,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.18)",
  background: "rgba(255,255,255,0.08)",
  color: "white",
};

export function actionButtonStyle({
  tone = "neutral",
  disabled = false,
} = {}) {
  const toneBackground = {
    neutral: "rgba(255,255,255,0.08)",
    primary: "rgba(27,88,131,0.22)",
    accent: "rgba(95,61,196,0.22)",
    warning: "rgba(199,146,0,0.22)",
  };

  return {
    padding: "12px 14px",
    borderRadius: 12,
    border: "1px solid rgba(255,255,255,0.18)",
    background: disabled
      ? "rgba(255,255,255,0.06)"
      : toneBackground[tone] || toneBackground.neutral,
    color: "white",
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.7 : 1,
    fontWeight: 700,
  };
}

export const infoBannerStyle = {
  fontSize: 12,
  borderRadius: 10,
  padding: 10,
  background: "rgba(27,88,131,0.16)",
  border: "1px solid rgba(27,88,131,0.35)",
};

export const errorBannerStyle = {
  fontSize: 12,
  color: "#ffd9d6",
  background: "rgba(179,38,30,0.18)",
  border: "1px solid rgba(179,38,30,0.35)",
  borderRadius: 10,
  padding: 10,
  whiteSpace: "pre-wrap",
};
