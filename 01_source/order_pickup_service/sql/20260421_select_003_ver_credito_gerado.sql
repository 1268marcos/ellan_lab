-- Ver crédito gerado
-- 21/04/2026

SELECT
    id,
    user_id,
    order_id,
    amount_cents,
    status,
    created_at,
    expires_at,
    used_at,
    revoked_at,
    source_type,
    source_reason
FROM public.credits
WHERE order_id = 'd0e9afa4-d01f-443b-9e1b-5b267d930c72'
ORDER BY created_at DESC;