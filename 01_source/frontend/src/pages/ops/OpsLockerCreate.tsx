import { FormEvent, useCallback, useMemo, useState } from 'react'
import { lockerCreateApi, type LockerCreatePayload, type LockerOut } from '../../api/lockerCreate'

const DEFAULT_SLOTS: LockerCreatePayload['slot_configs'] = [
  { slot_size: 'P', slot_count: 10, available_count: 10, width_mm: 100, height_mm: 100, depth_mm: 400, max_weight_g: 2000 },
  { slot_size: 'M', slot_count: 10, available_count: 10, width_mm: 200, height_mm: 200, depth_mm: 400, max_weight_g: 5000 },
  { slot_size: 'G', slot_count: 10, available_count: 10, width_mm: 300, height_mm: 400, depth_mm: 400, max_weight_g: 10000 },
]

const emptyForm = (): LockerCreatePayload => ({
  id: '',
  display_name: '',
  region: 'PR',
  city: '',
  state: 'PR',
  country: 'BR',
  timezone: 'America/Sao_Paulo',
  operator_id: 'OP-ELLAN-001',
  temperature_zone: 'AMBIENT',
  security_level: 'STANDARD',
  has_camera: false,
  has_alarm: false,
  has_kiosk: true,
  has_printer: false,
  has_card_reader: true,
  has_nfc: false,
  slot_configs: DEFAULT_SLOTS,
  copy_product_configs_from: 'SP-OSASCO-CENTRO-LK-001',
})

function parseBulkJson(raw: string): LockerCreatePayload[] {
  const parsed = JSON.parse(raw) as unknown
  if (!Array.isArray(parsed)) throw new Error('JSON deve ser um array de lockers.')
  return parsed as LockerCreatePayload[]
}

