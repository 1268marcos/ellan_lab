BEGIN;

-- =========================================================
-- HOTFIX 5B
-- Copiar capability de:
--   kiosk:checkout
-- para:
--   kiosk:order_creation
--
-- Copia:
--   - methods
--   - interfaces
--   - requirements
-- =========================================================

-- =========================================================
-- 1) COPIAR METHODS
-- =========================================================
WITH source_profiles AS (
    SELECT cp.id, cp.region_id
    FROM public.capability_profile cp
    JOIN public.capability_context ctx ON ctx.id = cp.context_id
    JOIN public.capability_channel ch ON ch.id = cp.channel_id
    WHERE ctx.code = 'checkout'
      AND ch.code = 'kiosk'
),
target_profiles AS (
    SELECT cp.id, cp.region_id
    FROM public.capability_profile cp
    JOIN public.capability_context ctx ON ctx.id = cp.context_id
    JOIN public.capability_channel ch ON ch.id = cp.channel_id
    WHERE ctx.code = 'order_creation'
      AND ch.code = 'kiosk'
),
profile_map AS (
    SELECT
        sp.id AS source_profile_id,
        tp.id AS target_profile_id
    FROM source_profiles sp
    JOIN target_profiles tp
      ON tp.region_id = sp.region_id
)
INSERT INTO public.capability_profile_method (
    profile_id,
    payment_method_id,
    label,
    sort_order,
    is_default,
    is_active,
    rules_json,
    created_at,
    updated_at
)
SELECT
    pm.target_profile_id,
    cpm.payment_method_id,
    cpm.label,
    cpm.sort_order,
    cpm.is_default,
    cpm.is_active,
    cpm.rules_json,
    NOW(),
    NOW()
FROM public.capability_profile_method cpm
JOIN profile_map pm
  ON pm.source_profile_id = cpm.profile_id
WHERE NOT EXISTS (
    SELECT 1
    FROM public.capability_profile_method x
    WHERE x.profile_id = pm.target_profile_id
      AND x.payment_method_id = cpm.payment_method_id
);

-- =========================================================
-- 2) COPIAR INTERFACES
-- =========================================================
WITH source_profiles AS (
    SELECT cp.id, cp.region_id
    FROM public.capability_profile cp
    JOIN public.capability_context ctx ON ctx.id = cp.context_id
    JOIN public.capability_channel ch ON ch.id = cp.channel_id
    WHERE ctx.code = 'checkout'
      AND ch.code = 'kiosk'
),
target_profiles AS (
    SELECT cp.id, cp.region_id
    FROM public.capability_profile cp
    JOIN public.capability_context ctx ON ctx.id = cp.context_id
    JOIN public.capability_channel ch ON ch.id = cp.channel_id
    WHERE ctx.code = 'order_creation'
      AND ch.code = 'kiosk'
),
profile_map AS (
    SELECT
        sp.id AS source_profile_id,
        tp.id AS target_profile_id
    FROM source_profiles sp
    JOIN target_profiles tp
      ON tp.region_id = sp.region_id
)
INSERT INTO public.capability_profile_method_interface (
    profile_method_id,
    payment_interface_id,
    sort_order,
    is_default,
    is_active,
    config_json,
    created_at,
    updated_at
)
SELECT
    target_cpm.id,
    cpmi.payment_interface_id,
    cpmi.sort_order,
    cpmi.is_default,
    cpmi.is_active,
    cpmi.config_json,
    NOW(),
    NOW()
FROM public.capability_profile_method_interface cpmi
JOIN public.capability_profile_method source_cpm
  ON source_cpm.id = cpmi.profile_method_id
JOIN profile_map pm
  ON pm.source_profile_id = source_cpm.profile_id
JOIN public.capability_profile_method target_cpm
  ON target_cpm.profile_id = pm.target_profile_id
 AND target_cpm.payment_method_id = source_cpm.payment_method_id
WHERE NOT EXISTS (
    SELECT 1
    FROM public.capability_profile_method_interface x
    WHERE x.profile_method_id = target_cpm.id
      AND x.payment_interface_id = cpmi.payment_interface_id
);

