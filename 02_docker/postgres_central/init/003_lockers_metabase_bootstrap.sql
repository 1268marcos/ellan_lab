-- Bootstrap para dev: tabela lockers (runtime sync) + DB do Metabase.
-- Idempotente; seguro em volumes já inicializados se executado manualmente.

-- Metabase application DB (fora de locker_central)
SELECT 'CREATE DATABASE metabase_app OWNER admin'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'metabase_app')\gexec

\c locker_central

CREATE TABLE IF NOT EXISTS lockers (
    id                      VARCHAR(36) PRIMARY KEY,
    display_name            VARCHAR(255),
    external_id             VARCHAR(100),
    machine_id              VARCHAR(100),
    operator_id             VARCHAR(100),
    tenant_id               VARCHAR(100),
    site_id                 VARCHAR(100),
    region                  VARCHAR(10) NOT NULL,
    timezone                VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    country                 VARCHAR(100) DEFAULT 'BR',
    address_line            VARCHAR(255),
    address_number          VARCHAR(50),
    address_extra           VARCHAR(255),
    district                VARCHAR(100),
    city                    VARCHAR(100),
    state                   VARCHAR(100),
    postal_code             VARCHAR(50),
    latitude                DOUBLE PRECISION,
    longitude               DOUBLE PRECISION,
    geolocation_wkt         TEXT,
    slots_count             INTEGER NOT NULL DEFAULT 0,
    slots_available         INTEGER NOT NULL DEFAULT 0,
    active                  BOOLEAN NOT NULL DEFAULT TRUE,
    allowed_channels        VARCHAR(100),
    allowed_payment_methods VARCHAR(255),
    access_hours            TEXT,
    has_alarm               BOOLEAN NOT NULL DEFAULT FALSE,
    has_camera              BOOLEAN NOT NULL DEFAULT FALSE,
    has_kiosk               BOOLEAN NOT NULL DEFAULT FALSE,
    has_printer             BOOLEAN NOT NULL DEFAULT FALSE,
    has_card_reader         BOOLEAN NOT NULL DEFAULT FALSE,
    has_nfc                 BOOLEAN NOT NULL DEFAULT FALSE,
    is_rented               BOOLEAN NOT NULL DEFAULT FALSE,
    security_level          VARCHAR(50) DEFAULT 'STANDARD',
    temperature_zone        VARCHAR(50) DEFAULT 'AMBIENT',
    description             TEXT,
    metadata_json           JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_lockers_active ON lockers (active);
CREATE INDEX IF NOT EXISTS ix_lockers_region ON lockers (region);
CREATE INDEX IF NOT EXISTS ix_lockers_operator ON lockers (operator_id);
