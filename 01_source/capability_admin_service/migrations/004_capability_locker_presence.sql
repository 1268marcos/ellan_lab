CREATE TABLE IF NOT EXISTS capability_player_locker_presence (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL REFERENCES capability_ecosystem_player(id) ON DELETE CASCADE,
    player_code VARCHAR(48) NOT NULL,
    locker_role VARCHAR(40) NOT NULL,
    program_code VARCHAR(48) NOT NULL,
    program_name VARCHAR(160) NOT NULL,
    region_scope VARCHAR(80) NOT NULL DEFAULT 'GLOBAL',
    supports_inbound BOOLEAN NOT NULL DEFAULT TRUE,
    supports_outbound BOOLEAN NOT NULL DEFAULT TRUE,
    supports_returns BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_player_locker_presence UNIQUE (player_id, program_code)
);

CREATE INDEX IF NOT EXISTS ix_cap_locker_presence_code ON capability_player_locker_presence(player_code);
CREATE INDEX IF NOT EXISTS ix_cap_locker_presence_role ON capability_player_locker_presence(locker_role);
