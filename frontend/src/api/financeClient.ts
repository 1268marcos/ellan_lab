import axios, { AxiosError } from 'axios'

export const financeApi = axios.create({
  baseURL: '/api/wallet-svc',
  timeout: 15_000,
})

financeApi.interceptors.response.use(
  (r) => r,
  (err: AxiosError) => {
    const msg =
      (err.response?.data as { detail?: string } | undefined)?.detail ??
      err.message ??
      'request failed'
    console.error('[financeApi]', err.response?.status, msg)
    return Promise.reject(err)
  },
)
