-- =====================================================================
-- 02_docker/postgres_central/init/001_schema.sql
-- POSTGRES CENTRAL SCHEMA (locker_central)
-- - UTC epoch em BIGINT (segundos)
-- - Suporte a ONLINE e GUEST_TOTEM (guest também vira order)
-- - QR rotativo: janela 2h + step 10min (ou configurável)
-- - Crédito automático 50%: idempotente (UNIQUE(order_id,type))
-- - Auditoria consolidada: gateway_events (append-only)
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Extensões úteis (opcional)
-- ---------------------------------------------------------------------
-- CREATE EXTENSION IF NOT EXISTS pgcrypto; -- se quiser gerar UUID no banco
-- (você pode gerar UUID no app e manter o schema simples)

-- ---------------------------------------------------------------------
-- ENUMs como TEXT (mais flexível que enum nativo no começo)
-- Sugestão de valores:
--   channel: 'ONLINE' | 'GUEST_TOTEM'
--   order_status: 'CREATED' | 'PAID_PENDING_PICKUP' | 'PICKED_UP' |
--                'EXPIRED_CREDITED' | 'CANCELLED' | 'FAILED'
--   payment_status: 'CREATED' | 'AUTHORIZED' | 'CAPTURED' | 'FAILED' | 'REFUNDED'
--   credit_type: 'PICKUP_EXPIRED_50PCT'
-- ---------------------------------------------------------------------

-- =====================================================================
-- 1) AUDITORIA CONSOLIDADA (append-only)
-- =====================================================================
CREATE TABLE IF NOT EXISTS gateway_events (
  id            TEXT PRIMARY KEY,               -- UUID (gerado no app)
  gateway_id    TEXT NOT NULL,                  -- ex: 'PT-001', 'SP-001'
  region        TEXT NOT NULL,                  -- 'PT' | 'SP'
  locker_id     TEXT NOT NULL,                  -- ex: 'PT_LOCKER_A'
  porta         INTEGER NULL,                   -- pode ser null para eventos gerais
  event_type    TEXT NOT NULL,                  -- ex: 'PAYMENT_CONFIRMED','DOOR_OPENED','PICKUP_CONFIRMED'
  created_at    BIGINT NOT NULL,                -- UTC epoch (segundos)
  request_id    TEXT NULL,                      -- correlaciona com request/checkout
  order_id      TEXT NULL,                      -- correlaciona com pedido central
  payload_json  JSONB NOT NULL                  -- corpo livre do evento (audit trail)
);

CREATE INDEX IF NOT EXISTS ix_gateway_events_created_at
ON gateway_events (created_at);

CREATE INDEX IF NOT EXISTS ix_gateway_events_gateway_created
ON gateway_events (gateway_id, created_at);

CREATE INDEX IF NOT EXISTS ix_gateway_events_order_created
ON gateway_events (order_id, created_at);

CREATE INDEX IF NOT EXISTS ix_gateway_events_region_locker_porta_created
ON gateway_events (region, locker_id, porta, created_at);


-- =====================================================================
-- 2) ORDERS (ONLINE e GUEST_TOTEM)
-- =====================================================================
CREATE TABLE IF NOT EXISTS orders (
  id                    TEXT PRIMARY KEY,       -- UUID (gerado no app)
  channel               TEXT NOT NULL,          -- 'ONLINE' | 'GUEST_TOTEM'
  user_id               TEXT NULL,              -- para ONLINE; NULL para guest sem conta

  region                TEXT NOT NULL,          -- 'PT' | 'SP'
  locker_id              TEXT NOT NULL,
  porta                 INTEGER NOT NULL,

  amount_cents          INTEGER NOT NULL CHECK (amount_cents >= 0),
  currency              TEXT NOT NULL DEFAULT 'EUR',

  status                TEXT NOT NULL,          -- ver sugestões acima

  created_at            BIGINT NOT NULL,        -- UTC epoch (segundos)
  paid_at               BIGINT NULL,            -- UTC epoch (segundos)
  pickup_deadline_at    BIGINT NULL,            -- ONLINE: created/paid + 2h (epoch)
  picked_up_at          BIGINT NULL,            -- quando confirmado retirada

  -- Guest: captura de contato opcional (fatura/recibo + promo)
  guest_contact_email   TEXT NULL,
  guest_contact_phone   TEXT NULL,
  guest_marketing_opt_in BOOLEAN NOT NULL DEFAULT FALSE,

  -- rastreio extra opcional
  guest_session_id      TEXT NULL               -- UUID da sessão no totem
);

-- Índices essenciais para operação
CREATE INDEX IF NOT EXISTS ix_orders_status_deadline
ON orders (status, pickup_deadline_at);

