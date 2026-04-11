SELECT event_key, order_id, status, error_message, created_at
FROM billing_processed_events
ORDER BY created_at DESC
LIMIT 50;