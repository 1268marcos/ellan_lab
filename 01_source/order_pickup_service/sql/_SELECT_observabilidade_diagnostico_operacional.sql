-- Como ler as prioridades
-- P0: Pedido já devia ter sido encerrado/liberado ou deadline de pickup falhou.
-- P1: Fluxo inconsistente, mas ainda com correção operacional controlada.
-- P2: Pedido ativo, acompanhar.
-- P3: Sem urgência operacional.

-- V5 FINAL - DIAGNÓSTICO OPERACIONAL CONFIÁVEL
-- Objetivo:
-- 1) Priorizar apenas problemas reais
-- 2) Não acusar pickup timeout failed em pedido já retirado/concluído
-- 3) Manter visão única com semáforos, diagnóstico, ação e reparo sugerido

WITH latest_alloc AS (
    SELECT DISTINCT ON (a.order_id)
        a.order_id,
        a.id AS allocation_id,
        a.slot,
        a.state AS allocation_state,
        a.locked_until,
        a.released_at,
        a.created_at AS allocation_created_at,
        a.updated_at AS allocation_updated_at
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
        p.created_at AS pickup_created_at,
        p.updated_at AS pickup_updated_at,
        p.locker_id AS pickup_locker_id,
        p.machine_id AS pickup_machine_id,
        p.slot AS pickup_slot
    FROM public.pickups p
    ORDER BY p.order_id, p.created_at DESC, p.id DESC
),
deadline_rollup AS (
    SELECT
        d.order_id,

        MAX(d.due_at) FILTER (
            WHERE d.deadline_type = 'PREPAYMENT_TIMEOUT'
        ) AS prepayment_due_at,

        MAX(d.due_at) FILTER (
            WHERE d.deadline_type = 'PICKUP_TIMEOUT'
        ) AS pickup_due_at,

        MAX(d.status::text) FILTER (
            WHERE d.deadline_type = 'PREPAYMENT_TIMEOUT'
        ) AS prepayment_deadline_status,

        MAX(d.status::text) FILTER (
            WHERE d.deadline_type = 'PICKUP_TIMEOUT'
        ) AS pickup_deadline_status,

        MAX(d.failure_count) FILTER (
            WHERE d.deadline_type = 'PREPAYMENT_TIMEOUT'
        ) AS prepayment_failure_count,

        MAX(d.failure_count) FILTER (
            WHERE d.deadline_type = 'PICKUP_TIMEOUT'
        ) AS pickup_failure_count
    FROM public.lifecycle_deadlines d
    GROUP BY d.order_id
),
credit_rollup AS (
    SELECT
        c.order_id,
        MAX(c.id) AS credit_id,
        MAX(c.amount_cents) AS credit_amount_cents,
        MAX(c.status::text) AS credit_status,
        MAX(c.expires_at) AS credit_expires_at,
        MAX(c.created_at) AS credit_created_at
    FROM public.credits c
    GROUP BY c.order_id
),
base AS (
    SELECT
        o.id AS order_id,
        o.channel,
        o.region,
        o.totem_id,
        o.sku_id,
        o.payment_method,
        o.amount_cents,
        o.status::text AS order_status,
        o.payment_status,
        o.paid_at,
        o.pickup_deadline_at,
        o.created_at,
        o.updated_at,

        la.allocation_id,
        la.slot,
        la.allocation_state,
        la.locked_until,
        la.released_at,
        la.allocation_created_at,
        la.allocation_updated_at,

        lp.pickup_id,
        lp.pickup_status::text AS pickup_status,
        lp.lifecycle_stage::text AS lifecycle_stage,
        lp.pickup_expires_at,
        lp.expired_at,
        lp.pickup_created_at,
        lp.pickup_updated_at,
        lp.pickup_locker_id,
        lp.pickup_machine_id,
        lp.pickup_slot,

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
        cr.credit_created_at,

        COALESCE(
            lp.pickup_expires_at,
            o.pickup_deadline_at,
            dr.pickup_due_at
        ) AS prazo_retirada_referencia,

        CASE
            WHEN COALESCE(lp.pickup_expires_at, o.pickup_deadline_at, dr.pickup_due_at) IS NOT NULL
            THEN now() > COALESCE(lp.pickup_expires_at, o.pickup_deadline_at, dr.pickup_due_at)
            ELSE FALSE
        END AS deadline_pickup_vencido,

        CASE
            WHEN COALESCE(lp.pickup_expires_at, o.pickup_deadline_at, dr.pickup_due_at) IS NOT NULL
                 AND now() > COALESCE(lp.pickup_expires_at, o.pickup_deadline_at, dr.pickup_due_at)
            THEN FLOOR(
                EXTRACT(
                    EPOCH FROM (
                        now() - COALESCE(lp.pickup_expires_at, o.pickup_deadline_at, dr.pickup_due_at)
                    )
                ) / 60.0
            )::int
            ELSE 0
        END AS minutos_em_atraso,

        CASE
            WHEN o.status::text IN ('EXPIRED', 'EXPIRED_CREDIT_50', 'CANCELLED', 'FAILED', 'REFUNDED')
              OR lp.pickup_status::text = 'EXPIRED'
              OR (
                  o.payment_status = 'APPROVED'
                  AND o.status::text = 'PAID_PENDING_PICKUP'
                  AND COALESCE(lp.pickup_expires_at, o.pickup_deadline_at, dr.pickup_due_at) IS NOT NULL
                  AND now() > COALESCE(lp.pickup_expires_at, o.pickup_deadline_at, dr.pickup_due_at)
              )
            THEN TRUE
            ELSE FALSE
        END AS runtime_liberacao_esperada,

        CASE
            WHEN o.status::text = 'EXPIRED_CREDIT_50' AND cr.credit_id IS NULL THEN TRUE
            ELSE FALSE
        END AS precisa_credito,

        CASE
            WHEN lp.pickup_status::text = 'EXPIRED' AND o.status::text = 'PAID_PENDING_PICKUP' THEN TRUE
            ELSE FALSE
        END AS tem_inconsistencia_order_pickup,

        CASE
            WHEN o.payment_status = 'APPROVED'
             AND o.status::text = 'PAID_PENDING_PICKUP'
             AND COALESCE(la.allocation_state::text, '') = 'RESERVED_PENDING_PAYMENT'
            THEN TRUE
            WHEN o.status::text IN ('EXPIRED', 'EXPIRED_CREDIT_50')
             AND COALESCE(la.allocation_state::text, '') <> 'RELEASED'
            THEN TRUE
            ELSE FALSE
        END AS tem_inconsistencia_order_allocation,

        CASE
            WHEN o.status::text IN ('DISPENSED', 'PICKED_UP')
              OR COALESCE(lp.pickup_status::text, '') IN ('REDEEMED')
              OR COALESCE(lp.lifecycle_stage::text, '') IN ('COMPLETED')
            THEN TRUE
            ELSE FALSE
        END AS pedido_concluido_com_sucesso
    FROM public.orders o
    LEFT JOIN latest_alloc la
        ON la.order_id = o.id
    LEFT JOIN latest_pickup lp
        ON lp.order_id = o.id
    LEFT JOIN deadline_rollup dr
        ON dr.order_id = o.id
    LEFT JOIN credit_rollup cr
        ON cr.order_id = o.id
),
diagnosticado AS (
    SELECT
        b.*,

        CASE
            WHEN b.pedido_concluido_com_sucesso = TRUE
            THEN 'OK_RETIRADO'

            WHEN b.order_status IN ('EXPIRED', 'EXPIRED_CREDIT_50')
             AND COALESCE(b.allocation_state::text, '') = 'RELEASED'
            THEN 'OK_EXPIRADO_LIBERADO'

            WHEN b.order_status = 'EXPIRED_CREDIT_50'
             AND b.credit_id IS NULL
            THEN 'EXPIRADO_SEM_CREDITO'

            WHEN COALESCE(b.pickup_deadline_status, '') = 'FAILED'
             AND b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
            THEN 'PICKUP_TIMEOUT_FAILED'

            WHEN COALESCE(b.prepayment_deadline_status, '') = 'FAILED'
             AND b.payment_status <> 'APPROVED'
            THEN 'PREPAYMENT_TIMEOUT_FAILED'

            WHEN b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
             AND b.deadline_pickup_vencido = TRUE
             AND COALESCE(b.allocation_state::text, '') <> 'RELEASED'
            THEN 'PEDIDO_TRAVADO_APOS_PRAZO'

            WHEN b.pickup_status = 'EXPIRED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
            THEN 'ORDER_ATRASADO_VS_PICKUP_EXPIRADO'

            WHEN b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
             AND COALESCE(b.allocation_state::text, '') = 'RESERVED_PENDING_PAYMENT'
            THEN 'ALLOCATION_AINDA_EM_PREPAYMENT'

            WHEN b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
            THEN 'OK_AGUARDANDO_RETIRADA'

            WHEN b.order_status IN ('PAYMENT_PENDING', 'CREATED')
             AND b.payment_status IN ('CREATED', 'PENDING_CUSTOMER_ACTION')
            THEN 'AGUARDANDO_PAGAMENTO'

            WHEN b.order_status IN ('CANCELLED', 'FAILED')
             AND COALESCE(b.allocation_state::text, '') = 'RELEASED'
            THEN 'OK_CANCELADO_LIBERADO'

            ELSE 'REVISAR'
        END AS diagnostico_final,

        CASE
            WHEN b.pedido_concluido_com_sucesso = TRUE
            THEN 'OK'

            WHEN b.order_status IN ('EXPIRED', 'EXPIRED_CREDIT_50')
             AND COALESCE(b.allocation_state::text, '') = 'RELEASED'
             AND (b.credit_id IS NOT NULL OR b.order_status = 'EXPIRED')
            THEN 'OK'

            WHEN b.order_status = 'EXPIRED_CREDIT_50'
             AND b.credit_id IS NULL
            THEN 'GERAR_CREDITO'

            WHEN COALESCE(b.pickup_deadline_status, '') = 'FAILED'
             AND b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
            THEN 'REPROCESSAR_DEADLINE'

            WHEN b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
             AND b.deadline_pickup_vencido = TRUE
             AND COALESCE(b.allocation_state::text, '') <> 'RELEASED'
            THEN 'LIBERAR_RUNTIME'

            WHEN b.pickup_status = 'EXPIRED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
            THEN 'REVISAR_FLUXO_POS_PAGAMENTO'

            WHEN b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
             AND COALESCE(b.allocation_state::text, '') = 'RESERVED_PENDING_PAYMENT'
            THEN 'REVISAR_FLUXO_POS_PAGAMENTO'

            WHEN COALESCE(b.prepayment_deadline_status, '') = 'FAILED'
             AND b.payment_status = 'APPROVED'
            THEN 'REVISAR_CANCELAMENTO_PREPAYMENT'

            WHEN b.order_status IN ('PAYMENT_PENDING', 'CREATED')
             AND b.payment_status IN ('CREATED', 'PENDING_CUSTOMER_ACTION')
            THEN 'ACOMPANHAR'

            WHEN b.order_status IN ('CANCELLED', 'FAILED')
             AND COALESCE(b.allocation_state::text, '') = 'RELEASED'
            THEN 'OK'

            ELSE 'REVISAR_MANUALMENTE'
        END AS acao_recomendada,

        CASE
            WHEN b.order_status = 'EXPIRED_CREDIT_50'
             AND b.credit_id IS NULL
            THEN 'P0'

            WHEN COALESCE(b.pickup_deadline_status, '') = 'FAILED'
             AND b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
            THEN 'P0'

            WHEN b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
             AND b.deadline_pickup_vencido = TRUE
             AND COALESCE(b.allocation_state::text, '') <> 'RELEASED'
            THEN 'P0'

            WHEN b.pickup_status = 'EXPIRED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
            THEN 'P1'

            WHEN b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
             AND COALESCE(b.allocation_state::text, '') = 'RESERVED_PENDING_PAYMENT'
            THEN 'P1'

            WHEN COALESCE(b.prepayment_deadline_status, '') = 'FAILED'
             AND b.payment_status = 'APPROVED'
            THEN 'P1'

            WHEN b.payment_status = 'APPROVED'
             AND b.order_status = 'PAID_PENDING_PICKUP'
            THEN 'P2'

            ELSE 'P3'
        END AS prioridade_operacional
    FROM base b
)
SELECT
    d.order_id,
    d.channel,
    d.region,
    d.totem_id,
    d.sku_id,
    d.payment_method,
    d.amount_cents,

    d.order_status,
    d.payment_status,
    d.paid_at,
    d.pickup_deadline_at,

    d.allocation_id,
    d.slot,
    d.allocation_state,
    d.locked_until,
    d.released_at,

    d.pickup_id,
    d.pickup_status,
    d.lifecycle_stage,
    d.pickup_expires_at,
    d.expired_at,

    d.prepayment_due_at,
    d.prepayment_deadline_status,
    d.prepayment_failure_count,
    d.pickup_due_at,
    d.pickup_deadline_status,
    d.pickup_failure_count,

    d.credit_id,
    d.credit_amount_cents,
    d.credit_status,
    d.credit_expires_at,

    d.prazo_retirada_referencia,
    d.deadline_pickup_vencido,
    d.minutos_em_atraso,
    d.runtime_liberacao_esperada,
    d.precisa_credito,
    d.tem_inconsistencia_order_pickup,
    d.tem_inconsistencia_order_allocation,
    d.pedido_concluido_com_sucesso,

    CASE
        WHEN d.pedido_concluido_com_sucesso = TRUE
        THEN 'OK'
        WHEN d.order_status IN ('EXPIRED', 'EXPIRED_CREDIT_50')
        THEN 'OK'
        WHEN d.payment_status = 'APPROVED'
         AND d.order_status = 'PAID_PENDING_PICKUP'
         AND d.deadline_pickup_vencido = TRUE
        THEN 'ERRO'
        WHEN d.payment_status = 'APPROVED'
         AND d.order_status = 'PAID_PENDING_PICKUP'
        THEN 'ALERTA'
        ELSE 'ALERTA'
    END AS semaforo_order,

    CASE
        WHEN d.pedido_concluido_com_sucesso = TRUE
        THEN 'OK'
        WHEN d.order_status IN ('EXPIRED', 'EXPIRED_CREDIT_50', 'CANCELLED', 'FAILED')
            AND COALESCE(d.allocation_state::text, '') = 'RELEASED'
        THEN 'OK'
        WHEN d.pickup_id IS NULL
        THEN 'ERRO'
        WHEN d.pickup_status IN ('REDEEMED', 'EXPIRED')
        THEN 'OK'
        WHEN d.pickup_status = 'ACTIVE' AND d.deadline_pickup_vencido = TRUE
        THEN 'ERRO'
        WHEN d.pickup_status = 'ACTIVE'
        THEN 'ALERTA'
        ELSE 'ALERTA'
    END AS semaforo_pickup,

    CASE
        WHEN d.pedido_concluido_com_sucesso = TRUE
             AND COALESCE(d.allocation_state::text, '') IN ('OPENED_FOR_PICKUP', 'PICKED_UP', 'RELEASED')
        THEN 'OK'
        WHEN d.order_status IN ('EXPIRED', 'EXPIRED_CREDIT_50')
             AND COALESCE(d.allocation_state::text, '') = 'RELEASED'
        THEN 'OK'
        WHEN d.allocation_id IS NULL
        THEN 'ERRO'
        WHEN d.runtime_liberacao_esperada = TRUE
             AND COALESCE(d.allocation_state::text, '') <> 'RELEASED'
        THEN 'ERRO'
        WHEN d.payment_status = 'APPROVED'
             AND d.order_status = 'PAID_PENDING_PICKUP'
             AND COALESCE(d.allocation_state::text, '') = 'RESERVED_PENDING_PAYMENT'
        THEN 'ERRO'
        WHEN COALESCE(d.allocation_state::text, '') = 'RELEASED'
        THEN 'OK'
        ELSE 'ALERTA'
    END AS semaforo_allocation,

    CASE
        WHEN d.pedido_concluido_com_sucesso = TRUE
        THEN 'OK'
        WHEN d.order_status IN ('EXPIRED', 'EXPIRED_CREDIT_50')
             AND COALESCE(d.pickup_deadline_status, '') IN ('EXECUTED', 'CANCELLED', '')
        THEN 'OK'
        WHEN COALESCE(d.pickup_deadline_status, '') = 'FAILED'
             AND d.payment_status = 'APPROVED'
             AND d.order_status = 'PAID_PENDING_PICKUP'
        THEN 'ERRO'
        WHEN COALESCE(d.prepayment_deadline_status, '') = 'FAILED'
             AND d.payment_status <> 'APPROVED'
        THEN 'ERRO'
        WHEN d.payment_status = 'APPROVED'
             AND d.order_status = 'PAID_PENDING_PICKUP'
             AND COALESCE(d.pickup_deadline_status, '') NOT IN ('PENDING', 'EXECUTED', 'CANCELLED')
        THEN 'ERRO'
        WHEN d.payment_status = 'APPROVED'
             AND COALESCE(d.prepayment_deadline_status, '') = 'PENDING'
        THEN 'ERRO'
        WHEN COALESCE(d.pickup_deadline_status, '') = 'EXECUTED'
          OR COALESCE(d.prepayment_deadline_status, '') = 'CANCELLED'
        THEN 'OK'
        ELSE 'ALERTA'
    END AS semaforo_deadlines,

    CASE
        WHEN d.order_status = 'EXPIRED_CREDIT_50' AND d.credit_id IS NULL
        THEN 'ERRO'
        WHEN d.order_status = 'EXPIRED_CREDIT_50' AND d.credit_id IS NOT NULL
        THEN 'OK'
        WHEN d.order_status = 'EXPIRED'
        THEN 'OK'
        WHEN d.credit_id IS NOT NULL AND d.credit_status = 'AVAILABLE'
        THEN 'OK'
        WHEN d.credit_id IS NOT NULL
        THEN 'ALERTA'
        ELSE 'OK'
    END AS semaforo_credito,

    d.diagnostico_final,
    d.acao_recomendada,
    d.prioridade_operacional,

    CASE
        WHEN d.acao_recomendada = 'REPROCESSAR_DEADLINE' THEN
            'BEGIN; UPDATE public.lifecycle_deadlines SET status = ''PENDING'', locked_at = NULL, updated_at = now() WHERE order_id = ''' || d.order_id || ''' AND deadline_type = ''PICKUP_TIMEOUT'' AND status = ''FAILED''; COMMIT;'

        WHEN d.acao_recomendada = 'LIBERAR_RUNTIME' THEN
            '-- SQL banco: verificar allocation/pickup/order do pedido ' || d.order_id || E'\n' ||
            'SELECT * FROM public.orders WHERE id = ''' || d.order_id || ''';' || E'\n' ||
            'SELECT * FROM public.allocations WHERE order_id = ''' || d.order_id || ''' ORDER BY created_at DESC;' || E'\n' ||
            'SELECT * FROM public.pickups WHERE order_id = ''' || d.order_id || ''' ORDER BY created_at DESC;'

        WHEN d.acao_recomendada = 'GERAR_CREDITO' THEN
            '-- pedido ' || d.order_id || ' precisa crédito; revisar pipeline de expiração e geração de credits'

        WHEN d.acao_recomendada = 'REVISAR_FLUXO_POS_PAGAMENTO' THEN
            '-- revisar fulfill_payment_post_approval / persistência pós-pagamento do pedido ' || d.order_id

        WHEN d.acao_recomendada = 'REVISAR_CANCELAMENTO_PREPAYMENT' THEN
            'BEGIN; UPDATE public.lifecycle_deadlines SET status = ''CANCELLED'', cancelled_at = now(), updated_at = now() WHERE order_id = ''' || d.order_id || ''' AND deadline_type = ''PREPAYMENT_TIMEOUT'' AND status = ''FAILED''; COMMIT;'

        ELSE
            '-- sem reparo SQL automático sugerido'
    END AS sql_reparo_sugerido

FROM diagnosticado d
ORDER BY
    CASE d.prioridade_operacional
        WHEN 'P0' THEN 0
        WHEN 'P1' THEN 1
        WHEN 'P2' THEN 2
        ELSE 3
    END,
    d.minutos_em_atraso DESC,
    d.created_at DESC;