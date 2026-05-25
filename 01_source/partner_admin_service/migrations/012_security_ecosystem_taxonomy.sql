-- Taxonomia mundial: segmentos, relações player↔player, canais de integração

ALTER TABLE security_locker_player_registry ADD COLUMN IF NOT EXISTS parent_group character varying(40);
ALTER TABLE security_locker_player_registry ADD COLUMN IF NOT EXISTS integration_modes_json text DEFAULT '[]';
ALTER TABLE security_locker_player_registry ADD COLUMN IF NOT EXISTS external_refs_json text DEFAULT '{}';

CREATE TABLE IF NOT EXISTS security_player_segments (
    code character varying(32) NOT NULL PRIMARY KEY,
    label character varying(128) NOT NULL,
    description character varying(500),
    primary_domain character varying(32) NOT NULL,
    sort_order integer DEFAULT 100 NOT NULL,
    icon_key character varying(32),
    is_active boolean DEFAULT true NOT NULL
);

CREATE TABLE IF NOT EXISTS security_player_relations (
    id character varying(36) NOT NULL PRIMARY KEY,
    from_player_code character varying(48) NOT NULL,
    to_player_code character varying(48) NOT NULL,
    relation_type character varying(40) NOT NULL,
    strength character varying(16) DEFAULT 'PRIMARY' NOT NULL,
    notes character varying(500),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (from_player_code, to_player_code, relation_type)
);

CREATE TABLE IF NOT EXISTS security_player_integrations (
    id character varying(36) NOT NULL PRIMARY KEY,
    player_code character varying(48) NOT NULL,
    channel_type character varying(32) NOT NULL,
    direction character varying(16) DEFAULT 'BIDIRECTIONAL' NOT NULL,
    target_domain character varying(32) NOT NULL,
    capability_key character varying(64) NOT NULL,
    is_required boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    metadata_json text DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_sec_player_rel_from ON security_player_relations (from_player_code);
CREATE INDEX IF NOT EXISTS ix_sec_player_rel_to ON security_player_relations (to_player_code);
CREATE INDEX IF NOT EXISTS ix_sec_player_int_player ON security_player_integrations (player_code, is_active);
