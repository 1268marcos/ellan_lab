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
  'rounded border px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100'

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
            className="rounded border px-3 py-2 text-sm dark:border-slate-600"
          >
            {loading ? 'Atualizando…' : 'Listar'}
          </button>
          <button
            type="button"
            onClick={() => void onSeed()}
            disabled={loading}
            className="rounded border px-3 py-2 text-sm dark:border-slate-600"
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

      <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
          className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-3 lg:grid-cols-5"
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
          className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-4"
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
        <div className="flex flex-wrap gap-2 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
          <button type="button" className="rounded border px-3 py-2 text-sm dark:border-slate-600" onClick={() => void onLinkCategory()} disabled={!selectedId || !categoryLinkCategoryId}>
            Vincular ao seller
          </button>
        </div>
      )}

      {tab === 'channels' && (
        <div className="space-y-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
            <button type="button" className="rounded border px-3 py-2 text-sm dark:border-slate-600" onClick={() => void onCreateLockerNetwork()} disabled={!selectedId || !networkChannelId}>
              Vincular rede locker
            </button>
          </div>
        </div>
      )}

      {tab === 'contacts' && (
        <div className="flex flex-wrap gap-2 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
        <div className="flex flex-wrap gap-2 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <input className={inp} placeholder="holder_name" value={payoutForm.holder_name} onChange={(e) => setPayoutForm((f) => ({ ...f, holder_name: e.target.value }))} />
          <input className={inp} placeholder="pix_key" value={payoutForm.pix_key} onChange={(e) => setPayoutForm((f) => ({ ...f, pix_key: e.target.value }))} />
          <button type="button" className="rounded bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => void onCreatePayout()} disabled={!selectedId || !payoutForm.holder_name}>
            Criar conta PIX
          </button>
        </div>
      )}

      {tab === 'settlements' && (
        <div className="flex flex-wrap gap-2 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
          <button type="button" className="rounded border px-3 py-2 text-sm dark:border-slate-600" onClick={() => void onMarkBatchPaid()} disabled={!selectedBatchId}>
            Marcar lote PAID
          </button>
        </div>
      )}

      {tab === 'kyc' && (
        <div className="flex flex-wrap gap-2 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
          <button type="button" className="rounded border px-3 py-2 text-sm dark:border-slate-600" onClick={() => void onApproveKyc()} disabled={!selectedKycId}>
            Aprovar KYC
          </button>
        </div>
      )}

      {tab === 'disputes' && (
        <div className="flex flex-wrap gap-2 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
          <button type="button" className="rounded border px-3 py-2 text-sm dark:border-slate-600" onClick={() => void onResolveDispute()} disabled={!selectedDisputeId}>
            Resolver disputa
          </button>
        </div>
      )}

      {tab === 'commissions' && (
        <div className="flex flex-wrap gap-2 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <select className={inp} value={selectedCommissionId} onChange={(e) => setSelectedCommissionId(e.target.value)}>
            <option value="">commission_id (PENDING)</option>
            {pendingCommissions.map((c) => (
              <option key={c.id} value={c.id}>
                {c.order_id} · {formatBrl(c.commission_amount_cents)}
              </option>
            ))}
          </select>
          <button type="button" className="rounded border px-3 py-2 text-sm dark:border-slate-600" onClick={() => void onSettleCommission()} disabled={!selectedCommissionId}>
            Liquidar comissão
          </button>
        </div>
      )}

      {tab === 'readiness' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button type="button" className="rounded bg-indigo-600 px-3 py-2 text-sm text-white" onClick={() => void onRecomputeReadiness()} disabled={loading}>
              Recalcular prontidão
            </button>
            <button type="button" className="rounded border px-3 py-2 text-sm dark:border-slate-600" onClick={() => void onSimulateInpostDrop()} disabled={loading}>
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
              className="rounded border px-3 py-2 text-sm dark:border-slate-600"
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
                <div key={String(label)} className="rounded-xl border bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className="text-lg font-semibold">{String(val)}</p>
                </div>
              ))}
            </div>
          )}

          <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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

          <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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

          <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
            <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
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
                <div key={String(label)} className="rounded-xl border bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className="text-lg font-semibold">{String(val)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab !== 'overview' && (
        <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-2 text-lg font-medium">Webhook e API key (seller)</h2>
          <div className="flex flex-wrap gap-2">
            <input className={`min-w-[14rem] flex-1 ${inp}`} placeholder="Webhook URL" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
            <input className={inp} placeholder="Secret" value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} />
            <button type="button" onClick={() => void onWebhook()} className="rounded border px-3 py-2 text-sm dark:border-slate-600" disabled={!selectedId || !webhookUrl}>
              Salvar webhook
            </button>
            <button type="button" onClick={() => void onRotateKey()} className="rounded bg-amber-600 px-3 py-2 text-sm text-white" disabled={!selectedId}>
              Rotacionar API key
            </button>
          </div>
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
