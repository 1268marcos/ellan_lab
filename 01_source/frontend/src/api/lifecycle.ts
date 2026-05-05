import axios, { type AxiosResponse } from 'axios'

const lifecycleApiClient = axios.create({
  baseURL: '/api/order-lifecycle',
  timeout: 30_000,
})

lifecycleApiClient.interceptors.request.use((config) => {
  const token = import.meta.env.VITE_INTERNAL_TOKEN as string | undefined
  if (token) {
    config.headers = config.headers ?? {}
    config.headers['X-Internal-Token'] = token
  }
  return config
})

export type LifecycleMetricsParams = Record<string, string | number | boolean | undefined | null>
export type LifecycleRankingParams = Record<string, string | number | boolean | undefined | null>

export const lifecycleApi = {
  getHealth: (): Promise<AxiosResponse<unknown>> => lifecycleApiClient.get('/health'),

  getMetrics: (params?: LifecycleMetricsParams): Promise<AxiosResponse<unknown>> =>
    lifecycleApiClient.get('/internal/analytics/pickup-metrics', { params }),

  getRanking: (params?: LifecycleRankingParams): Promise<AxiosResponse<unknown>> =>
    lifecycleApiClient.get('/internal/analytics/pickup-ranking', { params }),

  getPickupHealth: (params?: LifecycleRankingParams): Promise<AxiosResponse<unknown>> =>
    lifecycleApiClient.get('/internal/analytics/pickup-health', { params }),
}
