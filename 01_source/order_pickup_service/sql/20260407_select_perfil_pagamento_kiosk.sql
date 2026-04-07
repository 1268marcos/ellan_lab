--- faça esse primeiro para anotar o id
SELECT
    cp.id,
    cp.profile_code,
    cp.name,
    cp.priority,
    cp.is_active,
    r.code AS region_code,
    ch.code AS channel_code,
    ctx.code AS context_code
FROM capability_profile cp
JOIN capability_region r ON r.id = cp.region_id
JOIN capability_channel ch ON ch.id = cp.channel_id
JOIN capability_context ctx ON ctx.id = cp.context_id
WHERE r.code = 'SP'
  AND ch.code = 'KIOSK'
  AND ctx.code = 'ORDER_CREATION'
  AND cp.is_active = TRUE
ORDER BY cp.priority, cp.id;


-- region_catalog              =  capability_region
-- sales_channel_catalog       =  capability_channel
-- capability_context_catalog  =  capability_context
-- resultado será id = 7

-- com o id acima substituir no lugar 
SELECT
    cp.profile_code,
    pmc.code AS payment_method_code,
    cpm.is_active,
    cpm.is_default,
    cpm.sort_order,
    cpm.rules_json
FROM capability_profile_method cpm
JOIN capability_profile cp ON cp.id = cpm.profile_id
JOIN payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
WHERE cp.id = 7
ORDER BY cpm.sort_order, cpm.id;

-- <PROFILE_ID_ENCONTRADO>  = 7