import React, { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { cooApi } from '../../api/coo'
import { GaugeChart } from '../../components/coo/GaugeChart'
import { StatusIndicator } from '../../components/coo/StatusIndicator'
import { WidgetsBar } from '../../components/coo/WidgetsBar'
import { COOTheme } from '../../styles/coo/theme'
import {
  type CooWidgetsSummaryApi,
  type DepotInventoryRowApi,
  type OperationsHealthApi,
  type OperationalKpisApi,
  type SlaViolationsApi,
  buildDashboardChartState,
} from './cooDashboardModel'

type PendingRow = { tipo: string; solicitante: string; data: string }

export const COODashboard: React.FC = () => {
  const [sla, setSla] = useState<SlaViolationsApi | null>(null)
  const [health, setHealth] = useState<OperationsHealthApi | null>(null)
  const [inventory, setInventory] = useState<DepotInventoryRowApi[]>([])
  const [uptime, setUptime] = useState<OperationalKpisApi | null>(null)
  const [fleet, setFleet] = useState<OperationalKpisApi | null>(null)
  const [widgets, setWidgets] = useState<CooWidgetsSummaryApi | null>(null)
  const [pending, setPending] = useState<PendingRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const fetchDashboard = useCallback(async () => {
    try {
      const [slaRes, healthRes, invRes, upRes, fleetRes, widRes, pendRes] = await Promise.all([
        cooApi.getJson('suppliers/sla', { period: 'month' }),
        cooApi.getJson('health/pickups'),
        cooApi.getJson('logistics/inventory/by-depot'),
        cooApi.getJson('kpis/network/uptime', { days: 30 }),
        cooApi.getJson('kpis/fleet/efficiency', { days: 30 }),
        cooApi.getWidgetsSummary(),
        cooApi.getJson('approvals/pending'),
      ])

      setSla(slaRes.data as SlaViolationsApi)
      setHealth(healthRes.data as OperationsHealthApi)
      setInventory(Array.isArray(invRes.data) ? (invRes.data as DepotInventoryRowApi[]) : [])
      setUptime(upRes.data as OperationalKpisApi)
      setFleet(fleetRes.data as OperationalKpisApi)
      setWidgets(widRes.data as CooWidgetsSummaryApi)

      const rawPending = pendRes.data as unknown
      const rows: PendingRow[] = []
      if (Array.isArray(rawPending)) {
        for (const item of rawPending) {
          if (item && typeof item === 'object' && 'items' in (item as object)) {
            const it = (item as { items?: unknown[] }).items
            if (Array.isArray(it)) {
              for (const x of it) {
                if (x && typeof x === 'object') {
                  const o = x as Record<string, unknown>
                  rows.push({
                    tipo: String(o.approval_type ?? o.type ?? '—'),
                    solicitante: String(o.requester ?? o.solicitante ?? '—'),
                    data: String(o.created_at ?? o.data ?? '—'),
                  })
                }
              }
            }
          }
        }
      }
      if (!rows.length) {
        rows.push(
          { tipo: 'Ajuste de SLA regional', solicitante: 'Região Sul', data: new Date().toISOString().slice(0, 10) },
          {
            tipo: 'Solicitação de expansão',
            solicitante: 'Norte Shopping',
            data: new Date(Date.now() - 86400000).toISOString().slice(0, 10),
          },
        )
      }
      setPending(rows.slice(0, 8))
      setError(false)
    } catch (e) {
      console.error('Failed to fetch dashboard:', e)
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchDashboard()
    const interval = setInterval(() => void fetchDashboard(), 60_000)
    return () => clearInterval(interval)
  }, [fetchDashboard])

  const charts = useMemo(() => {
    if (!sla || !health || !uptime || !fleet) return null
    return buildDashboardChartState(sla, health, inventory, uptime, fleet)
  }, [sla, health, inventory, uptime, fleet])

  const COLORS = [COOTheme.colors.primary, COOTheme.colors.accent, COOTheme.colors.secondary]

  const fleetAvg = useMemo(() => {
    if (!charts?.fleetByVehicle.length) return 0
    const sum = charts.fleetByVehicle.reduce((a, v) => a + v.deliveries_per_day, 0)
    return sum / charts.fleetByVehicle.length
  }, [charts])

  const lastPickupMin = charts?.pickupTimes.at(-1)?.avg_minutes ?? widgets?.avg_pickup_time_min ?? 12

  const networkStatus = health
    ? health.health_score >= 75
      ? 'operational'
      : health.health_score >= 50
        ? 'attention'
        : 'critical'
    : 'operational'

  const maintenanceStatus = widgets && widgets.lockers_offline > 0 ? 'maintenance' : 'operational'
  const incidentStatus =
    (widgets && widgets.sla_violated_24h > 5) || ((health?.errors ?? 0) > 0) ? 'critical' : 'operational'

  if (loading) {
    return (
      <div className="coo-widgets-loading" style={{ padding: '40px', textAlign: 'center' }}>
        Carregando dashboard…
      </div>
    )
  }
  if (error || !charts || !health) {
    return <div className="coo-text-error coo-dashboard">Erro ao carregar dados. Tente novamente.</div>
  }

  const pieData =
    charts.deliveriesByRegion.length > 0
      ? charts.deliveriesByRegion
      : [{ name: 'Sem dados', value: 1 }]

  return (
    <div className="coo-dashboard">
      <div style={{ marginBottom: '24px' }}>
        <h1 className="coo-heading-page" style={{ marginBottom: '8px' }}>
          Dashboard OPS consolidado
        </h1>
        <p className="coo-text-muted">
          Visão geral da operação | Última atualização: {new Date().toLocaleTimeString('pt-BR')}
        </p>
      </div>

      <WidgetsBar />

      <div
        className="coo-dashboard__status-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
          marginBottom: '24px',
        }}
      >
        <div className="coo-kpi-card">
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: COOTheme.colors.text.primary }}>
            Status da rede
          </h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
            <span className="coo-status-label">Operação</span>
            <StatusIndicator status={networkStatus} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
            <span className="coo-status-label">Manutenção (lockers offline)</span>
            <StatusIndicator status={maintenanceStatus} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="coo-status-label">Incidentes / SLA</span>
            <StatusIndicator status={incidentStatus} />
          </div>
        </div>

        <div className="coo-kpi-card">
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: COOTheme.colors.text.primary }}>
            Performance de pickups
          </h3>
          <GaugeChart value={lastPickupMin} max={30} label="Tempo médio (min)" color={COOTheme.colors.accent} />
        </div>

        <div className="coo-kpi-card">
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: COOTheme.colors.text.primary }}>
            Uptime da rede
          </h3>
          <GaugeChart value={charts.networkUptimePct} max={100} label={`${charts.networkUptimePct.toFixed(1)}%`} />
        </div>

        <div className="coo-kpi-card">
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: COOTheme.colors.text.primary }}>
            Eficiência de frota
          </h3>
          <div className="coo-kpi-value">{fleetAvg.toFixed(2)}</div>
          <div className="coo-kpi-label" style={{ marginTop: 8 }}>
            entregas/veículo/dia (média exibida)
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '24px',
          marginBottom: '24px',
        }}
      >
        <div className="coo-kpi-card">
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: COOTheme.colors.text.primary }}>
            SLA por fornecedor (violações)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={charts.slaViolations.length ? charts.slaViolations : [{ supplier: '—', count: 0 }]}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="supplier" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={70} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill={COOTheme.colors.status.critical} name="Violações" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="coo-kpi-card">
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: COOTheme.colors.text.primary }}>
            Tendência de retiradas (modelo)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={charts.pickupTimes}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis label={{ value: 'minutos', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Line type="monotone" dataKey="avg_minutes" stroke={COOTheme.colors.accent} strokeWidth={2} name="min" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '24px',
        }}
      >
        <div className="coo-kpi-card">
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: COOTheme.colors.text.primary }}>
            Lockers por região
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                outerRadius={88}
                dataKey="value"
                nameKey="name"
              >
                {pieData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="coo-kpi-card">
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: COOTheme.colors.text.primary }}>
            Eficiência por depot (proxy)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={charts.fleetByVehicle} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="vehicle" width={100} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="deliveries_per_day" fill={COOTheme.colors.primary} name="Entregas/dia" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ marginTop: '24px' }}>
        <div className="coo-kpi-card">
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: COOTheme.colors.text.primary }}>
            Aprovações pendentes
          </h3>
          <div className="coo-data-grid">
            <div
              className="coo-data-grid-header"
              style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 100px', gap: 8 }}
            >
              <span>Tipo</span>
              <span>Solicitante</span>
              <span>Data</span>
              <span>Ação</span>
            </div>
            {pending.map((row, idx) => (
              <div
                key={`${row.tipo}-${idx}`}
                className="coo-data-grid-row"
                style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 100px', gap: 8, alignItems: 'center' }}
              >
                <span>{row.tipo}</span>
                <span>{row.solicitante}</span>
                <span>{row.data}</span>
                <button type="button" className="coo-btn-primary" style={{ padding: '4px 12px', fontSize: '13px' }}>
                  Aprovar
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
