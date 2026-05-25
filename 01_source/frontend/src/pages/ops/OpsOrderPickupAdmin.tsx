import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  orderPickupAdminApi,
  type ChannelRow,
  type EcommercePartner,
  type LogisticsPartner,
  type OrderRow,
  type FoodDeliveryRow,
  type IntegrationHealthRow,
  type Order360,
  type OrderDispute,
  type OrderHoldRow,
  type OrderNotificationRow,
  type OrderReturnRow,
  type PaymentReconRow,
  type PaymentTransactionRow,
  type ItemSubstitutionRow,
  type GiftPickupRow,
  type SlaWatch,
  type WorldPlayersReview,
} from '../../api/orderPickupAdmin'
import { useOpsTabFromUrl } from '../../hooks/useOpsTabFromUrl'

const TABS = [
  'overview',
  'partners',
  'orders',
  'items',
  'allocations',
  'manifests',
  'channels',
  'omnichannel',
  'warehouse',
  'deadlines',
  'commissions',
  'credits',
  'food',
  'lookup',
  'sla',
  'disputes',
  'returns',
  'notifications',
  'reconciliation',
  'holds',
  'substitutions',
  'gifts',
  'payments',
  'integration',
] as const
type Tab = (typeof TABS)[number]
type PartnerSubTab = 'ecommerce' | 'logistics'

