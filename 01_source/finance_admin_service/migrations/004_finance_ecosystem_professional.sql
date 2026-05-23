-- Ecossistema FINANCE profissional: segmentos, capacidades de integração, relações entre players

CREATE TABLE IF NOT EXISTS finance_ecosystem_segments (
    code character varying(40) NOT NULL PRIMARY KEY,
    name character varying(120) NOT NULL,
    description text,
    sort_order integer DEFAULT 100 NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_player_capabilities (
    id integer PRIMARY KEY AUTOINCREMENT,
    catalog_code character varying(48) NOT NULL,
    capability_code character varying(40) NOT NULL,
    protocol character varying(20) DEFAULT 'REST' NOT NULL,
    direction character varying(10) DEFAULT 'OUTBOUND' NOT NULL,
    UNIQUE (catalog_code, capability_code)
);

CREATE TABLE IF NOT EXISTS finance_player_relations (
    id character varying(36) NOT NULL PRIMARY KEY,
    from_catalog_code character varying(48) NOT NULL,
    to_catalog_code character varying(48) NOT NULL,
    relation_type character varying(40) NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (from_catalog_code, to_catalog_code, relation_type)
);

-- Extensão do catálogo principal
ALTER TABLE finance_locker_network_catalog ADD COLUMN segment_code character varying(40);
ALTER TABLE finance_locker_network_catalog ADD COLUMN supports_collection_points boolean DEFAULT false NOT NULL;
ALTER TABLE finance_locker_network_catalog ADD COLUMN supports_food_delivery boolean DEFAULT false NOT NULL;
ALTER TABLE finance_locker_network_catalog ADD COLUMN integration_modes_json text DEFAULT '[]' NOT NULL;
