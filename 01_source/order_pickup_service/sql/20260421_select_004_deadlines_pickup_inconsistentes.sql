-- 4) Deadlines de pickup inconsistentes com pickup/order
SELECT
    d.id AS deadline_id,
    d.order_id,
    d.deadline_type,
    d.deadline_key,
    d.status AS deadline_status,
    d.due_at,
    d.executed_at,
    d.cancelled_at,
    d.failure_count,
    o.status AS order_status,
    o.payment_status,
    o.pickup_deadline_at,
    p.id AS pickup_id,
    p.status AS pickup_status,
    p.lifecycle_stage,
    p.expires_at AS pickup_expires_at,
    CASE
        WHEN d.deadline_type = 'PICKUP_TIMEOUT'
         AND p.expires_at IS NOT NULL
         AND d.due_at <> p.expires_at
        THEN 'DIVERGENTE_COM_PICKUP'
        WHEN d.deadline_type = 'PICKUP_TIMEOUT'
         AND o.pickup_deadline_at IS NOT NULL
         AND d.due_at <> o.pickup_deadline_at
        THEN 'DIVERGENTE_COM_ORDER'
        ELSE 'OK'
    END AS diagnostico
FROM public.lifecycle_deadlines d
LEFT JOIN public.orders o
    ON o.id = d.order_id
LEFT JOIN LATERAL (
    SELECT *
    FROM public.pickups p1
    WHERE p1.order_id = d.order_id
    ORDER BY p1.created_at DESC, p1.id DESC
    LIMIT 1
) p ON TRUE
WHERE d.deadline_type = 'PICKUP_TIMEOUT'
ORDER BY d.due_at DESC;