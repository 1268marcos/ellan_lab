-- Tabelas auxiliares do locker_create_service (Postgres central)
CREATE TABLE IF NOT EXISTS locker_webhook_configs (
    locker_id character varying(64) NOT NULL PRIMARY KEY REFERENCES lockers(id) ON DELETE CASCADE,
    url character varying(512) NOT NULL,
    secret_hash character varying(128),
    events text NOT NULL DEFAULT 'locker.created,locker.updated',
    active boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone NOT NULL DEFAULT NOW(),
    updated_at timestamp without time zone NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS locker_api_keys (
    id serial PRIMARY KEY,
    locker_id character varying(64) NOT NULL REFERENCES lockers(id) ON DELETE CASCADE,
    key_prefix character varying(16) NOT NULL,
    key_hash character varying(128) NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone NOT NULL DEFAULT NOW(),
    rotated_at timestamp without time zone
);

CREATE INDEX IF NOT EXISTS idx_locker_api_keys_locker ON locker_api_keys (locker_id, active);
