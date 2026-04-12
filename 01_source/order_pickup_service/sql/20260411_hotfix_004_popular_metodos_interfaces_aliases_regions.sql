-- Primeiro, fazer ROLLBACK
ROLLBACK;

-- Script corrigido
BEGIN;

-- =========================================================
-- HOTFIX 2: Popular métodos + interfaces + aliases
-- Para TODAS as regiões
-- Profiles: {REGION}:online:checkout e {REGION}:kiosk:checkout
-- =========================================================

-- =========================================================
-- 1) GARANTIR CATÁLOGO DE MÉTODOS
-- =========================================================

UPDATE public.payment_method_catalog
SET is_active = TRUE, updated_at = NOW()
WHERE code IN ('pix', 'creditCard', 'debitCard', 'giftCard');

-- =========================================================
-- 2) GARANTIR CATÁLOGO DE INTERFACES
-- =========================================================

UPDATE public.payment_interface_catalog
SET is_active = TRUE, updated_at = NOW()
WHERE code IN ('qr_code', 'deep_link', 'web_token', 'chip', 'nfc', 'kiosk_pinpad', 'manual');

-- =========================================================
-- 3) GARANTIR ALIASES DE UI
-- =========================================================

UPDATE public.payment_method_ui_alias
SET is_active = TRUE, updated_at = NOW()
WHERE ui_code IN ('PIX', 'CARTAO_CREDITO', 'CARTAO_DEBITO', 'CARTAO_PRESENTE', 
                  'CREDITCARD', 'DEBITCARD', 'GIFTCARD');

-- =========================================================
-- 4) VINCULAR MÉTODOS AOS PROFILES (TODAS AS REGIÕES)
-- =========================================================

WITH target_profiles AS (
    SELECT id, profile_code
    FROM public.capability_profile
    WHERE profile_code LIKE '%:online:checkout' 
       OR profile_code LIKE '%:kiosk:checkout'
),
target_methods AS (
    SELECT id, code
    FROM public.payment_method_catalog
    WHERE code IN ('pix', 'creditCard', 'debitCard', 'giftCard')
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
    p.id,
    m.id,
    CASE
        WHEN m.code = 'pix' THEN 'PIX'
        WHEN m.code = 'creditCard' THEN 'Cartão de Crédito'
        WHEN m.code = 'debitCard' THEN 'Cartão de Débito'
        WHEN m.code = 'giftCard' THEN 'Cartão Presente'
        ELSE m.code
    END,
    CASE
        WHEN m.code = 'pix' THEN 10
        WHEN m.code = 'creditCard' THEN 20
        WHEN m.code = 'debitCard' THEN 30
        WHEN m.code = 'giftCard' THEN 40
        ELSE 100
    END,
    CASE
        WHEN p.profile_code LIKE '%:online:checkout' AND m.code = 'pix' THEN TRUE
        WHEN p.profile_code LIKE '%:kiosk:checkout' AND m.code = 'creditCard' THEN TRUE
        ELSE FALSE
    END,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM target_profiles p
CROSS JOIN target_methods m
ON CONFLICT (profile_id, payment_method_id) DO NOTHING;

-- =========================================================
-- 5) VINCULAR INTERFACES AOS MÉTODOS DOS PROFILES (TODAS AS REGIÕES)
-- =========================================================

