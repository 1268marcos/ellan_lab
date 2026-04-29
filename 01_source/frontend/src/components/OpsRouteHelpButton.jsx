import React from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsHelpTutorialModal from "./OpsHelpTutorialModal";
import { resolveOpsTutorial } from "../constants/opsTutorialContent";

export default function OpsRouteHelpButton() {
  const location = useLocation();
  const { token, user } = useAuth();
  const routePath = String(location.pathname || "");
  if (!routePath.startsWith("/ops/")) return null;

  const tutorial = resolveOpsTutorial(routePath, null);
  return (
    <OpsHelpTutorialModal
      title={tutorial.title}
      subtitle={tutorial.subtitle}
      sections={tutorial.sections}
      ctaLabel="Abrir registro de atualizações OPS"
      ctaHref="/ops/updates"
      storageKey={routePath.replaceAll("/", "-").replace(/^-+/, "") || "ops"}
      userKey={token ? token.slice(0, 16) : user?.email || "anonymous"}
    />
  );
}
