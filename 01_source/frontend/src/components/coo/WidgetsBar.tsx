import React, { useEffect, useState } from 'react'

import { cooApi, type CooWidgetsSummary } from '../../api/coo'
import { COOTheme } from '../../styles/coo/theme'

type WidgetRow = {
  label: string
  raw: number | null
  unit: string
  critical?: boolean
  attention?: boolean
  positive?: boolean
  format?: 'currency'
}

function formatDisplay(w: WidgetRow): string {
  if (w.format === 'currency') {
    if (w.raw == null) return '—'
    return `R$ ${Number(w.raw).toFixed(2)}`
  }
  if (w.raw == null) return '—'
  return String(w.raw)
}

export const WidgetsBar: React.FC = () => {
  const [data, setData] = useState<CooWidgetsSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchWidgets = async () => {
      try {
        const response = await cooApi.getWidgetsSummary()
        setData(response.data)
      } catch (error) {
        console.error('Failed to fetch widgets:', error)
      } finally {
        setLoading(false)
      }
    }
    void fetchWidgets()
    const interval = setInterval(() => void fetchWidgets(), 30_000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <div className="coo-widgets-loading">Carregando…</div>
  }
  if (!data) {
    return null
  }

  const widgets: WidgetRow[] = [
    {
      label: 'SLA violados (24h)',
      raw: data.sla_violated_24h,
      unit: '',
      critical: data.sla_violated_24h > 5,
    },
    {
      label: 'Tempo médio de retirada',
      raw: data.avg_pickup_time_min,
      unit: 'min',
      attention: data.avg_pickup_time_min != null && data.avg_pickup_time_min > 15,
    },
    {
      label: 'Entregas realizadas hoje',
      raw: data.deliveries_today,
      unit: '',
      positive: true,
    },
    {
      label: 'Lockers offline',
      raw: data.lockers_offline,
      unit: '',
      critical: data.lockers_offline > 10,
    },
    {
      label: 'Custo por entrega',
      raw: data.cost_per_delivery,
      unit: '',
      format: 'currency',
    },
  ]

  return (
    <div className="coo-widgets-bar">
      {widgets.map((widget) => (
        <div
          key={widget.label}
          className="coo-kpi-card"
          style={{
            borderLeft:
              widget.critical === true
                ? `4px solid ${COOTheme.colors.status.critical}`
                : widget.attention === true
                  ? `4px solid ${COOTheme.colors.warning}`
                  : widget.positive === true
                    ? `4px solid ${COOTheme.colors.status.operational}`
                    : 'none',
          }}
        >
          <div className="coo-kpi-label">{widget.label}</div>
          <div className="coo-kpi-value">
            {formatDisplay(widget)}
            {widget.unit && widget.raw != null && (
              <span style={{ fontSize: '14px', marginLeft: '4px' }}>{widget.unit}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
