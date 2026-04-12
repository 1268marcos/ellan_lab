-- HOTFIX 7 - ONLINE constraint
BEGIN;

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
JOIN public.capability_context ctx ON ctx.id = cp.context_id
JOIN public.capability_channel ch ON ch.id = cp.channel_id
WHERE ch.code = 'online'
  AND ctx.code = 'checkout'
  AND NOT EXISTS (
      SELECT 1
      FROM public.capability_profile_constraint cpc
      WHERE cpc.profile_id = cp.id
        AND cpc.code = 'prepayment_timeout_sec'
  );

COMMIT;