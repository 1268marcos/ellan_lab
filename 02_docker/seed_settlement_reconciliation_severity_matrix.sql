-- Matriz de teste: reconciliacao de settlements (severidades HIGH / MEDIUM / LOW).
-- Alinhado ao helper _settlement_reconciliation_severity em order_pickup_service (partners.py).
--
-- Parceiros: mesmos IDs do seed base (sprint0 / locker_seed): OP-ELLAN-001, OP-PHARMA-001.
-- Ordem: DELETE itens antes dos batches (FK).
--
-- Aplicar (exemplo):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f 02_docker/seed_settlement_reconciliation_severity_matrix.sql
--
-- Reverter manualmente (copiar e executar; remove so estes batch_id):
--   DELETE FROM partner_settlement_items WHERE batch_id IN (
--     'c0ffee01-0001-4000-8000-000000000001','c0ffee01-0002-4000-8000-000000000001',
--     'c0ffee01-0003-4000-8000-000000000001','c0ffee01-0004-4000-8000-000000000001',
--     'c0ffee01-0005-4000-8000-000000000001');
--   DELETE FROM partner_settlement_batches WHERE id IN (
--     'c0ffee01-0001-4000-8000-000000000001','c0ffee01-0002-4000-8000-000000000001',
--     'c0ffee01-0003-4000-8000-000000000001','c0ffee01-0004-4000-8000-000000000001',
--     'c0ffee01-0005-4000-8000-000000000001');

-- Idempotente: limpa antes de inserir de novo
DELETE FROM partner_settlement_items WHERE batch_id IN (
  'c0ffee01-0001-4000-8000-000000000001',
  'c0ffee01-0002-4000-8000-000000000001',
  'c0ffee01-0003-4000-8000-000000000001',
  'c0ffee01-0004-4000-8000-000000000001',
  'c0ffee01-0005-4000-8000-000000000001'
);
DELETE FROM partner_settlement_batches WHERE id IN (
  'c0ffee01-0001-4000-8000-000000000001',
  'c0ffee01-0002-4000-8000-000000000001',
  'c0ffee01-0003-4000-8000-000000000001',
  'c0ffee01-0004-4000-8000-000000000001',
  'c0ffee01-0005-4000-8000-000000000001'
);

-- Timestamps dentro da janela padrao do GET top-divergences (ultimos 30 dias a partir de "hoje" em lab).
INSERT INTO partner_settlement_batches (
  id, partner_id, partner_type, period_start, period_end, currency,
  total_orders, gross_revenue_cents, revenue_share_pct, revenue_share_cents,
  fees_cents, net_amount_cents, status, notes, created_at, updated_at
) VALUES
  -- HIGH #1: header gross maior que soma dos itens (delta gross negativo nos itens vs header)
  (
    'c0ffee01-0001-4000-8000-000000000001',
    'OP-ELLAN-001',
    'ECOMMERCE',
    DATE '2026-04-01',
    DATE '2026-04-30',
    'BRL',
    1,
    10000,
    0.1500,
    1500,
    0,
    8500,
    'DRAFT',
    'seed severity matrix: HIGH (gross divergente)',
    TIMESTAMPTZ '2026-04-26 18:00:00+00',
    TIMESTAMPTZ '2026-04-26 18:00:00+00'
  ),
  -- HIGH #2: soma dos itens gross maior que header
  (
    'c0ffee01-0002-4000-8000-000000000001',
    'OP-ELLAN-001',
    'ECOMMERCE',
    DATE '2026-04-01',
    DATE '2026-04-30',
    'BRL',
    2,
    2000,
    0.1500,
    300,
    0,
    1700,
    'APPROVED',
    'seed severity matrix: HIGH (gross divergente)',
    TIMESTAMPTZ '2026-04-26 18:05:00+00',
    TIMESTAMPTZ '2026-04-26 18:05:00+00'
  ),
  -- MEDIUM #1: gross e share batem; header total_orders menor que COUNT(itens)
  (
    'c0ffee01-0003-4000-8000-000000000001',
    'OP-PHARMA-001',
    'ECOMMERCE',
    DATE '2026-04-01',
    DATE '2026-04-30',
    'BRL',
    1,
    3000,
    0.1500,
    450,
    0,
    2550,
    'DRAFT',
    'seed severity matrix: MEDIUM (contagem itens)',
    TIMESTAMPTZ '2026-04-26 18:10:00+00',
    TIMESTAMPTZ '2026-04-26 18:10:00+00'
  ),
  -- MEDIUM #2: contagens e gross batem; share no header defasado >= 10 centavos
  (
    'c0ffee01-0004-4000-8000-000000000001',
    'OP-PHARMA-001',
    'ECOMMERCE',
    DATE '2026-04-01',
    DATE '2026-04-30',
    'BRL',
    2,
    2000,
    0.1500,
    280,
    0,
    1720,
    'PAID',
    'seed severity matrix: MEDIUM (share header vs itens)',
    TIMESTAMPTZ '2026-04-26 18:15:00+00',
    TIMESTAMPTZ '2026-04-26 18:15:00+00'
  ),
  -- LOW: so resíduo pequeno em share (< 10 centavos), sem delta gross nem em contagem
  (
    'c0ffee01-0005-4000-8000-000000000001',
    'OP-ELLAN-001',
    'ECOMMERCE',
    DATE '2026-04-01',
    DATE '2026-04-30',
    'BRL',
    1,
    1000,
    0.1500,
    145,
    0,
    855,
    'DRAFT',
    'seed severity matrix: LOW (share residual)',
    TIMESTAMPTZ '2026-04-26 18:20:00+00',
    TIMESTAMPTZ '2026-04-26 18:20:00+00'
  );

