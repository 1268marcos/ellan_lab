import axios, { AxiosError } from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 15_000,
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
