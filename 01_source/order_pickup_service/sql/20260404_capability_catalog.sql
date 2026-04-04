BEGIN;

-- =========================================================
-- 20260404_capability_catalog.sql
-- Capability catalog canônico no PostgreSQL
-- Base inicial: SP / PT + online/checkout + kiosk/purchase + kiosk/pickup
-- 01_source/order_pickup_service/sql/20260404_capability_catalog.sql
--
-- Em marcos@LAPTOP-3VC5VV2U:~/ellan_lab/02_docker$ faça:
-- docker compose exec -T postgres_central psql -U admin -d locker_central < ../01_source/order_pickup_service/sql/20260404_capability_catalog.sql
-- =========================================================

-- 1. capability_channel
CREATE TABLE IF NOT EXISTS capability_channel (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_capability_channel_active
    ON capability_channel (is_active);

-- 2. capability_context
CREATE TABLE IF NOT EXISTS capability_context (
    id BIGSERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL REFERENCES capability_channel(id) ON DELETE RESTRICT,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_context_channel_code UNIQUE (channel_id, code)
);

CREATE INDEX IF NOT EXISTS ix_capability_context_channel
    ON capability_context (channel_id);

CREATE INDEX IF NOT EXISTS ix_capability_context_active
    ON capability_context (is_active);

-- 3. capability_region
CREATE TABLE IF NOT EXISTS capability_region (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    country_code VARCHAR(10),
    continent VARCHAR(60),
    default_currency VARCHAR(10) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_capability_region_country
    ON capability_region (country_code);

CREATE INDEX IF NOT EXISTS ix_capability_region_active
    ON capability_region (is_active);

-- 4. payment_method_catalog
CREATE TABLE IF NOT EXISTS payment_method_catalog (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    family VARCHAR(80),
    is_wallet BOOLEAN NOT NULL DEFAULT FALSE,
    is_card BOOLEAN NOT NULL DEFAULT FALSE,
    is_bnpl BOOLEAN NOT NULL DEFAULT FALSE,
    is_cash_like BOOLEAN NOT NULL DEFAULT FALSE,
    is_bank_transfer BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_payment_method_catalog_family
    ON payment_method_catalog (family);

CREATE INDEX IF NOT EXISTS ix_payment_method_catalog_active
    ON payment_method_catalog (is_active);

-- 5. payment_interface_catalog
CREATE TABLE IF NOT EXISTS payment_interface_catalog (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    interface_type VARCHAR(60),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_payment_interface_catalog_type
    ON payment_interface_catalog (interface_type);

CREATE INDEX IF NOT EXISTS ix_payment_interface_catalog_active
    ON payment_interface_catalog (is_active);

-- 6. wallet_provider_catalog
CREATE TABLE IF NOT EXISTS wallet_provider_catalog (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_wallet_provider_catalog_active
    ON wallet_provider_catalog (is_active);

-- 7. capability_requirement_catalog
CREATE TABLE IF NOT EXISTS capability_requirement_catalog (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    data_type VARCHAR(40) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_capability_requirement_catalog_active
    ON capability_requirement_catalog (is_active);

-- 8. capability_profile
CREATE TABLE IF NOT EXISTS capability_profile (
    id BIGSERIAL PRIMARY KEY,
    region_id BIGINT NOT NULL REFERENCES capability_region(id) ON DELETE RESTRICT,
    channel_id BIGINT NOT NULL REFERENCES capability_channel(id) ON DELETE RESTRICT,
    context_id BIGINT NOT NULL REFERENCES capability_context(id) ON DELETE RESTRICT,
    profile_code VARCHAR(160) NOT NULL UNIQUE,
    name VARCHAR(180) NOT NULL,
    priority INT NOT NULL DEFAULT 100,
    currency VARCHAR(10) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_region_channel_context
        UNIQUE (region_id, channel_id, context_id)
);

CREATE INDEX IF NOT EXISTS ix_capability_profile_region
    ON capability_profile (region_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_channel
    ON capability_profile (channel_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_context
    ON capability_profile (context_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_active
    ON capability_profile (is_active);

CREATE INDEX IF NOT EXISTS ix_capability_profile_priority
    ON capability_profile (priority);

-- 9. capability_profile_action
CREATE TABLE IF NOT EXISTS capability_profile_action (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
    action_code VARCHAR(80) NOT NULL,
    label VARCHAR(120) NOT NULL,
    sort_order INT NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_action UNIQUE (profile_id, action_code)
);

CREATE INDEX IF NOT EXISTS ix_capability_profile_action_profile
    ON capability_profile_action (profile_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_action_active
    ON capability_profile_action (is_active);

-- 10. capability_profile_method
CREATE TABLE IF NOT EXISTS capability_profile_method (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
    payment_method_id BIGINT NOT NULL REFERENCES payment_method_catalog(id) ON DELETE RESTRICT,
    label VARCHAR(120),
    sort_order INT NOT NULL DEFAULT 100,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    wallet_provider_id BIGINT REFERENCES wallet_provider_catalog(id) ON DELETE RESTRICT,
    rules_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_method UNIQUE (profile_id, payment_method_id)
);

CREATE INDEX IF NOT EXISTS ix_capability_profile_method_profile
    ON capability_profile_method (profile_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_method_payment_method
    ON capability_profile_method (payment_method_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_method_wallet_provider
    ON capability_profile_method (wallet_provider_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_method_active
    ON capability_profile_method (is_active);

CREATE UNIQUE INDEX IF NOT EXISTS ux_capability_profile_method_default_per_profile
    ON capability_profile_method (profile_id)
    WHERE is_default = TRUE AND is_active = TRUE;

-- 11. capability_profile_method_interface
CREATE TABLE IF NOT EXISTS capability_profile_method_interface (
    id BIGSERIAL PRIMARY KEY,
    profile_method_id BIGINT NOT NULL REFERENCES capability_profile_method(id) ON DELETE CASCADE,
    payment_interface_id BIGINT NOT NULL REFERENCES payment_interface_catalog(id) ON DELETE RESTRICT,
    sort_order INT NOT NULL DEFAULT 100,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_method_interface
        UNIQUE (profile_method_id, payment_interface_id)
);

CREATE INDEX IF NOT EXISTS ix_capability_profile_method_interface_profile_method
    ON capability_profile_method_interface (profile_method_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_method_interface_interface
    ON capability_profile_method_interface (payment_interface_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_method_interface_active
    ON capability_profile_method_interface (is_active);

CREATE UNIQUE INDEX IF NOT EXISTS ux_cap_profile_method_interface_default
    ON capability_profile_method_interface (profile_method_id)
    WHERE is_default = TRUE AND is_active = TRUE;

-- 12. capability_profile_method_requirement
CREATE TABLE IF NOT EXISTS capability_profile_method_requirement (
    id BIGSERIAL PRIMARY KEY,
    profile_method_id BIGINT NOT NULL REFERENCES capability_profile_method(id) ON DELETE CASCADE,
    requirement_id BIGINT NOT NULL REFERENCES capability_requirement_catalog(id) ON DELETE RESTRICT,
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    requirement_scope VARCHAR(40) NOT NULL DEFAULT 'request',
    validation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_method_requirement
        UNIQUE (profile_method_id, requirement_id)
);

CREATE INDEX IF NOT EXISTS ix_capability_profile_method_requirement_profile_method
    ON capability_profile_method_requirement (profile_method_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_method_requirement_requirement
    ON capability_profile_method_requirement (requirement_id);

-- 13. capability_profile_constraint
CREATE TABLE IF NOT EXISTS capability_profile_constraint (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,
    value_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_constraint UNIQUE (profile_id, code)
);

CREATE INDEX IF NOT EXISTS ix_capability_profile_constraint_profile
    ON capability_profile_constraint (profile_id);

-- 14. capability_profile_target
CREATE TABLE IF NOT EXISTS capability_profile_target (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
    target_type VARCHAR(40) NOT NULL,
    target_key VARCHAR(120) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_target UNIQUE (profile_id, target_type, target_key)
);

CREATE INDEX IF NOT EXISTS ix_capability_profile_target_profile
    ON capability_profile_target (profile_id);

CREATE INDEX IF NOT EXISTS ix_capability_profile_target_type_key
    ON capability_profile_target (target_type, target_key);

-- 15. capability_profile_snapshot
CREATE TABLE IF NOT EXISTS capability_profile_snapshot (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
    snapshot_version INT NOT NULL,
    snapshot_json JSONB NOT NULL,
    created_by VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_snapshot UNIQUE (profile_id, snapshot_version)
);

CREATE INDEX IF NOT EXISTS ix_capability_profile_snapshot_profile
    ON capability_profile_snapshot (profile_id);

-- =========================================================
-- SEED MÍNIMO
-- =========================================================

INSERT INTO capability_channel (code, name, description)
VALUES
    ('online', 'Online', 'Fluxos online'),
    ('kiosk', 'Kiosk', 'Fluxos do kiosk / locker local')
ON CONFLICT (code) DO NOTHING;

INSERT INTO capability_region (code, name, country_code, continent, default_currency)
VALUES
    ('SP', 'São Paulo', 'BR', 'Latin America', 'BRL'),
    ('PT', 'Portugal', 'PT', 'Western Europe', 'EUR')
ON CONFLICT (code) DO NOTHING;

INSERT INTO capability_context (channel_id, code, name, description)
SELECT c.id, x.code, x.name, x.description
FROM capability_channel c
JOIN (
    VALUES
        ('online', 'checkout', 'Checkout', 'Checkout online'),
        ('kiosk', 'purchase', 'Purchase', 'Compra no kiosk'),
        ('kiosk', 'pickup', 'Pickup', 'Retirada no kiosk')
) AS x(channel_code, code, name, description)
    ON x.channel_code = c.code
ON CONFLICT (channel_id, code) DO NOTHING;

INSERT INTO payment_method_catalog (
    code,
    name,
    family,
    is_wallet,
    is_card,
    is_bnpl,
    is_cash_like,
    is_bank_transfer
)
VALUES
    ('pix', 'PIX', 'instant_bank_transfer', FALSE, FALSE, FALSE, FALSE, TRUE),
    ('creditCard', 'Cartão de crédito', 'card', FALSE, TRUE, FALSE, FALSE, FALSE),
    ('debitCard', 'Cartão de débito', 'card', FALSE, TRUE, FALSE, FALSE, FALSE),
    ('giftCard', 'Gift card', 'card', FALSE, TRUE, FALSE, FALSE, FALSE),
    ('mbway', 'MB WAY', 'wallet', TRUE, FALSE, FALSE, FALSE, FALSE),
    ('multibanco_reference', 'Multibanco', 'bank_reference', FALSE, FALSE, FALSE, FALSE, TRUE)
ON CONFLICT (code) DO NOTHING;

INSERT INTO payment_interface_catalog (code, name, interface_type)
VALUES
    ('qr_code', 'QR Code', 'digital'),
    ('web_token', 'Web Token', 'digital'),
    ('deep_link', 'Deep Link', 'digital'),
    ('chip', 'Chip', 'physical'),
    ('nfc', 'NFC', 'physical'),
    ('manual', 'Manual', 'manual')
ON CONFLICT (code) DO NOTHING;

INSERT INTO wallet_provider_catalog (code, name)
VALUES
    ('mbway', 'MB WAY')
ON CONFLICT (code) DO NOTHING;

INSERT INTO capability_requirement_catalog (code, name, data_type, description)
VALUES
    ('amount_cents', 'Amount cents', 'integer', 'Valor da transação em centavos'),
    ('customer_phone', 'Customer phone', 'string', 'Telefone do cliente'),
    ('wallet_provider', 'Wallet provider', 'string', 'Provedor de carteira digital')
ON CONFLICT (code) DO NOTHING;

-- =========================================================
-- PROFILES
-- =========================================================

INSERT INTO capability_profile (
    region_id,
    channel_id,
    context_id,
    profile_code,
    name,
    priority,
    currency,
    is_active
)
SELECT
    r.id,
    ch.id,
    cx.id,
    r.code || ':' || ch.code || ':' || cx.code,
    r.name || ' / ' || ch.name || ' / ' || cx.name,
    100,
    r.default_currency,
    TRUE
FROM capability_region r
JOIN capability_channel ch ON ch.code IN ('online', 'kiosk')
JOIN capability_context cx ON cx.channel_id = ch.id
WHERE
    (r.code = 'SP' AND ((ch.code = 'online' AND cx.code = 'checkout') OR (ch.code = 'kiosk' AND cx.code IN ('purchase', 'pickup'))))
 OR (r.code = 'PT' AND ((ch.code = 'online' AND cx.code = 'checkout') OR (ch.code = 'kiosk' AND cx.code IN ('purchase', 'pickup'))))
ON CONFLICT (profile_code) DO NOTHING;

-- =========================================================
-- ACTIONS
-- =========================================================

INSERT INTO capability_profile_action (
    profile_id,
    action_code,
    label,
    sort_order,
    is_active
)
SELECT
    p.id,
    a.action_code,
    a.label,
    a.sort_order,
    TRUE
FROM capability_profile p
JOIN (
    VALUES
        ('kiosk:purchase', 'create_order', 'Criar pedido', 10),
        ('kiosk:purchase', 'start_payment', 'Iniciar pagamento', 20),
        ('kiosk:purchase', 'approve_payment', 'Confirmar pagamento', 30),
        ('kiosk:purchase', 'identify_customer', 'Identificar cliente', 40),
        ('kiosk:pickup', 'enter_pickup_code', 'Digitar código de retirada', 10),
        ('kiosk:pickup', 'identify_customer', 'Identificar cliente', 20)
) AS a(scope_code, action_code, label, sort_order)
    ON ((split_part(p.profile_code, ':', 2) || ':' || split_part(p.profile_code, ':', 3)) = a.scope_code)
ON CONFLICT (profile_id, action_code) DO NOTHING;

-- =========================================================
-- METHODS
-- =========================================================

-- SP:online:checkout
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
    p.id,
    pm.id,
    x.label,
    x.sort_order,
    x.is_default,
    TRUE,
    wp.id,
    x.rules_json::jsonb
FROM (
    VALUES
        ('SP:online:checkout', 'pix', 'PIX', 10, TRUE,  NULL, '{"requires_amount": true}'),
        ('SP:online:checkout', 'creditCard', 'Cartão de crédito', 20, FALSE, NULL, '{"requires_amount": true}'),
        ('SP:online:checkout', 'debitCard', 'Cartão de débito', 30, FALSE, NULL, '{"requires_amount": true}')
) AS x(profile_code, method_code, label, sort_order, is_default, wallet_code, rules_json)
JOIN capability_profile p ON p.profile_code = x.profile_code
JOIN payment_method_catalog pm ON pm.code = x.method_code
LEFT JOIN wallet_provider_catalog wp ON wp.code = x.wallet_code
ON CONFLICT (profile_id, payment_method_id) DO NOTHING;

-- SP:kiosk:purchase
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
    p.id,
    pm.id,
    x.label,
    x.sort_order,
    x.is_default,
    TRUE,
    wp.id,
    x.rules_json::jsonb
FROM (
    VALUES
        ('SP:kiosk:purchase', 'pix', 'PIX', 10, TRUE,  NULL, '{"requires_amount": true}'),
        ('SP:kiosk:purchase', 'creditCard', 'Cartão de crédito', 20, FALSE, NULL, '{"requires_amount": true}'),
        ('SP:kiosk:purchase', 'debitCard', 'Cartão de débito', 30, FALSE, NULL, '{"requires_amount": true}'),
        ('SP:kiosk:purchase', 'giftCard', 'Gift card', 40, FALSE, NULL, '{}')
) AS x(profile_code, method_code, label, sort_order, is_default, wallet_code, rules_json)
JOIN capability_profile p ON p.profile_code = x.profile_code
JOIN payment_method_catalog pm ON pm.code = x.method_code
LEFT JOIN wallet_provider_catalog wp ON wp.code = x.wallet_code
ON CONFLICT (profile_id, payment_method_id) DO NOTHING;

-- PT:online:checkout
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
    p.id,
    pm.id,
    x.label,
    x.sort_order,
    x.is_default,
    TRUE,
    wp.id,
    x.rules_json::jsonb
FROM (
    VALUES
        ('PT:online:checkout', 'mbway', 'MB WAY', 10, TRUE, 'mbway', '{"requires_amount": true, "requires_customer_phone": true}'),
        ('PT:online:checkout', 'multibanco_reference', 'Multibanco', 20, FALSE, NULL, '{"requires_amount": true}'),
        ('PT:online:checkout', 'creditCard', 'Cartão de crédito', 30, FALSE, NULL, '{"requires_amount": true}')
) AS x(profile_code, method_code, label, sort_order, is_default, wallet_code, rules_json)
JOIN capability_profile p ON p.profile_code = x.profile_code
JOIN payment_method_catalog pm ON pm.code = x.method_code
LEFT JOIN wallet_provider_catalog wp ON wp.code = x.wallet_code
ON CONFLICT (profile_id, payment_method_id) DO NOTHING;

-- PT:kiosk:purchase
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
    p.id,
    pm.id,
    x.label,
    x.sort_order,
    x.is_default,
    TRUE,
    wp.id,
    x.rules_json::jsonb
FROM (
    VALUES
        ('PT:kiosk:purchase', 'mbway', 'MB WAY', 10, TRUE, 'mbway', '{"requires_amount": true, "requires_customer_phone": true}'),
        ('PT:kiosk:purchase', 'multibanco_reference', 'Multibanco', 20, FALSE, NULL, '{"requires_amount": true}'),
        ('PT:kiosk:purchase', 'creditCard', 'Cartão de crédito', 30, FALSE, NULL, '{"requires_amount": true}')
) AS x(profile_code, method_code, label, sort_order, is_default, wallet_code, rules_json)
JOIN capability_profile p ON p.profile_code = x.profile_code
JOIN payment_method_catalog pm ON pm.code = x.method_code
LEFT JOIN wallet_provider_catalog wp ON wp.code = x.wallet_code
ON CONFLICT (profile_id, payment_method_id) DO NOTHING;

-- =========================================================
-- INTERFACES
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
    pm.id,
    pi.id,
    x.sort_order,
    x.is_default,
    TRUE,
    '{}'::jsonb
FROM (
    VALUES
        ('SP:online:checkout', 'pix', 'qr_code', 10, TRUE),
        ('SP:online:checkout', 'pix', 'web_token', 20, FALSE),
        ('SP:online:checkout', 'pix', 'deep_link', 30, FALSE),
        ('SP:online:checkout', 'creditCard', 'web_token', 10, TRUE),
        ('SP:online:checkout', 'debitCard', 'web_token', 10, TRUE),

        ('SP:kiosk:purchase', 'pix', 'qr_code', 10, TRUE),
        ('SP:kiosk:purchase', 'creditCard', 'chip', 10, TRUE),
        ('SP:kiosk:purchase', 'creditCard', 'nfc', 20, FALSE),
        ('SP:kiosk:purchase', 'creditCard', 'manual', 30, FALSE),
        ('SP:kiosk:purchase', 'debitCard', 'chip', 10, TRUE),
        ('SP:kiosk:purchase', 'debitCard', 'nfc', 20, FALSE),
        ('SP:kiosk:purchase', 'giftCard', 'manual', 10, TRUE),

        ('PT:online:checkout', 'mbway', 'qr_code', 10, TRUE),
        ('PT:online:checkout', 'mbway', 'web_token', 20, FALSE),
        ('PT:online:checkout', 'multibanco_reference', 'qr_code', 10, TRUE),
        ('PT:online:checkout', 'multibanco_reference', 'web_token', 20, FALSE),
        ('PT:online:checkout', 'creditCard', 'web_token', 10, TRUE),

        ('PT:kiosk:purchase', 'mbway', 'qr_code', 10, TRUE),
        ('PT:kiosk:purchase', 'mbway', 'web_token', 20, FALSE),
        ('PT:kiosk:purchase', 'multibanco_reference', 'qr_code', 10, TRUE),
        ('PT:kiosk:purchase', 'creditCard', 'chip', 10, TRUE),
        ('PT:kiosk:purchase', 'creditCard', 'nfc', 20, FALSE)
) AS x(profile_code, method_code, interface_code, sort_order, is_default)
JOIN capability_profile p ON p.profile_code = x.profile_code
JOIN payment_method_catalog pmc ON pmc.code = x.method_code
JOIN capability_profile_method pm
    ON pm.profile_id = p.id
   AND pm.payment_method_id = pmc.id
JOIN payment_interface_catalog pi ON pi.code = x.interface_code
ON CONFLICT (profile_method_id, payment_interface_id) DO NOTHING;

-- =========================================================
-- REQUIREMENTS
-- =========================================================

INSERT INTO capability_profile_method_requirement (
    profile_method_id,
    requirement_id,
    is_required,
    requirement_scope,
    validation_json
)
SELECT
    pm.id,
    rq.id,
    TRUE,
    'request',
    '{}'::jsonb
FROM (
    VALUES
        ('SP:online:checkout', 'pix', 'amount_cents'),
        ('SP:online:checkout', 'creditCard', 'amount_cents'),
        ('SP:online:checkout', 'debitCard', 'amount_cents'),

        ('SP:kiosk:purchase', 'pix', 'amount_cents'),
        ('SP:kiosk:purchase', 'creditCard', 'amount_cents'),
        ('SP:kiosk:purchase', 'debitCard', 'amount_cents'),

        ('PT:online:checkout', 'mbway', 'amount_cents'),
        ('PT:online:checkout', 'mbway', 'customer_phone'),
        ('PT:online:checkout', 'mbway', 'wallet_provider'),
        ('PT:online:checkout', 'multibanco_reference', 'amount_cents'),
        ('PT:online:checkout', 'creditCard', 'amount_cents'),

        ('PT:kiosk:purchase', 'mbway', 'amount_cents'),
        ('PT:kiosk:purchase', 'mbway', 'customer_phone'),
        ('PT:kiosk:purchase', 'mbway', 'wallet_provider'),
        ('PT:kiosk:purchase', 'multibanco_reference', 'amount_cents'),
        ('PT:kiosk:purchase', 'creditCard', 'amount_cents')
) AS x(profile_code, method_code, requirement_code)
JOIN capability_profile p ON p.profile_code = x.profile_code
JOIN payment_method_catalog pmc ON pmc.code = x.method_code
JOIN capability_profile_method pm
    ON pm.profile_id = p.id
   AND pm.payment_method_id = pmc.id
JOIN capability_requirement_catalog rq ON rq.code = x.requirement_code
ON CONFLICT (profile_method_id, requirement_id) DO NOTHING;

-- =========================================================
-- CONSTRAINTS
-- =========================================================

INSERT INTO capability_profile_constraint (
    profile_id,
    code,
    value_json
)
SELECT
    p.id,
    x.code,
    to_jsonb(x.value_text)
FROM (
    VALUES
        ('SP:online:checkout', 'pickup_window_sec', '7200'),
        ('SP:online:checkout', 'prepayment_timeout_sec', '90'),
        ('SP:kiosk:purchase', 'pickup_window_sec', '7200'),
        ('SP:kiosk:purchase', 'prepayment_timeout_sec', '90'),
        ('SP:kiosk:pickup', 'pickup_window_sec', '7200'),

        ('PT:online:checkout', 'pickup_window_sec', '7200'),
        ('PT:online:checkout', 'prepayment_timeout_sec', '120'),
        ('PT:kiosk:purchase', 'pickup_window_sec', '7200'),
        ('PT:kiosk:purchase', 'prepayment_timeout_sec', '120'),
        ('PT:kiosk:pickup', 'pickup_window_sec', '7200')
) AS x(profile_code, code, value_text)
JOIN capability_profile p ON p.profile_code = x.profile_code
ON CONFLICT (profile_id, code) DO NOTHING;

COMMIT;