BEGIN;

-- =========================================================
-- HOTFIX PG_GATEWAY_002
-- ELLAN LAB
-- Estruturas Postgres profissionais para payment_gateway
-- com namespace explícito em nome de tabela
--
-- NOVAS TABELAS:
--   payment_gateway_idempotency_keys
--   payment_gateway_device_registry
--   payment_gateway_risk_events
--
-- OBS:
-- - usa slot (não usa porta)
-- - não sobrescreve tabelas legadas
-- - pronto para evolução futura
-- =========================================================


-- =========================================================
-- 1) PAYMENT GATEWAY - IDEMPOTENCY KEYS
-- =========================================================
CREATE TABLE IF NOT EXISTS public.payment_gateway_idempotency_keys (
    id                  text PRIMARY KEY,
    endpoint            text NOT NULL,
    idem_key            text NOT NULL,
    payload_hash        text NOT NULL,
    response_blob       jsonb NOT NULL DEFAULT '{}'::jsonb,
    status              text NOT NULL,
    region_code         varchar(20),
    sales_channel       varchar(50),
    request_fingerprint text,
    created_at_epoch    bigint NOT NULL,
    expires_at_epoch    bigint NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pg_gateway_idem_endpoint_key
    ON public.payment_gateway_idempotency_keys (endpoint, idem_key);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_idem_expires_epoch
    ON public.payment_gateway_idempotency_keys (expires_at_epoch);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_idem_region_channel
    ON public.payment_gateway_idempotency_keys (region_code, sales_channel);


-- =========================================================
-- 2) PAYMENT GATEWAY - DEVICE REGISTRY
-- =========================================================
CREATE TABLE IF NOT EXISTS public.payment_gateway_device_registry (
    device_hash         text PRIMARY KEY,
    version             text NOT NULL,
    first_seen_at_epoch bigint NOT NULL,
    last_seen_at_epoch  bigint NOT NULL,
    seen_count          integer NOT NULL DEFAULT 1,
    region_code         varchar(20),
    locker_id           varchar(120),
    flags_json          jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_device_last_seen_epoch
    ON public.payment_gateway_device_registry (last_seen_at_epoch);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_device_region_locker
    ON public.payment_gateway_device_registry (region_code, locker_id);


-- =========================================================
-- 3) PAYMENT GATEWAY - RISK EVENTS
-- =========================================================
CREATE TABLE IF NOT EXISTS public.payment_gateway_risk_events (
    id                  text PRIMARY KEY,
    request_id          text NOT NULL,
    event_type          text NOT NULL,
    decision            text NOT NULL,
    score               integer NOT NULL,
    policy_id           text NOT NULL,
    region_code         varchar(20) NOT NULL,
    locker_id           varchar(120) NOT NULL,
    slot                integer NOT NULL,
    audit_event_id      text NOT NULL,
    reasons_json        jsonb NOT NULL DEFAULT '[]'::jsonb,
    signals_json        jsonb NOT NULL DEFAULT '{}'::jsonb,
    metadata_json       jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at_epoch    bigint NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_risk_created_at_epoch
    ON public.payment_gateway_risk_events (created_at_epoch);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_risk_region_locker_slot
    ON public.payment_gateway_risk_events (region_code, locker_id, slot);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_risk_decision
    ON public.payment_gateway_risk_events (decision);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_risk_policy_id
    ON public.payment_gateway_risk_events (policy_id);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_risk_request_id
    ON public.payment_gateway_risk_events (request_id);

CREATE INDEX IF NOT EXISTS ix_pg_gateway_risk_event_type
    ON public.payment_gateway_risk_events (event_type);


-- =========================================================
-- 4) CONSTRAINTS
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_pg_gateway_risk_score_range'
    ) THEN
        ALTER TABLE public.payment_gateway_risk_events
        ADD CONSTRAINT ck_pg_gateway_risk_score_range
        CHECK (score >= 0 AND score <= 100);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_pg_gateway_risk_slot_positive'
    ) THEN
        ALTER TABLE public.payment_gateway_risk_events
        ADD CONSTRAINT ck_pg_gateway_risk_slot_positive
        CHECK (slot > 0);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_pg_gateway_risk_decision_values'
    ) THEN
        ALTER TABLE public.payment_gateway_risk_events
        ADD CONSTRAINT ck_pg_gateway_risk_decision_values
        CHECK (UPPER(decision) IN ('ALLOW', 'BLOCK', 'CHALLENGE'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_pg_gateway_device_seen_count_positive'
    ) THEN
        ALTER TABLE public.payment_gateway_device_registry
        ADD CONSTRAINT ck_pg_gateway_device_seen_count_positive
        CHECK (seen_count >= 1);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_pg_gateway_idem_expires_after_create'
    ) THEN
        ALTER TABLE public.payment_gateway_idempotency_keys
        ADD CONSTRAINT ck_pg_gateway_idem_expires_after_create
        CHECK (expires_at_epoch >= created_at_epoch);
    END IF;
