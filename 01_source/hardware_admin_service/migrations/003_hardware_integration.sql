-- Integration hub: segment taxonomy, player capabilities, relations, locker channel bindings

ALTER TABLE hardware_ecosystem_players
    ADD COLUMN IF NOT EXISTS parent_group VARCHAR(32) DEFAULT 'LOCKER_NETWORK' NOT NULL,
    ADD COLUMN IF NOT EXISTS integration_mode VARCHAR(32) DEFAULT 'DIRECT_API' NOT NULL,
    ADD COLUMN IF NOT EXISTS supports_lockers BOOLEAN DEFAULT true NOT NULL,
    ADD COLUMN IF NOT EXISTS supports_marketplace BOOLEAN DEFAULT false NOT NULL,
    ADD COLUMN IF NOT EXISTS supports_food_delivery BOOLEAN DEFAULT false NOT NULL,
    ADD COLUMN IF NOT EXISTS supports_aggregation BOOLEAN DEFAULT false NOT NULL;

CREATE INDEX IF NOT EXISTS ix_hw_eco_player_parent ON hardware_ecosystem_players (parent_group);

CREATE TABLE IF NOT EXISTS hardware_player_segment_catalog (
    code VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    parent_group VARCHAR(32) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 100 NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_hw_player_seg_parent ON hardware_player_segment_catalog (parent_group);

CREATE TABLE IF NOT EXISTS hardware_player_integration_capabilities (
    id VARCHAR(36) PRIMARY KEY,
    player_id VARCHAR(36) NOT NULL,
    player_code VARCHAR(48) NOT NULL,
    capability_code VARCHAR(40) NOT NULL,
    protocol VARCHAR(24) NOT NULL,
    direction VARCHAR(16) NOT NULL,
    target_domain VARCHAR(32) DEFAULT 'HARDWARE' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT uq_hw_player_cap_domain UNIQUE (player_id, capability_code, target_domain)
);

CREATE INDEX IF NOT EXISTS ix_hw_player_cap_code ON hardware_player_integration_capabilities (player_code);

CREATE TABLE IF NOT EXISTS hardware_ecosystem_player_relations (
    id VARCHAR(36) PRIMARY KEY,
    from_player_id VARCHAR(36) NOT NULL,
    from_player_code VARCHAR(48) NOT NULL,
    to_player_id VARCHAR(36) NOT NULL,
    to_player_code VARCHAR(48) NOT NULL,
    relation_type VARCHAR(32) NOT NULL,
    notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT uq_hw_player_relation UNIQUE (from_player_id, to_player_id, relation_type)
);

CREATE INDEX IF NOT EXISTS ix_hw_player_rel_from ON hardware_ecosystem_player_relations (from_player_id);
CREATE INDEX IF NOT EXISTS ix_hw_player_rel_to ON hardware_ecosystem_player_relations (to_player_id);

CREATE TABLE IF NOT EXISTS hardware_locker_channel_bindings (
    id VARCHAR(36) PRIMARY KEY,
    locker_id VARCHAR(120) NOT NULL,
    channel_type VARCHAR(32) NOT NULL,
    player_id VARCHAR(36),
    player_code VARCHAR(48) NOT NULL,
    player_name VARCHAR(160) NOT NULL,
    integration_mode VARCHAR(32) DEFAULT 'DIRECT_API' NOT NULL,
    priority INTEGER DEFAULT 100 NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT uq_hw_locker_channel UNIQUE (locker_id, channel_type, player_code)
);

CREATE INDEX IF NOT EXISTS ix_hw_locker_channel_locker ON hardware_locker_channel_bindings (locker_id, channel_type);
CREATE INDEX IF NOT EXISTS ix_hw_locker_channel_player ON hardware_locker_channel_bindings (player_code);
