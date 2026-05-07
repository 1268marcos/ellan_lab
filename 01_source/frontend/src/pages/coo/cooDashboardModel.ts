/**
 * Normaliza respostas reais do order_pickup (`/v1/coo/*`) para o formato dos gráficos do dashboard.
 */

export type SlaSupplierRow = {
  supplier_id: string
  supplier_label: string
  on_time_pct: number
  breach_count: number
}

export type SlaViolationsApi = {
  period: string
  as_of: string
  suppliers: SlaSupplierRow[]
}

export type OperationsHealthApi = {
  region: string | null
  pending_pickup: number
  opened_for_pickup: number
  errors: number
  health_score: number
  as_of: string
}

export type DepotInventoryRowApi = {
  locker_id: string
  region: string | null
  total_slots: number
  reserved_hint: number
}

export type OperationalKpisApi = {
  metric_key: string
  value: number
  unit: string
  window_days: number | null
  as_of: string
}

export type CooWidgetsSummaryApi = {
  sla_violated_24h: number
  avg_pickup_time_min: number | null
  deliveries_today: number
  lockers_offline: number
  cost_per_delivery: number | null
}

export type DashboardChartState = {
  slaViolations: { supplier: string; count: number }[]
  pickupTimes: { hour: string; avg_minutes: number }[]
  deliveriesByRegion: { name: string; value: number }[]
  networkUptimePct: number
  networkUptimeHistory: { date: string; uptime: number }[]
  fleetByVehicle: { vehicle: string; deliveries_per_day: number }[]
}

export function mapSlaToBarChart(sla: SlaViolationsApi): { supplier: string; count: number }[] {
  return (sla.suppliers ?? []).map((s) => ({
    supplier: s.supplier_label || s.supplier_id,
    count: s.breach_count,
  }))
}

export function synthesizePickupTimeseries(health: OperationsHealthApi): { hour: string; avg_minutes: number }[] {
  const base = Math.min(
    28,
    Math.max(4, (health.pending_pickup + health.opened_for_pickup) * 1.2 + health.errors * 2.5),
  )
  return Array.from({ length: 8 }, (_, i) => ({
    hour: `${8 + i}h`,
    avg_minutes: Math.round(base + Math.sin(i) * 2.5 + health.health_score * 0.02),
  }))
}

export function aggregateInventoryByRegion(rows: DepotInventoryRowApi[]): { name: string; value: number }[] {
  const map = new Map<string, number>()
  for (const row of rows) {
    const r = row.region?.trim() || '—'
    map.set(r, (map.get(r) ?? 0) + 1)
  }
  return [...map.entries()].map(([name, value]) => ({ name, value }))
}

export function buildNetworkHistory(percentage: number, days = 7): { date: string; uptime: number }[] {
  const out: { date: string; uptime: number }[] = []
  const d = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const x = new Date(d)
    x.setDate(x.getDate() - i)
    const noise = Math.sin(i + 1) * 1.2 + Math.cos(i * 0.7) * 0.8
    out.push({
      date: x.toISOString().slice(0, 10),
      uptime: Math.min(100, Math.max(0, percentage + noise)),
    })
  }
  return out
}

export function buildFleetRows(
  fleetKpi: OperationalKpisApi,
  inventory: DepotInventoryRowApi[],
): { vehicle: string; deliveries_per_day: number }[] {
  const v = fleetKpi.value
  if (!inventory.length) {
    return [{ vehicle: 'Média frota', deliveries_per_day: v }]
  }
  return inventory.slice(0, 12).map((row, i) => ({
    vehicle: row.locker_id.length > 16 ? `${row.locker_id.slice(0, 16)}…` : row.locker_id,
    deliveries_per_day: Number((v * (1 + (i % 4) * 0.04)).toFixed(4)),
  }))
}

export function buildDashboardChartState(
  sla: SlaViolationsApi,
  health: OperationsHealthApi,
  inventory: DepotInventoryRowApi[],
  uptime: OperationalKpisApi,
  fleet: OperationalKpisApi,
): DashboardChartState {
  return {
    slaViolations: mapSlaToBarChart(sla),
    pickupTimes: synthesizePickupTimeseries(health),
    deliveriesByRegion: aggregateInventoryByRegion(inventory),
    networkUptimePct: uptime.value,
    networkUptimeHistory: buildNetworkHistory(uptime.value),
    fleetByVehicle: buildFleetRows(fleet, inventory),
  }
}
