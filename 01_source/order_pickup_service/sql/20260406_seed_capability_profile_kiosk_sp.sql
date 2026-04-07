BEGIN;

-- =========================================================
-- 1) CHANNEL
-- =========================================================
INSERT INTO capability_channel (
    code,
    name,
    description,
    is_active
)
VALUES (
    'KIOSK',
    'Kiosk',
    'Canal de pedidos operados em kiosk/totem',
    TRUE
)
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

-- =========================================================
-- 2) CONTEXT
-- capability_context tem unique(channel_id, code)
-- =========================================================
INSERT INTO capability_context (
    channel_id,
    code,
    name,
    description,
    is_active
)
SELECT
    ch.id,
    'ORDER_CREATION',
    'Order Creation',
    'Contexto de criação de pedido no KIOSK',
    TRUE
FROM capability_channel ch
WHERE ch.code = 'KIOSK'
ON CONFLICT (channel_id, code) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

-- =========================================================
-- 3) REGION
-- =========================================================
INSERT INTO capability_region (
    code,
    name,
    country_code,
    continent,
    default_currency,
    is_active,
    metadata_json
)
VALUES (
    'SP',
    'São Paulo',
    'BR',
    'South America',
    'BRL',
    TRUE,
    '{}'::jsonb
)
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    country_code = EXCLUDED.country_code,
    continent = EXCLUDED.continent,
    default_currency = EXCLUDED.default_currency,
    is_active = EXCLUDED.is_active;

-- =========================================================
-- 4) PAYMENT METHOD CATALOG
-- =========================================================
INSERT INTO payment_method_catalog (
    code,
    name,
    family,
    is_wallet,
    is_card,
    is_bnpl,
    is_cash_like,
    is_bank_transfer,
    metadata_json,
    is_active
)
VALUES
    (
        'creditCard',
        'Cartão de Crédito',
        'card',
        FALSE,
        TRUE,
        FALSE,
        FALSE,
        FALSE,
        '{}'::jsonb,
        TRUE
    ),
    (
        'pix',
        'PIX',
        'instant_payment',
        FALSE,
        FALSE,
        FALSE,
        FALSE,
        TRUE,
        '{}'::jsonb,
        TRUE
    )
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    family = EXCLUDED.family,
    is_wallet = EXCLUDED.is_wallet,
    is_card = EXCLUDED.is_card,
    is_bnpl = EXCLUDED.is_bnpl,
    is_cash_like = EXCLUDED.is_cash_like,
    is_bank_transfer = EXCLUDED.is_bank_transfer,
    is_active = EXCLUDED.is_active;

-- =========================================================
-- 5) PAYMENT INTERFACE CATALOG
-- =========================================================
INSERT INTO payment_interface_catalog (
    code,
    name,
    interface_type,
    metadata_json,
    is_active
)
VALUES
    (
        'chip',
        'Chip',
        'physical_card',
        '{}'::jsonb,
        TRUE
    ),
    (
        'qr_code',
        'QR Code',
        'digital_qr',
        '{}'::jsonb,
        TRUE
    )
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    interface_type = EXCLUDED.interface_type,
    is_active = EXCLUDED.is_active;

-- =========================================================
-- 6) REQUIREMENT CATALOG
-- opcional, mas útil para o método PIX / cartão
-- =========================================================
INSERT INTO capability_requirement_catalog (
    code,
    name,
    data_type,
    description,
    is_active
)
VALUES
    (
        'customer_phone',
        'Customer Phone',
        'string',
        'Telefone do cliente quando exigido pelo método',
        TRUE
    ),
    (
        'wallet_provider',
        'Wallet Provider',
        'string',
        'Provedor de carteira digital quando exigido',
        TRUE
    )
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    data_type = EXCLUDED.data_type,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

-- =========================================================
-- 7) CAPABILITY PROFILE
-- combinação que o service procura:
-- region=SP / channel=KIOSK / context=ORDER_CREATION
-- =========================================================
INSERT INTO capability_profile (
    region_id,
    channel_id,
    context_id,
    profile_code,
    name,
    priority,
    currency,
    is_active,
    metadata_json
)
SELECT
    rg.id,
    ch.id,
    ctx.id,
    'KIOSK_SP_ORDER_CREATION',
    'Kiosk SP Order Creation',
    100,
    'BRL',
    TRUE,
    '{}'::jsonb
FROM capability_region rg
JOIN capability_channel ch
    ON ch.code = 'KIOSK'
JOIN capability_context ctx
    ON ctx.channel_id = ch.id
   AND ctx.code = 'ORDER_CREATION'
WHERE rg.code = 'SP'
ON CONFLICT (region_id, channel_id, context_id) DO UPDATE
SET
    profile_code = EXCLUDED.profile_code,
    name = EXCLUDED.name,
    priority = EXCLUDED.priority,
    currency = EXCLUDED.currency,
    is_active = EXCLUDED.is_active;

