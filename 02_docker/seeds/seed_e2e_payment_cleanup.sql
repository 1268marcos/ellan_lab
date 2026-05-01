-- Apenas limpeza de dados E2E (mesma ordem de FK que seed_e2e_payment_order.sql).
-- Uso: psql ... -v order_id='<uuid ou id>' -f seed_e2e_payment_cleanup.sql

BEGIN;

DELETE FROM pickup_tokens WHERE pickup_id IN (SELECT id FROM pickups WHERE order_id = :'order_id');
DELETE FROM pickups WHERE order_id = :'order_id';
DELETE FROM fiscal_documents WHERE order_id = :'order_id';
DELETE FROM domain_event_outbox WHERE aggregate_id = :'order_id';
DELETE FROM order_items WHERE order_id = :'order_id';
DELETE FROM allocations WHERE order_id = :'order_id';
DELETE FROM orders WHERE id = :'order_id';

COMMIT;
