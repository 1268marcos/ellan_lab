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
    r.default_currency,
    ch.code AS channel_code,
    ch.name AS channel_name,
    ctx.code AS context_code,
    ctx.name AS context_name
FROM public.capability_profile p
JOIN public.capability_region r ON r.id = p.region_id
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE p.profile_code IN ('SP:online:checkout', 'SP:kiosk:checkout', 'KIOSK_SP_ORDER_CREATION')
ORDER BY p.profile_code;