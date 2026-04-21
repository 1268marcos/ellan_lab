-- 5) Deadlines FAILED que ainda merecem reprocessamento
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
    p.status AS pickup_status,
    p.expires_at,
    a.state AS allocation_state
FROM public.lifecycle_deadlines d
JOIN public.orders o
    ON o.id = d.order_id
LEFT JOIN LATERAL (
    SELECT *
    FROM public.pickups p1
    WHERE p1.order_id = d.order_id
    ORDER BY p1.created_at DESC, p1.id DESC
    LIMIT 1
) p ON TRUE
LEFT JOIN LATERAL (
    SELECT *
    FROM public.allocations a1
    WHERE a1.order_id = d.order_id
    ORDER BY a1.created_at DESC, a1.id DESC
    LIMIT 1
) a ON TRUE
WHERE d.status = 'FAILED'
  AND (
      (d.deadline_type = 'PICKUP_TIMEOUT' AND o.status = 'PAID_PENDING_PICKUP' AND o.payment_status = 'APPROVED')
      OR
      (d.deadline_type = 'PREPAYMENT_TIMEOUT' AND o.payment_status <> 'APPROVED')
  )
ORDER BY d.updated_at DESC NULLS LAST, d.due_at ASC;