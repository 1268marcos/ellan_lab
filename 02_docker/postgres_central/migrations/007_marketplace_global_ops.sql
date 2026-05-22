-- Camada Global OPS Marketplace: certificações, corredores, prontidão cross-border

CREATE TABLE IF NOT EXISTS marketplace_player_certifications (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    channel_partner_id VARCHAR(36) NOT NULL,
    partner_code VARCHAR(48) NOT NULL,
    certification_type VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'VALID',
    issuer VARCHAR(120),
    issued_at DATE,
    expires_at DATE,
    evidence_url VARCHAR(500),
    scope_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    FOREIGN KEY (channel_partner_id) REFERENCES marketplace_channel_partners(id) ON DELETE CASCADE,
    UNIQUE (channel_partner_id, certification_type)
);

CREATE INDEX IF NOT EXISTS ix_mkt_cert_code ON marketplace_player_certifications(partner_code, status);

CREATE TABLE IF NOT EXISTS marketplace_global_corridors (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    corridor_code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    origin_country VARCHAR(2) NOT NULL,
    dest_country VARCHAR(2) NOT NULL,
    primary_channel_partner_id VARCHAR(36) NOT NULL,
    primary_partner_code VARCHAR(48) NOT NULL,
    fallback_channel_partner_id VARCHAR(36),
    fallback_partner_code VARCHAR(48),
    handoff_type VARCHAR(32) NOT NULL DEFAULT 'LOCKER_TO_LOCKER',
    service_level VARCHAR(20) NOT NULL DEFAULT 'STANDARD',
    transit_days_min INTEGER NOT NULL DEFAULT 1,
    transit_days_max INTEGER NOT NULL DEFAULT 5,
    supports_returns BOOLEAN NOT NULL DEFAULT false,
    active BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER NOT NULL DEFAULT 100,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    FOREIGN KEY (primary_channel_partner_id) REFERENCES marketplace_channel_partners(id),
    FOREIGN KEY (fallback_channel_partner_id) REFERENCES marketplace_channel_partners(id)
);

CREATE INDEX IF NOT EXISTS ix_mkt_corridor_route ON marketplace_global_corridors(origin_country, dest_country, active);

CREATE TABLE IF NOT EXISTS marketplace_corridor_player_steps (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    corridor_id VARCHAR(36) NOT NULL,
    step_order INTEGER NOT NULL DEFAULT 1,
    channel_partner_id VARCHAR(36) NOT NULL,
    partner_code VARCHAR(48) NOT NULL,
    step_role VARCHAR(32) NOT NULL DEFAULT 'HANDOFF',
    notes TEXT,
    FOREIGN KEY (corridor_id) REFERENCES marketplace_global_corridors(id) ON DELETE CASCADE,
    FOREIGN KEY (channel_partner_id) REFERENCES marketplace_channel_partners(id),
    UNIQUE (corridor_id, step_order)
);

CREATE INDEX IF NOT EXISTS ix_mkt_corridor_steps ON marketplace_corridor_player_steps(corridor_id, step_order);
