-- Ligação canónica FINANCE ↔ ML Admin

ALTER TABLE ml_locker_network_players ADD COLUMN IF NOT EXISTS finance_catalog_code character varying(48);
CREATE INDEX IF NOT EXISTS ix_ml_locker_finance_code ON ml_locker_network_players (finance_catalog_code);
