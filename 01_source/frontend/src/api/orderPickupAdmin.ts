import { api } from './client'

const BASE = '/api/order-pickup-admin/v1/order-pickup-admin'

export type EcommercePartner = {
  id: string
  name: string
  code: string
  status: string
  active: boolean
}

export type LogisticsPartner = {
  id: string
  name: string
  code: string
  active: boolean
}

export type OrderRow = {
  id: string
  status: string
  payment_status: string
  amount_cents: number
  ecommerce_partner_id?: string
  locker_id?: string
}

export type ChannelRow = {
  id: string
  code: string
  name: string
  player_type: string
  country: string
  region_scope: string
  api_profile?: string
  active: boolean
  review_status?: string
  pickup_modes?: string[]
  markets?: string[]
  linked_partners?: { kind: string; code: string; name?: string; role?: string }[]
}

export type PlayerReview = {
  code: string
  name: string
  player_type: string
  country: string
  review_status: string
  markets: string[]
  pickup_modes: string[]
  ecommerce_partner_code?: string
  logistics_partner_code?: string
  configured: boolean
  active: boolean
  prompt_group?: string
}

export type WorldPlayersReview = {
  players: PlayerReview[]
  by_type: Record<string, number>
  prompt3_total: number
  prompt3_configured: number
  prompt3_complete: boolean
  prompt4_total: number
  prompt4_configured: number
  prompt4_complete: boolean
  catalog_total: number
  catalog_configured: number
}

export type FoodDeliveryRow = {
  id: string
  order_id: string
  platform_code: string
  status: string
  temperature_zone: string
  external_order_ref?: string
}

export type TimelineEvent = {
  id: string
  order_id: string
  event_source: string
  event_type: string
  severity: string
  title: string
  occurred_at: string
}

export type Order360 = {
  order_id: string
  order: Record<string, unknown>
  counts: Record<string, number>
  timeline: TimelineEvent[]
  sla: { active: number; breached: number }
  disputes_open: number
  risk_flags: string[]
  health_score: number
  pickups: { id: string; status: string; lifecycle_stage: string; locker_id?: string }[]
  partner_outbox_pending: number
}

export type SlaWatch = {
  id: string
  order_id: string
  watch_type: string
  due_at: string
  status: string
  breached_at?: string
  breach_reason?: string
}

export type OrderDispute = {
  id: string
  order_id: string
  dispute_type: string
  status: string
  amount_cents?: number
  currency: string
  reason_code?: string
  opened_at: string
}

export type IntegrationHealthRow = {
  id: string
  channel_code: string
  check_type: string
  status: string
  latency_ms?: number
  last_error?: string
  checked_at: string
}

export type OrderReturnRow = {
  id: string
  order_id: string
  return_type: string
  status: string
  reason_code?: string
  refund_amount_cents?: number
  requested_at: string
}

export type OrderNotificationRow = {
  id: string
  order_id: string
  channel: string
  template_code: string
  status: string
  sent_at: string
}

export type PaymentReconRow = {
  id: string
  order_id: string
  expected_cents: number
  captured_cents: number
  fee_cents: number
  status: string
  mismatch_reason?: string
}

export type OrderHoldRow = {
  id: string
  order_id: string
  hold_type: string
  status: string
  reason?: string
  placed_by: string
  placed_at: string
}

export type ItemSubstitutionRow = {
  id: string
  order_id: string
  original_sku_id: string
  substitute_sku_id: string
  reason_code: string
  status: string
  quantity: number
}

export type GiftPickupRow = {
  id: string
  order_id: string
  recipient_name: string
  purchaser_name?: string
  pickup_authorization_code?: string
  status: string
  id_verification_required: boolean
}

export type PaymentTransactionRow = {
  id: string
  order_id: string
  gateway: string
  amount_cents: number
  status: string
  gateway_fee_cents: number
  payment_method: string
  source: string
}

