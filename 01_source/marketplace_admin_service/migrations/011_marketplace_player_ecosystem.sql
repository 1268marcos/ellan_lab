-- Ecossistema mundial: segmentos, corredores, relações entre players, planos de integração seller

CREATE TABLE IF NOT EXISTS marketplace_player_segments (
    code character varying(32) NOT NULL PRIMARY KEY,
    name character varying(128) NOT NULL,
    parent_group character varying(32) NOT NULL,
    description text,
    default_integration_mode character varying(32) DEFAULT 'DIRECT_API',
    sort_order integer DEFAULT 100 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS marketplace_channel_partner_segments (
    id character varying(36) NOT NULL PRIMARY KEY,
    channel_partner_id character varying(36) NOT NULL,
    segment_code character varying(32) NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_partner_segment UNIQUE (channel_partner_id, segment_code)
);

CREATE INDEX IF NOT EXISTS ix_mcps_partner ON marketplace_channel_partner_segments (channel_partner_id);
CREATE INDEX IF NOT EXISTS ix_mcps_segment ON marketplace_channel_partner_segments (segment_code);

CREATE TABLE IF NOT EXISTS marketplace_player_relationships (
    id character varying(36) NOT NULL PRIMARY KEY,
    from_partner_id character varying(36) NOT NULL,
    to_partner_id character varying(36) NOT NULL,
    relationship_type character varying(32) NOT NULL,
    corridor_code character varying(48),
    notes text,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_player_rel UNIQUE (from_partner_id, to_partner_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS ix_mpr_from ON marketplace_player_relationships (from_partner_id, relationship_type);
CREATE INDEX IF NOT EXISTS ix_mpr_to ON marketplace_player_relationships (to_partner_id);

CREATE TABLE IF NOT EXISTS marketplace_corridors (
    code character varying(48) NOT NULL PRIMARY KEY,
    name character varying(128) NOT NULL,
    origin_country character varying(2) NOT NULL,
    destination_country character varying(2) NOT NULL,
    corridor_type character varying(24) DEFAULT 'DOMESTIC' NOT NULL,
    currency character varying(8) DEFAULT 'EUR',
    active boolean DEFAULT true NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS marketplace_corridor_players (
    id character varying(36) NOT NULL PRIMARY KEY,
    corridor_code character varying(48) NOT NULL,
    channel_partner_id character varying(36) NOT NULL,
    player_role_in_corridor character varying(32) NOT NULL,
    priority integer DEFAULT 100 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_corridor_player UNIQUE (corridor_code, channel_partner_id, player_role_in_corridor)
);

CREATE INDEX IF NOT EXISTS ix_mcp_corridor ON marketplace_corridor_players (corridor_code, active);

CREATE TABLE IF NOT EXISTS seller_player_integration_plans (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    channel_partner_id character varying(36) NOT NULL,
    integration_path character varying(32) NOT NULL,
    status character varying(20) DEFAULT 'PLANNED' NOT NULL,
    target_go_live date,
    primary_capability character varying(40),
    via_partner_id character varying(36),
    corridor_code character varying(48),
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_player_plan UNIQUE (seller_id, channel_partner_id, integration_path)
);

CREATE INDEX IF NOT EXISTS ix_spip_seller ON seller_player_integration_plans (seller_id, status);
CREATE INDEX IF NOT EXISTS ix_spip_partner ON seller_player_integration_plans (channel_partner_id, status);
