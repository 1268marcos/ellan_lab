-- 1. Pedido Completo (Sucesso)
DO $$ 
DECLARE 
    v_order_id VARCHAR := gen_random_uuid()::text;
    v_pay_id VARCHAR := gen_random_uuid()::text;
BEGIN
    INSERT INTO public.orders (id, user_id, channel, region, totem_id, sku_id, amount_cents, status, payment_method, payment_status, paid_at, picked_up_at, created_at, updated_at)
    VALUES (v_order_id, '6b15af19-874b-41ad-a89e-2e2d6e88e9e7', 'ONLINE', 'SP', ' SP-ALPHAVILLE-SHOP-LK-001, 'cookie_laranja', 1968, 'PICKED_UP', 'pix', 'APPROVED', now() - INTERVAL '2 days', now() - INTERVAL '1 day', now() - INTERVAL '2 days', now() - INTERVAL '1 day');
    
    INSERT INTO public.payment_transactions (id, order_id, gateway, amount_cents, payment_method, status, initiated_at, approved_at, created_at, updated_at)
    VALUES (v_pay_id, v_order_id, 'GATEWAY_ASAAS', 1968, 'pix', 'APPROVED', now() - INTERVAL '2 days', now() - INTERVAL '2 days', now() - INTERVAL '2 days', now() - INTERVAL '2 days');
    
    INSERT INTO public.financial_ledger (id, order_id, payment_transaction_id, entry_type, amount_cents, external_reference, created_at)
    VALUES (gen_random_uuid()::text, v_order_id, v_pay_id, 'CAPTURE', 1968, 'NSU_ASAAS_998877', now() - INTERVAL '2 days');
    
    INSERT INTO public.audit_logs (actor_id, action, target_type, target_id, new_state, occurred_at)
    VALUES ('6b15af19-874b-41ad-a89e-2e2d6e88e9e7', 'ORDER_LIFECYCLE_COMPLETE', 'ORDER', v_order_id, '{"status":"PICKED_UP"}', now() - INTERVAL '1 day');
END $$;