-- =========================================================
-- 3) COPIAR REQUIREMENTS
-- =========================================================
WITH source_profiles AS (
    SELECT cp.id, cp.region_id
    FROM public.capability_profile cp
    JOIN public.capability_context ctx ON ctx.id = cp.context_id
    JOIN public.capability_channel ch ON ch.id = cp.channel_id
    WHERE ctx.code = 'checkout'
      AND ch.code = 'kiosk'
),
target_profiles AS (
    SELECT cp.id, cp.region_id
    FROM public.capability_profile cp
    JOIN public.capability_context ctx ON ctx.id = cp.context_id
    JOIN public.capability_channel ch ON ch.id = cp.channel_id
    WHERE ctx.code = 'order_creation'
      AND ch.code = 'kiosk'
),
profile_map AS (
    SELECT
        sp.id AS source_profile_id,
        tp.id AS target_profile_id
    FROM source_profiles sp
    JOIN target_profiles tp
      ON tp.region_id = sp.region_id
)
INSERT INTO public.capability_profile_method_requirement (
    profile_method_id,
    requirement_id,
    is_required,
    requirement_scope,
    validation_json,
    created_at,
    updated_at
)
SELECT
    target_cpm.id,
    cpmr.requirement_id,
    cpmr.is_required,
    cpmr.requirement_scope,
    cpmr.validation_json,
    NOW(),
    NOW()
FROM public.capability_profile_method_requirement cpmr
JOIN public.capability_profile_method source_cpm
  ON source_cpm.id = cpmr.profile_method_id
JOIN profile_map pm
  ON pm.source_profile_id = source_cpm.profile_id
JOIN public.capability_profile_method target_cpm
  ON target_cpm.profile_id = pm.target_profile_id
 AND target_cpm.payment_method_id = source_cpm.payment_method_id
WHERE NOT EXISTS (
    SELECT 1
    FROM public.capability_profile_method_requirement x
    WHERE x.profile_method_id = target_cpm.id
      AND x.requirement_id = cpmr.requirement_id
);

COMMIT;

-- =========================================================
-- VALIDAÇÃO 1: METHODS
-- =========================================================
SELECT
    r.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    cpm.is_default,
    cpm.is_active
FROM public.capability_profile cp
JOIN public.capability_region r ON r.id = cp.region_id
JOIN public.capability_context ctx ON ctx.id = cp.context_id
JOIN public.capability_channel ch ON ch.id = cp.channel_id
JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
WHERE ch.code = 'kiosk'
  AND ctx.code = 'order_creation'
ORDER BY r.code, cp.profile_code, cpm.sort_order;

-- =========================================================
-- VALIDAÇÃO 2: INTERFACES
-- =========================================================
SELECT
    r.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    pic.code AS interface_code,
    cpmi.is_default,
    cpmi.is_active
FROM public.capability_profile cp
JOIN public.capability_region r ON r.id = cp.region_id
JOIN public.capability_context ctx ON ctx.id = cp.context_id
JOIN public.capability_channel ch ON ch.id = cp.channel_id
JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
JOIN public.capability_profile_method_interface cpmi ON cpmi.profile_method_id = cpm.id
JOIN public.payment_interface_catalog pic ON pic.id = cpmi.payment_interface_id
WHERE ch.code = 'kiosk'
  AND ctx.code = 'order_creation'
ORDER BY r.code, cp.profile_code, pmc.code, cpmi.sort_order;

-- =========================================================
-- VALIDAÇÃO 3: REQUIREMENTS
-- =========================================================
SELECT
    r.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    crc.code AS requirement_code
FROM public.capability_profile cp
JOIN public.capability_region r ON r.id = cp.region_id
JOIN public.capability_context ctx ON ctx.id = cp.context_id
JOIN public.capability_channel ch ON ch.id = cp.channel_id
JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
LEFT JOIN public.capability_profile_method_requirement cpmr ON cpmr.profile_method_id = cpm.id
LEFT JOIN public.capability_requirement_catalog crc ON crc.id = cpmr.requirement_id
WHERE ch.code = 'kiosk'
  AND ctx.code = 'order_creation'
ORDER BY r.code, cp.profile_code, pmc.code, crc.code;