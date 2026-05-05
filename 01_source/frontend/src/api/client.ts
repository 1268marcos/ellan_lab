import axios, { AxiosError } from 'axios'
import { loadAuth } from './auth'

export const api = axios.create({
  baseURL: '/api',
  timeout: 15_000,
})

api.interceptors.request.use((config) => {
  const auth = loadAuth()
  if (auth?.apiKey) {
    config.headers = config.headers ?? {}
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
    console.error('[api]', err.response?.status, msg)
    return Promise.reject(err)
  },
)
