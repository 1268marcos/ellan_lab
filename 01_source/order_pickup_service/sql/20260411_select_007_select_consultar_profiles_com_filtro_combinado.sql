SELECT 
    p.id,
    p.profile_code,
    p.name,
    r.code AS region_code,
    ch.code AS channel_code,
    ctx.code AS context_code
FROM public.capability_profile p
JOIN public.capability_region r ON r.id = p.region_id
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE r.code = 'SP' 
  AND ch.code = 'online' 
  AND ctx.code = 'checkout';