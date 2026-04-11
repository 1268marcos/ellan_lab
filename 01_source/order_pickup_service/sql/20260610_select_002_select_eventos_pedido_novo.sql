SELECT event_key, aggregate_id, event_name, created_at
FROM domain_events
WHERE aggregate_type = 'order'
  AND event_name = 'order.paid'
ORDER BY created_at DESC
LIMIT 10;