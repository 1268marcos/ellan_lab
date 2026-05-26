import { api } from './client'

const BASE = '/api/op/public/subscriptions'

export type PublicPlan = {
  code: string
  name: string
  monthly_fee_cents: number
  benefits: { free_shipping: boolean; priority_shelf: boolean; exclusive_deals: boolean }
}

export type PromoValidation = {
  ok: boolean
  valid: boolean
  reason?: string
  code?: string
  discount_cents?: number
  discount_pct?: number
  bonus_months?: number
  description?: string
}

export const publicSubscriptionsApi = {
  my: () =>
    api.get<{
      has_subscription: boolean
      subscription?: { plan_type: string; status: string; monthly_fee_cents: number }
      promo_applied?: { promo_code: string; discount_cents: number }
    }>(`${BASE}/my`),

  listPlans: () => api.get<{ items: PublicPlan[]; total: number }>(`${BASE}/my/plans`),

  validatePromo: (code: string, planCode: string) =>
    api.post<PromoValidation>(`${BASE}/promo/validate`, null, {
      params: { code, plan_code: planCode },
    }),

  subscribe: (body: {
    plan_code: string
    billing_cycle?: string
    partner_code?: string
    trial_days?: number
    promo_code?: string
  }) =>
    api.post<{
      has_subscription: boolean
      subscription: { plan_type: string; monthly_fee_cents: number }
      promo_applied?: { promo_code: string; discount_cents: number; bonus_months?: number }
    }>(`${BASE}/my/subscribe`, body),
}
