/** Aba padrão quando o link do menu não traz `?tab=`. */
export const OPS_ROUTE_DEFAULT_TAB: Record<string, string> = {
  '/ops/payments/admin': 'intelligence',
  '/ops/money-cambio/admin': 'overview',
  '/ops/fiscal/admin': 'global',
  '/ops/finance/admin': 'networks',
  '/ops/partners/admin': 'onboarding',
  '/ops/marketplace/admin': 'overview',
  '/ops/ml/admin': 'partners',
  '/ops/rentals/admin': 'networks',
  '/ops/products/admin': 'ecosystem',
  '/ops/privacy-compliance/admin': 'compliance',
  '/ops/access/security-admin': 'overview',
  '/ops/marketing/promotions': 'campaigns',
  '/ops/orders/admin': 'overview',
  /** Rota legada redireciona para hub; default só se a rota existir sem redirect. */
  '/ops/order/deadlines': 'overview',
  '/ops/order-pickup/admin': 'overview',
  '/ops/workers/admin': 'overview',
  '/ops/payment-gateway/admin': 'providers',
  '/ops/hardware/admin': 'dashboard',
}

