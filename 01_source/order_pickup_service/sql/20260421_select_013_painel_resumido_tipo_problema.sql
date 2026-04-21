-- 9) Painel resumido por tipo de problema
WITH latest_alloc AS (
    SELECT DISTINCT ON (order_id)
        order_id, id, slot, state, locked_until, released_at
    FROM public.allocations
    ORDER BY order_id, created_at DESC, id DESC
),
latest_pickup AS (
    SELECT DISTINCT ON (order_id)
        order_id, id, status, lifecycle_stage, expires_at, expired_at
    FROM public.pickups
    ORDER BY order_id, created_at DESC, id DESC
),
failed_deadlines AS (
    SELECT
        order_id,
        COUNT(*) FILTER (WHERE deadline_type = 'PICKUP_TIMEOUT' AND status = 'FAILED') AS failed_pickup_deadlines,
        COUNT(*) FILTER (WHERE deadline_type = 'PREPAYMENT_TIMEOUT' AND status = 'FAILED') AS failed_prepayment_deadlines
    FROM public.lifecycle_deadlines
    GROUP BY order_id
)
SELECT
    COUNT(*) FILTER (
        WHERE o.payment_status = 'APPROVED'
          AND o.status = 'PAID_PENDING_PICKUP'
          AND lp.expires_at IS NOT NULL
          AND now() > lp.expires_at
    ) AS pedidos_travados_apos_prazo,

    COUNT(*) FILTER (
        WHERE o.status IN ('EXPIRED', 'EXPIRED_CREDIT_50')
          AND la.state <> 'RELEASED'
    ) AS allocations_nao_liberadas,

    COUNT(*) FILTER (
        WHERE COALESCE(fd.failed_pickup_deadlines, 0) > 0
           OR COALESCE(fd.failed_prepayment_deadlines, 0) > 0
    ) AS orders_com_deadlines_failed,

    COUNT(*) FILTER (
        WHERE o.payment_status = 'APPROVED'
          AND o.status = 'PAID_PENDING_PICKUP'
          AND la.state = 'RESERVED_PENDING_PAYMENT'
    ) AS allocations_ainda_em_prepayment,

    COUNT(*) FILTER (
        WHERE o.status = 'EXPIRED_CREDIT_50'
          AND NOT EXISTS (
              SELECT 1
              FROM public.credits c
              WHERE c.order_id = o.id
          )
    ) AS expirados_sem_credito
FROM public.orders o
LEFT JOIN latest_alloc la
    ON la.order_id = o.id
LEFT JOIN latest_pickup lp
    ON lp.order_id = o.id
LEFT JOIN failed_deadlines fd
    ON fd.order_id = o.id;