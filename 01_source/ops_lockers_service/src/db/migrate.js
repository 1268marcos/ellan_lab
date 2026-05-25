import { pool } from '../lib/db.js'

const MIGRATION_SQL = `
CREATE TABLE IF NOT EXISTS locker_maintenance_tickets (
  id VARCHAR(36) PRIMARY KEY DEFAULT (gen_random_uuid()::text),
  locker_id VARCHAR(36) NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
  priority VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
  assigned_to VARCHAR(100),
  created_by VARCHAR(100),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at TIMESTAMPTZ,
  CONSTRAINT ck_lmt_status CHECK (status IN ('OPEN','IN_PROGRESS','WAITING_PARTS','RESOLVED','CANCELLED')),
  CONSTRAINT ck_lmt_priority CHECK (priority IN ('LOW','MEDIUM','HIGH','CRITICAL'))
);
CREATE INDEX IF NOT EXISTS ix_lmt_locker_status ON locker_maintenance_tickets (locker_id, status);
CREATE INDEX IF NOT EXISTS ix_lmt_updated ON locker_maintenance_tickets (updated_at DESC);
`

export async function ensureSchema() {
  await pool.query(MIGRATION_SQL)
}
