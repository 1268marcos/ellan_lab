BEGIN;

-- =========================================================
-- HOTFIX 4 (CONSERVADOR)
-- Habilitar PIX em KIOSK somente para:
--   SP, PT, ES
--
-- SEM mexer no default atual dos cartões
-- SEM desabilitar cartões
-- SEM alterar ONLINE
--
-- Objetivo:
--   - garantir método pix nos profiles kiosk:checkout
--   - garantir interfaces qr_code + deep_link para pix
--   - manter defaults atuais de cartão intactos
-- =========================================================

-- =========================================================
-- 1) GARANTIR CATÁLOGO PIX E INTERFACES
-- =========================================================

UPDATE public.payment_method_catalog
SET
    is_active = TRUE,
    updated_at = NOW()
WHERE code = 'pix';

UPDATE public.payment_interface_catalog
SET
    is_active = TRUE,
    updated_at = NOW()
WHERE code IN ('qr_code', 'deep_link');

-- =========================================================
-- 2) GARANTIR PIX NOS PROFILES KIOSK DE SP / PT / ES
--    sem mexer em defaults existentes
-- =========================================================

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
    cp.id,
    pmc.id,
    'PIX',
    10,
    FALSE,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM public.capability_profile cp
JOIN public.capability_region cr
  ON cr.id = cp.region_id
JOIN public.payment_method_catalog pmc
  ON pmc.code = 'pix'
WHERE cp.profile_code LIKE '%:kiosk:checkout'
  AND cr.code IN ('SP', 'PT', 'ES')
  AND NOT EXISTS (
      SELECT 1
      FROM public.capability_profile_method cpm
      WHERE cpm.profile_id = cp.id
        AND cpm.payment_method_id = pmc.id
  );

UPDATE public.capability_profile_method cpm
SET
    label = 'PIX',
    sort_order = 10,
    is_active = TRUE,
    updated_at = NOW()
FROM public.capability_profile cp,
     public.capability_region cr,
     public.payment_method_catalog pmc
WHERE cp.id = cpm.profile_id
  AND cr.id = cp.region_id
  AND pmc.id = cpm.payment_method_id
  AND cp.profile_code LIKE '%:kiosk:checkout'
  AND cr.code IN ('SP', 'PT', 'ES')
  AND pmc.code = 'pix';

-- =========================================================
-- 3) GARANTIR INTERFACES DO PIX EM KIOSK
--    qr_code = default do próprio PIX
--    deep_link = secundária
--    sem mexer no default do MÉTODO no profile
-- =========================================================

