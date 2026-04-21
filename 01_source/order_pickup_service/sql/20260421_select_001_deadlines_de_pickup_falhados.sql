-- Ver deadlines de pickup falhados com contexto
-- 21/04/2026

SELECT
    id,
    order_id,
    deadline_type,
    deadline_key,
    status,
    due_at,
    executed_at,
    cancelled_at,
    failure_count,
    updated_at,
    payload
FROM public.lifecycle_deadlines
WHERE deadline_type = 'PICKUP_TIMEOUT'
  AND status = 'FAILED'
ORDER BY due_at ASC, updated_at ASC;