INSERT INTO partner_settlement_items (
  batch_id, order_id, order_date, gross_cents, share_pct, share_cents, currency
) VALUES
  -- HIGH #1: um pedido; soma gross 8000 vs header 10000
  (
    'c0ffee01-0001-4000-8000-000000000001',
    'd0ffee01-0001-4000-8000-000000000001',
    TIMESTAMPTZ '2026-04-10 10:00:00+00',
    8000,
    0.1500,
    1200,
    'BRL'
  ),
  -- HIGH #2: dois pedidos; soma gross 2600 vs header 2000
  (
    'c0ffee01-0002-4000-8000-000000000001',
    'd0ffee01-0002-4000-8000-000000000001',
    TIMESTAMPTZ '2026-04-11 11:00:00+00',
    1300,
    0.1500,
    195,
    'BRL'
  ),
  (
    'c0ffee01-0002-4000-8000-000000000001',
    'd0ffee01-0002-4000-8000-000000000002',
    TIMESTAMPTZ '2026-04-11 12:00:00+00',
    1300,
    0.1500,
    195,
    'BRL'
  ),
  -- MEDIUM #1: tres linhas, gross/share consistentes com header exceto total_orders
  (
    'c0ffee01-0003-4000-8000-000000000001',
    'd0ffee01-0003-4000-8000-000000000001',
    TIMESTAMPTZ '2026-04-12 09:00:00+00',
    1000,
    0.1500,
    150,
    'BRL'
  ),
  (
    'c0ffee01-0003-4000-8000-000000000001',
    'd0ffee01-0003-4000-8000-000000000002',
    TIMESTAMPTZ '2026-04-12 10:00:00+00',
    1000,
    0.1500,
    150,
    'BRL'
  ),
  (
    'c0ffee01-0003-4000-8000-000000000001',
    'd0ffee01-0003-4000-8000-000000000003',
    TIMESTAMPTZ '2026-04-12 11:00:00+00',
    1000,
    0.1500,
    150,
    'BRL'
  ),
  -- MEDIUM #2: share somada 300 vs header 280
  (
    'c0ffee01-0004-4000-8000-000000000001',
    'd0ffee01-0004-4000-8000-000000000001',
    TIMESTAMPTZ '2026-04-13 08:00:00+00',
    1000,
    0.1500,
    150,
    'BRL'
  ),
  (
    'c0ffee01-0004-4000-8000-000000000001',
    'd0ffee01-0004-4000-8000-000000000002',
    TIMESTAMPTZ '2026-04-13 09:00:00+00',
    1000,
    0.1500,
    150,
    'BRL'
  ),
  -- LOW: item share 150 vs header 145 (delta +5 centavos nos itens vs header)
  (
    'c0ffee01-0005-4000-8000-000000000001',
    'd0ffee01-0005-4000-8000-000000000001',
    TIMESTAMPTZ '2026-04-14 14:00:00+00',
    1000,
    0.1500,
    150,
    'BRL'
  );
