-- inventory_sync_queue + worker_dead_letter_queue (Node postgres_workers)

CREATE TABLE IF NOT EXISTS inventory_sync_queue (
    id VARCHAR(36) PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    locker_id VARCHAR(64),
    marketplace VARCHAR(32) NOT NULL,
    operation VARCHAR(32) NOT NULL DEFAULT 'UPSERT_STOCK',
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    quantity_available INTEGER NOT NULL DEFAULT 0,
    payload_json TEXT NOT NULL DEFAULT '{}',
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 5,
    next_retry_at TIMESTAMPTZ,
    processing_started_at TIMESTAMPTZ,
    last_error TEXT,
    synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_isq_marketplace CHECK (
        marketplace IN ('SHOPEE', 'MAGALU', 'MERCADO_LIVRE')
    ),
    CONSTRAINT ck_isq_status CHECK (
        status IN ('PENDING', 'PROCESSING', 'SYNCED', 'FAILED', 'DEAD_LETTER')
    )
);

CREATE INDEX IF NOT EXISTS ix_inventory_sync_queue_pending
    ON inventory_sync_queue (created_at)
    WHERE status IN ('PENDING', 'PROCESSING');

CREATE INDEX IF NOT EXISTS ix_inventory_sync_queue_marketplace_status
    ON inventory_sync_queue (marketplace, status, next_retry_at);

CREATE TABLE IF NOT EXISTS worker_dead_letter_queue (
    id VARCHAR(36) PRIMARY KEY,
    worker_name VARCHAR(64) NOT NULL,
    source_table VARCHAR(64) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    dead_lettered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_worker_dlq_worker_created
    ON worker_dead_letter_queue (worker_name, dead_lettered_at DESC);

CREATE INDEX IF NOT EXISTS ix_worker_dlq_source
    ON worker_dead_letter_queue (source_table, source_id);