END $$;


-- =========================================================
-- 5) UPDATED_AT TRIGGER
-- =========================================================
CREATE OR REPLACE FUNCTION public.set_row_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_pg_gateway_idempotency_keys_updated_at
ON public.payment_gateway_idempotency_keys;

CREATE TRIGGER trg_pg_gateway_idempotency_keys_updated_at
BEFORE UPDATE ON public.payment_gateway_idempotency_keys
FOR EACH ROW
EXECUTE FUNCTION public.set_row_updated_at();

DROP TRIGGER IF EXISTS trg_pg_gateway_device_registry_updated_at
ON public.payment_gateway_device_registry;

CREATE TRIGGER trg_pg_gateway_device_registry_updated_at
BEFORE UPDATE ON public.payment_gateway_device_registry
FOR EACH ROW
EXECUTE FUNCTION public.set_row_updated_at();

DROP TRIGGER IF EXISTS trg_pg_gateway_risk_events_updated_at
ON public.payment_gateway_risk_events;

CREATE TRIGGER trg_pg_gateway_risk_events_updated_at
BEFORE UPDATE ON public.payment_gateway_risk_events
FOR EACH ROW
EXECUTE FUNCTION public.set_row_updated_at();


-- =========================================================
-- 6) SEED TÉCNICO INICIAL
-- =========================================================

-- 6.1 Device registry seed
INSERT INTO public.payment_gateway_device_registry (
    device_hash,
    version,
    first_seen_at_epoch,
    last_seen_at_epoch,
    seen_count,
    region_code,
    locker_id,
    flags_json
)
SELECT
    'pgw_seed_device_hash_sp_001',
    'v1',
    EXTRACT(EPOCH FROM now())::bigint,
    EXTRACT(EPOCH FROM now())::bigint,
    1,
    'SP',
    'SP-ALPHAVILLE-SHOP-LK-001',
    jsonb_build_object(
        'seed', true,
        'environment', 'lab',
        'source', 'postgres_hotfix'
    )
WHERE NOT EXISTS (
    SELECT 1
    FROM public.payment_gateway_device_registry
    WHERE device_hash = 'pgw_seed_device_hash_sp_001'
);

INSERT INTO public.payment_gateway_device_registry (
    device_hash,
    version,
    first_seen_at_epoch,
    last_seen_at_epoch,
    seen_count,
    region_code,
    locker_id,
    flags_json
)
SELECT
    'pgw_seed_device_hash_pt_001',
    'v1',
    EXTRACT(EPOCH FROM now())::bigint,
    EXTRACT(EPOCH FROM now())::bigint,
    1,
    'PT',
    'PT-LISBOA-CENTRO-LK-001',
    jsonb_build_object(
        'seed', true,
        'environment', 'lab',
        'source', 'postgres_hotfix'
    )
