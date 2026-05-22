-- Partner OPS: capabilities, relações, presença por mercado

ALTER TABLE partner_ecosystem_players ADD COLUMN IF NOT EXISTS integration_status character varying(16) DEFAULT 'PLANNED';
ALTER TABLE partner_ecosystem_players ADD COLUMN IF NOT EXISTS website_url character varying(500);
ALTER TABLE partner_ecosystem_players ADD COLUMN IF NOT EXISTS estimated_locker_count integer;
ALTER TABLE partner_ecosystem_players ADD COLUMN IF NOT EXISTS data_source character varying(32) DEFAULT 'CATALOG';

CREATE TABLE IF NOT EXISTS partner_integration_capability_catalog (
    code character varying(40) NOT NULL PRIMARY KEY,
    name character varying(120) NOT NULL,
    category character varying(32) NOT NULL DEFAULT 'CORE',
    default_protocol character varying(20) NOT NULL DEFAULT 'REST',
    description text,
    sort_order integer NOT NULL DEFAULT 100
);

CREATE TABLE IF NOT EXISTS partner_player_capabilities (
    id character varying(36) NOT NULL PRIMARY KEY,
    ecosystem_player_id character varying(36) NOT NULL REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    capability_code character varying(40) NOT NULL REFERENCES partner_integration_capability_catalog(code),
    protocol character varying(20) NOT NULL DEFAULT 'REST',
    direction character varying(10) NOT NULL DEFAULT 'OUTBOUND',
    enabled boolean NOT NULL DEFAULT true,
    sandbox_ready boolean NOT NULL DEFAULT false,
    production_ready boolean NOT NULL DEFAULT false,
    notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT uq_partner_player_capability UNIQUE (ecosystem_player_id, capability_code)
);

CREATE INDEX IF NOT EXISTS idx_partner_player_cap_player ON partner_player_capabilities (ecosystem_player_id);

CREATE TABLE IF NOT EXISTS partner_player_relations (
    id character varying(36) NOT NULL PRIMARY KEY,
    from_player_id character varying(36) NOT NULL REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    to_player_id character varying(36) NOT NULL REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    relation_type character varying(32) NOT NULL,
    strength character varying(16) NOT NULL DEFAULT 'PRIMARY',
    notes text,
    active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT uq_partner_player_relation UNIQUE (from_player_id, to_player_id, relation_type),
    CONSTRAINT chk_partner_player_relation_diff CHECK (from_player_id <> to_player_id)
);

CREATE INDEX IF NOT EXISTS idx_partner_player_rel_from ON partner_player_relations (from_player_id, relation_type);

CREATE TABLE IF NOT EXISTS partner_market_presence (
    id character varying(36) NOT NULL PRIMARY KEY,
    ecosystem_player_id character varying(36) NOT NULL REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    country character varying(2) NOT NULL,
    region_code character varying(16),
    service_level character varying(20) NOT NULL DEFAULT 'FULL',
    locker_density character varying(16) NOT NULL DEFAULT 'MEDIUM',
    active boolean NOT NULL DEFAULT true,
    launched_at date,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT uq_partner_market_presence UNIQUE (ecosystem_player_id, country, region_code)
);

CREATE INDEX IF NOT EXISTS idx_partner_market_presence_country ON partner_market_presence (country, active);
