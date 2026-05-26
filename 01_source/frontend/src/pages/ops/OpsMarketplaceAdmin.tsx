import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import {
  marketplaceAdminApi,
  type MarketplaceCommission,
  type MarketplaceSeller,
  type SellerProduct,
  type SellerReview,
} from '../../api/marketplaceAdmin'

const MKA = '/api/marketplace-admin/v1/marketplace-admin'

type Tab =
  | 'overview'
  | 'sellers'
  | 'products'
  | 'categories'
  | 'channels'
  | 'readiness'
  | 'commissions'
  | 'settlements'
  | 'payouts'
  | 'contacts'
  | 'reviews'
  | 'kyc'
  | 'disputes'
  | 'integrations'
  | 'audit'
  | 'tiers'
  | 'compliance'
  | 'performance'
  | 'agreements'
  | 'risk'
  | 'intelligence'
  | 'operations'

const TAB_KEYS: Tab[] = [
  'overview',
  'sellers',
  'products',
  'categories',
  'channels',
  'readiness',
  'commissions',
  'settlements',
  'payouts',
  'contacts',
  'reviews',
  'kyc',
  'disputes',
  'integrations',
  'audit',
  'tiers',
  'compliance',
  'performance',
  'agreements',
  'risk',
  'intelligence',
  'operations',
]

const tabs: { key: Tab; label: string }[] = [
  { key: 'overview', label: 'Visão geral' },
  { key: 'sellers', label: 'Sellers' },
  { key: 'products', label: 'Produtos' },
  { key: 'categories', label: 'Categorias' },
  { key: 'channels', label: 'Canais e redes' },
  { key: 'readiness', label: 'Prontidão integração' },
  { key: 'commissions', label: 'Comissões' },
  { key: 'settlements', label: 'Repasses' },
  { key: 'payouts', label: 'Contas PIX' },
  { key: 'contacts', label: 'Contatos' },
  { key: 'reviews', label: 'Avaliações' },
  { key: 'kyc', label: 'KYC' },
  { key: 'disputes', label: 'Disputas' },
  { key: 'integrations', label: 'Webhooks & API keys' },
  { key: 'audit', label: 'Auditoria sync' },
  { key: 'tiers', label: 'Programas & tiers' },
  { key: 'compliance', label: 'Compliance fiscal' },
  { key: 'performance', label: 'Performance' },
  { key: 'agreements', label: 'Contratos' },
  { key: 'risk', label: 'Risco' },
  { key: 'intelligence', label: 'Ops intelligence' },
  { key: 'operations', label: 'Operações seller' },
]

type ChannelPartner = {
  id: string
  code: string
  name: string
  parent_group?: string
  partner_role?: string
  integration_mode?: string
  country?: string
  capabilities?: unknown[]
  supports_lockers?: boolean
  locker_operator_ref?: string
}

type ReadinessRow = {
  channel_partner_id: string
  partner_code: string
  readiness_band: string
  score_total: number
  score_capabilities: number
  score_api: number
  score_operations: number
  blockers?: string[]
}

type IntegrationIncident = {
  id: string
  partner_code: string
  severity: string
  incident_type: string
  title: string
  status: string
}

type IntegrationHub = {
  readiness_rows: number
  avg_score: number
  bands: Record<string, number>
  open_incidents: number
  open_readiness_alerts: number
  partners_with_blockers: number
  top_go_live: { partner_code?: string; score_total?: number }[]
}

const inp =
  'ellan-field dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100'

function formatBrl(cents: number | null | undefined) {
  const n = Number(cents)
  if (!Number.isFinite(n)) return '—'
  return `R$ ${(n / 100).toFixed(2)}`
}

function partnersFromPayload(data: { partners?: ChannelPartner[]; items?: ChannelPartner[] }) {
  return data.partners ?? data.items ?? []
}

const mkaExtra = {
  listCategoryLinks: (seller_id?: string) =>
    api.get<{ links: { id: string; seller_id: string; category_id: string; is_primary?: boolean }[] }>(
      `${MKA}/seller-category-links`,
      { params: seller_id ? { seller_id } : undefined },
    ),
  linkCategory: (body: Record<string, unknown>) => api.post(`${MKA}/seller-category-links`, body),
  listChannelListings: (seller_id?: string) =>
    api.get<{ listings: { id: string; seller_id: string; channel_partner_id: string; external_store_id?: string; listing_status?: string }[] }>(
      `${MKA}/seller-channel-listings`,
      { params: seller_id ? { seller_id } : undefined },
    ),
  createChannelListing: (body: Record<string, unknown>) => api.post(`${MKA}/seller-channel-listings`, body),
  listLockerNetworkLinks: (seller_id?: string) =>
    api.get<{ links: { id: string; seller_id: string; channel_partner_id: string; locker_id?: string; priority?: number }[] }>(
      `${MKA}/seller-locker-network-links`,
      { params: seller_id ? { seller_id } : undefined },
    ),
  createLockerNetworkLink: (body: Record<string, unknown>) => api.post(`${MKA}/seller-locker-network-links`, body),
}

const emptySeller = () => ({
  legal_name: '',
  trade_name: '',
  tax_id: '',
  email: '',
  commission_pct: '5.00',
})

const emptyProduct = () => ({
  locker_id: '',
  product_id: '',
  price_cents: '',
  quantity: '1',
})

