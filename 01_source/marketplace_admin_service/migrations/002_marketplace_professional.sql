-- Extensao profissional do dominio marketplace (admin)

CREATE TABLE IF NOT EXISTS marketplace_categories (
    id character varying(36) NOT NULL PRIMARY KEY,
    code character varying(32) NOT NULL UNIQUE,
    name character varying(128) NOT NULL,
    parent_id character varying(36),
    active boolean DEFAULT true NOT NULL,
    sort_order integer DEFAULT 100 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_category_links (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    category_id character varying(36) NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_category UNIQUE (seller_id, category_id)
);

CREATE TABLE IF NOT EXISTS seller_contacts (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    contact_type character varying(20) NOT NULL,
    name character varying(128) NOT NULL,
    email character varying(128),
    phone character varying(32),
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_payout_accounts (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    account_type character varying(20) DEFAULT 'PIX' NOT NULL,
    label character varying(64),
    pix_key character varying(128),
    bank_code character varying(10),
    branch character varying(10),
    account_number character varying(20),
    holder_name character varying(140) NOT NULL,
    holder_tax_id character varying(32),
    is_default boolean DEFAULT false NOT NULL,
    verified boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_settlement_batches (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    commission_count integer DEFAULT 0 NOT NULL,
    gross_net_cents bigint DEFAULT 0 NOT NULL,
    fees_cents bigint DEFAULT 0 NOT NULL,
    net_payout_cents bigint DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'DRAFT' NOT NULL,
    settled_at timestamp with time zone,
    settlement_ref character varying(128),
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_settlement_items (
    id character varying(36) NOT NULL PRIMARY KEY,
    batch_id character varying(36) NOT NULL,
    commission_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    net_to_seller_cents integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_kyc_documents (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    doc_type character varying(30) NOT NULL,
    status character varying(20) DEFAULT 'PENDING' NOT NULL,
    file_ref character varying(255),
    notes text,
    verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_commission_disputes (
    id character varying(36) NOT NULL PRIMARY KEY,
    commission_id character varying(36) NOT NULL,
    seller_id character varying(36) NOT NULL,
    reason text NOT NULL,
    status character varying(20) DEFAULT 'OPEN' NOT NULL,
    resolution_notes text,
    opened_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_seller_category_links_seller ON seller_category_links (seller_id);
CREATE INDEX IF NOT EXISTS ix_seller_contacts_seller ON seller_contacts (seller_id);
CREATE INDEX IF NOT EXISTS ix_seller_payout_accounts_seller ON seller_payout_accounts (seller_id, is_default);
CREATE INDEX IF NOT EXISTS ix_seller_settlement_batches_seller ON seller_settlement_batches (seller_id, status);
CREATE INDEX IF NOT EXISTS ix_seller_settlement_items_batch ON seller_settlement_items (batch_id);
CREATE INDEX IF NOT EXISTS ix_seller_kyc_documents_seller ON seller_kyc_documents (seller_id, status);
CREATE INDEX IF NOT EXISTS ix_seller_commission_disputes_status ON seller_commission_disputes (status, seller_id);
