import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import Papa from 'papaparse'
import type { BulkProductItem } from '../api/partners'
import { partnersApi } from '../api/partners'
import { api } from '../api/client'

type Preview = { ok: boolean; items: BulkProductItem[]; errors: string[] }

function parseJson(text: string): Preview {
  const errors: string[] = []
  try {
    const raw = JSON.parse(text) as unknown
    const arr = Array.isArray(raw) ? raw : (raw as { items?: unknown })?.items
    if (!Array.isArray(arr)) {
      return { ok: false, items: [], errors: ['JSON deve ser array ou { items: [] }'] }
    }
    if (arr.length > 100) return { ok: false, items: [], errors: ['Máximo 100 itens'] }
    const items = arr as BulkProductItem[]
    return { ok: true, items, errors }
  } catch {
    return { ok: false, items: [], errors: ['JSON inválido'] }
  }
}

function rowToItem(row: Record<string, string>): BulkProductItem | null {
  const partner_sku = row.partner_sku?.trim() || row.sku?.trim()
  const name = row.name?.trim()
  const category_id = row.category_id?.trim() || row.category?.trim()
  const price = Number(row.price_cents ?? row.price ?? '')
  if (!partner_sku || !name || !category_id || Number.isNaN(price)) return null
  return {
    partner_sku,
    name,
    category_id,
    price_cents: Math.max(0, Math.floor(price)),
    currency: row.currency || 'BRL',
    dimensions: {
      width_mm: row.width_mm ? Number(row.width_mm) : undefined,
      height_mm: row.height_mm ? Number(row.height_mm) : undefined,
      depth_mm: row.depth_mm ? Number(row.depth_mm) : undefined,
      weight_g: row.weight_g ? Number(row.weight_g) : undefined,
    },
  }
}

export function BulkUpload({
  partnerId,
  onDone,
}: {
  partnerId: string
  onDone?: () => void
}) {
  const [preview, setPreview] = useState<Preview | null>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const onDrop = useCallback((files: File[]) => {
    const f = files[0]
    if (!f) return
    setMsg(null)
    const reader = () => {
      const ext = f.name.toLowerCase()
      if (ext.endsWith('.json')) {
        f.text().then((t) => setPreview(parseJson(t)))
        return
      }
      Papa.parse(f, {
        header: true,
        skipEmptyLines: true,
        complete: (res) => {
          const errors: string[] = []
          const items: BulkProductItem[] = []
          const rows = res.data as Record<string, string>[]
          if (rows.length > 100) {
            setPreview({ ok: false, items: [], errors: ['Máximo 100 linhas'] })
            return
          }
          rows.forEach((row, i) => {
            const it = rowToItem(row)
            if (!it) errors.push(`Linha ${i + 2}: campos obrigatórios partner_sku,name,category_id,price_cents`)
            else items.push(it)
          })
          setPreview({ ok: errors.length === 0 && items.length > 0, items, errors })
        },
      })
    }
    reader()
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'application/json': ['.json'] },
    maxFiles: 1,
  })

  async function submit() {
    if (!preview?.ok || !preview.items.length) return
    setBusy(true)
    setMsg(null)
    try {
      try {
        const file = new File([JSON.stringify(preview.items)], 'bulk.json', { type: 'application/json' })
        await partnersApi.bulkUpload(partnerId, file)
      } catch {
        await api.post(`/v1/products/bulk`, { partner_id: partnerId, items: preview.items })
      }
      setMsg('Upload concluído.')
      setPreview(null)
      onDone?.()
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : 'Falha no envio')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
      <h3 className="text-sm font-semibold text-slate-200">Bulk CSV / JSON (até 100)</h3>
      <div
        {...getRootProps()}
        className={`mt-3 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-sm transition-colors ${
          isDragActive ? 'border-emerald-500 bg-emerald-950/20' : 'border-slate-600 bg-slate-950/40 hover:border-slate-500'
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-slate-400">Arraste CSV ou JSON aqui</p>
        <p className="mt-1 text-xs text-slate-500">Colunas: partner_sku, name, category_id, price_cents</p>
      </div>
      {preview && (
        <div className="mt-3 space-y-2">
          <p className={`text-sm ${preview.ok ? 'text-emerald-400' : 'text-red-400'}`}>
            {preview.ok ? `${preview.items.length} itens válidos` : 'Validação falhou'}
          </p>
          {preview.errors.map((e) => (
            <p key={e} className="text-xs text-red-300">
              {e}
            </p>
          ))}
          {preview.ok && (
            <pre className="max-h-40 overflow-auto rounded bg-slate-950 p-2 text-xs text-slate-300">
              {JSON.stringify(preview.items.slice(0, 5), null, 2)}
              {preview.items.length > 5 ? '\n…' : ''}
            </pre>
          )}
          <button
            type="button"
            disabled={!preview.ok || busy}
            onClick={submit}
            className="rounded-md bg-slate-700 px-3 py-1.5 text-sm text-white hover:bg-slate-600 disabled:opacity-40"
          >
            {busy ? 'Enviando…' : 'Confirmar envio'}
          </button>
        </div>
      )}
      {msg && <p className="mt-2 text-xs text-slate-400">{msg}</p>}
    </div>
  )
}