export default function OpsMarketplaceAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [tab, setTab] = useState<Tab>('overview')
  const [dashboard, setDashboard] = useState<Record<string, number | null> | null>(null)
  const [integrationHub, setIntegrationHub] = useState<IntegrationHub | null>(null)
  const [sellers, setSellers] = useState<MarketplaceSeller[]>([])
  const [products, setProducts] = useState<SellerProduct[]>([])
  const [commissions, setCommissions] = useState<MarketplaceCommission[]>([])
  const [reviews, setReviews] = useState<SellerReview[]>([])
  const [categories, setCategories] = useState<{ id: string; code: string; name: string; active?: boolean }[]>([])
  const [categoryLinks, setCategoryLinks] = useState<{ id: string; seller_id: string; category_id: string; is_primary?: boolean }[]>([])
  const [contacts, setContacts] = useState<{ id: string; name: string; email?: string; phone?: string; contact_type?: string; is_primary?: boolean }[]>([])
  const [payoutAccounts, setPayoutAccounts] = useState<{ id: string; holder_name: string; pix_key?: string; account_number?: string; account_type?: string; verified?: boolean; is_default?: boolean }[]>([])
  const [settlementBatches, setSettlementBatches] = useState<{ id: string; period_start: string; period_end: string; net_payout_cents: number; status: string; commission_count: number }[]>([])
  const [kycDocs, setKycDocs] = useState<{ id: string; seller_id: string; doc_type: string; status: string; file_ref?: string }[]>([])
  const [disputes, setDisputes] = useState<{ id: string; seller_id: string; commission_id: string; status: string; reason?: string }[]>([])
  const [channelPartners, setChannelPartners] = useState<ChannelPartner[]>([])
  const [channelListings, setChannelListings] = useState<{ id: string; seller_id: string; channel_partner_id: string; external_store_id?: string; listing_status?: string }[]>([])
  const [lockerNetworkLinks, setLockerNetworkLinks] = useState<{ id: string; seller_id: string; channel_partner_id: string; locker_id?: string; priority?: number }[]>([])
  const [readinessRows, setReadinessRows] = useState<ReadinessRow[]>([])
  const [integrationIncidents, setIntegrationIncidents] = useState<IntegrationIncident[]>([])
  const [readinessAlerts, setReadinessAlerts] = useState<Record<string, unknown>[]>([])
  const [mktGlobalCorridors, setMktGlobalCorridors] = useState<{ corridor_code: string; name: string; steps: { partner_code: string }[] }[]>([])
  const [mktGlobalOpsSummary, setMktGlobalOpsSummary] = useState<Record<string, unknown> | null>(null)
  const [capabilityWebhooks, setCapabilityWebhooks] = useState<Record<string, unknown>[]>([])
  const [channelParentGroup, setChannelParentGroup] = useState('')
  const [sellerForm, setSellerForm] = useState(emptySeller)
  const [productForm, setProductForm] = useState(emptyProduct)
  const [categoryForm, setCategoryForm] = useState({ code: '', name: '' })
  const [categoryLinkCategoryId, setCategoryLinkCategoryId] = useState('')
  const [contactForm, setContactForm] = useState({ name: '', email: '', contact_type: 'PRIMARY' })
  const [payoutForm, setPayoutForm] = useState({ pix_key: '', holder_name: '', account_type: 'PIX' })
  const [kycForm, setKycForm] = useState({ doc_type: 'CNPJ_CARD', file_ref: '' })
  const [disputeForm, setDisputeForm] = useState({ commission_id: '', reason: '' })
  const [listingChannelId, setListingChannelId] = useState('')
  const [listingStoreId, setListingStoreId] = useState('')
  const [networkChannelId, setNetworkChannelId] = useState('')
  const [networkLockerId, setNetworkLockerId] = useState('')
  const [capWebhookPartnerId, setCapWebhookPartnerId] = useState('')
  const [capWebhookCode, setCapWebhookCode] = useState('LOCKER_INVENTORY')
  const [capWebhookUrl, setCapWebhookUrl] = useState('')
  const [selectedId, setSelectedId] = useState('')
  const [selectedCommissionId, setSelectedCommissionId] = useState('')
  const [selectedBatchId, setSelectedBatchId] = useState('')
  const [selectedKycId, setSelectedKycId] = useState('')
  const [selectedDisputeId, setSelectedDisputeId] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [sellerApiKeys, setSellerApiKeys] = useState<{ id: string; key_prefix: string; revoked_at?: string }[]>([])
  const [sellerWebhookConfig, setSellerWebhookConfig] = useState<{ url?: string; events_json?: string; active?: boolean } | null>(null)
  const [settlementItems, setSettlementItems] = useState<{ id: string; order_id: string; net_to_seller_cents: number }[]>([])
  const [syncAuditRows, setSyncAuditRows] = useState<{ id: string; event_type: string; summary: string; created_at: string }[]>([])
  const [commissionPreview, setCommissionPreview] = useState<Record<string, number> | null>(null)
  const [previewPriceCents, setPreviewPriceCents] = useState('4990')
  const [profSummary, setProfSummary] = useState<Record<string, number | string | null> | null>(null)
  const [tierDefs, setTierDefs] = useState<{ code: string; name: string; min_gmv_cents: number }[]>([])
  const [tierEnrollments, setTierEnrollments] = useState<{ id: string; tier_code: string; status: string; effective_from: string }[]>([])
  const [complianceProfiles, setComplianceProfiles] = useState<{ id: string; country: string; tax_regime: string; fiscal_status: string; ioss_number?: string }[]>([])
  const [performanceRows, setPerformanceRows] = useState<{ id: string; month: string; gmv_cents: number; order_count: number; on_time_pickup_pct?: number }[]>([])
  const [agreements, setAgreements] = useState<{ id: string; agreement_type: string; version: string; status: string }[]>([])
  const [riskAssessments, setRiskAssessments] = useState<{ id: string; risk_score: number; risk_band: string; assessed_at: string }[]>([])
  const [tierEnrollCode, setTierEnrollCode] = useState('GROWTH')
  const [complianceForm, setComplianceForm] = useState({ country: 'PT', tax_regime: 'NORMAL', vat_number: '', ioss_number: '' })
  const [riskScore, setRiskScore] = useState('50')
  const [worldPriorityPlayers, setWorldPriorityPlayers] = useState<
    { code: string; role: string; readiness_band?: string; score_total?: number; in_catalog?: boolean }[]
  >([])
  const [sellerCoverage, setSellerCoverage] = useState<{
    coverage_pct?: number
    coverage_complete_count?: number
    players?: { partner_code: string; has_marketplace_listing: boolean; has_locker_network: boolean; coverage_complete: boolean }[]
  } | null>(null)
  const [opsIntelSummary, setOpsIntelSummary] = useState<Record<string, number> | null>(null)
  const [opsPlaybooks, setOpsPlaybooks] = useState<{ code: string; name: string; severity: string; trigger_type: string; steps: { action: string }[] }[]>([])
  const [sellerHealth, setSellerHealth] = useState<{ health_score: number; health_band: string; factors: string[] } | null>(null)
  const [channelQuotas, setChannelQuotas] = useState<{ partner_code?: string; quota_status: string; utilization_skus_pct: number; utilization_orders_pct: number }[]>([])
  const [catalogSyncJobs, setCatalogSyncJobs] = useState<{ id: string; partner_code?: string; job_type: string; status: string; items_ok: number; items_failed: number }[]>([])
  const [crossBorderProfiles, setCrossBorderProfiles] = useState<{ corridor_code: string; customs_scheme: string; status: string; dest_country: string }[]>([])
  const [partnerApiHealth, setPartnerApiHealth] = useState<{ partner_code: string; health_status: string; availability_pct: number; p95_latency_ms: number }[]>([])
  const [sellerPromotions, setSellerPromotions] = useState<{ campaign_code: string; name: string; status: string; discount_pct?: number }[]>([])
  const [opsSummary, setOpsSummary] = useState<Record<string, unknown> | null>(null)
  const [onboardingTasks, setOnboardingTasks] = useState<{ id: string; task_code: string; title: string; status: string; category: string }[]>([])
  const [onboardingProgress, setOnboardingProgress] = useState(0)
  const [skuMaps, setSkuMaps] = useState<{ partner_code?: string; internal_sku: string; channel_sku: string }[]>([])
  const [pricingRules, setPricingRules] = useState<{ name: string; rule_type: string; partner_code?: string }[]>([])
  const [returnPolicies, setReturnPolicies] = useState<{ policy_code: string; return_window_days: number }[]>([])
  const [notifSubs, setNotifSubs] = useState<{ event_type: string; channel: string; destination: string }[]>([])
  const [invAllocations, setInvAllocations] = useState<{ partner_code?: string; allocated_qty: number; available_qty: number }[]>([])
  const [fulfillmentPrefs, setFulfillmentPrefs] = useState<Record<string, unknown> | null>(null)
  const [pricingPreview, setPricingPreview] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const selectedSeller = sellers.find((s) => s.id === selectedId)
  const sellerParams = selectedId ? { seller_id: selectedId } : undefined

  const channelName = useCallback(
    (id: string) => channelPartners.find((p) => p.id === id)?.name || id,
    [channelPartners],
  )

  const filteredChannelPartners = useMemo(() => {
    if (!channelParentGroup) return channelPartners
    return channelPartners.filter((p) => p.parent_group === channelParentGroup)
  }, [channelPartners, channelParentGroup])

  const channelParentGroups = useMemo(() => {
    const groups = new Set(channelPartners.map((p) => p.parent_group).filter(Boolean))
    return [...groups].sort() as string[]
  }, [channelPartners])

  const setTabAndUrl = (next: Tab) => {
    setTab(next)
    if (next === 'overview') setSearchParams({}, { replace: true })
    else setSearchParams({ tab: next }, { replace: true })
  }

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const chParams = channelParentGroup
        ? ({ parent_group: channelParentGroup } as { parent_group?: string; lockers_only?: boolean })
        : undefined
      const [
        dash,
        s,
        p,
        c,
        r,
        cats,
        links,
        cont,
        pay,
        batches,
        kyc,
        disp,
        chp,
        chl,
        lnk,
        rd,
        inc,
        hub,
        alerts,
        hooks,
        auditLog,
        apiKeysRes,
        webhookRes,
        profSum,
        tiersDef,
        tiersEnr,
        compProf,
        perfRows,
        agrRows,
        riskRows,
        worldPlayers,
        sellerCov,
        opsSum,
        opsPb,
        opsHealth,
        opsQuotas,
        opsJobs,
        opsXb,
        opsApiH,
        opsPromo,
        sopSum,
        sopOnb,
        sopSku,
        sopPrice,
        sopRet,
        sopNotif,
        sopAlloc,
        sopFulfill,
      ] = await Promise.all([
        marketplaceAdminApi.getDashboard(),
        marketplaceAdminApi.listSellers(),
        marketplaceAdminApi.listProducts(sellerParams),
        marketplaceAdminApi.listCommissions(sellerParams),
        marketplaceAdminApi.listReviews(sellerParams),
        marketplaceAdminApi.listCategories(),
        mkaExtra.listCategoryLinks(selectedId || undefined),
        marketplaceAdminApi.listContacts(selectedId || undefined),
        marketplaceAdminApi.listPayoutAccounts(selectedId || undefined),
        marketplaceAdminApi.listSettlementBatches(selectedId || undefined),
        marketplaceAdminApi.listKyc(selectedId || undefined),
        marketplaceAdminApi.listDisputes(selectedId || undefined),
        marketplaceAdminApi.listChannelPartners(
          chParams as { lockers_only?: boolean; active_only?: boolean; parent_group?: string },
        ),
        mkaExtra.listChannelListings(selectedId || undefined),
        mkaExtra.listLockerNetworkLinks(selectedId || undefined),
        marketplaceAdminApi.listIntegrationReadiness({ limit: 120 }),
        marketplaceAdminApi.listIntegrationIncidents(false),
        marketplaceAdminApi.integrationHubSummary(),
        marketplaceAdminApi.listReadinessAlerts(false),
        marketplaceAdminApi.listCapabilityWebhooks(),
        marketplaceAdminApi.listSyncAuditLog(40),
        selectedId
          ? marketplaceAdminApi.listApiKeys(selectedId).catch(() => ({ data: { keys: [] as { id: string; key_prefix: string; revoked_at?: string }[] } }))
          : Promise.resolve({ data: { keys: [] as { id: string; key_prefix: string; revoked_at?: string }[] } }),
        selectedId
          ? marketplaceAdminApi.getSellerWebhook(selectedId).catch(() => ({ data: null }))
          : Promise.resolve({ data: null }),
        marketplaceAdminApi.sellerProfessionalSummary(selectedId || undefined),
        marketplaceAdminApi.listTierDefinitions(),
        marketplaceAdminApi.listTierEnrollments(selectedId || undefined),
        marketplaceAdminApi.listComplianceProfiles(selectedId || undefined),
        marketplaceAdminApi.listPerformanceMonthly(selectedId || undefined),
        marketplaceAdminApi.listAgreements(selectedId || undefined),
        marketplaceAdminApi.listRiskAssessments(selectedId || undefined),
        marketplaceAdminApi.listWorldPriorityPlayers(),
        selectedId ? marketplaceAdminApi.getSellerPlayerCoverage(selectedId) : Promise.resolve({ data: null }),
        marketplaceAdminApi.getOpsIntelligenceSummary().catch(() => ({ data: null })),
        marketplaceAdminApi.listOpsPlaybooks().catch(() => ({ data: { playbooks: [] } })),
        selectedId
          ? marketplaceAdminApi.listSellerHealth(selectedId).catch(() => ({ data: { snapshots: [] } }))
          : Promise.resolve({ data: { snapshots: [] } }),
        selectedId
          ? marketplaceAdminApi.listSellerChannelQuotas(selectedId).catch(() => ({ data: { quotas: [] } }))
          : Promise.resolve({ data: { quotas: [] } }),
        marketplaceAdminApi.listCatalogSyncJobs(selectedId ? { seller_id: selectedId } : undefined).catch(() => ({ data: { jobs: [] } })),
        selectedId
          ? marketplaceAdminApi.listCrossBorderProfiles(selectedId).catch(() => ({ data: { profiles: [] } }))
          : Promise.resolve({ data: { profiles: [] } }),
        marketplaceAdminApi.listPartnerApiHealth(true).catch(() => ({ data: { snapshots: [] } })),
        selectedId
          ? marketplaceAdminApi.listSellerPromotions(selectedId).catch(() => ({ data: { campaigns: [] } }))
          : Promise.resolve({ data: { campaigns: [] } })),
        selectedId
          ? marketplaceAdminApi.getSellerOperationsSummary(selectedId).catch(() => ({ data: null }))
          : Promise.resolve({ data: null }),
        selectedId
          ? marketplaceAdminApi.listOnboardingTasks(selectedId).catch(() => ({ data: { tasks: [], progress_pct: 0 } }))
          : Promise.resolve({ data: { tasks: [], progress_pct: 0 } }),
        selectedId
          ? marketplaceAdminApi.listChannelSkuMaps(selectedId).catch(() => ({ data: { maps: [] } }))
          : Promise.resolve({ data: { maps: [] } }),
        selectedId
          ? marketplaceAdminApi.listSellerPricingRules(selectedId).catch(() => ({ data: { rules: [] } }))
          : Promise.resolve({ data: { rules: [] } }),
        selectedId
          ? marketplaceAdminApi.listReturnPolicies(selectedId).catch(() => ({ data: { policies: [] } }))
          : Promise.resolve({ data: { policies: [] } }),
        selectedId
          ? marketplaceAdminApi.listNotificationSubscriptions(selectedId).catch(() => ({ data: { subscriptions: [] } }))
          : Promise.resolve({ data: { subscriptions: [] } }),
        selectedId
          ? marketplaceAdminApi.listInventoryAllocations(selectedId).catch(() => ({ data: { allocations: [] } }))
          : Promise.resolve({ data: { allocations: [] } }),
        selectedId
          ? marketplaceAdminApi.getFulfillmentPreferences(selectedId).catch(() => ({ data: null }))
          : Promise.resolve({ data: null }),
      ])
      const sellerList = s.data.sellers ?? []
      setDashboard(dash.data)
      setSellers(sellerList)
      setProducts(p.data.products ?? [])
      const commList = c.data.commissions ?? []
      setCommissions(commList)
      setReviews(r.data.reviews ?? [])
      setCategories((cats.data.categories ?? []) as typeof categories)
      setCategoryLinks(links.data.links ?? [])
      setContacts((cont.data.contacts ?? []) as typeof contacts)
      setPayoutAccounts((pay.data.accounts ?? []) as typeof payoutAccounts)
      const batchList = (batches.data.batches ?? []) as typeof settlementBatches
      setSettlementBatches(batchList)
      const kycList = (kyc.data.documents ?? []) as typeof kycDocs
      setKycDocs(kycList)
      const dispList = (disp.data.disputes ?? []) as typeof disputes
      setDisputes(dispList)
      setChannelPartners(partnersFromPayload(chp.data as { partners?: ChannelPartner[]; items?: ChannelPartner[] }))
      setChannelListings(chl.data.listings ?? [])
      setLockerNetworkLinks(lnk.data.links ?? [])
      setReadinessRows((rd.data.items ?? []) as ReadinessRow[])
      setIntegrationIncidents((inc.data.items ?? []) as IntegrationIncident[])
      setIntegrationHub(hub.data as IntegrationHub)
      setReadinessAlerts((alerts.data.items ?? []) as Record<string, unknown>[])
      setCapabilityWebhooks((hooks.data.items ?? []) as Record<string, unknown>[])
      setSyncAuditRows((auditLog.data.items ?? []) as typeof syncAuditRows)
      setSellerApiKeys(apiKeysRes.data.keys ?? [])
      const wh = webhookRes.data as { url?: string; events_json?: string; active?: boolean } | null
      setSellerWebhookConfig(wh)
      if (wh?.url) setWebhookUrl(wh.url)
      setProfSummary(profSum.data as Record<string, number | string | null>)
      setTierDefs((tiersDef.data.tiers ?? []) as typeof tierDefs)
      setTierEnrollments((tiersEnr.data.enrollments ?? []) as typeof tierEnrollments)
      setComplianceProfiles((compProf.data.profiles ?? []) as typeof complianceProfiles)
      setPerformanceRows((perfRows.data.rows ?? []) as typeof performanceRows)
      setAgreements((agrRows.data.agreements ?? []) as typeof agreements)
      setRiskAssessments((riskRows.data.assessments ?? []) as typeof riskAssessments)
      setWorldPriorityPlayers((worldPlayers.data.players ?? []) as typeof worldPriorityPlayers)
      setSellerCoverage(sellerCov.data as typeof sellerCoverage)
      setOpsIntelSummary((opsSum.data as Record<string, number>) ?? null)
      setOpsPlaybooks((opsPb.data.playbooks ?? []) as typeof opsPlaybooks)
      const healthSnap = (opsHealth.data.snapshots ?? [])[0] as { health_score: number; health_band: string; factors?: string[] } | undefined
      setSellerHealth(healthSnap ? { health_score: Number(healthSnap.health_score), health_band: healthSnap.health_band, factors: healthSnap.factors ?? [] } : null)
      setChannelQuotas((opsQuotas.data.quotas ?? []) as typeof channelQuotas)
      setCatalogSyncJobs((opsJobs.data.jobs ?? []) as typeof catalogSyncJobs)
      setCrossBorderProfiles((opsXb.data.profiles ?? []) as typeof crossBorderProfiles)
      setPartnerApiHealth((opsApiH.data.snapshots ?? []) as typeof partnerApiHealth)
      setSellerPromotions((opsPromo.data.campaigns ?? []) as typeof sellerPromotions)
      setOpsSummary((sopSum.data as Record<string, unknown>) ?? null)
      setOnboardingTasks((sopOnb.data.tasks ?? []) as typeof onboardingTasks)
      setOnboardingProgress(Number(sopOnb.data.progress_pct ?? 0))
      setSkuMaps((sopSku.data.maps ?? []) as typeof skuMaps)
      setPricingRules((sopPrice.data.rules ?? []) as typeof pricingRules)
      setReturnPolicies((sopRet.data.policies ?? []) as typeof returnPolicies)
      setNotifSubs((sopNotif.data.subscriptions ?? []) as typeof notifSubs)
      setInvAllocations((sopAlloc.data.allocations ?? []) as typeof invAllocations)
      setFulfillmentPrefs((sopFulfill.data as Record<string, unknown>) ?? null)
      setSelectedId((prev) => prev || sellerList[0]?.id || '')
      const pending = commList.filter((x) => x.status === 'PENDING')
      setSelectedCommissionId((prev) => prev || pending[0]?.id || '')
      setSelectedBatchId((prev) => prev || batchList[0]?.id || '')
      setSelectedKycId((prev) => prev || kycList.filter((d) => d.status === 'PENDING')[0]?.id || '')
      setSelectedDisputeId((prev) => prev || dispList.filter((d) => d.status === 'OPEN')[0]?.id || '')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [selectedId, channelParentGroup])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    const q = searchParams.get('tab') as Tab | null
    if (q && TAB_KEYS.includes(q)) setTab(q)
    else if (!q) setTab('overview')
  }, [searchParams])

  useEffect(() => {
    if (!selectedBatchId || tab !== 'settlements') {
      setSettlementItems([])
      return
    }
    void marketplaceAdminApi.listSettlementItems(selectedBatchId).then((r) => {
      setSettlementItems(r.data.items ?? [])
    })
  }, [selectedBatchId, tab])

  const run = async (fn: () => Promise<void>, okMsg: string) => {
    setLoading(true)
    setError(null)
    try {
      await fn()
      setMessage(okMsg)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na operação')
    } finally {
      setLoading(false)
    }
  }

  const onSeed = () => run(() => marketplaceAdminApi.seed().then(() => undefined), 'Seed aplicado.')

  const onSeedChannelPlayers = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await marketplaceAdminApi.seedChannelPlayers()
      const j = data as { inserted?: number; updated?: number; capabilities?: number }
      setMessage(
        `Catálogo sincronizado: +${j.inserted ?? 0} novos, ${j.updated ?? 0} atualizados, ${j.capabilities ?? 0} capacidades novas.`,
      )
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao sincronizar players')
    } finally {
      setLoading(false)
    }
  }

  const onCreateSeller = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const { data } = await marketplaceAdminApi.createSeller(sellerForm)
      setMessage(`Seller ${data.legal_name} criado.`)
      setSelectedId(data.id)
      setSellerForm(emptySeller())
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar seller')
    } finally {
      setLoading(false)
    }
  }

  const onCreateProduct = async (e: FormEvent) => {
    e.preventDefault()
    if (!selectedId) return
    setLoading(true)
    setError(null)
    try {
      await marketplaceAdminApi.createProduct({
        seller_id: selectedId,
        locker_id: productForm.locker_id,
        product_id: productForm.product_id,
        price_cents: Number(productForm.price_cents) || 0,
        quantity: Number(productForm.quantity) || 0,
      })
      setMessage(`Produto ${productForm.product_id} criado.`)
      setProductForm(emptyProduct())
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar produto')
    } finally {
      setLoading(false)
    }
  }

  const onApproveSeller = () => {
    if (!selectedId || selectedSeller?.status !== 'PENDING_APPROVAL') return
    run(
      () => marketplaceAdminApi.updateSeller(selectedId, { status: 'ACTIVE' }).then(() => undefined),
      `Seller ${selectedId} aprovado (ACTIVE).`,
    )
  }

  const onWebhook = async () => {
    if (!selectedId || !webhookUrl) return
    setLoading(true)
    try {
      await marketplaceAdminApi.configureWebhook(selectedId, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['order.created', 'commission.settled'],
      })
      setMessage('Webhook salvo.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedId) return
    setLoading(true)
    try {
      const { data } = await marketplaceAdminApi.rotateApiKey(selectedId)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…). Copie agora.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar chave')
    } finally {
      setLoading(false)
    }
  }

  const onSettleCommission = () => {
    if (!selectedCommissionId) return
    run(
      () => marketplaceAdminApi.updateCommission(selectedCommissionId, { status: 'SETTLED' }).then(() => undefined),
      `Comissão ${selectedCommissionId} liquidada.`,
    )
  }

  const onCreateCategory = () =>
    run(async () => {
      await marketplaceAdminApi.createCategory(categoryForm)
      setCategoryForm({ code: '', name: '' })
    }, `Categoria ${categoryForm.code} criada.`)

  const onLinkCategory = () => {
    if (!selectedId || !categoryLinkCategoryId) return
    run(
      () =>
        mkaExtra
          .linkCategory({ seller_id: selectedId, category_id: categoryLinkCategoryId, is_primary: false })
          .then(() => undefined),
      'Categoria vinculada ao seller.',
    )
  }

  const onCreateContact = () => {
    if (!selectedId || !contactForm.name) return
    run(async () => {
      await marketplaceAdminApi.createContact({ seller_id: selectedId, ...contactForm })
      setContactForm({ name: '', email: '', contact_type: 'PRIMARY' })
    }, `Contato ${contactForm.name} criado.`)
  }

  const onCreatePayout = () => {
    if (!selectedId || !payoutForm.holder_name) return
    run(async () => {
      await marketplaceAdminApi.createPayoutAccount({ seller_id: selectedId, is_default: true, ...payoutForm })
      setPayoutForm({ pix_key: '', holder_name: '', account_type: 'PIX' })
    }, 'Conta de repasse criada.')
  }

  const onCreateSettlement = async () => {
    if (!selectedId) return
    const today = new Date().toISOString().slice(0, 10)
    const start = `${today.slice(0, 8)}01`
    setLoading(true)
    setError(null)
    try {
      const { data } = await marketplaceAdminApi.createSettlementBatch({
        seller_id: selectedId,
        period_start: start,
        period_end: today,
        fees_cents: 0,
      })
      const j = data as { id: string; commission_count?: number }
      setSelectedBatchId(j.id)
      setMessage(`Lote ${j.id} criado (${j.commission_count ?? 0} comissões).`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar lote')
    } finally {
      setLoading(false)
    }
  }

  const onMarkBatchPaid = () => {
    if (!selectedBatchId) return
    run(
      () =>
        marketplaceAdminApi
          .updateSettlementBatch(selectedBatchId, { status: 'PAID', settlement_ref: `PIX-${Date.now()}` })
          .then(() => undefined),
      `Lote ${selectedBatchId} marcado como PAID.`,
    )
  }

  const onCreateKyc = () => {
    if (!selectedId) return
    run(() => marketplaceAdminApi.createKyc({ seller_id: selectedId, ...kycForm }).then(() => undefined), 'Documento KYC registrado.')
  }

  const onApproveKyc = () => {
    if (!selectedKycId) return
    run(
      () => marketplaceAdminApi.updateKyc(selectedKycId, { status: 'APPROVED' }).then(() => undefined),
      `KYC ${selectedKycId} aprovado.`,
    )
  }

  const onCreateDispute = () => {
    if (!selectedId || !disputeForm.commission_id || !disputeForm.reason) return
    run(async () => {
      await marketplaceAdminApi.createDispute({ seller_id: selectedId, ...disputeForm })
      setDisputeForm({ commission_id: '', reason: '' })
    }, 'Disputa aberta.')
  }

  const onResolveDispute = () => {
    if (!selectedDisputeId) return
    run(
      () =>
        marketplaceAdminApi
          .resolveDispute(selectedDisputeId, { status: 'RESOLVED', resolution_notes: 'Resolvido via OPS' })
          .then(() => undefined),
      `Disputa ${selectedDisputeId} resolvida.`,
    )
  }

  const onCreateChannelListing = () => {
    if (!selectedId || !listingChannelId) return
    run(async () => {
      await mkaExtra.createChannelListing({
        seller_id: selectedId,
        channel_partner_id: listingChannelId,
        external_store_id: listingStoreId || undefined,
      })
      setListingStoreId('')
    }, 'Listing de canal criado.')
  }

  const onCreateLockerNetwork = () => {
    if (!selectedId || !networkChannelId) return
    run(
      () =>
        mkaExtra
          .createLockerNetworkLink({
            seller_id: selectedId,
            channel_partner_id: networkChannelId,
            locker_id: networkLockerId || undefined,
          })
          .then(() => undefined),
      'Rede de locker vinculada.',
    )
  }

  const onRecomputeReadiness = () =>
    run(() => marketplaceAdminApi.recomputeIntegrationReadiness().then(() => undefined), 'Prontidão recalculada.')

  const onSimulateInpostDrop = () =>
    run(
      () => marketplaceAdminApi.simulateScoreDrop('INPOST', 30).then(() => undefined),
      'Simulação INPOST: score reduzido para 30 (demo alertas/webhooks).',
    )

  const onUpsertCapabilityWebhook = () => {
    if (!capWebhookPartnerId || !capWebhookUrl) return
    run(
      () =>
        marketplaceAdminApi
          .upsertCapabilityWebhook({
            channel_partner_id: capWebhookPartnerId,
            capability_code: capWebhookCode,
            url: capWebhookUrl,
            events: ['readiness.score_dropped'],
          })
          .then(() => undefined),
      'Webhook de capacidade salvo.',
    )
  }

  const onTestCapabilityWebhook = (webhookId: string) =>
    run(() => marketplaceAdminApi.testCapabilityWebhook(webhookId).then(() => undefined), `Teste enviado (${webhookId}).`)

  const onAckAlert = (alertId: string) =>
    run(() => marketplaceAdminApi.acknowledgeReadinessAlert(alertId).then(() => undefined), `Alerta ${alertId} reconhecido.`)

  const filteredProducts = selectedId ? products.filter((p) => p.seller_id === selectedId) : products
  const filteredCommissions = selectedId ? commissions.filter((c) => c.seller_id === selectedId) : commissions
  const filteredReviews = selectedId ? reviews.filter((r) => r.seller_id === selectedId) : reviews
  const pendingCommissions = commissions.filter((c) => c.status === 'PENDING')

  const showDataTable = tab !== 'overview' && tab !== 'readiness'

  const tableRows = useMemo(() => {
    if (tab === 'sellers')
      return sellers.map((s) => ({
        key: `s-${s.id}`,
        tipo: 'seller',
        id: s.tax_id || s.id,
        detalhe: `${s.trade_name || s.legal_name} · ${s.status} · comissão ${s.commission_pct}% · pedidos ${s.total_orders ?? 0}`,
      }))
    if (tab === 'products')
      return filteredProducts.map((p) => ({
        key: `p-${p.id}`,
        tipo: 'product',
        id: p.product_id,
        detalhe: `${p.locker_id} · ${formatBrl(p.price_cents)} · qtd ${p.quantity} · ${p.status}`,
      }))
    if (tab === 'channels')
      return [
        ...filteredChannelPartners.map((p) => ({
          key: `chp-${p.id}`,
          tipo: p.partner_role ?? 'partner',
          id: p.code,
          detalhe: `${p.name} · ${p.parent_group || '—'} · ${p.integration_mode || '—'} · ${p.country ?? '—'} · caps ${(p.capabilities || []).length} · lockers:${p.supports_lockers ? 'Y' : 'N'}`,
        })),
        ...channelListings.map((l) => ({
          key: `chl-${l.id}`,
          tipo: 'listing',
          id: l.external_store_id || l.id.slice(0, 12),
          detalhe: `seller ${l.seller_id.slice(0, 8)} · ${channelName(l.channel_partner_id)} · ${l.listing_status ?? '—'}`,
        })),
        ...lockerNetworkLinks.map((n) => ({
          key: `lnk-${n.id}`,
          tipo: 'locker_network',
          id: n.locker_id || 'rede',
          detalhe: `${channelName(n.channel_partner_id)} · prio ${n.priority ?? '—'} · seller ${n.seller_id.slice(0, 8)}`,
        })),
      ]
    if (tab === 'categories')
      return [
        ...categories.map((cat) => ({
          key: `cat-${cat.id}`,
          tipo: 'category',
          id: cat.code,
          detalhe: `${cat.name} · ${cat.active ? 'ativa' : 'inativa'}`,
        })),
        ...categoryLinks.map((l) => ({
          key: `link-${l.id}`,
          tipo: 'seller_category',
          id: l.category_id,
          detalhe: `seller ${l.seller_id} · ${l.is_primary ? 'principal' : 'secundária'}`,
        })),
      ]
    if (tab === 'commissions')
      return filteredCommissions.map((c) => ({
        key: `c-${c.id}`,
        tipo: 'commission',
        id: c.order_id,
        detalhe: `${formatBrl(c.commission_amount_cents)} comissão · líquido ${formatBrl(c.net_to_seller_cents)} · ${c.status}`,
      }))
    if (tab === 'settlements')
      return settlementBatches.map((b) => ({
        key: `b-${b.id}`,
        tipo: 'settlement_batch',
        id: b.id.slice(0, 12),
        detalhe: `${b.period_start} a ${b.period_end} · ${formatBrl(b.net_payout_cents)} · ${b.status} · ${b.commission_count} itens`,
      }))
    if (tab === 'payouts')
      return payoutAccounts.map((a) => ({
        key: `pay-${a.id}`,
        tipo: a.account_type ?? 'payout',
        id: a.pix_key || a.account_number || a.id.slice(0, 8),
        detalhe: `${a.holder_name} · ${a.verified ? 'verificada' : 'pendente'} · ${a.is_default ? 'default' : ''}`,
      }))
    if (tab === 'contacts')
      return contacts.map((c) => ({
        key: `ct-${c.id}`,
        tipo: c.contact_type ?? 'contact',
        id: c.name,
        detalhe: `${c.email || '—'} · ${c.phone || '—'} · ${c.is_primary ? 'principal' : ''}`,
      }))
    if (tab === 'kyc')
      return kycDocs.map((d) => ({
        key: `kyc-${d.id}`,
        tipo: d.doc_type,
        id: d.id.slice(0, 12),
        detalhe: `${d.status} · ${d.file_ref || 'sem arquivo'}`,
      }))
    if (tab === 'disputes')
      return disputes.map((d) => ({
        key: `disp-${d.id}`,
        tipo: 'dispute',
        id: d.commission_id.slice(0, 12),
        detalhe: `${d.status} · ${(d.reason || '').slice(0, 60)}`,
      }))
    return filteredReviews.map((rv) => ({
      key: `r-${rv.id}`,
      tipo: 'review',
      id: rv.order_id,
      detalhe: `nota ${rv.rating}/5 · ${(rv.comment || '').slice(0, 80) || 'sem comentário'}`,
    }))
  }, [
    tab,
    sellers,
    filteredProducts,
    filteredChannelPartners,
    channelListings,
    lockerNetworkLinks,
    channelName,
    categories,
    categoryLinks,
    filteredCommissions,
    settlementBatches,
    payoutAccounts,
    contacts,
    kycDocs,
    disputes,
    filteredReviews,
  ])

  const listTitle =
    tab === 'sellers'
      ? `Sellers (${sellers.length})`
      : tab === 'products'
        ? `Produtos (${filteredProducts.length})`
        : tab === 'channels'
          ? `Players (${filteredChannelPartners.length}/${channelPartners.length}) · listings (${channelListings.length})`
          : tab === 'categories'
            ? `Categorias (${categories.length}) e vínculos (${categoryLinks.length})`
            : tab === 'commissions'
              ? `Comissões (${filteredCommissions.length})`
              : tab === 'settlements'
                ? `Lotes de repasse (${settlementBatches.length})`
                : tab === 'payouts'
                  ? `Contas PIX (${payoutAccounts.length})`
                  : tab === 'contacts'
                    ? `Contatos (${contacts.length})`
                    : tab === 'kyc'
                      ? `KYC (${kycDocs.length})`
                      : tab === 'disputes'
                        ? `Disputas (${disputes.length})`
                        : `Avaliações (${filteredReviews.length})`

  return (
    <div className="space-y-4 p-4" data-testid="ops-marketplace-admin-page">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">OPS — Marketplace (admin)</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Sellers, canais (InPost, DHL, Magalu, ML…), prontidão de integração, repasses e KYC
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="ellan-btn-outline"
          >
            {loading ? 'Atualizando…' : 'Listar'}
          </button>
          <button
            type="button"
            onClick={() => void onSeed()}
            disabled={loading}
            className="ellan-btn-outline"
          >
            Seed
          </button>
          <button
            type="button"
            onClick={() => void onSeedChannelPlayers()}
            disabled={loading}
            className="rounded bg-violet-600 px-3 py-2 text-sm text-white"
          >
            Sync catálogo players
          </button>
          <button
            type="button"
            onClick={() => run(() => marketplaceAdminApi.seedSellerProfessional().then(() => undefined), 'Seller professional seed aplicado.')}
            disabled={loading}
            className="rounded bg-sky-600 px-3 py-2 text-sm text-white"
          >
            Seed tiers & compliance
          </button>
        </div>
      </header>

      {message && (
        <p className="rounded bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
          {message}
        </p>
      )}
      {error && (
        <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-800 dark:bg-red-950 dark:text-red-200">{error}</p>
      )}
      {lastApiKey && (
        <p className="rounded bg-amber-50 px-3 py-2 font-mono text-xs text-amber-900 dark:bg-amber-950">
          API key: {lastApiKey}
        </p>
      )}

      <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
        <h2 className="mb-2 text-sm font-medium">Seller em foco</h2>
        <select className={inp} value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
          <option value="">— selecione —</option>
          {sellers.map((s) => (
            <option key={s.id} value={s.id}>
              {s.trade_name || s.legal_name} — {s.status}
            </option>
          ))}
        </select>
        {selectedSeller ? (
          <p className="mt-2 text-xs text-gray-500 dark:text-slate-400">
            {selectedSeller.legal_name} · CNPJ {selectedSeller.tax_id} · rating {selectedSeller.seller_rating ?? '—'}
          </p>
        ) : null}
      </section>

      <div className="flex flex-wrap gap-1 border-b dark:border-slate-700">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTabAndUrl(t.key)}
            className={`rounded-t px-3 py-2 text-sm ${
              tab === t.key
                ? 'border-b-2 border-indigo-600 font-medium text-indigo-700 dark:text-indigo-300'
                : 'text-gray-600 dark:text-slate-400'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'sellers' && (
        <form
          onSubmit={onCreateSeller}
          className="grid gap-3 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-3 lg:grid-cols-5"
        >
          <input className={inp} placeholder="Razão social" required value={sellerForm.legal_name} onChange={(e) => setSellerForm((f) => ({ ...f, legal_name: e.target.value }))} />
          <input className={inp} placeholder="Nome fantasia" value={sellerForm.trade_name} onChange={(e) => setSellerForm((f) => ({ ...f, trade_name: e.target.value }))} />
          <input className={inp} placeholder="CNPJ" required value={sellerForm.tax_id} onChange={(e) => setSellerForm((f) => ({ ...f, tax_id: e.target.value }))} />
          <input className={inp} placeholder="E-mail" required value={sellerForm.email} onChange={(e) => setSellerForm((f) => ({ ...f, email: e.target.value }))} />
          <input className={inp} placeholder="commission_pct" value={sellerForm.commission_pct} onChange={(e) => setSellerForm((f) => ({ ...f, commission_pct: e.target.value }))} />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-3 lg:col-span-5">
            Criar seller
          </button>
          <button
            type="button"
            className="rounded border px-4 py-2 text-sm dark:border-slate-600 md:col-span-3 lg:col-span-5"
            onClick={() => void onApproveSeller()}
            disabled={!selectedId || selectedSeller?.status !== 'PENDING_APPROVAL'}
          >
            Aprovar seller selecionado
          </button>
        </form>
      )}

      {tab === 'products' && (
        <form
          onSubmit={onCreateProduct}
          className="grid gap-3 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-4"
        >
          <input className={inp} placeholder="LOCKER-DEMO-01" required value={productForm.locker_id} onChange={(e) => setProductForm((f) => ({ ...f, locker_id: e.target.value }))} />
          <input className={inp} placeholder="product_id" required value={productForm.product_id} onChange={(e) => setProductForm((f) => ({ ...f, product_id: e.target.value }))} />
          <input className={inp} placeholder="price_cents" required value={productForm.price_cents} onChange={(e) => setProductForm((f) => ({ ...f, price_cents: e.target.value }))} />
          <input className={inp} placeholder="quantity" value={productForm.quantity} onChange={(e) => setProductForm((f) => ({ ...f, quantity: e.target.value }))} />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-4" disabled={!selectedId}>
            Criar produto no locker
          </button>
        </form>
      )}

      {tab === 'categories' && (
        <div className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <input className={inp} placeholder="code" value={categoryForm.code} onChange={(e) => setCategoryForm((f) => ({ ...f, code: e.target.value }))} />
          <input className={inp} placeholder="name" value={categoryForm.name} onChange={(e) => setCategoryForm((f) => ({ ...f, name: e.target.value }))} />
          <select className={inp} value={categoryLinkCategoryId} onChange={(e) => setCategoryLinkCategoryId(e.target.value)}>
            <option value="">category_id (vínculo)</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.code}
              </option>
            ))}
          </select>
          <button type="button" className="rounded bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => void onCreateCategory()} disabled={!categoryForm.code || !categoryForm.name}>
            Criar categoria
          </button>
          <button type="button" className="ellan-btn-outline" onClick={() => void onLinkCategory()} disabled={!selectedId || !categoryLinkCategoryId}>
            Vincular ao seller
          </button>
        </div>
      )}

      {tab === 'channels' && (
        <div className="space-y-3">
          <section className="rounded-xl border border-indigo-500/40 bg-indigo-950/30 p-4">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-medium">Players mundiais (locker + marketplace)</h2>
              {sellerCoverage ? (
                <span className="text-sm text-indigo-200">
                  Cobertura seller: {sellerCoverage.coverage_complete_count}/{sellerCoverage.players?.length ?? 0} (
                  {sellerCoverage.coverage_pct}%)
                </span>
              ) : null}
              <button
                type="button"
                className="ellan-btn-outline text-xs"
                disabled={!selectedId}
                onClick={() =>
                  void run(
                    () => marketplaceAdminApi.seedPriorityPlayerLinks(selectedId).then(() => undefined),
                    'Vínculos prioritários aplicados.',
                  )
                }
              >
                Seed vínculos InPost · DHL · ML…
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-xs">
                <thead>
                  <tr className="text-gray-500">
                    <th className="px-2 py-1">Player</th>
                    <th className="px-2 py-1">Papel</th>
                    <th className="px-2 py-1">Prontidão</th>
                    <th className="px-2 py-1">Listing</th>
                    <th className="px-2 py-1">Rede locker</th>
                    <th className="px-2 py-1">OK</th>
                  </tr>
                </thead>
                <tbody>
                  {(sellerCoverage?.players ?? worldPriorityPlayers.map((w) => ({ partner_code: w.code, has_marketplace_listing: false, has_locker_network: false, coverage_complete: false }))).map((row) => {
                    const meta = worldPriorityPlayers.find((w) => w.code === row.partner_code)
                    return (
                      <tr key={row.partner_code} className="border-t border-slate-700">
                        <td className="px-2 py-1 font-mono">{row.partner_code}</td>
                        <td className="px-2 py-1">{meta?.role ?? '—'}</td>
                        <td className="px-2 py-1">
                          {meta?.readiness_band ?? '—'} {meta?.score_total != null ? `(${meta.score_total})` : ''}
                        </td>
                        <td className="px-2 py-1">{row.has_marketplace_listing ? '✓' : '—'}</td>
                        <td className="px-2 py-1">{row.has_locker_network ? '✓' : '—'}</td>
                        <td className="px-2 py-1">{row.coverage_complete ? '✓' : '○'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>
        <div className="space-y-3 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex flex-wrap gap-2">
            <select className={inp} value={channelParentGroup} onChange={(e) => setChannelParentGroup(e.target.value)}>
              <option value="">parent_group — todos</option>
              {channelParentGroups.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
            <select className={inp} value={listingChannelId} onChange={(e) => setListingChannelId(e.target.value)}>
              <option value="">canal (listing)</option>
              {channelPartners.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code}
                </option>
              ))}
            </select>
            <input className={inp} placeholder="external_store_id" value={listingStoreId} onChange={(e) => setListingStoreId(e.target.value)} />
            <select className={inp} value={networkChannelId} onChange={(e) => setNetworkChannelId(e.target.value)}>
              <option value="">canal (rede locker)</option>
              {channelPartners.filter((p) => p.supports_lockers).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code}
                </option>
              ))}
            </select>
            <input className={inp} placeholder="locker_id (opcional)" value={networkLockerId} onChange={(e) => setNetworkLockerId(e.target.value)} />
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="rounded bg-indigo-600 px-3 py-2 text-sm text-white" onClick={() => void onCreateChannelListing()} disabled={!selectedId || !listingChannelId}>
              Vincular canal (listing)
            </button>
            <button type="button" className="ellan-btn-outline" onClick={() => void onCreateLockerNetwork()} disabled={!selectedId || !networkChannelId}>
              Vincular rede locker
            </button>
          </div>
        </div>
        </div>
      )}

      {tab === 'contacts' && (
        <div className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <input className={inp} placeholder="name" value={contactForm.name} onChange={(e) => setContactForm((f) => ({ ...f, name: e.target.value }))} />
          <input className={inp} placeholder="email" value={contactForm.email} onChange={(e) => setContactForm((f) => ({ ...f, email: e.target.value }))} />
          <select className={inp} value={contactForm.contact_type} onChange={(e) => setContactForm((f) => ({ ...f, contact_type: e.target.value }))}>
            <option value="PRIMARY">PRIMARY</option>
            <option value="SUPPORT">SUPPORT</option>
            <option value="FINANCE">FINANCE</option>
          </select>
          <button type="button" className="rounded bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => void onCreateContact()} disabled={!selectedId || !contactForm.name}>
            Criar contato
          </button>
        </div>
      )}

      {tab === 'payouts' && (
        <div className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <input className={inp} placeholder="holder_name" value={payoutForm.holder_name} onChange={(e) => setPayoutForm((f) => ({ ...f, holder_name: e.target.value }))} />
          <input className={inp} placeholder="pix_key" value={payoutForm.pix_key} onChange={(e) => setPayoutForm((f) => ({ ...f, pix_key: e.target.value }))} />
          <button type="button" className="rounded bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => void onCreatePayout()} disabled={!selectedId || !payoutForm.holder_name}>
            Criar conta PIX
          </button>
        </div>
      )}

      {tab === 'settlements' && (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <select className={inp} value={selectedBatchId} onChange={(e) => setSelectedBatchId(e.target.value)}>
              <option value="">batch_id</option>
              {settlementBatches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.id.slice(0, 12)} · {b.status} · {formatBrl(b.net_payout_cents)}
                </option>
              ))}
            </select>
            <button type="button" className="rounded bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => void onCreateSettlement()} disabled={!selectedId}>
              Gerar lote de repasse
            </button>
            <button type="button" className="ellan-btn-outline" onClick={() => void onMarkBatchPaid()} disabled={!selectedBatchId}>
              Marcar lote PAID
            </button>
          </div>
          {selectedBatchId && settlementItems.length > 0 ? (
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2">Pedido</th>
                  <th className="px-3 py-2">Líquido seller</th>
                </tr>
              </thead>
              <tbody>
                {settlementItems.map((it) => (
                  <tr key={it.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 font-mono text-xs">{it.order_id}</td>
                    <td className="px-3 py-2">{formatBrl(it.net_to_seller_cents)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </div>
      )}

      {tab === 'kyc' && (
        <div className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <select className={inp} value={kycForm.doc_type} onChange={(e) => setKycForm((f) => ({ ...f, doc_type: e.target.value }))}>
            <option value="CNPJ_CARD">CNPJ_CARD</option>
            <option value="ID">ID</option>
            <option value="ADDRESS">ADDRESS</option>
            <option value="BANK_PROOF">BANK_PROOF</option>
          </select>
          <input className={inp} placeholder="file_ref" value={kycForm.file_ref} onChange={(e) => setKycForm((f) => ({ ...f, file_ref: e.target.value }))} />
          <select className={inp} value={selectedKycId} onChange={(e) => setSelectedKycId(e.target.value)}>
            <option value="">kyc_id (aprovar)</option>
            {kycDocs.filter((d) => d.status === 'PENDING').map((d) => (
              <option key={d.id} value={d.id}>
                {d.doc_type} · {d.seller_id.slice(0, 8)}
              </option>
            ))}
          </select>
          <button type="button" className="rounded bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => void onCreateKyc()} disabled={!selectedId}>
            Registrar documento
          </button>
          <button type="button" className="ellan-btn-outline" onClick={() => void onApproveKyc()} disabled={!selectedKycId}>
            Aprovar KYC
          </button>
        </div>
      )}

      {tab === 'disputes' && (
        <div className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <input className={inp} placeholder="commission_id" value={disputeForm.commission_id} onChange={(e) => setDisputeForm((f) => ({ ...f, commission_id: e.target.value }))} />
          <input className={inp} placeholder="reason" value={disputeForm.reason} onChange={(e) => setDisputeForm((f) => ({ ...f, reason: e.target.value }))} />
          <select className={inp} value={selectedDisputeId} onChange={(e) => setSelectedDisputeId(e.target.value)}>
            <option value="">dispute_id (resolver)</option>
            {disputes.filter((d) => d.status === 'OPEN').map((d) => (
              <option key={d.id} value={d.id}>
                {d.commission_id.slice(0, 12)}
              </option>
            ))}
          </select>
          <button type="button" className="rounded bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => void onCreateDispute()} disabled={!selectedId || !disputeForm.commission_id || !disputeForm.reason}>
            Abrir disputa
          </button>
          <button type="button" className="ellan-btn-outline" onClick={() => void onResolveDispute()} disabled={!selectedDisputeId}>
            Resolver disputa
          </button>
        </div>
      )}

      {tab === 'commissions' && (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <input className={inp} placeholder="price_cents" value={previewPriceCents} onChange={(e) => setPreviewPriceCents(e.target.value)} />
            <button
              type="button"
              className="ellan-btn-outline"
              onClick={() => {
                const pct = selectedSeller?.commission_pct ?? '5'
                void marketplaceAdminApi
                  .commissionNetPreview(Number(previewPriceCents) || 0, pct)
                  .then((r) => setCommissionPreview(r.data as Record<string, number>))
                  .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Preview falhou'))
              }}
            >
              fn_calculate_seller_net
            </button>
            {commissionPreview ? (
              <p className="w-full text-sm text-gray-400">
                comissão {formatBrl(commissionPreview.commission_cents)} · Ellan {formatBrl(commissionPreview.ellan_fee_cents)} ·
                gateway {formatBrl(commissionPreview.gateway_fee_cents)} · líquido {formatBrl(commissionPreview.net_cents)}
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <select className={inp} value={selectedCommissionId} onChange={(e) => setSelectedCommissionId(e.target.value)}>
              <option value="">commission_id (PENDING)</option>
              {pendingCommissions.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.order_id} · {formatBrl(c.commission_amount_cents)}
                </option>
              ))}
            </select>
            <button type="button" className="ellan-btn-outline" onClick={() => void onSettleCommission()} disabled={!selectedCommissionId}>
              Liquidar comissão
            </button>
          </div>
        </div>
      )}

      {tab === 'readiness' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button type="button" className="rounded bg-indigo-600 px-3 py-2 text-sm text-white" onClick={() => void onRecomputeReadiness()} disabled={loading}>
              Recalcular prontidão
            </button>
            <button type="button" className="ellan-btn-outline" onClick={() => void onSimulateInpostDrop()} disabled={loading}>
              Simular queda INPOST (demo)
            </button>
            <button
              type="button"
              className="rounded border border-emerald-600 px-3 py-2 text-sm text-emerald-800 dark:text-emerald-300"
              onClick={() =>
                void run(async () => {
                  await marketplaceAdminApi.seedChannelPlayers()
                  const seed = await marketplaceAdminApi.seedGlobalOps()
                  await marketplaceAdminApi.mirrorCertificationsFromPartner()
                  const [sum, corridors, sla] = await Promise.all([
                    marketplaceAdminApi.globalOpsSummary(),
                    marketplaceAdminApi.listGlobalCorridors(),
                    marketplaceAdminApi.listCorridorSla(),
                  ])
                  setMktGlobalOpsSummary(sum.data as Record<string, unknown>)
                  setMktGlobalCorridors(corridors.data as typeof mktGlobalCorridors)
                  return `Global OPS: ${seed.data.corridors} corredores, SLA ${sla.data.length}`
                }, 'Corredores e certificações globais atualizados.')
              }
              disabled={loading}
            >
              Seed Global OPS
            </button>
            <button
              type="button"
              className="ellan-btn-outline"
              onClick={() =>
                void run(
                  () => marketplaceAdminApi.replayDeadLetterBatch(25).then((r) => undefined),
                  'Replay dead-letter marketplace.',
                )
              }
              disabled={loading}
            >
              Replay DLQ
            </button>
          </div>

          {mktGlobalOpsSummary ? (
            <div className="rounded-xl border border-emerald-600/30 bg-emerald-50/40 p-3 text-sm dark:bg-emerald-950/20">
              Certificações válidas: {String(mktGlobalOpsSummary.certifications_valid)} · Corredores:{' '}
              {String(mktGlobalOpsSummary.corridors_active)} · Steps: {String(mktGlobalOpsSummary.corridor_steps)}
            </div>
          ) : null}
          {mktGlobalCorridors.length > 0 ? (
            <ul className="text-xs text-gray-600 dark:text-slate-400">
              {mktGlobalCorridors.map((c) => (
                <li key={c.corridor_code}>
                  {c.name}: {c.steps.map((s) => s.partner_code).join(' → ')}
                </li>
              ))}
            </ul>
          ) : null}

          {integrationHub && (
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6">
              {[
                ['Linhas prontidão', integrationHub.readiness_rows],
                ['Score médio', integrationHub.avg_score?.toFixed?.(1) ?? integrationHub.avg_score],
                ['Incidentes abertos', integrationHub.open_incidents],
                ['Alertas abertos', integrationHub.open_readiness_alerts],
                ['Com blockers', integrationHub.partners_with_blockers],
                ...Object.entries(integrationHub.bands || {}).map(([k, v]) => [`Faixa ${k}`, v]),
              ].map(([label, val]) => (
                <div key={String(label)} className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-3 dark:border-slate-700 dark:bg-slate-900">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className="text-lg font-semibold">{String(val)}</p>
                </div>
              ))}
            </div>
          )}

          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <h3 className="mb-2 text-sm font-medium">Prontidão por player ({readinessRows.length})</h3>
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2">Código</th>
                  <th className="px-3 py-2">Faixa</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">Blockers</th>
                </tr>
              </thead>
              <tbody>
                {readinessRows.map((row) => (
                  <tr key={row.channel_partner_id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 font-mono text-xs">{row.partner_code}</td>
                    <td className="px-3 py-2">{row.readiness_band}</td>
                    <td className="px-3 py-2">
                      {row.score_total} (cap {row.score_capabilities} · api {row.score_api} · ops {row.score_operations})
                    </td>
                    <td className="px-3 py-2 text-xs">{(row.blockers || []).join('; ') || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <h3 className="mb-2 text-sm font-medium">Alertas ({readinessAlerts.length})</h3>
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2">Player</th>
                  <th className="px-3 py-2">Tipo</th>
                  <th className="px-3 py-2">Δ score</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {readinessAlerts.map((a) => {
                  const id = String(a.id ?? '')
                  return (
                    <tr key={id} className="border-t dark:border-slate-800">
                      <td className="px-3 py-2 font-mono text-xs">{String(a.partner_code ?? '')}</td>
                      <td className="px-3 py-2">{String(a.alert_type ?? '')}</td>
                      <td className="px-3 py-2">
                        {String(a.previous_band ?? '—')} → {String(a.new_band ?? '')} ({String(a.score_delta ?? '')})
                      </td>
                      <td className="px-3 py-2">{String(a.status ?? '')}</td>
                      <td className="px-3 py-2">
                        {String(a.status) === 'OPEN' && (
                          <button type="button" className="text-indigo-600 hover:underline" onClick={() => void onAckAlert(id)}>
                            ACK
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </section>

          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <h3 className="mb-2 text-sm font-medium">Webhooks de capacidade</h3>
            <div className="mb-3 flex flex-wrap gap-2">
              <select className={inp} value={capWebhookPartnerId} onChange={(e) => setCapWebhookPartnerId(e.target.value)}>
                <option value="">channel_partner_id</option>
                {channelPartners.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code}
                  </option>
                ))}
              </select>
              <input className={inp} placeholder="capability_code" value={capWebhookCode} onChange={(e) => setCapWebhookCode(e.target.value)} />
              <input className={inp} placeholder="url" value={capWebhookUrl} onChange={(e) => setCapWebhookUrl(e.target.value)} />
              <button type="button" className="rounded bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => void onUpsertCapabilityWebhook()} disabled={!capWebhookPartnerId || !capWebhookUrl}>
                Salvar webhook
              </button>
            </div>
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2">Player</th>
                  <th className="px-3 py-2">Capacidade</th>
                  <th className="px-3 py-2">URL</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {capabilityWebhooks.map((w) => {
                  const id = String(w.id ?? '')
                  return (
                    <tr key={id} className="border-t dark:border-slate-800">
                      <td className="px-3 py-2 font-mono text-xs">{String(w.partner_code ?? '')}</td>
                      <td className="px-3 py-2">{String(w.capability_code ?? '')}</td>
                      <td className="px-3 py-2 text-xs">{String(w.url ?? '').slice(0, 48)}</td>
                      <td className="px-3 py-2">
                        <button type="button" className="text-indigo-600 hover:underline" onClick={() => void onTestCapabilityWebhook(id)}>
                          Testar
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </section>

          {integrationIncidents.length > 0 && (
            <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
              <h3 className="mb-2 text-sm font-medium">Incidentes ({integrationIncidents.length})</h3>
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                  <tr>
                    <th className="px-3 py-2">Severidade</th>
                    <th className="px-3 py-2">Player</th>
                    <th className="px-3 py-2">Detalhe</th>
                  </tr>
                </thead>
                <tbody>
                  {integrationIncidents.map((i) => (
                    <tr key={i.id} className="border-t dark:border-slate-800">
                      <td className="px-3 py-2">{i.severity}</td>
                      <td className="px-3 py-2 font-mono text-xs">{i.partner_code}</td>
                      <td className="px-3 py-2">
                        {i.incident_type} · {i.title} · {i.status}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </div>
      )}

      {tab === 'overview' && dashboard && (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5">
            {[
              ['Sellers ativos', dashboard.sellers_active],
              ['Pendentes aprovação', dashboard.sellers_pending_approval],
              ['Produtos ativos', dashboard.products_active],
              ['Comissões pendentes', dashboard.commissions_pending],
              ['Valor pendente', formatBrl(dashboard.commissions_pending_cents as number)],
              ['Comissões liquidadas', dashboard.commissions_settled],
              ['Disputas abertas', dashboard.open_disputes],
              ['Lotes repasse (draft)', dashboard.settlement_batches_draft],
              ['KYC pendente', dashboard.kyc_pending],
              ['Rating médio', dashboard.avg_seller_rating ?? '—'],
              ['Players ativos', dashboard.channel_partners_active],
              ['GO_LIVE (prontidão)', dashboard.integration_go_live],
              ['Score médio integração', dashboard.integration_avg_score],
              ['Incidentes abertos', dashboard.integration_open_incidents],
              ['Listings canal', dashboard.seller_channel_listings],
              ['Redes locker', dashboard.locker_network_links],
              ...(profSummary
                ? [
                    ['Tier ativo', profSummary.tier_enrollments_active],
                    ['Compliance verificado', profSummary.compliance_profiles_verified],
                    ['Contratos assinados', profSummary.agreements_signed],
                    ['Risco', profSummary.latest_risk_band ?? '—'],
                  ]
                : []),
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-2xl font-semibold">{value}</p>
              </div>
            ))}
          </div>
          {integrationHub && (
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6">
              <p className="col-span-full text-sm font-medium text-gray-600 dark:text-slate-300">Integration hub</p>
              {[
                ['Linhas prontidão', integrationHub.readiness_rows],
                ['Score médio hub', integrationHub.avg_score],
                ['Alertas abertos', integrationHub.open_readiness_alerts],
                ['GO_LIVE top', integrationHub.top_go_live?.[0]?.partner_code ?? '—'],
              ].map(([label, val]) => (
                <div key={String(label)} className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-3 dark:border-slate-700 dark:bg-slate-900">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className="text-lg font-semibold">{String(val)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'integrations' && (
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-2 text-lg font-medium">Webhook do seller</h2>
            {sellerWebhookConfig?.url ? (
              <p className="mb-2 text-xs text-gray-500">
                Ativo: {String(sellerWebhookConfig.active)} · eventos: {sellerWebhookConfig.events_json}
              </p>
            ) : (
              <p className="mb-2 text-xs text-gray-500">Nenhum webhook configurado.</p>
            )}
            <div className="flex flex-wrap gap-2">
              <input className={`min-w-[14rem] flex-1 ${inp}`} placeholder="Webhook URL" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
              <input className={inp} placeholder="Secret" value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} />
              <button type="button" onClick={() => void onWebhook()} className="ellan-btn-outline" disabled={!selectedId || !webhookUrl}>
                Salvar webhook
              </button>
            </div>
          </section>
          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-2 text-lg font-medium">API keys</h2>
            <button type="button" onClick={() => void onRotateKey()} className="mb-3 rounded bg-amber-600 px-3 py-2 text-sm text-white" disabled={!selectedId}>
              Rotacionar API key
            </button>
            <ul className="space-y-1 text-sm">
              {sellerApiKeys.length === 0 ? (
                <li className="text-gray-500">Nenhuma chave registrada.</li>
              ) : (
                sellerApiKeys.map((k) => (
                  <li key={k.id} className="font-mono text-xs">
                    {k.key_prefix}… {k.revoked_at ? '(revogada)' : '(ativa)'}
                  </li>
                ))
              )}
            </ul>
          </section>
        </div>
      )}

      {tab === 'tiers' && (
        <div className="space-y-4">
          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-2 text-lg font-medium">Catálogo de tiers (STARTER · GROWTH · ENTERPRISE)</h2>
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2">Código</th>
                  <th className="px-3 py-2">Nome</th>
                  <th className="px-3 py-2">GMV mín.</th>
                </tr>
              </thead>
              <tbody>
                {tierDefs.map((t) => (
                  <tr key={t.code} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 font-mono text-xs">{t.code}</td>
                    <td className="px-3 py-2">{t.name}</td>
                    <td className="px-3 py-2">{formatBrl(t.min_gmv_cents)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-2 text-sm font-medium">Matrícula do seller</h2>
            <div className="flex flex-wrap gap-2">
              <select className={inp} value={tierEnrollCode} onChange={(e) => setTierEnrollCode(e.target.value)}>
                {tierDefs.map((t) => (
                  <option key={t.code} value={t.code}>
                    {t.code}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="ellan-btn-outline"
                disabled={!selectedId}
                onClick={() =>
                  void run(async () => {
                    const today = new Date().toISOString().slice(0, 10)
                    await marketplaceAdminApi.createTierEnrollment({
                      seller_id: selectedId,
                      tier_code: tierEnrollCode,
                      effective_from: today,
                    })
                  }, 'Tier vinculado.')
                }
              >
                Vincular tier
              </button>
            </div>
            <ul className="mt-3 space-y-1 text-sm">
              {tierEnrollments.map((e) => (
                <li key={e.id}>
                  {e.tier_code} · {e.status} · desde {e.effective_from}
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}

      {tab === 'compliance' && (
        <div className="space-y-4">
          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-2 text-lg font-medium">Perfis fiscais multi-país (BR · EU · IOSS)</h2>
            <div className="mb-3 flex flex-wrap gap-2">
              <input className={inp} placeholder="PAís (PT, ES, BR)" value={complianceForm.country} onChange={(e) => setComplianceForm((f) => ({ ...f, country: e.target.value.toUpperCase() }))} />
              <input className={inp} placeholder="tax_regime" value={complianceForm.tax_regime} onChange={(e) => setComplianceForm((f) => ({ ...f, tax_regime: e.target.value }))} />
              <input className={inp} placeholder="VAT" value={complianceForm.vat_number} onChange={(e) => setComplianceForm((f) => ({ ...f, vat_number: e.target.value }))} />
              <input className={inp} placeholder="IOSS" value={complianceForm.ioss_number} onChange={(e) => setComplianceForm((f) => ({ ...f, ioss_number: e.target.value }))} />
              <button
                type="button"
                className="rounded bg-emerald-600 px-3 py-2 text-sm text-white"
                disabled={!selectedId}
                onClick={() =>
                  void run(
                    () =>
                      marketplaceAdminApi
                        .createComplianceProfile({ seller_id: selectedId, ...complianceForm, cross_border_enabled: complianceForm.country !== 'BR' })
                        .then(() => undefined),
                    'Perfil fiscal criado.',
                  )
                }
              >
                Adicionar país
              </button>
            </div>
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2">País</th>
                  <th className="px-3 py-2">Regime</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">IOSS/VAT</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {complianceProfiles.map((p) => (
                  <tr key={p.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2">{p.country}</td>
                    <td className="px-3 py-2">{p.tax_regime}</td>
                    <td className="px-3 py-2">{p.fiscal_status}</td>
                    <td className="px-3 py-2 text-xs">{p.ioss_number || '—'}</td>
                    <td className="px-3 py-2">
                      {p.fiscal_status !== 'VERIFIED' && (
                        <button
                          type="button"
                          className="text-indigo-600 hover:underline"
                          onClick={() =>
                            void run(
                              () => marketplaceAdminApi.updateComplianceProfile(p.id, { fiscal_status: 'VERIFIED' }).then(() => undefined),
                              'Perfil verificado.',
                            )
                          }
                        >
                          Verificar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>
      )}

      {tab === 'performance' && (
        <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-2 text-lg font-medium">KPIs mensais (GMV · OTD · defeitos)</h2>
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">Mês</th>
                <th className="px-3 py-2">GMV</th>
                <th className="px-3 py-2">Pedidos</th>
                <th className="px-3 py-2">OTD %</th>
              </tr>
            </thead>
            <tbody>
              {performanceRows.map((r) => (
                <tr key={r.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2">{r.month}</td>
                  <td className="px-3 py-2">{formatBrl(r.gmv_cents)}</td>
                  <td className="px-3 py-2">{r.order_count}</td>
                  <td className="px-3 py-2">{r.on_time_pickup_pct ?? '—'}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'agreements' && (
        <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-2 text-lg font-medium">Contratos & DPA (marketplace / dados)</h2>
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">Tipo</th>
                <th className="px-3 py-2">Versão</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {agreements.map((a) => (
                <tr key={a.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2">{a.agreement_type}</td>
                  <td className="px-3 py-2">{a.version}</td>
                  <td className="px-3 py-2">{a.status}</td>
                  <td className="px-3 py-2">
                    {a.status !== 'SIGNED' && (
                      <button
                        type="button"
                        className="text-indigo-600 hover:underline"
                        onClick={() =>
                          void run(
                            () => marketplaceAdminApi.updateAgreement(a.id, { status: 'SIGNED' }).then(() => undefined),
                            'Contrato assinado.',
                          )
                        }
                      >
                        Assinar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'operations' && (
        <div className="space-y-4">
          <section className="rounded-xl border border-violet-500/40 bg-violet-950/20 p-4">
            <div className="mb-2 flex flex-wrap gap-2">
              <button
                type="button"
                className="ellan-btn-outline text-xs"
                onClick={() =>
                  void run(
                    () => marketplaceAdminApi.seedSellerOperations(selectedId || 'mk-seller-demo-001').then(() => undefined),
                    'Operações seller seed.',
                  )
                }
              >
                Seed operações
              </button>
              <button
                type="button"
                className="ellan-btn-outline text-xs"
                disabled={!selectedId}
                onClick={() =>
                  void run(async () => {
                    const r = await marketplaceAdminApi.getPricingPreview(selectedId, {
                      internal_sku: 'DEMO-001',
                      base_price_cents: Number(previewPriceCents) || 4990,
                      channel_partner_id: 'mcp-meli',
                    })
                    setPricingPreview(r.data)
                  }, 'Preview preço calculado.')
                }
              >
                Preview preço ML
              </button>
            </div>
            {opsSummary ? (
              <p className="text-sm">
                Onboarding {String(opsSummary.onboarding_progress_pct)}% · SKU maps {String(opsSummary.sku_maps)} ·
                Alocações {String(opsSummary.inventory_allocations)}
              </p>
            ) : null}
            <p className="text-sm text-violet-200">Progresso onboarding: {onboardingProgress}%</p>
            {pricingPreview ? (
              <p className="text-xs text-gray-400">
                Preview: {String(pricingPreview.base_price_cents)} → {String(pricingPreview.final_price_cents)} (
                {(pricingPreview.rules_applied as string[])?.join(', ')})
              </p>
            ) : null}
          </section>
          <section className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm font-medium">Onboarding</h3>
              <ul className="space-y-1 text-xs">
                {onboardingTasks.map((t) => (
                  <li key={t.id} className="flex justify-between gap-2">
                    <span>{t.title}</span>
                    <span className={t.status === 'COMPLETED' ? 'text-emerald-400' : 'text-amber-400'}>{t.status}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm font-medium">SKU por canal</h3>
              {skuMaps.map((m) => (
                <div key={`${m.partner_code}-${m.internal_sku}`} className="text-xs font-mono">
                  {m.partner_code}: {m.internal_sku} → {m.channel_sku}
                </div>
              ))}
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm font-medium">Regras de preço</h3>
              {pricingRules.map((r) => (
                <div key={r.name} className="text-xs">
                  {r.rule_type} — {r.name} {r.partner_code ? `(${r.partner_code})` : ''}
                </div>
              ))}
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm font-medium">Devoluções · notificações · stock</h3>
              {returnPolicies.map((p) => (
                <div key={p.policy_code} className="text-xs">
                  {p.policy_code} — {p.return_window_days}d
                </div>
              ))}
              {notifSubs.map((n) => (
                <div key={n.event_type} className="text-xs">
                  {n.event_type} via {n.channel}
                </div>
              ))}
              {invAllocations.map((a) => (
                <div key={a.partner_code} className="text-xs">
                  {a.partner_code}: disp {a.available_qty} / {a.allocated_qty}
                </div>
              ))}
              {fulfillmentPrefs ? (
                <p className="mt-2 text-xs">Fulfillment: {String(fulfillmentPrefs.handoff_mode)}</p>
              ) : null}
            </div>
          </section>
        </div>
      )}

      {tab === 'intelligence' && (
        <div className="space-y-4">
          <section className="rounded-xl border border-cyan-500/40 bg-cyan-950/20 p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-medium">Ops intelligence</h2>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="ellan-btn-outline text-xs"
                  onClick={() => void run(() => marketplaceAdminApi.seedOpsIntelligence().then(() => undefined), 'Ops intelligence seed.')}
                >
                  Seed intelligence
                </button>
                <button
                  type="button"
                  className="ellan-btn-outline text-xs"
                  disabled={!selectedId}
                  onClick={() =>
                    void run(
                      () => marketplaceAdminApi.computeSellerHealth(selectedId).then(() => load()),
                      'Health score atualizado.',
                    )
                  }
                >
                  Recalcular health
                </button>
              </div>
            </div>
            {opsIntelSummary ? (
              <div className="mb-3 grid grid-cols-2 gap-2 text-sm md:grid-cols-3">
                <div>Playbooks: {opsIntelSummary.playbooks_total}</div>
                <div>API degradada: {opsIntelSummary.api_health_degraded}</div>
                <div>Promo ativas: {opsIntelSummary.active_promotions}</div>
                <div>Sync running: {opsIntelSummary.sync_jobs_running}</div>
                <div>Cross-border: {opsIntelSummary.cross_border_profiles}</div>
              </div>
            ) : null}
            {sellerHealth ? (
              <p className="text-sm text-cyan-200">
                Health {sellerHealth.health_score} ({sellerHealth.health_band}) — {sellerHealth.factors.join(', ') || 'sem alertas'}
              </p>
            ) : (
              <p className="text-sm text-gray-500">Selecione seller e recalcule health.</p>
            )}
          </section>
          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4">
            <h3 className="mb-2 font-medium">Quotas por canal</h3>
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-gray-500">
                  <th className="px-2 py-1">Canal</th>
                  <th className="px-2 py-1">Status</th>
                  <th className="px-2 py-1">SKU %</th>
                  <th className="px-2 py-1">Pedidos %</th>
                </tr>
              </thead>
              <tbody>
                {channelQuotas.map((q) => (
                  <tr key={q.partner_code} className="border-t border-slate-700">
                    <td className="px-2 py-1 font-mono">{q.partner_code}</td>
                    <td className="px-2 py-1">{q.quota_status}</td>
                    <td className="px-2 py-1">{q.utilization_skus_pct}%</td>
                    <td className="px-2 py-1">{q.utilization_orders_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4">
            <h3 className="mb-2 font-medium">Playbooks ops</h3>
            <ul className="space-y-2 text-xs">
              {opsPlaybooks.map((p) => (
                <li key={p.code} className="rounded border border-slate-700 p-2">
                  <span className="font-mono text-amber-300">{p.code}</span> — {p.name} ({p.severity})
                </li>
              ))}
            </ul>
          </section>
          <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4">
            <h3 className="mb-2 font-medium">Cross-border · sync · promo · API health</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="text-xs text-gray-500">Cross-border</h4>
                {crossBorderProfiles.map((x) => (
                  <div key={x.corridor_code} className="text-xs">
                    {x.corridor_code} — {x.customs_scheme} ({x.status})
                  </div>
                ))}
              </div>
              <div>
                <h4 className="text-xs text-gray-500">Sync jobs</h4>
                {catalogSyncJobs.map((j) => (
                  <div key={j.id} className="text-xs">
                    {j.partner_code} {j.job_type} {j.status} ok={j.items_ok} fail={j.items_failed}
                  </div>
                ))}
              </div>
              <div>
                <h4 className="text-xs text-gray-500">Promoções</h4>
                {sellerPromotions.map((p) => (
                  <div key={p.campaign_code} className="text-xs">
                    {p.campaign_code} — {p.name} ({p.status})
                  </div>
                ))}
              </div>
              <div>
                <h4 className="text-xs text-gray-500">API degradada</h4>
                {partnerApiHealth.map((h) => (
                  <div key={h.partner_code} className="text-xs">
                    {h.partner_code} {h.health_status} avail={h.availability_pct}% p95={h.p95_latency_ms}ms
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      )}

      {tab === 'risk' && (
        <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-2 text-lg font-medium">Avaliação de risco (fraude · chargeback · KYC)</h2>
          <div className="mb-3 flex flex-wrap gap-2">
            <input className={inp} placeholder="risk_score 0-100" value={riskScore} onChange={(e) => setRiskScore(e.target.value)} />
            <button
              type="button"
              className="rounded bg-amber-600 px-3 py-2 text-sm text-white"
              disabled={!selectedId}
              onClick={() => {
                const score = Number(riskScore) || 50
                const band = score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW'
                void run(
                  () =>
                    marketplaceAdminApi
                      .createRiskAssessment({
                        seller_id: selectedId,
                        risk_score: score,
                        risk_band: band,
                        factors_json: '[]',
                      })
                      .then(() => undefined),
                  'Avaliação registrada.',
                )
              }}
            >
              Registrar avaliação
            </button>
          </div>
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">Quando</th>
                <th className="px-3 py-2">Score</th>
                <th className="px-3 py-2">Faixa</th>
              </tr>
            </thead>
            <tbody>
              {riskAssessments.map((r) => (
                <tr key={r.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 text-xs">{r.assessed_at}</td>
                  <td className="px-3 py-2">{r.risk_score}</td>
                  <td className="px-3 py-2">{r.risk_band}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'audit' && (
        <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-2 text-lg font-medium">marketplace_sync_audit_log</h2>
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">Quando</th>
                <th className="px-3 py-2">Evento</th>
                <th className="px-3 py-2">Resumo</th>
              </tr>
            </thead>
            <tbody>
              {syncAuditRows.map((row) => (
                <tr key={row.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 text-xs">{row.created_at}</td>
                  <td className="px-3 py-2 font-mono text-xs">{row.event_type}</td>
                  <td className="px-3 py-2">{row.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {showDataTable && (
        <>
          <h2 className="text-lg font-medium">{listTitle}</h2>
          {tableRows.length === 0 ? (
            <p className="text-sm text-gray-500">Nenhum registro. Use Listar ou Seed.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2">Tipo</th>
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Detalhe</th>
                </tr>
              </thead>
              <tbody>
                {tableRows.map((row) => (
                  <tr key={row.key} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">{row.tipo}</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.id}</td>
                    <td className="px-3 py-2">{row.detalhe}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {tab === 'overview' && !dashboard && !loading && (
        <p className="text-sm text-gray-500">Clique em Listar para carregar o dashboard.</p>
      )}
    </div>
  )
}
