-- Como ler rápido:
--   
-- semaforo_order
--   ERRO: pedido pago e vencido, mas ainda ativo
--   ALERTA: pago e aguardando retirada
--   OK: já foi para terminal esperado
--   
-- semaforo_pickup
--   ERRO: pickup faltando ou vencido sem ter sido encerrado
--   ALERTA: pickup ativo
--   OK: pickup expirado corretamente
--   
-- semaforo_allocation
--   ERRO: allocation presa quando deveria ter sido liberada, ou ainda em prepayment mesmo com pagamento aprovado
--   OK: released
--   
-- semaforo_deadlines
--   ERRO: deadline failed ou prepayment ainda pendente em pedido já aprovado
--   OK: executado/cancelado corretamente
--   
-- semaforo_credito
--   ERRO: pedido EXPIRED_CREDIT_50 sem crédito
--   ALERTA: expirado sem crédito ainda
--   OK: crédito disponível
--   
-- diagnostico_final
--   resume o principal problema por pedido

WITH latest_alloc AS (
    SELECT DISTINCT ON (a.order_id)
        a.order_id,
        a.id AS allocation_id,
        a.slot,
        a.state AS allocation_state,
        a.locked_until,
        a.released_at,
        a.created_at AS allocation_created_at
    FROM public.allocations a
    ORDER BY a.order_id, a.created_at DESC, a.id DESC
),
latest_pickup AS (
    SELECT DISTINCT ON (p.order_id)
        p.order_id,
        p.id AS pickup_id,
        p.status AS pickup_status,
        p.lifecycle_stage,
        p.expires_at AS pickup_expires_at,
        p.expired_at,
        p.created_at AS pickup_created_at
    FROM public.pickups p
    ORDER BY p.order_id, p.created_at DESC, p.id DESC
),
deadline_rollup AS (
    SELECT
        d.order_id,
        MAX(d.due_at) FILTER (WHERE d.deadline_type = 'PREPAYMENT_TIMEOUT') AS prepayment_due_at,
        MAX(d.due_at) FILTER (WHERE d.deadline_type = 'PICKUP_TIMEOUT') AS pickup_due_at,

        MAX(d.status::text) FILTER (WHERE d.deadline_type = 'PREPAYMENT_TIMEOUT') AS prepayment_deadline_status,
        MAX(d.status::text) FILTER (WHERE d.deadline_type = 'PICKUP_TIMEOUT') AS pickup_deadline_status,

        MAX(d.failure_count) FILTER (WHERE d.deadline_type = 'PREPAYMENT_TIMEOUT') AS prepayment_failure_count,
        MAX(d.failure_count) FILTER (WHERE d.deadline_type = 'PICKUP_TIMEOUT') AS pickup_failure_count
    FROM public.lifecycle_deadlines d
    GROUP BY d.order_id
),
credit_rollup AS (
    SELECT
        c.order_id,
        MAX(c.id) AS credit_id,
        MAX(c.amount_cents) AS credit_amount_cents,
        MAX(c.status::text) AS credit_status,
        MAX(c.expires_at) AS credit_expires_at
    FROM public.credits c
    GROUP BY c.order_id
)
SELECT
    o.id AS order_id,
    o.channel,
    o.region,
    o.totem_id,
    o.sku_id,
    o.payment_method,
    o.amount_cents,
    o.status AS order_status,
    o.payment_status,
    o.paid_at,
    o.pickup_deadline_at,

    la.allocation_id,
    la.slot,
    la.allocation_state,
    la.locked_until,
    la.released_at,

    lp.pickup_id,
    lp.pickup_status,
    lp.lifecycle_stage,
    lp.pickup_expires_at,
    lp.expired_at,

    dr.prepayment_due_at,
    dr.prepayment_deadline_status,
    COALESCE(dr.prepayment_failure_count, 0) AS prepayment_failure_count,
    dr.pickup_due_at,
    dr.pickup_deadline_status,
    COALESCE(dr.pickup_failure_count, 0) AS pickup_failure_count,

    cr.credit_id,
    cr.credit_amount_cents,
    cr.credit_status,
    cr.credit_expires_at,

    CASE
        WHEN o.payment_status = 'APPROVED'
         AND o.status = 'PAID_PENDING_PICKUP'
         AND COALESCE(lp.pickup_expires_at, o.pickup_deadline_at) IS NOT NULL
         AND now() > COALESCE(lp.pickup_expires_at, o.pickup_deadline_at)
        THEN 'ERRO'
        WHEN o.payment_status = 'APPROVED'
         AND o.status = 'PAID_PENDING_PICKUP'
        THEN 'ALERTA'
        WHEN o.status IN ('EXPIRED', 'EXPIRED_CREDIT_50', 'PICKED_UP', 'DISPENSED')
        THEN 'OK'
        ELSE 'ALERTA'
    END AS semaforo_order,

    CASE
        WHEN lp.pickup_id IS NULL
        THEN 'ERRO'
        WHEN lp.pickup_status = 'EXPIRED'
        THEN 'OK'
        WHEN lp.pickup_status = 'ACTIVE'
         AND lp.pickup_expires_at IS NOT NULL
         AND now() > lp.pickup_expires_at
        THEN 'ERRO'
        WHEN lp.pickup_status = 'ACTIVE'
        THEN 'ALERTA'
        ELSE 'ALERTA'
    END AS semaforo_pickup,

    CASE
        WHEN la.allocation_id IS NULL
        THEN 'ERRO'
        WHEN o.status IN ('EXPIRED', 'EXPIRED_CREDIT_50', 'CANCELLED', 'FAILED', 'REFUNDED')
         AND la.allocation_state <> 'RELEASED'
        THEN 'ERRO'
        WHEN o.payment_status = 'APPROVED'
         AND o.status = 'PAID_PENDING_PICKUP'
         AND la.allocation_state = 'RESERVED_PENDING_PAYMENT'
        THEN 'ERRO'
        WHEN la.allocation_state = 'RELEASED'
        THEN 'OK'
        ELSE 'ALERTA'
    END AS semaforo_allocation,

    CASE
        WHEN COALESCE(dr.pickup_deadline_status, '') = 'FAILED'
          OR COALESCE(dr.prepayment_deadline_status, '') = 'FAILED'
        THEN 'ERRO'
        WHEN o.payment_status = 'APPROVED'
         AND COALESCE(dr.prepayment_deadline_status, '') = 'PENDING'
        THEN 'ERRO'
        WHEN o.status = 'PAID_PENDING_PICKUP'
         AND COALESCE(dr.pickup_deadline_status, '') NOT IN ('PENDING', 'EXECUTED', 'CANCELLED')
        THEN 'ERRO'
        WHEN COALESCE(dr.pickup_deadline_status, '') = 'EXECUTED'
          OR COALESCE(dr.prepayment_deadline_status, '') = 'CANCELLED'
        THEN 'OK'
        ELSE 'ALERTA'
    END AS semaforo_deadlines,

    CASE
        WHEN o.status = 'EXPIRED_CREDIT_50' AND cr.credit_id IS NULL
        THEN 'ERRO'
        WHEN cr.credit_id IS NOT NULL AND cr.credit_status = 'AVAILABLE'
        THEN 'OK'
        WHEN cr.credit_id IS NOT NULL
        THEN 'ALERTA'
        WHEN o.status = 'EXPIRED'
        THEN 'ALERTA'
        ELSE 'OK'
    END AS semaforo_credito,

    CASE
        WHEN o.payment_status = 'APPROVED'
         AND o.status = 'PAID_PENDING_PICKUP'
         AND COALESCE(lp.pickup_expires_at, o.pickup_deadline_at) IS NOT NULL
         AND now() > COALESCE(lp.pickup_expires_at, o.pickup_deadline_at)
         AND la.allocation_state <> 'RELEASED'
        THEN 'PEDIDO_TRAVADO_APOS_PRAZO'

        WHEN COALESCE(dr.pickup_deadline_status, '') = 'FAILED'
        THEN 'PICKUP_TIMEOUT_FAILED'

        WHEN COALESCE(dr.prepayment_deadline_status, '') = 'FAILED'
        THEN 'PREPAYMENT_TIMEOUT_FAILED'

        WHEN o.payment_status = 'APPROVED'
         AND o.status = 'PAID_PENDING_PICKUP'
         AND la.allocation_state = 'RESERVED_PENDING_PAYMENT'
        THEN 'ALLOCATION_AINDA_EM_PREPAYMENT'

        WHEN o.status = 'EXPIRED_CREDIT_50'
         AND cr.credit_id IS NULL
        THEN 'EXPIRADO_SEM_CREDITO'

        WHEN lp.pickup_status = 'EXPIRED'
         AND o.status = 'PAID_PENDING_PICKUP'
        THEN 'ORDER_ATRASADO_VS_PICKUP_EXPIRADO'

        WHEN o.status IN ('EXPIRED', 'EXPIRED_CREDIT_50')
         AND la.allocation_state = 'RELEASED'
        THEN 'OK_EXPIRADO_LIBERADO'

        WHEN o.status IN ('PICKED_UP', 'DISPENSED')
        THEN 'OK_RETIRADO'

        WHEN o.payment_status = 'APPROVED'
         AND o.status = 'PAID_PENDING_PICKUP'
        THEN 'OK_AGUARDANDO_RETIRADA'

        ELSE 'REVISAR'
    END AS diagnostico_final

