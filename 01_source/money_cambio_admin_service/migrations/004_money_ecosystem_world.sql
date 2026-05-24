-- Ecossistema mundial Money: segmentos, relações entre players, integração Finance/Fiscal

CREATE TABLE IF NOT EXISTS money_ecosystem_segment (
    code VARCHAR(32) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 100 NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL
);

CREATE TABLE IF NOT EXISTS money_player_relation (
    id VARCHAR(36) PRIMARY KEY,
    from_player_code VARCHAR(48) NOT NULL,
    to_player_code VARCHAR(48) NOT NULL,
    relation_type VARCHAR(32) NOT NULL,
    notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE (from_player_code, to_player_code, relation_type)
);

CREATE INDEX IF NOT EXISTS ix_mpr_from ON money_player_relation (from_player_code);
CREATE INDEX IF NOT EXISTS ix_mpr_to ON money_player_relation (to_player_code);
CREATE INDEX IF NOT EXISTS ix_mpr_type ON money_player_relation (relation_type);
