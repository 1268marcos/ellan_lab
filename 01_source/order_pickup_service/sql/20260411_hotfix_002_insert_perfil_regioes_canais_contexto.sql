BEGIN;

-- =========================================================
-- HOTFIX: Criação em massa de capability profiles
-- Para todas as regiões com canais online e kiosk
-- =========================================================

-- =========================================================
-- 1. GARANTIR EXISTÊNCIA DOS CANAIS NECESSÁRIOS
-- =========================================================

-- Canal online
INSERT INTO public.capability_channel (code, name, description, is_active, created_at, updated_at)
SELECT 'online', 'Online', 'Canal de checkout online', TRUE, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM public.capability_channel WHERE code = 'online');

UPDATE public.capability_channel
SET name = 'Online', description = 'Canal de checkout online', is_active = TRUE, updated_at = NOW()
WHERE code = 'online';

-- Canal kiosk
INSERT INTO public.capability_channel (code, name, description, is_active, created_at, updated_at)
SELECT 'kiosk', 'Kiosk', 'Canal de terminal físico (self-service)', TRUE, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM public.capability_channel WHERE code = 'kiosk');

UPDATE public.capability_channel
SET name = 'Kiosk', description = 'Canal de terminal físico (self-service)', is_active = TRUE, updated_at = NOW()
WHERE code = 'kiosk';

-- =========================================================
-- 2. GARANTIR EXISTÊNCIA DOS CONTEXTOS
-- =========================================================

-- Contexto checkout (para canal online)
INSERT INTO public.capability_context (channel_id, code, name, description, is_active, created_at, updated_at)
SELECT ch.id, 'checkout', 'Checkout', 'Contexto de checkout público online', TRUE, NOW(), NOW()
FROM public.capability_channel ch
WHERE ch.code = 'online'
  AND NOT EXISTS (
      SELECT 1 FROM public.capability_context ctx
      WHERE ctx.channel_id = ch.id AND ctx.code = 'checkout'
  );

UPDATE public.capability_context ctx
SET name = 'Checkout', description = 'Contexto de checkout público online', is_active = TRUE, updated_at = NOW()
FROM public.capability_channel ch
WHERE ch.code = 'online' AND ctx.channel_id = ch.id AND ctx.code = 'checkout';

-- Contexto order_creation (para canal kiosk)
INSERT INTO public.capability_context (channel_id, code, name, description, is_active, created_at, updated_at)
SELECT ch.id, 'order_creation', 'Criação de Pedido', 'Contexto para criação de pedidos em terminais kiosk', TRUE, NOW(), NOW()
FROM public.capability_channel ch
WHERE ch.code = 'kiosk'
  AND NOT EXISTS (
      SELECT 1 FROM public.capability_context ctx
      WHERE ctx.channel_id = ch.id AND ctx.code = 'order_creation'
  );

UPDATE public.capability_context ctx
SET name = 'Criação de Pedido', description = 'Contexto para criação de pedidos em terminais kiosk', is_active = TRUE, updated_at = NOW()
FROM public.capability_channel ch
WHERE ch.code = 'kiosk' AND ctx.channel_id = ch.id AND ctx.code = 'order_creation';

-- =========================================================
-- 3. PROFILES PARA CANAL ONLINE (TODAS AS REGIÕES)
-- Formato: {REGION_CODE}:online:checkout
-- =========================================================

INSERT INTO public.capability_profile (
    region_id, channel_id, context_id, profile_code, name, priority, currency, is_active, metadata_json, created_at, updated_at, valid_from, valid_until
)
SELECT
    r.id,
    ch.id,
    ctx.id,
    CONCAT(r.code, ':online:checkout'),
    CONCAT(r.name, ' - Online Checkout'),
    100,
    r.default_currency,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW(),
    NULL,
    NULL
FROM public.capability_region r
CROSS JOIN public.capability_channel ch
CROSS JOIN public.capability_context ctx
WHERE ch.code = 'online'
  AND ctx.code = 'checkout'
  AND NOT EXISTS (
      SELECT 1 FROM public.capability_profile p
      WHERE p.profile_code = CONCAT(r.code, ':online:checkout')
  );

