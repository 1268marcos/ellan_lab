-- Rollback da transação atual
ROLLBACK;

-- TRUNCATE com CASCADE (já funcionou)
TRUNCATE TABLE public.capability_profile CASCADE;

-- Agora recriar todos os profiles (sem as colunas valid_from/valid_until se não forem necessárias)
BEGIN;

INSERT INTO public.capability_profile (
    region_id, 
    channel_id, 
    context_id, 
    profile_code, 
    name, 
    priority, 
    currency, 
    is_active, 
    metadata_json, 
    created_at, 
    updated_at
)
-- 1. Profiles online:checkout (formato: REGION:online:checkout)
SELECT
    r.id,
    ch.id,
    ctx_checkout_online.id,
    CONCAT(r.code, ':online:checkout'),
    CONCAT(r.name, ' - Online Checkout'),
    100,
    r.default_currency,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM public.capability_region r
CROSS JOIN public.capability_channel ch
CROSS JOIN LATERAL (SELECT id FROM public.capability_context WHERE code = 'checkout' AND channel_id = ch.id) ctx_checkout_online
WHERE ch.code = 'online'

UNION ALL

-- 2. Profiles kiosk:checkout (formato: REGION:kiosk:checkout)
SELECT
    r.id,
    ch.id,
    ctx_checkout_kiosk.id,
    CONCAT(r.code, ':kiosk:checkout'),
    CONCAT(r.name, ' - Kiosk Checkout'),
    100,
    r.default_currency,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM public.capability_region r
CROSS JOIN public.capability_channel ch
CROSS JOIN LATERAL (SELECT id FROM public.capability_context WHERE code = 'checkout' AND channel_id = ch.id) ctx_checkout_kiosk
WHERE ch.code = 'kiosk'

UNION ALL

-- 3. Profiles kiosk:order_creation (formato: KIOSK_REGION_ORDER_CREATION)
SELECT
    r.id,
    ch.id,
    ctx_order.id,
    CONCAT('KIOSK_', r.code, '_ORDER_CREATION'),
    CONCAT('KIOSK_', r.code, '_ORDER_CREATION'),
    100,
    r.default_currency,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM public.capability_region r
CROSS JOIN public.capability_channel ch
CROSS JOIN LATERAL (SELECT id FROM public.capability_context WHERE code = 'order_creation' AND channel_id = ch.id) ctx_order
WHERE ch.code = 'kiosk';

COMMIT;

-- =========================================================
-- VALIDAÇÃO COMPLETA
-- =========================================================

-- Total de profiles por tipo
SELECT 
    ch.code AS channel,
    ctx.code AS context,
    COUNT(*) AS total
FROM public.capability_profile p
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
GROUP BY ch.code, ctx.code
ORDER BY ch.code, ctx.code;

-- Verificar profiles para SP (deve ter 3)
SELECT
    p.profile_code,
    p.name,
    p.currency,
    p.is_active,
    r.code AS region_code,
    ch.code AS channel_code,
    ctx.code AS context_code
FROM public.capability_profile p
JOIN public.capability_region r ON r.id = p.region_id
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE r.code = 'SP'
ORDER BY ch.code, ctx.code;

-- Verificar profiles para PT (deve ter 3)
SELECT
    p.profile_code,
    p.name,
    p.currency,
    p.is_active,
    r.code AS region_code,
    ch.code AS channel_code,
    ctx.code AS context_code
FROM public.capability_profile p
JOIN public.capability_region r ON r.id = p.region_id
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE r.code = 'PT'
ORDER BY ch.code, ctx.code;

-- Estatísticas finais
SELECT 
    'online:checkout' as profile_type,
    COUNT(*) as total
FROM public.capability_profile p
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE ch.code = 'online' AND ctx.code = 'checkout'

UNION ALL

SELECT 
    'kiosk:checkout' as profile_type,
    COUNT(*) as total
FROM public.capability_profile p
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE ch.code = 'kiosk' AND ctx.code = 'checkout'

UNION ALL

SELECT 
    'kiosk:order_creation (KIOSK_*)' as profile_type,
    COUNT(*) as total
FROM public.capability_profile p
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE ch.code = 'kiosk' AND ctx.code = 'order_creation'

UNION ALL

SELECT 
    'TOTAL GERAL' as profile_type,
    COUNT(*) as total
FROM public.capability_profile;

-- Verificar exemplo específico do formato solicitado
SELECT 
    profile_code,
    name,
    currency,
    '✅ CORRETO' as status
FROM public.capability_profile 
WHERE profile_code = 'KIOSK_SP_ORDER_CREATION';