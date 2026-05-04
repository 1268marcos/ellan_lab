import { api } from './client'

export type BalanceOut = { user_id?: string; partner_id?: string; balance: number; version?: number }

export type TxRow = {
  id?: string
  transaction_id?: string
  type?: string
  status?: string
  amount?: number
  created_at?: string
  occurred_at?: string
}

export const walletApi = {
  getBalance: (partnerId: string) =>
    api.get<BalanceOut>(`/wallet/${partnerId}/balance`).catch(() => api.get<BalanceOut>(`/v1/balance/${partnerId}`)),

  getTransactions: (partnerId: string, params?: Record<string, string>) =>
    api.get<TxRow[]>(`/wallet/${partnerId}/transactions`, { params }),

  getExpiredCredits: (partnerId: string) =>
    api
      .get<unknown>(`/wallet/${partnerId}/credits/expired`)
      .catch(() => api.get(`/v1/wallet/${partnerId}/credits/expired`).catch(() => ({ data: [] as unknown }))),

  applyCredit: (partnerId: string, amount: number, orderId: string) =>
    api
      .post(`/wallet/${partnerId}/apply-credit`, { amount, order_id: orderId })
      .catch(() =>
        api.post(`/v1/credit-offer`, {
          user_id: partnerId,
          amount,
          promotional: false,
        }),
      ),

  reconcile: () => api.post(`/wallet/reconcile`).catch(() => api.post(`/v1/reconcile`)),

  getDivergences: () => api.get(`/wallet/divergences`),

  getReconcileHistory: () => api.get(`/wallet/reconcile/history`),
}
