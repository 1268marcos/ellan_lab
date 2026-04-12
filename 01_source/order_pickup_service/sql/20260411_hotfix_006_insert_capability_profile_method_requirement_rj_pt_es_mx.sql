BEGIN;

-- =========================================================
-- HOTFIX 3B REGIONAL
-- Aplicar requirement amount_cents somente para:
--   PT, RJ, MX, ES
-- e somente nos profiles:
--   :online:checkout
--   :kiosk:checkout
-- =========================================================

WITH req AS (
    SELECT id
    FROM public.capability_requirement_catalog
    WHERE code = 'amount_cents'
),
target_methods AS (
    SELECT
        cpm.id AS profile_method_id
    FROM public.capability_profile_method cpm
    JOIN public.capability_profile cp
      ON cp.id = cpm.profile_id
    JOIN public.capability_region cr
      ON cr.id = cp.region_id
    JOIN public.payment_method_catalog pmc
      ON pmc.id = cpm.payment_method_id
    WHERE cpm.is_active = TRUE
      AND cr.code IN ('PT', 'RJ', 'MX', 'ES')
      AND (
            cp.profile_code LIKE '%:online:checkout'
         OR cp.profile_code LIKE '%:kiosk:checkout'
      )
      AND pmc.code IN ('creditCard', 'debitCard', 'giftCard')
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
    tm.profile_method_id,
    req.id,
    TRUE,
    'request',
    '{}'::jsonb,
    NOW(),
    NOW()
FROM target_methods tm
CROSS JOIN req
WHERE NOT EXISTS (
    SELECT 1
    FROM public.capability_profile_method_requirement cpmr
    WHERE cpmr.profile_method_id = tm.profile_method_id
      AND cpmr.requirement_id = req.id
);

UPDATE public.capability_profile_method_requirement cpmr
SET
    is_required = TRUE,
    requirement_scope = 'request',
    updated_at = NOW()
FROM public.capability_requirement_catalog crc,
     public.capability_profile_method cpm,
     public.capability_profile cp,
     public.capability_region cr,
     public.payment_method_catalog pmc
WHERE crc.id = cpmr.requirement_id
  AND cpm.id = cpmr.profile_method_id
  AND cp.id = cpm.profile_id
  AND cr.id = cp.region_id
  AND pmc.id = cpm.payment_method_id
  AND crc.code = 'amount_cents'
  AND cr.code IN ('PT', 'RJ', 'MX', 'ES')
  AND (
        cp.profile_code LIKE '%:online:checkout'
     OR cp.profile_code LIKE '%:kiosk:checkout'
  )
  AND pmc.code IN ('creditCard', 'debitCard', 'giftCard');

COMMIT;

-- =========================================================
-- VALIDAÇÃO
-- =========================================================
SELECT
    cr.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    crc.code AS requirement_code,
    cpmr.is_required,
    cpmr.requirement_scope
FROM public.capability_profile cp
JOIN public.capability_region cr
  ON cr.id = cp.region_id
JOIN public.capability_profile_method cpm
  ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc
  ON pmc.id = cpm.payment_method_id
LEFT JOIN public.capability_profile_method_requirement cpmr
  ON cpmr.profile_method_id = cpm.id
LEFT JOIN public.capability_requirement_catalog crc
  ON crc.id = cpmr.requirement_id
WHERE cr.code IN ('PT', 'RJ', 'MX', 'ES')
  AND (
        cp.profile_code LIKE '%:online:checkout'
     OR cp.profile_code LIKE '%:kiosk:checkout'
  )
ORDER BY cr.code, cp.profile_code, pmc.code, crc.code;