-- =========================================================
-- 8) PROFILE METHODS
-- =========================================================
INSERT INTO capability_profile_method (
    profile_id,
    payment_method_id,
    label,
    sort_order,
    is_default,
    is_active,
    wallet_provider_id,
    rules_json
)
SELECT
    cp.id,
    pm.id,
    'Cartão de Crédito',
    10,
    TRUE,
    TRUE,
    NULL,
    jsonb_build_object(
        'aliases', jsonb_build_array('CARTAO_CREDITO', 'creditCard', 'CARD'),
        'ui_code', 'CARTAO_CREDITO'
    )
FROM capability_profile cp
JOIN payment_method_catalog pm
    ON pm.code = 'creditCard'
WHERE cp.profile_code = 'KIOSK_SP_ORDER_CREATION'
ON CONFLICT (profile_id, payment_method_id) DO UPDATE
SET
    label = EXCLUDED.label,
    sort_order = EXCLUDED.sort_order,
    is_default = EXCLUDED.is_default,
    is_active = EXCLUDED.is_active,
    wallet_provider_id = EXCLUDED.wallet_provider_id,
    rules_json = EXCLUDED.rules_json;

INSERT INTO capability_profile_method (
    profile_id,
    payment_method_id,
    label,
    sort_order,
    is_default,
    is_active,
    wallet_provider_id,
    rules_json
)
SELECT
    cp.id,
    pm.id,
    'PIX',
    20,
    FALSE,
    TRUE,
    NULL,
    jsonb_build_object(
        'aliases', jsonb_build_array('PIX', 'pix'),
        'ui_code', 'PIX'
    )
FROM capability_profile cp
JOIN payment_method_catalog pm
    ON pm.code = 'pix'
WHERE cp.profile_code = 'KIOSK_SP_ORDER_CREATION'
ON CONFLICT (profile_id, payment_method_id) DO UPDATE
SET
    label = EXCLUDED.label,
    sort_order = EXCLUDED.sort_order,
    is_default = EXCLUDED.is_default,
    is_active = EXCLUDED.is_active,
    wallet_provider_id = EXCLUDED.wallet_provider_id,
    rules_json = EXCLUDED.rules_json;

-- =========================================================
-- 9) PROFILE METHOD INTERFACES
-- =========================================================
INSERT INTO capability_profile_method_interface (
    profile_method_id,
    payment_interface_id,
    sort_order,
    is_default,
    is_active,
    config_json
)
SELECT
    cpm.id,
    pic.id,
    10,
    TRUE,
    TRUE,
    '{}'::jsonb
FROM capability_profile_method cpm
JOIN capability_profile cp
    ON cp.id = cpm.profile_id
JOIN payment_method_catalog pm
    ON pm.id = cpm.payment_method_id
JOIN payment_interface_catalog pic
    ON pic.code = 'chip'
WHERE cp.profile_code = 'KIOSK_SP_ORDER_CREATION'
  AND pm.code = 'creditCard'
ON CONFLICT (profile_method_id, payment_interface_id) DO UPDATE
SET
    sort_order = EXCLUDED.sort_order,
    is_default = EXCLUDED.is_default,
    is_active = EXCLUDED.is_active,
    config_json = EXCLUDED.config_json;

INSERT INTO capability_profile_method_interface (
    profile_method_id,
    payment_interface_id,
    sort_order,
    is_default,
    is_active,
    config_json
)
SELECT
    cpm.id,
    pic.id,
    10,
    TRUE,
    TRUE,
    '{}'::jsonb
FROM capability_profile_method cpm
JOIN capability_profile cp
    ON cp.id = cpm.profile_id
JOIN payment_method_catalog pm
    ON pm.id = cpm.payment_method_id
JOIN payment_interface_catalog pic
    ON pic.code = 'qr_code'
WHERE cp.profile_code = 'KIOSK_SP_ORDER_CREATION'
  AND pm.code = 'pix'
ON CONFLICT (profile_method_id, payment_interface_id) DO UPDATE
SET
    sort_order = EXCLUDED.sort_order,
    is_default = EXCLUDED.is_default,
    is_active = EXCLUDED.is_active,
    config_json = EXCLUDED.config_json;

-- =========================================================
-- 10) PROFILE CONSTRAINTS
-- opcionais, mas úteis para introspecção
-- =========================================================
INSERT INTO capability_profile_constraint (
    profile_id,
    code,
    value_json
)
SELECT
    cp.id,
    'locker_allowed_payment_methods_hint',
    '["PIX","CARD","CASH"]'::jsonb
FROM capability_profile cp
WHERE cp.profile_code = 'KIOSK_SP_ORDER_CREATION'
ON CONFLICT (profile_id, code) DO UPDATE
SET
    value_json = EXCLUDED.value_json;

COMMIT;