export default function OpsOrderPickupAdmin() {
  const location = useLocation()
  const ordersPath = location.pathname.includes('/ops/orders/admin') ? '/ops/orders/admin' : '/ops/order-pickup/admin'
  const { tab, setTab } = useOpsTabFromUrl(ordersPath, TABS, 'overview')
  const [partnerSubTab, setPartnerSubTab] = useState<PartnerSubTab>('ecommerce')
  const [ecItems, setEcItems] = useState<EcommercePartner[]>([])
  const [lgItems, setLgItems] = useState<LogisticsPartner[]>([])
  const [orders, setOrders] = useState<OrderRow[]>([])
  const [pickups, setPickups] = useState<unknown[]>([])
  const [credits, setCredits] = useState<unknown[]>([])
  const [outbox, setOutbox] = useState<unknown[]>([])
  const [fulfillment, setFulfillment] = useState<unknown[]>([])
  const [orderItems, setOrderItems] = useState<unknown[]>([])
  const [pickupEvents, setPickupEvents] = useState<unknown[]>([])
  const [pickupTokens, setPickupTokens] = useState<unknown[]>([])
  const [pickupAttempts, setPickupAttempts] = useState<unknown[]>([])
  const [domainOutbox, setDomainOutbox] = useState<unknown[]>([])
  const [omnichannel, setOmnichannel] = useState<unknown[]>([])
  const [warehouseOrders, setWarehouseOrders] = useState<unknown[]>([])
  const [hubSummary, setHubSummary] = useState<Record<string, number> | null>(null)
  const [allocations, setAllocations] = useState<unknown[]>([])
  const [manifests, setManifests] = useState<unknown[]>([])
  const [manifestItems, setManifestItems] = useState<unknown[]>([])
  const [channels, setChannels] = useState<ChannelRow[]>([])
  const [worldReview, setWorldReview] = useState<WorldPlayersReview | null>(null)
  const [channelFilter, setChannelFilter] = useState('')
  const [channelGroupFilter, setChannelGroupFilter] = useState('')
  const [foodOrders, setFoodOrders] = useState<FoodDeliveryRow[]>([])
  const [foodForm, setFoodForm] = useState({
    order_id: 'ord-seed-demo-001',
    platform_code: 'RAPPI',
    temperature_zone: 'HOT',
  })
  const [deadlines, setDeadlines] = useState<unknown[]>([])
  const [commissions, setCommissions] = useState<unknown[]>([])
  const [slaWatches, setSlaWatches] = useState<SlaWatch[]>([])
  const [disputes, setDisputes] = useState<OrderDispute[]>([])
  const [integrationHealth, setIntegrationHealth] = useState<IntegrationHealthRow[]>([])
  const [orderReturns, setOrderReturns] = useState<OrderReturnRow[]>([])
  const [orderNotifications, setOrderNotifications] = useState<OrderNotificationRow[]>([])
  const [paymentRecon, setPaymentRecon] = useState<PaymentReconRow[]>([])
  const [orderHolds, setOrderHolds] = useState<OrderHoldRow[]>([])
  const [substitutions, setSubstitutions] = useState<ItemSubstitutionRow[]>([])
  const [giftPickups, setGiftPickups] = useState<GiftPickupRow[]>([])
  const [paymentTxs, setPaymentTxs] = useState<PaymentTransactionRow[]>([])
  const [lookupOrderId, setLookupOrderId] = useState('ord-seed-demo-001')
  const [order360, setOrder360] = useState<Order360 | null>(null)
  const [allocForm, setAllocForm] = useState({ order_id: 'ord-seed-demo-001', locker_id: 'LOCKER-DEMO-01', slot: 12 })
  const [itemForm, setItemForm] = useState({ order_id: 'ord-seed-demo-001', sku_id: 'SKU-NEW', unit_amount_cents: 1990, quantity: 1 })
  const [partnerForm, setPartnerForm] = useState({ name: '', code: '' })
  const [omniForm, setOmniForm] = useState({
    order_id: 'ord-seed-demo-001',
    store_id: 'store-magalu-demo-01',
    pickup_type: 'LOCKER_DELIVERY',
  })
  const [warehouseForm, setWarehouseForm] = useState({
    order_id: 'ord-seed-demo-001',
    fulfillment_center_id: 'fc-sp-001',
    carrier: 'DHL',
  })
  const [orderForm, setOrderForm] = useState({
    amount_cents: 4990,
    ecommerce_partner_id: 'ec-ops-001',
    totem_id: 'TOTEM-OPS',
  })
  const [creditForm, setCreditForm] = useState({ order_id: 'ord-seed-demo-001', user_id: 'usr-demo', amount_cents: 500 })
  const [selectedId, setSelectedId] = useState('')
  const [partnerType, setPartnerType] = useState('ECOMMERCE')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const [ec, lg, ord, pk, cr, ob, ft, oi, pe, pt, pa, dom, omni, wh, hub, alloc, mf, mfi, ch, dl, comm, wrev, food, sla, disp, health, ret, notif, recon, holds, subs, gifts, paytx] =
        await Promise.all([
        orderPickupAdminApi.listEcommerce(),
        orderPickupAdminApi.listLogistics(),
        orderPickupAdminApi.listOrders(),
        orderPickupAdminApi.listPickups(),
        orderPickupAdminApi.listCredits(),
        orderPickupAdminApi.listOutbox(),
        orderPickupAdminApi.listFulfillment(),
        orderPickupAdminApi.listOrderItems(),
        orderPickupAdminApi.listPickupEvents(),
        orderPickupAdminApi.listPickupTokens(),
        orderPickupAdminApi.listPickupAttempts(),
        orderPickupAdminApi.listDomainOutbox(),
        orderPickupAdminApi.listOmnichannel(),
        orderPickupAdminApi.listFulfillmentOrders(),
        orderPickupAdminApi.hubSummary(),
        orderPickupAdminApi.listAllocations(),
        orderPickupAdminApi.listManifests(),
        orderPickupAdminApi.listManifestItems(),
        orderPickupAdminApi.listChannels(),
        orderPickupAdminApi.listLifecycleDeadlines(),
        orderPickupAdminApi.listCommissions(),
        orderPickupAdminApi.worldPlayersReview(),
        orderPickupAdminApi.listFoodDelivery(),
        orderPickupAdminApi.listSlaWatches(),
        orderPickupAdminApi.listDisputes(),
        orderPickupAdminApi.listIntegrationHealth(),
        orderPickupAdminApi.listOrderReturns(),
        orderPickupAdminApi.listOrderNotifications(),
        orderPickupAdminApi.listPaymentReconciliation(),
        orderPickupAdminApi.listOrderHolds(),
        orderPickupAdminApi.listItemSubstitutions(),
        orderPickupAdminApi.listGiftPickups(),
        orderPickupAdminApi.listPaymentTransactions(),
      ])
      setEcItems(ec.data.partners ?? [])
      setLgItems(lg.data.partners ?? [])
      setOrders(ord.data.items ?? [])
      setPickups(pk.data.items ?? [])
      setCredits(cr.data.items ?? [])
      setOutbox(ob.data.items ?? [])
      setFulfillment(ft.data.items ?? [])
      setOrderItems(oi.data.items ?? [])
      setPickupEvents(pe.data.items ?? [])
      setPickupTokens(pt.data.items ?? [])
      setPickupAttempts(pa.data.items ?? [])
      setDomainOutbox(dom.data.items ?? [])
      setOmnichannel(omni.data.items ?? [])
      setWarehouseOrders(wh.data.items ?? [])
      setHubSummary(hub.data)
      setAllocations(alloc.data.items ?? [])
      setManifests(mf.data.items ?? [])
      setManifestItems(mfi.data.items ?? [])
      setChannels(ch.data.items ?? [])
      setDeadlines(dl.data.items ?? [])
      setCommissions(comm.data.items ?? [])
      setWorldReview(wrev.data)
      setFoodOrders(food.data.items ?? [])
      setSlaWatches(sla.data.items ?? [])
      setDisputes(disp.data.items ?? [])
      setIntegrationHealth(health.data.items ?? [])
      setOrderReturns(ret.data.items ?? [])
      setOrderNotifications(notif.data.items ?? [])
      setPaymentRecon(recon.data.items ?? [])
      setOrderHolds(holds.data.items ?? [])
      setSubstitutions(subs.data.items ?? [])
      setGiftPickups(gifts.data.items ?? [])
      setPaymentTxs(paytx.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [])

  const onSeed = async () => {
    setLoading(true)
    try {
      await orderPickupAdminApi.seed()
      setMessage('Seed aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreatePartner = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const api =
        partnerSubTab === 'ecommerce' ? orderPickupAdminApi.createEcommerce : orderPickupAdminApi.createLogistics
      const body =
        partnerSubTab === 'ecommerce'
          ? { ...partnerForm, integration_type: 'REST', status: 'ACTIVE' }
          : { ...partnerForm, integration_type: 'REST' }
      const { data } = await api(body)
      setMessage(`Parceiro ${data.code} criado.`)
      setSelectedId(data.id)
      setPartnerType(partnerSubTab === 'ecommerce' ? 'ECOMMERCE' : 'LOGISTICS')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar parceiro')
    } finally {
      setLoading(false)
    }
  }

  const onCreateOrder = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await orderPickupAdminApi.createOrder({
        ...orderForm,
        channel: 'KIOSK',
        region: 'BR',
        status: 'PENDING',
        payment_status: 'PENDING',
      })
      setMessage(`Pedido ${data.id} criado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar pedido')
    } finally {
      setLoading(false)
    }
  }

  const onCreateAllocation = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await orderPickupAdminApi.createAllocation({
        ...allocForm,
        state: 'RESERVED_PAID_PENDING_PICKUP',
      })
      setMessage('Alocação criada.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha alocação')
    } finally {
      setLoading(false)
    }
  }

  const onCreateItem = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await orderPickupAdminApi.createOrderItem(itemForm)
      setMessage('Item criado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha item')
    } finally {
      setLoading(false)
    }
  }

  const onCreateFood = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await orderPickupAdminApi.createFoodDelivery({ ...foodForm, status: 'PLACED' })
      setMessage('Food delivery criado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha food delivery')
    } finally {
      setLoading(false)
    }
  }

  const onSyncWorldPlayers = async () => {
    setLoading(true)
    try {
      const { data } = await orderPickupAdminApi.syncWorldPlayers()
      setMessage(
        `Players mundiais: +${data.channels_created ?? 0} canais, ${data.ecommerce ?? 0} e-commerce, ${data.logistics ?? 0} logística.`,
      )
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha sync players')
    } finally {
      setLoading(false)
    }
  }

  const onCreateOmnichannel = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await orderPickupAdminApi.createOmnichannel({ ...omniForm, status: 'PENDING' })
      setMessage('Omnichannel criado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha omnichannel')
    } finally {
      setLoading(false)
    }
  }

  const onCreateWarehouse = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await orderPickupAdminApi.createFulfillmentOrder({ ...warehouseForm, status: 'PENDING' })
      setMessage('Fulfillment CD criado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha fulfillment CD')
    } finally {
      setLoading(false)
    }
  }

  const onCreateCredit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await orderPickupAdminApi.createCredit({
        ...creditForm,
        type: 'GOODWILL',
        currency: 'BRL',
        status: 'AVAILABLE',
      })
      setMessage('Crédito criado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar crédito')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedId || !webhookUrl) return
    setLoading(true)
    try {
      await orderPickupAdminApi.configureWebhook(selectedId, partnerType, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['ORDER_PAID', 'ORDER_PICKED_UP'],
      })
      setMessage('Webhook configurado.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedId) return
    setLoading(true)
    try {
      const { data } = await orderPickupAdminApi.rotateApiKey(selectedId, partnerType)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…).`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar chave')
    } finally {
      setLoading(false)
    }
  }

  const onReplayPartner = async (id: string) => {
    setLoading(true)
    try {
      await orderPickupAdminApi.replayOutbox(id)
      setMessage(`Outbox parceiro ${id} reenfileirado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no replay')
    } finally {
      setLoading(false)
    }
  }

  const onReplayDomain = async (id: string) => {
    setLoading(true)
    try {
      await orderPickupAdminApi.replayDomainOutbox(id)
      setMessage(`Domain outbox ${id} reenfileirado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no replay domain')
    } finally {
      setLoading(false)
    }
  }

  const partnerItems = partnerType === 'ECOMMERCE' ? ecItems : lgItems

  useEffect(() => {
    void load()
  }, [load])

  const onLookup360 = async () => {
    if (!lookupOrderId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const r = await orderPickupAdminApi.order360(lookupOrderId.trim())
      setOrder360(r.data)
      setMessage(`Order 360 · health ${r.data.health_score}`)
    } catch (err: unknown) {
      setOrder360(null)
      setError(err instanceof Error ? err.message : 'Pedido não encontrado')
    } finally {
      setLoading(false)
    }
  }

  const onRunReconciliation = async () => {
    setLoading(true)
    try {
      const r = await orderPickupAdminApi.runPaymentReconciliation()
      setMessage(
        `Recon: ${r.data.mismatched} divergências · gateway ${r.data.used_gateway} pedidos · ${r.data.created}+${r.data.updated} linhas`,
      )
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha reconciliação')
    } finally {
      setLoading(false)
    }
  }

  const onSyncPaymentTx = async () => {
    setLoading(true)
    try {
      const r = await orderPickupAdminApi.syncPaymentTransactions()
      if (r.data.error) {
        setMessage(`Sync: ${r.data.error} (use seed local ou PAYMENTS_ADMIN_BASE_URL)`)
      } else {
        setMessage(`Sync gateway: ${r.data.synced} transações`)
      }
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha sync payment_transactions')
    } finally {
      setLoading(false)
    }
  }

  const onSyncSla = async () => {
    setLoading(true)
    try {
      const r = await orderPickupAdminApi.syncSlaWatches()
      setMessage(`SLA sync: +${r.data.created} criados, ${r.data.breached} violados`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha SLA sync')
    } finally {
      setLoading(false)
    }
  }

  const tableRows =
    tab === 'overview' || tab === 'lookup'
      ? []
      : tab === 'omnichannel'
        ? omnichannel.map((x) => {
            const row = x as { id: string; order_id: string; store_id: string; pickup_type: string; status: string }
            return {
              key: `omni-${row.id}`,
              tipo: 'omnichannel',
              id: row.id,
              detalhe: `${row.store_id} · ${row.pickup_type} · ${row.status} · order ${row.order_id}`,
            }
          })
        : tab === 'warehouse'
          ? warehouseOrders.map((x) => {
              const row = x as { id: string; order_id: string; status: string; carrier?: string; tracking_code?: string }
              return {
                key: `wh-${row.id}`,
                tipo: 'fulfillment_cd',
                id: row.id,
                detalhe: `${row.status} · ${row.carrier ?? '—'} · ${row.tracking_code ?? '—'} · order ${row.order_id}`,
              }
            })
          : tab === 'allocations'
            ? allocations.map((x) => {
                const row = x as { id: string; order_id: string; slot: number; state: string; locker_id?: string }
                return {
                  key: `alloc-${row.id}`,
                  tipo: 'allocation',
                  id: row.id,
                  detalhe: `slot ${row.slot} · ${row.state} · ${row.locker_id ?? '—'} · order ${row.order_id}`,
                }
              })
            : tab === 'manifests'
              ? [
                  ...manifests.map((x) => {
                    const row = x as { id: string; status: string; locker_id: string; expected_parcel_count: number }
                    return {
                      key: `mf-${row.id}`,
                      tipo: 'manifest',
                      id: row.id,
                      detalhe: `${row.status} · ${row.locker_id} · esperado ${row.expected_parcel_count}`,
                    }
                  }),
                  ...manifestItems.map((x) => {
                    const row = x as { id: string; manifest_id: string; tracking_code: string; status: string }
                    return {
                      key: `mfi-${row.id}`,
                      tipo: 'manifest_item',
                      id: row.tracking_code,
                      detalhe: `${row.status} · manifest ${row.manifest_id}`,
                    }
                  }),
                ]
              : tab === 'food'
                ? foodOrders.map((row) => ({
                    key: `fd-${row.id}`,
                    tipo: 'food',
                    id: row.platform_code,
                    detalhe: `${row.status} · ${row.temperature_zone} · order ${row.order_id} · ${row.external_order_ref ?? '—'}`,
                  }))
                : tab === 'channels'
                  ? (() => {
                      let list = channels
                      if (channelFilter) {
                        list = list.filter(
                          (c) => c.code.includes(channelFilter.toUpperCase()) || c.player_type === channelFilter,
                        )
                      }
                      if (channelGroupFilter) {
                        list = list.filter((c) =>
                          worldReview?.players.find((p) => p.code === c.code)?.prompt_group === channelGroupFilter,
                        )
                      }
                      return list
                    })().map((row) => {
                    const links = (row.linked_partners ?? []).map((l) => `${l.kind}:${l.code}`).join(', ')
                    return {
                      key: `ch-${row.id}`,
                      tipo: row.player_type,
                      id: row.code,
                      detalhe: `${row.name} · ${row.country} · ${row.review_status ?? '—'} · ${row.markets?.join('/') ?? ''} · ${links || 'sem vínculo'}`,
                    }
                  })
                  : tab === 'items'
                  ? orderItems.map((i) => {
                      const row = i as { id: string; order_id: string; sku_id: string; quantity: number; item_status: string }
                      return {
                        key: `oi-${row.id}`,
                        tipo: 'item',
                        id: row.sku_id,
                        detalhe: `order ${row.order_id} · qty ${row.quantity} · ${row.item_status}`,
                      }
                    })
                  : tab === 'deadlines'
                    ? deadlines.map((x) => {
                        const row = x as { id: string; order_id: string; deadline_type: string; status: string; due_at: string }
                        return {
                          key: `dl-${row.id}`,
                          tipo: 'deadline',
                          id: row.deadline_type,
                          detalhe: `${row.status} · order ${row.order_id} · ${row.due_at}`,
                        }
                      })
                    : tab === 'sla'
                      ? slaWatches.map((row) => ({
                          key: `sla-${row.id}`,
                          tipo: row.watch_type,
                          id: row.order_id,
                          detalhe: `${row.status} · due ${row.due_at}${row.breach_reason ? ` · ${row.breach_reason}` : ''}`,
                        }))
                      : tab === 'disputes'
                        ? disputes.map((row) => ({
                            key: `disp-${row.id}`,
                            tipo: row.dispute_type,
                            id: row.id,
                            detalhe: `${row.status} · order ${row.order_id} · ${row.amount_cents != null ? `R$ ${(row.amount_cents / 100).toFixed(2)}` : '—'}`,
                          }))
                        : tab === 'returns'
                          ? orderReturns.map((row) => ({
                              key: `ret-${row.id}`,
                              tipo: row.return_type,
                              id: row.order_id,
                              detalhe: `${row.status} · ${row.reason_code ?? '—'} · ${row.refund_amount_cents != null ? `R$ ${(row.refund_amount_cents / 100).toFixed(2)}` : '—'}`,
                            }))
                          : tab === 'notifications'
                            ? orderNotifications.map((row) => ({
                                key: `ntf-${row.id}`,
                                tipo: row.channel,
                                id: row.template_code,
                                detalhe: `${row.status} · order ${row.order_id} · ${row.sent_at}`,
                              }))
                            : tab === 'reconciliation'
                              ? paymentRecon.map((row) => ({
                                  key: `rec-${row.id}`,
                                  tipo: row.status,
                                  id: row.order_id,
                                  detalhe: `esp ${row.expected_cents} · cap ${row.captured_cents} · fee ${row.fee_cents}${row.mismatch_reason ? ` · ${row.mismatch_reason}` : ''}`,
                                }))
                              : tab === 'substitutions'
                                ? substitutions.map((row) => ({
                                    key: `sub-${row.id}`,
                                    tipo: row.reason_code,
                                    id: row.order_id,
                                    detalhe: `${row.status} · ${row.original_sku_id} → ${row.substitute_sku_id} · qty ${row.quantity}`,
                                  }))
                                : tab === 'gifts'
                                  ? giftPickups.map((row) => ({
                                      key: `gift-${row.id}`,
                                      tipo: 'gift',
                                      id: row.order_id,
                                      detalhe: `${row.status} · ${row.recipient_name} · código ${row.pickup_authorization_code ?? '—'}`,
                                    }))
                                  : tab === 'payments'
                                    ? paymentTxs.map((row) => ({
                                        key: `ptx-${row.id}`,
                                        tipo: row.gateway,
                                        id: row.order_id,
                                        detalhe: `${row.status} · R$ ${(row.amount_cents / 100).toFixed(2)} · fee ${row.gateway_fee_cents} · ${row.source}`,
                                      }))
                                    : tab === 'holds'
                                ? orderHolds.map((row) => ({
                                    key: `hold-${row.id}`,
                                    tipo: row.hold_type,
                                    id: row.order_id,
                                    detalhe: `${row.status} · ${row.placed_by} · ${row.reason ?? '—'}`,
                                    replay: row.status === 'ACTIVE' ? () => void orderPickupAdminApi.releaseOrderHold(row.id).then(() => load()) : undefined,
                                  }))
                                : tab === 'commissions'
                      ? commissions.map((x) => {
                          const row = x as {
                            id: string
                            order_id: string
                            commission_amount_cents: number
                            status: string
                            seller_id: string
                          }
                          return {
                            key: `mc-${row.id}`,
                            tipo: 'commission',
                            id: row.id,
                            detalhe: `${row.status} · R$ ${(row.commission_amount_cents / 100).toFixed(2)} · seller ${row.seller_id} · order ${row.order_id}`,
                          }
                        })
                      : tab === 'partners'
      ? [
          ...ecItems.map((p) => ({ key: `ec-${p.id}`, tipo: 'EC', id: p.code, detalhe: `${p.name} · ${p.status}` })),
          ...lgItems.map((p) => ({ key: `lg-${p.id}`, tipo: 'LG', id: p.code, detalhe: p.name })),
        ]
      : tab === 'orders'
        ? [
            ...orders.map((o) => ({
              key: `ord-${o.id}`,
              tipo: 'order',
              id: o.id,
              detalhe: `${o.status}/${o.payment_status} · R$ ${(o.amount_cents / 100).toFixed(2)}`,
            })),
            ...pickups.map((p) => {
              const row = p as { id: string; order_id: string; status: string; lifecycle_stage: string }
              return {
                key: `pkp-${row.id}`,
                tipo: 'pickup',
                id: row.id,
                detalhe: `${row.status} · ${row.lifecycle_stage} · order ${row.order_id}`,
              }
            }),
          ]
        : tab === 'credits'
          ? credits.map((c) => {
              const row = c as { id: string; order_id: string; amount_cents: number; status: string; type: string }
              return {
                key: `crd-${row.id}`,
                tipo: 'credit',
                id: row.id,
                detalhe: `${row.type} · ${row.status} · R$ ${(row.amount_cents / 100).toFixed(2)} · order ${row.order_id}`,
              }
            })
          : [
              ...integrationHealth.map((row) => ({
                key: `ih-${row.id}`,
                tipo: 'health',
                id: row.channel_code,
                detalhe: `${row.check_type} · ${row.status} · ${row.latency_ms ?? '—'}ms · ${row.checked_at}`,
              })),
              ...outbox.map((x) => {
                const row = x as { id: string; event_type: string; status: string; order_id: string }
                return {
                  key: `pob-${row.id}`,
                  tipo: 'partner_outbox',
                  id: row.id,
                  detalhe: `${row.event_type} · ${row.status} · ${row.order_id}`,
                  replay: () => onReplayPartner(row.id),
                }
              }),
              ...domainOutbox.map((x) => {
                const row = x as { id: string; event_name?: string; status: string; aggregate_id?: string }
                return {
                  key: `dob-${row.id}`,
                  tipo: 'domain_outbox',
                  id: row.id,
                  detalhe: `${row.event_name ?? '—'} · ${row.status} · ${row.aggregate_id ?? '—'}`,
                  replay: () => onReplayDomain(row.id),
                }
              }),
              ...pickupEvents.map((x) => {
                const row = x as { id: string; pickup_id: string; event_type: string }
                return { key: `pe-${row.id}`, tipo: 'pickup_event', id: row.id, detalhe: `${row.event_type} · ${row.pickup_id}` }
              }),
              ...pickupTokens.map((x) => {
                const row = x as { id: string; order_id: string; is_active: boolean }
                return {
                  key: `pt-${row.id}`,
                  tipo: 'token',
                  id: row.id,
                  detalhe: `order ${row.order_id} · ${row.is_active ? 'ativo' : 'inativo'}`,
                }
              }),
              ...pickupAttempts.map((x) => {
                const row = x as { id: string; order_id: string; ok: boolean }
                return {
                  key: `pa-${row.id}`,
                  tipo: 'attempt',
                  id: row.id,
                  detalhe: `order ${row.order_id} · ${row.ok ? 'ok' : 'fail'}`,
                }
              }),
              ...fulfillment.map((x) => {
                const row = x as { id: string; order_id: string; status: string }
                return { key: `ft-${row.id}`, tipo: 'fulfillment', id: row.order_id, detalhe: row.status }
              }),
            ]

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap justify-end gap-2 text-sm">
        <Link to="/ops/tenants/admin" className="text-indigo-600 hover:underline">
          Tenants
        </Link>
        <Link to="/ops/partners/admin" className="text-indigo-600 hover:underline">
          Parceiros
        </Link>
        <Link to="/ops/payment-gateway/admin" className="text-indigo-600 hover:underline">
          Payment Gateway
        </Link>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Pedidos</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Hub pedidos: parceiros (Magalu, ML, Amazon, DHL, DPD), omnichannel, fulfillment CD, pickups, créditos e
            integração outbox.
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSeed()} className="ellan-btn-outline">
            Seed
          </button>
          <button
            type="button"
            onClick={() => void load()}
            className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            {loading ? 'Atualizando…' : 'Listar'}
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-gray-500">Processando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="rounded border border-red-300 bg-red-50 p-2 text-sm text-red-700">{error}</p>}
      {lastApiKey && (
        <p className="rounded border border-amber-300 bg-amber-50 p-2 font-mono text-xs text-amber-900">
          API key: {lastApiKey}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {(
          [
            ['overview', 'Hub'],
            ['lookup', '360'],
            ['orders', 'Pedidos'],
            ['items', 'Itens'],
            ['allocations', 'Alocações'],
            ['channels', 'Players'],
            ['food', 'Food'],
            ['omnichannel', 'Omnichannel'],
            ['warehouse', 'CD'],
            ['manifests', 'Manifestos'],
            ['deadlines', 'Deadlines'],
            ['sla', 'SLA'],
            ['disputes', 'Disputas'],
            ['returns', 'Devoluções'],
            ['notifications', 'Notificações'],
            ['reconciliation', 'Pagamentos'],
            ['holds', 'Holds'],
            ['substitutions', 'Substituições'],
            ['gifts', 'Gift'],
            ['payments', 'Gateway'],
            ['commissions', 'Comissões'],
            ['credits', 'Créditos'],
            ['partners', 'Parceiros'],
            ['integration', 'Integração'],
          ] as const
        ).map(([t, label]) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'border border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'overview' && hubSummary && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(
            [
              ['Pedidos', hubSummary.orders],
              ['Pickups', hubSummary.pickups],
              ['Outbox parceiro (pend.)', hubSummary.partner_outbox_pending],
              ['Domain outbox (pend.)', hubSummary.domain_outbox_pending],
              ['Omnichannel', hubSummary.omnichannel],
              ['Fulfillment CD', hubSummary.fulfillment_orders],
              ['Tracking pickup', hubSummary.fulfillment_tracking],
              ['Créditos', hubSummary.credits],
              ['Alocações', hubSummary.allocations ?? 0],
              ['Manifestos', hubSummary.logistics_manifests ?? 0],
              ['Players', hubSummary.integration_channels ?? 0],
              ['Comissões', hubSummary.marketplace_commissions ?? 0],
              ['Deadlines pend.', hubSummary.lifecycle_deadlines_pending ?? 0],
              ['Itens', hubSummary.order_items ?? 0],
              ['Food delivery', hubSummary.food_delivery_orders ?? 0],
              ['Timeline', hubSummary.timeline_events ?? 0],
              ['SLA ativos', hubSummary.sla_watches_active ?? 0],
              ['SLA violados', hubSummary.sla_watches_breached ?? 0],
              ['Disputas abertas', hubSummary.disputes_open ?? 0],
              ['Devoluções abertas', hubSummary.returns_open ?? 0],
              ['Recon divergente', hubSummary.payment_recon_mismatch ?? 0],
              ['Holds ativos', hubSummary.ops_holds_active ?? 0],
              ['Notificações', hubSummary.notifications_sent ?? 0],
              ['Substituições pend.', hubSummary.substitutions_pending ?? 0],
              ['Gifts p/ verificar', hubSummary.gifts_pending_verification ?? 0],
              ['Tx gateway', hubSummary.payment_transactions ?? 0],
            ] as const
          ).map(([label, value]) => (
            <div
              key={label}
              className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900"
            >
              <p className="text-xs uppercase text-slate-400">{label}</p>
              <p className="text-2xl font-semibold text-slate-100">{value}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'lookup' && (
        <section className="space-y-4 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-sm text-slate-400">
            Visão consolidada: timeline, SLA, disputas, riscos e health score do pedido.
          </p>
          <div className="flex flex-wrap gap-2">
            <input
              className="ellan-field min-w-[240px]"
              placeholder="order_id"
              value={lookupOrderId}
              onChange={(e) => setLookupOrderId(e.target.value)}
            />
            <button type="button" onClick={() => void onLookup360()} className="rounded-lg bg-indigo-600 px-3 py-2 text-sm text-white">
              Buscar 360
            </button>
          </div>
          {order360 && (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-slate-600 p-3">
                <p className="text-xs text-slate-400">Health score</p>
                <p className="text-3xl font-semibold text-emerald-400">{order360.health_score}</p>
                <p className="mt-2 text-sm text-slate-300">
                  {order360.order.status as string} / {order360.order.payment_status as string} · R${' '}
                  {((order360.order.amount_cents as number) / 100).toFixed(2)}
                </p>
                {order360.risk_flags.length > 0 && (
                  <p className="mt-2 text-xs text-amber-400">Riscos: {order360.risk_flags.join(', ')}</p>
                )}
              </div>
              <div className="rounded-lg border border-slate-600 p-3 text-sm text-slate-300">
                <p className="mb-2 font-medium text-slate-200">Contagens</p>
                <ul className="space-y-1">
                  {Object.entries(order360.counts).map(([k, v]) => (
                    <li key={k}>
                      {k}: {v}
                    </li>
                  ))}
                </ul>
                <p className="mt-2">
                  SLA ativo {order360.sla.active} · violado {order360.sla.breached} · disputas {order360.disputes_open}
                </p>
              </div>
              <div className="md:col-span-2 rounded-lg border border-slate-600 p-3">
                <p className="mb-2 text-sm font-medium text-slate-200">Timeline</p>
                <ul className="max-h-48 space-y-1 overflow-y-auto text-xs text-slate-400">
                  {order360.timeline.map((ev) => (
                    <li key={ev.id}>
                      [{ev.severity}] {ev.title} · {ev.event_type} · {ev.occurred_at}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </section>
      )}

      {tab === 'sla' && (
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSyncSla()} className="ellan-btn-outline">
            Sincronizar SLA (deadlines → watches)
          </button>
        </div>
      )}

      {tab === 'reconciliation' && (
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => void onSyncPaymentTx()} className="ellan-btn-outline">
            Sync payment_transactions (payments-admin)
          </button>
          <button type="button" onClick={() => void onRunReconciliation()} className="ellan-btn-outline">
            Reconciliar (soma gateway vs pedido)
          </button>
        </div>
      )}

      {tab === 'payments' && (
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSyncPaymentTx()} className="ellan-btn-outline">
            Sync do payments-admin
          </button>
        </div>
      )}

      {tab === 'partners' && (
        <section className="space-y-4 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPartnerSubTab('ecommerce')}
              className={`rounded px-3 py-1 text-sm ${partnerSubTab === 'ecommerce' ? 'bg-indigo-600 text-white' : 'border border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700'}`}
            >
              E-commerce
            </button>
            <button
              type="button"
              onClick={() => setPartnerSubTab('logistics')}
              className={`rounded px-3 py-1 text-sm ${partnerSubTab === 'logistics' ? 'bg-indigo-600 text-white' : 'border border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700'}`}
            >
              Logística
            </button>
          </div>
          <form onSubmit={onCreatePartner} className="grid gap-3 md:grid-cols-3">
            <input
              className="ellan-field"
              placeholder="Nome"
              required
              value={partnerForm.name}
              onChange={(e) => setPartnerForm((f) => ({ ...f, name: e.target.value }))}
            />
            <input
              className="ellan-field"
              placeholder="Código"
              required
              value={partnerForm.code}
              onChange={(e) => setPartnerForm((f) => ({ ...f, code: e.target.value }))}
            />
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
              Criar {partnerSubTab === 'ecommerce' ? 'e-commerce' : 'logística'}
            </button>
          </form>
          <div className="flex flex-wrap gap-2">
            <select
              className="ellan-field"
              value={partnerType}
              onChange={(e) => setPartnerType(e.target.value)}
            >
              <option value="ECOMMERCE">ECOMMERCE</option>
              <option value="LOGISTICS">LOGISTICS</option>
            </select>
            <select
              className="ellan-field"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              <option value="">Parceiro</option>
              {partnerItems.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code}
                </option>
              ))}
            </select>
            <input
              className="min-w-[14rem] flex-1 ellan-field"
              placeholder="Webhook URL"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
            />
            <button type="button" onClick={() => void onWebhook()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
              Salvar webhook
            </button>
            <button type="button" onClick={() => void onRotateKey()} className="rounded bg-amber-600 px-3 py-1 text-sm text-white">
              Rotacionar API key
            </button>
          </div>
        </section>
      )}

      {tab === 'allocations' && (
        <form
          onSubmit={onCreateAllocation}
          className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900"
        >
          <input
            className="ellan-field"
            placeholder="order_id"
            value={allocForm.order_id}
            onChange={(e) => setAllocForm((f) => ({ ...f, order_id: e.target.value }))}
          />
          <input
            className="ellan-field"
            placeholder="locker_id"
            value={allocForm.locker_id}
            onChange={(e) => setAllocForm((f) => ({ ...f, locker_id: e.target.value }))}
          />
          <input
            type="number"
            className="w-20 ellan-field"
            value={allocForm.slot}
            onChange={(e) => setAllocForm((f) => ({ ...f, slot: Number(e.target.value) }))}
          />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar alocação
          </button>
        </form>
      )}

      {tab === 'items' && (
        <form
          onSubmit={onCreateItem}
          className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900"
        >
          <input
            className="ellan-field"
            placeholder="order_id"
            value={itemForm.order_id}
            onChange={(e) => setItemForm((f) => ({ ...f, order_id: e.target.value }))}
          />
          <input
            className="ellan-field"
            placeholder="sku_id"
            value={itemForm.sku_id}
            onChange={(e) => setItemForm((f) => ({ ...f, sku_id: e.target.value }))}
          />
          <input
            type="number"
            className="w-28 ellan-field"
            value={itemForm.unit_amount_cents}
            onChange={(e) => setItemForm((f) => ({ ...f, unit_amount_cents: Number(e.target.value) }))}
          />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar item
          </button>
        </form>
      )}

      {tab === 'channels' && (
        <div className="space-y-4">
          {worldReview && (
            <div className="rounded-xl border border-indigo-500/40 bg-indigo-950/30 p-4">
              <p className="text-sm font-medium text-indigo-200">
                Catálogo: {worldReview.catalog_configured}/{worldReview.catalog_total} · P3:{' '}
                {worldReview.prompt3_configured}/{worldReview.prompt3_total} · P4:{' '}
                {worldReview.prompt4_configured}/{worldReview.prompt4_total}{' '}
                {worldReview.prompt4_complete ? '✓' : '…'}
              </p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-300">
                {Object.entries(worldReview.by_type).map(([t, n]) => (
                  <span key={t} className="rounded bg-slate-800 px-2 py-1">
                    {t}: {n}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
            <button type="button" onClick={() => void onSyncWorldPlayers()} className="rounded bg-indigo-600 px-3 py-2 text-sm text-white">
              Sync catálogo mundial (28 players)
            </button>
            <select
              className="ellan-field"
              value={channelGroupFilter}
              onChange={(e) => setChannelGroupFilter(e.target.value)}
            >
              <option value="">P3 + P4</option>
              <option value="P3">Prompt 3</option>
              <option value="P4">Prompt 4</option>
            </select>
            <select
              className="ellan-field"
              value={channelFilter}
              onChange={(e) => setChannelFilter(e.target.value)}
            >
              <option value="">Todos os tipos</option>
              <option value="MARKETPLACE">MARKETPLACE</option>
              <option value="COLLECTION_POINT">COLLECTION_POINT</option>
              <option value="LOCKER_NETWORK">LOCKER_NETWORK</option>
              <option value="CARRIER">CARRIER</option>
              <option value="AGGREGATOR">AGGREGATOR</option>
              <option value="FOOD_DELIVERY">FOOD_DELIVERY</option>
            </select>
          </div>
          {worldReview ? (
            <div className="grid gap-2 md:grid-cols-2">
              {worldReview.players.map((p) => (
                <div
                  key={p.code}
                  className={`rounded-lg border p-3 text-sm ${p.configured ? 'border-emerald-600/50 bg-emerald-950/20' : 'border-amber-600/50 bg-amber-950/20'}`}
                >
                  <div className="font-semibold text-slate-100">
                    {p.name}{' '}
                    <span className="text-xs text-slate-400">
                      ({p.code}) · {p.prompt_group ?? '—'}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400">
                    {p.player_type} · {p.country} · {p.review_status}
                  </div>
                  <div className="mt-1 text-xs text-slate-300">
                    EC: {p.ecommerce_partner_code ?? '—'} · LG: {p.logistics_partner_code ?? '—'}
                  </div>
                  <div className="text-xs text-slate-500">{p.pickup_modes?.join(' · ')}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      )}

      {tab === 'food' && (
        <form
          onSubmit={onCreateFood}
          className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900"
        >
          <input
            className="ellan-field"
            placeholder="order_id"
            value={foodForm.order_id}
            onChange={(e) => setFoodForm((f) => ({ ...f, order_id: e.target.value }))}
          />
          <select
            className="ellan-field"
            value={foodForm.platform_code}
            onChange={(e) => setFoodForm((f) => ({ ...f, platform_code: e.target.value }))}
          >
            {['IFOOD', 'RAPPI', 'UBER_EATS', 'GLOVO', 'DOORDASH'].map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <select
            className="ellan-field"
            value={foodForm.temperature_zone}
            onChange={(e) => setFoodForm((f) => ({ ...f, temperature_zone: e.target.value }))}
          >
            <option value="HOT">HOT</option>
            <option value="COLD">COLD</option>
          </select>
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar handoff food → locker
          </button>
        </form>
      )}

      {tab === 'omnichannel' && (
        <form
          onSubmit={onCreateOmnichannel}
          className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900"
        >
          <input
            className="ellan-field"
            placeholder="order_id"
            value={omniForm.order_id}
            onChange={(e) => setOmniForm((f) => ({ ...f, order_id: e.target.value }))}
          />
          <input
            className="ellan-field"
            placeholder="store_id"
            value={omniForm.store_id}
            onChange={(e) => setOmniForm((f) => ({ ...f, store_id: e.target.value }))}
          />
          <select
            className="ellan-field"
            value={omniForm.pickup_type}
            onChange={(e) => setOmniForm((f) => ({ ...f, pickup_type: e.target.value }))}
          >
            <option value="LOCKER_DELIVERY">LOCKER_DELIVERY</option>
            <option value="STORE_PICKUP">STORE_PICKUP</option>
            <option value="HOME_DELIVERY">HOME_DELIVERY</option>
          </select>
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar omnichannel
          </button>
        </form>
      )}

      {tab === 'warehouse' && (
        <form
          onSubmit={onCreateWarehouse}
          className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900"
        >
          <input
            className="ellan-field"
            placeholder="order_id"
            value={warehouseForm.order_id}
            onChange={(e) => setWarehouseForm((f) => ({ ...f, order_id: e.target.value }))}
          />
          <input
            className="ellan-field"
            placeholder="fulfillment_center_id"
            value={warehouseForm.fulfillment_center_id}
            onChange={(e) => setWarehouseForm((f) => ({ ...f, fulfillment_center_id: e.target.value }))}
          />
          <input
            className="ellan-field"
            placeholder="carrier"
            value={warehouseForm.carrier}
            onChange={(e) => setWarehouseForm((f) => ({ ...f, carrier: e.target.value }))}
          />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar fulfillment CD
          </button>
        </form>
      )}

      {tab === 'orders' && (
        <form onSubmit={onCreateOrder} className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <input
            type="number"
            className="w-32 ellan-field"
            value={orderForm.amount_cents}
            onChange={(e) => setOrderForm((f) => ({ ...f, amount_cents: Number(e.target.value) }))}
          />
          <input
            className="ellan-field"
            placeholder="ecommerce_partner_id"
            value={orderForm.ecommerce_partner_id}
            onChange={(e) => setOrderForm((f) => ({ ...f, ecommerce_partner_id: e.target.value }))}
          />
          <input
            className="ellan-field"
            placeholder="totem_id"
            value={orderForm.totem_id}
            onChange={(e) => setOrderForm((f) => ({ ...f, totem_id: e.target.value }))}
          />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar pedido
          </button>
        </form>
      )}

      {tab === 'credits' && (
        <form onSubmit={onCreateCredit} className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <input
            className="ellan-field"
            placeholder="order_id"
            value={creditForm.order_id}
            onChange={(e) => setCreditForm((f) => ({ ...f, order_id: e.target.value }))}
          />
          <input
            className="ellan-field"
            placeholder="user_id"
            value={creditForm.user_id}
            onChange={(e) => setCreditForm((f) => ({ ...f, user_id: e.target.value }))}
          />
          <input
            type="number"
            className="w-28 ellan-field"
            value={creditForm.amount_cents}
            onChange={(e) => setCreditForm((f) => ({ ...f, amount_cents: Number(e.target.value) }))}
          />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar crédito
          </button>
        </form>
      )}

      {tab === 'overview' ? null : tableRows.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-slate-600/70 bg-slate-900/90 dark:border-slate-700 dark:bg-slate-900">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">tipo</th>
                <th className="px-3 py-2">id</th>
                <th className="px-3 py-2">detalhe</th>
                {tab === 'integration' || tab === 'holds' ? <th className="px-3 py-2">ação</th> : null}
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row) => (
                <tr key={row.key} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2">{row.tipo}</td>
                  <td className="px-3 py-2 font-mono text-xs">{row.id}</td>
                  <td className="px-3 py-2">{row.detalhe}</td>
                  {tab === 'integration' || tab === 'holds' ? (
                    <td className="px-3 py-2">
                      {'replay' in row && row.replay ? (
                        <button type="button" className="text-xs text-indigo-600" onClick={() => void row.replay?.()}>
                          {tab === 'holds' ? 'Liberar' : 'Replay'}
                        </button>
                      ) : (
                        '—'
                      )}
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-sm text-gray-500">Nenhum registro. Use Listar ou Seed.</p>
      )}
    </div>
  )
}
