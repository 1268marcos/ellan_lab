-- 3) Allocations com TTL de pré-pagamento ainda persistido em pedido já pago

-- Isso pega exatamente o padrão torto que apareceu no seu 
-- dump: pedido pago, pickup ativo, mas allocation ainda 
-- em RESERVED_PENDING_PAYMENT com locked_until curto.

SELECT
    o.id AS order_id,
    o.status AS order_status,
    o.payment_status,
    o.paid_at,
    a.id AS allocation_id,
    a.slot,
    a.state AS allocation_state,
    a.locked_until,
    p.id AS pickup_id,
    p.status AS pickup_status,
    p.lifecycle_stage,
    p.expires_at AS pickup_expires_at
FROM public.orders o
JOIN LATERAL (
    SELECT *
    FROM public.allocations a1
    WHERE a1.order_id = o.id
    ORDER BY a1.created_at DESC, a1.id DESC
    LIMIT 1
) a ON TRUE
LEFT JOIN LATERAL (
    SELECT *
    FROM public.pickups p1
    WHERE p1.order_id = o.id
    ORDER BY p1.created_at DESC, p1.id DESC
    LIMIT 1
) p ON TRUE
WHERE o.payment_status = 'APPROVED'
  AND o.status = 'PAID_PENDING_PICKUP'
  AND a.state = 'RESERVED_PENDING_PAYMENT'
ORDER BY o.created_at DESC;