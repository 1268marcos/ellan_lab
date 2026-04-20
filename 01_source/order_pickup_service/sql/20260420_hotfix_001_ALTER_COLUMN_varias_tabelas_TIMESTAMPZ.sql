-- Colar no Alembic ou rodar direto em dev antes do upgrade

-- Tabela pickups
ALTER TABLE pickups
    ALTER COLUMN activated_at     TYPE TIMESTAMPTZ USING activated_at AT TIME ZONE 'UTC',
    ALTER COLUMN ready_at         TYPE TIMESTAMPTZ USING ready_at     AT TIME ZONE 'UTC',
    ALTER COLUMN expires_at       TYPE TIMESTAMPTZ USING expires_at   AT TIME ZONE 'UTC',
    ALTER COLUMN door_opened_at   TYPE TIMESTAMPTZ USING door_opened_at  AT TIME ZONE 'UTC',
    ALTER COLUMN item_removed_at  TYPE TIMESTAMPTZ USING item_removed_at AT TIME ZONE 'UTC',
    ALTER COLUMN door_closed_at   TYPE TIMESTAMPTZ USING door_closed_at  AT TIME ZONE 'UTC',
    ALTER COLUMN redeemed_at      TYPE TIMESTAMPTZ USING redeemed_at     AT TIME ZONE 'UTC',
    ALTER COLUMN expired_at       TYPE TIMESTAMPTZ USING expired_at      AT TIME ZONE 'UTC',
    ALTER COLUMN cancelled_at     TYPE TIMESTAMPTZ USING cancelled_at    AT TIME ZONE 'UTC',
    ALTER COLUMN created_at       TYPE TIMESTAMPTZ USING created_at      AT TIME ZONE 'UTC',
    ALTER COLUMN updated_at       TYPE TIMESTAMPTZ USING updated_at      AT TIME ZONE 'UTC';

-- Tabela orders
ALTER TABLE orders
    ALTER COLUMN paid_at              TYPE TIMESTAMPTZ USING paid_at             AT TIME ZONE 'UTC',
    ALTER COLUMN pickup_deadline_at   TYPE TIMESTAMPTZ USING pickup_deadline_at  AT TIME ZONE 'UTC',
    ALTER COLUMN picked_up_at         TYPE TIMESTAMPTZ USING picked_up_at        AT TIME ZONE 'UTC',
    ALTER COLUMN payment_updated_at   TYPE TIMESTAMPTZ USING payment_updated_at  AT TIME ZONE 'UTC',
    ALTER COLUMN cancelled_at         TYPE TIMESTAMPTZ USING cancelled_at        AT TIME ZONE 'UTC',
    ALTER COLUMN refunded_at          TYPE TIMESTAMPTZ USING refunded_at         AT TIME ZONE 'UTC',
    ALTER COLUMN allocation_expires_at TYPE TIMESTAMPTZ USING allocation_expires_at AT TIME ZONE 'UTC',
    ALTER COLUMN created_at           TYPE TIMESTAMPTZ USING created_at          AT TIME ZONE 'UTC',
    ALTER COLUMN updated_at           TYPE TIMESTAMPTZ USING updated_at          AT TIME ZONE 'UTC';

-- Tabela pickup_tokens
ALTER TABLE pickup_tokens
    ALTER COLUMN expires_at  TYPE TIMESTAMPTZ USING expires_at AT TIME ZONE 'UTC',
    ALTER COLUMN used_at     TYPE TIMESTAMPTZ USING used_at    AT TIME ZONE 'UTC',
    ALTER COLUMN created_at  TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- Tabela domain_event_outbox
ALTER TABLE domain_event_outbox
    ALTER COLUMN occurred_at  TYPE TIMESTAMPTZ USING occurred_at  AT TIME ZONE 'UTC',
    ALTER COLUMN published_at TYPE TIMESTAMPTZ USING published_at AT TIME ZONE 'UTC',
    ALTER COLUMN created_at   TYPE TIMESTAMPTZ USING created_at   AT TIME ZONE 'UTC',
    ALTER COLUMN updated_at   TYPE TIMESTAMPTZ USING updated_at   AT TIME ZONE 'UTC';