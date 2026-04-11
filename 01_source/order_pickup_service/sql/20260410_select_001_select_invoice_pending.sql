SELECT id, order_id, status, retry_count, error_message, created_at
FROM invoices
ORDER BY created_at DESC
LIMIT 20;