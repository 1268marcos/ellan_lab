-- One-time cleanup for legacy enum-like values stored as text in orders.
-- Execute manually against locker_central before starting services that read orders.
-- Example:
--   docker compose exec -T postgres_central psql -U admin -d locker_central -f /tmp/cleanup_legacy_payment_enums.sql
-- or:
--   psql "postgresql://admin:admin123@localhost:5432/locker_central" -f cleanup_legacy_payment_enums.sql

UPDATE orders
SET payment_method = CAST('creditCard' AS paymentmethod)
WHERE upper(trim(payment_method::text)) IN ('CARTAO', 'PAYMENTMETHOD.CARTAO');

-- Quick verification
SELECT payment_method, count(*) AS total
FROM orders
GROUP BY payment_method
ORDER BY total DESC;
