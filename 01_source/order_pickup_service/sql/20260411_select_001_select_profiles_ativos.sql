SELECT 
    p.id,
    p.profile_code,
    p.name,
    p.priority,
    p.currency,
    r.code AS region_code,
    ch.code AS channel_code,
    ctx.code AS context_code
FROM public.capability_profile p
LEFT JOIN public.capability_region r ON r.id = p.region_id
LEFT JOIN public.capability_channel ch ON ch.id = p.channel_id
LEFT JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE p.is_active = TRUE
ORDER BY p.priority DESC, p.name;