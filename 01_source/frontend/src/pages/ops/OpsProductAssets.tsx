import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
const inp =
  'w-full rounded border border-gray-300 bg-white px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100'

export default function OpsProductAssets() {
  const [productId, setProductId] = useState('')
  const [mediaJson, setMediaJson] = useState(
    '{"media_type":"IMAGE","url":"https://cdn.exemplo/item.jpg","is_primary":true}',
  )
  const [barcodeJson, setBarcodeJson] = useState(
    '{"barcode_type":"EAN13","barcode_value":"7890000000001","is_primary":true}',
  )
  const [result, setResult] = useState('')

  const base = useMemo(() => `/api/op/products/${encodeURIComponent(productId || '_')}`, [productId])

  async function post(path: string, body: object) {
    if (!productId.trim()) return
    const r = await fetch(`/api/op/products/${encodeURIComponent(productId)}${path}`, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await r.json().catch(() => ({}))
    setResult(JSON.stringify(data, null, 2))
  }

  return (
    <div className="p-6">
      <Link to="/ops/products/admin" className="text-sm text-indigo-600 hover:underline">
        ← Hub produtos
      </Link>
      <h1 className="mt-2 text-xl font-bold">Assets de produto</h1>
      <p className="text-sm text-gray-500">Mídia e barcodes (GTIN/EAN) por SKU.</p>
      <label className="mt-4 block text-sm">
        product_id
        <input className={`${inp} mt-1 max-w-md`} value={productId} onChange={(e) => setProductId(e.target.value)} />
      </label>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-sm font-medium">POST {base}/media</p>
          <textarea className={`${inp} mt-1 font-mono text-xs`} rows={5} value={mediaJson} onChange={(e) => setMediaJson(e.target.value)} />
          <button
            type="button"
            className="mt-2 rounded bg-indigo-600 px-3 py-1 text-sm text-white"
            onClick={() => void post('/media', JSON.parse(mediaJson) as object)}
          >
            Enviar mídia
          </button>
        </div>
        <div>
          <p className="text-sm font-medium">POST {base}/barcodes</p>
          <textarea className={`${inp} mt-1 font-mono text-xs`} rows={5} value={barcodeJson} onChange={(e) => setBarcodeJson(e.target.value)} />
          <button
            type="button"
            className="mt-2 rounded bg-indigo-600 px-3 py-1 text-sm text-white"
            onClick={() => void post('/barcodes', JSON.parse(barcodeJson) as object)}
          >
            Enviar barcode
          </button>
        </div>
      </div>
      {result ? (
        <pre className="mt-4 max-h-80 overflow-auto rounded bg-gray-900 p-3 text-xs text-gray-100">{result}</pre>
      ) : null}
    </div>
  )
}
