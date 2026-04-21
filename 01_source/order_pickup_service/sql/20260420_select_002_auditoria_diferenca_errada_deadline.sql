-- DETECTAR DIFERENÇA ERRADA DE DEADLINE
-- Esperado: diff_hours = 2
-- Se aparecer 1 → ainda está errado

SELECT
    id,
    paid_at,
    pickup_deadline_at,
    EXTRACT(EPOCH FROM (pickup_deadline_at - paid_at)) / 3600 AS diff_hours
FROM orders
WHERE paid_at IS NOT NULL
ORDER BY created_at DESC
LIMIT 50;