-- Para profiles ONLINE:CHECKOUT
WITH online_profiles AS (
    SELECT 
        cpm.id AS profile_method_id,
        pmc.code AS method_code
    FROM public.capability_profile cp
    JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
    JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
    WHERE cp.profile_code LIKE '%:online:checkout'
      AND pmc.code IN ('pix', 'creditCard', 'debitCard', 'giftCard')
),
online_interfaces AS (
    SELECT 'pix' AS method_code, 'qr_code' AS interface_code, 10 AS sort_order, TRUE AS is_default
    UNION ALL SELECT 'pix', 'deep_link', 20, FALSE
    UNION ALL SELECT 'creditCard', 'web_token', 10, TRUE
    UNION ALL SELECT 'debitCard', 'web_token', 10, TRUE
    UNION ALL SELECT 'giftCard', 'web_token', 10, TRUE
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
    op.profile_method_id,
    pic.id,
    oi.sort_order,
    oi.is_default,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM online_profiles op
JOIN online_interfaces oi ON oi.method_code = op.method_code
JOIN public.payment_interface_catalog pic ON pic.code = oi.interface_code
ON CONFLICT (profile_method_id, payment_interface_id) DO NOTHING;

-- Para profiles KIOSK:CHECKOUT
WITH kiosk_profiles AS (
    SELECT 
        cpm.id AS profile_method_id,
        pmc.code AS method_code
    FROM public.capability_profile cp
    JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
    JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
    WHERE cp.profile_code LIKE '%:kiosk:checkout'
      AND pmc.code IN ('pix', 'creditCard', 'debitCard', 'giftCard')
),
kiosk_interfaces AS (
    SELECT 'pix' AS method_code, 'qr_code' AS interface_code, 10 AS sort_order, TRUE AS is_default
    UNION ALL SELECT 'creditCard', 'chip', 10, TRUE
    UNION ALL SELECT 'creditCard', 'nfc', 20, FALSE
    UNION ALL SELECT 'creditCard', 'kiosk_pinpad', 30, FALSE
    UNION ALL SELECT 'debitCard', 'chip', 10, TRUE
    UNION ALL SELECT 'debitCard', 'nfc', 20, FALSE
    UNION ALL SELECT 'giftCard', 'chip', 10, TRUE
    UNION ALL SELECT 'giftCard', 'manual', 20, FALSE
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
    kp.profile_method_id,
    pic.id,
    ki.sort_order,
    ki.is_default,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM kiosk_profiles kp
JOIN kiosk_interfaces ki ON ki.method_code = kp.method_code
JOIN public.payment_interface_catalog pic ON pic.code = ki.interface_code
ON CONFLICT (profile_method_id, payment_interface_id) DO NOTHING;

COMMIT;

-- =========================================================
-- VALIDAÇÃO: Verificar para SP
-- =========================================================

-- Validar SP:online:checkout
SELECT
    r.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    cpm.is_default AS method_default,
    pic.code AS interface_code,
    cpmi.is_default AS interface_default,
    cpmi.sort_order
FROM public.capability_profile cp
JOIN public.capability_region r ON r.id = cp.region_id
JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
LEFT JOIN public.capability_profile_method_interface cpmi ON cpmi.profile_method_id = cpm.id
LEFT JOIN public.payment_interface_catalog pic ON pic.id = cpmi.payment_interface_id
WHERE cp.profile_code = 'SP:online:checkout'
ORDER BY pmc.code, cpmi.sort_order;

-- Validar SP:kiosk:checkout
SELECT
    r.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    cpm.is_default AS method_default,
    pic.code AS interface_code,
    cpmi.is_default AS interface_default,
    cpmi.sort_order
FROM public.capability_profile cp
JOIN public.capability_region r ON r.id = cp.region_id
JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
LEFT JOIN public.capability_profile_method_interface cpmi ON cpmi.profile_method_id = cpm.id
LEFT JOIN public.payment_interface_catalog pic ON pic.id = cpmi.payment_interface_id
WHERE cp.profile_code = 'SP:kiosk:checkout'
ORDER BY pmc.code, cpmi.sort_order;

-- Estatísticas finais
SELECT 
    'Métodos inseridos' as tipo,
    COUNT(*) as quantidade
FROM public.capability_profile_method
WHERE profile_id IN (SELECT id FROM public.capability_profile WHERE profile_code LIKE '%:online:checkout' OR profile_code LIKE '%:kiosk:checkout')

UNION ALL

SELECT 
    'Interfaces inseridas' as tipo,
    COUNT(*) as quantidade
FROM public.capability_profile_method_interface
WHERE profile_method_id IN (
    SELECT cpm.id 
    FROM public.capability_profile_method cpm
    JOIN public.capability_profile cp ON cp.id = cpm.profile_id
    WHERE cp.profile_code LIKE '%:online:checkout' OR cp.profile_code LIKE '%:kiosk:checkout'
);