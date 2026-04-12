SELECT 
    p.id,
    p.profile_code,
    p.name,
    p.priority,
    p.currency,
    p.is_active,
    p.metadata_json,
    p.created_at,
    p.updated_at,
    r.code AS region_code,
    r.name AS region_name,
    ch.code AS channel_code,
    ch.name AS channel_name,
    ctx.code AS context_code,
    ctx.name AS context_name
FROM public.capability_profile p
LEFT JOIN public.capability_region r ON r.id = p.region_id
LEFT JOIN public.capability_channel ch ON ch.id = p.channel_id
LEFT JOIN public.capability_context ctx ON ctx.id = p.context_id;