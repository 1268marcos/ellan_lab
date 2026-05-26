CREATE TABLE IF NOT EXISTS capability_feature_flag (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    scope VARCHAR(32) NOT NULL DEFAULT 'GLOBAL',
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS capability_corridor (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(48) NOT NULL UNIQUE,
    from_region_code VARCHAR(20) NOT NULL,
    to_region_code VARCHAR(20) NOT NULL,
    channel_code VARCHAR(50) NOT NULL,
    name VARCHAR(160) NOT NULL,
    default_currency VARCHAR(10) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS capability_profile_readiness (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL UNIQUE REFERENCES capability_profile(id) ON DELETE CASCADE,
    profile_code VARCHAR(160) NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    grade VARCHAR(2) NOT NULL DEFAULT 'F',
    dimensions_json JSONB NOT NULL DEFAULT '{}',
    gaps_json JSONB NOT NULL DEFAULT '[]',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_cap_profile_readiness_code ON capability_profile_readiness(profile_code);

CREATE TABLE IF NOT EXISTS capability_insight (
    id VARCHAR(36) PRIMARY KEY,
    severity VARCHAR(16) NOT NULL DEFAULT 'INFO',
    category VARCHAR(32) NOT NULL,
    title VARCHAR(200) NOT NULL,
    detail TEXT,
    entity_type VARCHAR(48),
    entity_id VARCHAR(64),
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    recommendation TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_cap_insight_status ON capability_insight(status);
CREATE INDEX IF NOT EXISTS ix_cap_insight_category ON capability_insight(category);