-- Update para profiles já existentes
UPDATE public.capability_profile p
SET
    region_id = r.id,
    channel_id = ch.id,
    context_id = ctx.id,
    name = CONCAT(r.name, ' - Online Checkout'),
    priority = 100,
    currency = r.default_currency,
    is_active = TRUE,
    metadata_json = '{}'::jsonb,
    updated_at = NOW(),
    valid_until = NULL
FROM public.capability_region r
CROSS JOIN public.capability_channel ch
CROSS JOIN public.capability_context ctx
WHERE ch.code = 'online'
  AND ctx.code = 'checkout'
  AND p.profile_code = CONCAT(r.code, ':online:checkout');

-- =========================================================
-- 4. PROFILES PARA CANAL KIOSK (TODAS AS REGIÕES)
-- Formato: {REGION_CODE}:kiosk:order_creation (padrão)
-- Nome alternativo: KIOSK_{REGION_CODE}_ORDER_CREATION
-- =========================================================

INSERT INTO public.capability_profile (
    region_id, channel_id, context_id, profile_code, name, priority, currency, is_active, metadata_json, created_at, updated_at, valid_from, valid_until
)
SELECT
    r.id,
    ch.id,
    ctx.id,
    CONCAT(r.code, ':kiosk:order_creation'),
    CONCAT('KIOSK_', r.code, '_ORDER_CREATION'),
    100,
    r.default_currency,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW(),
    NULL,
    NULL
FROM public.capability_region r
CROSS JOIN public.capability_channel ch
CROSS JOIN public.capability_context ctx
WHERE ch.code = 'kiosk'
  AND ctx.code = 'order_creation'
  AND NOT EXISTS (
      SELECT 1 FROM public.capability_profile p
      WHERE p.profile_code = CONCAT(r.code, ':kiosk:order_creation')
  );

-- Update para profiles já existentes
UPDATE public.capability_profile p
SET
    region_id = r.id,
    channel_id = ch.id,
    context_id = ctx.id,
    name = CONCAT('KIOSK_', r.code, '_ORDER_CREATION'),
    priority = 100,
    currency = r.default_currency,
    is_active = TRUE,
    metadata_json = '{}'::jsonb,
    updated_at = NOW(),
    valid_until = NULL
FROM public.capability_region r
CROSS JOIN public.capability_channel ch
CROSS JOIN public.capability_context ctx
WHERE ch.code = 'kiosk'
  AND ctx.code = 'order_creation'
  AND p.profile_code = CONCAT(r.code, ':kiosk:order_creation');

COMMIT;

-- =========================================================
-- VALIDAÇÃO RÁPIDA
-- =========================================================

-- Total de profiles criados/atualizados por canal
SELECT 
    ch.code AS channel_code,
    COUNT(p.id) AS total_profiles
FROM public.capability_profile p
JOIN public.capability_channel ch ON ch.id = p.channel_id
GROUP BY ch.code
ORDER BY ch.code;

-- Amostra dos profiles online:checkout
SELECT
    p.id,
    p.profile_code,
    p.name,
    p.currency,
    p.priority,
    p.is_active,
    r.code AS region_code,
    ch.code AS channel_code,
    ctx.code AS context_code
FROM public.capability_profile p
JOIN public.capability_region r ON r.id = p.region_id
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE ch.code = 'online'
ORDER BY r.code
LIMIT 10;

-- Amostra dos profiles kiosk:order_creation
SELECT
    p.id,
    p.profile_code,
    p.name,
    p.currency,
    p.priority,
    p.is_active,
    r.code AS region_code,
    ch.code AS channel_code,
    ctx.code AS context_code
FROM public.capability_profile p
JOIN public.capability_region r ON r.id = p.region_id
JOIN public.capability_channel ch ON ch.id = p.channel_id
JOIN public.capability_context ctx ON ctx.id = p.context_id
WHERE ch.code = 'kiosk'
ORDER BY r.code
LIMIT 10;