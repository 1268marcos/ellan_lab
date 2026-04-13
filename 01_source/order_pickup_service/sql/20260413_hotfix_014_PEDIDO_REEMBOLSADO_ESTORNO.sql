-- 2. Pedido Reembolsado (Estorno)
DO $$ 
DECLARE 
    v_order_id VARCHAR := gen_random_uuid()::text;
    v_pay_id VARCHAR := gen_random_uuid()::text;
BEGIN
    INSERT INTO public.orders (
        id, user_id, channel, region, totem_id, sku_id, amount_cents, 
        status, payment_method, payment_status, paid_at, cancelled_at, 
        created_at, updated_at, consent_marketing
    )
    VALUES (
        v_order_id, 'ed5ddeb2-40df-4cc9-8507-43c335991e6b', 'KIOSK', 'PT', 
        'PT-GUIMARAES-AZUREM-LK-001', 'cookie_chocolate', 8957, 'REFUNDED', 
        'creditCard', 'REFUNDED', now() - INTERVAL '5 days', now() - INTERVAL '3 days', 
        now() - INTERVAL '5 days', now() - INTERVAL '3 days', 0  -- ← usando 0 em vez de false
    );
    
    INSERT INTO public.payment_transactions (
        id, order_id, gateway, amount_cents, payment_method, status, 
        initiated_at, refunded_at, created_at, updated_at
    )
    VALUES (
        v_pay_id, v_order_id, 'STRIPE', 8957, 'creditCard', 'REFUNDED', 
        now() - INTERVAL '5 days', now() - INTERVAL '3 days', 
        now() - INTERVAL '5 days', now() - INTERVAL '3 days'
    );
    
    INSERT INTO public.financial_ledger (
        id, order_id, payment_transaction_id, entry_type, amount_cents, 
        external_reference, created_at
    )
    VALUES 
    (
        gen_random_uuid()::text, v_order_id, v_pay_id, 'CAPTURE', 8900, 
        'CH_STRIPE_111', now() - INTERVAL '5 days'
    ),
    (
        gen_random_uuid()::text, v_order_id, v_pay_id, 'REFUND', -8900, 
        'RE_STRIPE_222', now() - INTERVAL '3 days'
    );
END $$;