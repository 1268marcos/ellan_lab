-- Limpeza de batches de settlement usados em testes manuais de reconciliacao OPS
-- (divergencias sinteticas antigas). Remove itens antes dos batches (FK).
--
-- IDs alinhados a evidencias de `top-divergences` em lab (OP-ELLAN-001 / partner_demo_001).
-- Nao remove a matriz controlada `c0ffee01-*` (ver `seed_settlement_reconciliation_severity_matrix.sql`).
--
-- Executar (exemplo):
--   PGPASSWORD=admin123 psql -h 127.0.0.1 -p 5435 -U admin -d locker_central -v ON_ERROR_STOP=1 \
--     -f 02_docker/cleanup_settlement_reconciliation_legacy_test_batches.sql

BEGIN;

DELETE FROM partner_settlement_items
WHERE batch_id IN (
  'a58a31be-d121-4a88-af7c-c58e6586af00',
  '9a664dfb-0e70-433d-a037-0b2751d0650a',
  'f0a59eef-c923-42bc-b5ad-5ef3eef3ed8b'
);

DELETE FROM partner_settlement_batches
WHERE id IN (
  'a58a31be-d121-4a88-af7c-c58e6586af00',
  '9a664dfb-0e70-433d-a037-0b2751d0650a',
  'f0a59eef-c923-42bc-b5ad-5ef3eef3ed8b'
);

COMMIT;

-- Opcional: remover tambem a matriz de severidade (c0ffee01-0001 .. 0005), descomente:
-- BEGIN;
-- DELETE FROM partner_settlement_items WHERE batch_id LIKE 'c0ffee01-%';
-- DELETE FROM partner_settlement_batches WHERE id LIKE 'c0ffee01-%';
-- COMMIT;