WITH pix_kiosk_methods AS (
    SELECT
        cpm.id AS profile_method_id
    FROM public.capability_profile_method cpm
    JOIN public.capability_profile cp
      ON cp.id = cpm.profile_id
    JOIN public.capability_region cr
      ON cr.id = cp.region_id
    JOIN public.payment_method_catalog pmc
      ON pmc.id = cpm.payment_method_id
    WHERE cp.profile_code LIKE '%:kiosk:checkout'
      AND cr.code IN ('SP', 'PT', 'ES')
      AND pmc.code = 'pix'
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
    pkm.profile_method_id,
    pic.id,
    CASE
        WHEN pic.code = 'qr_code' THEN 10
        WHEN pic.code = 'deep_link' THEN 20
        ELSE 100
    END,
    CASE
        WHEN pic.code = 'qr_code' THEN TRUE
        ELSE FALSE
    END,
    TRUE,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM pix_kiosk_methods pkm
JOIN public.payment_interface_catalog pic
  ON pic.code IN ('qr_code', 'deep_link')
WHERE NOT EXISTS (
    SELECT 1
    FROM public.capability_profile_method_interface cpmi
    WHERE cpmi.profile_method_id = pkm.profile_method_id
      AND cpmi.payment_interface_id = pic.id
);

UPDATE public.capability_profile_method_interface cpmi
SET
    sort_order = CASE
        WHEN pic.code = 'qr_code' THEN 10
        WHEN pic.code = 'deep_link' THEN 20
        ELSE cpmi.sort_order
    END,
    is_default = CASE
        WHEN pic.code = 'qr_code' THEN TRUE
        ELSE FALSE
    END,
    is_active = TRUE,
    updated_at = NOW()
FROM public.payment_interface_catalog pic,
     public.capability_profile_method cpm,
     public.capability_profile cp,
     public.capability_region cr,
     public.payment_method_catalog pmc
WHERE pic.id = cpmi.payment_interface_id
  AND cpm.id = cpmi.profile_method_id
  AND cp.id = cpm.profile_id
  AND cr.id = cp.region_id
  AND pmc.id = cpm.payment_method_id
  AND cp.profile_code LIKE '%:kiosk:checkout'
  AND cr.code IN ('SP', 'PT', 'ES')
  AND pmc.code = 'pix'
  AND pic.code IN ('qr_code', 'deep_link');

-- remove default de outras interfaces do próprio PIX, se houver
UPDATE public.capability_profile_method_interface cpmi
SET
    is_default = FALSE,
    updated_at = NOW()
FROM public.payment_interface_catalog pic,
     public.capability_profile_method cpm,
     public.capability_profile cp,
     public.capability_region cr,
     public.payment_method_catalog pmc
WHERE pic.id = cpmi.payment_interface_id
  AND cpm.id = cpmi.profile_method_id
  AND cp.id = cpm.profile_id
  AND cr.id = cp.region_id
  AND pmc.id = cpm.payment_method_id
  AND cp.profile_code LIKE '%:kiosk:checkout'
  AND cr.code IN ('SP', 'PT', 'ES')
  AND pmc.code = 'pix'
  AND pic.code NOT IN ('qr_code');

COMMIT;

-- =========================================================
-- VALIDAÇÃO 1
-- PIX presente e ativo em SP / PT / ES KIOSK
-- =========================================================
SELECT
    cr.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    cpm.is_default AS method_default,
    cpm.is_active AS method_active
FROM public.capability_profile cp
JOIN public.capability_region cr
  ON cr.id = cp.region_id
JOIN public.capability_profile_method cpm
  ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc
  ON pmc.id = cpm.payment_method_id
WHERE cp.profile_code LIKE '%:kiosk:checkout'
  AND cr.code IN ('SP', 'PT', 'ES')
  AND pmc.code = 'pix'
ORDER BY cr.code, cp.profile_code;

-- =========================================================
-- VALIDAÇÃO 2
-- interfaces do PIX em SP / PT / ES KIOSK
-- =========================================================
SELECT
    cr.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    pic.code AS interface_code,
    cpmi.is_default AS interface_default,
    cpmi.is_active AS interface_active,
    cpmi.sort_order
FROM public.capability_profile cp
JOIN public.capability_region cr
  ON cr.id = cp.region_id
JOIN public.capability_profile_method cpm
  ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc
  ON pmc.id = cpm.payment_method_id
JOIN public.capability_profile_method_interface cpmi
  ON cpmi.profile_method_id = cpm.id
JOIN public.payment_interface_catalog pic
  ON pic.id = cpmi.payment_interface_id
WHERE cp.profile_code LIKE '%:kiosk:checkout'
  AND cr.code IN ('SP', 'PT', 'ES')
  AND pmc.code = 'pix'
ORDER BY cr.code, cp.profile_code, cpmi.sort_order;

-- =========================================================
-- VALIDAÇÃO 3
-- defaults atuais do profile continuam intactos
-- =========================================================
SELECT
    cr.code AS region,
    cp.profile_code,
    pmc.code AS default_method
FROM public.capability_profile cp
JOIN public.capability_region cr
  ON cr.id = cp.region_id
JOIN public.capability_profile_method cpm
  ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc
  ON pmc.id = cpm.payment_method_id
WHERE cp.profile_code LIKE '%:kiosk:checkout'
  AND cr.code IN ('SP', 'PT', 'ES')
  AND cpm.is_default = TRUE
ORDER BY cr.code, cp.profile_code;