import { api } from './client'

const BASE = '/api/order-pickup-admin/v1/order-pickup-admin'

export type WorkerQueueStats = {
  domain_event_outbox: Record<string, number>
  lifecycle_deadlines: Record<string, number>
  inventory_sync_queue: Record<string, number>
  worker_dead_letter_queue: Record<string, number>
}

export type LifecycleDeadlineRow = {
  id: string
  deadline_key: string
  order_id: string
  deadline_type: string
  status: string
  due_at: string
  failure_count: number
  created_at: string
}

export type InventorySyncRow = {
  id: string
  product_id: string
  marketplace: string
  status: string
  quantity_available: number
  retry_count: number
  last_error?: string | null
  created_at: string
}

export type WorkerDlqRow = {
  id: string
  worker_name: string
  source_table: string
  source_id: string
  error_message?: string | null
  attempt_count: number
  dead_lettered_at: string
}

export const workersAdminApi = {
  stats: () => api.get<WorkerQueueStats>(`${BASE}/workers/stats`),
  listLifecycle: (params?: { status?: string; deadline_type?: string }) =>
    api.get<{ items: LifecycleDeadlineRow[]; total: number }>(`${BASE}/workers/lifecycle-deadlines`, {
      params,
    }),
  listInventory: (params?: { status?: string; marketplace?: string }) =>
    api.get<{ items: InventorySyncRow[]; total: number }>(`${BASE}/workers/inventory-sync-queue`, {
      params,
    }),
  replayInventory: (id: string) =>
    api.post<InventorySyncRow>(`${BASE}/workers/inventory-sync-queue/${encodeURIComponent(id)}/replay`),
  listDlq: (params?: { worker_name?: string }) =>
    api.get<{ items: WorkerDlqRow[]; total: number }>(`${BASE}/workers/dead-letter-queue`, { params }),
}
