import { FormEvent, useCallback, useEffect, useState } from 'react'
import {
  hardwareAdminApi,
  type HardwareAsset,
  type HardwareCrossDomainDashboard,
  type HardwareIntegrationHubSummary,
  type HardwareVendorPartner,
} from '../../api/hardwareAdmin'
import { useOpsTabFromUrl } from '../../hooks/useOpsTabFromUrl'

const TABS = [
  'dashboard',
  'vendors',
  'ecosystem',
  'marketplace',
  'payments',
  'carriers',
  'assets',
  'finance',
  'operators',
  'runtime',
  'topology',
  'references',
  'links',
  'channels',
  'world',
  'ops',
] as const

type Tab = (typeof TABS)[number]

const TAB_LABELS: Record<Tab, string> = {
  dashboard: 'Dashboard 360°',
  vendors: 'Redes / Vendors',
  ecosystem: 'Ecossistema mundial',
  marketplace: 'Marketplace ↔ Locker',
  payments: 'Payment Gateway ↔ Locker',
  carriers: 'Carriers globais',
  assets: 'Ativos CAPEX',
  finance: 'CAPEX / OPEX',
  operators: 'Operadores',
  runtime: 'Runtime MQTT',
  topology: 'Features · Slots',
  references: 'Refs cross-domain',
  links: 'Locker 360 · Domínios',
  channels: 'Integration Hub · Canais',
  world: 'World Ops · Certificações',
  ops: 'Devices · Sync · Telemetria',
}

