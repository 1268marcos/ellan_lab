import React from "react";
import { Link } from "react-router-dom";
import OpsRouteHelpButton from "./OpsRouteHelpButton";

export default function OpsPageTitleHeader({
  title,
  versionLabel = "",
  versionTo = "",
  versionTitle = "",
  titleStyle = {},
  containerStyle = {},
}) {
  return (
    <div style={{ ...baseContainerStyle, ...containerStyle }}>
      <h1 style={{ ...baseTitleStyle, ...titleStyle }}>{title}</h1>
      {versionLabel ? (
        versionTo ? (
          <Link to={versionTo} style={versionBadgeStyle} title={versionTitle || "Abrir política de versionamento"}>
            {versionLabel}
          </Link>
        ) : (
          <span style={versionBadgeStyle}>{versionLabel}</span>
        )
      ) : null}
      <OpsRouteHelpButton />
    </div>
  );
}

const baseContainerStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
  marginBottom: 8,
};

const baseTitleStyle = {
  marginTop: 0,
  marginBottom: 0,
};

const versionBadgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  padding: "3px 8px",
  borderRadius: 999,
  border: "1px solid rgba(125,211,252,0.55)",
  background: "rgba(14,116,144,0.16)",
  color: "#bae6fd",
  textDecoration: "none",
  fontSize: 11,
  fontWeight: 700,
};