FROM public.orders o
LEFT JOIN latest_alloc la
    ON la.order_id = o.id
LEFT JOIN latest_pickup lp
    ON lp.order_id = o.id
LEFT JOIN deadline_rollup dr
    ON dr.order_id = o.id
LEFT JOIN credit_rollup cr
    ON cr.order_id = o.id

ORDER BY
    CASE
        WHEN
            (
                o.payment_status = 'APPROVED'
                AND o.status = 'PAID_PENDING_PICKUP'
                AND COALESCE(lp.pickup_expires_at, o.pickup_deadline_at) IS NOT NULL
                AND now() > COALESCE(lp.pickup_expires_at, o.pickup_deadline_at)
                AND la.allocation_state <> 'RELEASED'
            )
            OR COALESCE(dr.pickup_deadline_status, '') = 'FAILED'
            OR COALESCE(dr.prepayment_deadline_status, '') = 'FAILED'
            OR (
                o.payment_status = 'APPROVED'
                AND o.status = 'PAID_PENDING_PICKUP'
                AND la.allocation_state = 'RESERVED_PENDING_PAYMENT'
            )
        THEN 0
        WHEN o.payment_status = 'APPROVED' AND o.status = 'PAID_PENDING_PICKUP'
        THEN 1
        ELSE 2
    END,
    o.created_at DESC;


    