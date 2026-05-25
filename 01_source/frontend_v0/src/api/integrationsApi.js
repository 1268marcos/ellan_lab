import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

export const integrationsApi = {
  listPartners: (params) => api.get('/partners', { params }),
  getPartner: (id) => api.get(`/partners/${encodeURIComponent(id)}`),
  createPartner: (body) => api.post('/partners', body),
  updatePartner: (id, body) => api.put(`/partners/${encodeURIComponent(id)}`, body),
  deletePartner: (id) => api.delete(`/partners/${encodeURIComponent(id)}`),
  listCapabilities: (partnerId) => api.get(`/partners/${encodeURIComponent(partnerId)}/capabilities`),
  createCapability: (partnerId, body) =>
    api.post(`/partners/${encodeURIComponent(partnerId)}/capabilities`, body),
  listMarketplaceConnections: (params) => api.get('/marketplaces/connections', { params }),
  listCarrierRates: (params) => api.get('/carriers/rates', { params }),
  createCarrierRate: (body) => api.post('/carriers/rates', body),
  updateRateLimit: (partnerId, limit_per_minute) =>
    api.put(`/partners/${encodeURIComponent(partnerId)}/rate-limit`, { limit_per_minute }),
  getHealth: (partnerId) => api.get(`/partners/${encodeURIComponent(partnerId)}/health`),
  runHealthCheck: (partnerId, endpoint_url) =>
    api.post(`/partners/${encodeURIComponent(partnerId)}/health/check`, { endpoint_url }),
  testWebhook: (body) => api.post('/partners/webhook/test', body),
}
