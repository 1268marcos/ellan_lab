-- 10) Reprocessamento seguro de PICKUP_TIMEOUT FAILED
BEGIN;

UPDATE public.lifecycle_deadlines d
SET
    status = 'PENDING',
    locked_at = NULL,
    updated_at = now()
WHERE d.deadline_type = 'PICKUP_TIMEOUT'
  AND d.status = 'FAILED'
  AND EXISTS (
      SELECT 1
      FROM public.orders o
      WHERE o.id = d.order_id
        AND o.status = 'PAID_PENDING_PICKUP'
        AND o.payment_status = 'APPROVED'
  );

COMMIT;
