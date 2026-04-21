-- Ver se o pedido ainda está travado
-- 21/04/2026
SELECT
    o.id AS order_id,
    o.status AS order_status,
    o.payment_status,
    o.pickup_deadline_at,
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
LEFT JOIN public.allocations a
    ON a.order_id = o.id
LEFT JOIN public.pickups p
    ON p.order_id = o.id
WHERE o.id = 'd0e9afa4-d01f-443b-9e1b-5b267d930c72'
ORDER BY a.created_at DESC, p.created_at DESC;