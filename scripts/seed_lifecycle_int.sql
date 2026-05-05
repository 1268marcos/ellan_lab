-- Seed for lifecycle integration test (idempotent keys)
DELETE FROM analytics_facts WHERE fact_key LIKE 'lc-int-%';
DELETE FROM orders WHERE id LIKE 'lc-int-%';

INSERT INTO orders (id, ecommerce_partner_id) VALUES
  ('lc-int-order-alpha', 'partner-alpha'),
  ('lc-int-order-beta', 'partner-beta');

INSERT INTO analytics_facts (
  id,
  fact_key,
  fact_name,
  order_id,
  order_channel,
  region_code,
  slot_id,
  payload,
  occurred_at,
  created_at
) VALUES
  (
    gen_random_uuid(),
    'lc-int-fact-alpha-1',
    'pickup_terminal_state',
    'lc-int-order-alpha',
    'ONLINE',
    'SP',
    'slot-a',
    '{"terminal_state": "redeemed"}'::jsonb,
    NOW(),
    NOW()
  ),
  (
    gen_random_uuid(),
    'lc-int-fact-beta-1',
    'pickup_terminal_state',
    'lc-int-order-beta',
    'ONLINE',
    'RJ',
    'slot-b',
    '{"terminal_state": "redeemed"}'::jsonb,
    NOW(),
    NOW()
  ),
  (
    gen_random_uuid(),
    'lc-int-fact-beta-2',
    'pickup_terminal_state',
    'lc-int-order-beta',
    'ONLINE',
    'RJ',
    'slot-b',
    '{"terminal_state": "expired"}'::jsonb,
    NOW(),
    NOW()
  );
