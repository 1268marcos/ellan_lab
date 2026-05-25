import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  privacyComplianceAdminApi,
  type PrivacyDashboard,
  type PrivacyRegulation,
} from '../../api/privacyComplianceAdmin'
import CriticalAppLayerBanner from '../../components/ops/CriticalAppLayerBanner'

type Tab =
  | 'overview'
  | 'regulations'
  | 'policies'
  | 'consents'
  | 'deletions'
  | 'subject_requests'
  | 'integrations'

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Visão geral' },
  { id: 'regulations', label: 'Marcos regulatórios' },
  { id: 'policies', label: 'Políticas' },
  { id: 'consents', label: 'Consentimentos (app layer)' },
  { id: 'deletions', label: 'Eliminação de dados' },
  { id: 'subject_requests', label: 'DSAR titulares' },
  { id: 'integrations', label: 'Webhooks e API keys' },
]

const REGULATIONS = [
  '',
  'GDPR',
  'UKGDPR',
  'LGPD',
  'CCPA',
  'VCDPA',
  'PIPEDA',
  'FADP',
  'APPI',
  'PIPA_KR',
  'PDPA_SG',
  'AU_PA',
  'POPIA',
  'PDPL_SA',
  'EPRIVACY',
  'DPDP_IN',
] as const

export default function OpsPrivacyComplianceAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = (searchParams.get('tab') as Tab) || 'overview'
  const [tab, setTab] = useState<Tab>(TABS.some((t) => t.id === initialTab) ? initialTab : 'overview')
  const [filterRegulation, setFilterRegulation] = useState('')
  const [selectedRegulationCode, setSelectedRegulationCode] = useState('GDPR')
  const [dashboard, setDashboard] = useState<PrivacyDashboard | null>(null)
  const [regulations, setRegulations] = useState<PrivacyRegulation[]>([])
  const [policies, setPolicies] = useState<unknown[]>([])
  const [consents, setConsents] = useState<unknown[]>([])
  const [deletions, setDeletions] = useState<unknown[]>([])
  const [subjectRequests, setSubjectRequests] = useState<unknown[]>([])
  const [webhooks, setWebhooks] = useState<unknown[]>([])
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const switchTab = (id: Tab) => {
    setTab(id)
    setSearchParams(id === 'overview' ? {} : { tab: id }, { replace: true })
  }

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const reg = filterRegulation || undefined
      const [d, r, p, c, del, sub, wh] = await Promise.all([
        privacyComplianceAdminApi.dashboard(),
        privacyComplianceAdminApi.listRegulations(),
        privacyComplianceAdminApi.listPolicies(),
        privacyComplianceAdminApi.listConsents(reg),
        privacyComplianceAdminApi.listDeletions(reg),
        privacyComplianceAdminApi.listSubjectRequests(reg),
        privacyComplianceAdminApi.listWebhooks(),
      ])
      setDashboard(d.data)
      setRegulations(r.data.items ?? [])
      setPolicies(p.data.items ?? [])
      setConsents(c.data.items ?? [])
      setDeletions(del.data.items ?? [])
      setSubjectRequests(sub.data.items ?? [])
      setWebhooks(wh.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [filterRegulation])

  useEffect(() => {
    load()
  }, [load])

  const onSeed = async () => {
    setLoading(true)
    try {
      const r = await privacyComplianceAdminApi.seed()
      setMessage(`Seed: ${JSON.stringify(r.data)}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    setLoading(true)
    try {
      const r = await privacyComplianceAdminApi.rotateApiKey(selectedRegulationCode)
      setLastApiKey(r.data.api_key)
      setMessage(`API key rotacionada (${r.data.key_prefix}…)`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na rotação')
    } finally {
      setLoading(false)
    }
  }

  const onSaveWebhook = async (e: FormEvent) => {
    e.preventDefault()
    if (!webhookUrl.trim()) return
    setLoading(true)
    try {
      await privacyComplianceAdminApi.upsertWebhook({
        regulation_code: selectedRegulationCode,
        url: webhookUrl.trim(),
        secret: webhookSecret || undefined,
        events: ['consent.granted', 'deletion.completed', 'dsar.completed'],
      })
      setMessage(`Webhook ${selectedRegulationCode} salvo.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ops-page">
      <header className="ops-page-header">
        <h1>Privacy Compliance — marcos globais</h1>
        <p className="muted">Consentimentos, políticas, DSAR, eliminação, webhooks e API keys.</p>
      </header>

      <div className="ops-toolbar">
        <Link to="/ops/access/security-admin?tab=critical-policies">Políticas · hub segurança</Link>
        <Link to="/ops/marketplace/admin?tab=kyc">Marketplace KYC</Link>
        <button type="button" onClick={load} disabled={loading}>
          Atualizar
        </button>
        <button type="button" onClick={onSeed} disabled={loading}>
          Seed demo
        </button>
      </div>

      {error && <p className="ops-error">{error}</p>}
      {message && <p className="ops-ok">{message}</p>}
      {lastApiKey && (
        <p className="ops-api-key">
          <strong>API key:</strong> {lastApiKey}
        </p>
      )}

      <div className="ops-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? 'active' : ''}
            onClick={() => switchTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <label>
        Marco regulatório
        <select value={filterRegulation} onChange={(e) => setFilterRegulation(e.target.value)}>
          {REGULATIONS.map((c) => (
            <option key={c || 'all'} value={c}>
              {c || 'Todos'}
            </option>
          ))}
        </select>
      </label>

      {tab === 'overview' && dashboard && (
        <div className="ops-kpi-grid">
          {[
            ['Marcos', dashboard.regulations],
            ['Políticas ativas', dashboard.active_policies],
            ['Eliminações pendentes', dashboard.pending_deletions],
            ['DSAR pendentes', dashboard.pending_subject_requests],
            ['Consentimentos ativos', dashboard.consents_granted],
            ['Webhooks ativos', dashboard.webhooks_active],
          ].map(([label, val]) => (
            <div key={String(label)} className="ops-kpi-card">
              <div className="ops-kpi-label">{label}</div>
              <div className="ops-kpi-value">{val}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'regulations' && (
        <table className="ops-table">
          <thead>
            <tr>
              <th>Código</th>
              <th>Nome</th>
              <th>Jurisdição</th>
              <th>Retenção (d)</th>
              <th>SLA (d)</th>
              <th>DPO</th>
            </tr>
          </thead>
          <tbody>
            {regulations.map((r) => (
              <tr key={r.id}>
                <td>{r.code}</td>
                <td>{r.name}</td>
                <td>{r.jurisdiction}</td>
                <td>{r.default_retention_days}</td>
                <td>{r.response_sla_days}</td>
                <td>{r.dpo_email ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === 'policies' && (
        <table className="ops-table">
          <thead>
            <tr>
              <th>Versão</th>
              <th>Título</th>
              <th>Vigência</th>
            </tr>
          </thead>
          <tbody>
            {(policies as Array<{ id: string; version: string; title: string; effective_at?: string }>).map(
              (p) => (
                <tr key={p.id}>
                  <td>{p.version}</td>
                  <td>{p.title}</td>
                  <td>{p.effective_at?.slice(0, 10) ?? '—'}</td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      )}

      {tab === 'consents' && (
        <>
          <CriticalAppLayerBanner tables="privacy_consents" />
          <table className="ops-table">
            <thead>
              <tr>
                <th>Marco</th>
                <th>Tipo</th>
                <th>Titular</th>
                <th>Concedido</th>
                <th>Serviço</th>
                <th>Política v</th>
              </tr>
            </thead>
            <tbody>
              {(
                consents as Array<{
                  id: string
                  regulation_code: string
                  consent_type: string
                  user_id?: string
                  granted: boolean
                  revoked_at?: string
                  recorded_by_service?: string
                  access_policy_version?: number
                }>
              ).map((c) => (
                <tr key={c.id}>
                  <td>{c.regulation_code}</td>
                  <td>{c.consent_type}</td>
                  <td>{c.user_id ?? '—'}</td>
                  <td>{c.granted && !c.revoked_at ? 'Sim' : 'Não'}</td>
                  <td className="font-mono text-xs">{c.recorded_by_service ?? '—'}</td>
                  <td>{c.access_policy_version ?? 1}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {tab === 'deletions' && (
        <table className="ops-table">
          <thead>
            <tr>
              <th>Marco</th>
              <th>user_id</th>
              <th>Status</th>
              <th>Motivo</th>
            </tr>
          </thead>
          <tbody>
            {(deletions as Array<{ id: string; regulation_code: string; user_id?: string; status: string; reason?: string }>).map(
              (d) => (
                <tr key={d.id}>
                  <td>{d.regulation_code}</td>
                  <td>{d.user_id ?? '—'}</td>
                  <td>{d.status}</td>
                  <td>{d.reason ?? '—'}</td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      )}

      {tab === 'subject_requests' && (
        <table className="ops-table">
          <thead>
            <tr>
              <th>Marco</th>
              <th>Tipo</th>
              <th>Status</th>
              <th>Prazo</th>
            </tr>
          </thead>
          <tbody>
            {(subjectRequests as Array<{ id: string; regulation_code: string; request_type: string; status: string; due_at?: string }>).map(
              (s) => (
                <tr key={s.id}>
                  <td>{s.regulation_code}</td>
                  <td>{s.request_type}</td>
                  <td>{s.status}</td>
                  <td>{s.due_at?.slice(0, 10) ?? '—'}</td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      )}

      {tab === 'integrations' && (
        <form onSubmit={onSaveWebhook} className="ops-form">
          <select
            value={selectedRegulationCode}
            onChange={(e) => setSelectedRegulationCode(e.target.value)}
          >
            {REGULATIONS.filter(Boolean).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <input
            placeholder="URL webhook"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
          />
          <input
            placeholder="secret"
            value={webhookSecret}
            onChange={(e) => setWebhookSecret(e.target.value)}
          />
          <button type="submit" disabled={loading}>
            Salvar webhook
          </button>
          <button type="button" onClick={onRotateKey} disabled={loading}>
            Rotacionar API key
          </button>
        </form>
      )}

      {loading && <p className="muted">Carregando…</p>}
    </div>
  )
}
