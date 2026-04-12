SELECT 
    ch.code AS channel_code,
    ctx.code AS context_code,
    COUNT(*) AS total_profiles,
    COUNT(DISTINCT r.code) AS total_regions
FROM public.capability_profile p
JOIN public.capability_region r ON r.id = p.region_id
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
GROUP BY ch.code, ctx.code
ORDER BY ch.code, ctx.code;