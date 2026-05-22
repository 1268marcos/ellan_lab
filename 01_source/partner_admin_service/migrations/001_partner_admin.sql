-- DDL alinhado ao schema public (complete_schema_20260521_c.sql)
-- Tabelas gerenciadas pelo partner_admin_service

CREATE TABLE IF NOT EXISTS ecommerce_partners (
    id character varying(36) NOT NULL PRIMARY KEY,
    name character varying(128) NOT NULL,
    code character varying(32) NOT NULL UNIQUE,
    integration_type character varying(30) NOT NULL,
    api_base_url character varying(500),
    credentials_secret_ref character varying(255),
    webhook_secret_ref character varying(255),
    revenue_share_pct numeric(6,4),
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    sla_pickup_hours integer DEFAULT 72 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    country character varying(2) DEFAULT 'BR' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(30) DEFAULT 'DRAFT' NOT NULL,
    legal_name character varying(140),
    tax_id character varying(32),
    tier character varying(20) DEFAULT 'STANDARD',
    support_email character varying(128),
    support_phone character varying(32)
);

CREATE TABLE IF NOT EXISTS logistics_partners (
    id character varying(36) NOT NULL PRIMARY KEY,
    name character varying(128) NOT NULL,
    code character varying(32) NOT NULL UNIQUE,
    integration_type character varying(30) NOT NULL,
    api_base_url character varying(500),
    tracking_url_template character varying(500),
    auth_type character varying(20),
    credentials_secret_ref character varying(255),
    default_sla_hours integer DEFAULT 72 NOT NULL,
    reminder_hours_before integer DEFAULT 24 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    country character varying(2) DEFAULT 'BR' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id character varying(36) NOT NULL PRIMARY KEY,
    full_name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(32),
    password_hash character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    email_verified boolean NOT NULL,
    phone_verified boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users (email);

CREATE TABLE IF NOT EXISTS user_roles (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL PRIMARY KEY,
    user_id character varying(36) NOT NULL REFERENCES users(id),
    role character varying(40) NOT NULL,
    scope_type character varying(40) DEFAULT 'GLOBAL',
    scope_id character varying(36),
    is_active boolean DEFAULT true NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_role_active
    ON user_roles (user_id, role, scope_type, scope_id) WHERE (revoked_at IS NULL);

CREATE TABLE IF NOT EXISTS partner_webhook_endpoints (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    url character varying(500) NOT NULL,
    secret_hash character varying(128) NOT NULL,
    secret_key character varying(256),
    events_json text DEFAULT '["*"]' NOT NULL,
    api_version character varying(10) DEFAULT 'v1' NOT NULL,
    retry_policy text DEFAULT '{}' NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_api_keys (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    key_prefix character varying(16) NOT NULL,
    key_hash character varying(128) NOT NULL,
    label character varying(64),
    scopes_json text DEFAULT '[]' NOT NULL,
    expires_at timestamp with time zone,
    last_used_at timestamp with time zone,
    revoked_at timestamp with time zone,
    created_by character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_contacts (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    contact_type character varying(20) NOT NULL,
    name character varying(128) NOT NULL,
    email character varying(128),
    phone character varying(32),
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS tenant_fiscal_config (
    tenant_id character varying(100) NOT NULL PRIMARY KEY,
    cnpj character varying(18) NOT NULL,
    razao_social character varying(140) NOT NULL,
    ie character varying(20),
    regime character varying(20) NOT NULL,
    crt character(1) NOT NULL,
    cert_a1_ref character varying(255),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    brand_config jsonb DEFAULT '{}'::jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS custom_domains (
    id character varying(36) NOT NULL PRIMARY KEY,
    tenant_id character varying(100) NOT NULL,
    domain character varying(255) NOT NULL UNIQUE,
    verified boolean DEFAULT false,
    ssl_cert_ref character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    verified_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS tenant_partner_links (
    id character varying(36) NOT NULL PRIMARY KEY,
    tenant_id character varying(100) NOT NULL,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