WHERE NOT EXISTS (
    SELECT 1
    FROM public.payment_gateway_device_registry
    WHERE device_hash = 'pgw_seed_device_hash_pt_001'
);


-- 6.2 Idempotency seed
INSERT INTO public.payment_gateway_idempotency_keys (
    id,
    endpoint,
    idem_key,
    payload_hash,
    response_blob,
    status,
    region_code,
    sales_channel,
    request_fingerprint,
    created_at_epoch,
    expires_at_epoch
)
SELECT
    'pgw_seed_idem_sp_pix_001',
    '/payment/create',
    'seed-idem-key-sp-pix-001',
    'seed-payload-hash-sp-pix-001',
    jsonb_build_object(
        'seed', true,
        'provider', 'mercadopago',
        'status', 'PENDING'
    ),
    'PENDING',
    'SP',
    'ONLINE',
    'seed-request-fingerprint-sp-001',
    EXTRACT(EPOCH FROM now())::bigint,
    EXTRACT(EPOCH FROM now())::bigint + 3600
WHERE NOT EXISTS (
    SELECT 1
    FROM public.payment_gateway_idempotency_keys
    WHERE id = 'pgw_seed_idem_sp_pix_001'
);

INSERT INTO public.payment_gateway_idempotency_keys (
    id,
    endpoint,
    idem_key,
    payload_hash,
    response_blob,
    status,
    region_code,
    sales_channel,
    request_fingerprint,
    created_at_epoch,
    expires_at_epoch
)
SELECT
    'pgw_seed_idem_sp_kiosk_card_001',
    '/payment/create',
    'seed-idem-key-sp-kiosk-card-001',
    'seed-payload-hash-sp-kiosk-card-001',
    jsonb_build_object(
        'seed', true,
        'provider', 'pinpad_stub',
        'status', 'CREATED'
    ),
    'CREATED',
    'SP',
    'KIOSK',
    'seed-request-fingerprint-sp-kiosk-001',
    EXTRACT(EPOCH FROM now())::bigint,
    EXTRACT(EPOCH FROM now())::bigint + 1800
WHERE NOT EXISTS (
    SELECT 1
    FROM public.payment_gateway_idempotency_keys
    WHERE id = 'pgw_seed_idem_sp_kiosk_card_001'
);


-- 6.3 Risk events seed
INSERT INTO public.payment_gateway_risk_events (
    id,
    request_id,
    event_type,
    decision,
    score,
    policy_id,
    region_code,
    locker_id,
    slot,
    audit_event_id,
    reasons_json,
    signals_json,
    metadata_json,
    created_at_epoch
)
SELECT
    'pgw_seed_risk_event_001',
    'pgw_seed_request_001',
    'PAYMENT',
    'ALLOW',
    5,
    'policy_default_allow',
    'SP',
    'SP-ALPHAVILLE-SHOP-LK-001',
    27,
    'pgw_seed_audit_event_001',
    jsonb_build_array(
        jsonb_build_object(
            'code', 'LOW_RISK_PROFILE',
            'message', 'Seed técnico de evento allow'
        )
    ),
    jsonb_build_object(
        'device_hash', 'pgw_seed_device_hash_sp_001',
        'ip_hash', 'seed_ip_hash_001',
        'channel', 'KIOSK'
    ),
    jsonb_build_object(
        'seed', true,
        'currency', 'BRL',
        'amount_cents', 4990
    ),
    EXTRACT(EPOCH FROM now())::bigint
WHERE NOT EXISTS (
    SELECT 1
    FROM public.payment_gateway_risk_events
    WHERE id = 'pgw_seed_risk_event_001'
);

