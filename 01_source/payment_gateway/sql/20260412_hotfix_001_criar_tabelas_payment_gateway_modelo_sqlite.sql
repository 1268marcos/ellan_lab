BEGIN;

-- =========================================================
-- HOTFIX PG_GATEWAY_AUDIT_001
-- Espelhar no Postgres as tabelas locais hoje usadas no SQLite
-- do payment_gateway:
--   - idempotency_keys
--   - device_registry
--   - risk_events
-- =========================================================

-- =========================================================
-- 1) IDEMPOTENCY KEYS
-- =========================================================
CREATE TABLE IF NOT EXISTS public.idempotency_keys (
    id              text PRIMARY KEY,
    endpoint        text NOT NULL,
    idem_key        text NOT NULL,
    payload_hash    text NOT NULL,
    response_blob   text NOT NULL,
    status          text NOT NULL,
    created_at      bigint NOT NULL,
    expires_at      bigint NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_idem_endpoint_key
    ON public.idempotency_keys (endpoint, idem_key);

CREATE INDEX IF NOT EXISTS ix_idem_expires
    ON public.idempotency_keys (expires_at);


-- =========================================================
-- 2) DEVICE REGISTRY
-- =========================================================
CREATE TABLE IF NOT EXISTS public.device_registry (
    device_hash     text PRIMARY KEY,
    version         text NOT NULL,
    first_seen_at   bigint NOT NULL,
    last_seen_at    bigint NOT NULL,
    seen_count      integer NOT NULL DEFAULT 1,
    flags_json      jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_device_last_seen
    ON public.device_registry (last_seen_at);


-- =========================================================
-- 3) RISK EVENTS
-- =========================================================
CREATE TABLE IF NOT EXISTS public.risk_events (
    id              text PRIMARY KEY,
    request_id      text NOT NULL,
    event_type      text NOT NULL,
    decision        text NOT NULL,
    score           integer NOT NULL,
    policy_id       text NOT NULL,
    region          text NOT NULL,
    locker_id       text NOT NULL,
    porta           integer NOT NULL,
    created_at      bigint NOT NULL,
    reasons_json    jsonb NOT NULL DEFAULT '[]'::jsonb,
    signals_json    jsonb NOT NULL DEFAULT '{}'::jsonb,
    audit_event_id  text NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_risk_created_at
    ON public.risk_events (created_at);

CREATE INDEX IF NOT EXISTS ix_risk_region_locker_porta
    ON public.risk_events (region, locker_id, porta);


-- =========================================================
-- 4) CHECKS BÁSICOS DE INTEGRIDADE
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_risk_events_score_range'
    ) THEN
        ALTER TABLE public.risk_events
        ADD CONSTRAINT ck_risk_events_score_range
        CHECK (score >= 0 AND score <= 100);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_risk_events_porta_positive'
    ) THEN
        ALTER TABLE public.risk_events
        ADD CONSTRAINT ck_risk_events_porta_positive
        CHECK (porta > 0);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_device_registry_seen_count_positive'
    ) THEN
        ALTER TABLE public.device_registry
        ADD CONSTRAINT ck_device_registry_seen_count_positive
        CHECK (seen_count >= 1);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_decision_allowed_values'
    ) THEN
        ALTER TABLE public.risk_events
        ADD CONSTRAINT ck_decision_allowed_values
        CHECK (UPPER(decision) IN ('ALLOW', 'BLOCK', 'CHALLENGE'));
    END IF;
END $$;


-- =========================================================
-- 5) DADOS INICIAIS MÍNIMOS
-- Não insere eventos reais; apenas deixa a estrutura pronta.
-- Seed técnico opcional para smoke test.
-- =========================================================

INSERT INTO public.device_registry (
    device_hash,
    version,
    first_seen_at,
    last_seen_at,
    seen_count,
    flags_json
)
SELECT
    '__seed_device_hash__',
    'v1',
    EXTRACT(EPOCH FROM NOW())::bigint,
    EXTRACT(EPOCH FROM NOW())::bigint,
    1,
    '{"seed": true}'::jsonb
WHERE NOT EXISTS (
    SELECT 1
    FROM public.device_registry
    WHERE device_hash = '__seed_device_hash__'
);

INSERT INTO public.idempotency_keys (
    id,
    endpoint,
    idem_key,
    payload_hash,
    response_blob,
    status,
    created_at,
    expires_at
)
SELECT
    '__seed_idempotency__',
    '/__seed__',
    '__seed_key__',
    '__seed_payload_hash__',
    '{"seed": true}'::text,
    'SEED',
    EXTRACT(EPOCH FROM NOW())::bigint,
    EXTRACT(EPOCH FROM NOW())::bigint + 3600
WHERE NOT EXISTS (
    SELECT 1
    FROM public.idempotency_keys
    WHERE id = '__seed_idempotency__'
);

INSERT INTO public.risk_events (
    id,
    request_id,
    event_type,
    decision,
    score,
    policy_id,
    region,
    locker_id,
    porta,
    created_at,
    reasons_json,
    signals_json,
    audit_event_id
)
SELECT
    '__seed_risk_event__',
    '__seed_request__',
    'PAYMENT',
    'ALLOW',
    0,
    '__seed_policy__',
    'SP',
    '__seed_locker__',
    1,
    EXTRACT(EPOCH FROM NOW())::bigint,
    '[]'::jsonb,
    '{}'::jsonb,
    '__seed_audit_event__'
WHERE NOT EXISTS (
    SELECT 1
    FROM public.risk_events
    WHERE id = '__seed_risk_event__'
);

COMMIT;


-- =========================================================
-- VALIDAÇÃO 1
-- =========================================================
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('idempotency_keys', 'device_registry', 'risk_events')
ORDER BY table_name;

-- =========================================================
-- VALIDAÇÃO 2
-- =========================================================
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('idempotency_keys', 'device_registry', 'risk_events')
ORDER BY tablename, indexname;

-- =========================================================
-- VALIDAÇÃO 3
-- =========================================================
SELECT
    (SELECT COUNT(*) FROM public.idempotency_keys) AS total_idempotency_keys,
    (SELECT COUNT(*) FROM public.device_registry) AS total_device_registry,
    (SELECT COUNT(*) FROM public.risk_events) AS total_risk_events;