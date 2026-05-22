-- Partner OPS: catálogo ecossistema + vínculos (Postgres central locker_central)

CREATE TABLE IF NOT EXISTS partner_ecosystem_players (
    id character varying(36) NOT NULL PRIMARY KEY,
    code character varying(48) NOT NULL UNIQUE,
    name character varying(160) NOT NULL,
    player_role character varying(40) NOT NULL,
    parent_group character varying(40) NOT NULL,
    country character varying(2) NOT NULL,
    regions_json text NOT NULL DEFAULT '[]',
    supports_lockers boolean NOT NULL DEFAULT false,
    supports_marketplace boolean NOT NULL DEFAULT false,
    integration_mode character varying(40) NOT NULL DEFAULT 'DIRECT_API',
    marketplace_channel_id character varying(36),
    marketplace_channel_code character varying(48),
    locker_operator_ref character varying(48),
    ecommerce_partner_code character varying(48),
    api_docs_url character varying(500),
    notes text,
    global_tier character varying(20) NOT NULL DEFAULT 'REGIONAL',
    sort_order integer NOT NULL DEFAULT 100,
    active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_partner_ecosystem_parent ON partner_ecosystem_players (parent_group);
CREATE INDEX IF NOT EXISTS idx_partner_ecosystem_tier ON partner_ecosystem_players (global_tier);

CREATE TABLE IF NOT EXISTS partner_ecosystem_links (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    ecosystem_player_id character varying(36) NOT NULL REFERENCES partner_ecosystem_players(id),
    link_role character varying(40) NOT NULL DEFAULT 'CHANNEL',
    is_primary boolean NOT NULL DEFAULT false,
    integration_status character varying(30) NOT NULL DEFAULT 'PLANNED',
    notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT uq_partner_ecosystem_link UNIQUE (partner_id, partner_type, ecosystem_player_id)
);

CREATE INDEX IF NOT EXISTS idx_partner_ecosystem_links_partner ON partner_ecosystem_links (partner_id, partner_type);
