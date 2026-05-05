export interface Locker {
  id: string
  occupancy: number
  status: 'active' | 'maintenance'
}

export interface Manifest {
  id: string
  status: string
}

export interface SLAMetrics {
  compliance_percent?: number
  sla_percent?: number
  percent?: number
  value?: number
}

export interface OpsDashboardSummary {
  lockersAtivos: number
  pickupsHoje: number
  slaPercent: number
  lockers: Locker[]
}

export type Status =
  | 'OPEN'
  | 'COMPUTING'
  | 'APPROVED'
  | 'INVOICED'
  | 'PAID'
  | 'DISPUTED'
  | 'CANCELLED'

export type BillingCycleStatus = Status

export interface BillingCycle {
  id: string
  partner_id: string
  status: Status | string
  amount_cents: number
  currency: string
  created_at: string
  updated_at: string
  period_start?: string
  period_end?: string
  /** Resposta legada da API */
  total_amount_cents?: number
}

export type PartnerInvoiceStatus =
  | 'DRAFT'
  | 'ISSUED'
  | 'SENT'
  | 'VIEWED'
  | 'PAID'
  | 'OVERDUE'
  | 'DISPUTED'
  | 'CANCELLED'

export interface PartnerInvoice {
  id: string
  partner_id: string
  status: PartnerInvoiceStatus | string
  amount_cents: number
  currency: string
  created_at: string
  updated_at: string
  invoice_number?: string
  issued_at?: string
  invoice_id?: string
}

export type CreditNoteStatus =
  | 'PENDING'
  | 'APPROVED'
  | 'APPLIED'
  | 'REFUNDED'
  | 'EXPIRED'
  | 'CANCELLED'

export interface CreditNote {
  id: string
  partner_id: string
  status: CreditNoteStatus | string
  amount_cents: number
  currency: string
  created_at: string
  updated_at: string
  reason_code?: string
  description?: string
  expires_at?: string
  credit_note_id?: string
}

export type DisputeStatus = 'OPEN' | 'UNDER_REVIEW' | 'ACCEPTED' | 'REJECTED' | 'CLOSED'

export interface Dispute {
  id: string
  partner_id: string
  status: DisputeStatus | string
  amount_cents: number
  currency: string
  created_at: string
  updated_at: string
  invoice_id?: string
  reason?: string
  resolved_at?: string
  dispute_id?: string
  history?: unknown
  events?: unknown
}
