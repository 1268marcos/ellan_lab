import axios, { AxiosError } from 'axios'
import type { BillingCycle, CreditNote, Dispute, PartnerInvoice } from '../types'
import { loadAuth } from './auth'

export type BillingListResponse<T> =
  | T[]
  | { items: T[] }
  | { data: T[] }
  | { cycles: T[] }
  | { invoices: T[] }
  | { credit_notes: T[] }
  | { disputes: T[] }

const api = axios.create({
  baseURL: '/api/billing-svc',
  timeout: 15_000,
})

api.interceptors.request.use((config) => {
  const auth = loadAuth()
  if (auth?.apiKey) {
    config.headers = (config.headers ?? {}) as typeof config.headers
    config.headers['X-API-Key'] = auth.apiKey
    config.headers.Authorization = `Bearer ${auth.token || auth.apiKey}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err: AxiosError) => {
    const msg =
      (err.response?.data as { detail?: string } | undefined)?.detail ??
      err.message ??
      'request failed'
    console.error('[billingApi]', err.response?.status, msg)
    return Promise.reject(err)
  },
)

export type BillingQuery = {
  partner_id?: string
  date_start?: string
  date_end?: string
  cycle_id?: string
  status?: string
  limit?: number
  offset?: number
}

export type ComputeCyclePayload = {
  partner_id: string
  date_start: string
  date_end: string
  dry_run?: boolean
}

export type DisputeInvoicePayload = {
  invoice_id: string
  reason: string
  description?: string
}

export type CancelInvoicePayload = {
  invoice_id: string
  reason?: string
}

export const billingApi = {
  getCycles: (partnerId: string, params?: Omit<BillingQuery, 'partner_id'>) =>
    api.get<BillingListResponse<BillingCycle>>('/v1/billing/cycles', { params: { ...params, partner_id: partnerId } }),
  getInvoices: (partnerId: string, params?: Omit<BillingQuery, 'partner_id'>) =>
    api.get<BillingListResponse<PartnerInvoice>>('/v1/billing/invoices', { params: { ...params, partner_id: partnerId } }),
  getCreditNotes: (partnerId: string, params?: Omit<BillingQuery, 'partner_id'>) =>
    api.get<BillingListResponse<CreditNote>>('/v1/billing/credit-notes', { params: { ...params, partner_id: partnerId } }),
  getDisputes: (partnerId: string, params?: Omit<BillingQuery, 'partner_id'>) =>
    api.get<BillingListResponse<Dispute>>('/v1/billing/disputes', { params: { ...params, partner_id: partnerId } }),
  computeCycle: (payload: ComputeCyclePayload) => api.post('/v1/billing/cycles/compute', payload),
  disputeInvoice: (payload: DisputeInvoicePayload) => api.post('/v1/billing/invoices/dispute', payload),
  cancelInvoice: (payload: CancelInvoicePayload) => api.post('/v1/billing/invoices/cancel', payload),
  applyCreditNote: (id: string, cycleId: string) =>
    api.post('/v1/billing/credit-notes/apply', { credit_note_id: id, cycle_id: cycleId }),
  respondDispute: (id: string, response: string) =>
    api.post('/v1/billing/disputes/respond', { dispute_id: id, response }),
}
