SELECT 
    p.id,
    p.profile_code,
    p.name,
    r.code AS region_code,
    ch.code AS channel_code,
    ctx.code AS context_code,
    COUNT(DISTINCT pa.id) AS total_actions,
    COUNT(DISTINCT pm.id) AS total_methods,
    COUNT(DISTINCT pc.id) AS total_constraints,
    COUNT(DISTINCT pt.id) AS total_targets
FROM public.capability_profile p
LEFT JOIN public.capability_region r ON r.id = p.region_id
LEFT JOIN public.capability_channel ch ON ch.id = p.channel_id
LEFT JOIN public.capability_context ctx ON ctx.id = p.context_id
LEFT JOIN public.capability_profile_action pa ON pa.profile_id = p.id
LEFT JOIN public.capability_profile_method pm ON pm.profile_id = p.id
LEFT JOIN public.capability_profile_constraint pc ON pc.profile_id = p.id
LEFT JOIN public.capability_profile_target pt ON pt.profile_id = p.id
WHERE p.profile_code = 'KIOSK_SP_ORDER_CREATION'
GROUP BY p.id, r.code, ch.code, ctx.code;