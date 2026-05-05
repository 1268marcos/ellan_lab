import axios, { AxiosError, type AxiosInstance, type AxiosResponse } from 'axios'

import { loadAuth } from './auth'

const RUNTIME_TIMEOUT_MS = 8_000

export type InventorySlotRow = {
  slot_number: number | null
  runtime_slot_size: string | null
  runtime_slot_active: boolean | null
  catalog_slot_id: string | null
  slot_label: string | null
  catalog_slot_size: string | null
  catalog_slot_status: string | null
  door_state: string | null
  door_updated_at: string | null
}

export type InventoryLockerBlock = {
  locker_id: string
  machine_id: string | null
  display_name: string | null
  region: string | null
  runtime_active: boolean | null
  runtime_enabled: boolean | null
  topology_version: number | null
  slot_count_total: number | null
  slots: InventorySlotRow[]
}

export type InventoryOccupancy = {
  total_runtime_slot_rows: number
  active_runtime_slots: number
  catalog_available_slots: number
  catalog_non_available_slots: number
}

export type InventoryRuntimePayload = {
  lockers: InventoryLockerBlock[]
  occupancy: InventoryOccupancy
}

export type BffEnvelopeMeta = {
  partner_id: string
  etag?: string
  max_ts?: string | null
  row_count?: number
}

export type InventoryRuntimeResponse = {
  success: boolean
  data: InventoryRuntimePayload | null
  meta: BffEnvelopeMeta
  cached: boolean
}

export type AllocationRow = {
  id: string
  order_id: string
  locker_id: string
  slot: number
  state: string
  created_at?: string | null
  updated_at?: string | null
  allocated_at?: string | null
  released_at?: string | null
  slot_size?: string | null
  release_reason?: string | null
}

export type InventoryAllocationsResponse = {
  success: boolean
  data: { allocations: AllocationRow[] } | null
  meta: BffEnvelopeMeta
  cached: boolean
}

export type RuntimeApiClient = AxiosInstance & {
  getRuntimeInventory: (
    partnerId: string,
    options?: { ifNoneMatch?: string },
  ) => Promise<InventoryRuntimeResponse>
}

export const runtimeApi = axios.create({
  baseURL: '/api/runtime',
  timeout: RUNTIME_TIMEOUT_MS,
}) as RuntimeApiClient

runtimeApi.interceptors.request.use((config) => {
  const auth = loadAuth()
  config.headers = config.headers ?? {}
  if (auth?.apiKey) {
    config.headers['X-API-Key'] = auth.apiKey
  }
  if (auth?.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  } else if (auth?.apiKey) {
    config.headers.Authorization = `Bearer ${auth.apiKey}`
  }
  return config
})

runtimeApi.interceptors.response.use(
  (r: AxiosResponse) => r,
  (err: AxiosError) => {
    const data = err.response?.data as { detail?: string } | undefined
    const msg = data?.detail ?? err.message ?? 'runtime request failed'
    console.error('[runtimeApi]', err.response?.status ?? err.code, msg)
    return Promise.reject(
      err.response?.data != null && typeof err.response.data === 'object'
        ? Object.assign(new Error(msg), { response: err.response })
        : new Error(msg),
    )
  },
)

export async function fetchInventoryRuntime(
  partnerId: string,
  options?: { ifNoneMatch?: string },
): Promise<InventoryRuntimeResponse> {
  const headers: Record<string, string> = {}
  if (options?.ifNoneMatch) {
    headers['If-None-Match'] = options.ifNoneMatch
  }
  const { data } = await runtimeApi.get<InventoryRuntimeResponse>(
    `/partners/${encodeURIComponent(partnerId)}/inventory/runtime`,
    { headers },
  )
  return data
}

runtimeApi.getRuntimeInventory = fetchInventoryRuntime

export async function fetchInventoryAllocations(
  partnerId: string,
  options?: { ifNoneMatch?: string },
): Promise<InventoryAllocationsResponse> {
  const headers: Record<string, string> = {}
  if (options?.ifNoneMatch) {
    headers['If-None-Match'] = options.ifNoneMatch
  }
  const { data } = await runtimeApi.get<InventoryAllocationsResponse>(
    `/partners/${encodeURIComponent(partnerId)}/inventory/allocations`,
    { headers },
  )
  return data
}
