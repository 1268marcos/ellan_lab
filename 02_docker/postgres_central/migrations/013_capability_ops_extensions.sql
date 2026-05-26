-- Source: 01_source/capability_admin_service/migrations/006_capability_ops_extensions.sql

CREATE TABLE IF NOT EXISTS capability_profile_template (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    description TEXT,
    region_code VARCHAR(20),
    channel_code VARCHAR(50),
    context_code VARCHAR(80),
    currency VARCHAR(10) NOT NULL DEFAULT 'BRL',
    template_json JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS capability_ops_job (
    id VARCHAR(36) PRIMARY KEY,
    job_type VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    actor VARCHAR(120),
    request_json JSONB NOT NULL DEFAULT '{}',
    result_json JSONB NOT NULL DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_cap_ops_job_type ON capability_ops_job(job_type);
CREATE INDEX IF NOT EXISTS ix_cap_ops_job_created ON capability_ops_job(created_at DESC);
