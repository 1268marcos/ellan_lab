import { navItem, opsGroup, section } from './opsNavHelpers'

const BASE = '/ops/orders/admin'

/** Pedidos OPS — menu final (prompts 1–6): hub, 17 abas do admin + integração + workers. */
export const ordersOpsNavGroup = opsGroup('ordersOps', '📦', 'Pedidos OPS', {
  hub: navItem(`${BASE}?tab=overview`, 'Hub pedidos (KPIs)', {
    newTag: 'Hub',
    keywords: 'orders pickups outbox omnichannel fulfillment timeline SLA disputes health',
  }),
  sections: [
    section(
      'monitoring',
      'Monitoramento order_pickup',
      [
        navItem('/ops', 'Hub monitoramento OPS', {
          newTag: 'Live',
          keywords: 'credits reconciliation runtime deadlocks order_pickup monitoring',
        }),
        navItem('/ops/monitoring', 'Créditos · reconciliação · runtime'),
      ],
      true,
    ),
    section(
      'hub',
      'Hub & visão',
      [
        navItem(`${BASE}?tab=overview`, 'Visão geral · KPIs', { newTag: 'Hub' }),
        navItem(`${BASE}?tab=lookup`, 'Order 360 · lookup', {
          newTag: '360',
          keywords: 'timeline health score risk flags consolidated',
        }),
      ],
      true,
    ),
    section('nucleo', 'Núcleo do pedido', [
      navItem(`${BASE}?tab=orders`, 'Pedidos & pickups'),
      navItem(`${BASE}?tab=items`, 'Itens do pedido (SKU)'),
      navItem(`${BASE}?tab=substitutions`, 'Substituições de SKU', {
        newTag: 'P7+',
        keywords: 'out of stock upgrade item swap',
      }),
      navItem(`${BASE}?tab=gifts`, 'Gift · recipient pickup', {
        newTag: 'P7+',
        keywords: 'third party authorization code verification',
      }),
      navItem(`${BASE}?tab=allocations`, 'Alocações locker / slot'),
    ]),
    section('canais', 'Canais & omnichannel', [
      navItem(`${BASE}?tab=channels`, 'Players mundiais (28)', {
        newTag: 'P3+P4',
        keywords: 'InPost DHL Magalu MercadoLivre Amazon Cainiao iFood aggregators locker',
      }),
      navItem(`${BASE}?tab=food`, 'Food delivery → locker', {
        keywords: 'iFood Rappi Uber Eats Glovo DoorDash handoff',
      }),
      navItem(`${BASE}?tab=omnichannel`, 'Omnichannel (loja → locker)'),
      navItem(`${BASE}?tab=warehouse`, 'Fulfillment CD'),
    ]),
    section('logistica', 'Logística & prazos', [
      navItem(`${BASE}?tab=manifests`, 'Manifestos DPD · Correios · CTT'),
      navItem(`${BASE}?tab=deadlines`, 'Lifecycle deadlines'),
      navItem(`${BASE}?tab=sla`, 'SLA watches & breach', {
        keywords: 'sync breach pickup deadline',
      }),
    ]),
    section('risco', 'Risco & qualidade', [
      navItem(`${BASE}?tab=disputes`, 'Disputas / chargeback', {
        keywords: 'chargeback open amount',
      }),
      navItem(`${BASE}?tab=returns`, 'Devoluções / RMA locker', {
        newTag: 'P7',
        keywords: 'return refund locker drop off',
      }),
      navItem(`${BASE}?tab=holds`, 'Holds operacionais', {
        newTag: 'P7',
        keywords: 'fraud review block pickup release',
      }),
    ]),
    section('comms', 'Comunicação & pagamento', [
      navItem(`${BASE}?tab=notifications`, 'Notificações pickup', {
        newTag: 'P7',
        keywords: 'SMS email push reminder ready',
      }),
      navItem(`${BASE}?tab=payments`, 'Transações gateway', {
        newTag: 'P7+',
        keywords: 'payment_transactions stripe pix approved',
      }),
      navItem(`${BASE}?tab=reconciliation`, 'Reconciliação pagamento', {
        newTag: 'P7',
        keywords: 'captured expected fee mismatch gateway sync',
      }),
      navItem('/ops/payments/admin?tab=transactions', 'Payments OPS · transações', {
        keywords: 'payments-admin cross link',
      }),
    ]),
    section('marketplace', 'Marketplace & compensação', [
      navItem(`${BASE}?tab=commissions`, 'Comissões marketplace'),
      navItem(`${BASE}?tab=credits`, 'Créditos e goodwill'),
    ]),
    section('parceiros', 'Parceiros', [
      navItem(`${BASE}?tab=partners`, 'E-commerce / logística · webhook · API key'),
    ]),
    section('integracao', 'Integração & eventos', [
      navItem(`${BASE}?tab=integration`, 'Outbox · domain events · health', {
        keywords: 'partner_outbox domain_event integration_health replay',
      }),
      navItem('/ops/integration/orders-fiscal', 'I-1 pedido × fiscal', {
        keywords: 'fulfillment partner events billing',
      }),
      navItem('/ops/integration/orders-partner-lookup', 'L-3 partner lookup', {
        keywords: 'external ref partner order lookup',
      }),
    ]),
    section('workers', 'Workers & filas', [
      navItem('/ops/workers/admin?tab=overview', 'Workers · dashboard filas', { newTag: 'Node' }),
      navItem('/ops/workers/admin?tab=lifecycle', 'Workers · lifecycle deadlines'),
      navItem('/ops/workers/admin?tab=domain', 'Workers · domain event outbox'),
    ]),
    section('legacy', 'Legado', [
      navItem('/ops/order-pickup/admin', 'Order Pickup (URL legada)'),
      navItem('/ops/order/deadlines', 'Lifecycle interno (POST)', {
        keywords: 'order_lifecycle_service internal token',
      }),
    ]),
  ],
})
