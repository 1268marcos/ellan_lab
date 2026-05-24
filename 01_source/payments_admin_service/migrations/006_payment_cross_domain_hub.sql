-- Hub PAYMENT ↔ outros domínios: registry, referências externas, obrigações, eventos

CREATE TABLE IF NOT EXISTS payment_domain_registry (
    code VARCHAR(40) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    ops_base_path VARCHAR(255),
    api_service_name VARCHAR(80),
    is_active BOOLEAN DEFAULT true NOT NULL,
    sort_order INTEGER DEFAULT 100 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_external_reference (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64),
    payment_entity_type VARCHAR(40) NOT NULL,
    payment_entity_id VARCHAR(64) NOT NULL,
    external_domain VARCHAR(40) NOT NULL,
    external_entity_type VARCHAR(60) NOT NULL,
    external_entity_id VARCHAR(120) NOT NULL,
    link_role VARCHAR(40) DEFAULT 'PRIMARY' NOT NULL,
    sync_status VARCHAR(20) DEFAULT 'LINKED' NOT NULL,
    last_synced_at TIMESTAMPTZ,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT uq_per_ext_unique UNIQUE (
        payment_entity_type,
        payment_entity_id,
        external_domain,
        external_entity_type,
        external_entity_id
    )
);
CREATE INDEX IF NOT EXISTS ix_per_order ON payment_external_reference (order_id);
CREATE INDEX IF NOT EXISTS ix_per_domain ON payment_external_reference (external_domain);

CREATE TABLE IF NOT EXISTS payment_domain_obligation (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    domain_code VARCHAR(40) NOT NULL,
    obligation_type VARCHAR(60) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    priority INTEGER DEFAULT 50 NOT NULL,
    blocking_payment BOOLEAN DEFAULT false NOT NULL,
    due_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    external_ref_id VARCHAR(120),
    notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pdo_order ON payment_domain_obligation (order_id);
CREATE INDEX IF NOT EXISTS ix_pdo_status ON payment_domain_obligation (status);

CREATE TABLE IF NOT EXISTS payment_cross_domain_event (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64),
    event_type VARCHAR(80) NOT NULL,
    source_domain VARCHAR(40) DEFAULT 'PAYMENT' NOT NULL,
    target_domains_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    payload_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    published_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pcde_order ON payment_cross_domain_event (order_id);
CREATE INDEX IF NOT EXISTS ix_pcde_status ON payment_cross_domain_event (status);
