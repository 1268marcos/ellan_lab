-- 6) Pedidos expirados sem crédito gerado

SELECT
    o.id AS order_id,
    o.user_id,
    o.status AS order_status,
    o.payment_status,
    o.amount_cents,
    o.region,
    o.updated_at,
    c.id AS credit_id,
    c.amount_cents AS credit_amount_cents,
    c.status AS credit_status,
    c.expires_at AS credit_expires_at
FROM public.orders o
LEFT JOIN public.credits c
    ON c.order_id = o.id
WHERE o.status IN ('EXPIRED', 'EXPIRED_CREDIT_50')
ORDER BY o.updated_at DESC NULLS LAST, o.created_at DESC;
