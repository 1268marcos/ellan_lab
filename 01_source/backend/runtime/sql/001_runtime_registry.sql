-- 01_source/backend/runtime/sql/001_runtime_registry.sql

BEGIN;

CREATE TABLE IF NOT EXISTS runtime_lockers (
    locker_id               VARCHAR(120) PRIMARY KEY,
    machine_id              VARCHAR(120) NOT NULL UNIQUE,
    display_name            VARCHAR(255) NOT NULL,
    region                  VARCHAR(16) NOT NULL,
    country                 VARCHAR(8) NOT NULL,
    timezone                VARCHAR(64) NOT NULL,
    operator_id             VARCHAR(120),
    temperature_zone        VARCHAR(32) NOT NULL DEFAULT 'AMBIENT',
    security_level          VARCHAR(32) NOT NULL DEFAULT 'STANDARD',

    active                  BOOLEAN NOT NULL DEFAULT TRUE,
    runtime_enabled         BOOLEAN NOT NULL DEFAULT TRUE,

    mqtt_region             VARCHAR(32) NOT NULL,
    mqtt_locker_id          VARCHAR(120) NOT NULL,

    topology_version        INTEGER NOT NULL DEFAULT 1,
    slot_count_total        INTEGER NOT NULL,

    payment_methods_json    JSONB NOT NULL DEFAULT '[]'::jsonb,

    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runtime_lockers_region
    ON runtime_lockers(region);

CREATE INDEX IF NOT EXISTS idx_runtime_lockers_active
    ON runtime_lockers(active, runtime_enabled);

CREATE TABLE IF NOT EXISTS runtime_locker_slots (
    locker_id               VARCHAR(120) NOT NULL REFERENCES runtime_lockers(locker_id) ON DELETE CASCADE,
    slot_number             INTEGER NOT NULL,
    slot_size               VARCHAR(16) NOT NULL,
    width_cm                INTEGER,
    height_cm               INTEGER,
    depth_cm                INTEGER,
    max_weight_kg           NUMERIC(10, 3),
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (locker_id, slot_number)
);

CREATE INDEX IF NOT EXISTS idx_runtime_locker_slots_active
    ON runtime_locker_slots(locker_id, is_active, slot_number);

CREATE TABLE IF NOT EXISTS runtime_locker_features (
    locker_id                       VARCHAR(120) PRIMARY KEY REFERENCES runtime_lockers(locker_id) ON DELETE CASCADE,
    supports_online                 BOOLEAN NOT NULL DEFAULT TRUE,
    supports_kiosk                  BOOLEAN NOT NULL DEFAULT TRUE,
    supports_pickup_qr              BOOLEAN NOT NULL DEFAULT TRUE,
    supports_manual_code            BOOLEAN NOT NULL DEFAULT TRUE,
    supports_open_command           BOOLEAN NOT NULL DEFAULT TRUE,
    supports_light_command          BOOLEAN NOT NULL DEFAULT TRUE,
    supports_paid_pending_pickup    BOOLEAN NOT NULL DEFAULT TRUE,
    supports_refrigerated_items     BOOLEAN NOT NULL DEFAULT FALSE,
    supports_frozen_items           BOOLEAN NOT NULL DEFAULT FALSE,
    supports_high_value_items       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS door_state (
    machine_id   VARCHAR(120) NOT NULL,
    door_id      INTEGER NOT NULL,
    state        VARCHAR(40) NOT NULL,
    product_id   VARCHAR(120),
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (machine_id, door_id)
);

CREATE INDEX IF NOT EXISTS idx_door_state_machine
    ON door_state(machine_id);

CREATE INDEX IF NOT EXISTS idx_door_state_machine_state
    ON door_state(machine_id, state);

-- 01/04/2026
-- ===================================================================
-- Runtime Registry Schema
-- Version: 001
-- Description: Core tables for locker payment methods and runtime configuration
-- ===================================================================

-- Tabela: locker_payment_methods
-- Descrição: Define os métodos de pagamento disponíveis por locker
-- ===================================================================
CREATE TABLE IF NOT EXISTS locker_payment_methods (
    locker_id VARCHAR(120) NOT NULL REFERENCES lockers(id) ON DELETE CASCADE,
    method VARCHAR(64) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (locker_id, method)
);

-- Índices para locker_payment_methods
-- Índice para busca por locker (consultas frequentes)
CREATE INDEX IF NOT EXISTS idx_locker_payment_methods_locker_id 
ON locker_payment_methods(locker_id);

-- Índice para busca por método de pagamento ativo
CREATE INDEX IF NOT EXISTS idx_locker_payment_methods_active 
ON locker_payment_methods(is_active) 
WHERE is_active = TRUE;

-- Índice composto para consultas que filtram por locker e status ativo
CREATE INDEX IF NOT EXISTS idx_locker_payment_methods_locker_active 
ON locker_payment_methods(locker_id, is_active) 
WHERE is_active = TRUE;

-- Índice para ordenação por data de criação/atualização
CREATE INDEX IF NOT EXISTS idx_locker_payment_methods_created_at 
ON locker_payment_methods(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_locker_payment_methods_updated_at 
ON locker_payment_methods(updated_at DESC);

-- ===================================================================
-- Função para atualizar automaticamente o updated_at
-- ===================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar updated_at automaticamente
DROP TRIGGER IF EXISTS update_locker_payment_methods_updated_at 
ON locker_payment_methods;

CREATE TRIGGER update_locker_payment_methods_updated_at
    BEFORE UPDATE ON locker_payment_methods
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===================================================================
-- Comentários para documentação
-- ===================================================================
COMMENT ON TABLE locker_payment_methods IS 'Métodos de pagamento disponíveis por locker';
COMMENT ON COLUMN locker_payment_methods.locker_id IS 'ID do locker (referencia lockers.id)';
COMMENT ON COLUMN locker_payment_methods.method IS 'Método de pagamento (PIX, NFC, CARTAO_CREDITO, etc)';
COMMENT ON COLUMN locker_payment_methods.is_active IS 'Indica se o método está ativo para o locker';
COMMENT ON COLUMN locker_payment_methods.created_at IS 'Data de criação do registro';
COMMENT ON COLUMN locker_payment_methods.updated_at IS 'Data da última atualização';

-- ===================================================================
-- Estatísticas para otimização do planner
-- ===================================================================
ANALYZE locker_payment_methods;






COMMIT;