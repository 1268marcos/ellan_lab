-- 7) Tokens ainda ativos em pickups já vencidos
SELECT
    p.order_id,
    p.id AS pickup_id,
    p.status AS pickup_status,
    p.lifecycle_stage,
    p.expires_at,
    t.id AS token_id,
    t.used_at,
    t.expires_at AS token_expires_at
FROM public.pickups p
JOIN public.pickup_tokens t
    ON t.pickup_id = p.id
WHERE p.expires_at IS NOT NULL
  AND now() > p.expires_at
  AND t.used_at IS NULL
ORDER BY p.expires_at ASC;
