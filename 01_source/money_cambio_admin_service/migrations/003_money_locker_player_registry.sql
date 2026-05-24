-- Players locker/marketplace/carrier — alinhamento Money ↔ Finance ↔ Fiscal

CREATE TABLE IF NOT EXISTS money_locker_player_registry (
    id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    segment VARCHAR(32) NOT NULL,
    primary_country CHAR(2) NOT NULL,
    regions_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    default_settlement_currency CHAR(3) NOT NULL,
    finance_catalog_code VARCHAR(48),
    fiscal_corridor_code VARCHAR(48),
    cambio_corridor_code VARCHAR(48),
    notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_mlpr_segment ON money_locker_player_registry (segment, is_active);
CREATE INDEX IF NOT EXISTS ix_mlpr_finance ON money_locker_player_registry (finance_catalog_code);
CREATE INDEX IF NOT EXISTS ix_mlpr_fiscal ON money_locker_player_registry (fiscal_corridor_code);
