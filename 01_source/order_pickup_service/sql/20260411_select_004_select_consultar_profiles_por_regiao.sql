SELECT 
    p.profile_code,
    p.name,
    ch.code AS channel_code,
    ctx.code AS context_code,
    p.currency,
    p.priority
FROM public.capability_profile p
JOIN public.capability_region r ON r.id = p.region_id
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE r.code = 'SP'  -- ou qualquer outra região
ORDER BY ch.code, ctx.code;