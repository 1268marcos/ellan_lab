import { Navigate, useSearchParams } from "react-router-dom";

/** Compat v1: /ops/products/admin?tab=… → rotas dedicadas do v0 */
const TAB_TARGETS = {
  overview: "/ops/products/professional",
  ecosystem: "/ops/products/ecosystem",
  catalog: "/ops/products/catalog",
  categories: "/ops/products/categories",
  taxonomy: "/ops/products/professional?tab=taxonomy",
  channels: "/ops/products/professional?tab=channels",
  attributes: "/ops/products/professional?tab=attributes",
  bundles: "/ops/products/bundles",
  fiscal: "/ops/products/pricing-fiscal",
  inventory: "/ops/products/inventory-health",
};

export default function OpsProductsAdminRedirect() {
  const [searchParams] = useSearchParams();
  const tab = String(searchParams.get("tab") || "overview").trim().toLowerCase();
  const target = TAB_TARGETS[tab] || TAB_TARGETS.overview;
  return <Navigate to={target} replace />;
}
