import { FormEvent, useCallback, useState } from 'react'
import { tenantAdminApi, type CustomDomain, type Tenant, type TenantPartnerLink } from '../../api/tenantAdmin'
import { partnerAdminApi } from '../../api/partnerAdmin'

type Tab = 'tenants' | 'domains' | 'links'

export default function OpsTenantsAdmin() {
  const [tab, setTab] = useState<Tab>('tenants')
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [domains, setDomains] = useState<CustomDomain[]>([])
  const [links, setLinks] = useState<TenantPartnerLink[]>([])
  const [ecPartners, setEcPartners] = useState<{ id: string; code: string }[]>([])
  const [selectedTenant, setSelectedTenant] = useState('')
  const [tenantForm, setTenantForm] = useState({
    tenant_id: '',
    cnpj: '',
    razao_social: '',
    regime: 'SIMPLES',
    crt: '1',
  })
  const [domainInput, setDomainInput] = useState('')
  const [linkPartnerId, setLinkPartnerId] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadAssociations = useCallback(async (tenantId: string) => {
    if (!tenantId) {
      setDomains([])
      setLinks([])
      return
    }
    const [d, l] = await Promise.all([
      tenantAdminApi.listDomains(tenantId),
      tenantAdminApi.listPartnerLinks(tenantId),
    ])
    setDomains(d.data.domains ?? [])
    setLinks(l.data.links ?? [])
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [t, ec] = await Promise.all([
        tenantAdminApi.listTenants(),
        partnerAdminApi.listEcommerce(),
      ])
      const list = t.data.tenants ?? []
      setTenants(list)
      setEcPartners((ec.data.partners ?? []).map((p) => ({ id: p.id, code: p.code })))
      const tid = selectedTenant || list[0]?.tenant_id || ''
      if (tid && !selectedTenant) setSelectedTenant(tid)
      await loadAssociations(tid || selectedTenant)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [selectedTenant, loadAssociations])

  const onSeed = async () => {
    setLoading(true)
    try {
      await tenantAdminApi.seed()
      setMessage('Seed aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreateTenant = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await tenantAdminApi.createTenant(tenantForm)
      setMessage(`Tenant ${data.tenant_id} criado.`)
      setSelectedTenant(data.tenant_id)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar tenant')
    } finally {
      setLoading(false)
    }
  }

  const onAddDomain = async () => {
    if (!selectedTenant || !domainInput) return
    setLoading(true)
    try {
      await tenantAdminApi.addDomain(selectedTenant, { domain: domainInput })
      setMessage('Domínio adicionado.')
      setDomainInput('')
      await loadAssociations(selectedTenant)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao adicionar domínio')
    } finally {
      setLoading(false)
    }
  }

  const onAddLink = async () => {
    if (!selectedTenant || !linkPartnerId) return
    setLoading(true)
    try {
      await tenantAdminApi.addPartnerLink(selectedTenant, {
        partner_id: linkPartnerId,
        partner_type: 'ECOMMERCE',
        is_default: true,
      })
      setMessage('Vínculo criado.')
      await loadAssociations(selectedTenant)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao vincular')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Tenants</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            `tenant_fiscal_config`, domínios white label e vínculos com parceiros.
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSeed()} className="ellan-btn-outline">
            Seed
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

      <div className="flex gap-2">
        {(['tenants', 'domains', 'links'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'border border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700'}`}
          >
            {t === 'tenants' ? 'Tenants' : t === 'domains' ? 'Domínios' : 'Parceiros'}
          </button>
        ))}
      </div>

      <select
        className="ellan-field"
        value={selectedTenant}
        onChange={(e) => {
          setSelectedTenant(e.target.value)
          void loadAssociations(e.target.value)
        }}
      >
        <option value="">Tenant</option>
        {tenants.map((t) => (
          <option key={t.tenant_id} value={t.tenant_id}>
            {t.tenant_id} — {t.razao_social}
          </option>
        ))}
      </select>

      {tab === 'tenants' && (
        <form onSubmit={onCreateTenant} className="grid gap-3 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2">
          <input className="ellan-field" placeholder="tenant_id" required value={tenantForm.tenant_id} onChange={(e) => setTenantForm((f) => ({ ...f, tenant_id: e.target.value }))} />
          <input className="ellan-field" placeholder="CNPJ" required value={tenantForm.cnpj} onChange={(e) => setTenantForm((f) => ({ ...f, cnpj: e.target.value }))} />
          <input className="ellan-field md:col-span-2" placeholder="Razão social" required value={tenantForm.razao_social} onChange={(e) => setTenantForm((f) => ({ ...f, razao_social: e.target.value }))} />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-2">
            Criar tenant
          </button>
        </form>
      )}

      {tab === 'domains' && (
        <div className="flex flex-wrap gap-2">
          <input className="ellan-field" placeholder="domínio" value={domainInput} onChange={(e) => setDomainInput(e.target.value)} />
          <button type="button" onClick={() => void onAddDomain()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
            Adicionar
          </button>
        </div>
      )}

      {tab === 'links' && (
        <div className="flex flex-wrap gap-2">
          <select className="ellan-field" value={linkPartnerId} onChange={(e) => setLinkPartnerId(e.target.value)}>
            <option value="">Parceiro e-commerce</option>
            {ecPartners.map((p) => (
              <option key={p.id} value={p.id}>
                {p.code}
              </option>
            ))}
          </select>
          <button type="button" onClick={() => void onAddLink()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
            Vincular
          </button>
        </div>
      )}

      <table className="w-full text-left text-sm">
        <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
          <tr>
            <th className="px-3 py-2">Tipo</th>
            <th className="px-3 py-2">ID</th>
            <th className="px-3 py-2">Detalhe</th>
          </tr>
        </thead>
        <tbody>
          {tab === 'tenants' &&
            tenants.map((t) => (
              <tr key={t.tenant_id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2">tenant</td>
                <td className="px-3 py-2 font-mono text-xs">{t.tenant_id}</td>
                <td className="px-3 py-2">{t.razao_social}</td>
              </tr>
            ))}
          {tab === 'domains' &&
            domains.map((d) => (
              <tr key={d.id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2">domain</td>
                <td className="px-3 py-2 font-mono text-xs">{d.domain}</td>
                <td className="px-3 py-2">{d.verified ? 'verificado' : 'pendente'}</td>
              </tr>
            ))}
          {tab === 'links' &&
            links.map((l) => (
              <tr key={l.id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2">{l.partner_type}</td>
                <td className="px-3 py-2 font-mono text-xs">{l.partner_id}</td>
                <td className="px-3 py-2">{l.is_default ? 'default' : ''}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  )
}
