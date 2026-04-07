-- select * from capability_profile_method_interface;
-- 1) Inserir interface chip para debitCard
INSERT INTO capability_profile_method_interface (
    profile_method_id,
    payment_interface_id,
    is_default,
    is_active,
    sort_order,
    config_json,
    created_at,
    updated_at
)
SELECT
    cpm.id,
    pic.id,
    TRUE,
    TRUE,
    10,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM capability_profile_method cpm
JOIN payment_method_catalog pmc
    ON pmc.id = cpm.payment_method_id
JOIN payment_interface_catalog pic
    ON pic.code = 'chip'
WHERE cpm.profile_id = 7
  AND pmc.code = 'debitCard'
  AND NOT EXISTS (
      SELECT 1
      FROM capability_profile_method_interface cpmi
      WHERE cpmi.profile_method_id = cpm.id
        AND cpmi.payment_interface_id = pic.id
  );


-- 2) Inserir interface chip para giftCard
INSERT INTO capability_profile_method_interface (
    profile_method_id,
    payment_interface_id,
    is_default,
    is_active,
    sort_order,
    config_json,
    created_at,
    updated_at
)
SELECT
    cpm.id,
    pic.id,
    TRUE,
    TRUE,
    10,
    '{}'::jsonb,
    NOW(),
    NOW()
FROM capability_profile_method cpm
JOIN payment_method_catalog pmc
    ON pmc.id = cpm.payment_method_id
JOIN payment_interface_catalog pic
    ON pic.code = 'chip'
WHERE cpm.profile_id = 7
  AND pmc.code = 'giftCard'
  AND NOT EXISTS (
      SELECT 1
      FROM capability_profile_method_interface cpmi
      WHERE cpmi.profile_method_id = cpm.id
        AND cpmi.payment_interface_id = pic.id
  );