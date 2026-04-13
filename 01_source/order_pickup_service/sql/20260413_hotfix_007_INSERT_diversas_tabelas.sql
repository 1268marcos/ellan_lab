-- 1. Criar wallets zeradas para todos os usuários existentes
INSERT INTO public.user_wallets (id, user_id, balance_cents, currency)
SELECT gen_random_uuid()::text, u.id, 0, 'BRL'
FROM public.users u
WHERE u.id NOT IN (SELECT user_id FROM public.user_wallets);

-- 2. Popular regras padrão nos lockers existentes
UPDATE public.lockers SET payment_rules = jsonb_set(payment_rules, '{allowed_methods}', '["pix", "creditCard", "debitCard", "apple_pay"]'::jsonb)
WHERE payment_rules->'allowed_methods' = '[]'::jsonb;

-- 3. Backfill de instruções para pedidos históricos (opcional, mas recomendado)
-- Cria instruções "CAPTURED" para pedidos já finalizados
INSERT INTO public.payment_instructions (id, order_id, instruction_type, amount_cents, currency, status, captured_at, created_at, updated_at)
SELECT gen_random_uuid()::text, o.id, 'CAPTURE_NOW', o.amount_cents, o.currency, 'CAPTURED', o.paid_at, o.created_at, o.updated_at
FROM public.orders o
WHERE o.status IN ('DISPENSED', 'PICKED_UP', 'REFUNDED')
AND o.id NOT IN (SELECT order_id FROM public.payment_instructions);

-- 4. Migrar métodos salvos (apenas se seu gateway já fornece tokens e você tem consentimento)
-- Exemplo conceitual. Na prática, faça via script seguro ou comece do zero para novos cadastros.
-- INSERT INTO public.saved_payment_methods (...) SELECT ... FROM payment_transactions WHERE ...;