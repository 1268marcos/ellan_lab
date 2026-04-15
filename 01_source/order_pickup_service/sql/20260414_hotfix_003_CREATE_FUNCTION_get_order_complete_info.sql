-- =====================================================
-- FUNÇÃO: get_order_complete_info(order_id TEXT)
-- DESCRIÇÃO: Retorna todas as informações relacionadas a um pedido
-- como usar:
-- SELECT * FROM get_order_complete_info('d0b9500f-a2a5-4e48-bdd5-8d409efe9568');
-- resultado: RESUMO COM 23 LINHAS
-- =====================================================

-- Se precisar remover/recriar a função:
-- Remover função existente
-- DROP FUNCTION IF EXISTS get_order_complete_info(TEXT);
-- Depois recriar com o código abaixo


CREATE OR REPLACE FUNCTION get_order_complete_info(p_order_id TEXT)
RETURNS TABLE(
    section TEXT,
    data JSONB
) LANGUAGE plpgsql AS $$
BEGIN

-- 1. Pedido principal
RETURN QUERY
SELECT '1. PEDIDO PRINCIPAL'::TEXT, 
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.orders WHERE id = p_order_id) t;

-- 2. Itens do pedido
RETURN QUERY
SELECT '2. ITENS DO PEDIDO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.order_items WHERE order_id = p_order_id) t;

-- 3. Alocação de slot
RETURN QUERY
SELECT '3. ALOCAÇÃO DE SLOT'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.allocations WHERE order_id = p_order_id) t;

-- 4. Pickup
RETURN QUERY
SELECT '4. PICKUP'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.pickups WHERE order_id = p_order_id) t;

-- 5. Tokens de pickup
RETURN QUERY
SELECT '5. TOKENS DE PICKUP'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(pt)), '[]'::jsonb)
FROM public.pickup_tokens pt
INNER JOIN public.pickups p ON pt.pickup_id = p.id
WHERE p.order_id = p_order_id;

-- 6. Transações de pagamento
RETURN QUERY
SELECT '6. TRANSAÇÕES DE PAGAMENTO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.payment_transactions WHERE order_id = p_order_id) t;

-- 7. Instruções de pagamento
RETURN QUERY
SELECT '7. INSTRUÇÕES DE PAGAMENTO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.payment_instructions WHERE order_id = p_order_id) t;

-- 8. Divisões de pagamento
RETURN QUERY
SELECT '8. DIVISÕES DE PAGAMENTO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.payment_splits WHERE order_id = p_order_id) t;

-- 9. Documentos fiscais
RETURN QUERY
SELECT '9. DOCUMENTOS FISCAIS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.fiscal_documents WHERE order_id = p_order_id) t;

-- 10. Notas fiscais (invoices)
RETURN QUERY
SELECT '10. NOTAS FISCAIS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.invoices WHERE order_id = p_order_id) t;

-- 11. Prazos do ciclo de vida
RETURN QUERY
SELECT '11. PRAZOS DO CICLO DE VIDA'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.lifecycle_deadlines WHERE order_id = p_order_id) t;

-- 12. Eventos analíticos
RETURN QUERY
SELECT '12. EVENTOS ANALÍTICOS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.analytics_facts WHERE order_id = p_order_id) t;

-- 13. Eventos processados de faturamento
RETURN QUERY
SELECT '13. EVENTOS DE FATURAMENTO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.billing_processed_events WHERE order_id = p_order_id) t;

-- 14. Notificações
RETURN QUERY
SELECT '14. NOTIFICAÇÕES'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.notification_logs WHERE order_id = p_order_id) t;

-- 15. Eventos de domínio
RETURN QUERY
SELECT '15. EVENTOS DE DOMÍNIO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.domain_events 
      WHERE aggregate_id = p_order_id AND aggregate_type = 'Order') t;

-- 16. Outbox de eventos
RETURN QUERY
SELECT '16. OUTBOX DE EVENTOS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.domain_event_outbox 
      WHERE aggregate_id = p_order_id) t;

-- 17. Registros de auditoria
RETURN QUERY
SELECT '17. REGISTROS DE AUDITORIA'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.audit_logs 
      WHERE target_id = p_order_id AND target_type = 'Order') t;

-- 18. Créditos
RETURN QUERY
SELECT '18. CRÉDITOS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.credits WHERE order_id = p_order_id) t;

-- 19. Histórico de ocupação de slot (via allocations)
RETURN QUERY
SELECT '19. HISTÓRICO DE OCUPAÇÃO DE SLOT'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(soh)), '[]'::jsonb)
FROM public.slot_occupancy_history soh
WHERE soh.allocation_id IN (SELECT id FROM public.allocations WHERE order_id = p_order_id);

-- 20. Livro razão financeiro
RETURN QUERY
SELECT '20. LIVRO RAZÃO FINANCEIRO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.financial_ledger WHERE order_id = p_order_id) t;

-- 21. Detalhes do locker (via allocations)
RETURN QUERY
SELECT '21. DETALHES DO LOCKER'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(l)), '[]'::jsonb)
FROM public.lockers l
WHERE l.id IN (SELECT locker_id FROM public.allocations WHERE order_id = p_order_id AND locker_id IS NOT NULL);

-- 22. Detalhes do slot (via allocations)
RETURN QUERY
SELECT '22. DETALHES DO SLOT'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(ls)), '[]'::jsonb)
FROM public.locker_slots ls
WHERE ls.locker_id IN (SELECT locker_id FROM public.allocations WHERE order_id = p_order_id AND locker_id IS NOT NULL)
  AND ls.slot_label IN (SELECT slot::TEXT FROM public.allocations WHERE order_id = p_order_id);

-- 23. RESUMO COMPLETO EM JSON
RETURN QUERY
SELECT '23. RESUMO COMPLETO (JSON)'::TEXT,
       jsonb_build_object(
           'order', COALESCE((SELECT to_jsonb(t) FROM (SELECT * FROM public.orders WHERE id = p_order_id) t), '{}'::jsonb),
           'items', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.order_items WHERE order_id = p_order_id) t), '[]'::jsonb),
           'allocation', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.allocations WHERE order_id = p_order_id) t), '[]'::jsonb),
           'pickup', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.pickups WHERE order_id = p_order_id) t), '[]'::jsonb),
           'payment_transactions', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.payment_transactions WHERE order_id = p_order_id) t), '[]'::jsonb),
           'payment_instructions', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.payment_instructions WHERE order_id = p_order_id) t), '[]'::jsonb),
           'fiscal_documents', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.fiscal_documents WHERE order_id = p_order_id) t), '[]'::jsonb),
           'invoices', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.invoices WHERE order_id = p_order_id) t), '[]'::jsonb),
           'notifications', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.notification_logs WHERE order_id = p_order_id) t), '[]'::jsonb),
           'domain_events', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.domain_events WHERE aggregate_id = p_order_id AND aggregate_type = 'Order') t), '[]'::jsonb),
           'audit_logs', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.audit_logs WHERE target_id = p_order_id AND target_type = 'Order') t), '[]'::jsonb),
           'financial_ledger', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.financial_ledger WHERE order_id = p_order_id) t), '[]'::jsonb)
       );

END;
$$;