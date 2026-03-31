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

COMMIT;