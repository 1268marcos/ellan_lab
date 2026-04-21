-- 8) Divergência entre orders, pickups e allocations
SELECT
    o.id AS order_id,
    o.status AS order_status,
    o.payment_status,
    p.status AS pickup_status,
    p.lifecycle_stage,
    a.state AS allocation_state,
    p.expires_at,
    a.locked_until,
    CASE
        WHEN o.status = 'PAID_PENDING_PICKUP'
         AND p.status = 'EXPIRED'
        THEN 'ORDER_ATRASADO_VS_PICKUP_EXPIRADO'
        WHEN o.status IN ('EXPIRED', 'EXPIRED_CREDIT_50')
         AND a.state <> 'RELEASED'
        THEN 'ORDER_EXPIRADO_VS_ALLOCATION_PRESA'
        WHEN o.payment_status = 'APPROVED'
         AND o.status = 'PAID_PENDING_PICKUP'
         AND a.state = 'RESERVED_PENDING_PAYMENT'
        THEN 'ALLOCATION_AINDA_EM_PREPAYMENT'
        ELSE 'OK'
    END AS diagnostico
FROM public.orders o
LEFT JOIN LATERAL (
    SELECT *
    FROM public.pickups p1
    WHERE p1.order_id = o.id
    ORDER BY p1.created_at DESC, p1.id DESC
    LIMIT 1
) p ON TRUE
LEFT JOIN LATERAL (
    SELECT *
    FROM public.allocations a1
    WHERE a1.order_id = o.id
    ORDER BY a1.created_at DESC, a1.id DESC
    LIMIT 1
) a ON TRUE
WHERE
    (
        (o.status = 'PAID_PENDING_PICKUP' AND p.status = 'EXPIRED')
        OR
        (o.status IN ('EXPIRED', 'EXPIRED_CREDIT_50') AND a.state <> 'RELEASED')
        OR
        (o.payment_status = 'APPROVED' AND o.status = 'PAID_PENDING_PICKUP' AND a.state = 'RESERVED_PENDING_PAYMENT')
    )
ORDER BY o.created_at DESC;

