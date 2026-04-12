SELECT *
FROM public.capability_context;

SELECT *
FROM capability_channel;

SELECT 
    p.profile_code,
    p.name,
    r.code AS region_code,
    ch.code AS channel_code,
    p.currency
FROM public.capability_profile p
JOIN public.capability_region r ON r.id = p.region_id
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE ctx.code = 'checkout' AND r.code = 'SP'  -- ou 'order_creation'  ou  'ORDER_CREATION'
ORDER BY ch.code, r.code;

select * from public.capability_profile_constraint;

SELECT
    r.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    crc.code AS requirement_code
FROM public.capability_profile cp
JOIN public.capability_region r ON r.id = cp.region_id
JOIN public.capability_context ctx ON ctx.id = cp.context_id
JOIN public.capability_channel ch ON ch.id = cp.channel_id
JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
LEFT JOIN public.capability_profile_method_requirement cpmr ON cpmr.profile_method_id = cpm.id
LEFT JOIN public.capability_requirement_catalog crc ON crc.id = cpmr.requirement_id
WHERE ch.code = 'kiosk'
  AND ctx.code = 'order_creation'
  AND r.code = 'SP'
ORDER BY r.code, cp.profile_code, pmc.code, crc.code;