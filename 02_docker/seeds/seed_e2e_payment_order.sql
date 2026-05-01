-- Seed P0 E2E: pedido ONLINE em PAYMENT_PENDING + alocação alinhada ao runtime (allocate prévio).
-- Uso (variáveis psql -v):
--   psql ... -v order_id='e2e-order-p0-123' -v allocation_id='al_e2e_p0_123' -v slot='21' \
--            -v totem_id='SP-CARAPICUIBA-JDMARILU-LK-002' -v region='SP' -v currency='BRL' -v sku_id='cookie_especial' \
--            -v user_id=''   (vazio = NULL) ou -v user_id='<uuid users.id>' \
--            -f seed_e2e_payment_order.sql
--
-- O allocation_id e slot devem coincidir com o POST /locker/allocate executado antes deste seed.

BEGIN;

DELETE FROM pickup_tokens WHERE pickup_id IN (SELECT id FROM pickups WHERE order_id = :'order_id');
DELETE FROM pickups WHERE order_id = :'order_id';
DELETE FROM fiscal_documents WHERE order_id = :'order_id';
DELETE FROM domain_event_outbox WHERE aggregate_id = :'order_id';
DELETE FROM order_items WHERE order_id = :'order_id';
DELETE FROM allocations WHERE order_id = :'order_id';
DELETE FROM orders WHERE id = :'order_id';

INSERT INTO orders (
  id,
  user_id,
  channel,
  region,
  totem_id,
  sku_id,
  amount_cents,
  status,
  gateway_transaction_id,
  payment_method,
  payment_status,
  consent_marketing,
  consent_analytics,
  currency,
  created_at,
  updated_at,
  allocation_id,
  slot
) VALUES (
  :'order_id',
  CASE WHEN trim(:'user_id') = '' THEN NULL ELSE trim(:'user_id') END,
  'ONLINE'::orderchannel,
  :'region',
  :'totem_id',
  :'sku_id',
  1000,
  'PAYMENT_PENDING'::orderstatus,
  NULL,
  NULL,
  'CREATED'::paymentstatus,
  0,
  false,
  :'currency',
  now(),
  now(),
  :'allocation_id',
  :'slot'::integer
);

INSERT INTO allocations (
  id,
  order_id,
  locker_id,
  slot,
  state,
  locked_until,
  ttl_seconds,
  created_at,
  updated_at
) VALUES (
  :'allocation_id',
  :'order_id',
  :'totem_id',
  :'slot'::integer,
  'RESERVED_PENDING_PAYMENT'::allocationstate,
  now() + interval '15 minutes',
  900,
  now(),
  now()
);

COMMIT;
