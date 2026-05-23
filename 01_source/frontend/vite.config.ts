import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const projectDir = path.dirname(fileURLToPath(import.meta.url))

/** Docker compose expõe partner_service em :8402; uvicorn local costuma usar :8002. */
const partnerServiceProxy = process.env.PARTNER_SERVICE_PROXY ?? 'http://localhost:8402'

/** billing_fiscal_service / stub de integração: MOCK_BILLING=true → 127.0.0.1:8020 por padrão. */
const billingServiceProxy =
  process.env.BILLING_SERVICE_PROXY ??
  (process.env.MOCK_BILLING === 'true' ? 'http://127.0.0.1:8020' : 'http://localhost:8020')

const orderLifecycleServiceProxy =
  process.env.ORDER_LIFECYCLE_SERVICE_PROXY ?? 'http://localhost:8010'

const lockerCreateServiceProxy =
  process.env.LOCKER_CREATE_SERVICE_PROXY ?? 'http://localhost:8015'

const partnerAdminServiceProxy =
  process.env.PARTNER_ADMIN_SERVICE_PROXY ?? 'http://localhost:8016'

const paymentGatewayAdminServiceProxy =
  process.env.PAYMENT_GATEWAY_ADMIN_SERVICE_PROXY ?? 'http://localhost:8017'

const orderPickupAdminServiceProxy =
  process.env.ORDER_PICKUP_ADMIN_SERVICE_PROXY ?? 'http://localhost:8018'

const marketplaceAdminServiceProxy =
  process.env.MARKETPLACE_ADMIN_SERVICE_PROXY ?? 'http://localhost:8019'

const mlAdminServiceProxy =
  process.env.ML_ADMIN_SERVICE_PROXY ?? 'http://localhost:8021'

const privacyComplianceAdminServiceProxy =
  process.env.PRIVACY_COMPLIANCE_ADMIN_SERVICE_PROXY ?? 'http://localhost:8022'

const orderPickupServiceProxy =
  process.env.ORDER_PICKUP_SERVICE_PROXY ?? 'http://localhost:8003'

function redirectRootToV1() {
  const handle = (req: { url?: string }, res: { statusCode: number; setHeader: (name: string, value: string) => void; end: () => void }, next: () => void) => {
    if (req.url === '/' || req.url === '/index.html') {
      res.statusCode = 302
      res.setHeader('Location', '/v1/')
      res.end()
      return
    }
    next()
  }

  return {
    name: 'redirect-root-to-v1',
    configureServer(server: { middlewares: { use: (handler: typeof handle) => void } }) {
      server.middlewares.use(handle)
    },
    configurePreviewServer(server: { middlewares: { use: (handler: typeof handle) => void } }) {
      server.middlewares.use(handle)
    },
  }
}

export default defineConfig({
  cacheDir: path.join(projectDir, '.vite-cache'),
  plugins: [redirectRootToV1(), react()],
  server: {
    proxy: {
      '/auth': {
        target: partnerServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/auth/, ''),
      },
      '/api/billing-svc': {
        target: billingServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/billing-svc/, ''),
      },
      '/api/order-lifecycle': {
        target: orderLifecycleServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/order-lifecycle/, ''),
      },
      '/api/locker-create': {
        target: lockerCreateServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/locker-create/, '/api'),
      },
      '/api/partner-admin': {
        target: partnerAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/partner-admin/, '/api'),
      },
      '/api/payment-gateway-admin': {
        target: paymentGatewayAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/payment-gateway-admin/, '/api'),
      },
      '/api/order-pickup-admin': {
        target: orderPickupAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/order-pickup-admin/, '/api'),
      },
      '/api/marketplace-admin': {
        target: marketplaceAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/marketplace-admin/, '/api'),
      },
      '/api/ml-admin': {
        target: mlAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/ml-admin/, '/api'),
      },
      '/api/privacy-compliance-admin': {
        target: privacyComplianceAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/privacy-compliance-admin/, '/api'),
      },
      '/api/op': {
        target: orderPickupServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/op/, ''),
      },
      '/api/runtime': {
        target: partnerServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/runtime/, '/api'),
      },
      '/api': partnerServiceProxy,
    },
  },
})
