-- validação financeira

SELECT SUM(amount_cents) FROM financial_ledger WHERE entry_type = 'CAPTURE' AND status = 'POSTED';

-- ou 
-- SELECT SUM(amount_cents) FROM orders WHERE status IN ('PICKED_UP','DISPENSED') AND deleted_at IS NULL;
