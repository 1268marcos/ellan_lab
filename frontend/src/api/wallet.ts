import { financeApi } from './financeClient'

const api = financeApi

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

export type DivergenceRow = {
  metric?: string
  divergence_percent?: number
  divergence_ratio?: number
  percent?: number
  details?: string
}

export type TransactionsFilter = {
  date_start?: string
  date_end?: string
  type?: 'credit' | 'debit' | ''
  status?: string
}

export const walletApi = {
  getBalance: (partnerId: string) => api.get<BalanceOut>(`/v1/wallet/${partnerId}/balance`),

  getTransactions: (partnerId: string, params?: TransactionsFilter) =>
    api.get<TxRow[]>(`/v1/wallet/${partnerId}/transactions`, { params }),

  getExpiredCredits: (partnerId: string) =>
    api.get<unknown>(`/v1/wallet/${partnerId}/credits/expired`).catch(() => ({ data: [] as unknown })),

  applyCredit: (partnerId: string, amount: number, orderId: string) =>
    api.post(`/v1/wallet/${partnerId}/apply-credit`, { amount, order_id: orderId }),

  reconcile: () => api.post(`/v1/wallet/reconcile`),

  getDivergences: () => api.get<DivergenceRow[]>(`/v1/wallet/divergences`),

  getReconcileHistory: () => api.get<unknown>(`/v1/wallet/reconcile/history`),
}