export const orderPickupAdminApi = {
  seed: () => api.post(`${BASE}/seed`),

  listEcommerce: () => api.get<{ partners: EcommercePartner[]; total: number }>(`${BASE}/ecommerce-partners`),
  listLogistics: () => api.get<{ partners: LogisticsPartner[]; total: number }>(`${BASE}/logistics-partners`),
  createEcommerce: (body: Record<string, unknown>) => api.post(`${BASE}/ecommerce-partners`, body),
  createLogistics: (body: Record<string, unknown>) => api.post(`${BASE}/logistics-partners`, body),
  configureWebhook: (partnerId: string, partnerType: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/partners/${encodeURIComponent(partnerId)}/webhook`, body, { params: { partner_type: partnerType } }),
  rotateApiKey: (partnerId: string, partnerType: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/partners/${encodeURIComponent(partnerId)}/api-keys/rotate`,
      null,
      { params: { partner_type: partnerType } },
    ),

  listOrders: (params?: { status?: string; partner_id?: string }) =>
    api.get<{ items: OrderRow[]; total: number }>(`${BASE}/orders`, { params }),
  createOrder: (body: Record<string, unknown>) => api.post(`${BASE}/orders`, body),
  updateOrder: (orderId: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/orders/${encodeURIComponent(orderId)}`, body),

  listPickups: (params?: { order_id?: string }) => api.get<{ items: unknown[]; total: number }>(`${BASE}/pickups`, { params }),
  createPickup: (body: Record<string, unknown>) => api.post(`${BASE}/pickups`, body),

  listCredits: (params?: { order_id?: string }) => api.get<{ items: unknown[]; total: number }>(`${BASE}/credits`, { params }),
  createCredit: (body: Record<string, unknown>) => api.post(`${BASE}/credits`, body),

  listOutbox: (params?: { status?: string }) => api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-outbox`, { params }),
  replayOutbox: (outboxId: string) => api.post(`${BASE}/integration-outbox/${encodeURIComponent(outboxId)}/replay`),

  listFulfillment: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fulfillment-tracking`),
  updateFulfillment: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/fulfillment-tracking/${encodeURIComponent(id)}`, body),

  listOrderItems: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/order-items`, { params }),
  listPickupEvents: (params?: { pickup_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/pickup-events`, { params }),
  listPickupTokens: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/pickup-tokens`, { params }),
  listPickupAttempts: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/pickup-attempts`, { params }),
  listDomainOutbox: (params?: { status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/domain-event-outbox`, { params }),
  replayDomainOutbox: (id: string) => api.post(`${BASE}/domain-event-outbox/${encodeURIComponent(id)}/replay`),

  hubSummary: () =>
    api.get<{
      orders: number
      pickups: number
      credits: number
      partner_outbox_pending: number
      domain_outbox_pending: number
      fulfillment_tracking: number
      omnichannel: number
      fulfillment_orders: number
      timeline_events: number
      sla_watches_active: number
      sla_watches_breached: number
      disputes_open: number
      returns_open: number
      payment_recon_mismatch: number
      ops_holds_active: number
      notifications_sent: number
      substitutions_pending: number
      gifts_pending_verification: number
      payment_transactions: number
    }>(`${BASE}/hub/summary`),

  order360: (orderId: string) => api.get<Order360>(`${BASE}/orders/${encodeURIComponent(orderId)}/360`),
  listTimeline: (orderId: string) =>
    api.get<{ items: TimelineEvent[]; total: number }>(`${BASE}/orders/${encodeURIComponent(orderId)}/timeline`),
  addTimelineNote: (orderId: string, body: Record<string, unknown>) =>
    api.post<TimelineEvent>(`${BASE}/orders/${encodeURIComponent(orderId)}/timeline`, body),

  listSlaWatches: (params?: { status?: string; order_id?: string }) =>
    api.get<{ items: SlaWatch[]; total: number }>(`${BASE}/sla-watches`, { params }),
  syncSlaWatches: () => api.post<{ created: number; breached: number }>(`${BASE}/sla-watches/sync`),

  listDisputes: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: OrderDispute[]; total: number }>(`${BASE}/order-disputes`, { params }),
  createDispute: (body: Record<string, unknown>) => api.post<OrderDispute>(`${BASE}/order-disputes`, body),

  listIntegrationHealth: (params?: { channel_code?: string }) =>
    api.get<{ items: IntegrationHealthRow[]; total: number }>(`${BASE}/integration-health`, { params }),

  listOrderReturns: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: OrderReturnRow[]; total: number }>(`${BASE}/order-returns`, { params }),
  createOrderReturn: (body: Record<string, unknown>) => api.post(`${BASE}/order-returns`, body),

  listOrderNotifications: (params?: { order_id?: string; channel?: string }) =>
    api.get<{ items: OrderNotificationRow[]; total: number }>(`${BASE}/order-notifications`, { params }),

  listPaymentReconciliation: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: PaymentReconRow[]; total: number }>(`${BASE}/payment-reconciliation`, { params }),
  runPaymentReconciliation: (body?: { order_id?: string }) =>
    api.post<{ created: number; updated: number; mismatched: number; used_gateway: number }>(
      `${BASE}/payment-reconciliation/run`,
      body ?? {},
    ),

  listOrderHolds: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: OrderHoldRow[]; total: number }>(`${BASE}/order-holds`, { params }),
  createOrderHold: (body: Record<string, unknown>) => api.post(`${BASE}/order-holds`, body),
  releaseOrderHold: (holdId: string, body?: { released_by?: string }) =>
    api.post(`${BASE}/order-holds/${encodeURIComponent(holdId)}/release`, body ?? {}),

  listItemSubstitutions: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: ItemSubstitutionRow[]; total: number }>(`${BASE}/item-substitutions`, { params }),
  createItemSubstitution: (body: Record<string, unknown>) => api.post(`${BASE}/item-substitutions`, body),
  updateItemSubstitution: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/item-substitutions/${encodeURIComponent(id)}`, body),

  listGiftPickups: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: GiftPickupRow[]; total: number }>(`${BASE}/gift-pickups`, { params }),
  createGiftPickup: (body: Record<string, unknown>) => api.post(`${BASE}/gift-pickups`, body),
  updateGiftPickup: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/gift-pickups/${encodeURIComponent(id)}`, body),

  listPaymentTransactions: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: PaymentTransactionRow[]; total: number }>(`${BASE}/payment-transactions`, { params }),
  syncPaymentTransactions: (body?: { order_id?: string }) =>
    api.post<{ synced: number; skipped: number; error?: string }>(`${BASE}/payment-transactions/sync`, body ?? {}),

  listOmnichannel: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/omnichannel-orders`, { params }),
  createOmnichannel: (body: Record<string, unknown>) => api.post(`${BASE}/omnichannel-orders`, body),
  updateOmnichannel: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/omnichannel-orders/${encodeURIComponent(id)}`, body),

  listFulfillmentOrders: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fulfillment-orders`, { params }),
  createFulfillmentOrder: (body: Record<string, unknown>) => api.post(`${BASE}/fulfillment-orders`, body),
  updateFulfillmentOrder: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/fulfillment-orders/${encodeURIComponent(id)}`, body),

  listAllocations: (params?: { order_id?: string; state?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/allocations`, { params }),
  createAllocation: (body: Record<string, unknown>) => api.post(`${BASE}/allocations`, body),
  updateAllocation: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/allocations/${encodeURIComponent(id)}`, body),

  listManifests: (params?: { status?: string; partner_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/logistics-manifests`, { params }),
  listManifestItems: (params?: { manifest_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/logistics-manifests/items`, { params }),
  createManifest: (body: Record<string, unknown>) => api.post(`${BASE}/logistics-manifests`, body),
  addManifestItem: (body: Record<string, unknown>) => api.post(`${BASE}/logistics-manifests/items`, body),

  listChannels: (params?: { player_type?: string; active?: boolean }) =>
    api.get<{ items: ChannelRow[]; total: number }>(`${BASE}/integration-channels`, { params }),
  worldPlayersReview: () => api.get<WorldPlayersReview>(`${BASE}/integration-channels/world-review`),
  syncWorldPlayers: () => api.post<Record<string, number>>(`${BASE}/integration-channels/sync-world-players`),
  seedChannels: () => api.post<Record<string, number>>(`${BASE}/integration-channels/seed-catalog`),

  createOrderItem: (body: Record<string, unknown>) => api.post(`${BASE}/order-items`, body),
  updateOrderItem: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/order-items/${encodeURIComponent(id)}`, body),

  listCommissions: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/marketplace-commissions`, { params }),
  createCommission: (body: Record<string, unknown>) => api.post(`${BASE}/marketplace-commissions`, body),

  listLifecycleDeadlines: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/lifecycle-deadlines`, { params }),

  listOpsAudit: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ops-audit`, { params }),

  listFoodDelivery: (params?: { order_id?: string; platform_code?: string }) =>
    api.get<{ items: FoodDeliveryRow[]; total: number }>(`${BASE}/food-delivery-orders`, { params }),
  createFoodDelivery: (body: Record<string, unknown>) => api.post(`${BASE}/food-delivery-orders`, body),
  updateFoodDelivery: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/food-delivery-orders/${encodeURIComponent(id)}`, body),
}
