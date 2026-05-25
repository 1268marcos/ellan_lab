import { FormEvent, useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  mlAdminApi,
  type MlCapabilityWebhook,
  type MlDashboard,
  type MlDataPartner,
  type MlLockerNetworkPlayer,
  type MlModelMetadata,
  type MlNetworkMlProfile,
  type MlPlayerCapability,
  type MlPlayerRelation,
  type MlReadinessAlert,
  type MlReadinessRow,
  type MlUseCase,
} from '../../api/mlAdmin'

type Tab =
  | 'overview'
  | 'use_cases'
  | 'registry'
  | 'training'
  | 'partners'
  | 'networks'
  | 'readiness'
  | 'models'
  | 'catalog'
  | 'features'
  | 'predictions'
  | 'drift'
  | 'governance'
  | 'deployments'
  | 'grants'
  | 'feedback'

const TAB_KEYS: Tab[] = [
  'overview',
  'use_cases',
  'registry',
  'training',
  'partners',
  'networks',
  'readiness',
  'models',
  'catalog',
  'features',
  'predictions',
  'drift',
  'governance',
  'deployments',
  'grants',
  'feedback',
]

const inputCls = 'ellan-field dark:border-slate-600 dark:bg-slate-800'
const cardCls = 'rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900'

function activeModelVersion(models: MlModelMetadata[]) {
  return models.find((m) => m.status === 'ACTIVE')?.model_version ?? ''
}

