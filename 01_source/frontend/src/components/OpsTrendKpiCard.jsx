import React from "react";
import { Link } from "react-router-dom";
import { getTrendToken } from "./opsVisualTokens";

/**
 * Resolve direção da tendência baseada no delta numérico.
 * Retornos possíveis: `up`, `down`, `stable`.
 */
export function resolveTrendByDelta(delta) {
  const value = Number(delta ?? 0);
  if (Number.isNaN(value)) return "stable";
  if (value > 0) return "up";
  if (value < 0) return "down";
  return "stable";
}

/**
 * Card KPI com realce de tendência para páginas OPS.
 *
 * Props principais:
 * - `label`: rótulo do indicador
 * - `value`: valor atual
 * - `previousValue`: valor anterior (opcional)
 * - `trend`: `up | down | stable` (opcional)
 * - `deltaLabel`: texto auxiliar de variação (opcional)
 * - `baseStyle`: estilo base do card
 * - `showTrend`: habilita/desabilita destaque de tendência
 */
export default function OpsTrendKpiCard({
  label,
  value,
  previousValue = null,
  trend = null,
  deltaLabel = null,
  auxiliaryLabel = null,
  linkTo = null,
  linkTitle = "Abrir drill-down",
  baseStyle = {},
  showTrend = true,
}) {
  const normalizedTrend = trend ? String(trend).toLowerCase() : "stable";
  const hasTrend =
    showTrend && (normalizedTrend === "up" || normalizedTrend === "down" || normalizedTrend === "stable");
  const trendStyle = getTrendToken(normalizedTrend);

  const resolvedCardStyle = {
    ...baseStyle,
    ...(hasTrend
      ? {
          background: trendStyle.accentBg,
          border: trendStyle.accentBorder,
        }
      : {}),
  };

  const content = (
    <>
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
            flexWrap: "wrap",
          }}
        >
          <span
            style={{
              color: "#94A3B8",
              fontWeight: 600,
            }}
          >
            {previousValue !== null && previousValue !== undefined
              ? `janela anterior: ${previousValue}`
              : "janela anterior: -"}
          </span>
          <span
            style={{
              color: hasTrend ? trendStyle.valueColor : "#E2E8F0",
              fontWeight: 800,
              fontSize: 12,
              letterSpacing: 0.2,
              padding: "2px 8px",
              borderRadius: 999,
              border: hasTrend ? trendStyle.accentBorder : "1px solid rgba(148,163,184,0.45)",
              background: hasTrend ? "rgba(15,23,42,0.45)" : "rgba(15,23,42,0.35)",
            }}
          >
            {`${trendStyle.symbol} ${deltaLabel || "-"}`}
          </span>
        </div>
      ) : null}
      {auxiliaryLabel ? (
        <small
          style={{
            marginTop: 2,
            fontSize: 11,
            color: "#CBD5E1",
            fontWeight: 600,
            display: "block",
          }}
        >
          {auxiliaryLabel}
        </small>
      ) : null}
    </>
  );

  if (linkTo) {
    return (
      <Link
        to={linkTo}
        title={linkTitle}
        style={{
          ...resolvedCardStyle,
          display: "block",
          textDecoration: "none",
          color: "inherit",
          cursor: "pointer",
          boxShadow: "0 0 0 1px rgba(59,130,246,0.22) inset",
        }}
      >
        {content}
      </Link>
    );
  }

  return <article style={resolvedCardStyle}>{content}</article>;
}
