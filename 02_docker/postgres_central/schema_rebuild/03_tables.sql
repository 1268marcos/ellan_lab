-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 03_tables.sql
-- Execução: ver README.md e run_rebuild.sh

--
-- Name: ellanlab_revenue_recognition; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ellanlab_revenue_recognition (
    id bigint NOT NULL,
    recognition_date date NOT NULL,
    partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    source_type character varying(40) NOT NULL,
    source_id character varying(64) NOT NULL,
    recognition_rule character varying(40) DEFAULT 'ACCRUAL_DAILY'::character varying NOT NULL,
    recognized_amount_cents bigint NOT NULL,
    deferred_amount_cents bigint DEFAULT 0 NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    dedupe_key character varying(180),
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_err_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_err_rule CHECK (((recognition_rule)::text = ANY ((ARRAY['ACCRUAL_DAILY'::character varying, 'CASH_BASIS'::character varying, 'MANUAL'::character varying])::text[]))),
    CONSTRAINT ck_err_source_type CHECK (((source_type)::text = ANY ((ARRAY['PARTNER_INVOICE'::character varying, 'PARTNER_CYCLE'::character varying, 'MANUAL_ADJUSTMENT'::character varying])::text[])))
);


ALTER TABLE public.ellanlab_revenue_recognition OWNER TO admin;

--
-- Name: financial_kpi_daily; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.financial_kpi_daily (
    id bigint NOT NULL,
    snapshot_date date NOT NULL,
    partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    revenue_recognized_cents bigint DEFAULT 0 NOT NULL,
    ar_open_cents bigint DEFAULT 0 NOT NULL,
    arpl_cents bigint DEFAULT 0 NOT NULL,
    gross_margin_pct numeric(10,4) DEFAULT 0 NOT NULL,
    dso_days numeric(10,2) DEFAULT 0 NOT NULL,
    active_invoice_count integer DEFAULT 0 NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    dedupe_key character varying(180),
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_fkd_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2)))
);


ALTER TABLE public.financial_kpi_daily OWNER TO admin;

--
-- Name: action; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.action (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    type text NOT NULL,
    model_id integer NOT NULL,
    name character varying(254) NOT NULL,
    description text,
    parameters text,
    parameter_mappings text,
    visualization_settings text,
    public_uuid character(36),
    made_public_by_id integer,
    creator_id integer,
    archived boolean DEFAULT false NOT NULL,
    entity_id character(21)
);


ALTER TABLE public.action OWNER TO admin;

--
-- Name: activity; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.activity (
    id integer NOT NULL,
    topic character varying(32) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    user_id integer,
    model character varying(32),
    model_id integer,
    database_id integer,
    table_id integer,
    custom_id character varying(48),
    details text NOT NULL
);


ALTER TABLE public.activity OWNER TO admin;

--
-- Name: allocations; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.allocations (
    id character varying NOT NULL,
    order_id character varying NOT NULL,
    locker_id character varying,
    slot integer NOT NULL,
    state public.allocationstate NOT NULL,
    locked_until timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    allocated_at timestamp with time zone,
    released_at timestamp with time zone,
    release_reason character varying(255),
    slot_size character varying(20),
    ttl_seconds integer
);


ALTER TABLE public.allocations OWNER TO admin;

