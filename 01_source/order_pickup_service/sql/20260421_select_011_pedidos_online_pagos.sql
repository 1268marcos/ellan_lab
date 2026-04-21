-- 1) Pedidos ONLINE pagos e ainda “ativos” após o prazo de retirada
SELECT
    o.id AS order_id,
    o.channel,
    o.status AS order_status,
    o.payment_status,
    o.region,
    o.totem_id,
    o.sku_id,
    o.amount_cents,
    o.paid_at,
    o.pickup_deadline_at,
    p.id AS pickup_id,
    p.status AS pickup_status,
    p.lifecycle_stage,
    p.expires_at AS pickup_expires_at,
    p.expired_at,
    a.id AS allocation_id,
    a.slot,
    a.state AS allocation_state,
    a.locked_until,
    a.released_at,
    CASE
        WHEN COALESCE(p.expires_at, o.pickup_deadline_at) IS NOT NULL
         AND now() > COALESCE(p.expires_at, o.pickup_deadline_at)
         AND o.status = 'PAID_PENDING_PICKUP'
        THEN 'TRAVADO_APOS_PRAZO'
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
WHERE o.channel = 'ONLINE'
  AND o.payment_status = 'APPROVED'
  AND o.status = 'PAID_PENDING_PICKUP'
  AND COALESCE(p.expires_at, o.pickup_deadline_at) IS NOT NULL
  AND now() > COALESCE(p.expires_at, o.pickup_deadline_at)
ORDER BY COALESCE(p.expires_at, o.pickup_deadline_at) ASC;