export default function OpsLockerCreate() {
  const [form, setForm] = useState(emptyForm)
  const [bulkJson, setBulkJson] = useState('')
  const [selectedId, setSelectedId] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [items, setItems] = useState<LockerOut[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const totalSlots = useMemo(
    () => (form.slot_configs ?? []).reduce((acc, s) => acc + (s.slot_count || 0), 0),
    [form.slot_configs],
  )

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await lockerCreateApi.list()
      setItems(data.lockers ?? [])
    } catch (err: unknown) {
      setItems([])
      setError(err instanceof Error ? err.message : 'Falha ao listar lockers')
    } finally {
      setLoading(false)
    }
  }, [])

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const { data } = await lockerCreateApi.create(form)
      setMessage(`Locker ${data.id} criado (${data.slots_count} slots).`)
      setSelectedId(data.id)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar locker')
    } finally {
      setLoading(false)
    }
  }

  const onBulk = async () => {
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const lockers = parseBulkJson(bulkJson)
      const { data } = await lockerCreateApi.bulkCreate(lockers)
      setMessage(`Bulk: ${data.created.length} criados, ${data.failed.length} falhas.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no bulk')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedId || !webhookUrl) return
    setLoading(true)
    setError(null)
    try {
      await lockerCreateApi.configureWebhook(selectedId, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['locker.created', 'locker.updated'],
      })
      setMessage(`Webhook configurado para ${selectedId}.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedId) return
    setLoading(true)
    setError(null)
    try {
      const { data } = await lockerCreateApi.rotateApiKey(selectedId)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…). Copie agora; nao sera exibida de novo.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar chave')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Criar lockers</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Cadastro de um ou varios equipamentos (CRUD, webhook e rotacao de API key).
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Atualizar lista
        </button>
      </div>

      {loading && <p className="text-sm text-gray-500">Processando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {lastApiKey && (
        <p className="rounded border border-amber-300 bg-amber-50 p-2 font-mono text-xs text-amber-900">
          API key: {lastApiKey}
        </p>
      )}

      <form onSubmit={onSubmit} className="grid gap-4 rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2">
        <label className="block text-sm md:col-span-2">
          <span className="text-gray-600 dark:text-slate-400">ID</span>
          <input
            className="mt-1 w-full ellan-field font-mono dark:border-slate-600 dark:bg-slate-800"
            value={form.id}
            onChange={(e) => setForm((f) => ({ ...f, id: e.target.value }))}
            placeholder="PR-CAPITAL-SANTAFELICIDADE-LK-001"
            required
          />
        </label>
        <label className="block text-sm md:col-span-2">
          <span className="text-gray-600 dark:text-slate-400">Nome exibicao</span>
          <input
            className="mt-1 w-full ellan-field dark:border-slate-600 dark:bg-slate-800"
            value={form.display_name}
            onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
            required
          />
        </label>
        <label className="block text-sm">
          <span className="text-gray-600 dark:text-slate-400">Regiao</span>
          <input
            className="mt-1 w-full ellan-field dark:border-slate-600 dark:bg-slate-800"
            value={form.region}
            onChange={(e) => setForm((f) => ({ ...f, region: e.target.value }))}
            required
          />
        </label>
        <label className="block text-sm">
          <span className="text-gray-600 dark:text-slate-400">Operador</span>
          <input
            className="mt-1 w-full ellan-field dark:border-slate-600 dark:bg-slate-800"
            value={form.operator_id ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, operator_id: e.target.value }))}
          />
        </label>
        <label className="block text-sm">
          <span className="text-gray-600 dark:text-slate-400">Cidade</span>
          <input
            className="mt-1 w-full ellan-field dark:border-slate-600 dark:bg-slate-800"
            value={form.city}
            onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))}
            required
          />
        </label>
        <label className="block text-sm">
          <span className="text-gray-600 dark:text-slate-400">UF</span>
          <input
            className="mt-1 w-full ellan-field dark:border-slate-600 dark:bg-slate-800"
            value={form.state}
            onChange={(e) => setForm((f) => ({ ...f, state: e.target.value }))}
            required
          />
        </label>
        <label className="block text-sm md:col-span-2">
          <span className="text-gray-600 dark:text-slate-400">Copiar product_configs de</span>
          <input
            className="mt-1 w-full ellan-field font-mono dark:border-slate-600 dark:bg-slate-800"
            value={form.copy_product_configs_from ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, copy_product_configs_from: e.target.value }))}
          />
        </label>
        <p className="text-xs text-gray-500 md:col-span-2">Slots padrao P/M/G: {totalSlots} gavetas.</p>
        <div className="flex flex-wrap gap-4 md:col-span-2">
          {(['has_kiosk', 'has_card_reader', 'has_camera', 'has_alarm', 'has_printer', 'has_nfc'] as const).map((key) => (
            <label key={key} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={Boolean(form[key])}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.checked }))}
              />
              {key.replace('has_', '')}
            </label>
          ))}
        </div>
        <button
          type="submit"
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 md:col-span-2"
        >
          Criar locker
        </button>
      </form>

      <section className="rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <h2 className="mb-2 text-lg font-medium">Bulk (JSON array)</h2>
        <textarea
          className="min-h-32 w-full ellan-field font-mono text-xs"
          value={bulkJson}
          onChange={(e) => setBulkJson(e.target.value)}
          placeholder={'[{"id":"LK-002","display_name":"…","region":"SP","city":"Osasco","state":"SP"}]'}
        />
        <button
          type="button"
          onClick={() => void onBulk()}
          className="mt-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-500"
        >
          Enviar bulk
        </button>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <h2 className="mb-2 text-lg font-medium">Webhook e API key</h2>
        <div className="flex flex-wrap gap-2">
          <select
            className="ellan-field dark:border-slate-600 dark:bg-slate-800"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            <option value="">Selecione locker</option>
            {items.map((l) => (
              <option key={l.id} value={l.id}>
                {l.id}
              </option>
            ))}
          </select>
          <input
            className="min-w-[16rem] flex-1 ellan-field dark:border-slate-600 dark:bg-slate-800"
            placeholder="Webhook URL"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
          />
          <input
            className="ellan-field dark:border-slate-600 dark:bg-slate-800"
            placeholder="Secret (opcional)"
            value={webhookSecret}
            onChange={(e) => setWebhookSecret(e.target.value)}
          />
          <button type="button" onClick={() => void onWebhook()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
            Salvar webhook
          </button>
          <button type="button" onClick={() => void onRotateKey()} className="rounded bg-amber-600 px-3 py-1 text-sm text-white">
            Rotacionar API key
          </button>
        </div>
      </section>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">Regiao</th>
              <th className="px-3 py-2">Slots</th>
              <th className="px-3 py-2">Ativo</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-gray-500">
                  Nenhum locker (carregue a lista)
                </td>
              </tr>
            ) : (
              items.map((l) => (
                <tr key={l.id} className="border-t border-gray-100 dark:border-slate-800">
                  <td className="px-3 py-2 font-mono text-xs">{l.id}</td>
                  <td className="px-3 py-2">{l.display_name}</td>
                  <td className="px-3 py-2">{l.region}</td>
                  <td className="px-3 py-2">{l.slots_count}</td>
                  <td className="px-3 py-2">{l.active ? 'sim' : 'nao'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
