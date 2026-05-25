import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  EmptyState,
  OpsErrorBanner,
  OpsSuccessBanner,
  OpsWorkspaceCard,
  StatusPill,
  formatMoney,
  formatShortIso,
  BTN_GHOST,
  BTN_PRIMARY,
  BTN_SHORTCUT,
} from '../../components/ops/OpsMarketingUi'
import {
  orderPickupPromotionsApi,
  type Promotion,
  type PromotionExclusion,
} from '../../api/orderPickupPromotions'

const PROMO_TYPES = ['PERCENT_OFF', 'FIXED_OFF', 'BUY_X_GET_Y', 'FREE_ITEM', 'BUNDLE_DISCOUNT'] as const
const FEATURED_LOCKER_PLAYERS = [
  'INPOST',
  'DHL',
  'MAGALU',
  'MERCADO_LIVRE',
  'AMAZON',
  'DPD',
  'CORREIOS',
  'CTT',
  'WORTEN',
  'EL_CORTE_INGLES',
] as const
const SCOPE_TYPES = ['PLAYER', 'COUNTRY', 'CHANNEL', 'PARTNER', 'MARKETPLACE', 'LOCKER_OPERATOR', 'REGION'] as const

function toLocalInputValue(date: Date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d}T${hh}:${mm}`
}

function toIsoOrNull(localDateTimeValue: string) {
  const raw = String(localDateTimeValue || '').trim()
  if (!raw) return null
  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed.toISOString()
}

type Props = { embedded?: boolean }

export default function OpsPromotions({ embedded = false }: Props) {
  const [codeFilter, setCodeFilter] = useState('')
  const [isActiveFilter, setIsActiveFilter] = useState('')
  const [typeLocalFilter, setTypeLocalFilter] = useState('')
  const [limit, setLimit] = useState(25)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [items, setItems] = useState<Promotion[]>([])
  const [total, setTotal] = useState(0)
  const [listLoaded, setListLoaded] = useState(false)
  const [patchingId, setPatchingId] = useState('')
  const [cloningId, setCloningId] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [formCode, setFormCode] = useState('')
  const [formName, setFormName] = useState('')
  const [formType, setFormType] = useState<(typeof PROMO_TYPES)[number]>('PERCENT_OFF')
  const [formDiscountPct, setFormDiscountPct] = useState('10')
  const [formDiscountCents, setFormDiscountCents] = useState('')
  const [formMinOrderCents, setFormMinOrderCents] = useState('0')
  const [formValidFrom, setFormValidFrom] = useState(() => toLocalInputValue(new Date()))
  const [formValidUntil, setFormValidUntil] = useState('')
  const [formConditionsJson, setFormConditionsJson] = useState('{}')
  const [selected, setSelected] = useState<Promotion | null>(null)
  const [exclusions, setExclusions] = useState<PromotionExclusion[]>([])
  const [exclusionTotal, setExclusionTotal] = useState(0)
  const [exclusionProductId, setExclusionProductId] = useState('')
  const [exclusionsLoading, setExclusionsLoading] = useState(false)
  const [scopes, setScopes] = useState<import('../../api/orderPickupPromotions').PromotionScope[]>([])
  const [scopesError, setScopesError] = useState<string | null>(null)
  const [scopeType, setScopeType] = useState('PLAYER')
  const [scopeValue, setScopeValue] = useState('')
  const [scopeBusy, setScopeBusy] = useState(false)
  const [playerCatalog, setPlayerCatalog] = useState<import('../../api/orderPickupPromotions').LockerPlayerRef[]>([])

  const loadPlayerCatalog = useCallback(async () => {
    try {
      const { data } = await orderPickupPromotionsApi.lockerPlayersCatalog()
      setPlayerCatalog(data.items ?? [])
    } catch {
      setPlayerCatalog([])
    }
  }, [])

  const loadList = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, unknown> = { limit, offset }
      const c = codeFilter.trim()
      if (c) params.code = c
      if (isActiveFilter === 'true') params.is_active = true
      if (isActiveFilter === 'false') params.is_active = false
      const { data } = await orderPickupPromotionsApi.list(params)
      setItems(data.items ?? [])
      setTotal(data.total ?? 0)
      setListLoaded(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao listar promoções')
      setItems([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [codeFilter, isActiveFilter, limit, offset])

  useEffect(() => {
    if (embedded) void loadList()
  }, [embedded]) // eslint-disable-line react-hooks/exhaustive-deps -- carga inicial na aba Promoções

  useEffect(() => {
    void loadPlayerCatalog()
  }, [loadPlayerCatalog])

  const loadExclusions = useCallback(async (promotionId: string) => {
    setExclusionsLoading(true)
    setError(null)
    try {
      const { data } = await orderPickupPromotionsApi.listExclusions(promotionId)
      setExclusions(data.items ?? [])
      setExclusionTotal(data.total ?? 0)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar exclusões')
      setExclusions([])
      setExclusionTotal(0)
    } finally {
      setExclusionsLoading(false)
    }
  }, [])

  const loadScopes = useCallback(async (promotionId: string) => {
    setScopesError(null)
    try {
      const { data } = await orderPickupPromotionsApi.listScopes(promotionId)
      setScopes(data.items ?? [])
    } catch (err: unknown) {
      setScopes([])
      setScopesError(err instanceof Error ? err.message : 'Falha ao carregar escopos')
    }
  }, [])

  useEffect(() => {
    if (!selected?.id) {
      setExclusions([])
      setExclusionTotal(0)
      setScopes([])
      setScopesError(null)
      return
    }
    void loadExclusions(selected.id)
    void loadScopes(selected.id)
  }, [selected?.id, loadExclusions, loadScopes])

  const displayedItems = useMemo(() => {
    const needle = typeLocalFilter.trim().toUpperCase()
    if (!needle) return items
    return items.filter((row) => String(row.type || '').toUpperCase() === needle)
  }, [items, typeLocalFilter])

  const onSeed = async () => {
    setLoading(true)
    setMessage(null)
    setError(null)
    try {
      const { data } = await orderPickupPromotionsApi.seedWorld()
      setMessage(
        `Seed mundial: ${data.promotions_inserted} promoções, ${data.scopes_inserted} escopos, ${data.campaigns_inserted} campanhas.`,
      )
      setOffset(0)
      await loadList()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    let conditionsJson: Record<string, unknown> = {}
    try {
      conditionsJson = JSON.parse(formConditionsJson.trim() || '{}') as Record<string, unknown>
      if (conditionsJson === null || Array.isArray(conditionsJson)) {
        throw new Error('conditions_json deve ser um objeto JSON.')
      }
    } catch (err: unknown) {
      setLoading(false)
      setError(err instanceof Error ? err.message : 'JSON inválido')
      return
    }
    const validFromIso = toIsoOrNull(formValidFrom)
    if (!validFromIso) {
      setLoading(false)
      setError('Informe valid_from válido.')
      return
    }
    const body: Record<string, unknown> = {
      code: formCode.trim() || null,
      name: formName.trim(),
      type: formType,
      min_order_cents: Math.max(0, Number(formMinOrderCents) || 0),
      conditions_json: conditionsJson,
      valid_from: validFromIso,
    }
    if (!body.name) {
      setLoading(false)
      setError('Nome é obrigatório.')
      return
    }
    if (formDiscountPct.trim() !== '') body.discount_pct = Number(formDiscountPct)
    if (formDiscountCents.trim() !== '') body.discount_cents = Math.max(0, Number(formDiscountCents))
    const vu = toIsoOrNull(formValidUntil)
    if (vu) body.valid_until = vu
    try {
      await orderPickupPromotionsApi.create(body)
      setMessage('Promoção criada.')
      setShowCreate(false)
      setFormName('')
      setFormCode('')
      setOffset(0)
      await loadList()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar')
    } finally {
      setLoading(false)
    }
  }

  const onPatchStatus = async (promotionId: string, nextActive: boolean) => {
    setPatchingId(promotionId)
    setError(null)
    try {
      await orderPickupPromotionsApi.patchStatus(promotionId, {
        is_active: nextActive,
        reason: 'OpsPromotions v1',
      })
      await loadList()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar status')
    } finally {
      setPatchingId('')
    }
  }

  const onClone = async (row: Promotion) => {
    const ref = String(row.id || row.code || '').trim()
    if (!ref) {
      setError('Promoção sem id/código — recarregue a lista.')
      return
    }
    const base = String(row.code || row.id)
      .trim()
      .toUpperCase()
      .replace(/-COPY\d*$/i, '')
    const suggested = `${base}-COPY`
    const newCode = window.prompt('Código da cópia:', suggested)?.trim().toUpperCase()
    if (!newCode) return
    setCloningId(row.id || ref)
    setError(null)
    setMessage(null)
    try {
      const { data } = await orderPickupPromotionsApi.clone(ref, {
        new_code: newCode,
        new_name: row.name ? `${row.name} (cópia)` : undefined,
      })
      setMessage(`Promoção clonada: ${data.promotion_code}`)
      setOffset(0)
      await loadList()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao clonar')
    } finally {
      setCloningId('')
    }
  }

  const onAddExclusion = async (e: FormEvent) => {
    e.preventDefault()
    if (!selected?.id) return
    const productId = exclusionProductId.trim()
    if (!productId) {
      setError('Informe product_id (SKU).')
      return
    }
    setLoading(true)
    try {
      await orderPickupPromotionsApi.addExclusion(selected.id, productId)
      setExclusionProductId('')
      await loadExclusions(selected.id)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao adicionar exclusão')
    } finally {
      setLoading(false)
    }
  }

  const onRemoveExclusion = async (productId: string) => {
    if (!selected?.id) return
    setLoading(true)
    try {
      await orderPickupPromotionsApi.removeExclusion(selected.id, productId)
      await loadExclusions(selected.id)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao remover exclusão')
    } finally {
      setLoading(false)
    }
  }

  const onAddScope = async (e: FormEvent) => {
    e.preventDefault()
    if (!selected?.id || !scopeValue.trim()) {
      setScopesError('Informe scope_value (ex.: INPOST, MAGALU, BR).')
      return
    }
    setScopeBusy(true)
    setScopesError(null)
    try {
      await orderPickupPromotionsApi.addScope(selected.id, {
        scope_type: scopeType,
        scope_value: scopeValue.trim(),
      })
      setScopeValue('')
      await loadScopes(selected.id)
    } catch (err: unknown) {
      setScopesError(err instanceof Error ? err.message : 'Falha ao adicionar escopo')
    } finally {
      setScopeBusy(false)
    }
  }

  const onRemoveScope = async (scopeId: string) => {
    if (!selected?.id) return
    setScopeBusy(true)
    try {
      await orderPickupPromotionsApi.removeScope(selected.id, scopeId)
      await loadScopes(selected.id)
    } catch (err: unknown) {
      setScopesError(err instanceof Error ? err.message : 'Falha ao remover escopo')
    } finally {
      setScopeBusy(false)
    }
  }

  const inputCls = 'ellan-field'
  const labelCls = 'grid gap-1 text-xs text-slate-400'

  const content = (
    <div className={embedded ? 'space-y-4' : 'mx-auto max-w-6xl space-y-5'}>
      {!embedded ? (
        <>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Marketing / Promoções</h1>
              <p className="text-sm text-gray-500 dark:text-slate-400">
                Domínio <code className="text-xs">promotions</code>, escopos e exclusões de SKU.
              </p>
            </div>
            <Link to="/ops/products/admin?tab=fiscal" className={BTN_SHORTCUT}>
              Pricing & fiscal hub
            </Link>
          </div>
        </>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <button type="button" className={BTN_GHOST} onClick={() => void loadList()} disabled={loading}>
          {loading ? 'Atualizando…' : embedded ? 'Atualizar lista' : 'Listar'}
        </button>
        {!embedded ? (
          <button type="button" className={BTN_GHOST} onClick={() => void onSeed()} disabled={loading}>
            Seed mundial
          </button>
        ) : null}
        <button type="button" className={BTN_PRIMARY} onClick={() => setShowCreate((v) => !v)}>
          {showCreate ? 'Fechar formulário' : 'Nova promoção'}
        </button>
      </div>

      {message ? <OpsSuccessBanner>{message}</OpsSuccessBanner> : null}
      {error ? <OpsErrorBanner>{error}</OpsErrorBanner> : null}

      <OpsWorkspaceCard title="Filtros" hint="Parâmetros enviados ao servidor; tipo é filtrado localmente na página atual.">
        <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-4">
          <label className={labelCls}>
            Código (exato)
            <input className={inputCls} value={codeFilter} onChange={(e) => setCodeFilter(e.target.value)} placeholder="PR3-PROMO-001" />
          </label>
          <label className={labelCls}>
            Ativa
            <select className={inputCls} value={isActiveFilter} onChange={(e) => setIsActiveFilter(e.target.value)}>
              <option value="">Todas</option>
              <option value="true">Sim</option>
              <option value="false">Não</option>
            </select>
          </label>
          <label className={labelCls}>
            Tipo (local)
            <select className={inputCls} value={typeLocalFilter} onChange={(e) => setTypeLocalFilter(e.target.value)}>
              <option value="">Todos</option>
              {PROMO_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className={labelCls}>
            Limite
            <input
              type="number"
              min={1}
              max={500}
              className={inputCls}
              value={limit}
              onChange={(e) => setLimit(Math.max(1, Math.min(500, Number(e.target.value) || 25)))}
            />
          </label>
        </div>
      </OpsWorkspaceCard>

      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <button
          type="button"
          className={BTN_GHOST}
          disabled={offset <= 0 || loading}
          onClick={() => setOffset((o) => Math.max(0, o - limit))}
        >
          Página anterior
        </button>
        <button
          type="button"
          className={BTN_GHOST}
          disabled={offset + limit >= total || loading}
          onClick={() => setOffset((o) => o + limit)}
        >
          Próxima página
        </button>
        <span>
          offset={offset} · total={total}
          {typeLocalFilter ? ` · exibindo ${displayedItems.length}` : ''}
        </span>
      </div>

      {showCreate && (
        <form onSubmit={onCreate} className="grid gap-3 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2">
          <input className={inputCls} placeholder="Código" value={formCode} onChange={(e) => setFormCode(e.target.value)} />
          <input className={inputCls} placeholder="Nome *" required value={formName} onChange={(e) => setFormName(e.target.value)} />
          <select className={inputCls} value={formType} onChange={(e) => setFormType(e.target.value as (typeof PROMO_TYPES)[number])}>
            {PROMO_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <input className={inputCls} placeholder="discount_pct" value={formDiscountPct} onChange={(e) => setFormDiscountPct(e.target.value)} />
          <input className={inputCls} placeholder="discount_cents" value={formDiscountCents} onChange={(e) => setFormDiscountCents(e.target.value)} />
          <input className={inputCls} placeholder="min_order_cents" value={formMinOrderCents} onChange={(e) => setFormMinOrderCents(e.target.value)} />
          <input type="datetime-local" className={inputCls} value={formValidFrom} onChange={(e) => setFormValidFrom(e.target.value)} />
          <input type="datetime-local" className={inputCls} value={formValidUntil} onChange={(e) => setFormValidUntil(e.target.value)} />
          <textarea
            className={`${inputCls} font-mono md:col-span-2`}
            rows={3}
            value={formConditionsJson}
            onChange={(e) => setFormConditionsJson(e.target.value)}
          />
          <button type="submit" className={`${BTN_PRIMARY} md:col-span-2`} disabled={loading}>
            Criar promoção
          </button>
        </form>
      )}

      {!listLoaded && !loading && !embedded ? (
        <EmptyState>Clique em <strong>Listar</strong> ou use <strong>Seed mundial</strong> para carregar o catálogo.</EmptyState>
      ) : !displayedItems.length && listLoaded && !loading ? (
        <EmptyState>Nenhuma promoção para os filtros atuais. Ajuste código, status ou tipo.</EmptyState>
      ) : displayedItems.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border dark:border-slate-700">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-800/80 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-3 py-2">Selecionar</th>
                <th className="px-3 py-2">Código</th>
                <th className="px-3 py-2">Tipo</th>
                <th className="px-3 py-2">% / valor</th>
                <th className="px-3 py-2">Válida de</th>
                <th className="px-3 py-2">Até</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Nome</th>
                <th className="px-3 py-2">Ações</th>
              </tr>
            </thead>
            <tbody>
              {displayedItems.map((row) => (
                <tr
                  key={row.id}
                  className={`border-t dark:border-slate-700 ${selected?.id === row.id ? 'bg-indigo-50 dark:bg-indigo-950/40' : ''}`}
                >
                  <td className="px-3 py-2">
                    <button
                      type="button"
                      className="rounded border px-2 py-0.5 text-xs dark:border-slate-600"
                      onClick={() => setSelected((cur) => (cur?.id === row.id ? null : row))}
                    >
                      {selected?.id === row.id ? 'Selecionada' : 'Selecionar'}
                    </button>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">{row.code || '—'}</td>
                  <td className="px-3 py-2">{row.type}</td>
                  <td className="px-3 py-2">
                    {row.discount_pct != null
                      ? `${row.discount_pct}%`
                      : row.discount_cents != null
                        ? formatMoney(row.discount_cents)
                        : '—'}
                  </td>
                  <td className="px-3 py-2">{formatShortIso(row.valid_from)}</td>
                  <td className="px-3 py-2">{row.valid_until ? formatShortIso(row.valid_until) : '—'}</td>
                  <td className="px-3 py-2">
                    <StatusPill active={row.is_active} />
                  </td>
                  <td className="px-3 py-2">{row.name}</td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      <button
                        type="button"
                        className="rounded border px-2 py-0.5 text-xs dark:border-slate-600"
                        disabled={patchingId === row.id || cloningId === row.id}
                        onClick={() => void onPatchStatus(row.id, !row.is_active)}
                      >
                        {patchingId === row.id ? '…' : row.is_active ? 'Desativar' : 'Ativar'}
                      </button>
                      <button
                        type="button"
                        className="rounded border border-indigo-500/50 px-2 py-0.5 text-xs text-indigo-200"
                        disabled={cloningId === row.id || patchingId === row.id}
                        onClick={() => void onClone(row)}
                        title="Duplica promoção, escopos e exclusões"
                      >
                        {cloningId === row.id ? '…' : 'Clonar'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : embedded && loading ? (
        <p className="text-sm text-slate-500">Carregando catálogo…</p>
      ) : null}

      {embedded && listLoaded && displayedItems.length > 0 && !selected ? (
        <p className="text-xs text-slate-500">Selecione uma linha na tabela para configurar escopos e exclusões.</p>
      ) : null}

      {selected && (
        <section className="rounded-xl border border-blue-500/40 bg-slate-900/25 p-4 dark:border-blue-500/50">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="text-base font-semibold text-slate-100">Configuração da promoção</h2>
              <p className="mt-1 text-xs text-slate-400">
                <code className="font-mono">{selected.code || selected.id}</code> — {selected.name}
              </p>
            </div>
            <button type="button" className={BTN_GHOST} onClick={() => setSelected(null)}>
              Fechar painel
            </button>
          </div>

          <h3 className="mt-4 text-sm font-medium text-slate-300">Exclusões de SKU</h3>
          <p className="text-xs text-slate-500">
            Total: {exclusionTotal}
            {exclusionsLoading ? ' (carregando…)' : ''}
          </p>
          <form onSubmit={onAddExclusion} className="mt-2 flex flex-wrap gap-2">
            <input
              className={`min-w-[200px] flex-1 ${inputCls}`}
              placeholder="product_id (SKU)"
              value={exclusionProductId}
              onChange={(e) => setExclusionProductId(e.target.value)}
            />
            <button type="submit" className={BTN_PRIMARY}>
              Adicionar exclusão
            </button>
            <button type="button" className={BTN_GHOST} onClick={() => void loadExclusions(selected.id)}>
              Atualizar
            </button>
          </form>
          {exclusions.length > 0 ? (
            <ul className="mt-3 space-y-1 text-sm">
              {exclusions.map((ex) => (
                <li key={ex.product_id} className="flex items-center justify-between gap-2 rounded border px-2 py-1 dark:border-slate-700">
                  <code className="text-xs">{ex.product_id}</code>
                  <button type="button" className="text-xs text-red-400 hover:text-red-300" onClick={() => void onRemoveExclusion(ex.product_id)}>
                    Remover
                  </button>
                </li>
              ))}
            </ul>
          ) : !exclusionsLoading ? (
            <p className="mt-2 text-xs text-slate-500">Nenhum SKU excluído — todos elegíveis dentro do escopo.</p>
          ) : null}

          <div className="mt-6 border-t border-slate-700/60 pt-4">
            <h3 className="text-sm font-medium text-slate-300">Escopos (player, país, marketplace…)</h3>
            <p className="text-xs text-slate-500">
              Catálogo mundial locker
              {playerCatalog.length ? ` — ${playerCatalog.length} players` : ''}
            </p>
            <div className="mt-2 flex flex-wrap gap-1">
              {FEATURED_LOCKER_PLAYERS.map((code) => (
                <button
                  key={code}
                  type="button"
                  className="rounded border border-slate-600 px-2 py-0.5 text-[11px] text-slate-300"
                  onClick={() => {
                    setScopeType('PLAYER')
                    setScopeValue(code)
                  }}
                >
                  {code}
                </button>
              ))}
            </div>
            {scopesError ? <div className="mt-2"><OpsErrorBanner>{scopesError}</OpsErrorBanner></div> : null}
            <form onSubmit={onAddScope} className="mt-2 flex flex-wrap gap-2">
              <select className={inputCls} value={scopeType} onChange={(e) => setScopeType(e.target.value)}>
                {SCOPE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <input
                className={`min-w-[140px] flex-1 ${inputCls}`}
                list="locker-players-datalist-v1"
                placeholder="INPOST, CORREIOS, MERCADO_LIVRE…"
                value={scopeValue}
                onChange={(e) => setScopeValue(e.target.value)}
              />
              <datalist id="locker-players-datalist-v1">
                {playerCatalog.map((p) => (
                  <option key={p.code} value={p.code}>
                    {p.display_name}
                  </option>
                ))}
              </datalist>
              <button type="submit" className={BTN_PRIMARY} disabled={scopeBusy}>
                Adicionar escopo
              </button>
            </form>
            {scopes.length > 0 ? (
              <table className="mt-3 min-w-full text-left text-sm">
                <thead className="text-xs uppercase text-slate-500">
                  <tr>
                    <th className="py-1 pr-3">Tipo</th>
                    <th className="py-1 pr-3">Valor</th>
                    <th className="py-1 pr-3">Modo</th>
                    <th className="py-1">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {scopes.map((sc) => (
                    <tr key={sc.id} className="border-t dark:border-slate-800">
                      <td className="py-1 pr-3">{sc.scope_type}</td>
                      <td className="py-1 pr-3">{sc.scope_value}</td>
                      <td className="py-1 pr-3">{sc.mode}</td>
                      <td className="py-1">
                        <button type="button" className="text-xs text-red-400" disabled={scopeBusy} onClick={() => void onRemoveScope(sc.id)}>
                          Remover
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="mt-2 text-xs text-slate-500">Sem escopo INCLUDE — elegível globalmente (salvo regras do motor).</p>
            )}
          </div>
        </section>
      )}
    </div>
  )

  return content
}