CREATE INDEX IF NOT EXISTS ix_orders_region_locker_porta_status
ON orders (region, locker_id, porta, status);

CREATE INDEX IF NOT EXISTS ix_orders_user_created
ON orders (user_id, created_at);

CREATE INDEX IF NOT EXISTS ix_orders_created_at
ON orders (created_at);


-- =====================================================================
-- 3) PAYMENTS (ligado ao order)
-- =====================================================================
CREATE TABLE IF NOT EXISTS payments (
  id                 TEXT PRIMARY KEY,          -- UUID (gerado no app)
  order_id            TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,

  provider            TEXT NOT NULL,            -- ex: 'PIX', 'STRIPE', 'MBWAY', 'CARD_PRESENT'
  provider_payment_id TEXT NULL,                -- id do gateway externo (se houver)
  method              TEXT NOT NULL,            -- ex: 'PIX','CARD','MBWAY'
  status              TEXT NOT NULL,            -- 'CREATED','AUTHORIZED','CAPTURED','FAILED','REFUNDED'
  amount_cents        INTEGER NOT NULL CHECK (amount_cents >= 0),
  currency            TEXT NOT NULL DEFAULT 'EUR',

  created_at          BIGINT NOT NULL,
  confirmed_at        BIGINT NULL,

  idempotency_key     TEXT NULL,                -- para deduplicar chamadas (opcional)
  raw_json            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_payments_order_created
ON payments (order_id, created_at);

CREATE INDEX IF NOT EXISTS ix_payments_status_created
ON payments (status, created_at);

CREATE UNIQUE INDEX IF NOT EXISTS ux_payments_idempotency
ON payments (idempotency_key)
WHERE idempotency_key IS NOT NULL;


-- =====================================================================
-- 4) PICKUP TOKENS (QR rotativo)
--    - Um registro por order online
--    - QR “muda” a cada rotation_step_sec, derivado via HMAC(secret, step_index...)
-- =====================================================================
CREATE TABLE IF NOT EXISTS pickup_tokens (
  order_id            TEXT PRIMARY KEY REFERENCES orders(id) ON DELETE CASCADE,
  secret              TEXT NOT NULL,             -- string/bytes base64 (gerado no app)
  window_start_at     BIGINT NOT NULL,           -- UTC epoch
  window_end_at       BIGINT NOT NULL,           -- UTC epoch = start + 2h (ou configurável)
  rotation_step_sec   INTEGER NOT NULL DEFAULT 600, -- 10 min
  created_at          BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_pickup_tokens_window_end
ON pickup_tokens (window_end_at);


-- =====================================================================
-- 5) PICKUP ATTEMPTS (tentativas de QR)
--    - Para antifraude e suporte
-- =====================================================================
CREATE TABLE IF NOT EXISTS pickup_attempts (
  id                 TEXT PRIMARY KEY,           -- UUID
  order_id            TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  gateway_id          TEXT NOT NULL,
  created_at          BIGINT NOT NULL,
  ok                 BOOLEAN NOT NULL,
  reason              TEXT NULL,                  -- ex: 'EXPIRED','BAD_SIGNATURE','WRONG_PORTA'
  provided_step_index INTEGER NULL,               -- útil para diagnosticar clock drift
  payload_json        JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_pickup_attempts_order_created
ON pickup_attempts (order_id, created_at);

CREATE INDEX IF NOT EXISTS ix_pickup_attempts_gateway_created
ON pickup_attempts (gateway_id, created_at);


-- =====================================================================
-- 6) CREDITS (crédito automático 50% por expiração)
--    - Idempotente via UNIQUE(order_id, type)
-- =====================================================================
CREATE TABLE IF NOT EXISTS credits (
  id                 TEXT PRIMARY KEY,           -- UUID
  order_id            TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  user_id             TEXT NOT NULL,              -- crédito é para conta (online)
  type               TEXT NOT NULL,               -- 'PICKUP_EXPIRED_50PCT'
  amount_cents        INTEGER NOT NULL CHECK (amount_cents >= 0),
  currency            TEXT NOT NULL DEFAULT 'EUR',
  created_at          BIGINT NOT NULL,
  meta_json           JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE(order_id, type)
);

CREATE INDEX IF NOT EXISTS ix_credits_user_created
ON credits (user_id, created_at);

CREATE INDEX IF NOT EXISTS ix_credits_created_at
ON credits (created_at);


-- =====================================================================
-- 7) CONSTRAINTS e CHECKs úteis (opcionais)
-- =====================================================================

-- Garante que deadline só faça sentido quando existir
-- (mantemos flexível por enquanto; validação principal no app)
-- ALTER TABLE orders ADD CONSTRAINT ck_deadline_after_created
-- CHECK (pickup_deadline_at IS NULL OR pickup_deadline_at >= created_at);

COMMIT;