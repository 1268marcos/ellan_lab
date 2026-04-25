import React from "react";
import { getTrendToken } from "./opsVisualTokens";

export function resolveTrendByDelta(delta) {
  const value = Number(delta ?? 0);
  if (Number.isNaN(value)) return "stable";
  if (value > 0) return "up";
  if (value < 0) return "down";
  return "stable";
}

export default function OpsTrendKpiCard({
  label,
  value,
  previousValue = null,
  trend = null,
  deltaLabel = null,
  baseStyle = {},
  showTrend = true,
}) {
  const normalizedTrend = trend ? String(trend).toLowerCase() : "stable";
  const hasTrend =
    showTrend && (normalizedTrend === "up" || normalizedTrend === "down" || normalizedTrend === "stable");
  const trendStyle = getTrendToken(normalizedTrend);

  return (
    <article
      style={{
        ...baseStyle,
        ...(hasTrend
          ? {
              background: trendStyle.accentBg,
              border: trendStyle.accentBorder,
            }
          : {}),
      }}
    >
      <small style={{ display: "block", color: "#94A3B8", textTransform: "uppercase", fontSize: 11 }}>{label}</small>
      <strong
        style={{
          display: "block",
          marginTop: 6,
          fontSize: 24,
          color: hasTrend ? trendStyle.valueColor : "#BFDBFE",
        }}
      >
        {value}
      </strong>
      {hasTrend || previousValue !== null ? (
        <div
          style={{
            marginTop: 6,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: 11,
            color: "#94A3B8",
            gap: 8,
          }}
        >
          <span>{previousValue !== null && previousValue !== undefined ? `prev: ${previousValue}` : "prev: -"}</span>
          <span>{`${trendStyle.symbol} ${deltaLabel || "-"}`}</span>
        </div>
      ) : null}
    </article>
  );
}
