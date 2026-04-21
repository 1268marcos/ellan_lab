-- DETECTAR REGISTROS COM OFFSET DIFERENTE DE UTC

SELECT
    'orders' as tabela,
    id,
    created_at,
    paid_at,
    pickup_deadline_at
FROM orders
WHERE
    created_at::text LIKE '%+01%' OR
    paid_at::text LIKE '%+01%' OR
    pickup_deadline_at::text LIKE '%+01%'

UNION ALL

SELECT
    'pickups',
    order_id,
    created_at,
    activated_at,
    expires_at
FROM pickups
WHERE
    created_at::text LIKE '%+01%' OR
    activated_at::text LIKE '%+01%' OR
    expires_at::text LIKE '%+01%'

UNION ALL

SELECT
    'pickup_tokens',
    pickup_id,
    created_at,
    used_at,
    expires_at
FROM pickup_tokens
WHERE
    created_at::text LIKE '%+01%' OR
    expires_at::text LIKE '%+01%'

UNION ALL

SELECT
    'domain_event_outbox',
    aggregate_id,
    created_at,
    occurred_at,
    published_at
FROM domain_event_outbox
WHERE
    created_at::text LIKE '%+01%' OR
    occurred_at::text LIKE '%+01%';