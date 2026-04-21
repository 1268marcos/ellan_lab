-- 2) Allocations que deveriam estar liberadas, mas continuam presas
SELECT
    o.id AS order_id,
    o.status AS order_status,
    o.payment_status,
    o.channel,
    o.region,
    a.id AS allocation_id,
    a.slot,
    a.state AS allocation_state,
    a.locked_until,
    a.released_at,
    p.id AS pickup_id,
    p.status AS pickup_status,
    p.lifecycle_stage,
    p.expires_at,
    p.expired_at
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
WHERE
    (
        o.status IN ('EXPIRED', 'EXPIRED_CREDIT_50', 'CANCELLED', 'FAILED', 'REFUNDED')
        OR (p.status = 'EXPIRED')
    )
    AND a.state <> 'RELEASED'
ORDER BY o.updated_at DESC NULLS LAST, o.created_at DESC;