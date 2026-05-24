CREATE TABLE IF NOT EXISTS payment_player_relation (
    id VARCHAR(36) PRIMARY KEY,
    from_player_code VARCHAR(64) NOT NULL,
    to_player_code VARCHAR(64) NOT NULL,
    relation_type VARCHAR(32) NOT NULL,
    notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ppr_from ON payment_player_relation (from_player_code);
CREATE INDEX IF NOT EXISTS ix_ppr_to ON payment_player_relation (to_player_code);
CREATE INDEX IF NOT EXISTS ix_ppr_type ON payment_player_relation (relation_type);
