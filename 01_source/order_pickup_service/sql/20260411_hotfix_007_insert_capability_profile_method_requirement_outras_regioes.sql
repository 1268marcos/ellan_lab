BEGIN;

-- =========================================================
-- HOTFIX 3B REGIONAL - PARA DEMAIS REGIÕES
-- Aplicar requirement amount_cents para TODAS as regiões
-- EXCETO: PT, SP, RJ, MX, ES
-- 
-- REGIÕES QUE JÁ POSSUEM: PT, SP, RJ, MX, ES (pular estas)
-- REGIÕES QUE PRECISAM: todas as outras
-- =========================================================

-- =========================================================
-- 1) GARANTIR QUE O CATÁLOGO EXISTE
-- =========================================================

INSERT INTO public.capability_requirement_catalog (
    code, name, data_type, description, is_active, created_at, updated_at
)
SELECT 'amount_cents', 'Amount Cents', 'integer',
       'Valor em centavos obrigatório para o método selecionado.',
       TRUE, NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM public.capability_requirement_catalog WHERE code = 'amount_cents'
);

-- =========================================================
-- 2) APLICAR amount_cents PARA DEMAIS REGIÕES
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
      AND cr.code NOT IN ('PT', 'SP', 'RJ', 'MX', 'ES')  -- ← EXCLUI as regiões que já têm
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

-- =========================================================
-- 3) UPDATE para garantir consistência nas demais regiões
-- =========================================================

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
  AND cr.code NOT IN ('PT', 'SP', 'RJ', 'MX', 'ES')  -- ← EXCLUI as regiões que já têm
  AND (
        cp.profile_code LIKE '%:online:checkout'
     OR cp.profile_code LIKE '%:kiosk:checkout'
  )
  AND pmc.code IN ('creditCard', 'debitCard', 'giftCard');

COMMIT;

-- =========================================================
-- VALIDAÇÃO 1: Verificar regiões que NÃO receberam (as 5)
-- =========================================================
SELECT
    cr.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    CASE WHEN cpmr.id IS NOT NULL THEN '✅ TEM' ELSE '❌ NÃO TEM' END AS amount_cents_requirement
FROM public.capability_profile cp
JOIN public.capability_region cr ON cr.id = cp.region_id
JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
LEFT JOIN public.capability_profile_method_requirement cpmr ON cpmr.profile_method_id = cpm.id
LEFT JOIN public.capability_requirement_catalog crc ON crc.id = cpmr.requirement_id AND crc.code = 'amount_cents'
WHERE cr.code IN ('PT', 'SP', 'RJ', 'MX', 'ES')
  AND (cp.profile_code LIKE '%:online:checkout' OR cp.profile_code LIKE '%:kiosk:checkout')
  AND pmc.code IN ('creditCard', 'debitCard', 'giftCard')
ORDER BY cr.code, cp.profile_code, pmc.code;

-- =========================================================
-- VALIDAÇÃO 2: Verificar amostra das regiões que receberam
-- =========================================================
SELECT
    cr.code AS region,
    cp.profile_code,
    pmc.code AS method_code,
    CASE WHEN cpmr.id IS NOT NULL THEN '✅ TEM' ELSE '❌ NÃO TEM' END AS amount_cents_requirement
FROM public.capability_profile cp
JOIN public.capability_region cr ON cr.id = cp.region_id
JOIN public.capability_profile_method cpm ON cpm.profile_id = cp.id
JOIN public.payment_method_catalog pmc ON pmc.id = cpm.payment_method_id
LEFT JOIN public.capability_profile_method_requirement cpmr ON cpmr.profile_method_id = cpm.id
LEFT JOIN public.capability_requirement_catalog crc ON crc.id = cpmr.requirement_id AND crc.code = 'amount_cents'
WHERE cr.code NOT IN ('PT', 'SP', 'RJ', 'MX', 'ES')
  AND (cp.profile_code LIKE '%:online:checkout' OR cp.profile_code LIKE '%:kiosk:checkout')
  AND pmc.code IN ('creditCard', 'debitCard', 'giftCard')
ORDER BY cr.code, cp.profile_code, pmc.code
LIMIT 30;

-- =========================================================
-- VALIDAÇÃO 3: Contagem total por região
-- =========================================================
SELECT 
    CASE 
        WHEN cr.code IN ('PT', 'SP', 'RJ', 'MX', 'ES') THEN '✅ JÁ POSSUI (5 regiões)'
        ELSE '🆕 NOVAS (demais regiões)'
    END AS status,
    COUNT(DISTINCT cr.code) AS total_regioes,
    COUNT(DISTINCT cpmr.id) AS total_requirements_aplicados
FROM public.capability_profile_method_requirement cpmr
JOIN public.capability_profile_method cpm ON cpm.id = cpmr.profile_method_id
JOIN public.capability_profile cp ON cp.id = cpm.profile_id
JOIN public.capability_region cr ON cr.id = cp.region_id
JOIN public.capability_requirement_catalog crc ON crc.id = cpmr.requirement_id
WHERE crc.code = 'amount_cents'
  AND (cp.profile_code LIKE '%:online:checkout' OR cp.profile_code LIKE '%:kiosk:checkout')
GROUP BY CASE 
    WHEN cr.code IN ('PT', 'SP', 'RJ', 'MX', 'ES') THEN '✅ JÁ POSSUI (5 regiões)'
    ELSE '🆕 NOVAS (demais regiões)'
END;