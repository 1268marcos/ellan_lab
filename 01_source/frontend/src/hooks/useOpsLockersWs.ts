import { useEffect, useRef, useState } from 'react'
import { opsRealtimeWsUrl } from '../api/lockersOps'

type WsOpts = {
  path: '/ws/ops/realtime' | '/ws/ops/alerts'
  subscribeLockerIds?: string[]
  enabled?: boolean
}

export function useOpsLockersWs<T>({ path, subscribeLockerIds, enabled = true }: WsOpts) {
  const [payload, setPayload] = useState<T | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!enabled) return undefined
    const ws = new WebSocket(opsRealtimeWsUrl(path))
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      if (path === '/ws/ops/realtime' && subscribeLockerIds?.length) {
        ws.send(JSON.stringify({ type: 'subscribe', locker_ids: subscribeLockerIds }))
      }
    }
    ws.onmessage = (ev) => {
      try {
        setPayload(JSON.parse(ev.data) as T)
      } catch {
        /* ignore */
      }
    }
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [path, enabled, subscribeLockerIds?.join(',')])

  return { payload, connected }
}
