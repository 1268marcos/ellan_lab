BEGIN;

-- =========================================================
-- HOTFIX 6B
-- Criar constraint obrigatória:
--   prepayment_timeout_sec
-- para:
--   channel = kiosk
--   context = order_creation
--
-- Schema real:
--   capability_profile_constraint(profile_id, code, value_json, ...)
-- =========================================================

INSERT INTO public.capability_profile_constraint (
    profile_id,
    code,
    value_json,
    created_at,
    updated_at
)
SELECT
    cp.id,
    'prepayment_timeout_sec',
    jsonb_build_object('value', 300),
    NOW(),
    NOW()
FROM public.capability_profile cp
JOIN public.capability_context ctx
  ON ctx.id = cp.context_id
JOIN public.capability_channel ch
  ON ch.id = cp.channel_id
WHERE ch.code = 'kiosk'
  AND ctx.code = 'order_creation'
  AND NOT EXISTS (
      SELECT 1
      FROM public.capability_profile_constraint cpc
      WHERE cpc.profile_id = cp.id
        AND cpc.code = 'prepayment_timeout_sec'
  );

UPDATE public.capability_profile_constraint cpc
SET
    value_json = jsonb_build_object('value', 300),
    updated_at = NOW()
FROM public.capability_profile cp
JOIN public.capability_context ctx
  ON ctx.id = cp.context_id
JOIN public.capability_channel ch
  ON ch.id = cp.channel_id
WHERE cp.id = cpc.profile_id
  AND ch.code = 'kiosk'
  AND ctx.code = 'order_creation'
  AND cpc.code = 'prepayment_timeout_sec';

COMMIT;

-- =========================================================
-- VALIDAÇÃO
-- =========================================================
SELECT
    r.code AS region,
    cp.profile_code,
    cpc.code,
    cpc.value_json
FROM public.capability_profile_constraint cpc
JOIN public.capability_profile cp
  ON cp.id = cpc.profile_id
JOIN public.capability_region r
  ON r.id = cp.region_id
JOIN public.capability_context ctx
  ON ctx.id = cp.context_id
JOIN public.capability_channel ch
  ON ch.id = cp.channel_id
WHERE ch.code = 'kiosk'
  AND ctx.code = 'order_creation'
  AND cpc.code = 'prepayment_timeout_sec'
ORDER BY r.code, cp.profile_code;