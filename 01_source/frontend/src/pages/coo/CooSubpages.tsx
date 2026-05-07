import React from 'react'

import { Placeholder } from './Placeholder'

export const PickupHealth: React.FC = () => (
  <Placeholder title="Saúde de pickups" endpointSlug="health/pickups" />
)

export const UrgentDeadlines: React.FC = () => (
  <Placeholder title="Deadlines urgentes" endpointSlug="deadlines/urgent" />
)

export const ActiveManifests: React.FC = () => (
  <Placeholder title="Manifestos ativos" endpointSlug="logistics/manifests/active" />
)

export const RealtimeRouting: React.FC = () => (
  <Placeholder title="Roteirização em tempo real" endpointSlug="logistics/routing/realtime" />
)

export const InventoryByDepot: React.FC = () => (
  <Placeholder title="Inventário por depot" endpointSlug="logistics/inventory/by-depot" />
)

export const SupplierSLA: React.FC = () => (
  <Placeholder title="SLA por fornecedor" endpointSlug="suppliers/sla" />
)

export const PenaltiesApplied: React.FC = () => (
  <Placeholder title="Penalidades aplicadas" endpointSlug="suppliers/penalties" />
)

export const ComplianceReports: React.FC = () => (
  <Placeholder title="Compliance reports" endpointSlug="suppliers/compliance" />
)

export const NetworkUptime: React.FC = () => (
  <Placeholder title="Uptime da rede" endpointSlug="kpis/network/uptime" />
)

export const MTTR: React.FC = () => <Placeholder title="MTTR" endpointSlug="kpis/mttr" />

export const FleetEfficiency: React.FC = () => (
  <Placeholder title="Eficiência de frota" endpointSlug="kpis/fleet/efficiency" />
)

export const PendingApprovals: React.FC = () => (
  <Placeholder title="Procedimentos pendentes" endpointSlug="approvals/pending" />
)

export const SLAAjustments: React.FC = () => (
  <Placeholder title="Ajustes de SLA regional" description="Use o formulário para enviar pedidos." endpointSlug="approvals/sla/adjust" />
)

export const ExpansionRequests: React.FC = () => (
  <Placeholder title="Solicitações de expansão" description="Use o formulário para enviar pedidos." endpointSlug="approvals/expansion" />
)
