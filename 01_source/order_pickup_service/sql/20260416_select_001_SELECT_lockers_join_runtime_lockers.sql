------------------------------------------------------
-- Analisando as duas tabelas lado a lado, identifiquei várias inconsistências e 
-- anomalias que provavelmente precisam de explicação. Vou organizar por categoria:
--
-- 1. slots_count divergente entre tabelas
-- O conjunto de todos os registros na tabela lockers mostram slots_count = 24, mas em 
-- runtime_lockers os valores são diferentes:
-- Lockerlockers.slots_countruntime_lockers.slot_count_totalSP-CARAPICUIBA-LK-0022460SP-ALPHAVILLE-SHOP-LK-0012432RJ-CAPITAL-CENTRO-LK-0012430SP-VILAOLIMPIA-FOOD-LK-0012420
-- Parece que o campo slots_count da tabela lockers não está sendo atualizado quando o runtime detecta mudanças físicas no equipamento.
-- 
-- 2. machine_id = NULL em todos os lockers
-- A tabela lockers tem machine_id = NULL para todos os registros, enquanto runtime_lockers tem o campo preenchido. O vínculo físico entre o locker lógico e a máquina parece não estar sendo propagado.
-- 
-- 3. slots_available = 0 em todos os lockers
-- O conjunto de todos os lockers mostram slots_available = 0. Ou todos estão ocupados ao 
-- mesmo tempo (improvável), ou esse campo simplesmente não está sendo atualizado pelo sistema de runtime.
--
-- 4. PIX e métodos de pagamento inconsistentes por país
-- LockerPaísProblemaES-MADRID-CENTRO-LK-001🇪🇸 Espanhaallowed_payment_methods inclui 
-- pix — método exclusivamente brasileiroPT-MAIA-CENTRO-LK-001🇵🇹 Portugalpayment_rules referencia pix e 
-- apple_pay, mas runtime tem mbway/multibancoPT-GUIMARAES-AZUREM-LK-001🇵🇹 PortugalMesmo problema acima
-- O payment_rules (JSON na tabela lockers) parece ter sido gerado com um template brasileiro padrão e nunca ajustado por país.
-- 
-- 5. payment_methods_json = [] no runtime para lockers ativos
-- RJ-CAPITAL-CENTRO-LK-001, ES-MADRID-CENTRO-LK-001 e PR-CAPITAL-SANTAFELICIDADE-LK-001 têm payment_methods_json vazio 
-- no runtime — sem nenhum método de pagamento configurado, mesmo com runtime_enabled = True.
--
-- 6. giftCard no runtime, ausente nos lockers
-- O runtime lista giftCard nos métodos de pagamento de vários lockers brasileiros e portugueses, mas 
-- esse método não aparece em nenhum allowed_payment_methods ou payment_rules da tabela lockers.
-- 
-- Resumo do que parece estar acontecendo
-- A tabela lockers parece ser a fonte de configuração lógica, e runtime_lockers reflete o 
-- estado real da máquina. As divergências sugerem que:
-- 
-- A sincronização entre as duas tabelas está quebrada ou não implementada
-- O seed/criação dos registros em lockers usou um template genérico sem adequação por país
-- Campos como slots_available e machine_id dependem de um processo de runtime que ainda não está rodando corretamente
-- 
-- O JOIN está correto e vai funcionar. Alguns pontos para considerar antes de usar:
--
-- O que está certo:
--
-- ON l.id = rl.locker_id é o vínculo correto entre as tabelas
-- LEFT JOIN é a escolha certa — garante que lockers sem correspondência em lockers ainda apareçam
-- O filtro active = TRUE AND runtime_enabled = TRUE vai retornar 8 lockers dos 11 (exclui RJ, ES e PR que estão inativos)
--
-- Pontos de atenção:
-- 
-- 1. deleted_at não está sendo verificado
-- A tabela lockers tem soft delete. Adicione ao WHERE:
-- sqlAND (l.deleted_at IS NULL OR l.id IS NULL)
-- 
-- 2. Inconsistência de slots vai aparecer aqui
-- rl.slot_count_total virá diferente do l.slots_count — vale incluir os dois para evidenciar:
-- sqll.slots_count AS slots_count_central,
-- rl.slot_count_total AS slots_count_runtime,
-- 
-- 3. payment_methods_json vazio no runtime
-- Para os 3 lockers ativos com [], a query vai trazer o campo vazio sem alertar. Considere adicionar um flag:
-- sqlCASE WHEN rl.payment_methods_json = '[]' THEN TRUE ELSE FALSE END AS sem_pagamento_configurado
-- 
-- 4. Coordenadas estão faltando
-- Se houver qualquer uso downstream (mapa, API de localização), vale incluir:
-- l.latitude,
-- l.longitude
--
-- IMPORTANTE - adicionado flags de inconsistência (slots_divergentes)
-- Isso é nível produção — dá para depois:
-- logar divergências
-- alertar inconsistência runtime vs central
-- evitar bugs de estoque real
------------------------------------------------------------
SELECT
    rl.locker_id,
    rl.machine_id,
    rl.display_name,
    rl.region,
    rl.country,
    rl.timezone,
    rl.operator_id,
    rl.temperature_zone,
    rl.security_level,
    rl.active,
    rl.runtime_enabled,
    rl.mqtt_region,
    rl.mqtt_locker_id,
    rl.topology_version,
    rl.payment_methods_json,
    rl.slot_count_total                                              AS slots_runtime,

    -- Central
    l.address_line,
    l.address_number,
    l.address_extra,
    l.district,
    l.city,
    l.state,
    l.postal_code,
    l.latitude,
    l.longitude,
    l.slots_count                                                    AS slots_central,

    -- Flags de inconsistência
    rl.slot_count_total <> l.slots_count                            AS slots_divergentes,
    rl.payment_methods_json = '[]'                                  AS sem_pagamento_runtime

FROM public.runtime_lockers rl
LEFT JOIN public.lockers l
    ON l.id = rl.locker_id
   AND l.deleted_at IS NULL

WHERE rl.active = TRUE
  AND rl.runtime_enabled = TRUE
ORDER BY rl.region, rl.display_name;