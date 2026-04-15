-- VER TODOS OS DETALHES DO PEDIDO É UM RESUMO COM 23 LINHAS
-- altere o número do pedido
SELECT * FROM get_order_complete_info('d0b9500f-a2a5-4e48-bdd5-8d409efe9568');

-- Opção 2 - Ver apenas uma seção específica:
-- SELECT data FROM get_order_complete_info('d0b9500f-a2a5-4e48-bdd5-8d409efe9568')
-- WHERE section = '1. PEDIDO PRINCIPAL';

-- Opção 3 - Ver apenas o resumo completo:
-- SELECT data FROM get_order_complete_info('d0b9500f-a2a5-4e48-bdd5-8d409efe9568')
-- WHERE section = '23. RESUMO COMPLETO (JSON)';

-- Opção 4 - Formatar o JSON para melhor visualização:
-- SELECT jsonb_pretty(data) 
-- FROM get_order_complete_info('d0b9500f-a2a5-4e48-bdd5-8d409efe9568')
-- WHERE section = '23. RESUMO COMPLETO (JSON)';