export default function OpsHardwareAdmin() {
  const { tab, setTab } = useOpsTabFromUrl<Tab>('/ops/hardware/admin', TABS, 'dashboard')
  const [dashboard, setDashboard] = useState<HardwareCrossDomainDashboard | null>(null)
  const [vendors, setVendors] = useState<HardwareVendorPartner[]>([])
  const [assets, setAssets] = useState<HardwareAsset[]>([])
  const [ecosystem, setEcosystem] = useState<unknown[]>([])
  const [marketplace, setMarketplace] = useState<unknown[]>([])
  const [payments, setPayments] = useState<unknown[]>([])
  const [carriers, setCarriers] = useState<unknown[]>([])
  const [capex, setCapex] = useState<unknown[]>([])
  const [opex, setOpex] = useState<unknown[]>([])
  const [operators, setOperators] = useState<unknown[]>([])
  const [runtimeLockers, setRuntimeLockers] = useState<unknown[]>([])
  const [features, setFeatures] = useState<unknown[]>([])
  const [slots, setSlots] = useState<unknown[]>([])
  const [references, setReferences] = useState<unknown[]>([])
  const [integrationHub, setIntegrationHub] = useState<HardwareIntegrationHubSummary | null>(null)
  const [segments, setSegments] = useState<unknown[]>([])
  const [capabilities, setCapabilities] = useState<unknown[]>([])
  const [playerRelations, setPlayerRelations] = useState<unknown[]>([])
  const [channelBindings, setChannelBindings] = useState<unknown[]>([])
  const [readinessRows, setReadinessRows] = useState<unknown[]>([])
  const [marketplaceBridge, setMarketplaceBridge] = useState<unknown[]>([])
  const [professionalOps, setProfessionalOps] = useState<Record<string, unknown> | null>(null)
  const [certifications, setCertifications] = useState<unknown[]>([])
  const [corridors, setCorridors] = useState<unknown[]>([])
  const [incidents, setIncidents] = useState<unknown[]>([])
  const [onboardingRuns, setOnboardingRuns] = useState<unknown[]>([])
  const [auditLog, setAuditLog] = useState<unknown[]>([])
  const [webhookDeliveries, setWebhookDeliveries] = useState<unknown[]>([])
  const [devices, setDevices] = useState<unknown[]>([])
  const [syncQueue, setSyncQueue] = useState<unknown[]>([])
  const [telemetry, setTelemetry] = useState<unknown[]>([])
  const [linkLockerId, setLinkLockerId] = useState('LOCKER-DEMO-01')
  const [locker360, setLocker360] = useState<Record<string, unknown> | null>(null)
  const [gapsScan, setGapsScan] = useState<Record<string, unknown> | null>(null)
  const [domainVerifications, setDomainVerifications] = useState<unknown[]>([])
  const [vendorForm, setVendorForm] = useState({ name: '', code: '', vendor_type: 'LOCKER_NETWORK' })
  const [selectedVendor, setSelectedVendor] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [
        dash,
        v,
        a,
        eco,
        mkt,
        pay,
        car,
        cap,
        opx,
        o,
        r,
        feat,
        sl,
        ref,
        hub,
        seg,
        caps,
        rels,
        ch,
        ready,
        bridge,
        pro,
        certs,
        corr,
        inc,
        runs,
        audit,
        whdel,
        d,
        s,
        t,
      ] = await Promise.all([
        hardwareAdminApi.getDashboard(),
        hardwareAdminApi.listVendors(),
        hardwareAdminApi.listAssets(),
        hardwareAdminApi.listEcosystemPlayers(),
        hardwareAdminApi.listMarketplaceLinks(),
        hardwareAdminApi.listPaymentBindings(),
        hardwareAdminApi.listCarrierBindings(),
        hardwareAdminApi.listCapex(),
        hardwareAdminApi.listOpex(),
        hardwareAdminApi.listOperators(),
        hardwareAdminApi.listRuntimeLockers(),
        hardwareAdminApi.listFeatures(),
        hardwareAdminApi.listSlots(),
        hardwareAdminApi.listDomainReferences(),
        hardwareAdminApi.getIntegrationHubSummary(),
        hardwareAdminApi.listIntegrationSegments(),
        hardwareAdminApi.listIntegrationCapabilities(),
        hardwareAdminApi.listPlayerRelations(),
        hardwareAdminApi.listChannelBindings(),
        hardwareAdminApi.listIntegrationReadiness(),
        hardwareAdminApi.getMarketplaceBridge(),
        hardwareAdminApi.getProfessionalOpsSummary(),
        hardwareAdminApi.listCertifications(),
        hardwareAdminApi.listCorridors(),
        hardwareAdminApi.listIncidents(),
        hardwareAdminApi.listOnboardingRuns(),
        hardwareAdminApi.listAuditLog(),
        hardwareAdminApi.listWebhookDeliveries(),
        hardwareAdminApi.listDevices(),
        hardwareAdminApi.listSyncQueue(),
        hardwareAdminApi.listTelemetry(),
      ])
      setDashboard(dash.data)
      setVendors(v.data.vendors ?? [])
      setAssets(a.data.items ?? [])
      setEcosystem(eco.data.items ?? [])
      setMarketplace(mkt.data.items ?? [])
      setPayments(pay.data.items ?? [])
      setCarriers(car.data.items ?? [])
      setCapex(cap.data.items ?? [])
      setOpex(opx.data.items ?? [])
      setOperators(o.data.items ?? [])
      setRuntimeLockers(r.data.items ?? [])
      setFeatures(feat.data.items ?? [])
      setSlots(sl.data.items ?? [])
      setReferences(ref.data.items ?? [])
      setIntegrationHub(hub.data)
      setSegments(seg.data.items ?? [])
      setCapabilities(caps.data.items ?? [])
      setPlayerRelations(rels.data.items ?? [])
      setChannelBindings(ch.data.items ?? [])
      setReadinessRows(ready.data.items ?? [])
      setMarketplaceBridge(bridge.data.items ?? [])
      setProfessionalOps(pro.data as Record<string, unknown>)
      setCertifications(certs.data.items ?? [])
      setCorridors(corr.data ?? [])
      setIncidents(inc.data.items ?? [])
      setOnboardingRuns(runs.data ?? [])
      setAuditLog(audit.data.items ?? [])
      setWebhookDeliveries(whdel.data.items ?? [])
      setDevices(d.data.items ?? [])
      setSyncQueue(s.data.items ?? [])
      setTelemetry(t.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const onSeed = async () => {
    setLoading(true)
    try {
      await hardwareAdminApi.seed()
      setMessage('Seed aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreateVendor = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await hardwareAdminApi.createVendor(vendorForm)
      setMessage(`Vendor ${data.code} criado.`)
      setSelectedVendor(data.id)
      setVendorForm({ name: '', code: '', vendor_type: 'LOCKER_NETWORK' })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar vendor')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedVendor || !webhookUrl) return
    setLoading(true)
    try {
      await hardwareAdminApi.configureWebhook(selectedVendor, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['locker.*', 'telemetry.*'],
      })
      setMessage('Webhook configurado.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedVendor) return
    setLoading(true)
    try {
      const { data } = await hardwareAdminApi.rotateApiKey(selectedVendor)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…). Copie agora.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar chave')
    } finally {
      setLoading(false)
    }
  }

  const onSyncMarketplaceMirror = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await hardwareAdminApi.syncMarketplaceMirror()
      setMessage(
        `Mirror marketplace: +${String(data.inserted ?? 0)} caps · sync ${String(data.capabilities_in_sync ?? '—')} players`,
      )
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao sincronizar mirror marketplace')
    } finally {
      setLoading(false)
    }
  }

  const onMirrorCerts = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await hardwareAdminApi.mirrorMarketplaceCertifications()
      setMessage(`Mirror certs: +${String(data.inserted ?? 0)} · updated ${String(data.updated ?? 0)}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao espelhar certificações')
    } finally {
      setLoading(false)
    }
  }

  const onSeedDlq = async () => {
    setLoading(true)
    try {
      const { data } = await hardwareAdminApi.seedDlqDemo()
      setMessage(`DLQ demo: ${String(data.dead_letter ?? 0)} dead-letter`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha seed DLQ')
    } finally {
      setLoading(false)
    }
  }

  const onLoadLocker360 = async () => {
    if (!linkLockerId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const { data } = await hardwareAdminApi.getLocker360(linkLockerId.trim())
      setLocker360(data)
      setDomainVerifications((data.domain_verifications as unknown[]) ?? [])
      setMessage(`Locker 360 carregado · ${String((data.gaps as unknown[])?.length ?? 0)} gaps`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha Locker 360')
    } finally {
      setLoading(false)
    }
  }

  const onScanGaps = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await hardwareAdminApi.scanCrossDomainGaps(
        linkLockerId.trim() ? { locker_id: linkLockerId.trim() } : undefined,
      )
      setGapsScan(data)
      setMessage(`Gap scan: ${String(data.total ?? 0)} achados em ${String(data.lockers_scanned ?? 0)} lockers`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha gap scan')
    } finally {
      setLoading(false)
    }
  }

  const onVerifyDomainRefs = async () => {
    setLoading(true)
    try {
      const { data } = await hardwareAdminApi.verifyDomainReferences(
        linkLockerId.trim() ? { locker_id: linkLockerId.trim() } : undefined,
      )
      setDomainVerifications(data)
      setMessage(`Verificação: ${data.length} refs`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha verificação refs')
    } finally {
      setLoading(false)
    }
  }

  const onSyncPaymentsFromGateway = async (dryRun = false) => {
    setLoading(true)
    try {
      const { data } = await hardwareAdminApi.syncPaymentBindingsFromGateway({
        locker_id: linkLockerId.trim() || undefined,
        dry_run: dryRun,
      })
      setMessage(
        dryRun
          ? `Dry-run gateway: ${String(data.gateway_methods ?? 0)} métodos · +${String(data.inserted ?? 0)} novos`
          : `Sync gateway: +${String(data.inserted ?? 0)} · updated ${String(data.updated ?? 0)}`,
      )
      if (!dryRun) await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha sync payment gateway')
    } finally {
      setLoading(false)
    }
  }

  const onAlignPartnerEcosystem = async () => {
    setLoading(true)
    try {
      const { data } = await hardwareAdminApi.alignEcosystemWithPartner(true)
      setMessage(
        `Partner align: ${String((data.matched as unknown[])?.length ?? 0)} matched · metadata ${String(data.metadata_updated ?? 0)}`,
      )
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha align partner')
    } finally {
      setLoading(false)
    }
  }

  const rows: unknown[] =
    tab === 'dashboard'
      ? dashboard
        ? [dashboard]
        : []
      : tab === 'vendors'
        ? vendors
        : tab === 'ecosystem'
          ? ecosystem
          : tab === 'marketplace'
            ? marketplace
            : tab === 'payments'
              ? payments
              : tab === 'carriers'
                ? carriers
                : tab === 'assets'
                  ? assets
                  : tab === 'finance'
                    ? [...capex, ...opex]
                    : tab === 'operators'
                      ? operators
                      : tab === 'runtime'
                        ? runtimeLockers
                        : tab === 'topology'
                          ? [...features, ...slots]
                          : tab === 'references'
                            ? references
                            : tab === 'links'
                              ? [
                                  ...(locker360 ? [locker360] : []),
                                  ...(gapsScan ? [gapsScan] : []),
                                  ...domainVerifications,
                                ]
                              : tab === 'channels'
                              ? [...readinessRows, ...marketplaceBridge, ...segments, ...capabilities, ...playerRelations, ...channelBindings]
                              : tab === 'world'
                                ? [...(professionalOps ? [professionalOps] : []), ...certifications, ...corridors, ...incidents, ...onboardingRuns, ...webhookDeliveries, ...auditLog]
                                : [...devices, ...syncQueue, ...telemetry]

  const rowLabel = (row: Record<string, unknown>, idx: number) =>
    String(
      row.player_code ??
        row.channel_code ??
        row.payment_method_code ??
        row.carrier_code ??
        row.readiness_band ??
        row.hardware_player_code ??
        row.marketplace_partner_code ??
        row.channel_type ??
        row.corridor_code ??
        row.certification_type ??
        row.incident_type ??
        row.playbook_code ??
        row.event_type ??
        row.capability_code ??
        row.relation_type ??
        row.code ??
        row.asset_code ??
        row.name ??
        row.status ??
        row.gap_type ??
        row.severity ??
        row.locker_id ??
        row.domain_type ??
        row.device_hash ??
        row.event_type ??
        (row.vendors !== undefined ? 'dashboard' : idx),
    )

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Hardware</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Hardware ↔ Marketplace · Payment · Carriers · Finance · Runtime · Order Pickup
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSeed()} className="rounded-lg border px-3 py-2 text-sm">
            Seed
          </button>
          <button
            type="button"
            onClick={async () => {
              setLoading(true)
              try {
                const { data } = await hardwareAdminApi.seedDomainFull(false)
                setMessage(
                  `Domain full: ${String(data.ecosystem_players_total ?? data.ecosystem_players)} players · ${String(data.network_runtime_lockers ?? 0)} redes · ${String(data.player_domain_refs ?? 0)} refs`,
                )
                await load()
              } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'Falha seed domain-full')
              } finally {
                setLoading(false)
              }
            }}
            className="rounded-lg border px-3 py-2 text-sm"
          >
            Seed domain-full
          </button>
          <button
            type="button"
            onClick={() => void onSyncMarketplaceMirror()}
            className="rounded-lg border px-3 py-2 text-sm"
          >
            Sync marketplace mirror
          </button>
          <button type="button" onClick={() => void onMirrorCerts()} className="rounded-lg border px-3 py-2 text-sm">
            Mirror certs (MKT)
          </button>
          <button type="button" onClick={() => void onSeedDlq()} className="rounded-lg border px-3 py-2 text-sm">
            Seed DLQ demo
          </button>
          <button
            type="button"
            onClick={() => void load()}
            className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Atualizar
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-gray-500">Processando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {lastApiKey && (
        <p className="rounded border border-amber-300 bg-amber-50 p-2 font-mono text-xs text-amber-900">
          API key: {lastApiKey}
        </p>
      )}

      {tab === 'world' && professionalOps && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(
            [
              ['Certificações', professionalOps.certifications],
              ['Corredores físicos', professionalOps.corridors],
              ['Incidentes abertos', professionalOps.open_incidents],
              ['Onboarding ativo', professionalOps.onboarding_runs_active],
              ['Webhooks capability', professionalOps.capability_webhooks],
              ['Alertas readiness', professionalOps.open_readiness_alerts],
              ['SLA compliant', professionalOps.corridor_sla_compliant],
              ['Audit log', professionalOps.audit_log_entries],
            ] as const
          ).map(([label, value]) => (
            <div key={label} className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
              <p className="text-xs uppercase text-gray-400">{label}</p>
              <p className="text-2xl font-semibold">{String(value ?? 0)}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'channels' && integrationHub && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(
            [
              ['Segmentos', integrationHub.segments],
              ['Capabilities', integrationHub.capabilities],
              ['Score médio', integrationHub.avg_score?.toFixed?.(1) ?? integrationHub.avg_score],
              ['GO_LIVE', integrationHub.bands?.GO_LIVE ?? 0],
              ['Marketplace linked', integrationHub.marketplace_partners_linked],
              ['Caps in sync', integrationHub.capabilities_in_sync],
              ['Gaps marketplace', integrationHub.marketplace_capability_gaps],
              ['Food delivery', integrationHub.food_delivery_bindings],
              ['Agregadores', integrationHub.aggregator_bindings],
              ['Channel bindings', integrationHub.locker_channel_bindings],
            ] as const
          ).map(([label, value]) => (
            <div key={label} className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
              <p className="text-xs uppercase text-gray-400">{label}</p>
              <p className="text-2xl font-semibold">{value}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'dashboard' && dashboard && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(
            [
              ['Vendors', dashboard.vendors],
              ['Ecossistema', dashboard.ecosystem_players],
              ['Marketplace links', dashboard.marketplace_links],
              ['Payment bindings', dashboard.payment_bindings],
              ['Carriers', dashboard.carrier_bindings],
              ['CAPEX', dashboard.capex_records],
              ['OPEX', dashboard.opex_records],
              ['Sync pending', dashboard.sync_pending],
            ] as const
          ).map(([label, value]) => (
            <div key={label} className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
              <p className="text-xs uppercase text-gray-400">{label}</p>
              <p className="text-2xl font-semibold">{value}</p>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'border'}`}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {tab === 'links' && (
        <div className="space-y-4 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Visão 360° do locker agregando Payment Gateway, Order Pickup, Payments, Finance e Partner — com verificação
            de refs e scan de gaps cross-domain.
          </p>
          <div className="flex flex-wrap items-end gap-2">
            <label className="text-sm">
              Locker ID
              <input
                className="ml-2 rounded border px-2 py-1 font-mono text-sm dark:border-slate-600 dark:bg-slate-800"
                value={linkLockerId}
                onChange={(e) => setLinkLockerId(e.target.value)}
              />
            </label>
            <button type="button" onClick={() => void onLoadLocker360()} className="rounded border px-3 py-1 text-sm">
              Locker 360
            </button>
            <button type="button" onClick={() => void onScanGaps()} className="rounded border px-3 py-1 text-sm">
              Scan gaps
            </button>
            <button type="button" onClick={() => void onVerifyDomainRefs()} className="rounded border px-3 py-1 text-sm">
              Verificar refs
            </button>
            <button
              type="button"
              onClick={() => void onSyncPaymentsFromGateway(true)}
              className="rounded border px-3 py-1 text-sm"
            >
              Dry-run payment sync
            </button>
            <button
              type="button"
              onClick={() => void onSyncPaymentsFromGateway(false)}
              className="rounded border px-3 py-1 text-sm"
            >
              Sync payment gateway
            </button>
            <button type="button" onClick={() => void onAlignPartnerEcosystem()} className="rounded border px-3 py-1 text-sm">
              Align partner ecosystem
            </button>
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                try {
                  const { data } = await hardwareAdminApi.mirrorMarketplaceChannelPartners()
                  setMessage(
                    `Mirror MKT partners: ${String(data.matched ?? 0)} matched · ${String(data.links_created ?? 0)} links`,
                  )
                  await load()
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : 'Falha mirror channel partners')
                } finally {
                  setLoading(false)
                }
              }}
              className="rounded border px-3 py-1 text-sm"
            >
              Mirror MKT channel partners
            </button>
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                try {
                  const { data } = await hardwareAdminApi.runtimeReconcilePull({
                    locker_id: linkLockerId.trim() || undefined,
                  })
                  setMessage(`Runtime pull: +${String(data.inserted ?? 0)} · updated ${String(data.updated ?? 0)}`)
                  await load()
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : 'Falha runtime pull')
                } finally {
                  setLoading(false)
                }
              }}
              className="rounded border px-3 py-1 text-sm"
            >
              Runtime pull
            </button>
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                try {
                  const { data } = await hardwareAdminApi.runtimeReconcilePush({
                    locker_id: linkLockerId.trim() || undefined,
                  })
                  setMessage(`Runtime push: ${String(data.queued ?? 0)} enqueued`)
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : 'Falha runtime push')
                } finally {
                  setLoading(false)
                }
              }}
              className="rounded border px-3 py-1 text-sm"
            >
              Runtime push
            </button>
          </div>
          {locker360 && (
            <pre className="max-h-64 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">
              {JSON.stringify(locker360, null, 2)}
            </pre>
          )}
        </div>
      )}

      {tab === 'vendors' && (
        <>
          <form
            onSubmit={onCreateVendor}
            className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-3"
          >
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Nome (ex. SwipBox)"
              required
              value={vendorForm.name}
              onChange={(e) => setVendorForm({ ...vendorForm, name: e.target.value })}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Código"
              required
              value={vendorForm.code}
              onChange={(e) => setVendorForm({ ...vendorForm, code: e.target.value })}
            />
            <button type="submit" className="rounded bg-indigo-600 px-3 py-2 text-sm text-white">
              Criar vendor
            </button>
          </form>
          <div className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2">
            <select
              className="rounded border px-2 py-1 text-sm"
              value={selectedVendor}
              onChange={(e) => setSelectedVendor(e.target.value)}
            >
              <option value="">Selecione vendor…</option>
              {vendors.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.code} — {v.name}
                </option>
              ))}
            </select>
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Webhook URL"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Webhook secret"
              value={webhookSecret}
              onChange={(e) => setWebhookSecret(e.target.value)}
            />
            <div className="flex gap-2">
              <button type="button" onClick={() => void onWebhook()} className="rounded border px-3 py-1 text-sm">
                Salvar webhook
              </button>
              <button type="button" onClick={() => void onRotateKey()} className="rounded border px-3 py-1 text-sm">
                Rotacionar API key
              </button>
            </div>
          </div>
        </>
      )}

      {tab !== 'dashboard' && (
        <div className="overflow-x-auto rounded-xl border bg-white dark:border-slate-700 dark:bg-slate-900">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b bg-gray-50 dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Detalhe</th>
              </tr>
            </thead>
            <tbody>
              {(rows as Record<string, unknown>[]).map((row, idx) => (
                <tr key={`${rowLabel(row, idx)}-${idx}`} className="border-b">
                  <td className="px-3 py-2 font-mono text-xs">{rowLabel(row, idx)}</td>
                  <td className="px-3 py-2 text-gray-600 dark:text-slate-300">
                    <pre className="whitespace-pre-wrap text-xs">{JSON.stringify(row).slice(0, 320)}</pre>
                  </td>
                </tr>
              ))}
              {!rows.length && (
                <tr>
                  <td colSpan={2} className="px-3 py-6 text-center text-gray-400">
                    Nenhum registro — clique Atualizar ou Seed.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