INSERT INTO public.payment_gateway_risk_events (
    id,
    request_id,
    event_type,
    decision,
    score,
    policy_id,
    region_code,
    locker_id,
    slot,
    audit_event_id,
    reasons_json,
    signals_json,
    metadata_json,
    created_at_epoch
)
SELECT
    'pgw_seed_risk_event_002',
    'pgw_seed_request_002',
    'PAYMENT',
    'CHALLENGE',
    62,
    'policy_bin_review',
    'SP',
    'SP-VILAOLIMPIA-FOOD-LK-001',
    14,
    'pgw_seed_audit_event_002',
    jsonb_build_array(
        jsonb_build_object(
            'code', 'CARD_REVIEW_REQUIRED',
            'message', 'Seed técnico de desafio para cartão'
        ),
        jsonb_build_object(
            'code', 'HIGH_TICKET_PATTERN',
            'message', 'Valor acima do baseline da máquina'
        )
    ),
    jsonb_build_object(
        'device_hash', 'pgw_seed_device_hash_sp_001',
        'ip_hash', 'seed_ip_hash_002',
        'channel', 'KIOSK',
        'card_type', 'CREDIT'
    ),
    jsonb_build_object(
        'seed', true,
        'currency', 'BRL',
        'amount_cents', 11099
    ),
    EXTRACT(EPOCH FROM now())::bigint
WHERE NOT EXISTS (
    SELECT 1
    FROM public.payment_gateway_risk_events
    WHERE id = 'pgw_seed_risk_event_002'
);

INSERT INTO public.payment_gateway_risk_events (
    id,
    request_id,
    event_type,
    decision,
    score,
    policy_id,
    region_code,
    locker_id,
    slot,
    audit_event_id,
    reasons_json,
    signals_json,
    metadata_json,
    created_at_epoch
)
SELECT
    'pgw_seed_risk_event_003',
    'pgw_seed_request_003',
    'PAYMENT',
    'BLOCK',
    96,
    'policy_device_abuse_block',
    'PT',
    'PT-LISBOA-CENTRO-LK-001',
    8,
    'pgw_seed_audit_event_003',
    jsonb_build_array(
        jsonb_build_object(
            'code', 'DEVICE_ABUSE_SIGNAL',
            'message', 'Múltiplas tentativas suspeitas'
        ),
        jsonb_build_object(
            'code', 'GEO_VELOCITY',
            'message', 'Padrão incompatível com origem esperada'
        )
    ),
    jsonb_build_object(
        'device_hash', 'pgw_seed_device_hash_pt_001',
        'ip_hash', 'seed_ip_hash_003',
        'channel', 'ONLINE'
    ),
    jsonb_build_object(
        'seed', true,
        'currency', 'EUR',
        'amount_cents', 4899
    ),
    EXTRACT(EPOCH FROM now())::bigint
WHERE NOT EXISTS (
    SELECT 1
    FROM public.payment_gateway_risk_events
    WHERE id = 'pgw_seed_risk_event_003'
);

COMMIT;


-- =========================================================
-- VALIDAÇÃO 1
-- =========================================================
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'payment_gateway_idempotency_keys',
      'payment_gateway_device_registry',
      'payment_gateway_risk_events'
  )
ORDER BY table_name;

-- =========================================================
-- VALIDAÇÃO 2
-- =========================================================
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN (
      'payment_gateway_idempotency_keys',
      'payment_gateway_device_registry',
      'payment_gateway_risk_events'
  )
ORDER BY tablename, indexname;

-- =========================================================
-- VALIDAÇÃO 3
-- =========================================================
SELECT
    (SELECT COUNT(*) FROM public.payment_gateway_idempotency_keys) AS total_payment_gateway_idempotency_keys,
    (SELECT COUNT(*) FROM public.payment_gateway_device_registry) AS total_payment_gateway_device_registry,
    (SELECT COUNT(*) FROM public.payment_gateway_risk_events) AS total_payment_gateway_risk_events;

-- =========================================================
-- VALIDAÇÃO 4
-- =========================================================
SELECT
    region_code,
    locker_id,
    slot,
    decision,
    score,
    policy_id
FROM public.payment_gateway_risk_events
ORDER BY created_at_epoch DESC, id;