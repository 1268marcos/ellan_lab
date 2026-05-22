import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import OpsPromotions from './OpsPromotions'
import OpsPromotionsLabPage from './OpsPromotionsLabPage'
import {
  EmptyState,
  KpiCard,
  OpsErrorBanner,
  OpsInfoBanner,
  OpsSuccessBanner,
  OpsWorkspaceCard,
  StatusPill,
  TabButton,
  formatMoney,
  formatShortIso,
  BTN_GHOST,
  BTN_PRIMARY,
  BTN_SHORTCUT,
} from '../../components/ops/OpsMarketingUi'
import {
  orderPickupPromotionsApi,
  type PromotionCampaign,
  type PromotionOverview,
  type PromotionRedemption,
} from '../../api/orderPickupPromotions'

const TABS = ['overview', 'campaigns', 'promotions', 'redemptions', 'lab'] as const
type TabId = (typeof TABS)[number]

const TAB_META: Record<TabId, { label: string; hint: string }> = {
  overview: {
    label: 'Visão geral',
    hint: 'KPIs de campanhas, promoções ativas e volume de resgates (24h e total).',
  },
  campaigns: {
    label: 'Campanhas',
    hint: 'Agrupe promoções por marketplace, carrier, rede locker ou agregador (Magalu, InPost, DHL…).',
  },
  promotions: {
    label: 'Promoções',
    hint: 'Selecione uma linha para configurar escopos mundiais, exclusões de SKU e status.',
  },
  redemptions: {
    label: 'Resgates',
    hint: 'Trilha de validações com desconto aplicado por pedido e player.',
  },
  lab: {
    label: 'Laboratório',
    hint: 'Simular, match elegíveis, conflitos de escopo e matriz player (dry-run).',
  },
}

const CHANNEL_FAMILIES = ['GENERAL', 'MARKETPLACE', 'LOCKER_NETWORK', 'CARRIER', 'AGGREGATOR', 'PUDO'] as const

