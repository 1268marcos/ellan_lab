import { useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsHelpTutorialModal, { type OpsTutorialSection } from "./OpsHelpTutorialModal";
import { resolveOpsTutorial } from "../constants/opsTutorialContent";

interface ResolvedTutorial {
  title: string;
  subtitle?: string;
  sections: OpsTutorialSection[];
}

export default function OpsRouteHelpButton() {
  const location = useLocation();
  const { token, user } = useAuth();
  const routePath = String(location.pathname || "");
  if (!routePath.startsWith("/ops/")) return null;

  const tutorial = resolveOpsTutorial(routePath, null) as ResolvedTutorial;
  const userEmail =
    user && typeof user === "object" && "email" in user && typeof (user as { email?: unknown }).email === "string"
      ? (user as { email: string }).email
      : "anonymous";

  return (
    <OpsHelpTutorialModal
      title={tutorial.title}
      subtitle={tutorial.subtitle}
      sections={tutorial.sections}
      ctaLabel="Abrir registro de atualizações OPS"
      ctaHref="/ops/updates"
      storageKey={routePath.replaceAll("/", "-").replace(/^-+/, "") || "ops"}
      userKey={token ? token.slice(0, 16) : userEmail}
    />
  );
}

