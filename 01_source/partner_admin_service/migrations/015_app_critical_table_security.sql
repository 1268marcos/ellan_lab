-- Camada de aplicacao: users, privacy_consents, audit_logs (sem RLS nativo)

CREATE TABLE IF NOT EXISTS app_critical_table_registry (
    table_name character varying(64) NOT NULL PRIMARY KEY,
    schema_name character varying(32) DEFAULT 'public' NOT NULL,
    rls_enabled boolean DEFAULT false NOT NULL,
    enforcement_layer character varying(24) DEFAULT 'APPLICATION' NOT NULL,
    description character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS app_critical_table_policy (
    id character varying(36) NOT NULL PRIMARY KEY,
    table_name character varying(64) NOT NULL REFERENCES app_critical_table_registry(table_name) ON DELETE CASCADE,
    operation character varying(16) NOT NULL,
    role character varying(40) NOT NULL,
    scope_type character varying(24) DEFAULT 'GLOBAL' NOT NULL,
    allowed boolean DEFAULT true NOT NULL,
    field_mask_json text,
    priority integer DEFAULT 100 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (table_name, operation, role, scope_type)
);

CREATE TABLE IF NOT EXISTS app_critical_table_access_log (
    id character varying(36) NOT NULL PRIMARY KEY,
    table_name character varying(64) NOT NULL,
    operation character varying(16) NOT NULL,
    actor_id character varying(36),
    actor_roles_json text,
    target_user_id character varying(36),
    row_id character varying(36),
    decision character varying(16) NOT NULL,
    reason character varying(128),
    service_name character varying(64),
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_app_crit_access_table_time ON app_critical_table_access_log (table_name, occurred_at DESC);
CREATE INDEX IF NOT EXISTS ix_app_crit_policy_table_op ON app_critical_table_policy (table_name, operation, is_active);

ALTER TABLE users ADD COLUMN IF NOT EXISTS app_security_class character varying(24) DEFAULT 'PII_CRITICAL' NOT NULL;
ALTER TABLE privacy_consents ADD COLUMN IF NOT EXISTS recorded_by_service character varying(64);
ALTER TABLE privacy_consents ADD COLUMN IF NOT EXISTS access_policy_version integer DEFAULT 1 NOT NULL;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS source_service character varying(64);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS immutable boolean DEFAULT true NOT NULL;

INSERT INTO app_critical_table_registry (table_name, description) VALUES
    ('users', 'PII critico — enforcement APPLICATION'),
    ('privacy_consents', 'LGPD/GDPR consents — enforcement APPLICATION'),
    ('audit_logs', 'Trilha imutavel — enforcement APPLICATION')
ON CONFLICT (table_name) DO NOTHING;

INSERT INTO app_critical_table_policy (id, table_name, operation, role, scope_type, allowed, priority) VALUES
    ('pol-u-sel-admin', 'users', 'SELECT', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-u-sel-audit', 'users', 'SELECT', 'auditoria', 'GLOBAL', true, 20),
    ('pol-u-sel-sup', 'users', 'SELECT', 'suporte', 'GLOBAL', true, 30),
    ('pol-u-sel-self', 'users', 'SELECT', 'usuario_comum', 'SELF', true, 40),
    ('pol-u-ins-admin', 'users', 'INSERT', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-u-ins-sys', 'users', 'INSERT', 'SYSTEM', 'GLOBAL', true, 15),
    ('pol-u-upd-admin', 'users', 'UPDATE', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-u-upd-self', 'users', 'UPDATE', 'usuario_comum', 'SELF', true, 40),
    ('pol-u-del-admin', 'users', 'DELETE', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-pc-sel-admin', 'privacy_consents', 'SELECT', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-pc-sel-audit', 'privacy_consents', 'SELECT', 'auditoria', 'GLOBAL', true, 20),
    ('pol-pc-sel-self', 'privacy_consents', 'SELECT', 'usuario_comum', 'SELF', true, 30),
    ('pol-pc-ins-admin', 'privacy_consents', 'INSERT', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-pc-ins-sys', 'privacy_consents', 'INSERT', 'SYSTEM', 'GLOBAL', true, 15),
    ('pol-pc-ins-self', 'privacy_consents', 'INSERT', 'usuario_comum', 'SELF', true, 20),
    ('pol-pc-upd-admin', 'privacy_consents', 'UPDATE', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-pc-del-admin', 'privacy_consents', 'DELETE', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-al-sel-admin', 'audit_logs', 'SELECT', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-al-sel-audit', 'audit_logs', 'SELECT', 'auditoria', 'GLOBAL', true, 20),
    ('pol-al-ins-admin', 'audit_logs', 'INSERT', 'admin_operacao', 'GLOBAL', true, 10),
    ('pol-al-ins-audit', 'audit_logs', 'INSERT', 'auditoria', 'GLOBAL', true, 20),
    ('pol-al-ins-sup', 'audit_logs', 'INSERT', 'suporte', 'GLOBAL', true, 30),
    ('pol-al-ins-sys', 'audit_logs', 'INSERT', 'SYSTEM', 'GLOBAL', true, 5),
    ('pol-al-upd-deny', 'audit_logs', 'UPDATE', 'admin_operacao', 'GLOBAL', false, 100),
    ('pol-al-del-deny', 'audit_logs', 'DELETE', 'admin_operacao', 'GLOBAL', false, 100)
ON CONFLICT (table_name, operation, role, scope_type) DO NOTHING;