export default function OpsMlAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [tab, setTab] = useState<Tab>('overview')
  const [dash, setDash] = useState<MlDashboard | null>(null)
  const [partners, setPartners] = useState<MlDataPartner[]>([])
  const [networkPlayers, setNetworkPlayers] = useState<MlLockerNetworkPlayer[]>([])
  const [networkProfiles, setNetworkProfiles] = useState<MlNetworkMlProfile[]>([])
  const [playerCapabilities, setPlayerCapabilities] = useState<MlPlayerCapability[]>([])
  const [playerRelations, setPlayerRelations] = useState<MlPlayerRelation[]>([])
  const [networkPriorityOnly, setNetworkPriorityOnly] = useState(false)
  const [models, setModels] = useState<MlModelMetadata[]>([])
  const [features, setFeatures] = useState<unknown[]>([])
  const [predictions, setPredictions] = useState<unknown[]>([])
  const [feedback, setFeedback] = useState<unknown[]>([])
  const [useCases, setUseCases] = useState<MlUseCase[]>([])
  const [registry, setRegistry] = useState<unknown[]>([])
  const [trainingRuns, setTrainingRuns] = useState<unknown[]>([])
  const [featureCatalog, setFeatureCatalog] = useState<unknown[]>([])
  const [driftReports, setDriftReports] = useState<unknown[]>([])
  const [slos, setSlos] = useState<unknown[]>([])
  const [alertRules, setAlertRules] = useState<unknown[]>([])
  const [deployments, setDeployments] = useState<unknown[]>([])
  const [grants, setGrants] = useState<unknown[]>([])
  const [mlReadiness, setMlReadiness] = useState<MlReadinessRow[]>([])
  const [mlReadinessHub, setMlReadinessHub] = useState<{
    readiness_rows: number
    avg_score: number
    open_readiness_alerts: number
  } | null>(null)
  const [mlReadinessAlerts, setMlReadinessAlerts] = useState<MlReadinessAlert[]>([])
  const [mlCapabilityWebhooks, setMlCapabilityWebhooks] = useState<MlCapabilityWebhook[]>([])
  const [selectedUseCase, setSelectedUseCase] = useState('')
  const [useCaseForm, setUseCaseForm] = useState({ code: '', name: '', domain: 'LOCKER', tier: 'STANDARD' })
  const [registryForm, setRegistryForm] = useState({ model_version: '', algorithm: 'RandomForest', stage: 'DEV' })
  const [trainingForm, setTrainingForm] = useState({ run_name: '' })
  const [catalogForm, setCatalogForm] = useState({
    feature_name: '',
    feature_group: 'telemetry',
    source_table: 'ml_features_daily',
  })
  const [driftForm, setDriftForm] = useState({ model_version: 'rf-v1-demo', psi_score: '0.1', status: 'OK' })
  const [sloForm, setSloForm] = useState({ p95_latency_ms: '500', min_availability_pct: '99.5' })
  const [alertForm, setAlertForm] = useState({ rule_code: 'DRIFT_PSI', metric: 'psi_score', threshold: '0.25' })
  const [grantPartnerId, setGrantPartnerId] = useState('')
  const [promoteRegistryId, setPromoteRegistryId] = useState('')
  const [capWebhookForm, setCapWebhookForm] = useState({ capability_code: 'TELEMETRY_INGEST', url: '', secret: '' })
  const [partnerForm, setPartnerForm] = useState({ name: '', code: '', partner_type: 'TELEMETRY' })
  const [modelForm, setModelForm] = useState({ model_version: '', status: 'ACTIVE' })
  const [featureForm, setFeatureForm] = useState({
    locker_id: '',
    feature_date: '',
    battery_min: '',
    door_failures_7d: '0',
  })
  const [predForm, setPredForm] = useState({
    locker_id: '',
    failure_probability: '0.1',
    health_score: '90',
    model_version: 'rf-v1-demo',
  })
  const [selectedPartner, setSelectedPartner] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const useCaseLabel = (id: string) => useCases.find((u) => u.id === id)?.code ?? id

  const setTabAndUrl = (next: Tab) => {
    setTab(next)
    if (next === 'overview') {
      setSearchParams({}, { replace: true })
    } else {
      setSearchParams({ tab: next }, { replace: true })
    }
  }

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const netParams = {
        active_only: true,
        ...(networkPriorityOnly ? { priority_only: true } : {}),
      }
      const [
        d,
        p,
        net,
        nprof,
        pcap,
        prel,
        m,
        f,
        pr,
        fb,
        uc,
        reg,
        tr,
        cat,
        dr,
        slo,
        al,
        dep,
        gr,
        mlrd,
        mlhub,
        mlalerts,
        mlwh,
      ] = await Promise.all([
        mlAdminApi.dashboard(),
        mlAdminApi.listPartners(),
        mlAdminApi.listLockerNetworks(netParams),
        mlAdminApi.listNetworkMlProfiles(),
        mlAdminApi.listPlayerCapabilities(),
        mlAdminApi.listPlayerRelations(),
        mlAdminApi.listModels(),
        mlAdminApi.listFeatures({ limit: 50 }),
        mlAdminApi.listPredictions({ limit: 50 }),
        mlAdminApi.listFeedback(),
        mlAdminApi.listUseCases(),
        mlAdminApi.listRegistry(),
        mlAdminApi.listTrainingRuns(),
        mlAdminApi.listFeatureCatalog(),
        mlAdminApi.listDrift(),
        mlAdminApi.listSlos(),
        mlAdminApi.listAlerts(),
        mlAdminApi.listDeployments(),
        mlAdminApi.listGrants(),
        mlAdminApi.listMlReadiness(),
        mlAdminApi.mlReadinessHub(),
        mlAdminApi.listMlReadinessAlerts(true),
        mlAdminApi.listMlCapabilityWebhooks(),
      ])
      const partnerList = p.data.partners ?? []
      const modelList = m.data.items ?? []
      const ucList = uc.data.items ?? []
      setDash(d.data)
      setPartners(partnerList)
      setNetworkPlayers(net.data.items ?? [])
      setNetworkProfiles(nprof.data.items ?? [])
      setPlayerCapabilities(pcap.data.items ?? [])
      setPlayerRelations(prel.data.items ?? [])
      setModels(modelList)
      setFeatures(f.data.items ?? [])
      setPredictions(pr.data.items ?? [])
      setFeedback(fb.data.items ?? [])
      setUseCases(ucList)
      setRegistry(reg.data.items ?? [])
      setTrainingRuns(tr.data.items ?? [])
      setFeatureCatalog(cat.data.items ?? [])
      setDriftReports(dr.data.items ?? [])
      setSlos(slo.data.items ?? [])
      setAlertRules(al.data.items ?? [])
      setDeployments(dep.data.items ?? [])
      setGrants(gr.data.items ?? [])
      setMlReadiness(mlrd.data.items ?? [])
      setMlReadinessHub(mlhub.data)
      setMlReadinessAlerts(mlalerts.data.items ?? [])
      setMlCapabilityWebhooks(mlwh.data.items ?? [])
      setSelectedUseCase((prev) => prev || ucList[0]?.id || '')
      setGrantPartnerId((prev) => prev || partnerList[0]?.id || '')
      const ver = activeModelVersion(modelList)
      if (ver) setPredForm((pf) => (pf.model_version ? pf : { ...pf, model_version: ver }))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [networkPriorityOnly])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    const q = searchParams.get('tab') as Tab | null
    if (q && TAB_KEYS.includes(q)) setTab(q)
    else if (!q) setTab('overview')
  }, [searchParams])

  const firstNetworkPlayerId = networkPlayers[0]?.id ?? ''

  const onSeed = async () => {
    setLoading(true)
    try {
      await mlAdminApi.seed()
      setMessage('Seed ML aplicado (casos de uso, redes, registry, catálogo, SLO, drift e demo).')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onSeedNetworks = async () => {
    setLoading(true)
    try {
      const { data } = await mlAdminApi.seedLockerNetworks()
      setMessage(
        `Redes locker: ${data.inserted} novas, ${data.updated} atualizadas, ${data.profiles_created} perfis ML (catálogo ${data.catalog_size}).`,
      )
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed de redes')
    } finally {
      setLoading(false)
    }
  }

  const onValidateFeedback = async () => {
    setLoading(true)
    try {
      const { data } = await mlAdminApi.validateFeedback()
      setMessage(`Feedback validado: ${data.inserted ?? 0} inseridos.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na validação')
    } finally {
      setLoading(false)
    }
  }

  const onCreatePartner = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await mlAdminApi.createPartner(partnerForm)
      setMessage(`Parceiro ML ${data.code} criado.`)
      setSelectedPartner(data.id)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar parceiro')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedPartner || !webhookUrl) return
    setLoading(true)
    try {
      await mlAdminApi.configureWebhook(selectedPartner, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['prediction.*', 'feedback.*'],
      })
      setMessage('Webhook ML salvo.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedPartner) return
    setLoading(true)
    try {
      const { data } = await mlAdminApi.rotateApiKey(selectedPartner)
      setLastApiKey(data.api_key)
      setMessage('API key rotacionada (copie agora).')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na rotação')
    } finally {
      setLoading(false)
    }
  }

  const onCreateUseCase = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await mlAdminApi.createUseCase(useCaseForm)
      setSelectedUseCase(data.id)
      setMessage(`Caso de uso ${data.code} criado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar caso de uso')
    } finally {
      setLoading(false)
    }
  }

  const onCreateRegistry = async (e: FormEvent) => {
    e.preventDefault()
    if (!selectedUseCase) return
    setLoading(true)
    try {
      await mlAdminApi.createRegistry({ use_case_id: selectedUseCase, ...registryForm })
      setMessage('Entrada no model registry criada.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no registry')
    } finally {
      setLoading(false)
    }
  }

  const onPromoteRegistry = async () => {
    if (!promoteRegistryId) return
    setLoading(true)
    try {
      const { data } = await mlAdminApi.promoteRegistry(promoteRegistryId, { actor_id: 'ops-ui' })
      setMessage(`Modelo ${(data as { model_version?: string }).model_version ?? promoteRegistryId} promovido.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao promover')
    } finally {
      setLoading(false)
    }
  }

  const onCreateTraining = async (e: FormEvent) => {
    e.preventDefault()
    if (!selectedUseCase) return
    setLoading(true)
    try {
      await mlAdminApi.createTrainingRun({
        use_case_id: selectedUseCase,
        run_name: trainingForm.run_name,
        triggered_by: 'ops-ui',
      })
      setMessage('Experimento enfileirado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no experimento')
    } finally {
      setLoading(false)
    }
  }

  const onCreateCatalogFeature = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await mlAdminApi.createFeatureCatalog({
        use_case_id: selectedUseCase || null,
        ...catalogForm,
      })
      setMessage(`Feature ${catalogForm.feature_name} no catálogo.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no catálogo')
    } finally {
      setLoading(false)
    }
  }

  const onCreateDrift = async (e: FormEvent) => {
    e.preventDefault()
    if (!selectedUseCase) return
    setLoading(true)
    try {
      await mlAdminApi.createDrift({
        use_case_id: selectedUseCase,
        model_version: driftForm.model_version,
        psi_score: Number(driftForm.psi_score),
        status: driftForm.status,
      })
      setMessage('Relatório de drift registrado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no drift')
    } finally {
      setLoading(false)
    }
  }

  const onCreateSlo = async (e: FormEvent) => {
    e.preventDefault()
    if (!selectedUseCase) return
    setLoading(true)
    try {
      await mlAdminApi.createSlo({
        use_case_id: selectedUseCase,
        p95_latency_ms: Number(sloForm.p95_latency_ms),
        min_availability_pct: Number(sloForm.min_availability_pct),
      })
      setMessage('SLO de inferência salvo.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no SLO')
    } finally {
      setLoading(false)
    }
  }

  const onCreateAlert = async (e: FormEvent) => {
    e.preventDefault()
    if (!selectedUseCase) return
    setLoading(true)
    try {
      await mlAdminApi.createAlertRule({
        use_case_id: selectedUseCase,
        ...alertForm,
        threshold: Number(alertForm.threshold),
      })
      setMessage(`Alerta ${alertForm.rule_code} criado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no alerta')
    } finally {
      setLoading(false)
    }
  }

  const onCreateGrant = async (e: FormEvent) => {
    e.preventDefault()
    if (!grantPartnerId || !selectedUseCase) return
    setLoading(true)
    try {
      await mlAdminApi.createGrant({ partner_id: grantPartnerId, use_case_id: selectedUseCase })
      setMessage('Grant parceiro ↔ caso de uso criado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no grant')
    } finally {
      setLoading(false)
    }
  }

  const onRecomputeReadiness = async () => {
    setLoading(true)
    try {
      await mlAdminApi.recomputeMlReadiness()
      setMessage('Prontidão ML recalculada.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao recalcular prontidão')
    } finally {
      setLoading(false)
    }
  }

  const onUpsertCapabilityWebhook = async (e: FormEvent) => {
    e.preventDefault()
    if (!firstNetworkPlayerId || !capWebhookForm.url) return
    setLoading(true)
    try {
      await mlAdminApi.upsertMlCapabilityWebhook({
        network_player_id: firstNetworkPlayerId,
        capability_code: capWebhookForm.capability_code,
        url: capWebhookForm.url,
        secret: capWebhookForm.secret || undefined,
        events: ['readiness.*', 'capability.*'],
      })
      setMessage('Webhook de capability salvo.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook de capability')
    } finally {
      setLoading(false)
    }
  }

  const onCreateModel = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await mlAdminApi.createModel({
        model_version: modelForm.model_version,
        status: modelForm.status,
        metrics: { seeded: true },
      })
      setMessage(`Modelo ${modelForm.model_version} registrado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar modelo')
    } finally {
      setLoading(false)
    }
  }

  const onCreateFeature = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await mlAdminApi.createFeature({
        locker_id: featureForm.locker_id,
        feature_date: featureForm.feature_date,
        battery_min: featureForm.battery_min ? Number(featureForm.battery_min) : null,
        door_failures_7d: Number(featureForm.door_failures_7d),
        usage_events_7d: 0,
        uptime_hours_7d: 0,
        failure_label_7d: 0,
      })
      setMessage('Feature diária criada.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar feature')
    } finally {
      setLoading(false)
    }
  }

  const onCreatePrediction = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await mlAdminApi.createPrediction({
        locker_id: predForm.locker_id,
        failure_probability: Number(predForm.failure_probability),
        health_score: Number(predForm.health_score),
        model_version: predForm.model_version,
      })
      setMessage('Predição registrada no log.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao registrar predição')
    } finally {
      setLoading(false)
    }
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'overview', label: 'Visão geral' },
    { key: 'use_cases', label: 'Casos de uso' },
    { key: 'registry', label: 'Model registry' },
    { key: 'training', label: 'Experimentos' },
    { key: 'partners', label: 'Parceiros ML' },
    { key: 'networks', label: 'Redes locker' },
    { key: 'readiness', label: 'Prontidão ML' },
    { key: 'models', label: 'Metadata' },
    { key: 'catalog', label: 'Catálogo features' },
    { key: 'features', label: 'Features diárias' },
    { key: 'predictions', label: 'Predições' },
    { key: 'drift', label: 'Drift' },
    { key: 'governance', label: 'SLO e alertas' },
    { key: 'deployments', label: 'Deployments' },
    { key: 'grants', label: 'Acesso parceiro' },
    { key: 'feedback', label: 'Feedback' },
  ]

  const useCaseTabs: Tab[] = ['registry', 'training', 'catalog', 'drift', 'governance', 'grants']
  const showDataTable = tab !== 'overview' && tab !== 'readiness'

  const useCaseSelect = (
    <select
      className={inputCls}
      value={selectedUseCase}
      onChange={(e) => setSelectedUseCase(e.target.value)}
    >
      <option value="">Caso de uso</option>
      {useCases.map((u) => (
        <option key={u.id} value={u.id}>
          {u.code} — {u.tier}
        </option>
      ))}
    </select>
  )

  return (
    <div className="space-y-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">ML OPS — Admin</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Casos de uso, registry, redes locker, prontidão ML, modelos, features e predições
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="ellan-btn-outline"
          >
            Atualizar
          </button>
          <button
            type="button"
            onClick={() => void onSeed()}
            disabled={loading}
            className="rounded bg-indigo-600 px-3 py-2 text-sm text-white"
          >
            Seed
          </button>
          {tab === 'networks' && (
            <button
              type="button"
              onClick={() => void onSeedNetworks()}
              disabled={loading}
              className="rounded bg-violet-600 px-3 py-2 text-sm text-white"
            >
              Seed redes locker
            </button>
          )}
          {tab === 'readiness' && (
            <button
              type="button"
              onClick={() => void onRecomputeReadiness()}
              disabled={loading}
              className="rounded bg-violet-600 px-3 py-2 text-sm text-white"
            >
              Recalcular prontidão
            </button>
          )}
          <button
            type="button"
            onClick={() => void onValidateFeedback()}
            disabled={loading}
            className="rounded bg-amber-600 px-3 py-2 text-sm text-white"
          >
            Validar feedback
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

      {tab === 'overview' && dash && (
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5">
          {[
            ['Casos de uso', dash.use_cases ?? 0],
            ['Modelos em PROD', dash.registry_production ?? 0],
            ['Modelos ativos', dash.active_models],
            ['Predições 24h', dash.predictions_24h],
            ['Drift CRITICAL', dash.drift_critical ?? 0],
            ['Features catálogo', dash.feature_definitions ?? 0],
            ['Experimentos RUNNING', dash.training_running ?? 0],
            ['Alertas ativos', dash.alert_rules ?? 0],
            ['Alertas prontidão abertos', dash.ml_readiness_alerts_open ?? 0],
            ['Deploys 7d', dash.deployments_7d ?? 0],
            ['Features diárias', dash.features_rows],
            ['Feedback', dash.feedback_rows],
            ['Parceiros ML', dash.partners],
            ['Redes locker', dash.locker_network_players ?? 0],
            ['Redes prioritárias', dash.locker_network_priority ?? 0],
            ['Perfis ML por rede', dash.network_ml_profiles ?? 0],
            ['Prontidão ML (redes)', dash.ml_readiness_rows ?? 0],
            ['ML GO_LIVE', dash.ml_readiness_go_live ?? 0],
            ['Score médio prontidão', dash.ml_readiness_avg_score ?? '—'],
            ['Capacidades', dash.player_capabilities ?? 0],
            ['Relações', dash.player_relations ?? 0],
            ['Players TIER1', dash.tier1_players ?? 0],
          ].map(([label, val]) => (
            <div key={String(label)} className={cardCls}>
              <p className="text-xs text-gray-500">{label}</p>
              <p className="text-2xl font-semibold">{val}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'overview' && dash && (
        <p className="text-sm text-gray-500 dark:text-slate-400">
          <button type="button" className="text-indigo-600 underline dark:text-indigo-300" onClick={() => setTabAndUrl('use_cases')}>
            Casos de uso
          </button>
          {' · '}
          <button type="button" className="text-indigo-600 underline dark:text-indigo-300" onClick={() => setTabAndUrl('networks')}>
            Redes locker
          </button>
          {' · '}
          <button type="button" className="text-indigo-600 underline dark:text-indigo-300" onClick={() => setTabAndUrl('readiness')}>
            Prontidão ML
          </button>
        </p>
      )}

      {useCaseTabs.includes(tab) && (
        <section className={`${cardCls} flex flex-wrap items-center gap-2`}>
          <span className="text-sm text-gray-500">Foco:</span>
          {useCaseSelect}
        </section>
      )}

      {tab === 'use_cases' && (
        <form onSubmit={onCreateUseCase} className={`${cardCls} grid gap-3 md:grid-cols-5`}>
          <input className={inputCls} placeholder="code" required value={useCaseForm.code} onChange={(e) => setUseCaseForm((f) => ({ ...f, code: e.target.value }))} />
          <input className={inputCls} placeholder="name" required value={useCaseForm.name} onChange={(e) => setUseCaseForm((f) => ({ ...f, name: e.target.value }))} />
          <select className={inputCls} value={useCaseForm.domain} onChange={(e) => setUseCaseForm((f) => ({ ...f, domain: e.target.value }))}>
            <option value="LOCKER">LOCKER</option>
            <option value="PARTNER">PARTNER</option>
            <option value="CUSTOMER">CUSTOMER</option>
            <option value="LOGISTICS">LOGISTICS</option>
            <option value="PRICING">PRICING</option>
          </select>
          <select className={inputCls} value={useCaseForm.tier} onChange={(e) => setUseCaseForm((f) => ({ ...f, tier: e.target.value }))}>
            <option value="CRITICAL">CRITICAL</option>
            <option value="STANDARD">STANDARD</option>
            <option value="EXPERIMENTAL">EXPERIMENTAL</option>
          </select>
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar caso de uso
          </button>
        </form>
      )}

      {tab === 'registry' && (
        <>
          <form onSubmit={onCreateRegistry} className={`${cardCls} grid gap-3 md:grid-cols-4`}>
            <input className={inputCls} placeholder="model_version" required value={registryForm.model_version} onChange={(e) => setRegistryForm((f) => ({ ...f, model_version: e.target.value }))} />
            <select className={inputCls} value={registryForm.stage} onChange={(e) => setRegistryForm((f) => ({ ...f, stage: e.target.value }))}>
              <option value="DEV">DEV</option>
              <option value="STAGING">STAGING</option>
              <option value="PRODUCTION">PRODUCTION</option>
            </select>
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
              Registrar no registry
            </button>
          </form>
          <div className={`${cardCls} flex flex-wrap gap-2`}>
            <select className={inputCls} value={promoteRegistryId} onChange={(e) => setPromoteRegistryId(e.target.value)}>
              <option value="">Promover entry</option>
              {registry.map((r) => {
                const row = r as { id: string; model_version: string; stage: string }
                return (
                  <option key={row.id} value={row.id}>
                    {row.model_version} ({row.stage})
                  </option>
                )
              })}
            </select>
            <button type="button" onClick={() => void onPromoteRegistry()} className="ellan-btn-outline">
              Promover PRODUCTION
            </button>
          </div>
        </>
      )}

      {tab === 'training' && (
        <form onSubmit={onCreateTraining} className={`${cardCls} grid gap-3 md:grid-cols-3`}>
          <input className={inputCls} placeholder="run_name" required value={trainingForm.run_name} onChange={(e) => setTrainingForm({ run_name: e.target.value })} />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Novo experimento
          </button>
        </form>
      )}

      {tab === 'catalog' && (
        <form onSubmit={onCreateCatalogFeature} className={`${cardCls} grid gap-3 md:grid-cols-4`}>
          <input className={inputCls} placeholder="feature_name" required value={catalogForm.feature_name} onChange={(e) => setCatalogForm((f) => ({ ...f, feature_name: e.target.value }))} />
          <input className={inputCls} placeholder="feature_group" value={catalogForm.feature_group} onChange={(e) => setCatalogForm((f) => ({ ...f, feature_group: e.target.value }))} />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Catalogar feature
          </button>
        </form>
      )}

      {tab === 'drift' && (
        <form onSubmit={onCreateDrift} className={`${cardCls} grid gap-3 md:grid-cols-4`}>
          <input className={inputCls} value={driftForm.model_version} onChange={(e) => setDriftForm((f) => ({ ...f, model_version: e.target.value }))} />
          <input className={inputCls} placeholder="psi_score" value={driftForm.psi_score} onChange={(e) => setDriftForm((f) => ({ ...f, psi_score: e.target.value }))} />
          <select className={inputCls} value={driftForm.status} onChange={(e) => setDriftForm((f) => ({ ...f, status: e.target.value }))}>
            <option value="OK">OK</option>
            <option value="WARNING">WARNING</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Registrar drift
          </button>
        </form>
      )}

      {tab === 'governance' && (
        <div className="space-y-3">
          <form onSubmit={onCreateSlo} className={`${cardCls} grid gap-3 md:grid-cols-4`}>
            <input className={inputCls} placeholder="p95_latency_ms" value={sloForm.p95_latency_ms} onChange={(e) => setSloForm((f) => ({ ...f, p95_latency_ms: e.target.value }))} />
            <input className={inputCls} placeholder="min_availability_pct" value={sloForm.min_availability_pct} onChange={(e) => setSloForm((f) => ({ ...f, min_availability_pct: e.target.value }))} />
            <button type="submit" className="rounded border px-4 py-2 text-sm dark:border-slate-600">
              Salvar SLO
            </button>
          </form>
          <form onSubmit={onCreateAlert} className={`${cardCls} grid gap-3 md:grid-cols-4`}>
            <input className={inputCls} value={alertForm.rule_code} onChange={(e) => setAlertForm((f) => ({ ...f, rule_code: e.target.value }))} />
            <input className={inputCls} placeholder="threshold" value={alertForm.threshold} onChange={(e) => setAlertForm((f) => ({ ...f, threshold: e.target.value }))} />
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
              Criar alerta
            </button>
          </form>
        </div>
      )}

      {tab === 'grants' && (
        <form onSubmit={onCreateGrant} className={`${cardCls} flex flex-wrap gap-2`}>
          <select className={inputCls} value={grantPartnerId} onChange={(e) => setGrantPartnerId(e.target.value)}>
            <option value="">Parceiro</option>
            {partners.map((p) => (
              <option key={p.id} value={p.id}>
                {p.code}
              </option>
            ))}
          </select>
          {useCaseSelect}
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Conceder acesso
          </button>
        </form>
      )}

      {tab === 'networks' && (
        <section className={cardCls}>
          <h2 className="text-lg font-medium">Redes locker mundiais</h2>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            InPost, DHL, Magalu, Mercado Livre e demais operadores do catálogo marketplace.
          </p>
          <label className="mt-2 flex items-center gap-2 text-sm">
            <input type="checkbox" checked={networkPriorityOnly} onChange={(e) => setNetworkPriorityOnly(e.target.checked)} />
            Somente redes prioritárias
          </label>
        </section>
      )}

      {tab === 'readiness' && (
        <div className="space-y-4">
          {mlReadinessHub && (
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                ['Redes avaliadas', mlReadinessHub.readiness_rows],
                ['Score médio', mlReadinessHub.avg_score?.toFixed?.(1) ?? mlReadinessHub.avg_score],
                ['Alertas abertos', mlReadinessHub.open_readiness_alerts],
              ].map(([label, val]) => (
                <div key={String(label)} className={cardCls}>
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className="text-2xl font-semibold">{val}</p>
                </div>
              ))}
            </div>
          )}
          <section className={cardCls}>
            <h2 className="mb-2 text-lg font-medium">Alertas de prontidão (abertos)</h2>
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2">Rede</th>
                  <th className="px-3 py-2">Tipo</th>
                  <th className="px-3 py-2">Severidade</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">Reconhecer</th>
                </tr>
              </thead>
              <tbody>
                {mlReadinessAlerts.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-gray-500">
                      Nenhum alerta aberto.
                    </td>
                  </tr>
                )}
                {mlReadinessAlerts.map((a) => (
                  <tr key={a.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 font-mono text-xs">{a.network_player_code}</td>
                    <td className="px-3 py-2">{a.alert_type}</td>
                    <td className="px-3 py-2">{a.severity}</td>
                    <td className="px-3 py-2">
                      {a.previous_score ?? '—'} → {a.new_score} (Δ{a.score_delta})
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-500">N/A</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section className={cardCls}>
            <h2 className="mb-2 text-lg font-medium">Webhooks de capability</h2>
            {firstNetworkPlayerId ? (
              <p className="mb-2 text-xs text-gray-500">
                network_player_id: <span className="font-mono">{networkPlayers[0]?.code ?? firstNetworkPlayerId}</span>
              </p>
            ) : (
              <p className="mb-2 text-sm text-amber-700 dark:text-amber-300">Seed redes locker para obter network_player_id.</p>
            )}
            <form onSubmit={onUpsertCapabilityWebhook} className="mb-3 grid gap-2 md:grid-cols-4">
              <input className={inputCls} placeholder="capability_code" value={capWebhookForm.capability_code} onChange={(e) => setCapWebhookForm((f) => ({ ...f, capability_code: e.target.value }))} />
              <input className={inputCls} placeholder="URL" required value={capWebhookForm.url} onChange={(e) => setCapWebhookForm((f) => ({ ...f, url: e.target.value }))} />
              <input className={inputCls} placeholder="secret (opcional)" value={capWebhookForm.secret} onChange={(e) => setCapWebhookForm((f) => ({ ...f, secret: e.target.value }))} />
              <button type="submit" disabled={!firstNetworkPlayerId} className="rounded bg-emerald-600 px-4 py-2 text-sm text-white disabled:opacity-50">
                Salvar webhook
              </button>
            </form>
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
                <tr>
                  <th className="px-3 py-2">Rede</th>
                  <th className="px-3 py-2">Capability</th>
                  <th className="px-3 py-2">URL</th>
                  <th className="px-3 py-2">HTTP</th>
                </tr>
              </thead>
              <tbody>
                {mlCapabilityWebhooks.map((w) => (
                  <tr key={w.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 font-mono text-xs">{w.network_player_code}</td>
                    <td className="px-3 py-2">{w.capability_code}</td>
                    <td className="px-3 py-2 truncate text-xs">{w.url}</td>
                    <td className="px-3 py-2">{w.last_http_status ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>
      )}

      {tab === 'partners' && (
        <>
          <form onSubmit={onCreatePartner} className={`${cardCls} grid gap-3 md:grid-cols-4`}>
            <input className={inputCls} placeholder="Nome" required value={partnerForm.name} onChange={(e) => setPartnerForm((f) => ({ ...f, name: e.target.value }))} />
            <input className={inputCls} placeholder="Código" required value={partnerForm.code} onChange={(e) => setPartnerForm((f) => ({ ...f, code: e.target.value }))} />
            <select className={inputCls} value={partnerForm.partner_type} onChange={(e) => setPartnerForm((f) => ({ ...f, partner_type: e.target.value }))}>
              <option value="TELEMETRY">TELEMETRY</option>
              <option value="SCORING">SCORING</option>
              <option value="EXTERNAL">EXTERNAL</option>
            </select>
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
              Criar parceiro ML
            </button>
          </form>
          <section className={cardCls}>
            <h2 className="mb-2 text-lg font-medium">Webhook e API key</h2>
            <div className="flex flex-wrap gap-2">
              <select className={inputCls} value={selectedPartner} onChange={(e) => setSelectedPartner(e.target.value)}>
                <option value="">Parceiro</option>
                {partners.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code}
                  </option>
                ))}
              </select>
              <input className={`${inputCls} min-w-[14rem] flex-1`} placeholder="Webhook URL" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
              <input className={inputCls} placeholder="Secret" value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} />
              <button type="button" onClick={() => void onWebhook()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
                Webhook
              </button>
              <button type="button" onClick={() => void onRotateKey()} className="rounded bg-amber-600 px-3 py-1 text-sm text-white">
                Rotacionar API key
              </button>
            </div>
          </section>
        </>
      )}

      {tab === 'models' && (
        <form onSubmit={onCreateModel} className={`${cardCls} grid gap-3 md:grid-cols-3`}>
          <input className={inputCls} placeholder="Versão (ex: rf-v2)" required value={modelForm.model_version} onChange={(e) => setModelForm((f) => ({ ...f, model_version: e.target.value }))} />
          <select className={inputCls} value={modelForm.status} onChange={(e) => setModelForm((f) => ({ ...f, status: e.target.value }))}>
            <option value="ACTIVE">ACTIVE</option>
            <option value="STALE">STALE</option>
            <option value="FAILED">FAILED</option>
          </select>
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Registrar modelo
          </button>
        </form>
      )}

      {tab === 'features' && (
        <form onSubmit={onCreateFeature} className={`${cardCls} grid gap-3 md:grid-cols-4`}>
          <input className={inputCls} placeholder="locker_id" required value={featureForm.locker_id} onChange={(e) => setFeatureForm((f) => ({ ...f, locker_id: e.target.value }))} />
          <input type="date" className={inputCls} required value={featureForm.feature_date} onChange={(e) => setFeatureForm((f) => ({ ...f, feature_date: e.target.value }))} />
          <input className={inputCls} placeholder="battery_min" value={featureForm.battery_min} onChange={(e) => setFeatureForm((f) => ({ ...f, battery_min: e.target.value }))} />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Inserir feature
          </button>
        </form>
      )}

      {tab === 'predictions' && (
        <form onSubmit={onCreatePrediction} className={`${cardCls} grid gap-3 md:grid-cols-5`}>
          <input className={inputCls} placeholder="locker_id" required value={predForm.locker_id} onChange={(e) => setPredForm((f) => ({ ...f, locker_id: e.target.value }))} />
          <input className={inputCls} placeholder="P(falha)" value={predForm.failure_probability} onChange={(e) => setPredForm((f) => ({ ...f, failure_probability: e.target.value }))} />
          <input className={inputCls} placeholder="health_score" value={predForm.health_score} onChange={(e) => setPredForm((f) => ({ ...f, health_score: e.target.value }))} />
          <input className={inputCls} placeholder="model_version" value={predForm.model_version} onChange={(e) => setPredForm((f) => ({ ...f, model_version: e.target.value }))} />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Registrar predição
          </button>
        </form>
      )}

      {showDataTable && (
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2">ID / Código</th>
              <th className="px-3 py-2">Detalhe</th>
            </tr>
          </thead>
          <tbody>
            {tab === 'use_cases' &&
              useCases.map((u) => (
                <tr key={u.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 text-xs text-gray-500">use_case</td>
                  <td className="px-3 py-2 font-mono text-xs">{u.code}</td>
                  <td className="px-3 py-2">
                    {u.name} · {u.domain} · {u.tier}
                  </td>
                </tr>
              ))}
            {tab === 'registry' &&
              registry.map((r) => {
                const row = r as { id: string; model_version: string; use_case_id: string; stage: string; algorithm?: string }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">registry</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.model_version}</td>
                    <td className="px-3 py-2">
                      {useCaseLabel(row.use_case_id)} · {row.stage} · {row.algorithm ?? '—'}
                    </td>
                  </tr>
                )
              })}
            {tab === 'training' &&
              trainingRuns.map((t) => {
                const row = t as { id: string; run_name: string; use_case_id: string; status: string; model_version?: string }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">run</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.run_name}</td>
                    <td className="px-3 py-2">
                      {useCaseLabel(row.use_case_id)} · {row.status} · {row.model_version ?? '—'}
                    </td>
                  </tr>
                )
              })}
            {tab === 'catalog' &&
              featureCatalog.map((c) => {
                const row = c as { id: string; feature_name: string; feature_group: string; source_table?: string; freshness_hours?: number }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">def</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.feature_name}</td>
                    <td className="px-3 py-2">
                      {row.feature_group} · {row.source_table ?? '—'} · SLA {row.freshness_hours ?? '—'}h
                    </td>
                  </tr>
                )
              })}
            {tab === 'drift' &&
              driftReports.map((d) => {
                const row = d as { id: string; drift_type?: string; model_version: string; use_case_id: string; psi_score?: number; status: string }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">{row.drift_type ?? 'drift'}</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.model_version}</td>
                    <td className="px-3 py-2">
                      {useCaseLabel(row.use_case_id)} · PSI {row.psi_score ?? '—'} · {row.status}
                    </td>
                  </tr>
                )
              })}
            {tab === 'governance' && (
              <>
                {slos.map((s) => {
                  const row = s as { id: string; use_case_id: string; p95_latency_ms: number; min_availability_pct: number }
                  return (
                    <tr key={`slo-${row.id}`} className="border-t dark:border-slate-800">
                      <td className="px-3 py-2 text-xs text-gray-500">slo</td>
                      <td className="px-3 py-2 font-mono text-xs">{useCaseLabel(row.use_case_id)}</td>
                      <td className="px-3 py-2">
                        p95 {row.p95_latency_ms}ms · avail {row.min_availability_pct}%
                      </td>
                    </tr>
                  )
                })}
                {alertRules.map((a) => {
                  const row = a as { id: string; rule_code: string; metric: string; operator?: string; threshold: number; severity: string }
                  return (
                    <tr key={`al-${row.id}`} className="border-t dark:border-slate-800">
                      <td className="px-3 py-2 text-xs text-gray-500">alert</td>
                      <td className="px-3 py-2 font-mono text-xs">{row.rule_code}</td>
                      <td className="px-3 py-2">
                        {row.metric} {row.operator ?? '>='} {row.threshold} · {row.severity}
                      </td>
                    </tr>
                  )
                })}
              </>
            )}
            {tab === 'deployments' &&
              deployments.map((d) => {
                const row = d as { id: string; event_type: string; to_version: string; use_case_id: string; from_version?: string; created_at: string }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">{row.event_type}</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.to_version}</td>
                    <td className="px-3 py-2">
                      {useCaseLabel(row.use_case_id)} · from {row.from_version ?? '—'} · {row.created_at}
                    </td>
                  </tr>
                )
              })}
            {tab === 'grants' &&
              grants.map((g) => {
                const row = g as { partner_id: string; use_case_id: string; scopes_json?: string }
                return (
                  <tr key={`${row.partner_id}-${row.use_case_id}`} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">grant</td>
                    <td className="px-3 py-2 font-mono text-xs">{useCaseLabel(row.use_case_id)}</td>
                    <td className="px-3 py-2">
                      partner {row.partner_id.slice(0, 8)}… · {row.scopes_json ?? '—'}
                    </td>
                  </tr>
                )
              })}
            {tab === 'networks' && networkPlayers.length === 0 && networkProfiles.length === 0 && (
              <tr>
                <td colSpan={3} className="px-3 py-4 text-gray-500">
                  Nenhuma rede. Use Seed ou Seed redes locker.
                </td>
              </tr>
            )}
            {tab === 'networks' &&
              networkPlayers.map((n) => (
                <tr key={n.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 text-xs text-gray-500">{n.parent_group}</td>
                  <td className="px-3 py-2 font-mono text-xs">{n.code}</td>
                  <td className="px-3 py-2">
                    {n.name} · {n.country} · {n.player_role} · {n.global_tier ?? '—'} / {n.integration_status ?? '—'}
                    {n.regions?.length ? ` · ${n.regions.join(', ')}` : ''}
                  </td>
                </tr>
              ))}
            {tab === 'networks' &&
              playerCapabilities.map((c) => (
                <tr key={c.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 text-xs text-gray-500">capability</td>
                  <td className="px-3 py-2 font-mono text-xs">{c.capability_code}</td>
                  <td className="px-3 py-2">
                    {c.network_player_code} · {c.capability_name} · {c.protocol}/{c.direction}
                    {c.production_ready ? ' · PROD' : ''}
                  </td>
                </tr>
              ))}
            {tab === 'networks' &&
              playerRelations.map((r) => (
                <tr key={r.id} className="border-t dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30">
                  <td className="px-3 py-2 text-xs text-gray-500">{r.relation_type}</td>
                  <td className="px-3 py-2 font-mono text-xs">
                    {r.from_player_code} → {r.to_player_code}
                  </td>
                  <td className="px-3 py-2">força {r.strength}</td>
                </tr>
              ))}
            {tab === 'networks' &&
              networkProfiles.map((pr) => (
                <tr key={pr.id} className="border-t dark:border-slate-800 bg-violet-50/30 dark:bg-violet-950/20">
                  <td className="px-3 py-2 text-xs text-gray-500">ml_profile</td>
                  <td className="px-3 py-2 font-mono text-xs">{pr.network_player_code ?? '—'}</td>
                  <td className="px-3 py-2">
                    {pr.use_case_code ?? '—'} · telemetria {pr.telemetry_density} · PSI base {pr.drift_baseline_psi ?? '—'} ·{' '}
                    {(pr.feature_pack ?? []).join(', ')}
                  </td>
                </tr>
              ))}
            {tab === 'partners' &&
              partners.map((p) => (
                <tr key={p.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 text-xs text-gray-500">{p.partner_type}</td>
                  <td className="px-3 py-2 font-mono text-xs">{p.code}</td>
                  <td className="px-3 py-2">
                    {p.name}
                    {p.network_player_code ? ` · rede ${p.network_player_code}` : ''}
                    {p.region_code ? ` · ${p.region_code}` : ''}
                  </td>
                </tr>
              ))}
            {tab === 'models' &&
              models.map((m) => (
                <tr key={m.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 text-xs text-gray-500">model</td>
                  <td className="px-3 py-2 font-mono text-xs">{m.model_version}</td>
                  <td className="px-3 py-2">
                    {m.trained_at} · {m.status}
                  </td>
                </tr>
              ))}
            {tab === 'features' &&
              features.map((x) => {
                const row = x as { id: number; locker_id: string; feature_date: string; battery_min?: number }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">feature</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.locker_id}</td>
                    <td className="px-3 py-2">
                      {row.feature_date} · battery {row.battery_min ?? '—'}
                    </td>
                  </tr>
                )
              })}
            {tab === 'predictions' &&
              predictions.map((x) => {
                const row = x as {
                  id: number
                  locker_id: string
                  health_score: number
                  failure_probability: number
                  model_version: string
                }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">prediction</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.locker_id}</td>
                    <td className="px-3 py-2">
                      P={row.failure_probability} · H={row.health_score} · {row.model_version}
                    </td>
                  </tr>
                )
              })}
            {tab === 'feedback' &&
              feedback.map((x) => {
                const row = x as {
                  id: string
                  prediction_id?: number
                  error_pct?: number
                  model_performance_status?: string
                }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 text-xs text-gray-500">feedback</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.prediction_id ?? '—'}</td>
                    <td className="px-3 py-2">
                      erro {row.error_pct ?? '—'}% · {row.model_performance_status ?? '—'}
                    </td>
                  </tr>
                )
              })}
          </tbody>
        </table>
      )}

      {tab === 'readiness' && mlReadiness.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2">Rede</th>
              <th className="px-3 py-2">Detalhe</th>
            </tr>
          </thead>
          <tbody>
            {mlReadiness.map((row) => {
              const ext = row as MlReadinessRow & {
                score_telemetry?: number
                score_capabilities?: number
                score_ml_ops?: number
              }
              return (
                <tr key={row.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 text-xs text-gray-500">{row.readiness_band}</td>
                  <td className="px-3 py-2 font-mono text-xs">{row.network_player_code}</td>
                  <td className="px-3 py-2">
                    score {row.score_total}
                    {ext.score_telemetry != null ? ` · telemetria ${ext.score_telemetry}` : ''}
                    {ext.score_capabilities != null ? ` · caps ${ext.score_capabilities}` : ''}
                    {ext.score_ml_ops != null ? ` · ops ${ext.score_ml_ops}` : ''}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
