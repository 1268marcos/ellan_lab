import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { integrationsViteProxies } from './integrations-vite-proxy.mjs'

const projectDir = path.dirname(fileURLToPath(import.meta.url))
const repoSiblingV0 = path.resolve(projectDir, '../frontend_v0/node_modules')

function xyflowAlias(subpath: string) {
  const local = path.resolve(projectDir, 'node_modules', subpath)
  const fromV0 = path.join(repoSiblingV0, subpath)
  try {
    fs.accessSync(local)
    return local
  } catch {
    return fromV0
  }
}

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

const paymentsAdminServiceProxy =
  process.env.PAYMENTS_ADMIN_SERVICE_PROXY ?? 'http://localhost:8126'

const orderPickupAdminServiceProxy =
  process.env.ORDER_PICKUP_ADMIN_SERVICE_PROXY ?? 'http://localhost:8018'

const marketplaceAdminServiceProxy =
  process.env.MARKETPLACE_ADMIN_SERVICE_PROXY ?? 'http://localhost:8119'

const hardwareAdminServiceProxy =
  process.env.HARDWARE_ADMIN_SERVICE_PROXY ?? 'http://localhost:8025'

const mlAdminServiceProxy =
  process.env.ML_ADMIN_SERVICE_PROXY ?? 'http://localhost:8021'

const privacyComplianceAdminServiceProxy =
  process.env.PRIVACY_COMPLIANCE_ADMIN_SERVICE_PROXY ?? 'http://localhost:8022'

const financeAdminServiceProxy =
  process.env.FINANCE_ADMIN_SERVICE_PROXY ?? 'http://localhost:8123'

const analyticsServiceProxy =
  process.env.ANALYTICS_SERVICE_PROXY ?? 'http://localhost:8127'

const fiscalAdminServiceProxy =
  process.env.FISCAL_ADMIN_SERVICE_PROXY ?? 'http://localhost:8024'

const moneyCambioAdminServiceProxy =
  process.env.MONEY_CAMBIO_ADMIN_SERVICE_PROXY ?? 'http://localhost:8125'

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
  base: '/v1/',
  cacheDir: path.join(projectDir, '.vite-cache'),
  resolve: {
    alias: {
      '@xyflow/react': xyflowAlias('@xyflow/react'),
      '@xyflow/system': xyflowAlias('@xyflow/system'),
    },
  },
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
      '/api/v1/security': {
        target: partnerAdminServiceProxy,
        changeOrigin: true,
      },
      '/api/payment-gateway-admin': {
        target: paymentGatewayAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/payment-gateway-admin/, '/api'),
      },
      '/api/payments-admin': {
        target: paymentsAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/payments-admin/, '/api'),
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
      '/api/hardware-admin': {
        target: hardwareAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/hardware-admin/, '/api'),
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
      '/api/finance-admin': {
        target: financeAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/finance-admin/, '/api'),
      },
      '/api/analytics': {
        target: analyticsServiceProxy,
        changeOrigin: true,
      },
      '/api/fiscal-admin': {
        target: fiscalAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/fiscal-admin/, '/api'),
      },
      '/api/money-cambio-admin': {
        target: moneyCambioAdminServiceProxy,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/money-cambio-admin/, '/api'),
      },
      ...integrationsViteProxies(),
      '/api/v1/partners/login': {
        target: orderPickupServiceProxy,
        changeOrigin: true,
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
