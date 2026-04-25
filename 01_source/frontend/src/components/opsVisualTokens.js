const BADGE_BASE = {
  display: "inline-flex",
  alignItems: "center",
  borderRadius: 999,
  padding: "4px 10px",
  fontSize: 12,
  fontWeight: 700,
};

export function getTrendToken(trend) {
  const normalized = String(trend || "stable").toLowerCase();
  if (normalized === "up") {
    return {
      key: "up",
      symbol: "▲",
      label: "UP",
      valueColor: "#86EFAC",
      accentBg: "rgba(22,163,74,0.2)",
      accentBorder: "1px solid rgba(22,163,74,0.45)",
    };
  }
  if (normalized === "down") {
    return {
      key: "down",
      symbol: "▼",
      label: "DOWN",
      valueColor: "#FCA5A5",
      accentBg: "rgba(220,38,38,0.2)",
      accentBorder: "1px solid rgba(220,38,38,0.45)",
    };
  }
  return {
    key: "stable",
    symbol: "■",
    label: "STABLE",
    valueColor: "#CBD5E1",
    accentBg: "rgba(71,85,105,0.25)",
    accentBorder: "1px solid rgba(100,116,139,0.45)",
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
      border: "1px solid rgba(179,38,30,0.65)",
      background: "rgba(179,38,30,0.20)",
      color: "#fecaca",
    };
  }
  if (normalized === "WARN") {
    return {
      ...BADGE_BASE,
      border: "1px solid rgba(199,146,0,0.65)",
      background: "rgba(199,146,0,0.18)",
      color: "#fde68a",
    };
  }
  return {
    ...BADGE_BASE,
    border: "1px solid rgba(31,122,63,0.65)",
    background: "rgba(31,122,63,0.18)",
    color: "#86efac",
  };
}