--
-- Name: analytics_facts; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.analytics_facts (
    id uuid NOT NULL,
    fact_key character varying(200) NOT NULL,
    fact_name character varying(150) NOT NULL,
    order_id character varying(100) NOT NULL,
    order_channel character varying(50),
    region_code character varying(20),
    slot_id character varying(100),
    payload jsonb NOT NULL,
    occurred_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.analytics_facts OWNER TO admin;

--
-- Name: api_key; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.api_key (
    id integer NOT NULL,
    user_id integer NOT NULL,
    key character varying(254) NOT NULL,
    key_prefix character varying(7) NOT NULL,
    creator_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(254) NOT NULL,
    updated_by_id integer NOT NULL
);


ALTER TABLE public.api_key OWNER TO admin;

--
-- Name: application_permissions_revision; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.application_permissions_revision (
    id integer NOT NULL,
    before text NOT NULL,
    after text NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    remark text
);


ALTER TABLE public.application_permissions_revision OWNER TO admin;

--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.audit_log (
    id integer NOT NULL,
    topic character varying(32) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    end_timestamp timestamp with time zone,
    user_id integer,
    model character varying(32),
    model_id integer,
    details text NOT NULL
);


ALTER TABLE public.audit_log OWNER TO admin;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.audit_logs (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    actor_id character varying(36),
    actor_role character varying(40),
    action character varying(80) NOT NULL,
    target_type character varying(40) NOT NULL,
    target_id character varying(36) NOT NULL,
    old_state jsonb,
    new_state jsonb,
    ip_address inet,
    user_agent text,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO admin;

--
-- Name: auth_sessions; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.auth_sessions (
    id integer NOT NULL,
    user_id character varying(36) NOT NULL,
    session_token_hash character varying(255) NOT NULL,
    user_agent character varying(500),
    ip_address character varying(64),
    created_at timestamp without time zone NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    revoked_at timestamp without time zone
);


ALTER TABLE public.auth_sessions OWNER TO admin;

--
-- Name: billing_processed_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.billing_processed_events (
    id uuid NOT NULL,
    event_key character varying(200) NOT NULL,
    order_id character varying(100) NOT NULL,
    status character varying(50) NOT NULL,
    error_message text,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.billing_processed_events OWNER TO admin;

--
-- Name: ble_handshake_logs; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ble_handshake_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    pickup_id character varying NOT NULL,
    locker_id character varying NOT NULL,
    handshake_type character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    rssi_at_handshake integer,
    duration_ms integer,
    challenge_hash character varying(128),
    response_hash character varying(128),
    ble_device_id character varying(128),
    error_code character varying(50),
    error_message text,
    metadata_json jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ble_handshake_logs OWNER TO admin;

--
-- Name: bookmark_ordering; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.bookmark_ordering (
    id integer NOT NULL,
    user_id integer NOT NULL,
    type character varying(255) NOT NULL,
    item_id integer NOT NULL,
    ordering integer NOT NULL
);


ALTER TABLE public.bookmark_ordering OWNER TO admin;

--
-- Name: capability_channel; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_channel (
    id bigint NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(120) NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_channel OWNER TO admin;

--
-- Name: capability_context; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_context (
    id bigint NOT NULL,
    channel_id bigint NOT NULL,
    code character varying(80) NOT NULL,
    name character varying(120) NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_context OWNER TO admin;

--
-- Name: capability_country; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_country (
    id integer NOT NULL,
    code character(2) NOT NULL,
    name character varying(100) NOT NULL,
    continent character varying(50),
    default_currency character(3),
    default_timezone character varying(50),
    address_format character varying(20),
    metadata_json jsonb,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.capability_country OWNER TO admin;

--
-- Name: capability_locker_location; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_locker_location (
    id integer NOT NULL,
    external_id character varying(100),
    province_code character varying(10),
    city_name character varying(100),
    district character varying(100),
    postal_code character varying(20),
    latitude numeric(10,8),
    longitude numeric(11,8),
    geom public.geometry(Point,4326),
    timezone character varying(50),
    address_street character varying(255),
    address_number character varying(20),
    address_complement character varying(100),
    operating_hours_json jsonb,
    is_active boolean DEFAULT true,
    metadata_json jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    has_ble boolean DEFAULT false
);


ALTER TABLE public.capability_locker_location OWNER TO admin;

--
-- Name: capability_profile; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_profile (
    id bigint NOT NULL,
    region_id bigint NOT NULL,
    channel_id bigint NOT NULL,
    context_id bigint NOT NULL,
    profile_code character varying(160) NOT NULL,
    name character varying(180) NOT NULL,
    priority integer DEFAULT 100 NOT NULL,
    currency character varying(10) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    valid_from timestamp with time zone,
    valid_until timestamp with time zone
);


ALTER TABLE public.capability_profile OWNER TO admin;

--
-- Name: capability_profile_action; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_profile_action (
    id bigint NOT NULL,
    profile_id bigint NOT NULL,
    action_code character varying(80) NOT NULL,
    label character varying(120) NOT NULL,
    sort_order integer DEFAULT 100 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    config_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_profile_action OWNER TO admin;

--
-- Name: capability_profile_constraint; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_profile_constraint (
    id bigint NOT NULL,
    profile_id bigint NOT NULL,
    code character varying(100) NOT NULL,
    value_json jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_profile_constraint OWNER TO admin;

--
-- Name: capability_profile_method; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_profile_method (
    id bigint NOT NULL,
    profile_id bigint NOT NULL,
    payment_method_id bigint NOT NULL,
    label character varying(120),
    sort_order integer DEFAULT 100 NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    wallet_provider_id bigint,
    rules_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_profile_method OWNER TO admin;

--
-- Name: capability_profile_method_interface; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_profile_method_interface (
    id bigint NOT NULL,
    profile_method_id bigint NOT NULL,
    payment_interface_id bigint NOT NULL,
    sort_order integer DEFAULT 100 NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    config_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_profile_method_interface OWNER TO admin;

--
-- Name: capability_profile_method_requirement; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_profile_method_requirement (
    id bigint NOT NULL,
    profile_method_id bigint NOT NULL,
    requirement_id bigint NOT NULL,
    is_required boolean DEFAULT true NOT NULL,
    requirement_scope character varying(40) DEFAULT 'request'::character varying NOT NULL,
    validation_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_profile_method_requirement OWNER TO admin;

--
-- Name: capability_profile_snapshot; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_profile_snapshot (
    id bigint NOT NULL,
    profile_id bigint NOT NULL,
    profile_code character varying(160) NOT NULL,
    locker_id character varying(36),
    resolved_json jsonb NOT NULL,
    snapshot_hash character varying(64) NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    status character varying(20) DEFAULT 'DRAFT'::character varying NOT NULL,
    published_at timestamp with time zone,
    superseded_at timestamp with time zone,
    generated_by character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_profile_snapshot OWNER TO admin;

--
-- Name: capability_profile_snapshot_old; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_profile_snapshot_old (
    id bigint NOT NULL,
    profile_id bigint NOT NULL,
    snapshot_version integer NOT NULL,
    snapshot_json jsonb NOT NULL,
    created_by character varying(120),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_profile_snapshot_old OWNER TO admin;

--
-- Name: capability_profile_target; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_profile_target (
    id bigint NOT NULL,
    profile_id bigint NOT NULL,
    target_type character varying(40) NOT NULL,
    target_key character varying(120) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    locker_id character varying(64)
);


ALTER TABLE public.capability_profile_target OWNER TO admin;

--
-- Name: capability_province; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_province (
    id integer NOT NULL,
    code character varying(10) NOT NULL,
    name character varying(100) NOT NULL,
    country_code character(2),
    province_code_original character(2),
    region character varying(50),
    timezone character varying(50),
    is_active boolean DEFAULT true,
    metadata_json jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.capability_province OWNER TO admin;

--
-- Name: capability_region; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_region (
    id bigint NOT NULL,
    code character varying(20) NOT NULL,
    name character varying(120) NOT NULL,
    country_code character varying(10),
    continent character varying(60),
    default_currency character varying(10) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_region OWNER TO admin;

--
-- Name: capability_requirement_catalog; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.capability_requirement_catalog (
    id bigint NOT NULL,
    code character varying(100) NOT NULL,
    name character varying(120) NOT NULL,
    data_type character varying(40) NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.capability_requirement_catalog OWNER TO admin;

--
-- Name: card_bookmark; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.card_bookmark (
    id integer NOT NULL,
    user_id integer NOT NULL,
    card_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.card_bookmark OWNER TO admin;

--
-- Name: card_label; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.card_label (
    id integer NOT NULL,
    card_id integer NOT NULL,
    label_id integer NOT NULL
);


ALTER TABLE public.card_label OWNER TO admin;

--
-- Name: chart_of_accounts; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.chart_of_accounts (
    id character varying(36) NOT NULL,
    account_code character varying(32) NOT NULL,
    account_name character varying(140) NOT NULL,
    account_type character varying(20) NOT NULL,
    normal_balance character varying(10) NOT NULL,
    parent_account_id character varying(36),
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    is_active boolean DEFAULT true NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_coa_account_type CHECK (((account_type)::text = ANY ((ARRAY['ASSET'::character varying, 'LIABILITY'::character varying, 'EQUITY'::character varying, 'REVENUE'::character varying, 'EXPENSE'::character varying])::text[]))),
    CONSTRAINT ck_coa_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_coa_normal_balance CHECK (((normal_balance)::text = ANY ((ARRAY['DEBIT'::character varying, 'CREDIT'::character varying])::text[])))
);


ALTER TABLE public.chart_of_accounts OWNER TO admin;

--
-- Name: collection; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.collection (
    id integer NOT NULL,
    name text NOT NULL,
    description text,
    archived boolean DEFAULT false NOT NULL,
    location character varying(254) DEFAULT '/'::character varying NOT NULL,
    personal_owner_id integer,
    slug character varying(510) NOT NULL,
    namespace character varying(254),
    authority_level character varying(255),
    entity_id character(21),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    type character varying(256)
);


ALTER TABLE public.collection OWNER TO admin;

--
-- Name: collection_bookmark; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.collection_bookmark (
    id integer NOT NULL,
    user_id integer NOT NULL,
    collection_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.collection_bookmark OWNER TO admin;

--
-- Name: collection_permission_graph_revision; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.collection_permission_graph_revision (
    id integer NOT NULL,
    before text NOT NULL,
    after text NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    remark text
);


ALTER TABLE public.collection_permission_graph_revision OWNER TO admin;

--
-- Name: connection_impersonations; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.connection_impersonations (
    id integer NOT NULL,
    db_id integer NOT NULL,
    group_id integer NOT NULL,
    attribute text
);


ALTER TABLE public.connection_impersonations OWNER TO admin;

--
-- Name: core_session; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.core_session (
    id character varying(254) NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    anti_csrf_token text
);


ALTER TABLE public.core_session OWNER TO admin;

--
-- Name: core_user; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.core_user (
    id integer NOT NULL,
    email public.citext NOT NULL,
    first_name character varying(254),
    last_name character varying(254),
    password character varying(254),
    password_salt character varying(254) DEFAULT 'default'::character varying,
    date_joined timestamp with time zone NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    reset_token character varying(254),
    reset_triggered bigint,
    is_qbnewb boolean DEFAULT true NOT NULL,
    login_attributes text,
    updated_at timestamp without time zone,
    sso_source character varying(254),
    locale character varying(5),
    is_datasetnewb boolean DEFAULT true NOT NULL,
    settings text,
    type character varying(64) DEFAULT 'personal'::character varying NOT NULL
);


ALTER TABLE public.core_user OWNER TO admin;

--
-- Name: cost_center_monthly; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.cost_center_monthly (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    locker_id character varying NOT NULL,
    month date NOT NULL,
    rent_cents bigint DEFAULT 0,
    maintenance_preventive_cents bigint DEFAULT 0,
    maintenance_corrective_cents bigint DEFAULT 0,
    connectivity_cents bigint DEFAULT 0,
    energy_cents bigint DEFAULT 0,
    insurance_cents bigint DEFAULT 0,
    payment_gateway_fee_cents bigint DEFAULT 0,
    depreciation_cents bigint DEFAULT 0,
    cleaning_cents bigint DEFAULT 0,
    security_cents bigint DEFAULT 0,
    marketing_cents bigint DEFAULT 0,
    other_cents bigint DEFAULT 0,
    notes text,
    metadata_json jsonb DEFAULT '{}'::jsonb,
    created_by character varying(36),
    updated_by character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    total_opex_cents bigint GENERATED ALWAYS AS (((((((((((COALESCE(rent_cents, (0)::bigint) + COALESCE(maintenance_preventive_cents, (0)::bigint)) + COALESCE(maintenance_corrective_cents, (0)::bigint)) + COALESCE(connectivity_cents, (0)::bigint)) + COALESCE(energy_cents, (0)::bigint)) + COALESCE(insurance_cents, (0)::bigint)) + COALESCE(payment_gateway_fee_cents, (0)::bigint)) + COALESCE(cleaning_cents, (0)::bigint)) + COALESCE(security_cents, (0)::bigint)) + COALESCE(marketing_cents, (0)::bigint)) + COALESCE(other_cents, (0)::bigint))) STORED,
    total_costs_cents bigint GENERATED ALWAYS AS ((((((((((((COALESCE(rent_cents, (0)::bigint) + COALESCE(maintenance_preventive_cents, (0)::bigint)) + COALESCE(maintenance_corrective_cents, (0)::bigint)) + COALESCE(connectivity_cents, (0)::bigint)) + COALESCE(energy_cents, (0)::bigint)) + COALESCE(insurance_cents, (0)::bigint)) + COALESCE(payment_gateway_fee_cents, (0)::bigint)) + COALESCE(cleaning_cents, (0)::bigint)) + COALESCE(security_cents, (0)::bigint)) + COALESCE(marketing_cents, (0)::bigint)) + COALESCE(other_cents, (0)::bigint)) + COALESCE(depreciation_cents, (0)::bigint))) STORED,
    CONSTRAINT ck_ccm_amounts_non_negative CHECK (((rent_cents >= 0) AND (maintenance_preventive_cents >= 0) AND (maintenance_corrective_cents >= 0) AND (connectivity_cents >= 0) AND (energy_cents >= 0) AND (insurance_cents >= 0) AND (payment_gateway_fee_cents >= 0) AND (depreciation_cents >= 0))),
    CONSTRAINT ck_ccm_month_start CHECK ((month = (date_trunc('month'::text, (month)::timestamp without time zone))::date))
);


ALTER TABLE public.cost_center_monthly OWNER TO admin;

--
-- Name: cost_centers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.cost_centers (
    id uuid NOT NULL,
    locker_id character varying,
    operational_cost_monthly_cents bigint,
    maintenance_cost_annual_cents bigint,
    depreciation_cost_annual_cents bigint,
    utilities_cost_monthly_cents bigint,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.cost_centers OWNER TO admin;

--
-- Name: credits; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.credits (
    id character varying NOT NULL,
    user_id character varying,
    order_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.creditstatus NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    revoked_at timestamp with time zone,
    source_type character varying(50),
    source_reason character varying(255),
    notes text,
    CONSTRAINT ck_credits_amount_positive CHECK ((amount_cents > 0)),
    CONSTRAINT ck_credits_expiry_after_create CHECK ((expires_at > created_at)),
    CONSTRAINT ck_credits_revoked_after_create CHECK (((revoked_at IS NULL) OR (revoked_at >= created_at))),
    CONSTRAINT ck_credits_used_after_create CHECK (((used_at IS NULL) OR (used_at >= created_at)))
);


ALTER TABLE public.credits OWNER TO admin;

--
-- Name: custom_domains; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.custom_domains (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    tenant_id character varying(100) NOT NULL,
    domain character varying(255) NOT NULL,
    verified boolean DEFAULT false,
    ssl_cert_ref character varying(255),
    created_at timestamp with time zone DEFAULT now(),
    verified_at timestamp with time zone
);


ALTER TABLE public.custom_domains OWNER TO admin;

--
-- Name: customer_feedback; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.customer_feedback (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    order_id character varying(64),
    rating integer,
    comment text,
    sentiment_score double precision,
    sentiment_label character varying(20),
    topics text[],
    user_intent character varying(32),
    source character varying(64) DEFAULT 'api'::character varying NOT NULL,
    embedding_model character varying(160),
    alert_notified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_customer_feedback_rating CHECK (((rating IS NULL) OR ((rating >= 1) AND (rating <= 5))))
);


ALTER TABLE public.customer_feedback OWNER TO admin;

--
-- Name: customer_subscriptions; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.customer_subscriptions (
    id character varying(36) NOT NULL,
    user_id character varying(36),
    plan_type character varying(30) NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE'::character varying,
    monthly_fee_cents integer NOT NULL,
    free_shipping boolean DEFAULT false,
    priority_shelf boolean DEFAULT false,
    exclusive_deals boolean DEFAULT false,
    started_at timestamp without time zone,
    next_billing_at timestamp without time zone,
    cancelled_at timestamp without time zone,
    payment_method_id character varying(36),
    billing_cycle character varying(20) DEFAULT 'MONTHLY'::character varying,
    cancel_at_period_end boolean DEFAULT false,
    trial_start timestamp with time zone,
    trial_end timestamp with time zone,
    current_period_start timestamp with time zone,
    current_period_end timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.customer_subscriptions OWNER TO admin;

--
-- Name: dashboard_bookmark; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.dashboard_bookmark (
    id integer NOT NULL,
    user_id integer NOT NULL,
    dashboard_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.dashboard_bookmark OWNER TO admin;

--
-- Name: dashboard_favorite; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.dashboard_favorite (
    id integer NOT NULL,
    user_id integer NOT NULL,
    dashboard_id integer NOT NULL
);


ALTER TABLE public.dashboard_favorite OWNER TO admin;

--
-- Name: dashboard_tab; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.dashboard_tab (
    id integer NOT NULL,
    dashboard_id integer NOT NULL,
    name text NOT NULL,
    "position" integer NOT NULL,
    entity_id character(21),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.dashboard_tab OWNER TO admin;

--
-- Name: dashboardcard_series; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.dashboardcard_series (
    id integer NOT NULL,
    dashboardcard_id integer NOT NULL,
    card_id integer NOT NULL,
    "position" integer NOT NULL
);


ALTER TABLE public.dashboardcard_series OWNER TO admin;

--
-- Name: data_deletion_requests; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.data_deletion_requests (
    id character varying(36) NOT NULL,
    user_id character varying(36),
    requested_by character varying(255),
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    reason character varying(255),
    rejection_reason text,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.data_deletion_requests OWNER TO admin;

--
-- Name: databasechangelog; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.databasechangelog (
    id character varying(255) NOT NULL,
    author character varying(255) NOT NULL,
    filename character varying(255) NOT NULL,
    dateexecuted timestamp without time zone NOT NULL,
    orderexecuted integer NOT NULL,
    exectype character varying(10) NOT NULL,
    md5sum character varying(35),
    description character varying(255),
    comments character varying(255),
    tag character varying(255),
    liquibase character varying(20),
    contexts character varying(255),
    labels character varying(255),
    deployment_id character varying(10)
);


ALTER TABLE public.databasechangelog OWNER TO admin;

--
-- Name: databasechangeloglock; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.databasechangeloglock (
    id integer NOT NULL,
    locked boolean NOT NULL,
    lockgranted timestamp without time zone,
    lockedby character varying(255)
);


ALTER TABLE public.databasechangeloglock OWNER TO admin;

--
-- Name: demand_forecast; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.demand_forecast (
    id bigint NOT NULL,
    locker_id character varying(36) NOT NULL,
    forecast_date date NOT NULL,
    predicted_orders integer NOT NULL,
    predicted_revenue_cents bigint NOT NULL,
    confidence_lower integer,
    confidence_upper integer,
    model_version character varying(50),
    generated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_forecast_predicted CHECK (((predicted_orders >= 0) AND (predicted_revenue_cents >= 0)))
);


ALTER TABLE public.demand_forecast OWNER TO admin;

--
-- Name: dependency; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.dependency (
    id integer NOT NULL,
    model character varying(32) NOT NULL,
    model_id integer NOT NULL,
    dependent_on_model character varying(32) NOT NULL,
    dependent_on_id integer NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.dependency OWNER TO admin;

--
-- Name: device_registry; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.device_registry (
    device_hash text NOT NULL,
    version text NOT NULL,
    first_seen_at bigint NOT NULL,
    last_seen_at bigint NOT NULL,
    seen_count integer DEFAULT 1 NOT NULL,
    flags_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT ck_device_registry_seen_count_positive CHECK ((seen_count >= 1))
);


ALTER TABLE public.device_registry OWNER TO admin;

--
-- Name: dimension; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.dimension (
    id integer NOT NULL,
    field_id integer NOT NULL,
    name character varying(254) NOT NULL,
    type character varying(254) NOT NULL,
    human_readable_field_id integer,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    entity_id character(21)
);


ALTER TABLE public.dimension OWNER TO admin;

--
-- Name: domain_event_outbox; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.domain_event_outbox (
    id character varying NOT NULL,
    event_key character varying(255) NOT NULL,
    aggregate_type character varying(100),
    aggregate_id character varying(100),
    event_name character varying(100),
    event_version integer,
    status character varying(50),
    payload_json text,
    occurred_at timestamp with time zone,
    published_at timestamp with time zone,
    last_error text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    retry_count integer DEFAULT 0 NOT NULL,
    next_retry_at timestamp without time zone,
    processing_started_at timestamp without time zone
);


ALTER TABLE public.domain_event_outbox OWNER TO admin;

--
-- Name: domain_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.domain_events (
    id uuid NOT NULL,
    event_key character varying(200) NOT NULL,
    aggregate_type character varying(100) NOT NULL,
    aggregate_id character varying(100) NOT NULL,
    event_name character varying(150) NOT NULL,
    event_version integer NOT NULL,
    status public.event_status_enum NOT NULL,
    payload jsonb NOT NULL,
    occurred_at timestamp with time zone NOT NULL,
    published_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.domain_events OWNER TO admin;

--
-- Name: door_state; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.door_state (
    machine_id character varying(120) NOT NULL,
    door_id integer NOT NULL,
    state character varying(40) NOT NULL,
    product_id character varying(120),
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.door_state OWNER TO admin;

--
-- Name: dynamic_pricing_rules; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.dynamic_pricing_rules (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    rule_name character varying(128) NOT NULL,
    product_id character varying(255),
    category_id character varying(64),
    locker_id character varying(36),
    rule_type character varying(30) NOT NULL,
    trigger_condition jsonb NOT NULL,
    adjustment_type character varying(20) NOT NULL,
    adjustment_value numeric(10,4) NOT NULL,
    min_price_cents integer,
    max_price_cents integer,
    priority integer DEFAULT 100,
    is_active boolean DEFAULT true,
    valid_from timestamp with time zone,
    valid_until timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_dpr_adjustment_type CHECK (((adjustment_type)::text = ANY ((ARRAY['PERCENTAGE'::character varying, 'FIXED_AMOUNT'::character varying])::text[]))),
    CONSTRAINT ck_dpr_rule_type CHECK (((rule_type)::text = ANY ((ARRAY['DEMAND_BASED'::character varying, 'INVENTORY_BASED'::character varying, 'TIME_BASED'::character varying, 'COMPETITOR_BASED'::character varying])::text[])))
);


ALTER TABLE public.dynamic_pricing_rules OWNER TO admin;

--
-- Name: ecommerce_partners; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ecommerce_partners (
    id character varying(36) NOT NULL,
    name character varying(128) NOT NULL,
    code character varying(32) NOT NULL,
    integration_type character varying(30) NOT NULL,
    api_base_url character varying(500),
    credentials_secret_ref character varying(255),
    webhook_secret_ref character varying(255),
    revenue_share_pct numeric(6,4),
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    sla_pickup_hours integer DEFAULT 72 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    country character varying(2) DEFAULT 'BR'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(30) DEFAULT 'DRAFT'::character varying NOT NULL,
    legal_name character varying(140),
    tax_id character varying(32),
    tier character varying(20) DEFAULT 'STANDARD'::character varying,
    support_email character varying(128),
    support_phone character varying(32)
);


ALTER TABLE public.ecommerce_partners OWNER TO admin;

--
-- Name: ellanlab_depreciation_schedule; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ellanlab_depreciation_schedule (
    id bigint NOT NULL,
    asset_id character varying(36) NOT NULL,
    depreciation_month date NOT NULL,
    partner_id character varying(36),
    locker_id character varying(36),
    depreciation_amount_cents bigint NOT NULL,
    accumulated_depreciation_cents bigint NOT NULL,
    nbv_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    status character varying(20) DEFAULT 'POSTED'::character varying NOT NULL,
    dedupe_key character varying(180),
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_eds_month_start CHECK ((depreciation_month = (date_trunc('month'::text, (depreciation_month)::timestamp with time zone))::date)),
    CONSTRAINT ck_eds_status CHECK (((status)::text = ANY ((ARRAY['POSTED'::character varying, 'REVERSED'::character varying])::text[])))
);


ALTER TABLE public.ellanlab_depreciation_schedule OWNER TO admin;

--
-- Name: ellanlab_hardware_assets; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ellanlab_hardware_assets (
    id character varying(36) NOT NULL,
    asset_code character varying(64) NOT NULL,
    locker_id character varying(36),
    partner_id character varying(36),
    asset_category character varying(40) NOT NULL,
    description character varying(255) NOT NULL,
    acquisition_date date NOT NULL,
    in_service_date date,
    acquisition_cost_cents bigint NOT NULL,
    residual_value_cents bigint DEFAULT 0 NOT NULL,
    useful_life_months integer NOT NULL,
    depreciation_method character varying(20) DEFAULT 'STRAIGHT_LINE'::character varying NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    status character varying(20) DEFAULT 'ACTIVE'::character varying NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    installation_cost_cents bigint DEFAULT 0 NOT NULL,
    supplier_name character varying(140),
    warranty_ends_at date,
    notes text,
    CONSTRAINT ck_eha_asset_category CHECK (((asset_category)::text = ANY ((ARRAY['LOCKER'::character varying, 'TOTEM'::character varying, 'SENSOR'::character varying, 'NETWORK'::character varying, 'BATTERY'::character varying, 'OTHER'::character varying])::text[]))),
    CONSTRAINT ck_eha_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_eha_life CHECK ((useful_life_months > 0)),
    CONSTRAINT ck_eha_method CHECK (((depreciation_method)::text = 'STRAIGHT_LINE'::text)),
    CONSTRAINT ck_eha_status CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'INACTIVE'::character varying, 'DISPOSED'::character varying])::text[])))
);


ALTER TABLE public.ellanlab_hardware_assets OWNER TO admin;

--
-- Name: ellanlab_monthly_pnl; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ellanlab_monthly_pnl (
    id bigint NOT NULL,
    pnl_month date NOT NULL,
    partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    revenue_cents bigint DEFAULT 0 NOT NULL,
    cogs_cents bigint DEFAULT 0 NOT NULL,
    opex_cents bigint DEFAULT 0 NOT NULL,
    depreciation_cents bigint DEFAULT 0 NOT NULL,
    gross_profit_cents bigint DEFAULT 0 NOT NULL,
    gross_margin_pct numeric(10,4),
    ebitda_cents bigint DEFAULT 0 NOT NULL,
    net_income_cents bigint DEFAULT 0 NOT NULL,
    ar_open_cents bigint DEFAULT 0 NOT NULL,
    dso_days numeric(10,2),
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_emp_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_emp_month_start CHECK ((pnl_month = (date_trunc('month'::text, (pnl_month)::timestamp with time zone))::date))
);


ALTER TABLE public.ellanlab_monthly_pnl OWNER TO admin;

--
-- Name: ellanlab_opex_entries; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ellanlab_opex_entries (
    id character varying(36) NOT NULL,
    expense_date date NOT NULL,
    expense_month date NOT NULL,
    partner_id character varying(36),
    locker_id character varying(36),
    cost_center_code character varying(32),
    category character varying(40) NOT NULL,
    description character varying(255) NOT NULL,
    amount_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    vendor_ref character varying(120),
    reference_source character varying(50) DEFAULT 'manual'::character varying NOT NULL,
    dedupe_key character varying(180),
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_eoe_category CHECK (((category)::text = ANY ((ARRAY['MAINTENANCE'::character varying, 'CONNECTIVITY'::character varying, 'ENERGY'::character varying, 'RENT'::character varying, 'SUPPORT'::character varying, 'LOGISTICS'::character varying, 'OTHER'::character varying])::text[]))),
    CONSTRAINT ck_eoe_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_eoe_month_start CHECK ((expense_month = (date_trunc('month'::text, (expense_month)::timestamp with time zone))::date))
);


ALTER TABLE public.ellanlab_opex_entries OWNER TO admin;

--
-- Name: financial_ledger; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.financial_ledger (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    order_id character varying(36),
    payment_transaction_id character varying(36),
    wallet_id character varying(36),
    entry_type character varying(30) NOT NULL,
    amount_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    status character varying(20) DEFAULT 'POSTED'::character varying NOT NULL,
    external_reference character varying(100),
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_ledger_amount_nonzero CHECK ((amount_cents <> 0)),
    CONSTRAINT ck_ledger_status_check CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'POSTED'::character varying, 'VOIDED'::character varying])::text[])))
);


ALTER TABLE public.financial_ledger OWNER TO admin;

--
-- Name: fiscal_accounting_approvals; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.fiscal_accounting_approvals (
    id character varying(80) NOT NULL,
    owner character varying(160) NOT NULL,
    eta timestamp with time zone,
    status character varying(80) NOT NULL,
    payload_json jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.fiscal_accounting_approvals OWNER TO admin;

--
-- Name: fiscal_authority_callbacks; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.fiscal_authority_callbacks (
    id character varying(60) NOT NULL,
    invoice_id character varying(50) NOT NULL,
    authority character varying(30) NOT NULL,
    event_type character varying(80),
    status character varying(40),
    protocol_number character varying(120),
    raw_payload jsonb,
    received_at timestamp with time zone NOT NULL
);


ALTER TABLE public.fiscal_authority_callbacks OWNER TO admin;

--
-- Name: fiscal_auto_classification_log; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.fiscal_auto_classification_log (
    id bigint NOT NULL,
    order_id character varying(36) NOT NULL,
    invoice_id character varying(50),
    sku_id character varying(255) NOT NULL,
    ncm_applied character varying(10),
    icms_cst_applied character varying(3),
    pis_cst_applied character varying(2),
    cofins_cst_applied character varying(2),
    cfop_applied character varying(5),
    source character varying(20) NOT NULL,
    classified_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_facl_source CHECK (((source)::text = ANY ((ARRAY['AUTO_PRODUCT_CONFIG'::character varying, 'CATEGORY_FALLBACK'::character varying, 'MANUAL'::character varying, 'DEFAULT'::character varying])::text[])))
);


ALTER TABLE public.fiscal_auto_classification_log OWNER TO admin;

--
-- Name: fiscal_documents; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.fiscal_documents (
    id character varying NOT NULL,
    order_id character varying NOT NULL,
    receipt_code character varying(64) NOT NULL,
    document_type character varying(50) NOT NULL,
    channel character varying(20),
    region character varying(10),
    amount_cents integer NOT NULL,
    currency character varying(10) NOT NULL,
    delivery_mode character varying(20),
    send_status character varying(50),
    send_target character varying(255),
    print_status character varying(50),
    print_site_path character varying(255),
    payload_json text NOT NULL,
    issued_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    cancel_reason text,
    cancelled_at timestamp with time zone,
    chave_acesso character varying(255),
    printed_at timestamp with time zone,
    sent_at timestamp with time zone,
    tax_amount_cents bigint,
    tax_breakdown_json jsonb,
    tenant_id character varying(64),
    xml_signed bytea,
    attempt integer DEFAULT 1 NOT NULL,
    previous_receipt_code character varying(64),
    regenerated_at timestamp without time zone,
    regenerate_reason character varying(255)
);


ALTER TABLE public.fiscal_documents OWNER TO admin;

--
-- Name: fiscal_provider_health_status; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.fiscal_provider_health_status (
    country character varying(5) NOT NULL,
    provider_name character varying(80) NOT NULL,
    mode character varying(20) NOT NULL,
    enabled boolean NOT NULL,
    base_url character varying(300),
    last_status character varying(20) NOT NULL,
    last_http_status integer,
    last_latency_ms integer,
    last_error character varying(1000),
    checked_at timestamp with time zone NOT NULL
);


ALTER TABLE public.fiscal_provider_health_status OWNER TO admin;

--
-- Name: fiscal_reconciliation_gaps; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.fiscal_reconciliation_gaps (
    id character varying(60) NOT NULL,
    dedupe_key character varying(180) NOT NULL,
    gap_type character varying(80) NOT NULL,
    severity character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    order_id character varying(100),
    invoice_id character varying(50),
    details_json jsonb,
    first_detected_at timestamp with time zone NOT NULL,
    last_detected_at timestamp with time zone NOT NULL,
    resolved_at timestamp with time zone
);


ALTER TABLE public.fiscal_reconciliation_gaps OWNER TO admin;

--
-- Name: fulfillment_centers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.fulfillment_centers (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    name character varying(128) NOT NULL,
    code character varying(32) NOT NULL,
    address_line character varying(255) NOT NULL,
    city character varying(100) NOT NULL,
    state character varying(50) NOT NULL,
    postal_code character varying(20) NOT NULL,
    country character varying(2) DEFAULT 'BR'::character varying,
    latitude numeric(10,8),
    longitude numeric(11,8),
    capacity_slots integer DEFAULT 0,
    active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.fulfillment_centers OWNER TO admin;

--
-- Name: fulfillment_inventory; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.fulfillment_inventory (
    id bigint NOT NULL,
    fulfillment_center_id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    quantity_on_hand integer DEFAULT 0 NOT NULL,
    quantity_reserved integer DEFAULT 0 NOT NULL,
    quantity_available integer GENERATED ALWAYS AS ((quantity_on_hand - quantity_reserved)) STORED,
    reorder_point integer DEFAULT 0,
    last_restocked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_fulfillment_qty CHECK (((quantity_on_hand >= 0) AND (quantity_reserved >= 0)))
);


ALTER TABLE public.fulfillment_inventory OWNER TO admin;

--
-- Name: fulfillment_orders; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.fulfillment_orders (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    order_id character varying(36) NOT NULL,
    fulfillment_center_id character varying(36) NOT NULL,
    status character varying(30) DEFAULT 'PENDING'::character varying NOT NULL,
    priority integer DEFAULT 100,
    picked_at timestamp with time zone,
    packed_at timestamp with time zone,
    shipped_at timestamp with time zone,
    delivered_to_locker_at timestamp with time zone,
    tracking_code character varying(128),
    carrier character varying(50),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_fulfillment_order_status CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'PICKING'::character varying, 'PACKING'::character varying, 'SHIPPED'::character varying, 'DELIVERED'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.fulfillment_orders OWNER TO admin;

--
-- Name: sandboxes; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.sandboxes (
    id integer NOT NULL,
    group_id integer NOT NULL,
    table_id integer NOT NULL,
    card_id integer,
    attribute_remappings text,
    permission_id integer
);


ALTER TABLE public.sandboxes OWNER TO admin;

--
-- Name: http_action; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.http_action (
    action_id integer NOT NULL,
    template text NOT NULL,
    response_handle text,
    error_handle text
);


ALTER TABLE public.http_action OWNER TO admin;

--
-- Name: idempotency_keys; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.idempotency_keys (
    id text NOT NULL,
    endpoint text NOT NULL,
    idem_key text NOT NULL,
    payload_hash text NOT NULL,
    response_blob text NOT NULL,
    status text NOT NULL,
    created_at bigint NOT NULL,
    expires_at bigint NOT NULL
);


ALTER TABLE public.idempotency_keys OWNER TO admin;

--
-- Name: implicit_action; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.implicit_action (
    action_id integer NOT NULL,
    kind text NOT NULL
);


ALTER TABLE public.implicit_action OWNER TO admin;

--
-- Name: inbound_deliveries; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.inbound_deliveries (
    id character varying(36) NOT NULL,
    logistics_partner_id character varying(36) NOT NULL,
    locker_id character varying(36) NOT NULL,
    slot_label character varying(20),
    tracking_code character varying(128) NOT NULL,
    barcode character varying(128),
    partner_order_ref character varying(128),
    recipient_name character varying(255),
    recipient_document character varying(32),
    recipient_phone character varying(32),
    recipient_email character varying(128),
    weight_g integer,
    width_mm integer,
    height_mm integer,
    depth_mm integer,
    declared_value_cents integer,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    requires_signature boolean DEFAULT false NOT NULL,
    requires_id_check boolean DEFAULT false NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    stored_at timestamp with time zone,
    first_notified_at timestamp with time zone,
    last_notified_at timestamp with time zone,
    notification_count integer DEFAULT 0 NOT NULL,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    returned_at timestamp with time zone,
    return_reason character varying(255),
    pickup_token_id character varying(36),
    carrier_payload_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.inbound_deliveries OWNER TO admin;

--
-- Name: inventory_movements; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.inventory_movements (
    id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    locker_id character varying(64) NOT NULL,
    movement_type character varying(30) NOT NULL,
    quantity_delta integer NOT NULL,
    reference_id character varying(64),
    reference_type character varying(30),
    note text,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_im_movement_type CHECK (((movement_type)::text = ANY ((ARRAY['RESTOCK'::character varying, 'SALE'::character varying, 'RESERVATION'::character varying, 'RESERVATION_RELEASE'::character varying, 'ADJUSTMENT'::character varying, 'RETURN'::character varying, 'DAMAGE'::character varying, 'EXPIRED'::character varying, 'TRANSFER_IN'::character varying, 'TRANSFER_OUT'::character varying])::text[])))
);


ALTER TABLE public.inventory_movements OWNER TO admin;

--
-- Name: inventory_reservations; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.inventory_reservations (
    id character varying(36) NOT NULL,
    order_id character varying(64) NOT NULL,
    product_id character varying(255) NOT NULL,
    locker_id character varying(64) NOT NULL,
    slot_size character varying(8) NOT NULL,
    quantity integer DEFAULT 1 NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE'::character varying NOT NULL,
    note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_ir_quantity_positive CHECK ((quantity > 0)),
    CONSTRAINT ck_ir_status CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'RELEASED'::character varying, 'CONSUMED'::character varying, 'EXPIRED'::character varying])::text[])))
);


ALTER TABLE public.inventory_reservations OWNER TO admin;

--
-- Name: invoice_delivery_log; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.invoice_delivery_log (
    id character varying(50) NOT NULL,
    invoice_id character varying(50) NOT NULL,
    channel character varying(32) NOT NULL,
    status character varying(32) NOT NULL,
    detail jsonb,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.invoice_delivery_log OWNER TO admin;

--
-- Name: invoice_email_outbox; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.invoice_email_outbox (
    id character varying(50) NOT NULL,
    invoice_id character varying(50) NOT NULL,
    template character varying(32) NOT NULL,
    to_email character varying(255) NOT NULL,
    subject character varying(500) NOT NULL,
    body_text text NOT NULL,
    detail_json jsonb,
    status character varying(24) NOT NULL,
    retry_count integer NOT NULL,
    next_retry_at timestamp with time zone,
    last_error character varying(2000),
    locked_by character varying(120),
    locked_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    sent_at timestamp with time zone
);


ALTER TABLE public.invoice_email_outbox OWNER TO admin;

--
-- Name: invoices; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.invoices (
    id character varying(50) NOT NULL,
    order_id character varying(100) NOT NULL,
    tenant_id character varying(100),
    country character varying(5) NOT NULL,
    invoice_type character varying(20) NOT NULL,
    status public.invoicestatus NOT NULL,
    xml_content jsonb,
    payload_json jsonb,
    error_message character varying(500),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    invoice_number character varying(50),
    invoice_series character varying(50),
    access_key character varying(120),
    payment_method character varying(50),
    currency character varying(10),
    tax_details jsonb,
    government_response jsonb,
    issued_at timestamp with time zone,
    processing_started_at timestamp with time zone,
    region character varying(20),
    amount_cents bigint,
    order_snapshot jsonb,
    last_error_code character varying(120),
    retry_count integer DEFAULT 0,
    next_retry_at timestamp with time zone,
    last_attempt_at timestamp with time zone,
    dead_lettered_at timestamp with time zone,
    locked_by character varying(120),
    locked_at timestamp with time zone,
    locker_id character varying(64),
    totem_id character varying(64),
    slot_label character varying(32),
    fiscal_doc_subtype character varying(20) DEFAULT 'NFC_E_65'::character varying NOT NULL,
    emission_mode character varying(20) DEFAULT 'ONLINE'::character varying NOT NULL,
    emitter_cnpj character varying(18),
    emitter_name character varying(140),
    consumer_cpf character varying(14),
    consumer_name character varying(140),
    locker_address jsonb,
    items_json jsonb,
    tax_breakdown_json jsonb,
    ecommerce_partner_id character varying(100)
);


ALTER TABLE public.invoices OWNER TO admin;

--
-- Name: journal_entries; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.journal_entries (
    id character varying(36) NOT NULL,
    entry_date date NOT NULL,
    description character varying(255) NOT NULL,
    reference_type character varying(50),
    reference_id character varying(36),
    reference_source character varying(50) DEFAULT 'manual'::character varying NOT NULL,
    dedupe_key character varying(128),
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    is_posted boolean DEFAULT false NOT NULL,
    posted_at timestamp with time zone,
    posted_by character varying(36),
    created_by character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.journal_entries OWNER TO admin;

--
-- Name: journal_entry_lines; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.journal_entry_lines (
    id bigint NOT NULL,
    journal_entry_id character varying(36) NOT NULL,
    line_number integer NOT NULL,
    account_id character varying(36) NOT NULL,
    partner_id character varying(36),
    locker_id character varying(36),
    description character varying(255),
    debit_amount numeric(16,2) DEFAULT 0 NOT NULL,
    credit_amount numeric(16,2) DEFAULT 0 NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    reference_source character varying(50) DEFAULT 'manual'::character varying NOT NULL,
    reference_id character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_jel_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_jel_single_side CHECK ((((debit_amount > (0)::numeric) AND (credit_amount = (0)::numeric)) OR ((credit_amount > (0)::numeric) AND (debit_amount = (0)::numeric))))
);


ALTER TABLE public.journal_entry_lines OWNER TO admin;

--
-- Name: kiosk_antifraud_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.kiosk_antifraud_events (
    id character varying NOT NULL,
    fp_hash character varying NOT NULL,
    ip_hash character varying NOT NULL,
    totem_id character varying NOT NULL,
    region character varying NOT NULL,
    created_at timestamp without time zone NOT NULL,
    blocked_until timestamp without time zone
);


ALTER TABLE public.kiosk_antifraud_events OWNER TO admin;

--
-- Name: label; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.label (
    id integer NOT NULL,
    name character varying(254) NOT NULL,
    slug character varying(254) NOT NULL,
    icon character varying(128)
);


ALTER TABLE public.label OWNER TO admin;

--
-- Name: lifecycle_deadlines; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.lifecycle_deadlines (
    id uuid NOT NULL,
    deadline_key character varying(200) NOT NULL,
    order_id character varying(100) NOT NULL,
    order_channel character varying(50),
    deadline_type public.deadline_type_enum NOT NULL,
    status public.deadline_status_enum NOT NULL,
    due_at timestamp with time zone NOT NULL,
    locked_at timestamp with time zone,
    executed_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    failure_count integer NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.lifecycle_deadlines OWNER TO admin;

--
-- Name: locker_capex; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_capex (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    locker_id character varying(36) NOT NULL,
    asset_id character varying(36),
    acquisition_cost_cents bigint NOT NULL,
    installation_cost_cents bigint DEFAULT 0 NOT NULL,
    residual_value_cents bigint DEFAULT 0 NOT NULL,
    useful_life_months integer DEFAULT 60 NOT NULL,
    depreciation_method character varying(20) DEFAULT 'STRAIGHT_LINE'::character varying NOT NULL,
    depreciation_start_date date DEFAULT CURRENT_DATE NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE'::character varying NOT NULL,
    disposal_date date,
    disposal_proceeds_cents bigint DEFAULT 0,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT locker_capex_acquisition_cost_cents_check CHECK ((acquisition_cost_cents >= 0)),
    CONSTRAINT locker_capex_depreciation_method_check CHECK (((depreciation_method)::text = ANY ((ARRAY['STRAIGHT_LINE'::character varying, 'DEGRESSIVE'::character varying])::text[]))),
    CONSTRAINT locker_capex_installation_cost_cents_check CHECK ((installation_cost_cents >= 0)),
    CONSTRAINT locker_capex_residual_value_cents_check CHECK ((residual_value_cents >= 0)),
    CONSTRAINT locker_capex_status_check CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'DISPOSED'::character varying, 'WRITTEN_OFF'::character varying])::text[]))),
    CONSTRAINT locker_capex_useful_life_months_check CHECK ((useful_life_months > 0))
);


ALTER TABLE public.locker_capex OWNER TO admin;

--
-- Name: locker_capex_details; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_capex_details (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    locker_id character varying NOT NULL,
    equipment_cost_cents bigint DEFAULT 0 NOT NULL,
    installation_cost_cents bigint DEFAULT 0 NOT NULL,
    connectivity_setup_cents bigint DEFAULT 0 NOT NULL,
    go_live_cost_cents bigint DEFAULT 0 NOT NULL,
    property_rent_cents bigint DEFAULT 0,
    property_ownership boolean DEFAULT false,
    property_address text,
    useful_life_months integer DEFAULT 60,
    salvage_value_cents bigint DEFAULT 0,
    depreciation_method character varying(20) DEFAULT 'STRAIGHT_LINE'::character varying,
    installation_date date,
    go_live_date date,
    supplier character varying(255),
    invoice_ref character varying(255),
    metadata_json jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_capex_amounts_non_negative CHECK (((equipment_cost_cents >= 0) AND (installation_cost_cents >= 0) AND (connectivity_setup_cents >= 0) AND (go_live_cost_cents >= 0))),
    CONSTRAINT ck_capex_depreciation_method CHECK (((depreciation_method)::text = ANY ((ARRAY['STRAIGHT_LINE'::character varying, 'DEGRESSIVE'::character varying, 'SUM_OF_YEARS'::character varying])::text[])))
);


ALTER TABLE public.locker_capex_details OWNER TO admin;

--
-- Name: locker_operators; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_operators (
    id character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    document character varying(32),
    email character varying(128),
    phone character varying(32),
    operator_type character varying(32) DEFAULT 'LOGISTICS'::character varying NOT NULL,
    country character varying(2) DEFAULT 'BR'::character varying NOT NULL,
    active boolean DEFAULT true NOT NULL,
    commission_rate double precision,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    contract_start_at timestamp with time zone,
    contract_end_at timestamp with time zone,
    contract_ref character varying(255),
    sla_pickup_hours integer DEFAULT 72,
    sla_return_hours integer DEFAULT 24,
    status character varying(30) DEFAULT 'DRAFT'::character varying NOT NULL,
    legal_name character varying(140),
    tier character varying(20) DEFAULT 'STANDARD'::character varying
);


ALTER TABLE public.locker_operators OWNER TO admin;

--
-- Name: locker_opex; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_opex (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    locker_id character varying(36) NOT NULL,
    reference_month date NOT NULL,
    cost_type character varying(40) NOT NULL,
    amount_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    description text,
    invoice_ref character varying(100),
    paid_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT locker_opex_amount_cents_check CHECK ((amount_cents >= 0)),
    CONSTRAINT locker_opex_cost_type_check CHECK (((cost_type)::text = ANY ((ARRAY['RENT'::character varying, 'MAINTENANCE_PREVENTIVE'::character varying, 'MAINTENANCE_CORRECTIVE'::character varying, 'CONNECTIVITY'::character varying, 'ENERGY'::character varying, 'INSURANCE'::character varying, 'CLEANING'::character varying, 'SECURITY'::character varying, 'OTHER'::character varying])::text[])))
);


ALTER TABLE public.locker_opex OWNER TO admin;

--
-- Name: locker_payment_methods; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_payment_methods (
    locker_id character varying(120) NOT NULL,
    method character varying(64) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.locker_payment_methods OWNER TO admin;

--
-- Name: locker_slot_configs; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_slot_configs (
    id bigint NOT NULL,
    locker_id character varying(64) NOT NULL,
    slot_size character varying(8) NOT NULL,
    slot_count integer DEFAULT 0 NOT NULL,
    available_count integer,
    width_cm integer,
    height_cm integer,
    depth_cm integer,
    max_weight_kg double precision,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    width_mm integer,
    height_mm integer,
    depth_mm integer,
    max_weight_g integer,
    CONSTRAINT ck_slot_cfg_dimensions_positive CHECK ((((width_mm IS NULL) OR (width_mm > 0)) AND ((height_mm IS NULL) OR (height_mm > 0)) AND ((depth_mm IS NULL) OR (depth_mm > 0)) AND ((max_weight_g IS NULL) OR (max_weight_g > 0))))
);


ALTER TABLE public.locker_slot_configs OWNER TO admin;

--
-- Name: locker_slot_hourly_occupancy; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_slot_hourly_occupancy (
    id bigint NOT NULL,
    locker_id character varying(36) NOT NULL,
    slot_number integer NOT NULL,
    hour_bucket timestamp with time zone NOT NULL,
    is_occupied boolean NOT NULL,
    delivery_id character varying(36),
    occupied_duration_minutes integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_lsho_occupied_duration CHECK (((occupied_duration_minutes >= 0) AND (occupied_duration_minutes <= 60)))
);


ALTER TABLE public.locker_slot_hourly_occupancy OWNER TO admin;

--
-- Name: locker_slots; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_slots (
    id character varying(36) NOT NULL,
    locker_id character varying(36) NOT NULL,
    slot_label character varying(20) NOT NULL,
    slot_size character varying(8) NOT NULL,
    status character varying(20) DEFAULT 'AVAILABLE'::character varying NOT NULL,
    occupied_since timestamp with time zone,
    current_allocation_id character varying(36),
    current_delivery_id character varying(36),
    current_rental_id character varying(36),
    last_opened_at timestamp with time zone,
    last_closed_at timestamp with time zone,
    fault_code character varying(50),
    fault_detail text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.locker_slots OWNER TO admin;

--
-- Name: locker_telemetry; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_telemetry (
    id bigint NOT NULL,
    locker_id character varying(36) NOT NULL,
    event_type character varying(50) NOT NULL,
    slot_label character varying(20),
    temperature_celsius numeric(5,2),
    humidity_pct numeric(5,2),
    battery_pct numeric(5,2),
    voltage_mv integer,
    signal_rssi integer,
    firmware_version character varying(50),
    raw_payload_json jsonb,
    occurred_at timestamp with time zone NOT NULL,
    received_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.locker_telemetry OWNER TO admin;

--
-- Name: locker_telemetry_partitioned; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_telemetry_partitioned (
    id bigint NOT NULL,
    locker_id character varying(36) NOT NULL,
    event_type character varying(50) NOT NULL,
    slot_label character varying(20),
    temperature_celsius numeric(5,2),
    humidity_pct numeric(5,2),
    battery_pct numeric(5,2),
    voltage_mv integer,
    signal_rssi integer,
    firmware_version character varying(50),
    raw_payload_json jsonb,
    occurred_at timestamp with time zone NOT NULL,
    received_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.locker_telemetry_partitioned OWNER TO admin;

--
-- Name: locker_utilization_snapshots; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.locker_utilization_snapshots (
    id bigint NOT NULL,
    snapshot_date date NOT NULL,
    partner_id character varying(36) NOT NULL,
    locker_id character varying(36) NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    timezone character varying(64) DEFAULT 'UTC'::character varying NOT NULL,
    measured_occupied_minutes integer DEFAULT 0 NOT NULL,
    measured_occupied_hours numeric(12,4) DEFAULT 0 NOT NULL,
    billed_storage_units numeric(12,4) DEFAULT 0 NOT NULL,
    billed_storage_hours numeric(12,4) DEFAULT 0 NOT NULL,
    billed_storage_amount_cents bigint DEFAULT 0 NOT NULL,
    difference_hours numeric(12,4) DEFAULT 0 NOT NULL,
    difference_pct numeric(10,4),
    divergence_status character varying(20) DEFAULT 'OK'::character varying NOT NULL,
    dedupe_key character varying(180),
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_lus_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_lus_status CHECK (((divergence_status)::text = ANY ((ARRAY['OK'::character varying, 'UNDER_BILLED'::character varying, 'OVER_BILLED'::character varying, 'MISSING_BILLING'::character varying])::text[])))
);


ALTER TABLE public.locker_utilization_snapshots OWNER TO admin;

--
-- Name: lockers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.lockers (
    id character varying NOT NULL,
    external_id character varying(100),
    display_name character varying(255),
    description text,
    region character varying(10) NOT NULL,
    site_id character varying(100),
    timezone character varying(50),
    address_line character varying(255),
    address_number character varying(50),
    address_extra character varying(255),
    district character varying(100),
    city character varying(100),
    state character varying(100),
    postal_code character varying(50),
    country character varying(100),
    latitude double precision,
    longitude double precision,
    active boolean DEFAULT true,
    slots_count integer DEFAULT 0 NOT NULL,
    machine_id character varying(100),
    allowed_channels character varying(100),
    allowed_payment_methods character varying(255),
    temperature_zone character varying(50) DEFAULT 'AMBIENT'::character varying,
    security_level character varying(50) DEFAULT 'STANDARD'::character varying,
    has_camera boolean DEFAULT false,
    has_alarm boolean DEFAULT false,
    access_hours text,
    operator_id character varying(100),
    tenant_id character varying(100),
    is_rented boolean DEFAULT false,
    metadata_json jsonb,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    finding_instructions text,
    pickup_code_length integer DEFAULT 6 NOT NULL,
    pickup_reuse_policy character varying(32) DEFAULT 'NO_REUSE'::character varying NOT NULL,
    pickup_reuse_window_sec integer,
    pickup_max_reopens integer DEFAULT 0 NOT NULL,
    geolocation_wkt text,
    has_card_reader boolean DEFAULT false NOT NULL,
    has_kiosk boolean DEFAULT false NOT NULL,
    has_nfc boolean DEFAULT false NOT NULL,
    has_printer boolean DEFAULT false NOT NULL,
    slots_available integer DEFAULT 0 NOT NULL,
    payment_rules jsonb DEFAULT '{"cash_allowed": false, "wallet_allowed": true, "allowed_methods": [], "payment_instruction": "CAPTURE_NOW", "minimum_amount_cents": 0}'::jsonb,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone,
    has_ble boolean DEFAULT false NOT NULL,
    CONSTRAINT ck_lockers_pickup_code_length_range CHECK (((pickup_code_length >= 4) AND (pickup_code_length <= 12))),
    CONSTRAINT ck_lockers_pickup_max_reopens_non_negative CHECK ((pickup_max_reopens >= 0)),
    CONSTRAINT ck_lockers_pickup_reuse_policy CHECK (((pickup_reuse_policy)::text = ANY ((ARRAY['NO_REUSE'::character varying, 'SAME_TOKEN_UNTIL_DEADLINE'::character varying, 'ALLOW_REOPEN_WINDOW'::character varying])::text[]))),
    CONSTRAINT ck_lockers_pickup_reuse_window_sec_non_negative CHECK (((pickup_reuse_window_sec IS NULL) OR (pickup_reuse_window_sec >= 0))),
    CONSTRAINT ck_lockers_slots_available_non_negative CHECK ((slots_available >= 0))
);


ALTER TABLE public.lockers OWNER TO admin;

--
-- Name: login_history; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.login_history (
    id integer NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    user_id integer NOT NULL,
    session_id character varying(254),
    device_id character(36) NOT NULL,
    device_description text NOT NULL,
    ip_address text NOT NULL
);


ALTER TABLE public.login_history OWNER TO admin;

--
-- Name: login_otps; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.login_otps (
    id character varying NOT NULL,
    channel public.otpchannel NOT NULL,
    email character varying,
    phone character varying,
    otp_hash character varying NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    used_at timestamp without time zone,
    attempts integer NOT NULL,
    requested_ip character varying,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.login_otps OWNER TO admin;

--
-- Name: logistics_capacity_allocations; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_capacity_allocations (
    id character varying(36) NOT NULL,
    logistics_partner_id character varying(36) NOT NULL,
    locker_id character varying(64) NOT NULL,
    slot_size character varying(8) NOT NULL,
    reserved_slots integer NOT NULL,
    valid_from date NOT NULL,
    valid_until date,
    priority integer DEFAULT 100 NOT NULL,
    notes text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_lca_date_range CHECK (((valid_until IS NULL) OR (valid_until >= valid_from))),
    CONSTRAINT logistics_capacity_allocations_reserved_slots_check CHECK ((reserved_slots >= 0)),
    CONSTRAINT logistics_capacity_allocations_slot_size_check CHECK (((slot_size)::text = ANY ((ARRAY['S'::character varying, 'M'::character varying, 'L'::character varying, 'XL'::character varying])::text[])))
);


ALTER TABLE public.logistics_capacity_allocations OWNER TO admin;

--
-- Name: logistics_carrier_auth_config; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_carrier_auth_config (
    id character varying(36) NOT NULL,
    carrier_code character varying(20) NOT NULL,
    signature_header character varying(64) DEFAULT 'X-Carrier-Signature'::character varying NOT NULL,
    algorithm character varying(20) DEFAULT 'HMAC_SHA256'::character varying NOT NULL,
    secret_key character varying(256),
    required boolean DEFAULT false NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.logistics_carrier_auth_config OWNER TO admin;

--
-- Name: logistics_carrier_rates; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_carrier_rates (
    id character varying(36) NOT NULL,
    carrier_code character varying(20) NOT NULL,
    origin_zone character varying(10) NOT NULL,
    destination_zone character varying(10) NOT NULL,
    weight_tier_g integer NOT NULL,
    size_tier character varying(8),
    amount_cents integer NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    valid_from date NOT NULL,
    valid_until date,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_lcr_date_range CHECK (((valid_until IS NULL) OR (valid_until >= valid_from))),
    CONSTRAINT logistics_carrier_rates_amount_cents_check CHECK ((amount_cents >= 0)),
    CONSTRAINT logistics_carrier_rates_weight_tier_g_check CHECK ((weight_tier_g > 0))
);


ALTER TABLE public.logistics_carrier_rates OWNER TO admin;

--
-- Name: logistics_carrier_status_map; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_carrier_status_map (
    id character varying(36) NOT NULL,
    carrier_code character varying(20) NOT NULL,
    raw_status character varying(80) NOT NULL,
    normalized_event_code character varying(40) NOT NULL,
    normalized_event_label character varying(120) NOT NULL,
    normalized_outcome character varying(20),
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.logistics_carrier_status_map OWNER TO admin;

--
-- Name: logistics_delivery_attempts; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_delivery_attempts (
    id character varying(36) NOT NULL,
    delivery_id character varying(36) NOT NULL,
    attempt_number integer NOT NULL,
    status character varying(20) NOT NULL,
    attempted_at timestamp with time zone DEFAULT now() NOT NULL,
    failure_reason character varying(160),
    carrier_note text,
    carrier_agent character varying(128),
    proof_url character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.logistics_delivery_attempts OWNER TO admin;

--
-- Name: logistics_manifest_items; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_manifest_items (
    id bigint NOT NULL,
    manifest_id character varying(36) NOT NULL,
    delivery_id character varying(36),
    tracking_code character varying(128) NOT NULL,
    sequence_number integer,
    status character varying(20) DEFAULT 'EXPECTED'::character varying NOT NULL,
    exception_note text,
    processed_at timestamp with time zone,
    CONSTRAINT logistics_manifest_items_status_check CHECK (((status)::text = ANY ((ARRAY['EXPECTED'::character varying, 'STORED'::character varying, 'EXCEPTION'::character varying, 'MISSING'::character varying])::text[])))
);


ALTER TABLE public.logistics_manifest_items OWNER TO admin;

--
-- Name: logistics_manifests; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_manifests (
    id character varying(36) NOT NULL,
    logistics_partner_id character varying(36) NOT NULL,
    locker_id character varying(64) NOT NULL,
    manifest_date date NOT NULL,
    carrier_route_code character varying(64),
    carrier_vehicle_id character varying(64),
    expected_parcel_count integer DEFAULT 0 NOT NULL,
    actual_parcel_count integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    dispatched_at timestamp with time zone,
    delivered_at timestamp with time zone,
    carrier_note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT logistics_manifests_status_check CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'IN_TRANSIT'::character varying, 'DELIVERED'::character varying, 'PARTIAL'::character varying, 'FAILED'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.logistics_manifests OWNER TO admin;

--
-- Name: logistics_partners; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_partners (
    id character varying(36) NOT NULL,
    name character varying(128) NOT NULL,
    code character varying(32) NOT NULL,
    integration_type character varying(30) NOT NULL,
    api_base_url character varying(500),
    tracking_url_template character varying(500),
    auth_type character varying(20),
    credentials_secret_ref character varying(255),
    default_sla_hours integer DEFAULT 72 NOT NULL,
    reminder_hours_before integer DEFAULT 24 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    country character varying(2) DEFAULT 'BR'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.logistics_partners OWNER TO admin;

--
-- Name: logistics_return_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_return_events (
    id character varying(36) NOT NULL,
    return_id character varying(36) NOT NULL,
    from_status character varying(30),
    to_status character varying(30) NOT NULL,
    reason character varying(200),
    changed_by character varying(36),
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.logistics_return_events OWNER TO admin;

--
-- Name: logistics_returns; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_returns (
    id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    reason_code character varying(40) NOT NULL,
    status character varying(30) DEFAULT 'REQUESTED'::character varying NOT NULL,
    notes text,
    created_by character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.logistics_returns OWNER TO admin;

--
-- Name: logistics_shipment_labels; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_shipment_labels (
    id character varying(36) NOT NULL,
    delivery_id character varying(36) NOT NULL,
    carrier_code character varying(20) NOT NULL,
    tracking_code character varying(128) NOT NULL,
    label_format character varying(10) DEFAULT 'PDF'::character varying NOT NULL,
    label_url character varying(500),
    label_payload text DEFAULT '{}'::text NOT NULL,
    status character varying(20) DEFAULT 'GENERATED'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone
);


ALTER TABLE public.logistics_shipment_labels OWNER TO admin;

--
-- Name: logistics_tracking_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.logistics_tracking_events (
    id character varying(36) NOT NULL,
    delivery_id character varying(36) NOT NULL,
    event_code character varying(40) NOT NULL,
    event_label character varying(120) NOT NULL,
    raw_status character varying(80),
    location_city character varying(80),
    location_state character varying(80),
    location_country character varying(2),
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    source character varying(40) DEFAULT 'CARRIER_WEBHOOK'::character varying NOT NULL,
    source_ref character varying(128),
    payload_json text DEFAULT '{}'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.logistics_tracking_events OWNER TO admin;

--
-- Name: marketplace_commissions; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.marketplace_commissions (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    seller_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    order_item_id bigint,
    commission_rate_pct numeric(5,2) NOT NULL,
    commission_amount_cents integer NOT NULL,
    ellan_fee_cents integer NOT NULL,
    payment_gateway_fee_cents integer NOT NULL,
    net_to_seller_cents integer NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    settled_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_mc_status CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'SETTLED'::character varying, 'DISPUTED'::character varying, 'REFUNDED'::character varying])::text[])))
);


ALTER TABLE public.marketplace_commissions OWNER TO admin;

--
-- Name: marketplace_sellers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.marketplace_sellers (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    legal_name character varying(140) NOT NULL,
    trade_name character varying(140),
    tax_id character varying(32) NOT NULL,
    email character varying(128) NOT NULL,
    phone character varying(32),
    website character varying(255),
    status character varying(20) DEFAULT 'PENDING_APPROVAL'::character varying NOT NULL,
    commission_pct numeric(5,2) DEFAULT 5.00 NOT NULL,
    monthly_fee_cents bigint DEFAULT 0 NOT NULL,
    seller_rating numeric(3,2) DEFAULT 0,
    total_sales_cents bigint DEFAULT 0,
    total_orders integer DEFAULT 0,
    joined_at timestamp with time zone DEFAULT now(),
    approved_at timestamp with time zone,
    suspended_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone,
    CONSTRAINT ck_seller_commission CHECK (((commission_pct >= (0)::numeric) AND (commission_pct <= (30)::numeric))),
    CONSTRAINT ck_seller_status CHECK (((status)::text = ANY ((ARRAY['PENDING_APPROVAL'::character varying, 'ACTIVE'::character varying, 'SUSPENDED'::character varying, 'BANNED'::character varying, 'INACTIVE'::character varying])::text[])))
);


ALTER TABLE public.marketplace_sellers OWNER TO admin;

--
-- Name: metabase_database; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.metabase_database (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(254) NOT NULL,
    description text,
    details text NOT NULL,
    engine character varying(254) NOT NULL,
    is_sample boolean DEFAULT false NOT NULL,
    is_full_sync boolean DEFAULT true NOT NULL,
    points_of_interest text,
    caveats text,
    metadata_sync_schedule character varying(254) DEFAULT '0 50 * * * ? *'::character varying NOT NULL,
    cache_field_values_schedule character varying(254) DEFAULT '0 50 0 * * ? *'::character varying NOT NULL,
    timezone character varying(254),
    is_on_demand boolean DEFAULT false NOT NULL,
    auto_run_queries boolean DEFAULT true NOT NULL,
    refingerprint boolean,
    cache_ttl integer,
    initial_sync_status character varying(32) DEFAULT 'complete'::character varying NOT NULL,
    creator_id integer,
    settings text,
    dbms_version text,
    is_audit boolean DEFAULT false NOT NULL
);


ALTER TABLE public.metabase_database OWNER TO admin;

--
-- Name: metabase_field; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.metabase_field (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    name character varying(254) NOT NULL,
    base_type character varying(255) NOT NULL,
    semantic_type character varying(255),
    active boolean DEFAULT true NOT NULL,
    description text,
    preview_display boolean DEFAULT true NOT NULL,
    "position" integer DEFAULT 0 NOT NULL,
    table_id integer NOT NULL,
    parent_id integer,
    display_name character varying(254),
    visibility_type character varying(32) DEFAULT 'normal'::character varying NOT NULL,
    fk_target_field_id integer,
    last_analyzed timestamp with time zone,
    points_of_interest text,
    caveats text,
    fingerprint text,
    fingerprint_version integer DEFAULT 0 NOT NULL,
    database_type text NOT NULL,
    has_field_values text,
    settings text,
    database_position integer DEFAULT 0 NOT NULL,
    custom_position integer DEFAULT 0 NOT NULL,
    effective_type character varying(255),
    coercion_strategy character varying(255),
    nfc_path character varying(254),
    database_required boolean DEFAULT false NOT NULL,
    json_unfolding boolean DEFAULT false NOT NULL,
    database_is_auto_increment boolean DEFAULT false NOT NULL,
    database_indexed boolean,
    database_partitioned boolean
);


ALTER TABLE public.metabase_field OWNER TO admin;

--
-- Name: metabase_fieldvalues; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.metabase_fieldvalues (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    "values" text,
    human_readable_values text,
    field_id integer NOT NULL,
    has_more_values boolean DEFAULT false,
    type character varying(32) DEFAULT 'full'::character varying NOT NULL,
    hash_key text,
    last_used_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.metabase_fieldvalues OWNER TO admin;

--
-- Name: metabase_table; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.metabase_table (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    name character varying(256) NOT NULL,
    description text,
    entity_type character varying(254),
    active boolean NOT NULL,
    db_id integer NOT NULL,
    display_name character varying(256),
    visibility_type character varying(254),
    schema character varying(254),
    points_of_interest text,
    caveats text,
    show_in_getting_started boolean DEFAULT false NOT NULL,
    field_order character varying(254) DEFAULT 'database'::character varying NOT NULL,
    initial_sync_status character varying(32) DEFAULT 'complete'::character varying NOT NULL,
    is_upload boolean DEFAULT false NOT NULL,
    database_require_filter boolean
);


ALTER TABLE public.metabase_table OWNER TO admin;

--
-- Name: metric; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.metric (
    id integer NOT NULL,
    table_id integer NOT NULL,
    creator_id integer NOT NULL,
    name character varying(254) NOT NULL,
    description text,
    archived boolean DEFAULT false NOT NULL,
    definition text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    points_of_interest text,
    caveats text,
    how_is_this_calculated text,
    show_in_getting_started boolean DEFAULT false NOT NULL,
    entity_id character(21)
);


ALTER TABLE public.metric OWNER TO admin;

--
-- Name: metric_important_field; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.metric_important_field (
    id integer NOT NULL,
    metric_id integer NOT NULL,
    field_id integer NOT NULL
);


ALTER TABLE public.metric_important_field OWNER TO admin;

--
-- Name: ml_features_daily; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ml_features_daily (
    id bigint NOT NULL,
    locker_id character varying(36) NOT NULL,
    feature_date date NOT NULL,
    temperature_mean numeric(10,4),
    humidity_mean numeric(10,4),
    battery_min numeric(10,2),
    door_failures_7d integer DEFAULT 0 NOT NULL,
    usage_events_7d integer DEFAULT 0 NOT NULL,
    uptime_hours_7d numeric(10,2) DEFAULT 0 NOT NULL,
    failure_label_7d smallint DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    temperature_avg_70d numeric(10,4),
    humidity_avg_70d numeric(10,4),
    battery_min_70d numeric(10,2),
    door_failures_70d integer,
    usage_events_70d integer,
    uptime_hours_70d numeric(10,2),
    failure_label_70d smallint,
    CONSTRAINT ck_ml_features_failure_label CHECK ((failure_label_7d = ANY (ARRAY[0, 1])))
);


ALTER TABLE public.ml_features_daily OWNER TO admin;

--
-- Name: ml_model_metadata; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ml_model_metadata (
    id bigint NOT NULL,
    model_version character varying(64) NOT NULL,
    trained_at timestamp with time zone DEFAULT now() NOT NULL,
    metrics_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    status character varying(32) DEFAULT 'ACTIVE'::character varying NOT NULL,
    CONSTRAINT ck_ml_model_status CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'STALE'::character varying, 'FAILED'::character varying])::text[])))
);


ALTER TABLE public.ml_model_metadata OWNER TO admin;

--
-- Name: ml_prediction_feedback; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ml_prediction_feedback (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    prediction_id bigint,
    actual_value double precision,
    error_pct numeric(5,2),
    feedback_at timestamp with time zone DEFAULT now(),
    model_performance_status character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.ml_prediction_feedback OWNER TO admin;

--
-- Name: ml_predictions_log; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ml_predictions_log (
    id bigint NOT NULL,
    locker_id character varying(36) NOT NULL,
    predicted_at timestamp with time zone DEFAULT now() NOT NULL,
    failure_probability numeric(8,6) NOT NULL,
    health_score numeric(8,2) NOT NULL,
    model_version character varying(64) NOT NULL
);


ALTER TABLE public.ml_predictions_log OWNER TO admin;

--
-- Name: model_index; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.model_index (
    id integer NOT NULL,
    model_id integer,
    pk_ref text NOT NULL,
    value_ref text NOT NULL,
    schedule text NOT NULL,
    state text NOT NULL,
    indexed_at timestamp with time zone,
    error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    creator_id integer NOT NULL
);


ALTER TABLE public.model_index OWNER TO admin;

--
-- Name: model_index_value; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.model_index_value (
    model_index_id integer,
    model_pk integer NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.model_index_value OWNER TO admin;

--
-- Name: moderation_review; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.moderation_review (
    id integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(255),
    text text,
    moderated_item_id integer NOT NULL,
    moderated_item_type character varying(255) NOT NULL,
    moderator_id integer NOT NULL,
    most_recent boolean NOT NULL
);


ALTER TABLE public.moderation_review OWNER TO admin;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false NOT NULL,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders OWNER TO admin;

--
-- Name: rental_contracts; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.rental_contracts (
    id character varying(36) NOT NULL,
    locker_id character varying(36) NOT NULL,
    slot_label character varying(20) NOT NULL,
    plan_id character varying(36),
    tenant_id character varying(100),
    renter_user_id character varying(36),
    renter_name character varying(255),
    renter_document character varying(32),
    renter_phone character varying(32),
    renter_email character varying(128),
    amount_cents integer NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    billing_cycle character varying(20) NOT NULL,
    next_billing_at timestamp with time zone,
    auto_renew boolean DEFAULT false NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    started_at timestamp with time zone,
    ends_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    ended_at timestamp with time zone,
    access_pin_hash character varying(255),
    access_token_ref character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.rental_contracts OWNER TO admin;

--
-- Name: seller_products; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.seller_products (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    seller_id character varying(36) NOT NULL,
    locker_id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    seller_sku character varying(64),
    price_cents integer NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    max_quantity_per_order integer DEFAULT 10,
    status character varying(20) DEFAULT 'ACTIVE'::character varying NOT NULL,
    priority integer DEFAULT 100,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    deleted_at timestamp with time zone,
    CONSTRAINT ck_seller_product_price CHECK ((price_cents > 0)),
    CONSTRAINT ck_seller_product_quantity CHECK ((quantity >= 0)),
    CONSTRAINT ck_seller_product_status CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'INACTIVE'::character varying, 'OUT_OF_STOCK'::character varying])::text[])))
);


ALTER TABLE public.seller_products OWNER TO admin;

--
-- Name: pickups; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.pickups (
    id character varying NOT NULL,
    order_id character varying NOT NULL,
    channel public.pickupchannel NOT NULL,
    region character varying NOT NULL,
    locker_id character varying,
    machine_id character varying,
    slot character varying,
    operator_id character varying,
    tenant_id character varying,
    site_id character varying,
    status public.pickupstatus NOT NULL,
    lifecycle_stage public.pickuplifecyclestage NOT NULL,
    current_token_id character varying,
    activated_at timestamp with time zone NOT NULL,
    ready_at timestamp with time zone,
    expires_at timestamp with time zone,
    door_opened_at timestamp with time zone,
    item_removed_at timestamp with time zone,
    door_closed_at timestamp with time zone,
    redeemed_at timestamp with time zone,
    redeemed_via public.pickupredeemvia,
    expired_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    cancel_reason character varying,
    correlation_id character varying,
    source_event_id character varying,
    sensor_event_id character varying,
    notes character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    machine_state character varying(50),
    pickup_phase public.pickup_phase,
    evidence_score integer DEFAULT 0,
    evidence_strength character varying(10) DEFAULT 'NONE'::character varying,
    dispute_state public.dispute_state DEFAULT 'NONE'::public.dispute_state NOT NULL,
    verified_at timestamp with time zone,
    verified_by character varying(255),
    disputed_at timestamp with time zone,
    dispute_reason text,
    reconciled_at timestamp with time zone,
    reconciled_by character varying(255),
    aggregate_version bigint DEFAULT 0 NOT NULL,
    fraud_flag boolean DEFAULT false NOT NULL,
    fraud_reason text,
    CONSTRAINT ck_pickups_v2_dispute_requires_disputed_at CHECK (((dispute_state = 'NONE'::public.dispute_state) OR (disputed_at IS NOT NULL))),
    CONSTRAINT ck_pickups_v2_evidence_score_range CHECK (((evidence_score IS NOT NULL) AND ((evidence_score >= 0) AND (evidence_score <= 100)))),
    CONSTRAINT ck_pickups_v2_evidence_strength_consistent CHECK (((evidence_strength)::text = (public.fn_derive_evidence_strength(evidence_score))::text)),
    CONSTRAINT ck_pickups_v2_reconciled_requires_reconciled_at CHECK (((pickup_phase <> 'RECONCILED'::public.pickup_phase) OR (reconciled_at IS NOT NULL))),
    CONSTRAINT ck_pickups_v2_unverified_requires_weak_evidence CHECK (((pickup_phase <> 'COMPLETED_UNVERIFIED'::public.pickup_phase) OR (evidence_score < 80))),
    CONSTRAINT ck_pickups_v2_verified_requires_strong_evidence CHECK (((pickup_phase <> 'COMPLETED_VERIFIED'::public.pickup_phase) OR ((evidence_score >= 80) AND (verified_at IS NOT NULL))))
);


ALTER TABLE public.pickups OWNER TO admin;

--
-- Name: sla_breach_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.sla_breach_events (
    id character varying(36) NOT NULL,
    delivery_id character varying(36),
    return_request_id character varying(36),
    logistics_partner_id character varying(36),
    breach_type character varying(40) NOT NULL,
    severity character varying(10) NOT NULL,
    expected_at timestamp with time zone NOT NULL,
    detected_at timestamp with time zone DEFAULT now() NOT NULL,
    notified_at timestamp with time zone,
    resolved_at timestamp with time zone,
    notes text,
    CONSTRAINT sla_breach_events_breach_type_check CHECK (((breach_type)::text = ANY ((ARRAY['PICKUP_TIMEOUT'::character varying, 'RETURN_TIMEOUT'::character varying, 'NOTIFICATION_FAILURE'::character varying, 'DELIVERY_ATTEMPT_EXCEEDED'::character varying, 'RETURN_TRANSIT_TIMEOUT'::character varying])::text[]))),
    CONSTRAINT sla_breach_events_severity_check CHECK (((severity)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[])))
);


ALTER TABLE public.sla_breach_events OWNER TO admin;

--
-- Name: native_query_snippet; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.native_query_snippet (
    id integer NOT NULL,
    name character varying(254) NOT NULL,
    description text,
    content text NOT NULL,
    creator_id integer NOT NULL,
    archived boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    collection_id integer,
    entity_id character(21)
);


ALTER TABLE public.native_query_snippet OWNER TO admin;

--
-- Name: notification_logs; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.notification_logs (
    id integer NOT NULL,
    user_id character varying(36),
    order_id character varying(64),
    channel character varying(32) NOT NULL,
    template_key character varying(100) NOT NULL,
    destination_masked character varying(255),
    destination_value character varying(255),
    dedupe_key character varying(255),
    provider_name character varying(100),
    provider_message_id character varying(255),
    status character varying(50) NOT NULL,
    attempt_count integer NOT NULL,
    error_message text,
    payload_json json,
    processing_started_at timestamp without time zone,
    last_attempt_at timestamp without time zone,
    next_attempt_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    sent_at timestamp without time zone,
    delivered_at timestamp without time zone,
    failed_at timestamp without time zone,
    pickup_id uuid,
    delivery_id uuid,
    rental_id uuid,
    provider_status character varying(100),
    error_detail text,
    locale character varying(10)
);


ALTER TABLE public.notification_logs OWNER TO admin;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.notifications (
    id character varying(36) NOT NULL,
    channel character varying(16) NOT NULL,
    payload text NOT NULL,
    status character varying(32) NOT NULL,
    attempts integer NOT NULL,
    last_error text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.notifications OWNER TO admin;

--
-- Name: omnichannel_orders; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.omnichannel_orders (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    order_id character varying(36) NOT NULL,
    store_id character varying(36) NOT NULL,
    pickup_type character varying(20) DEFAULT 'STORE_PICKUP'::character varying NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    ready_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_omni_pickup_type CHECK (((pickup_type)::text = ANY ((ARRAY['STORE_PICKUP'::character varying, 'LOCKER_DELIVERY'::character varying, 'HOME_DELIVERY'::character varying])::text[]))),
    CONSTRAINT ck_omni_status CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'PROCESSING'::character varying, 'READY'::character varying, 'PICKED_UP'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.omnichannel_orders OWNER TO admin;

--
-- Name: ops_action_audit; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ops_action_audit (
    id character varying(40) NOT NULL,
    action character varying(120) NOT NULL,
    result character varying(20) NOT NULL,
    correlation_id character varying(80) NOT NULL,
    user_id character varying(36),
    role character varying(80),
    order_id character varying(36),
    error_message text,
    details_json text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ops_action_audit OWNER TO admin;

--
-- Name: ops_outbox_replay_priority_runs; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ops_outbox_replay_priority_runs (
    id character varying(36) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_role character varying(30) DEFAULT 'ops_user'::character varying NOT NULL,
    dry_run boolean DEFAULT true NOT NULL,
    run_after_replay boolean DEFAULT false NOT NULL,
    top_n_groups integer DEFAULT 5 NOT NULL,
    max_items integer DEFAULT 100 NOT NULL,
    total_groups_selected integer DEFAULT 0 NOT NULL,
    total_candidates integer DEFAULT 0 NOT NULL,
    selected_count integer DEFAULT 0 NOT NULL,
    replayed_count integer DEFAULT 0 NOT NULL,
    skipped_count integer DEFAULT 0 NOT NULL,
    filters_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    selected_groups_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    worker_run_json jsonb
);


ALTER TABLE public.ops_outbox_replay_priority_runs OWNER TO admin;

--
-- Name: ops_temp_recon_seed; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ops_temp_recon_seed (
    tag text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    batch_ids jsonb NOT NULL,
    inserted_order_ids jsonb NOT NULL
);


ALTER TABLE public.ops_temp_recon_seed OWNER TO admin;

--
-- Name: ops_temp_recon_seed_levels; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ops_temp_recon_seed_levels (
    tag text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    inserted_order_ids jsonb NOT NULL
);


ALTER TABLE public.ops_temp_recon_seed_levels OWNER TO admin;

--
-- Name: order_fulfillment_tracking; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.order_fulfillment_tracking (
    id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    fulfillment_type character varying(30) DEFAULT 'ECOMMERCE_PARTNER'::character varying NOT NULL,
    partner_id character varying(36),
    status character varying(30) DEFAULT 'PENDING'::character varying NOT NULL,
    last_event_type character varying(50),
    last_outbox_status character varying(20),
    allocated_at timestamp with time zone,
    dispensed_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    returned_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_oft_status CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'ALLOCATED'::character varying, 'DISPENSED'::character varying, 'PICKED_UP'::character varying, 'RETURNED'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.order_fulfillment_tracking OWNER TO admin;

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.order_items (
    id bigint NOT NULL,
    order_id character varying(36) NOT NULL,
    sku_id character varying(255) NOT NULL,
    sku_description text,
    quantity integer DEFAULT 1 NOT NULL,
    unit_amount_cents bigint NOT NULL,
    total_amount_cents bigint NOT NULL,
    slot_preference integer,
    slot_size character varying(20),
    item_status character varying(32) DEFAULT 'PENDING'::character varying NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    ncm character varying(10),
    CONSTRAINT ck_order_items_quantity_positive CHECK ((quantity > 0)),
    CONSTRAINT ck_order_items_slot_preference_positive CHECK (((slot_preference IS NULL) OR (slot_preference > 0))),
    CONSTRAINT ck_order_items_total_amount_non_negative CHECK ((total_amount_cents >= 0)),
    CONSTRAINT ck_order_items_total_matches_quantity CHECK ((total_amount_cents = (quantity * unit_amount_cents))),
    CONSTRAINT ck_order_items_unit_amount_non_negative CHECK ((unit_amount_cents >= 0))
);


ALTER TABLE public.order_items OWNER TO admin;

--
-- Name: orders_partitioned; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_partitioned (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
)
PARTITION BY RANGE (created_at);


ALTER TABLE public.orders_partitioned OWNER TO admin;

--
-- Name: orders_2025_06; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2025_06 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2025_06 OWNER TO admin;

--
-- Name: orders_2025_07; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2025_07 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2025_07 OWNER TO admin;

--
-- Name: orders_2025_08; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2025_08 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2025_08 OWNER TO admin;

--
-- Name: orders_2025_09; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2025_09 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2025_09 OWNER TO admin;

--
-- Name: orders_2025_10; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2025_10 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2025_10 OWNER TO admin;

--
-- Name: orders_2025_11; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2025_11 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2025_11 OWNER TO admin;

--
-- Name: orders_2025_12; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2025_12 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2025_12 OWNER TO admin;

--
-- Name: orders_2026_01; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2026_01 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2026_01 OWNER TO admin;

--
-- Name: orders_2026_02; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2026_02 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2026_02 OWNER TO admin;

--
-- Name: orders_2026_03; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2026_03 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2026_03 OWNER TO admin;

--
-- Name: orders_2026_04; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2026_04 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2026_04 OWNER TO admin;

--
-- Name: orders_2026_05; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.orders_2026_05 (
    id character varying NOT NULL,
    user_id character varying,
    channel public.orderchannel NOT NULL,
    region character varying NOT NULL,
    totem_id character varying NOT NULL,
    sku_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    status public.orderstatus NOT NULL,
    gateway_transaction_id character varying,
    payment_method public.paymentmethod,
    payment_status public.paymentstatus NOT NULL,
    card_type public.cardtype,
    payment_updated_at timestamp with time zone,
    paid_at timestamp with time zone,
    pickup_deadline_at timestamp with time zone,
    picked_up_at timestamp with time zone,
    guest_session_id character varying,
    public_access_token_hash character varying,
    receipt_email character varying,
    receipt_phone character varying,
    consent_marketing integer NOT NULL,
    guest_phone character varying,
    guest_email character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying,
    site_id character varying(100),
    tenant_id character varying(100),
    ecommerce_partner_id character varying(100),
    partner_order_ref character varying(255),
    sku_description text,
    slot_size character varying(20),
    card_last4 character varying(8),
    card_brand character varying(50),
    installments integer,
    guest_name character varying(255),
    consent_analytics boolean DEFAULT false,
    cancelled_at timestamp with time zone,
    cancel_reason character varying(255),
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    payment_interface character varying(32),
    wallet_provider character varying(64),
    device_id character varying(128),
    ip_address character varying(64),
    user_agent character varying(500),
    idempotency_key character varying(255),
    order_metadata jsonb,
    slot integer,
    allocation_id character varying,
    allocation_expires_at timestamp with time zone,
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);


ALTER TABLE public.orders_2026_05 OWNER TO admin;

--
-- Name: parameter_card; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.parameter_card (
    id integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    card_id integer NOT NULL,
    parameterized_object_type character varying(32) NOT NULL,
    parameterized_object_id integer NOT NULL,
    parameter_id character varying(36) NOT NULL
);


ALTER TABLE public.parameter_card OWNER TO admin;

--
-- Name: partner_api_keys; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_api_keys (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    key_prefix character varying(16) NOT NULL,
    key_hash character varying(128) NOT NULL,
    label character varying(64),
    scopes_json text DEFAULT '[]'::text NOT NULL,
    expires_at timestamp with time zone,
    last_used_at timestamp with time zone,
    revoked_at timestamp with time zone,
    created_by character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.partner_api_keys OWNER TO admin;

--
-- Name: partner_b2b_invoices; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_b2b_invoices (
    id character varying(36) NOT NULL,
    cycle_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    invoice_number character varying(50),
    invoice_series character varying(20),
    access_key character varying(140),
    document_type character varying(30) DEFAULT 'INVOICE'::character varying NOT NULL,
    amount_cents bigint NOT NULL,
    tax_cents bigint DEFAULT 0 NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    timezone character varying(64) DEFAULT 'UTC'::character varying NOT NULL,
    due_date date,
    payment_method character varying(30),
    emitter_tax_id character varying(32),
    emitter_name character varying(140),
    taker_tax_id character varying(32),
    taker_name character varying(140),
    taker_email character varying(128),
    status character varying(20) DEFAULT 'DRAFT'::character varying NOT NULL,
    dedupe_key character varying(180),
    external_provider_ref character varying(140),
    issued_at timestamp with time zone,
    sent_at timestamp with time zone,
    viewed_at timestamp with time zone,
    paid_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    cancel_reason text,
    pdf_url character varying(500),
    xml_content jsonb,
    government_response jsonb,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pbi_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_pbi_document_type CHECK (((document_type)::text = ANY ((ARRAY['INVOICE'::character varying, 'NFS_E'::character varying, 'NFE_55'::character varying, 'NFC_E_65'::character varying, 'BOLETO'::character varying, 'INVOICE_PDF'::character varying])::text[]))),
    CONSTRAINT ck_pbi_status CHECK (((status)::text = ANY ((ARRAY['DRAFT'::character varying, 'ISSUED'::character varying, 'SENT'::character varying, 'VIEWED'::character varying, 'PAID'::character varying, 'OVERDUE'::character varying, 'DISPUTED'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.partner_b2b_invoices OWNER TO admin;

--
-- Name: partner_billing_cycles; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_billing_cycles (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    partner_type character varying(20) NOT NULL,
    billing_plan_id character varying(36) NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    period_timezone character varying(64) DEFAULT 'UTC'::character varying NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    total_deliveries integer DEFAULT 0 NOT NULL,
    total_pickups integer DEFAULT 0 NOT NULL,
    total_slot_days numeric(10,2) DEFAULT 0 NOT NULL,
    total_overdue_days numeric(10,2) DEFAULT 0 NOT NULL,
    base_fee_cents bigint DEFAULT 0 NOT NULL,
    usage_fee_cents bigint DEFAULT 0 NOT NULL,
    overage_fee_cents bigint DEFAULT 0 NOT NULL,
    sla_penalty_cents bigint DEFAULT 0 NOT NULL,
    discount_cents bigint DEFAULT 0 NOT NULL,
    tax_cents bigint DEFAULT 0 NOT NULL,
    total_amount_cents bigint DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'OPEN'::character varying NOT NULL,
    dedupe_key character varying(160),
    computed_at timestamp with time zone,
    approved_at timestamp with time zone,
    approved_by character varying(36),
    invoiced_at timestamp with time zone,
    paid_at timestamp with time zone,
    payment_ref character varying(128),
    dispute_reason text,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pbc_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_pbc_status CHECK (((status)::text = ANY ((ARRAY['OPEN'::character varying, 'COMPUTING'::character varying, 'REVIEW'::character varying, 'APPROVED'::character varying, 'INVOICED'::character varying, 'PAID'::character varying, 'DISPUTED'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.partner_billing_cycles OWNER TO admin;

--
-- Name: partner_billing_line_items; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_billing_line_items (
    id bigint NOT NULL,
    cycle_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    line_type character varying(40) NOT NULL,
    description character varying(255) NOT NULL,
    reference_id character varying(36),
    reference_type character varying(40),
    reference_source character varying(50) DEFAULT 'billing_engine'::character varying NOT NULL,
    dedupe_key character varying(180),
    quantity numeric(12,4) DEFAULT 1 NOT NULL,
    unit_price_cents bigint NOT NULL,
    total_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    tax_code character varying(32),
    tax_rate_pct numeric(8,4),
    period_from timestamp with time zone,
    period_to timestamp with time zone,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pbli_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_pbli_line_type CHECK (((line_type)::text = ANY ((ARRAY['BASE_FEE'::character varying, 'DELIVERY_FEE'::character varying, 'PICKUP_FEE'::character varying, 'STORAGE_DAY_FEE'::character varying, 'OVERAGE_FEE'::character varying, 'SLA_PENALTY'::character varying, 'TAX'::character varying, 'DISCOUNT'::character varying, 'CREDIT_NOTE'::character varying, 'ADJUSTMENT'::character varying])::text[])))
);


ALTER TABLE public.partner_billing_line_items OWNER TO admin;

--
-- Name: partner_billing_plans; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_billing_plans (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    plan_name character varying(128) NOT NULL,
    billing_model character varying(30) NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    timezone character varying(64) DEFAULT 'UTC'::character varying NOT NULL,
    monthly_fee_cents bigint,
    fee_per_delivery_cents bigint,
    fee_per_pickup_cents bigint,
    fee_per_day_stored_cents bigint,
    free_storage_hours integer DEFAULT 72 NOT NULL,
    revenue_share_pct numeric(6,4),
    min_monthly_fee_cents bigint,
    included_deliveries_month integer,
    overage_fee_cents bigint,
    valid_from date NOT NULL,
    valid_until date,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pbp_billing_model CHECK (((billing_model)::text = ANY ((ARRAY['FLAT_MONTHLY'::character varying, 'PER_USE'::character varying, 'HYBRID'::character varying, 'REVENUE_SHARE'::character varying, 'FREE_TIER'::character varying])::text[]))),
    CONSTRAINT ck_pbp_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_pbp_partner_type CHECK (((partner_type)::text = ANY ((ARRAY['ECOMMERCE'::character varying, 'LOGISTICS'::character varying, 'LOCAL_MERCHANT'::character varying, 'CARRIER'::character varying, 'ENTERPRISE'::character varying])::text[]))),
    CONSTRAINT ck_pbp_revenue_share_pct CHECK (((revenue_share_pct IS NULL) OR ((revenue_share_pct >= (0)::numeric) AND (revenue_share_pct <= (1)::numeric))))
);


ALTER TABLE public.partner_billing_plans OWNER TO admin;

--
-- Name: partner_commission_structure; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_commission_structure (
    id uuid NOT NULL,
    partner_id character varying(36),
    commission_percentage numeric(5,2),
    revenue_threshold_cents bigint,
    effective_from date
);


ALTER TABLE public.partner_commission_structure OWNER TO admin;

--
-- Name: partner_contacts; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_contacts (
    id character varying(36) NOT NULL,
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


ALTER TABLE public.partner_contacts OWNER TO admin;

--
-- Name: partner_credit_notes; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_credit_notes (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    original_invoice_id character varying(36),
    cycle_id character varying(36),
    reason_code character varying(40) NOT NULL,
    description text NOT NULL,
    amount_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    country_code character varying(2),
    jurisdiction_code character varying(32),
    timezone character varying(64) DEFAULT 'UTC'::character varying NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    dedupe_key character varying(180),
    approved_by character varying(36),
    approved_at timestamp with time zone,
    applied_to_cycle_id character varying(36),
    applied_at timestamp with time zone,
    expires_at timestamp with time zone,
    dispute_ref character varying(140),
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pcn_country_code CHECK (((country_code IS NULL) OR (length((country_code)::text) = 2))),
    CONSTRAINT ck_pcn_reason_code CHECK (((reason_code)::text = ANY ((ARRAY['SLA_BREACH'::character varying, 'HARDWARE_DOWNTIME'::character varying, 'COMMERCIAL_ADJUSTMENT'::character varying, 'DUPLICATE'::character varying, 'TAX_ADJUSTMENT'::character varying, 'OTHER'::character varying])::text[]))),
    CONSTRAINT ck_pcn_status CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'APPROVED'::character varying, 'APPLIED'::character varying, 'REFUNDED'::character varying, 'EXPIRED'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.partner_credit_notes OWNER TO admin;

--
-- Name: partner_integration_health; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_integration_health (
    id bigint NOT NULL,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    endpoint_url character varying(500),
    checked_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(20) NOT NULL,
    latency_ms integer,
    http_status integer,
    error_message character varying(500)
);


ALTER TABLE public.partner_integration_health OWNER TO admin;

--
-- Name: partner_order_events_outbox; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_order_events_outbox (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    event_type character varying(50) NOT NULL,
    payload_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    api_version character varying(10) DEFAULT 'v1'::character varying NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    max_attempts integer DEFAULT 5 NOT NULL,
    next_retry_at timestamp with time zone,
    last_error text,
    delivered_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_poeo_event_type CHECK (((event_type)::text = ANY ((ARRAY['ORDER_CREATED'::character varying, 'ORDER_PAID'::character varying, 'ORDER_DISPENSED'::character varying, 'ORDER_PICKED_UP'::character varying, 'ORDER_EXPIRED'::character varying, 'ORDER_CANCELLED'::character varying, 'ORDER_REFUNDED'::character varying, 'DELIVERY_STORED'::character varying, 'DELIVERY_PICKED_UP'::character varying])::text[]))),
    CONSTRAINT ck_poeo_status CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'DELIVERED'::character varying, 'FAILED'::character varying, 'DEAD_LETTER'::character varying, 'SKIPPED'::character varying])::text[])))
);


ALTER TABLE public.partner_order_events_outbox OWNER TO admin;

--
-- Name: partner_payment_holds; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_payment_holds (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    invoice_id character varying(36) NOT NULL,
    hold_amount_cents bigint NOT NULL,
    release_schedule character varying(30) DEFAULT 'AFTER_15_DAYS'::character varying NOT NULL,
    released_at timestamp with time zone,
    released_amount_cents bigint,
    dispute_opened_at timestamp with time zone,
    dispute_resolved_at timestamp with time zone,
    dispute_result character varying(20),
    status character varying(20) DEFAULT 'HELD'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pph_dispute_result CHECK (((dispute_result IS NULL) OR ((dispute_result)::text = ANY ((ARRAY['IN_FAVOR_ELLAN'::character varying, 'IN_FAVOR_PARTNER'::character varying])::text[])))),
    CONSTRAINT ck_pph_release_schedule CHECK (((release_schedule)::text = ANY ((ARRAY['AFTER_15_DAYS'::character varying, 'AFTER_30_DAYS'::character varying, 'UPON_DISPUTE_RESOLUTION'::character varying])::text[]))),
    CONSTRAINT ck_pph_status CHECK (((status)::text = ANY ((ARRAY['HELD'::character varying, 'RELEASED'::character varying, 'DISPUTED'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.partner_payment_holds OWNER TO admin;

--
-- Name: partner_performance_metrics; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_performance_metrics (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    period_month character(7) NOT NULL,
    total_orders integer DEFAULT 0 NOT NULL,
    on_time_pickup_pct numeric(5,2),
    return_rate_pct numeric(5,2),
    avg_pickup_hours numeric(6,2),
    sla_compliance_pct numeric(5,2),
    webhook_success_rate numeric(5,2),
    generated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.partner_performance_metrics OWNER TO admin;

--
-- Name: partner_service_areas; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_service_areas (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) DEFAULT 'ECOMMERCE'::character varying NOT NULL,
    locker_id character varying(36) NOT NULL,
    priority integer DEFAULT 100 NOT NULL,
    exclusive boolean DEFAULT false NOT NULL,
    valid_from date NOT NULL,
    valid_until date,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.partner_service_areas OWNER TO admin;

--
-- Name: partner_settlement_batches; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_settlement_batches (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) DEFAULT 'ECOMMERCE'::character varying NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    total_orders integer DEFAULT 0 NOT NULL,
    gross_revenue_cents bigint DEFAULT 0 NOT NULL,
    revenue_share_pct numeric(6,4) NOT NULL,
    revenue_share_cents bigint DEFAULT 0 NOT NULL,
    fees_cents bigint DEFAULT 0 NOT NULL,
    net_amount_cents bigint DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'DRAFT'::character varying NOT NULL,
    settled_at timestamp with time zone,
    settlement_ref character varying(128),
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_psb_status CHECK (((status)::text = ANY ((ARRAY['DRAFT'::character varying, 'APPROVED'::character varying, 'PAID'::character varying, 'DISPUTED'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.partner_settlement_batches OWNER TO admin;

--
-- Name: partner_settlement_items; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_settlement_items (
    id bigint NOT NULL,
    batch_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    order_date timestamp with time zone NOT NULL,
    gross_cents bigint NOT NULL,
    share_pct numeric(6,4) NOT NULL,
    share_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL
);


ALTER TABLE public.partner_settlement_items OWNER TO admin;

--
-- Name: partner_sla_agreements; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_sla_agreements (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    country character varying(2) DEFAULT 'BR'::character varying NOT NULL,
    product_category character varying(64),
    sla_pickup_hours integer DEFAULT 72 NOT NULL,
    sla_return_hours integer DEFAULT 24 NOT NULL,
    penalty_pct numeric(5,2) DEFAULT 0,
    valid_from date NOT NULL,
    valid_until date,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.partner_sla_agreements OWNER TO admin;

--
-- Name: partner_status_history; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_status_history (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    from_status character varying(30),
    to_status character varying(30) NOT NULL,
    reason text,
    changed_by character varying(36),
    changed_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.partner_status_history OWNER TO admin;

--
-- Name: partner_stores; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_stores (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    name character varying(128) NOT NULL,
    legal_name character varying(140),
    tax_id character varying(32),
    address_line character varying(255) NOT NULL,
    city character varying(100) NOT NULL,
    state character varying(50) NOT NULL,
    postal_code character varying(20) NOT NULL,
    phone character varying(32),
    email character varying(128),
    latitude numeric(10,8),
    longitude numeric(11,8),
    operating_hours jsonb,
    commission_pct numeric(5,2) DEFAULT 5.00,
    active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_store_commission CHECK (((commission_pct >= (0)::numeric) AND (commission_pct <= (30)::numeric)))
);


ALTER TABLE public.partner_stores OWNER TO admin;

--
-- Name: partner_webhook_deliveries; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_webhook_deliveries (
    id character varying(36) NOT NULL,
    endpoint_id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    event_type character varying(80) NOT NULL,
    payload_json text DEFAULT '{}'::text NOT NULL,
    payload_hash character varying(64),
    http_status integer,
    attempt_count integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    last_error text,
    next_retry_at timestamp with time zone,
    processing_started_at timestamp with time zone,
    delivered_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.partner_webhook_deliveries OWNER TO admin;

--
-- Name: partner_webhook_endpoints; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.partner_webhook_endpoints (
    id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    url character varying(500) NOT NULL,
    secret_hash character varying(128) NOT NULL,
    secret_key character varying(256),
    events_json text DEFAULT '["*"]'::text NOT NULL,
    api_version character varying(10) DEFAULT 'v1'::character varying NOT NULL,
    retry_policy text DEFAULT '{}'::text NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.partner_webhook_endpoints OWNER TO admin;

--
-- Name: payment_gateway_device_registry; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.payment_gateway_device_registry (
    device_hash text NOT NULL,
    version text NOT NULL,
    first_seen_at_epoch bigint NOT NULL,
    last_seen_at_epoch bigint NOT NULL,
    seen_count integer DEFAULT 1 NOT NULL,
    region_code character varying(20),
    locker_id character varying(120),
    flags_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pg_gateway_device_seen_count_positive CHECK ((seen_count >= 1))
);


ALTER TABLE public.payment_gateway_device_registry OWNER TO admin;

--
-- Name: payment_gateway_idempotency_keys; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.payment_gateway_idempotency_keys (
    id text NOT NULL,
    endpoint text NOT NULL,
    idem_key text NOT NULL,
    payload_hash text NOT NULL,
    response_blob jsonb DEFAULT '{}'::jsonb NOT NULL,
    status text NOT NULL,
    region_code character varying(20),
    sales_channel character varying(50),
    request_fingerprint text,
    created_at_epoch bigint NOT NULL,
    expires_at_epoch bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pg_gateway_idem_expires_after_create CHECK ((expires_at_epoch >= created_at_epoch))
);


ALTER TABLE public.payment_gateway_idempotency_keys OWNER TO admin;

--
-- Name: payment_gateway_risk_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.payment_gateway_risk_events (
    id text NOT NULL,
    request_id text NOT NULL,
    event_type text NOT NULL,
    decision text NOT NULL,
    score integer NOT NULL,
    policy_id text NOT NULL,
    region_code character varying(20) NOT NULL,
    locker_id character varying(120) NOT NULL,
    slot integer NOT NULL,
    audit_event_id text NOT NULL,
    reasons_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    signals_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at_epoch bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pg_gateway_risk_decision_values CHECK ((upper(decision) = ANY (ARRAY['ALLOW'::text, 'BLOCK'::text, 'CHALLENGE'::text]))),
    CONSTRAINT ck_pg_gateway_risk_score_range CHECK (((score >= 0) AND (score <= 100))),
    CONSTRAINT ck_pg_gateway_risk_slot_positive CHECK ((slot > 0))
);


ALTER TABLE public.payment_gateway_risk_events OWNER TO admin;

--
-- Name: payment_instructions; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.payment_instructions (
    id character varying(36) NOT NULL,
    order_id character varying NOT NULL,
    instruction_type character varying(50) NOT NULL,
    amount_cents integer NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    status character varying(30) DEFAULT 'PENDING'::character varying NOT NULL,
    expires_at timestamp with time zone,
    qr_code text,
    qr_code_text text,
    barcode character varying(255),
    digitable_line text,
    authorization_code character varying(100),
    capture_amount_cents integer,
    captured_at timestamp with time zone,
    payment_token character varying(255),
    customer_payment_method_id character varying(36),
    wallet_provider character varying(50),
    wallet_transaction_id character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    redirect_url text,
    provider_payment_id text,
    provider_name text
);


ALTER TABLE public.payment_instructions OWNER TO admin;

--
-- Name: payment_interface_catalog; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.payment_interface_catalog (
    id bigint NOT NULL,
    code character varying(80) NOT NULL,
    name character varying(120) NOT NULL,
    interface_type character varying(60),
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    requires_hw boolean DEFAULT false NOT NULL
);


ALTER TABLE public.payment_interface_catalog OWNER TO admin;

--
-- Name: payment_method_catalog; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.payment_method_catalog (
    id bigint NOT NULL,
    code character varying(80) NOT NULL,
    name character varying(120) NOT NULL,
    family character varying(80),
    is_wallet boolean DEFAULT false NOT NULL,
    is_card boolean DEFAULT false NOT NULL,
    is_bnpl boolean DEFAULT false NOT NULL,
    is_cash_like boolean DEFAULT false NOT NULL,
    is_bank_transfer boolean DEFAULT false NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_instant boolean DEFAULT false NOT NULL
);


ALTER TABLE public.payment_method_catalog OWNER TO admin;

--
-- Name: payment_method_ui_alias; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.payment_method_ui_alias (
    id text NOT NULL,
    ui_code text NOT NULL,
    canonical_method_code text NOT NULL,
    default_payment_interface_code text,
    default_wallet_provider_code text,
    requires_customer_phone boolean DEFAULT false NOT NULL,
    requires_wallet_provider boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.payment_method_ui_alias OWNER TO admin;

--
-- Name: payment_splits; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.payment_splits (
    id character varying(36) NOT NULL,
    order_id character varying NOT NULL,
    recipient_type character varying(30) NOT NULL,
    recipient_id character varying NOT NULL,
    amount_cents integer NOT NULL,
    percentage numeric(5,2),
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    settled_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.payment_splits OWNER TO admin;

--
-- Name: payment_transactions; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.payment_transactions (
    id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    gateway character varying(50) NOT NULL,
    gateway_transaction_id character varying(128),
    gateway_idempotency_key character varying(128),
    amount_cents integer NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    payment_method character varying(30) NOT NULL,
    card_brand character varying(20),
    card_last4 character varying(4),
    card_type character varying(10),
    installments integer DEFAULT 1 NOT NULL,
    nsu character varying(50),
    authorization_code character varying(50),
    status character varying(20) DEFAULT 'INITIATED'::character varying NOT NULL,
    error_code character varying(100),
    error_message text,
    raw_request_json text,
    raw_response_json text,
    initiated_at timestamp with time zone DEFAULT now() NOT NULL,
    approved_at timestamp with time zone,
    settled_at timestamp with time zone,
    refunded_at timestamp with time zone,
    refund_reason character varying(255),
    refund_amount_cents integer,
    chargeback_at timestamp with time zone,
    chargeback_reason character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    gateway_webhook_received_at timestamp with time zone,
    gateway_webhook_payload jsonb,
    acquirer_name character varying(100),
    acquirer_message text,
    tid character varying(50),
    arqc character varying(50),
    nsu_sitef character varying(50),
    reconciliation_status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    reconciliation_batch_id character varying(100),
    gateway_fee_cents integer DEFAULT 0,
    installment_fee_cents integer DEFAULT 0,
    net_amount_cents integer
);


ALTER TABLE public.payment_transactions OWNER TO admin;

--
-- Name: permissions; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.permissions (
    id integer NOT NULL,
    object character varying(254) NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.permissions OWNER TO admin;

--
-- Name: permissions_group; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.permissions_group (
    id integer NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE public.permissions_group OWNER TO admin;

--
-- Name: permissions_group_membership; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.permissions_group_membership (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL,
    is_group_manager boolean DEFAULT false NOT NULL
);


ALTER TABLE public.permissions_group_membership OWNER TO admin;

--
-- Name: permissions_revision; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.permissions_revision (
    id integer NOT NULL,
    before text NOT NULL,
    after text NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    remark text
);


ALTER TABLE public.permissions_revision OWNER TO admin;

--
-- Name: persisted_info; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.persisted_info (
    id integer NOT NULL,
    database_id integer NOT NULL,
    card_id integer NOT NULL,
    question_slug text NOT NULL,
    table_name text NOT NULL,
    definition text,
    query_hash text,
    active boolean DEFAULT false NOT NULL,
    state text NOT NULL,
    refresh_begin timestamp with time zone NOT NULL,
    refresh_end timestamp with time zone,
    state_change_at timestamp with time zone,
    error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    creator_id integer
);


ALTER TABLE public.persisted_info OWNER TO admin;

--
-- Name: pickup_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.pickup_events (
    id bigint NOT NULL,
    pickup_id character varying NOT NULL,
    version bigint NOT NULL,
    event_type character varying(100) NOT NULL,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    source character varying(100) DEFAULT 'migration'::character varying NOT NULL,
    idempotency_key character varying(255),
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.pickup_events OWNER TO admin;

--
-- Name: pickup_tokens; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.pickup_tokens (
    id character varying NOT NULL,
    pickup_id character varying NOT NULL,
    token_hash character varying NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    manual_code character varying,
    manual_code_encrypted character varying
);


ALTER TABLE public.pickup_tokens OWNER TO admin;

--
-- Name: price_history; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.price_history (
    id bigint NOT NULL,
    product_id character varying(255) NOT NULL,
    locker_id character varying(36),
    old_price_cents integer NOT NULL,
    new_price_cents integer NOT NULL,
    rule_id character varying(36),
    reason character varying(100),
    changed_at timestamp with time zone DEFAULT now(),
    changed_by character varying(36)
);


ALTER TABLE public.price_history OWNER TO admin;

--
-- Name: pricing_rules; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.pricing_rules (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    region character varying(20),
    locker_id character varying(36),
    product_category character varying(64),
    valid_from timestamp with time zone NOT NULL,
    valid_until timestamp with time zone,
    base_amount_cents bigint NOT NULL,
    discount_pct numeric(5,2) DEFAULT 0.00,
    min_amount_cents bigint,
    max_amount_cents bigint,
    is_active boolean DEFAULT true NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pricing_valid_range CHECK (((valid_until IS NULL) OR (valid_until > valid_from)))
);


ALTER TABLE public.pricing_rules OWNER TO admin;

--
-- Name: privacy_consents; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.privacy_consents (
    id character varying(36) NOT NULL,
    user_id character varying(36),
    guest_identifier character varying(255),
    consent_type character varying(50) NOT NULL,
    granted boolean NOT NULL,
    channel character varying(20),
    ip_address character varying(64),
    user_agent character varying(500),
    policy_version character varying(20),
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.privacy_consents OWNER TO admin;

--
-- Name: product_barcodes; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_barcodes (
    id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    barcode_type character varying(20) NOT NULL,
    barcode_value character varying(128) NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT product_barcodes_barcode_type_check CHECK (((barcode_type)::text = ANY ((ARRAY['EAN13'::character varying, 'EAN8'::character varying, 'GTIN14'::character varying, 'QR'::character varying, 'CODE128'::character varying, 'DATAMATRIX'::character varying])::text[])))
);


ALTER TABLE public.product_barcodes OWNER TO admin;

--
-- Name: product_bundle_items; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_bundle_items (
    id bigint NOT NULL,
    bundle_id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    quantity integer DEFAULT 1 NOT NULL,
    unit_price_cents integer,
    sort_order integer DEFAULT 0 NOT NULL,
    CONSTRAINT ck_pbi_quantity_positive CHECK ((quantity > 0))
);


ALTER TABLE public.product_bundle_items OWNER TO admin;

--
-- Name: product_bundles; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_bundles (
    id character varying(36) NOT NULL,
    name character varying(128) NOT NULL,
    code character varying(32) NOT NULL,
    description text,
    amount_cents integer NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    bundle_type character varying(20) DEFAULT 'FIXED'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    valid_from timestamp with time zone,
    valid_until timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pb_bundle_type CHECK (((bundle_type)::text = ANY ((ARRAY['FIXED'::character varying, 'CONFIGURABLE'::character varying])::text[])))
);


ALTER TABLE public.product_bundles OWNER TO admin;

--
-- Name: product_categories; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_categories (
    id character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    description text,
    parent_category character varying(64),
    default_temperature_zone character varying(32) DEFAULT 'AMBIENT'::character varying NOT NULL,
    default_security_level character varying(32) DEFAULT 'STANDARD'::character varying NOT NULL,
    is_hazardous boolean DEFAULT false NOT NULL,
    requires_age_verification boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    requires_id boolean DEFAULT false,
    requires_signature boolean DEFAULT false,
    max_weight_g integer,
    max_width_mm integer,
    max_height_mm integer,
    max_depth_mm integer
);


ALTER TABLE public.product_categories OWNER TO admin;

--
-- Name: product_cogs; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_cogs (
    id uuid NOT NULL,
    product_id character varying(255),
    cogs_per_unit_cents bigint,
    supplier_id uuid,
    effective_from date,
    effective_to date
);


ALTER TABLE public.product_cogs OWNER TO admin;

--
-- Name: product_fiscal_config; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_fiscal_config (
    sku_id character varying(255) NOT NULL,
    ncm_code character varying(10),
    cest character varying(9),
    icms_cst character varying(3),
    pis_cst character varying(2),
    cofins_cst character varying(2),
    iva_category character varying(20),
    is_active boolean NOT NULL,
    unit_of_measure character varying(6) DEFAULT 'UN'::character varying NOT NULL,
    origin_type character(1) DEFAULT '0'::bpchar NOT NULL,
    cfop character varying(5),
    tax_rate_pct numeric(7,4),
    is_service boolean DEFAULT false NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.product_fiscal_config OWNER TO admin;

--
-- Name: product_inventory; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_inventory (
    id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    locker_id character varying(64) NOT NULL,
    slot_size character varying(8) NOT NULL,
    quantity_on_hand integer DEFAULT 0 NOT NULL,
    quantity_reserved integer DEFAULT 0 NOT NULL,
    quantity_available integer GENERATED ALWAYS AS ((quantity_on_hand - quantity_reserved)) STORED,
    reorder_point integer DEFAULT 0 NOT NULL,
    reorder_quantity integer DEFAULT 0 NOT NULL,
    last_counted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pi_non_negative CHECK (((quantity_on_hand >= 0) AND (quantity_reserved >= 0))),
    CONSTRAINT ck_pi_reserved_leq_hand CHECK ((quantity_reserved <= quantity_on_hand))
);


ALTER TABLE public.product_inventory OWNER TO admin;

--
-- Name: product_locker_compatibility; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_locker_compatibility (
    id uuid NOT NULL,
    product_id character varying(255) NOT NULL,
    locker_type_id bigint NOT NULL,
    is_compatible boolean DEFAULT true,
    rejection_reason character varying(255),
    rule_version integer,
    effective_from date,
    effective_to date,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.product_locker_compatibility OWNER TO admin;

--
-- Name: product_locker_configs; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_locker_configs (
    id bigint NOT NULL,
    locker_id character varying(64) NOT NULL,
    category character varying(64) NOT NULL,
    subcategory character varying(64),
    allowed boolean DEFAULT true NOT NULL,
    temperature_zone character varying(32) DEFAULT 'ANY'::character varying NOT NULL,
    min_value double precision,
    max_value double precision,
    max_weight_kg double precision,
    max_width_cm integer,
    max_height_cm integer,
    max_depth_cm integer,
    requires_signature boolean DEFAULT false NOT NULL,
    requires_id boolean DEFAULT false NOT NULL,
    is_fragile boolean DEFAULT false NOT NULL,
    is_hazardous boolean DEFAULT false NOT NULL,
    priority integer DEFAULT 100 NOT NULL,
    notes text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    min_value_cents bigint,
    max_value_cents bigint,
    max_weight_g integer,
    max_width_mm integer,
    max_height_mm integer,
    max_depth_mm integer,
    requires_id_check boolean DEFAULT false NOT NULL
);


ALTER TABLE public.product_locker_configs OWNER TO admin;

--
-- Name: product_media; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_media (
    id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    media_type character varying(10) NOT NULL,
    url character varying(500) NOT NULL,
    cdn_key character varying(255),
    alt_text character varying(255),
    sort_order integer DEFAULT 0 NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT product_media_media_type_check CHECK (((media_type)::text = ANY ((ARRAY['IMAGE'::character varying, 'VIDEO'::character varying, 'PDF'::character varying, '3D'::character varying])::text[])))
);


ALTER TABLE public.product_media OWNER TO admin;

--
-- Name: product_recommendations; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_recommendations (
    id bigint NOT NULL,
    user_id character varying(36),
    locker_id character varying(36),
    product_id character varying(255) NOT NULL,
    score numeric(5,4) NOT NULL,
    context character varying(50),
    generated_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone DEFAULT (now() + '24:00:00'::interval),
    CONSTRAINT ck_recommendation_score CHECK (((score >= (0)::numeric) AND (score <= (1)::numeric)))
);


ALTER TABLE public.product_recommendations OWNER TO admin;

--
-- Name: product_status_history; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.product_status_history (
    id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    from_status character varying(30),
    to_status character varying(30) NOT NULL,
    reason text,
    changed_by character varying(36),
    changed_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.product_status_history OWNER TO admin;

--
-- Name: products; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.products (
    id character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    amount_cents integer NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    category_id character varying(64),
    width_mm integer,
    height_mm integer,
    depth_mm integer,
    weight_g integer,
    is_active boolean DEFAULT true NOT NULL,
    requires_age_verification boolean DEFAULT false NOT NULL,
    requires_id_check boolean DEFAULT false NOT NULL,
    requires_signature boolean DEFAULT false NOT NULL,
    is_hazardous boolean DEFAULT false NOT NULL,
    is_fragile boolean DEFAULT false NOT NULL,
    is_virtual boolean DEFAULT false NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(30) DEFAULT 'DRAFT'::character varying NOT NULL
);


ALTER TABLE public.products OWNER TO admin;

--
-- Name: products_cache; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.products_cache (
    sku_id character varying(255) NOT NULL,
    partner_id character varying(36),
    partner_sku character varying(255),
    name character varying(255) NOT NULL,
    description text,
    category_id character varying(64) NOT NULL,
    amount_cents integer NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    width_mm integer,
    height_mm integer,
    depth_mm integer,
    weight_g integer,
    is_active boolean DEFAULT true NOT NULL,
    requires_signature boolean DEFAULT false NOT NULL,
    is_hazardous boolean DEFAULT false NOT NULL,
    temperature_zone character varying(32) DEFAULT 'AMBIENT'::character varying NOT NULL,
    payload_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    synced_at timestamp with time zone
);


ALTER TABLE public.products_cache OWNER TO admin;

--
-- Name: promotion_product_exclusions; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.promotion_product_exclusions (
    promotion_id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL
);


ALTER TABLE public.promotion_product_exclusions OWNER TO admin;

--
-- Name: promotions; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.promotions (
    id character varying(36) NOT NULL,
    code character varying(32),
    name character varying(128) NOT NULL,
    type character varying(30) NOT NULL,
    discount_pct numeric(5,2),
    discount_cents integer,
    min_order_cents integer DEFAULT 0 NOT NULL,
    max_discount_cents integer,
    max_uses integer,
    uses_count integer DEFAULT 0 NOT NULL,
    per_user_limit integer DEFAULT 1,
    conditions_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    valid_from timestamp with time zone NOT NULL,
    valid_until timestamp with time zone,
    created_by character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_promotions_type CHECK (((type)::text = ANY ((ARRAY['PERCENT_OFF'::character varying, 'FIXED_OFF'::character varying, 'BUY_X_GET_Y'::character varying, 'FREE_ITEM'::character varying, 'BUNDLE_DISCOUNT'::character varying])::text[])))
);


ALTER TABLE public.promotions OWNER TO admin;

--
-- Name: pulse; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.pulse (
    id integer NOT NULL,
    creator_id integer NOT NULL,
    name character varying(254),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    skip_if_empty boolean DEFAULT false NOT NULL,
    alert_condition character varying(254),
    alert_first_only boolean,
    alert_above_goal boolean,
    collection_id integer,
    collection_position smallint,
    archived boolean DEFAULT false,
    dashboard_id integer,
    parameters text NOT NULL,
    entity_id character(21)
);


ALTER TABLE public.pulse OWNER TO admin;

--
-- Name: pulse_card; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.pulse_card (
    id integer NOT NULL,
    pulse_id integer NOT NULL,
    card_id integer NOT NULL,
    "position" integer NOT NULL,
    include_csv boolean DEFAULT false NOT NULL,
    include_xls boolean DEFAULT false NOT NULL,
    dashboard_card_id integer,
    entity_id character(21)
);


ALTER TABLE public.pulse_card OWNER TO admin;

--
-- Name: pulse_channel; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.pulse_channel (
    id integer NOT NULL,
    pulse_id integer NOT NULL,
    channel_type character varying(32) NOT NULL,
    details text NOT NULL,
    schedule_type character varying(32) NOT NULL,
    schedule_hour integer,
    schedule_day character varying(64),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    schedule_frame character varying(32),
    enabled boolean DEFAULT true NOT NULL,
    entity_id character(21)
);


ALTER TABLE public.pulse_channel OWNER TO admin;

--
-- Name: pulse_channel_recipient; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.pulse_channel_recipient (
    id integer NOT NULL,
    pulse_channel_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.pulse_channel_recipient OWNER TO admin;

--
-- Name: qrtz_blob_triggers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_blob_triggers (
    sched_name character varying(120) NOT NULL,
    trigger_name character varying(200) NOT NULL,
    trigger_group character varying(200) NOT NULL,
    blob_data bytea
);


ALTER TABLE public.qrtz_blob_triggers OWNER TO admin;

--
-- Name: qrtz_calendars; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_calendars (
    sched_name character varying(120) NOT NULL,
    calendar_name character varying(200) NOT NULL,
    calendar bytea NOT NULL
);


ALTER TABLE public.qrtz_calendars OWNER TO admin;

--
-- Name: qrtz_cron_triggers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_cron_triggers (
    sched_name character varying(120) NOT NULL,
    trigger_name character varying(200) NOT NULL,
    trigger_group character varying(200) NOT NULL,
    cron_expression character varying(120) NOT NULL,
    time_zone_id character varying(80)
);


ALTER TABLE public.qrtz_cron_triggers OWNER TO admin;

--
-- Name: qrtz_fired_triggers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_fired_triggers (
    sched_name character varying(120) NOT NULL,
    entry_id character varying(95) NOT NULL,
    trigger_name character varying(200) NOT NULL,
    trigger_group character varying(200) NOT NULL,
    instance_name character varying(200) NOT NULL,
    fired_time bigint NOT NULL,
    sched_time bigint,
    priority integer NOT NULL,
    state character varying(16) NOT NULL,
    job_name character varying(200),
    job_group character varying(200),
    is_nonconcurrent boolean,
    requests_recovery boolean
);


ALTER TABLE public.qrtz_fired_triggers OWNER TO admin;

--
-- Name: qrtz_job_details; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_job_details (
    sched_name character varying(120) NOT NULL,
    job_name character varying(200) NOT NULL,
    job_group character varying(200) NOT NULL,
    description character varying(250),
    job_class_name character varying(250) NOT NULL,
    is_durable boolean NOT NULL,
    is_nonconcurrent boolean NOT NULL,
    is_update_data boolean NOT NULL,
    requests_recovery boolean NOT NULL,
    job_data bytea
);


ALTER TABLE public.qrtz_job_details OWNER TO admin;

--
-- Name: qrtz_locks; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_locks (
    sched_name character varying(120) NOT NULL,
    lock_name character varying(40) NOT NULL
);


ALTER TABLE public.qrtz_locks OWNER TO admin;

--
-- Name: qrtz_paused_trigger_grps; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_paused_trigger_grps (
    sched_name character varying(120) NOT NULL,
    trigger_group character varying(200) NOT NULL
);


ALTER TABLE public.qrtz_paused_trigger_grps OWNER TO admin;

--
-- Name: qrtz_scheduler_state; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_scheduler_state (
    sched_name character varying(120) NOT NULL,
    instance_name character varying(200) NOT NULL,
    last_checkin_time bigint NOT NULL,
    checkin_interval bigint NOT NULL
);


ALTER TABLE public.qrtz_scheduler_state OWNER TO admin;

--
-- Name: qrtz_simple_triggers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_simple_triggers (
    sched_name character varying(120) NOT NULL,
    trigger_name character varying(200) NOT NULL,
    trigger_group character varying(200) NOT NULL,
    repeat_count bigint NOT NULL,
    repeat_interval bigint NOT NULL,
    times_triggered bigint NOT NULL
);


ALTER TABLE public.qrtz_simple_triggers OWNER TO admin;

--
-- Name: qrtz_simprop_triggers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_simprop_triggers (
    sched_name character varying(120) NOT NULL,
    trigger_name character varying(200) NOT NULL,
    trigger_group character varying(200) NOT NULL,
    str_prop_1 character varying(512),
    str_prop_2 character varying(512),
    str_prop_3 character varying(512),
    int_prop_1 integer,
    int_prop_2 integer,
    long_prop_1 bigint,
    long_prop_2 bigint,
    dec_prop_1 numeric(13,4),
    dec_prop_2 numeric(13,4),
    bool_prop_1 boolean,
    bool_prop_2 boolean
);


ALTER TABLE public.qrtz_simprop_triggers OWNER TO admin;

--
-- Name: qrtz_triggers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.qrtz_triggers (
    sched_name character varying(120) NOT NULL,
    trigger_name character varying(200) NOT NULL,
    trigger_group character varying(200) NOT NULL,
    job_name character varying(200) NOT NULL,
    job_group character varying(200) NOT NULL,
    description character varying(250),
    next_fire_time bigint,
    prev_fire_time bigint,
    priority integer,
    trigger_state character varying(16) NOT NULL,
    trigger_type character varying(8) NOT NULL,
    start_time bigint NOT NULL,
    end_time bigint,
    calendar_name character varying(200),
    misfire_instr smallint,
    job_data bytea
);


ALTER TABLE public.qrtz_triggers OWNER TO admin;

--
-- Name: query; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.query (
    query_hash bytea NOT NULL,
    average_execution_time integer NOT NULL,
    query text
);


ALTER TABLE public.query OWNER TO admin;

--
-- Name: query_action; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.query_action (
    action_id integer NOT NULL,
    database_id integer NOT NULL,
    dataset_query text NOT NULL
);


ALTER TABLE public.query_action OWNER TO admin;

--
-- Name: query_cache; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.query_cache (
    query_hash bytea NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    results bytea NOT NULL
);


ALTER TABLE public.query_cache OWNER TO admin;

--
-- Name: query_execution; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.query_execution (
    id integer NOT NULL,
    hash bytea NOT NULL,
    started_at timestamp with time zone NOT NULL,
    running_time integer NOT NULL,
    result_rows integer NOT NULL,
    native boolean NOT NULL,
    context character varying(32),
    error text,
    executor_id integer,
    card_id integer,
    dashboard_id integer,
    pulse_id integer,
    database_id integer,
    cache_hit boolean,
    action_id integer,
    is_sandboxed boolean,
    cache_hash bytea
);


ALTER TABLE public.query_execution OWNER TO admin;

--
-- Name: recent_views; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.recent_views (
    id integer NOT NULL,
    user_id integer NOT NULL,
    model character varying(16) NOT NULL,
    model_id integer NOT NULL,
    "timestamp" timestamp without time zone NOT NULL
);


ALTER TABLE public.recent_views OWNER TO admin;

--
-- Name: reconciliation_pending; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.reconciliation_pending (
    id character varying(40) NOT NULL,
    dedupe_key character varying(180) NOT NULL,
    order_id character varying(36) NOT NULL,
    reason character varying(80) NOT NULL,
    status character varying(24) DEFAULT 'PENDING'::character varying NOT NULL,
    payload_json text,
    attempt_count integer DEFAULT 0 NOT NULL,
    max_attempts integer DEFAULT 5 NOT NULL,
    next_retry_at timestamp with time zone,
    processing_started_at timestamp with time zone,
    last_error text,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.reconciliation_pending OWNER TO admin;

--
-- Name: rental_plans; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.rental_plans (
    id character varying(36) NOT NULL,
    locker_id character varying(36),
    slot_size character varying(8),
    name character varying(128) NOT NULL,
    description text,
    billing_cycle character varying(20) NOT NULL,
    amount_cents integer NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    max_duration_days integer,
    grace_period_hours integer DEFAULT 24 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.rental_plans OWNER TO admin;

--
-- Name: report_card; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.report_card (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    name character varying(254) NOT NULL,
    description text,
    display character varying(254) NOT NULL,
    dataset_query text NOT NULL,
    visualization_settings text NOT NULL,
    creator_id integer NOT NULL,
    database_id integer NOT NULL,
    table_id integer,
    query_type character varying(16),
    archived boolean DEFAULT false NOT NULL,
    collection_id integer,
    public_uuid character(36),
    made_public_by_id integer,
    enable_embedding boolean DEFAULT false NOT NULL,
    embedding_params text,
    cache_ttl integer,
    result_metadata text,
    collection_position smallint,
    dataset boolean DEFAULT false NOT NULL,
    entity_id character(21),
    parameters text,
    parameter_mappings text,
    collection_preview boolean DEFAULT true NOT NULL,
    metabase_version character varying(100)
);


ALTER TABLE public.report_card OWNER TO admin;

--
-- Name: report_cardfavorite; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.report_cardfavorite (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    card_id integer NOT NULL,
    owner_id integer NOT NULL
);


ALTER TABLE public.report_cardfavorite OWNER TO admin;

--
-- Name: report_dashboard; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.report_dashboard (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    name character varying(254) NOT NULL,
    description text,
    creator_id integer NOT NULL,
    parameters text NOT NULL,
    points_of_interest text,
    caveats text,
    show_in_getting_started boolean DEFAULT false NOT NULL,
    public_uuid character(36),
    made_public_by_id integer,
    enable_embedding boolean DEFAULT false NOT NULL,
    embedding_params text,
    archived boolean DEFAULT false NOT NULL,
    "position" integer,
    collection_id integer,
    collection_position smallint,
    cache_ttl integer,
    entity_id character(21),
    auto_apply_filters boolean DEFAULT true NOT NULL
);


ALTER TABLE public.report_dashboard OWNER TO admin;

--
-- Name: report_dashboardcard; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.report_dashboardcard (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    size_x integer NOT NULL,
    size_y integer NOT NULL,
    "row" integer NOT NULL,
    col integer NOT NULL,
    card_id integer,
    dashboard_id integer NOT NULL,
    parameter_mappings text NOT NULL,
    visualization_settings text NOT NULL,
    entity_id character(21),
    action_id integer,
    dashboard_tab_id integer
);


ALTER TABLE public.report_dashboardcard OWNER TO admin;

--
-- Name: return_legs; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.return_legs (
    id character varying(36) NOT NULL,
    return_request_id character varying(36) NOT NULL,
    logistics_partner_id character varying(36),
    tracking_code character varying(128),
    label_id character varying(36),
    from_locker_id character varying(64),
    to_hub_address_json text DEFAULT '{}'::text NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    shipped_at timestamp with time zone,
    received_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT return_legs_status_check CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'IN_TRANSIT'::character varying, 'RECEIVED'::character varying, 'LOST'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.return_legs OWNER TO admin;

--
-- Name: return_reasons_catalog; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.return_reasons_catalog (
    id character varying(36) NOT NULL,
    code character varying(30) NOT NULL,
    label_pt character varying(128) NOT NULL,
    label_en character varying(128),
    category character varying(30),
    requires_photo boolean DEFAULT false NOT NULL,
    requires_detail boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.return_reasons_catalog OWNER TO admin;

--
-- Name: return_requests; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.return_requests (
    id character varying(36) NOT NULL,
    original_delivery_id character varying(36) NOT NULL,
    locker_id character varying(64),
    requester_type character varying(20) NOT NULL,
    requester_id character varying(36),
    return_reason_code character varying(30) NOT NULL,
    return_reason_detail text,
    photo_url character varying(500),
    status character varying(30) DEFAULT 'REQUESTED'::character varying NOT NULL,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    approved_at timestamp with time zone,
    approved_by character varying(36),
    closed_at timestamp with time zone,
    close_reason character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT return_requests_requester_type_check CHECK (((requester_type)::text = ANY ((ARRAY['RECIPIENT'::character varying, 'SENDER'::character varying, 'SYSTEM'::character varying, 'OPS'::character varying])::text[]))),
    CONSTRAINT return_requests_status_check CHECK (((status)::text = ANY ((ARRAY['REQUESTED'::character varying, 'APPROVED'::character varying, 'REJECTED'::character varying, 'LABEL_ISSUED'::character varying, 'IN_TRANSIT'::character varying, 'RECEIVED'::character varying, 'CLOSED'::character varying, 'DISPUTED'::character varying])::text[])))
);


ALTER TABLE public.return_requests OWNER TO admin;

--
-- Name: return_tracking_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.return_tracking_events (
    id character varying(36) NOT NULL,
    return_leg_id character varying(36) NOT NULL,
    event_code character varying(30) NOT NULL,
    description character varying(255),
    location_name character varying(128),
    occurred_at timestamp with time zone NOT NULL,
    source character varying(20) DEFAULT 'CARRIER_WEBHOOK'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.return_tracking_events OWNER TO admin;

--
-- Name: revision; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.revision (
    id integer NOT NULL,
    model character varying(16) NOT NULL,
    model_id integer NOT NULL,
    user_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    object text NOT NULL,
    is_reversion boolean DEFAULT false NOT NULL,
    is_creation boolean DEFAULT false NOT NULL,
    message text,
    most_recent boolean DEFAULT false NOT NULL,
    metabase_version character varying(100)
);


ALTER TABLE public.revision OWNER TO admin;

--
-- Name: risk_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.risk_events (
    id text NOT NULL,
    request_id text NOT NULL,
    event_type text NOT NULL,
    decision text NOT NULL,
    score integer NOT NULL,
    policy_id text NOT NULL,
    region text NOT NULL,
    locker_id text NOT NULL,
    porta integer NOT NULL,
    created_at bigint NOT NULL,
    reasons_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    signals_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    audit_event_id text NOT NULL,
    CONSTRAINT ck_decision_allowed_values CHECK ((upper(decision) = ANY (ARRAY['ALLOW'::text, 'BLOCK'::text, 'CHALLENGE'::text]))),
    CONSTRAINT ck_risk_events_porta_positive CHECK ((porta > 0)),
    CONSTRAINT ck_risk_events_score_range CHECK (((score >= 0) AND (score <= 100)))
);


ALTER TABLE public.risk_events OWNER TO admin;

--
-- Name: runtime_locker_features; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.runtime_locker_features (
    locker_id character varying(120) NOT NULL,
    supports_online boolean DEFAULT true NOT NULL,
    supports_kiosk boolean DEFAULT true NOT NULL,
    supports_pickup_qr boolean DEFAULT true NOT NULL,
    supports_manual_code boolean DEFAULT true NOT NULL,
    supports_open_command boolean DEFAULT true NOT NULL,
    supports_light_command boolean DEFAULT true NOT NULL,
    supports_paid_pending_pickup boolean DEFAULT true NOT NULL,
    supports_refrigerated_items boolean DEFAULT false NOT NULL,
    supports_frozen_items boolean DEFAULT false NOT NULL,
    supports_high_value_items boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    supports_ble boolean DEFAULT false NOT NULL
);


ALTER TABLE public.runtime_locker_features OWNER TO admin;

--
-- Name: runtime_locker_slots; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.runtime_locker_slots (
    locker_id character varying(120) NOT NULL,
    slot_number integer NOT NULL,
    slot_size character varying(16) NOT NULL,
    width_cm integer,
    height_cm integer,
    depth_cm integer,
    max_weight_kg numeric(10,3),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.runtime_locker_slots OWNER TO admin;

--
-- Name: runtime_lockers; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.runtime_lockers (
    locker_id character varying(120) NOT NULL,
    machine_id character varying(120) NOT NULL,
    display_name character varying(255) NOT NULL,
    region character varying(16) NOT NULL,
    country character varying(8) NOT NULL,
    timezone character varying(64) NOT NULL,
    operator_id character varying(120),
    temperature_zone character varying(32) DEFAULT 'AMBIENT'::character varying NOT NULL,
    security_level character varying(32) DEFAULT 'STANDARD'::character varying NOT NULL,
    active boolean DEFAULT true NOT NULL,
    runtime_enabled boolean DEFAULT true NOT NULL,
    mqtt_region character varying(32) NOT NULL,
    mqtt_locker_id character varying(120) NOT NULL,
    topology_version integer DEFAULT 1 NOT NULL,
    slot_count_total integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    payment_methods_json jsonb DEFAULT '[]'::jsonb NOT NULL
);


ALTER TABLE public.runtime_lockers OWNER TO admin;

--
-- Name: runtime_sync_queue; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.runtime_sync_queue (
    id character varying(36) NOT NULL,
    locker_id character varying(64) NOT NULL,
    operation character varying(32) NOT NULL,
    status character varying(20) NOT NULL,
    retry_count integer DEFAULT 0 NOT NULL,
    max_retries integer DEFAULT 3 NOT NULL,
    last_error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    processed_at timestamp with time zone,
    next_retry_at timestamp with time zone
);


ALTER TABLE public.runtime_sync_queue OWNER TO admin;

--
-- Name: saved_payment_methods; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.saved_payment_methods (
    id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    method_code character varying(80) NOT NULL,
    gateway_token character varying(255) NOT NULL,
    last4 character varying(4),
    card_brand character varying(50),
    cardholder_name character varying(255),
    expiry_month integer,
    expiry_year integer,
    is_default boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.saved_payment_methods OWNER TO admin;

--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.schema_migrations (
    name character varying(255) NOT NULL,
    applied_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.schema_migrations OWNER TO admin;

--
-- Name: secret; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.secret (
    id integer NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    creator_id integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone,
    name character varying(254) NOT NULL,
    kind character varying(254) NOT NULL,
    source character varying(254),
    value bytea NOT NULL
);


ALTER TABLE public.secret OWNER TO admin;

--
-- Name: segment; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.segment (
    id integer NOT NULL,
    table_id integer NOT NULL,
    creator_id integer NOT NULL,
    name character varying(254) NOT NULL,
    description text,
    archived boolean DEFAULT false NOT NULL,
    definition text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    points_of_interest text,
    caveats text,
    show_in_getting_started boolean DEFAULT false NOT NULL,
    entity_id character(21)
);


ALTER TABLE public.segment OWNER TO admin;

--
-- Name: seller_reviews; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.seller_reviews (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    seller_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    user_id character varying(36),
    rating integer NOT NULL,
    comment text,
    delivery_rating integer,
    product_quality_rating integer,
    communication_rating integer,
    verified_purchase boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_seller_review_rating CHECK (((rating >= 1) AND (rating <= 5))),
    CONSTRAINT ck_seller_review_sub_ratings CHECK ((((delivery_rating IS NULL) OR ((delivery_rating >= 1) AND (delivery_rating <= 5))) AND ((product_quality_rating IS NULL) OR ((product_quality_rating >= 1) AND (product_quality_rating <= 5))) AND ((communication_rating IS NULL) OR ((communication_rating >= 1) AND (communication_rating <= 5)))))
);


ALTER TABLE public.seller_reviews OWNER TO admin;

--
-- Name: setting; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.setting (
    key character varying(254) NOT NULL,
    value text NOT NULL
);


ALTER TABLE public.setting OWNER TO admin;

--
-- Name: slot_occupancy_history; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.slot_occupancy_history (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    locker_id character varying NOT NULL,
    slot_label character varying(20) NOT NULL,
    allocation_id character varying(36),
    previous_state character varying(40),
    current_state character varying(40) NOT NULL,
    triggered_by character varying(50),
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb
);


ALTER TABLE public.slot_occupancy_history OWNER TO admin;

--
-- Name: store_inventory; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.store_inventory (
    id bigint NOT NULL,
    store_id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    quantity integer DEFAULT 0,
    price_cents integer,
    last_sync_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_store_qty CHECK ((quantity >= 0))
);


ALTER TABLE public.store_inventory OWNER TO admin;

--
-- Name: subscription_benefits_usage; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.subscription_benefits_usage (
    id bigint NOT NULL,
    subscription_id character varying(36) NOT NULL,
    usage_month date NOT NULL,
    benefit_type character varying(30) NOT NULL,
    usage_count integer DEFAULT 0,
    usage_limit integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_benefit_type CHECK (((benefit_type)::text = ANY ((ARRAY['FREE_SHIPPING'::character varying, 'PRIORITY_SHELF'::character varying, 'EXCLUSIVE_DEAL'::character varying])::text[])))
);


ALTER TABLE public.subscription_benefits_usage OWNER TO admin;

--
-- Name: subscription_plans; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.subscription_plans (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    name character varying(50) NOT NULL,
    code character varying(20) NOT NULL,
    description text,
    monthly_fee_cents integer NOT NULL,
    yearly_fee_cents integer,
    free_shipping boolean DEFAULT false,
    priority_shelf boolean DEFAULT false,
    exclusive_deals boolean DEFAULT false,
    priority_support boolean DEFAULT false,
    max_orders_per_month integer,
    max_discount_pct numeric(5,2),
    features_json jsonb DEFAULT '{}'::jsonb,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_plan_code CHECK (((code)::text = ANY ((ARRAY['BASIC'::character varying, 'PREMIUM'::character varying, 'PRO'::character varying, 'ENTERPRISE'::character varying])::text[]))),
    CONSTRAINT ck_plan_monthly_fee CHECK ((monthly_fee_cents >= 0))
);


ALTER TABLE public.subscription_plans OWNER TO admin;

--
-- Name: subscription_usage; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.subscription_usage (
    id bigint NOT NULL,
    subscription_id character varying(36),
    usage_month date,
    orders_count integer DEFAULT 0,
    free_shipping_used integer DEFAULT 0,
    savings_cents integer DEFAULT 0
);


ALTER TABLE public.subscription_usage OWNER TO admin;

--
-- Name: table_privileges; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.table_privileges (
    table_id integer NOT NULL,
    role character varying(255),
    "select" boolean DEFAULT false NOT NULL,
    update boolean DEFAULT false NOT NULL,
    insert boolean DEFAULT false NOT NULL,
    delete boolean DEFAULT false NOT NULL
);


ALTER TABLE public.table_privileges OWNER TO admin;

--
-- Name: task_history; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.task_history (
    id integer NOT NULL,
    task character varying(254) NOT NULL,
    db_id integer,
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ended_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    duration integer NOT NULL,
    task_details text
);


ALTER TABLE public.task_history OWNER TO admin;

--
-- Name: templates; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.templates (
    id character varying(36) NOT NULL,
    name character varying(128) NOT NULL,
    body text NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.templates OWNER TO admin;

--
-- Name: tenant_fiscal_config; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.tenant_fiscal_config (
    tenant_id character varying(100) NOT NULL,
    cnpj character varying(18) NOT NULL,
    razao_social character varying(140) NOT NULL,
    ie character varying(20),
    regime character varying(20) NOT NULL,
    crt character(1) NOT NULL,
    cert_a1_ref character varying(255),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    brand_config jsonb DEFAULT '{"logo_url": null, "accent_color": "#38A169", "company_name": null, "custom_domain": null, "primary_color": "#1A365D", "support_email": null, "support_phone": null, "secondary_color": "#2D3748"}'::jsonb
);


ALTER TABLE public.tenant_fiscal_config OWNER TO admin;

--
-- Name: timeline; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.timeline (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(255),
    icon character varying(128) NOT NULL,
    collection_id integer,
    archived boolean DEFAULT false NOT NULL,
    creator_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    "default" boolean DEFAULT false NOT NULL,
    entity_id character(21)
);


ALTER TABLE public.timeline OWNER TO admin;

--
-- Name: timeline_event; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.timeline_event (
    id integer NOT NULL,
    timeline_id integer NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(255),
    "timestamp" timestamp with time zone NOT NULL,
    time_matters boolean NOT NULL,
    timezone character varying(255) NOT NULL,
    icon character varying(128) NOT NULL,
    archived boolean DEFAULT false NOT NULL,
    creator_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.timeline_event OWNER TO admin;

--
-- Name: ui_error_events; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.ui_error_events (
    id character varying(40) NOT NULL,
    event_id character varying(80) NOT NULL,
    domain character varying(40) NOT NULL,
    path character varying(200) NOT NULL,
    message text NOT NULL,
    stack text,
    component_stack text,
    trace_id character varying(80),
    source_ip character varying(80),
    event_created_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ui_error_events OWNER TO admin;

--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.user_roles (
    id character varying(36) DEFAULT (gen_random_uuid())::text NOT NULL,
    user_id character varying(36) NOT NULL,
    role character varying(40) NOT NULL,
    scope_type character varying(40) DEFAULT 'GLOBAL'::character varying,
    scope_id character varying(36),
    is_active boolean DEFAULT true NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone
);


ALTER TABLE public.user_roles OWNER TO admin;

--
-- Name: user_wallets; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.user_wallets (
    id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    balance_cents bigint DEFAULT 0 NOT NULL,
    currency character varying(8) DEFAULT 'BRL'::character varying NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE'::character varying NOT NULL,
    last_transaction_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_wallets OWNER TO admin;

--
-- Name: users; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.users (
    id character varying(36) NOT NULL,
    full_name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(32),
    password_hash character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    email_verified boolean NOT NULL,
    phone_verified boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    anonymized_at timestamp with time zone,
    locale character varying(10),
    totp_enabled boolean DEFAULT false NOT NULL,
    totp_secret_ref character varying(255),
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone,
    tax_country character varying(2),
    tax_document_type character varying(16),
    tax_document_value character varying(1024),
    fiscal_email character varying(1024),
    fiscal_phone character varying(1024),
    fiscal_address_line1 character varying(1024),
    fiscal_address_line2 character varying(1024),
    fiscal_address_city character varying(1024),
    fiscal_address_state character varying(1024),
    fiscal_address_postal_code character varying(1024),
    fiscal_address_country character varying(2),
    fiscal_profile_updated_at timestamp with time zone,
    fiscal_data_consent boolean DEFAULT false NOT NULL,
    cpf_encrypted bytea,
    phone_encrypted bytea
);


ALTER TABLE public.users OWNER TO admin;

--
-- Name: view_log; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.view_log (
    id integer NOT NULL,
    user_id integer,
    model character varying(16) NOT NULL,
    model_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    metadata text,
    has_access boolean,
    context character varying(32)
);


ALTER TABLE public.view_log OWNER TO admin;

--
-- Name: wallet_provider_catalog; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.wallet_provider_catalog (
    id bigint NOT NULL,
    code character varying(80) NOT NULL,
    name character varying(120) NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.wallet_provider_catalog OWNER TO admin;

--
-- Name: wallet_transactions; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.wallet_transactions (
    id character varying(36) NOT NULL,
    wallet_id character varying(36) NOT NULL,
    order_id character varying,
    type character varying(30) NOT NULL,
    amount_cents bigint NOT NULL,
    balance_after_cents bigint NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    external_reference character varying(255),
    description text,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.wallet_transactions OWNER TO admin;

--
-- Name: webhook_deliveries; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.webhook_deliveries (
    id character varying(36) NOT NULL,
    endpoint_id character varying(36) NOT NULL,
    event_name character varying(100) NOT NULL,
    aggregate_type character varying(50),
    aggregate_id character varying(36),
    payload_json text NOT NULL,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    max_attempts integer DEFAULT 5 NOT NULL,
    last_status_code integer,
    last_response_body text,
    last_attempt_at timestamp with time zone,
    next_attempt_at timestamp with time zone DEFAULT now() NOT NULL,
    delivered_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.webhook_deliveries OWNER TO admin;

--
-- Name: webhook_endpoints; Type: TABLE; Schema: public; Owner: admin
--


CREATE TABLE public.webhook_endpoints (
    id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    partner_id character varying(36) NOT NULL,
    url character varying(500) NOT NULL,
    events text NOT NULL,
    secret_ref character varying(255),
    signing_algo character varying(20) DEFAULT 'HMAC_SHA256'::character varying NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.webhook_endpoints OWNER TO admin;

--
-- Name: orders_2025_06; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2025_06 FOR VALUES FROM ('2025-06-01 00:00:00+00') TO ('2025-07-01 00:00:00+00');


--
-- Name: orders_2025_07; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2025_07 FOR VALUES FROM ('2025-07-01 00:00:00+00') TO ('2025-08-01 00:00:00+00');


--
-- Name: orders_2025_08; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2025_08 FOR VALUES FROM ('2025-08-01 00:00:00+00') TO ('2025-09-01 00:00:00+00');


--
-- Name: orders_2025_09; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2025_09 FOR VALUES FROM ('2025-09-01 00:00:00+00') TO ('2025-10-01 00:00:00+00');


--
-- Name: orders_2025_10; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2025_10 FOR VALUES FROM ('2025-10-01 00:00:00+00') TO ('2025-11-01 00:00:00+00');


--
-- Name: orders_2025_11; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2025_11 FOR VALUES FROM ('2025-11-01 00:00:00+00') TO ('2025-12-01 00:00:00+00');


--
-- Name: orders_2025_12; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2025_12 FOR VALUES FROM ('2025-12-01 00:00:00+00') TO ('2026-01-01 00:00:00+00');


--
-- Name: orders_2026_01; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2026_01 FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2026-02-01 00:00:00+00');


--
-- Name: orders_2026_02; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2026_02 FOR VALUES FROM ('2026-02-01 00:00:00+00') TO ('2026-03-01 00:00:00+00');


--
-- Name: orders_2026_03; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2026_03 FOR VALUES FROM ('2026-03-01 00:00:00+00') TO ('2026-04-01 00:00:00+00');


--
-- Name: orders_2026_04; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2026_04 FOR VALUES FROM ('2026-04-01 00:00:00+00') TO ('2026-05-01 00:00:00+00');


--
-- Name: orders_2026_05; Type: TABLE ATTACH; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned ATTACH PARTITION public.orders_2026_05 FOR VALUES FROM ('2026-05-01 00:00:00+00') TO ('2026-06-01 00:00:00+00');


