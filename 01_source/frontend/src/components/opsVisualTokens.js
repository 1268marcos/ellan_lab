const BADGE_BASE = {
  display: "inline-flex",
  alignItems: "center",
  borderRadius: 999,
  padding: "4px 10px",
  fontSize: 12,
  fontWeight: 800,
  lineHeight: 1.2,
};

export function getTrendToken(trend) {
  const normalized = String(trend || "stable").toLowerCase();
  if (normalized === "up") {
    return {
      key: "up",
      symbol: "▲",
      label: "UP",
      valueColor: "#DCFCE7",
      accentBg: "#166534",
      accentBorder: "1px solid #86EFAC",
    };
  }
  if (normalized === "down") {
    return {
      key: "down",
      symbol: "▼",
      label: "DOWN",
      valueColor: "#FEE2E2",
      accentBg: "#991B1B",
      accentBorder: "1px solid #FCA5A5",
    };
  }
  return {
    key: "stable",
    symbol: "■",
    label: "STABLE",
    valueColor: "#E2E8F0",
    accentBg: "#334155",
    accentBorder: "1px solid #94A3B8",
  };
}

export function getTrendBadgeStyle(trend) {
  const token = getTrendToken(trend);
  return {
    ...BADGE_BASE,
    padding: "2px 6px",
    fontSize: 10,
    border: token.accentBorder,
    background: token.accentBg,
    color: token.valueColor,
  };
}

export function getSeverityBadgeStyle(severity) {
  const normalized = String(severity || "OK").toUpperCase();
  if (normalized === "HIGH" || normalized === "ERROR") {
    return {
      ...BADGE_BASE,
      border: "1px solid #FCA5A5",
      background: "#991B1B",
      color: "#FEE2E2",
    };
  }
  if (normalized === "WARN") {
    return {
      ...BADGE_BASE,
      border: "1px solid #FDE68A",
      background: "#92400E",
      color: "#FEF3C7",
    };
  }
  return {
    ...BADGE_BASE,
    border: "1px solid #86EFAC",
    background: "#166534",
    color: "#DCFCE7",
  };
}

export function getConfidenceBadgeStyle(confidenceLevel) {
  const normalized = String(confidenceLevel || "MEDIUM").toUpperCase();
  if (normalized === "LOW") {
    return getSeverityBadgeStyle("ERROR");
  }
  if (normalized === "HIGH") {
    return getSeverityBadgeStyle("OK");
  }
  return getSeverityBadgeStyle("WARN");
}

export function getDataQualityFlagStyle(flag) {
  const normalized = String(flag || "").toUpperCase();
  if (normalized.includes("NO_EVENTS")) return getSeverityBadgeStyle("ERROR");
  if (normalized.includes("LOW_VOLUME")) return getSeverityBadgeStyle("WARN");
  if (normalized.includes("MEDIUM_VOLUME")) return getSeverityBadgeStyle("WARN");
  return {
    ...BADGE_BASE,
    border: "1px solid #93C5FD",
    background: "#1E3A8A",
    color: "#DBEAFE",
  };
}
