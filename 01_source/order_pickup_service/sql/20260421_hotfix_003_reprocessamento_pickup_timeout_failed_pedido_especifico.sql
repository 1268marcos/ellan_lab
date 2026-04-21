-- 10) Reprocessamento seguro de PICKUP_TIMEOUT FAILED
-- Para um pedido específico:

BEGIN;

UPDATE public.lifecycle_deadlines
SET
    status = 'PENDING',
    locked_at = NULL,
    updated_at = now()
WHERE order_id = 'd0e9afa4-d01f-443b-9e1b-5b267d930c72'
  AND deadline_type = 'PICKUP_TIMEOUT'
  AND status = 'FAILED';

COMMIT;