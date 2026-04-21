-- 6) Pedidos expirados sem crédito gerado
-- Para achar só os problemáticos:

SELECT
    o.id AS order_id,
    o.user_id,
    o.status AS order_status,
    o.payment_status,
    o.amount_cents,
    o.region,
    o.updated_at
FROM public.orders o
LEFT JOIN public.credits c
    ON c.order_id = o.id
WHERE o.status = 'EXPIRED_CREDIT_50'
  AND c.id IS NULL
ORDER BY o.updated_at DESC NULLS LAST, o.created_at DESC;

