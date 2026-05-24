-- Metadados mundiais: aliases, cobertura geográfica, blueprints de integração, tipos de relação

CREATE TABLE IF NOT EXISTS finance_relation_types (
    code character varying(40) NOT NULL PRIMARY KEY,
    name character varying(120) NOT NULL,
    description text
);

CREATE TABLE IF NOT EXISTS finance_player_aliases (
    alias_code character varying(48) NOT NULL PRIMARY KEY,
    catalog_code character varying(48) NOT NULL,
    source character varying(40) DEFAULT 'LEGACY' NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_fpa_catalog ON finance_player_aliases (catalog_code);

CREATE TABLE IF NOT EXISTS finance_player_country_coverage (
    id character varying(36) NOT NULL PRIMARY KEY,
    catalog_code character varying(48) NOT NULL,
    country_code character varying(2) NOT NULL,
    locker_service boolean DEFAULT false NOT NULL,
    pudo_service boolean DEFAULT false NOT NULL,
    marketplace_channel boolean DEFAULT false NOT NULL,
    food_pickup boolean DEFAULT false NOT NULL,
    UNIQUE (catalog_code, country_code)
);

CREATE INDEX IF NOT EXISTS ix_fpcc_country ON finance_player_country_coverage (country_code, catalog_code);

CREATE TABLE IF NOT EXISTS finance_integration_blueprints (
    code character varying(40) NOT NULL PRIMARY KEY,
    name character varying(160) NOT NULL,
    target_segments_json text DEFAULT '[]' NOT NULL,
    auth_type character varying(30) DEFAULT 'API_KEY' NOT NULL,
    primary_capability character varying(40) NOT NULL,
    webhook_events_json text DEFAULT '[]' NOT NULL,
    reference_players_json text DEFAULT '[]' NOT NULL,
    docs_hint text,
    sort_order integer DEFAULT 100 NOT NULL
);
