ALTER TABLE domain_event_outbox
ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE domain_event_outbox
ADD COLUMN next_retry_at TIMESTAMP NULL;

ALTER TABLE domain_event_outbox
ADD COLUMN processing_started_at TIMESTAMP NULL;