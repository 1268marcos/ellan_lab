BEGIN;

-- =========================================================
-- HOTFIX: capability profile ausente para
-- region=SP, channel=online, context=checkout
-- =========================================================

-- 1) Região SP
INSERT INTO public.capability_region (
    code,
    name,
    country_code,
    continent,
    default_currency,
    is_active,
    metadata_json,
    created_at,
    updated_at
)
SELECT
    'SP',
    'São Paulo',
    'BR',
    'South America',
    'BRL',
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1
    FROM public.capability_region
    WHERE code = 'SP'
);

UPDATE public.capability_region
SET
    name = 'São Paulo',
    country_code = 'BR',
    continent = 'South America',
    default_currency = 'BRL',
    is_active = TRUE,
    updated_at = NOW()
WHERE code = 'SP';

-- 2) Canal online
INSERT INTO public.capability_channel (
    code,
    name,
    description,
    is_active,
    created_at,
    updated_at
)
SELECT
    'online',
    'Online',
    'Canal de checkout online',
    TRUE,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1
    FROM public.capability_channel
    WHERE code = 'online'
);

UPDATE public.capability_channel
SET
    name = 'Online',
    description = 'Canal de checkout online',
    is_active = TRUE,
    updated_at = NOW()
WHERE code = 'online';

-- 3) Contexto checkout vinculado ao canal online
INSERT INTO public.capability_context (
    channel_id,
    code,
    name,
    description,
    is_active,
    created_at,
    updated_at
)
SELECT
    ch.id,
    'checkout',
    'Checkout',
    'Contexto de checkout público online',
    TRUE,
    NOW(),
    NOW()
FROM public.capability_channel ch
WHERE ch.code = 'online'
  AND NOT EXISTS (
      SELECT 1
      FROM public.capability_context ctx
      WHERE ctx.channel_id = ch.id
        AND ctx.code = 'checkout'
  );

UPDATE public.capability_context ctx
SET
    name = 'Checkout',
    description = 'Contexto de checkout público online',
    is_active = TRUE,
    updated_at = NOW()
FROM public.capability_channel ch
WHERE ch.code = 'online'
  AND ctx.channel_id = ch.id
  AND ctx.code = 'checkout';

-- 4) Profile SP:online:checkout
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
    updated_at,
    valid_from,
    valid_until
)
SELECT
    r.id,
    ch.id,
    ctx.id,
    'SP:online:checkout',
    'São Paulo - Online Checkout',
    100,
    'BRL',
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW(),
    NULL,
    NULL
FROM public.capability_region r
JOIN public.capability_channel ch
    ON ch.code = 'online'
JOIN public.capability_context ctx
    ON ctx.channel_id = ch.id
   AND ctx.code = 'checkout'
WHERE r.code = 'SP'
  AND NOT EXISTS (
      SELECT 1
      FROM public.capability_profile p
      WHERE p.profile_code = 'SP:online:checkout'
  );

UPDATE public.capability_profile p
SET
    region_id = r.id,
    channel_id = ch.id,
    context_id = ctx.id,
    name = 'São Paulo - Online Checkout',
    priority = 100,
    currency = 'BRL',
    is_active = TRUE,
    metadata_json = '{}'::jsonb,
    updated_at = NOW(),
    valid_until = NULL
FROM public.capability_region r
JOIN public.capability_channel ch
    ON ch.code = 'online'
JOIN public.capability_context ctx
    ON ctx.channel_id = ch.id
   AND ctx.code = 'checkout'
WHERE r.code = 'SP'
  AND p.profile_code = 'SP:online:checkout';

COMMIT;

-- =========================================================
-- VALIDAÇÃO RÁPIDA
-- =========================================================
SELECT
    p.id,
    p.profile_code,
    p.name,
    p.currency,
    p.priority,
    p.is_active,
    r.code  AS region_code,
    ch.code AS channel_code,
    ctx.code AS context_code
FROM public.capability_profile p
JOIN public.capability_region r
    ON r.id = p.region_id
JOIN public.capability_channel ch
    ON ch.id = p.channel_id
JOIN public.capability_context ctx
    ON ctx.id = p.context_id
WHERE p.profile_code = 'SP:online:checkout';