export default function OpsPromotionsAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const rawTab = searchParams.get('tab')
  const tab: TabId = TABS.includes(rawTab as TabId) ? (rawTab as TabId) : 'overview'
  const setTab = (t: TabId) => {
    setError(null)
    setSearchParams({ tab: t }, { replace: true })
  }

  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [overview, setOverview] = useState<PromotionOverview | null>(null)
  const [campaigns, setCampaigns] = useState<PromotionCampaign[]>([])
  const [redemptions, setRedemptions] = useState<PromotionRedemption[]>([])
  const [campForm, setCampForm] = useState({
    code: '',
    name: '',
    channel_family: 'MARKETPLACE' as string,
    primary_country: 'BR',
  })

  const loadOverview = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await orderPickupPromotionsApi.overview()
      setOverview(data)
    } catch (err: unknown) {
      setOverview(null)
      setError(err instanceof Error ? err.message : 'Falha no overview')
    } finally {
      setLoading(false)
    }
  }, [])

  const loadCampaigns = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await orderPickupPromotionsApi.listCampaigns({ limit: 100 })
      setCampaigns(data.items ?? [])
    } catch (err: unknown) {
      setCampaigns([])
      setError(err instanceof Error ? err.message : 'Falha nas campanhas')
    } finally {
      setLoading(false)
    }
  }, [])

  const loadRedemptions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await orderPickupPromotionsApi.listRedemptions({ limit: 50 })
      setRedemptions(data.items ?? [])
    } catch (err: unknown) {
      setRedemptions([])
      setError(err instanceof Error ? err.message : 'Falha nos resgates')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'overview') void loadOverview()
    if (tab === 'campaigns') void loadCampaigns()
    if (tab === 'redemptions') void loadRedemptions()
  }, [tab, loadOverview, loadCampaigns, loadRedemptions])

  const refreshTab = () => {
    if (tab === 'overview') void loadOverview()
    if (tab === 'campaigns') void loadCampaigns()
    if (tab === 'redemptions') void loadRedemptions()
  }

  const onSeedWorld = async () => {
    setLoading(true)
    setMessage(null)
    setError(null)
    try {
      const { data } = await orderPickupPromotionsApi.seedWorld()
      setMessage(
        `Seed mundial: ${data.campaigns_inserted} campanhas, ${data.promotions_inserted} promoções, ${data.scopes_inserted} escopos.`,
      )
      await loadOverview()
      if (tab === 'campaigns') await loadCampaigns()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreateCampaign = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await orderPickupPromotionsApi.createCampaign({
        ...campForm,
        valid_from: new Date().toISOString(),
      })
      setMessage('Campanha criada com sucesso.')
      setCampForm({ code: '', name: '', channel_family: 'MARKETPLACE', primary_country: 'BR' })
      await loadCampaigns()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar campanha')
    } finally {
      setLoading(false)
    }
  }

  const meta = TAB_META[tab]

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div className="flex flex-wrap justify-end gap-2">
        <Link to="/ops/products/admin?tab=fiscal" className={BTN_SHORTCUT}>
          Pricing hub
        </Link>
        <Link to="/ops/products/admin?tab=bundles" className={BTN_SHORTCUT}>
          Bundles
        </Link>
        <Link to="/ops/partners/admin" className={BTN_SHORTCUT}>
          Parceiros
        </Link>
      </div>

      <header>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Marketing / Promoções</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">
          Hub mundial: campanhas, escopos por player/país (InPost, DHL, Magalu, Mercado Livre…), promoções e resgates.
          Escrita via API com perfil <code className="text-xs text-slate-300">admin_operacao</code>.
        </p>
      </header>

      <OpsWorkspaceCard title="Área de trabalho" hint={meta.hint}>
        <div className="flex flex-wrap gap-2">
          {TABS.map((t) => (
            <TabButton key={t} active={tab === t} onClick={() => setTab(t)}>
              {TAB_META[t].label}
            </TabButton>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {tab !== 'promotions' ? (
            <button type="button" className={BTN_GHOST} onClick={refreshTab} disabled={loading}>
              {loading ? 'Atualizando…' : 'Atualizar'}
            </button>
          ) : null}
          <button type="button" className={BTN_GHOST} onClick={() => void onSeedWorld()} disabled={loading}>
            Seed mundial
          </button>
          {tab === 'promotions' ? (
            <button type="button" className={BTN_PRIMARY} onClick={() => setTab('overview')}>
              Ver KPIs
            </button>
          ) : null}
        </div>
      </OpsWorkspaceCard>

      {message ? <OpsSuccessBanner>{message}</OpsSuccessBanner> : null}
      {error ? <OpsErrorBanner>{error}</OpsErrorBanner> : null}
      <OpsInfoBanner>
        API order_pickup — leitura para auditoria; mutações (seed, campanhas, status) exigem <strong>admin_operacao</strong>.
      </OpsInfoBanner>

      {tab === 'overview' && (
        <OpsWorkspaceCard title="Painel operacional" hint={loading ? 'Carregando…' : undefined}>
          {overview ? (
            <>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <KpiCard
                  label="Promoções ativas"
                  value={String(overview.promotions_active)}
                  sub={`de ${overview.promotions_total} cadastradas`}
                />
                <KpiCard
                  label="Campanhas ativas"
                  value={String(overview.campaigns_active)}
                  sub={`de ${overview.campaigns_total} no catálogo`}
                />
                <KpiCard label="Resgates 24h" value={String(overview.redemptions_24h)} sub="validações recentes" />
                <KpiCard label="Resgates total" value={String(overview.redemptions_total)} sub="histórico acumulado" />
              </div>
              {overview.top_promotion_codes?.length ? (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-slate-400">Top códigos (resgates)</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {overview.top_promotion_codes.map((row) => (
                      <span
                        key={row.code}
                        className="rounded-full border border-slate-500/50 bg-slate-800/60 px-2 py-0.5 text-xs text-slate-200"
                      >
                        {row.code}: {row.redemptions}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
              {overview.player_segments?.length ? (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-slate-400">Segmentos (catálogo global)</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {overview.player_segments.map((row) => (
                      <span
                        key={row.segment}
                        className="rounded-full border border-slate-500/50 px-2 py-0.5 text-xs text-slate-300"
                      >
                        {row.segment}: {row.count}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
              {overview.featured_locker_players?.length ? (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-slate-400">
                    Players locker mundial (catálogo {overview.locker_players_catalog_size ?? '—'})
                  </h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {overview.featured_locker_players.map((code) => (
                      <span
                        key={code}
                        className="rounded-full border border-emerald-500/40 bg-emerald-950/30 px-2 py-0.5 text-xs text-emerald-200"
                      >
                        {code}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
              {overview.top_player_scopes?.length ? (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-slate-400">Players com escopo ativo (seed)</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {overview.top_player_scopes.map((row) => (
                      <span
                        key={row.player_code}
                        className="rounded-full border border-blue-500/40 bg-blue-950/40 px-2 py-0.5 text-xs text-blue-200"
                      >
                        {row.player_code} · {row.scopes}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
              {overview.player_promotion_matrix?.length ? (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-slate-400">
                    Matriz player → promoções ativas
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Contagem por escopo INCLUDE (PLAYER / LOCKER / MARKETPLACE). Detalhe na aba{' '}
                    <button type="button" className="text-indigo-300 underline" onClick={() => setTab('lab')}>
                      Laboratório
                    </button>
                    .
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {overview.player_promotion_matrix.map((row) => (
                      <span
                        key={row.player_code}
                        className="rounded-lg border border-indigo-500/45 bg-indigo-950/35 px-2.5 py-1 text-xs text-indigo-100"
                        title={`${row.active_promotions} promoção(ões) ativa(s)`}
                      >
                        {row.player_code}: {row.active_promotions}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
              {!overview.promotions_total ? (
                <EmptyState>
                  Catálogo vazio. Use <strong>Seed mundial</strong> para campanhas demo (Magalu, InPost, DHL…).
                </EmptyState>
              ) : null}
            </>
          ) : !loading ? (
            <EmptyState>
              Clique em <strong>Atualizar</strong> para carregar KPIs ou execute o seed na primeira visita.
            </EmptyState>
          ) : null}
        </OpsWorkspaceCard>
      )}

      {tab === 'campaigns' && (
        <OpsWorkspaceCard title={`Campanhas (${campaigns.length})`}>
          <form
            onSubmit={onCreateCampaign}
            className="grid gap-2 rounded-lg border border-slate-700/50 bg-slate-900/30 p-3 md:grid-cols-5"
          >
            <input
              className="rounded border px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-950"
              placeholder="Código"
              required
              value={campForm.code}
              onChange={(e) => setCampForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
            />
            <input
              className="rounded border px-2 py-1.5 text-sm md:col-span-2 dark:border-slate-600 dark:bg-slate-950"
              placeholder="Nome da campanha"
              required
              value={campForm.name}
              onChange={(e) => setCampForm((f) => ({ ...f, name: e.target.value }))}
            />
            <select
              className="rounded border px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-950"
              value={campForm.channel_family}
              onChange={(e) => setCampForm((f) => ({ ...f, channel_family: e.target.value }))}
            >
              {CHANNEL_FAMILIES.map((x) => (
                <option key={x} value={x}>
                  {x}
                </option>
              ))}
            </select>
            <button type="submit" className={BTN_PRIMARY} disabled={loading}>
              Criar campanha
            </button>
          </form>
          {campaigns.length > 0 ? (
            <div className="mt-3 overflow-x-auto rounded-lg border dark:border-slate-700">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-800/80 text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Código</th>
                    <th className="px-3 py-2">Família</th>
                    <th className="px-3 py-2">Promoções</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Nome</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((c) => (
                    <tr key={c.id} className="border-t dark:border-slate-800">
                      <td className="px-3 py-2 font-mono text-xs">{c.code}</td>
                      <td className="px-3 py-2">{c.channel_family}</td>
                      <td className="px-3 py-2">{c.promotions_count}</td>
                      <td className="px-3 py-2">
                        <StatusPill active={c.is_active} />
                      </td>
                      <td className="px-3 py-2">{c.name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : !loading ? (
            <EmptyState>Nenhuma campanha. Crie acima ou use <strong>Seed mundial</strong>.</EmptyState>
          ) : null}
        </OpsWorkspaceCard>
      )}

      {tab === 'promotions' && (
        <OpsWorkspaceCard
          title="Promoções"
          hint="Fluxo: 1) Listar → 2) Selecionar linha → 3) Escopos e exclusões no painel inferior."
        >
          <OpsPromotions embedded />
        </OpsWorkspaceCard>
      )}

      {tab === 'lab' && (
        <OpsWorkspaceCard title="Laboratório" hint={TAB_META.lab.hint}>
          <OpsPromotionsLabPage embedded />
        </OpsWorkspaceCard>
      )}

      {tab === 'redemptions' && (
        <OpsWorkspaceCard title={`Resgates (${redemptions.length})`}>
          {redemptions.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border dark:border-slate-700">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-800/80 text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Pedido</th>
                    <th className="px-3 py-2">Player</th>
                    <th className="px-3 py-2">País</th>
                    <th className="px-3 py-2">Desconto</th>
                    <th className="px-3 py-2">Quando</th>
                  </tr>
                </thead>
                <tbody>
                  {redemptions.map((r) => (
                    <tr key={r.id} className="border-t dark:border-slate-800">
                      <td className="px-3 py-2 font-mono text-xs">{r.order_id}</td>
                      <td className="px-3 py-2">{r.player_code || '—'}</td>
                      <td className="px-3 py-2">{r.country_code || '—'}</td>
                      <td className="px-3 py-2">{formatMoney(r.discount_cents)}</td>
                      <td className="px-3 py-2">{formatShortIso(r.redeemed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : !loading ? (
            <EmptyState>
              Nenhum resgate. Validações em <strong>POST /promotions/validate</strong> aparecem aqui.
            </EmptyState>
          ) : null}
        </OpsWorkspaceCard>
      )}
    </div>
  )
}
