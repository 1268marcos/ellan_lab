import { api } from './client'

const BASE = '/api/op/v1/subscriptions-admin'

export type SubscriptionPlan = {
  id: string
  name: string
  code: string
  description?: string | null
  monthly_fee_cents: number
  yearly_fee_cents?: number | null
  free_shipping: boolean
  priority_shelf: boolean
  exclusive_deals: boolean
  priority_support: boolean
  max_orders_per_month?: number | null
  max_discount_pct?: number | null
  features_json?: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export type CustomerSubscription = {
  id: string
  user_id?: string | null
  plan_type: string
  status: string
  monthly_fee_cents: number
  free_shipping: boolean
  priority_shelf: boolean
  exclusive_deals: boolean
  billing_cycle: string
  cancel_at_period_end: boolean
  partner_code?: string | null
  current_period_end?: string | null
  next_billing_at?: string | null
  created_at: string
  updated_at: string
}

export const orderPickupSubscriptionsApi = {
  ecosystemCatalog: () =>
    api.get<{ ok: boolean; catalog: Record<string, unknown> }>(`${BASE}/ecosystem/catalog`),

  priorityPlayers: () =>
    api.get<{ ok: boolean; codes: string[]; items: unknown[]; total: number }>(`${BASE}/players/priority`),

  playersCatalog: (params?: { region?: string; player_type?: string; priority_only?: boolean; segment?: string }) =>
    api.get<{ ok: boolean; items: unknown[]; total: number }>(`${BASE}/players/catalog`, { params }),

  syncGlobalPlayers: () => api.post<{ ok: boolean; synced: Record<string, number> }>(`${BASE}/sync/global-players`),

  syncEcosystemFull: () => api.post<{ ok: boolean; synced: Record<string, number> }>(`${BASE}/sync/ecosystem-full`),

  listEcosystemRelations: (params?: { relation_type?: string; from_player?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem/relations`, { params }),

  listIntegrationChannels: (playerCode?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/ecosystem/integration-channels`, {
      params: playerCode ? { player_code: playerCode } : {},
    }),

  listFoodHandoffs: (foodPlatform?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/ecosystem/food-handoffs`, {
      params: foodPlatform ? { food_platform: foodPlatform } : {},
    }),

  listEcosystemPlayersDb: (params?: { segment?: string; supports_food?: boolean }) =>
    api.get<{ items: unknown[] }>(`${BASE}/ecosystem/players-db`, { params }),

  metricsSummary: () =>
    api.get<{ ok: boolean; summary: Record<string, number> }>(`${BASE}/metrics/summary`),

  seed: () => api.post<{ ok: boolean; seeded: Record<string, number> }>(`${BASE}/seed`),

  listPlans: (params?: { active_only?: boolean }) =>
    api.get<{ items: SubscriptionPlan[]; total: number }>(`${BASE}/plans`, { params }),

  createPlan: (body: Record<string, unknown>) => api.post<SubscriptionPlan>(`${BASE}/plans`, body),

  updatePlan: (planId: string, body: Record<string, unknown>) =>
    api.patch<SubscriptionPlan>(`${BASE}/plans/${encodeURIComponent(planId)}`, body),

  deactivatePlan: (planId: string) => api.delete(`${BASE}/plans/${encodeURIComponent(planId)}`),

  listSubscriptions: (params?: {
    status?: string
    user_id?: string
    plan_type?: string
    partner_code?: string
  }) => api.get<{ items: CustomerSubscription[]; total: number }>(`${BASE}/subscriptions`, { params }),

  getSubscription: (id: string) =>
    api.get<CustomerSubscription>(`${BASE}/subscriptions/${encodeURIComponent(id)}`),

  createSubscription: (body: Record<string, unknown>) =>
    api.post<CustomerSubscription>(`${BASE}/subscriptions`, body),

  updateSubscription: (id: string, body: Record<string, unknown>) =>
    api.patch<CustomerSubscription>(`${BASE}/subscriptions/${encodeURIComponent(id)}`, body),

  cancelSubscription: (id: string, immediate?: boolean) =>
    api.post(`${BASE}/subscriptions/${encodeURIComponent(id)}/cancel`, null, {
      params: immediate ? { immediate: true } : {},
    }),

  renewSubscription: (id: string) =>
    api.post(`${BASE}/subscriptions/${encodeURIComponent(id)}/renew`),

  listBenefitsUsage: (params?: { subscription_id?: string; usage_month?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/benefits-usage`, { params }),

  listUsage: (params?: { subscription_id?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/usage`, { params }),

  listWebhooks: (partnerCode?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/webhooks`, {
      params: partnerCode ? { partner_code: partnerCode } : {},
    }),

  upsertWebhook: (partnerCode: string, body: Record<string, unknown>) =>
    api.put(`${BASE}/webhooks/${encodeURIComponent(partnerCode)}`, body),

  listApiKeys: (partnerCode?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/api-keys`, {
      params: partnerCode ? { partner_code: partnerCode } : {},
    }),

  rotateApiKey: (partnerCode: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/api-keys/${encodeURIComponent(partnerCode)}/rotate`,
    ),

  metricsTrends: (months?: number) =>
    api.get<{ ok: boolean; items: Array<Record<string, unknown>> }>(`${BASE}/metrics/trends`, {
      params: months ? { months } : {},
    }),

  subscription360: (subscriptionId: string) =>
    api.get<Record<string, unknown>>(`${BASE}/subscriptions/${encodeURIComponent(subscriptionId)}/360`),

  listEvents: (params?: { subscription_id?: string; event_type?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/events`, { params }),

  listInvoices: (params?: { subscription_id?: string; status?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/invoices`, { params }),

  generateInvoice: (body: { subscription_id: string; amount_cents?: number }) =>
    api.post(`${BASE}/invoices/generate`, body),

  markInvoicePaid: (invoiceId: string, paymentRef?: string) =>
    api.post(`${BASE}/invoices/${encodeURIComponent(invoiceId)}/mark-paid`, null, {
      params: paymentRef ? { payment_ref: paymentRef } : {},
    }),

  listEntitlements: (params?: { plan_code?: string; player_type?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/entitlements`, { params }),

  upsertEntitlement: (body: Record<string, unknown>) => api.post(`${BASE}/entitlements`, body),

  listPartnerPrograms: (params?: { partner_type?: string; active_only?: boolean }) =>
    api.get<{ items: unknown[] }>(`${BASE}/partner-programs`, { params }),

  createPartnerProgram: (body: Record<string, unknown>) => api.post(`${BASE}/partner-programs`, body),

  listDunning: (params?: { status?: string }) => api.get<{ items: unknown[] }>(`${BASE}/dunning`, { params }),

  resolveDunning: (caseId: string, body?: { resolution_note?: string }) =>
    api.post(`${BASE}/dunning/${encodeURIComponent(caseId)}/resolve`, body ?? {}),

  listWebhookDeliveries: (params?: { endpoint_id?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/webhook-deliveries`, { params }),

  simulateWebhookDelivery: (partnerCode: string, eventType?: string, subscriptionId?: string) =>
    api.post(`${BASE}/webhook-deliveries/simulate`, null, {
      params: {
        partner_code: partnerCode,
        ...(eventType ? { event_type: eventType } : {}),
        ...(subscriptionId ? { subscription_id: subscriptionId } : {}),
      },
    }),

  premiumSeed: () => api.post<{ ok: boolean; seeded: Record<string, number> }>(`${BASE}/premium/seed`),

  benefitCheck: (userId: string, benefitType: string) =>
    api.post<{ eligible: boolean; reason?: string }>(`${BASE}/benefit-check`, {
      user_id: userId,
      benefit_type: benefitType,
    }),

  plansCompareMatrix: () => api.get<{ plans: unknown[] }>(`${BASE}/plans/compare-matrix`),

  healthSummary: () => api.get<{ by_risk: unknown[] }>(`${BASE}/health/summary`),

  computeAllHealth: () => api.post<{ computed: number }>(`${BASE}/health/compute-all`),

  listAtRisk: () => api.get<{ items: unknown[] }>(`${BASE}/health/at-risk`),

  listReferrals: () => api.get<{ items: unknown[] }>(`${BASE}/referrals`),

  createReferral: (body: { referrer_user_id: string; reward_cents?: number }) =>
    api.post(`${BASE}/referrals`, body),

  listGifts: () => api.get<{ items: unknown[] }>(`${BASE}/gifts`),

  issueGift: (body: Record<string, unknown>) => api.post(`${BASE}/gifts/issue`, body),

  loyaltyBalance: (userId: string) => api.get(`${BASE}/loyalty/${encodeURIComponent(userId)}`),

  grantLoyalty: (body: Record<string, unknown>) => api.post(`${BASE}/loyalty/grant`, body),

  listExperiments: () => api.get<{ items: unknown[] }>(`${BASE}/experiments`),

  listRenewalQueue: () => api.get<{ items: unknown[] }>(`${BASE}/renewals/queue`),

  runDueRenewals: () => api.post<{ processed: number }>(`${BASE}/renewals/run-due`),

  listChurnAlerts: () => api.get<{ items: unknown[] }>(`${BASE}/churn/alerts`),

  worldSeed: () => api.post<{ ok: boolean; seeded: Record<string, number> }>(`${BASE}/world/seed`),

  worldSummary: () => api.get<{ counts: Record<string, number>; regions: string[] }>(`${BASE}/world/summary`),

  listRegionalPrices: (params?: { plan_code?: string; region_code?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/world/regional-prices`, { params }),

  listAddonCatalog: () => api.get<{ items: unknown[] }>(`${BASE}/world/addons/catalog`),

  listActiveAddons: (subscriptionId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/world/addons/active`, {
      params: subscriptionId ? { subscription_id: subscriptionId } : {},
    }),

  listPauses: () => api.get<{ items: unknown[] }>(`${BASE}/world/pauses`),

  listSlaTargets: (params?: { plan_code?: string; region_code?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/world/sla-targets`, { params }),

  listSettlements: (params?: { partner_code?: string; status?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/world/settlements`, { params }),

  listRetentionOffers: () => api.get<{ items: unknown[] }>(`${BASE}/world/retention-offers`),

  listConsents: () => api.get<{ items: unknown[] }>(`${BASE}/world/consents`),

  efficiencySeed: () => api.post<{ ok: boolean; seeded: Record<string, number> }>(`${BASE}/efficiency/seed`),

  efficiencySummary: () => api.get<{ counts: Record<string, number> }>(`${BASE}/efficiency/summary`),

  opsInbox: () =>
    api.get<{
      items: Array<{
        kind: string
        id: string
        title?: string
        user_id?: string
        actions?: Array<{ action: string; label: string }>
      }>
      total: number
      bulk_operations?: Array<{ operation: string; label: string }>
    }>(`${BASE}/efficiency/ops-inbox`),

  inboxAct: (body: {
    kind: string
    id: string
    action?: string
    notes?: string
    actor_id?: string
  }) => api.post<{ ok: boolean }>(`${BASE}/efficiency/ops-inbox/act`, body),

  inboxBulk: (operation: 'renewals_run_due' | 'churn_resolve_high' | 'churn_resolve_all') =>
    api.post<{ ok: boolean; processed: number }>(`${BASE}/efficiency/ops-inbox/bulk`, { operation }),

  listPromoCodes: () => api.get<{ items: unknown[] }>(`${BASE}/efficiency/promo-codes`),

  createPromoCode: (body: {
    code: string
    description?: string
    discount_pct?: number
    discount_cents?: number
    bonus_months?: number
    eligible_plans?: string[]
    max_redemptions?: number
    partner_code?: string
  }) => api.post<{ ok: boolean; id: string; code: string }>(`${BASE}/efficiency/promo-codes`, body),

  createAutomationRule: (body: {
    rule_code: string
    name: string
    trigger_event: string
    action_type: string
    config_json?: Record<string, unknown>
    priority?: number
  }) => api.post<{ ok: boolean; id: string }>(`${BASE}/efficiency/automation-rules`, body),

  acceptRetentionOffer: (offerId: string) =>
    api.post<{ ok: boolean }>(`${BASE}/world/retention-offers/${encodeURIComponent(offerId)}/accept`),

  validatePromoCode: (body: { code: string; user_id: string; plan_code: string }) =>
    api.post<{ valid: boolean; reason?: string; discount_pct?: number }>(
      `${BASE}/efficiency/promo-codes/validate`,
      body,
    ),

  listPlanChanges: (subscriptionId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/efficiency/plan-changes`, {
      params: subscriptionId ? { subscription_id: subscriptionId } : {},
    }),

  upgradeMatrix: () => api.get<{ items: unknown[]; period_month: string }>(`${BASE}/efficiency/upgrade-matrix`),

  listAutomationRules: () => api.get<{ items: unknown[] }>(`${BASE}/efficiency/automation-rules`),

  listUsageMeters: (params?: { subscription_id?: string; period_month?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/efficiency/usage-meters`, { params }),
}
