--
-- PostgreSQL database dump
--

-- Dumped from database version 15.8 (Debian 15.8-1.pgdg110+1)
-- Dumped by pg_dump version 15.8 (Debian 15.8-1.pgdg110+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: admin
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO admin;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: admin
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: address_standardizer; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS address_standardizer WITH SCHEMA public;


--
-- Name: EXTENSION address_standardizer; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION address_standardizer IS 'Used to parse an address into constituent elements. Generally used to support geocoding address normalization step.';


--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Name: allocationstate; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.allocationstate AS ENUM (
    'RESERVED_PENDING_PAYMENT',
    'RESERVED_PAID_PENDING_PICKUP',
    'OPENED_FOR_PICKUP',
    'PICKED_UP',
    'EXPIRED',
    'RELEASED',
    'CANCELLED',
    'FRAUD_REVIEW',
    'ERROR',
    'MAINTENANCE',
    'OUT_OF_STOCK'
);


ALTER TYPE public.allocationstate OWNER TO admin;

--
-- Name: cardtype; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.cardtype AS ENUM (
    'CREDIT',
    'DEBIT'
);


ALTER TYPE public.cardtype OWNER TO admin;

--
-- Name: creditstatus; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.creditstatus AS ENUM (
    'AVAILABLE',
    'USED',
    'EXPIRED',
    'REVOKED'
);


ALTER TYPE public.creditstatus OWNER TO admin;

--
-- Name: deadline_status_enum; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.deadline_status_enum AS ENUM (
    'PENDING',
    'EXECUTING',
    'EXECUTED',
    'CANCELLED',
    'FAILED'
);


ALTER TYPE public.deadline_status_enum OWNER TO admin;

--
-- Name: deadline_type_enum; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.deadline_type_enum AS ENUM (
    'PREPAYMENT_TIMEOUT',
    'POSTPAYMENT_EXPIRY',
    'PICKUP_TIMEOUT'
);


ALTER TYPE public.deadline_type_enum OWNER TO admin;

--
-- Name: dispute_state; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.dispute_state AS ENUM (
    'NONE',
    'OPEN',
    'UNDER_REVIEW',
    'ACCEPTED',
    'REJECTED',
    'CLOSED'
);


ALTER TYPE public.dispute_state OWNER TO admin;

--
-- Name: event_status_enum; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.event_status_enum AS ENUM (
    'PENDING',
    'PUBLISHED',
    'FAILED'
);


ALTER TYPE public.event_status_enum OWNER TO admin;

--
-- Name: invoice_status_enum; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.invoice_status_enum AS ENUM (
    'PENDING',
    'PROCESSING',
    'ISSUED',
    'FAILED',
    'CANCELLED'
);


ALTER TYPE public.invoice_status_enum OWNER TO admin;

--
-- Name: invoicestatus; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.invoicestatus AS ENUM (
    'PENDING',
    'ISSUED',
    'FAILED',
    'PROCESSING',
    'DEAD_LETTER',
    'CANCELLED'
);


ALTER TYPE public.invoicestatus OWNER TO admin;

--
-- Name: orderchannel; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.orderchannel AS ENUM (
    'ONLINE',
    'KIOSK'
);


ALTER TYPE public.orderchannel OWNER TO admin;

--
-- Name: orderstatus; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.orderstatus AS ENUM (
    'PAYMENT_PENDING',
    'PAID_PENDING_PICKUP',
    'DISPENSED',
    'PICKED_UP',
    'EXPIRED_CREDIT_50',
    'EXPIRED',
    'CANCELLED',
    'REFUNDED',
    'FAILED'
);


ALTER TYPE public.orderstatus OWNER TO admin;

--
-- Name: otpchannel; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.otpchannel AS ENUM (
    'EMAIL',
    'PHONE'
);


ALTER TYPE public.otpchannel OWNER TO admin;

--
-- Name: paymentinterface; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.paymentinterface AS ENUM (
    'NFC',
    'QR_CODE',
    'CHIP',
    'WEB_TOKEN',
    'MANUAL',
    'DEEP_LINK',
    'API',
    'USSD',
    'FACE_RECOGNITION',
    'FINGERPRINT',
    'BARCODE'
);


ALTER TYPE public.paymentinterface OWNER TO admin;

--
-- Name: paymentmethod; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.paymentmethod AS ENUM (
    'PIX',
    'CARTAO',
    'MBWAY',
    'MULTIBANCO_REFERENCE',
    'NFC',
    'APPLE_PAY',
    'GOOGLE_PAY',
    'MERCADO_PAGO_WALLET',
    'creditCard',
    'debitCard',
    'pix',
    'boleto',
    'apple_pay',
    'google_pay',
    'cash',
    'giftCard'
);


ALTER TYPE public.paymentmethod OWNER TO admin;

--
-- Name: paymentstatus; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.paymentstatus AS ENUM (
    'CREATED',
    'PENDING_CUSTOMER_ACTION',
    'PENDING_PROVIDER_CONFIRMATION',
    'APPROVED',
    'DECLINED',
    'EXPIRED',
    'FAILED',
    'CANCELLED',
    'AWAITING_INTEGRATION',
    'REFUNDED',
    'PARTIALLY_REFUNDED',
    'AUTHORIZED'
);


ALTER TYPE public.paymentstatus OWNER TO admin;

--
-- Name: pickup_phase; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.pickup_phase AS ENUM (
    'CREATED',
    'READY_FOR_PICKUP',
    'AUTH_PENDING',
    'AUTHENTICATED',
    'DISPENSE_REQUESTED',
    'ACCESS_GRANTED',
    'IN_PROGRESS',
    'COMPLETED_UNVERIFIED',
    'COMPLETED_VERIFIED',
    'EXPIRED',
    'CANCELLED',
    'FAILED',
    'RECONCILING',
    'RECONCILED'
);


ALTER TYPE public.pickup_phase OWNER TO admin;

--
-- Name: pickupchannel; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.pickupchannel AS ENUM (
    'ONLINE',
    'KIOSK'
);


ALTER TYPE public.pickupchannel OWNER TO admin;

--
-- Name: pickuplifecyclestage; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.pickuplifecyclestage AS ENUM (
    'CREATED',
    'READY_FOR_PICKUP',
    'DOOR_OPENED',
    'ITEM_REMOVED',
    'DOOR_CLOSED',
    'COMPLETED',
    'EXPIRED',
    'CANCELLED'
);


ALTER TYPE public.pickuplifecyclestage OWNER TO admin;

--
-- Name: pickupredeemvia; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.pickupredeemvia AS ENUM (
    'QR',
    'MANUAL',
    'KIOSK',
    'SENSOR',
    'OPERATOR'
);


ALTER TYPE public.pickupredeemvia OWNER TO admin;

--
-- Name: pickupstatus; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.pickupstatus AS ENUM (
    'ACTIVE',
    'REDEEMED',
    'EXPIRED',
    'CANCELLED'
);


ALTER TYPE public.pickupstatus OWNER TO admin;

--
-- Name: walletprovider; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.walletprovider AS ENUM (
    'APPLE_PAY',
    'GOOGLE_PAY',
    'SAMSUNG_PAY',
    'PAYPAL',
    'MERCADO_PAGO',
    'PICPAY',
    'VENMO',
    'CASHAPP',
    'REVOLUT',
    'MBWAY',
    'M_PESA',
    'ALIPAY',
    'WECHAT_PAY',
    'PAYPAY',
    'LINE_PAY'
);


ALTER TYPE public.walletprovider OWNER TO admin;

--
-- Name: find_lockers_by_distance(numeric, numeric, numeric, integer); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.find_lockers_by_distance(ref_lat numeric, ref_lon numeric, radius_meters numeric, max_results integer DEFAULT 50) RETURNS TABLE(id integer, external_id character varying, address_street character varying, city_name character varying, district character varying, postal_code character varying, distance_meters numeric, is_24h boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.id,
        l.external_id,
        l.address_street,
        l.city_name,
        l.district,
        l.postal_code,
        ROUND(CAST(ST_Distance(
            l.geom::geography,
            ST_SetSRID(ST_MakePoint(ref_lon, ref_lat), 4326)::geography
        ) AS NUMERIC), 2) AS distance_meters,
        (l.metadata_json->>'is_24h')::BOOLEAN AS is_24h
    FROM public.capability_locker_location l
    WHERE l.is_active = true
      AND l.geom IS NOT NULL
      AND ST_DWithin(
            l.geom::geography,
            ST_SetSRID(ST_MakePoint(ref_lon, ref_lat), 4326)::geography,
            radius_meters
          )
    ORDER BY l.geom <-> ST_SetSRID(ST_MakePoint(ref_lon, ref_lat), 4326)
    LIMIT max_results;
END;
$$;


ALTER FUNCTION public.find_lockers_by_distance(ref_lat numeric, ref_lon numeric, radius_meters numeric, max_results integer) OWNER TO admin;

--
-- Name: fn_derive_evidence_strength(integer); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.fn_derive_evidence_strength(p_score integer) RETURNS character varying
    LANGUAGE sql IMMUTABLE
    AS $$
    SELECT CASE
        WHEN COALESCE(p_score, 0) = 0 THEN 'NONE'
        WHEN p_score BETWEEN 1 AND 39 THEN 'WEAK'
        WHEN p_score BETWEEN 40 AND 79 THEN 'MEDIUM'
        WHEN p_score BETWEEN 80 AND 99 THEN 'STRONG'
        WHEN p_score = 100 THEN 'FINAL'
        ELSE NULL
    END;
$$;


ALTER FUNCTION public.fn_derive_evidence_strength(p_score integer) OWNER TO admin;

--
-- Name: get_active_fiscal_document(text); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.get_active_fiscal_document(p_order_id text) RETURNS TABLE(id text, receipt_code text, attempt integer, issued_at timestamp without time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fd.id,
        fd.receipt_code,
        fd.attempt,
        fd.issued_at
    FROM public.fiscal_documents fd
    WHERE fd.order_id = p_order_id
    ORDER BY fd.attempt DESC
    LIMIT 1;
END;
$$;


ALTER FUNCTION public.get_active_fiscal_document(p_order_id text) OWNER TO admin;

--
-- Name: get_latest_fiscal_attempt(text); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.get_latest_fiscal_attempt(p_order_id text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    latest_attempt INTEGER;
BEGIN
    SELECT COALESCE(MAX(attempt), 0) INTO latest_attempt
    FROM public.fiscal_documents
    WHERE order_id = p_order_id;
    
    RETURN latest_attempt;
END;
$$;


ALTER FUNCTION public.get_latest_fiscal_attempt(p_order_id text) OWNER TO admin;

--
-- Name: get_order_complete_info(text); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.get_order_complete_info(p_order_id text) RETURNS TABLE(section text, data jsonb)
    LANGUAGE plpgsql
    AS $$
BEGIN

-- 1. Pedido principal
RETURN QUERY
SELECT '1. PEDIDO PRINCIPAL'::TEXT, 
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.orders WHERE id = p_order_id) t;

-- 2. Itens do pedido
RETURN QUERY
SELECT '2. ITENS DO PEDIDO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.order_items WHERE order_id = p_order_id) t;

-- 3. Alocação de slot
RETURN QUERY
SELECT '3. ALOCAÇÃO DE SLOT'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.allocations WHERE order_id = p_order_id) t;

-- 4. Pickup
RETURN QUERY
SELECT '4. PICKUP'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.pickups WHERE order_id = p_order_id) t;

-- 5. Tokens de pickup
RETURN QUERY
SELECT '5. TOKENS DE PICKUP'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(pt)), '[]'::jsonb)
FROM public.pickup_tokens pt
INNER JOIN public.pickups p ON pt.pickup_id = p.id
WHERE p.order_id = p_order_id;

-- 6. Transações de pagamento
RETURN QUERY
SELECT '6. TRANSAÇÕES DE PAGAMENTO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.payment_transactions WHERE order_id = p_order_id) t;

-- 7. Instruções de pagamento
RETURN QUERY
SELECT '7. INSTRUÇÕES DE PAGAMENTO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.payment_instructions WHERE order_id = p_order_id) t;

-- 8. Divisões de pagamento
RETURN QUERY
SELECT '8. DIVISÕES DE PAGAMENTO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.payment_splits WHERE order_id = p_order_id) t;

-- 9. Documentos fiscais
RETURN QUERY
SELECT '9. DOCUMENTOS FISCAIS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.fiscal_documents WHERE order_id = p_order_id) t;

-- 10. Notas fiscais (invoices)
RETURN QUERY
SELECT '10. NOTAS FISCAIS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.invoices WHERE order_id = p_order_id) t;

-- 11. Prazos do ciclo de vida
RETURN QUERY
SELECT '11. PRAZOS DO CICLO DE VIDA'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.lifecycle_deadlines WHERE order_id = p_order_id) t;

-- 12. Eventos analíticos
RETURN QUERY
SELECT '12. EVENTOS ANALÍTICOS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.analytics_facts WHERE order_id = p_order_id) t;

-- 13. Eventos processados de faturamento
RETURN QUERY
SELECT '13. EVENTOS DE FATURAMENTO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.billing_processed_events WHERE order_id = p_order_id) t;

-- 14. Notificações
RETURN QUERY
SELECT '14. NOTIFICAÇÕES'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.notification_logs WHERE order_id = p_order_id) t;

-- 15. Eventos de domínio
RETURN QUERY
SELECT '15. EVENTOS DE DOMÍNIO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.domain_events 
      WHERE aggregate_id = p_order_id AND aggregate_type = 'Order') t;

-- 16. Outbox de eventos
RETURN QUERY
SELECT '16. OUTBOX DE EVENTOS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.domain_event_outbox 
      WHERE aggregate_id = p_order_id) t;

-- 17. Registros de auditoria
RETURN QUERY
SELECT '17. REGISTROS DE AUDITORIA'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.audit_logs 
      WHERE target_id = p_order_id AND target_type = 'Order') t;

-- 18. Créditos
RETURN QUERY
SELECT '18. CRÉDITOS'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.credits WHERE order_id = p_order_id) t;

-- 19. Histórico de ocupação de slot (via allocations)
RETURN QUERY
SELECT '19. HISTÓRICO DE OCUPAÇÃO DE SLOT'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(soh)), '[]'::jsonb)
FROM public.slot_occupancy_history soh
WHERE soh.allocation_id IN (SELECT id FROM public.allocations WHERE order_id = p_order_id);

-- 20. Livro razão financeiro
RETURN QUERY
SELECT '20. LIVRO RAZÃO FINANCEIRO'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb)
FROM (SELECT * FROM public.financial_ledger WHERE order_id = p_order_id) t;

-- 21. Detalhes do locker (via allocations)
RETURN QUERY
SELECT '21. DETALHES DO LOCKER'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(l)), '[]'::jsonb)
FROM public.lockers l
WHERE l.id IN (SELECT locker_id FROM public.allocations WHERE order_id = p_order_id AND locker_id IS NOT NULL);

-- 22. Detalhes do slot (via allocations)
RETURN QUERY
SELECT '22. DETALHES DO SLOT'::TEXT,
       COALESCE(jsonb_agg(to_jsonb(ls)), '[]'::jsonb)
FROM public.locker_slots ls
WHERE ls.locker_id IN (SELECT locker_id FROM public.allocations WHERE order_id = p_order_id AND locker_id IS NOT NULL)
  AND ls.slot_label IN (SELECT slot::TEXT FROM public.allocations WHERE order_id = p_order_id);

-- 23. RESUMO COMPLETO EM JSON
RETURN QUERY
SELECT '23. RESUMO COMPLETO (JSON)'::TEXT,
       jsonb_build_object(
           'order', COALESCE((SELECT to_jsonb(t) FROM (SELECT * FROM public.orders WHERE id = p_order_id) t), '{}'::jsonb),
           'items', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.order_items WHERE order_id = p_order_id) t), '[]'::jsonb),
           'allocation', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.allocations WHERE order_id = p_order_id) t), '[]'::jsonb),
           'pickup', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.pickups WHERE order_id = p_order_id) t), '[]'::jsonb),
           'payment_transactions', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.payment_transactions WHERE order_id = p_order_id) t), '[]'::jsonb),
           'payment_instructions', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.payment_instructions WHERE order_id = p_order_id) t), '[]'::jsonb),
           'fiscal_documents', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.fiscal_documents WHERE order_id = p_order_id) t), '[]'::jsonb),
           'invoices', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.invoices WHERE order_id = p_order_id) t), '[]'::jsonb),
           'notifications', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.notification_logs WHERE order_id = p_order_id) t), '[]'::jsonb),
           'domain_events', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.domain_events WHERE aggregate_id = p_order_id AND aggregate_type = 'Order') t), '[]'::jsonb),
           'audit_logs', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.audit_logs WHERE target_id = p_order_id AND target_type = 'Order') t), '[]'::jsonb),
           'financial_ledger', COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (SELECT * FROM public.financial_ledger WHERE order_id = p_order_id) t), '[]'::jsonb)
       );

END;
$$;


ALTER FUNCTION public.get_order_complete_info(p_order_id text) OWNER TO admin;

--
-- Name: set_row_updated_at(); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.set_row_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_row_updated_at() OWNER TO admin;

--
-- Name: trg_log_slot_state_change(); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.trg_log_slot_state_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO public.slot_occupancy_history (
            locker_id, slot_label, allocation_id, previous_state, current_state, triggered_by, metadata
        ) VALUES (
            NEW.locker_id, NEW.slot_label, NEW.current_allocation_id, OLD.status, NEW.status, 
            COALESCE(NEW.metadata->>'triggered_by', 'SYSTEM'), 
            jsonb_build_object('fault_code', NEW.fault_code, 'dimensions', jsonb_build_object('w', NEW.width_mm, 'h', NEW.height_mm, 'd', NEW.depth_mm))
        );
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_log_slot_state_change() OWNER TO admin;

--
-- Name: trg_pickups_sync_v2_derived(); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.trg_pickups_sync_v2_derived() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Compatibilidade com escrita legada: garantir score sempre valido.
    NEW.evidence_score := COALESCE(NEW.evidence_score, 0);

    IF NEW.dispute_state IS NULL THEN
        NEW.dispute_state := 'NONE'::public.dispute_state;
    END IF;

    NEW.evidence_strength := public.fn_derive_evidence_strength(NEW.evidence_score);

    IF NEW.pickup_phase = 'COMPLETED_VERIFIED'::public.pickup_phase
       AND NEW.verified_at IS NULL THEN
        NEW.verified_at := now();
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_pickups_sync_v2_derived() OWNER TO admin;

--
-- Name: update_geom_from_coords(); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.update_geom_from_coords() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    ELSIF NEW.latitude IS NULL OR NEW.longitude IS NULL THEN
        NEW.geom = NULL;
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_geom_from_coords() OWNER TO admin;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: admin
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

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
-- Name: auth_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.auth_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_sessions_id_seq OWNER TO admin;

--
-- Name: auth_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.auth_sessions_id_seq OWNED BY public.auth_sessions.id;


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
-- Name: capability_channel_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_channel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_channel_id_seq OWNER TO admin;

--
-- Name: capability_channel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_channel_id_seq OWNED BY public.capability_channel.id;


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
-- Name: capability_context_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_context_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_context_id_seq OWNER TO admin;

--
-- Name: capability_context_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_context_id_seq OWNED BY public.capability_context.id;


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
-- Name: TABLE capability_country; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON TABLE public.capability_country IS 'Países operacionais para o sistema de lockers';


--
-- Name: capability_country_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_country_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_country_id_seq OWNER TO admin;

--
-- Name: capability_country_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_country_id_seq OWNED BY public.capability_country.id;


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
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.capability_locker_location OWNER TO admin;

--
-- Name: TABLE capability_locker_location; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON TABLE public.capability_locker_location IS 'Localizações físicas dos lockers com suporte a geolocalização';


--
-- Name: COLUMN capability_locker_location.geom; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.capability_locker_location.geom IS 'Geometria PostGIS (Point, SRID 4326) para consultas espaciais avançadas';


--
-- Name: COLUMN capability_locker_location.operating_hours_json; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.capability_locker_location.operating_hours_json IS 'JSON com horários: {"monday": "08:00-22:00", "saturday": "09:00-14:00"}';


--
-- Name: COLUMN capability_locker_location.metadata_json; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.capability_locker_location.metadata_json IS 'Metadados extensíveis: {"is_24h": true, "locker_size": "large", "accessibility": "wheelchair"}';


--
-- Name: capability_locker_location_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_locker_location_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_locker_location_id_seq OWNER TO admin;

--
-- Name: capability_locker_location_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_locker_location_id_seq OWNED BY public.capability_locker_location.id;


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
-- Name: capability_profile_action_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_profile_action_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_profile_action_id_seq OWNER TO admin;

--
-- Name: capability_profile_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_profile_action_id_seq OWNED BY public.capability_profile_action.id;


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
-- Name: capability_profile_constraint_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_profile_constraint_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_profile_constraint_id_seq OWNER TO admin;

--
-- Name: capability_profile_constraint_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_profile_constraint_id_seq OWNED BY public.capability_profile_constraint.id;


--
-- Name: capability_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_profile_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_profile_id_seq OWNER TO admin;

--
-- Name: capability_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_profile_id_seq OWNED BY public.capability_profile.id;


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
-- Name: capability_profile_method_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_profile_method_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_profile_method_id_seq OWNER TO admin;

--
-- Name: capability_profile_method_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_profile_method_id_seq OWNED BY public.capability_profile_method.id;


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
-- Name: capability_profile_method_interface_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_profile_method_interface_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_profile_method_interface_id_seq OWNER TO admin;

--
-- Name: capability_profile_method_interface_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_profile_method_interface_id_seq OWNED BY public.capability_profile_method_interface.id;


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
-- Name: capability_profile_method_requirement_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_profile_method_requirement_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_profile_method_requirement_id_seq OWNER TO admin;

--
-- Name: capability_profile_method_requirement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_profile_method_requirement_id_seq OWNED BY public.capability_profile_method_requirement.id;


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
-- Name: capability_profile_snapshot_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_profile_snapshot_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_profile_snapshot_id_seq OWNER TO admin;

--
-- Name: capability_profile_snapshot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_profile_snapshot_id_seq OWNED BY public.capability_profile_snapshot_old.id;


--
-- Name: capability_profile_snapshot_id_seq1; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_profile_snapshot_id_seq1
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_profile_snapshot_id_seq1 OWNER TO admin;

--
-- Name: capability_profile_snapshot_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_profile_snapshot_id_seq1 OWNED BY public.capability_profile_snapshot.id;


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
-- Name: capability_profile_target_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_profile_target_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_profile_target_id_seq OWNER TO admin;

--
-- Name: capability_profile_target_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_profile_target_id_seq OWNED BY public.capability_profile_target.id;


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
-- Name: TABLE capability_province; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON TABLE public.capability_province IS 'Estados/Províncias com hierarquia ISO 3166-2 (ex: BR-SP)';


--
-- Name: capability_province_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_province_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_province_id_seq OWNER TO admin;

--
-- Name: capability_province_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_province_id_seq OWNED BY public.capability_province.id;


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
-- Name: capability_region_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_region_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_region_id_seq OWNER TO admin;

--
-- Name: capability_region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_region_id_seq OWNED BY public.capability_region.id;


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
-- Name: capability_requirement_catalog_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.capability_requirement_catalog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.capability_requirement_catalog_id_seq OWNER TO admin;

--
-- Name: capability_requirement_catalog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.capability_requirement_catalog_id_seq OWNED BY public.capability_requirement_catalog.id;


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
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ecommerce_partners OWNER TO admin;

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
    locked_at timestamp with time zone
);


ALTER TABLE public.invoices OWNER TO admin;

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
    sla_return_hours integer DEFAULT 24
);


ALTER TABLE public.locker_operators OWNER TO admin;

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
-- Name: locker_slot_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.locker_slot_configs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.locker_slot_configs_id_seq OWNER TO admin;

--
-- Name: locker_slot_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.locker_slot_configs_id_seq OWNED BY public.locker_slot_configs.id;


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
-- Name: locker_telemetry_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.locker_telemetry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.locker_telemetry_id_seq OWNER TO admin;

--
-- Name: locker_telemetry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.locker_telemetry_id_seq OWNED BY public.locker_telemetry.id;


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
    CONSTRAINT ck_lockers_pickup_code_length_range CHECK (((pickup_code_length >= 4) AND (pickup_code_length <= 12))),
    CONSTRAINT ck_lockers_pickup_max_reopens_non_negative CHECK ((pickup_max_reopens >= 0)),
    CONSTRAINT ck_lockers_pickup_reuse_policy CHECK (((pickup_reuse_policy)::text = ANY ((ARRAY['NO_REUSE'::character varying, 'SAME_TOKEN_UNTIL_DEADLINE'::character varying, 'ALLOW_REOPEN_WINDOW'::character varying])::text[]))),
    CONSTRAINT ck_lockers_pickup_reuse_window_sec_non_negative CHECK (((pickup_reuse_window_sec IS NULL) OR (pickup_reuse_window_sec >= 0))),
    CONSTRAINT ck_lockers_slots_available_non_negative CHECK ((slots_available >= 0))
);


ALTER TABLE public.lockers OWNER TO admin;

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
-- Name: notification_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.notification_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.notification_logs_id_seq OWNER TO admin;

--
-- Name: notification_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.notification_logs_id_seq OWNED BY public.notification_logs.id;


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
    CONSTRAINT ck_order_items_quantity_positive CHECK ((quantity > 0)),
    CONSTRAINT ck_order_items_slot_preference_positive CHECK (((slot_preference IS NULL) OR (slot_preference > 0))),
    CONSTRAINT ck_order_items_total_amount_non_negative CHECK ((total_amount_cents >= 0)),
    CONSTRAINT ck_order_items_total_matches_quantity CHECK ((total_amount_cents = (quantity * unit_amount_cents))),
    CONSTRAINT ck_order_items_unit_amount_non_negative CHECK ((unit_amount_cents >= 0))
);


ALTER TABLE public.order_items OWNER TO admin;

--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.order_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.order_items_id_seq OWNER TO admin;

--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.order_items_id_seq OWNED BY public.order_items.id;


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
-- Name: payment_interface_catalog_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.payment_interface_catalog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.payment_interface_catalog_id_seq OWNER TO admin;

--
-- Name: payment_interface_catalog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.payment_interface_catalog_id_seq OWNED BY public.payment_interface_catalog.id;


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
-- Name: payment_method_catalog_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.payment_method_catalog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.payment_method_catalog_id_seq OWNER TO admin;

--
-- Name: payment_method_catalog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.payment_method_catalog_id_seq OWNED BY public.payment_method_catalog.id;


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
    reconciliation_batch_id character varying(100)
);


ALTER TABLE public.payment_transactions OWNER TO admin;

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
-- Name: pickup_events_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.pickup_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pickup_events_id_seq OWNER TO admin;

--
-- Name: pickup_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.pickup_events_id_seq OWNED BY public.pickup_events.id;


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
-- Name: product_locker_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.product_locker_configs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.product_locker_configs_id_seq OWNER TO admin;

--
-- Name: product_locker_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.product_locker_configs_id_seq OWNED BY public.product_locker_configs.id;


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
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.products OWNER TO admin;

--
-- Name: TABLE products; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON TABLE public.products IS 'Central product catalog, aligning with sku_id used in orders and order_items.';


--
-- Name: COLUMN products.id; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.products.id IS 'SKU ID, matches orders.sku_id.';


--
-- Name: COLUMN products.amount_cents; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.products.amount_cents IS 'Price in cents to avoid floating point errors.';


--
-- Name: COLUMN products.metadata_json; Type: COMMENT; Schema: public; Owner: admin
--

COMMENT ON COLUMN public.products.metadata_json IS 'Flexible JSON field for additional product attributes.';


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
    updated_at timestamp without time zone DEFAULT now() NOT NULL
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
    deleted_at timestamp with time zone
);


ALTER TABLE public.users OWNER TO admin;

--
-- Name: vw_fiscal_documents_with_attempt; Type: VIEW; Schema: public; Owner: admin
--

CREATE VIEW public.vw_fiscal_documents_with_attempt AS
 SELECT fiscal_documents.id,
    fiscal_documents.order_id,
    fiscal_documents.receipt_code,
    fiscal_documents.document_type,
    fiscal_documents.channel,
    fiscal_documents.region,
    fiscal_documents.amount_cents,
    fiscal_documents.currency,
    fiscal_documents.delivery_mode,
    fiscal_documents.send_status,
    fiscal_documents.send_target,
    fiscal_documents.print_status,
    fiscal_documents.print_site_path,
    fiscal_documents.payload_json,
    fiscal_documents.issued_at,
    fiscal_documents.created_at,
    fiscal_documents.updated_at,
    fiscal_documents.attempt,
    fiscal_documents.previous_receipt_code,
    fiscal_documents.regenerated_at,
    fiscal_documents.regenerate_reason,
        CASE
            WHEN (fiscal_documents.attempt = 1) THEN 'PRIMEIRA_EMISSAO'::text
            ELSE 'REIMPRESSAO'::text
        END AS emission_type
   FROM public.fiscal_documents;


ALTER TABLE public.vw_fiscal_documents_with_attempt OWNER TO admin;

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
-- Name: wallet_provider_catalog_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.wallet_provider_catalog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.wallet_provider_catalog_id_seq OWNER TO admin;

--
-- Name: wallet_provider_catalog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.wallet_provider_catalog_id_seq OWNED BY public.wallet_provider_catalog.id;


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
-- Name: auth_sessions id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.auth_sessions ALTER COLUMN id SET DEFAULT nextval('public.auth_sessions_id_seq'::regclass);


--
-- Name: capability_channel id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_channel ALTER COLUMN id SET DEFAULT nextval('public.capability_channel_id_seq'::regclass);


--
-- Name: capability_context id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_context ALTER COLUMN id SET DEFAULT nextval('public.capability_context_id_seq'::regclass);


--
-- Name: capability_country id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_country ALTER COLUMN id SET DEFAULT nextval('public.capability_country_id_seq'::regclass);


--
-- Name: capability_locker_location id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_locker_location ALTER COLUMN id SET DEFAULT nextval('public.capability_locker_location_id_seq'::regclass);


--
-- Name: capability_profile id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile ALTER COLUMN id SET DEFAULT nextval('public.capability_profile_id_seq'::regclass);


--
-- Name: capability_profile_action id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_action ALTER COLUMN id SET DEFAULT nextval('public.capability_profile_action_id_seq'::regclass);


--
-- Name: capability_profile_constraint id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_constraint ALTER COLUMN id SET DEFAULT nextval('public.capability_profile_constraint_id_seq'::regclass);


--
-- Name: capability_profile_method id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method ALTER COLUMN id SET DEFAULT nextval('public.capability_profile_method_id_seq'::regclass);


--
-- Name: capability_profile_method_interface id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_interface ALTER COLUMN id SET DEFAULT nextval('public.capability_profile_method_interface_id_seq'::regclass);


--
-- Name: capability_profile_method_requirement id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_requirement ALTER COLUMN id SET DEFAULT nextval('public.capability_profile_method_requirement_id_seq'::regclass);


--
-- Name: capability_profile_snapshot id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_snapshot ALTER COLUMN id SET DEFAULT nextval('public.capability_profile_snapshot_id_seq1'::regclass);


--
-- Name: capability_profile_snapshot_old id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_snapshot_old ALTER COLUMN id SET DEFAULT nextval('public.capability_profile_snapshot_id_seq'::regclass);


--
-- Name: capability_profile_target id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_target ALTER COLUMN id SET DEFAULT nextval('public.capability_profile_target_id_seq'::regclass);


--
-- Name: capability_province id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_province ALTER COLUMN id SET DEFAULT nextval('public.capability_province_id_seq'::regclass);


--
-- Name: capability_region id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_region ALTER COLUMN id SET DEFAULT nextval('public.capability_region_id_seq'::regclass);


--
-- Name: capability_requirement_catalog id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_requirement_catalog ALTER COLUMN id SET DEFAULT nextval('public.capability_requirement_catalog_id_seq'::regclass);


--
-- Name: locker_slot_configs id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_slot_configs ALTER COLUMN id SET DEFAULT nextval('public.locker_slot_configs_id_seq'::regclass);


--
-- Name: locker_telemetry id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_telemetry ALTER COLUMN id SET DEFAULT nextval('public.locker_telemetry_id_seq'::regclass);


--
-- Name: notification_logs id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.notification_logs ALTER COLUMN id SET DEFAULT nextval('public.notification_logs_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: payment_interface_catalog id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_interface_catalog ALTER COLUMN id SET DEFAULT nextval('public.payment_interface_catalog_id_seq'::regclass);


--
-- Name: payment_method_catalog id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_method_catalog ALTER COLUMN id SET DEFAULT nextval('public.payment_method_catalog_id_seq'::regclass);


--
-- Name: pickup_events id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.pickup_events ALTER COLUMN id SET DEFAULT nextval('public.pickup_events_id_seq'::regclass);


--
-- Name: product_locker_configs id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.product_locker_configs ALTER COLUMN id SET DEFAULT nextval('public.product_locker_configs_id_seq'::regclass);


--
-- Name: wallet_provider_catalog id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.wallet_provider_catalog ALTER COLUMN id SET DEFAULT nextval('public.wallet_provider_catalog_id_seq'::regclass);


--
-- Name: allocations allocations_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.allocations
    ADD CONSTRAINT allocations_pkey PRIMARY KEY (id);


--
-- Name: analytics_facts analytics_facts_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.analytics_facts
    ADD CONSTRAINT analytics_facts_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: auth_sessions auth_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_pkey PRIMARY KEY (id);


--
-- Name: billing_processed_events billing_processed_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.billing_processed_events
    ADD CONSTRAINT billing_processed_events_pkey PRIMARY KEY (id);


--
-- Name: capability_channel capability_channel_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_channel
    ADD CONSTRAINT capability_channel_code_key UNIQUE (code);


--
-- Name: capability_channel capability_channel_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_channel
    ADD CONSTRAINT capability_channel_pkey PRIMARY KEY (id);


--
-- Name: capability_context capability_context_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_context
    ADD CONSTRAINT capability_context_pkey PRIMARY KEY (id);


--
-- Name: capability_country capability_country_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_country
    ADD CONSTRAINT capability_country_code_key UNIQUE (code);


--
-- Name: capability_country capability_country_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_country
    ADD CONSTRAINT capability_country_pkey PRIMARY KEY (id);


--
-- Name: capability_locker_location capability_locker_location_external_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_locker_location
    ADD CONSTRAINT capability_locker_location_external_id_key UNIQUE (external_id);


--
-- Name: capability_locker_location capability_locker_location_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_locker_location
    ADD CONSTRAINT capability_locker_location_pkey PRIMARY KEY (id);


--
-- Name: capability_profile_action capability_profile_action_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_action
    ADD CONSTRAINT capability_profile_action_pkey PRIMARY KEY (id);


--
-- Name: capability_profile_constraint capability_profile_constraint_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_constraint
    ADD CONSTRAINT capability_profile_constraint_pkey PRIMARY KEY (id);


--
-- Name: capability_profile_method_interface capability_profile_method_interface_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_interface
    ADD CONSTRAINT capability_profile_method_interface_pkey PRIMARY KEY (id);


--
-- Name: capability_profile_method capability_profile_method_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method
    ADD CONSTRAINT capability_profile_method_pkey PRIMARY KEY (id);


--
-- Name: capability_profile_method_requirement capability_profile_method_requirement_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_requirement
    ADD CONSTRAINT capability_profile_method_requirement_pkey PRIMARY KEY (id);


--
-- Name: capability_profile capability_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile
    ADD CONSTRAINT capability_profile_pkey PRIMARY KEY (id);


--
-- Name: capability_profile capability_profile_profile_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile
    ADD CONSTRAINT capability_profile_profile_code_key UNIQUE (profile_code);


--
-- Name: capability_profile_snapshot_old capability_profile_snapshot_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_snapshot_old
    ADD CONSTRAINT capability_profile_snapshot_pkey PRIMARY KEY (id);


--
-- Name: capability_profile_snapshot capability_profile_snapshot_pkey1; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_snapshot
    ADD CONSTRAINT capability_profile_snapshot_pkey1 PRIMARY KEY (id);


--
-- Name: capability_profile_target capability_profile_target_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_target
    ADD CONSTRAINT capability_profile_target_pkey PRIMARY KEY (id);


--
-- Name: capability_province capability_province_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_province
    ADD CONSTRAINT capability_province_code_key UNIQUE (code);


--
-- Name: capability_province capability_province_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_province
    ADD CONSTRAINT capability_province_pkey PRIMARY KEY (id);


--
-- Name: capability_region capability_region_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_region
    ADD CONSTRAINT capability_region_code_key UNIQUE (code);


--
-- Name: capability_region capability_region_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_region
    ADD CONSTRAINT capability_region_pkey PRIMARY KEY (id);


--
-- Name: capability_requirement_catalog capability_requirement_catalog_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_requirement_catalog
    ADD CONSTRAINT capability_requirement_catalog_code_key UNIQUE (code);


--
-- Name: capability_requirement_catalog capability_requirement_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_requirement_catalog
    ADD CONSTRAINT capability_requirement_catalog_pkey PRIMARY KEY (id);


--
-- Name: credits credits_order_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.credits
    ADD CONSTRAINT credits_order_id_key UNIQUE (order_id);


--
-- Name: credits credits_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.credits
    ADD CONSTRAINT credits_pkey PRIMARY KEY (id);


--
-- Name: data_deletion_requests data_deletion_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.data_deletion_requests
    ADD CONSTRAINT data_deletion_requests_pkey PRIMARY KEY (id);


--
-- Name: device_registry device_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.device_registry
    ADD CONSTRAINT device_registry_pkey PRIMARY KEY (device_hash);


--
-- Name: domain_event_outbox domain_event_outbox_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.domain_event_outbox
    ADD CONSTRAINT domain_event_outbox_pkey PRIMARY KEY (id);


--
-- Name: domain_events domain_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.domain_events
    ADD CONSTRAINT domain_events_pkey PRIMARY KEY (id);


--
-- Name: door_state door_state_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.door_state
    ADD CONSTRAINT door_state_pkey PRIMARY KEY (machine_id, door_id);


--
-- Name: ecommerce_partners ecommerce_partners_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.ecommerce_partners
    ADD CONSTRAINT ecommerce_partners_code_key UNIQUE (code);


--
-- Name: ecommerce_partners ecommerce_partners_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.ecommerce_partners
    ADD CONSTRAINT ecommerce_partners_pkey PRIMARY KEY (id);


--
-- Name: financial_ledger financial_ledger_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.financial_ledger
    ADD CONSTRAINT financial_ledger_pkey PRIMARY KEY (id);


--
-- Name: fiscal_documents fiscal_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fiscal_documents
    ADD CONSTRAINT fiscal_documents_pkey PRIMARY KEY (id);


--
-- Name: fiscal_documents fiscal_documents_receipt_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.fiscal_documents
    ADD CONSTRAINT fiscal_documents_receipt_code_key UNIQUE (receipt_code);


--
-- Name: idempotency_keys idempotency_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.idempotency_keys
    ADD CONSTRAINT idempotency_keys_pkey PRIMARY KEY (id);


--
-- Name: inbound_deliveries inbound_deliveries_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.inbound_deliveries
    ADD CONSTRAINT inbound_deliveries_pkey PRIMARY KEY (id);


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);


--
-- Name: kiosk_antifraud_events kiosk_antifraud_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.kiosk_antifraud_events
    ADD CONSTRAINT kiosk_antifraud_events_pkey PRIMARY KEY (id);


--
-- Name: lifecycle_deadlines lifecycle_deadlines_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.lifecycle_deadlines
    ADD CONSTRAINT lifecycle_deadlines_pkey PRIMARY KEY (id);


--
-- Name: locker_operators locker_operators_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_operators
    ADD CONSTRAINT locker_operators_pkey PRIMARY KEY (id);


--
-- Name: locker_payment_methods locker_payment_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_payment_methods
    ADD CONSTRAINT locker_payment_methods_pkey PRIMARY KEY (locker_id, method);


--
-- Name: locker_slot_configs locker_slot_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_slot_configs
    ADD CONSTRAINT locker_slot_configs_pkey PRIMARY KEY (id);


--
-- Name: locker_slots locker_slots_locker_id_slot_label_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_slots
    ADD CONSTRAINT locker_slots_locker_id_slot_label_key UNIQUE (locker_id, slot_label);


--
-- Name: locker_slots locker_slots_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_slots
    ADD CONSTRAINT locker_slots_pkey PRIMARY KEY (id);


--
-- Name: locker_telemetry locker_telemetry_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_telemetry
    ADD CONSTRAINT locker_telemetry_pkey PRIMARY KEY (id);


--
-- Name: lockers lockers_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.lockers
    ADD CONSTRAINT lockers_pkey PRIMARY KEY (id);


--
-- Name: login_otps login_otps_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.login_otps
    ADD CONSTRAINT login_otps_pkey PRIMARY KEY (id);


--
-- Name: logistics_partners logistics_partners_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.logistics_partners
    ADD CONSTRAINT logistics_partners_code_key UNIQUE (code);


--
-- Name: logistics_partners logistics_partners_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.logistics_partners
    ADD CONSTRAINT logistics_partners_pkey PRIMARY KEY (id);


--
-- Name: notification_logs notification_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.notification_logs
    ADD CONSTRAINT notification_logs_pkey PRIMARY KEY (id);


--
-- Name: ops_action_audit ops_action_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.ops_action_audit
    ADD CONSTRAINT ops_action_audit_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: payment_gateway_device_registry payment_gateway_device_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_gateway_device_registry
    ADD CONSTRAINT payment_gateway_device_registry_pkey PRIMARY KEY (device_hash);


--
-- Name: payment_gateway_idempotency_keys payment_gateway_idempotency_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_gateway_idempotency_keys
    ADD CONSTRAINT payment_gateway_idempotency_keys_pkey PRIMARY KEY (id);


--
-- Name: payment_gateway_risk_events payment_gateway_risk_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_gateway_risk_events
    ADD CONSTRAINT payment_gateway_risk_events_pkey PRIMARY KEY (id);


--
-- Name: payment_instructions payment_instructions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_instructions
    ADD CONSTRAINT payment_instructions_pkey PRIMARY KEY (id);


--
-- Name: payment_interface_catalog payment_interface_catalog_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_interface_catalog
    ADD CONSTRAINT payment_interface_catalog_code_key UNIQUE (code);


--
-- Name: payment_interface_catalog payment_interface_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_interface_catalog
    ADD CONSTRAINT payment_interface_catalog_pkey PRIMARY KEY (id);


--
-- Name: payment_method_catalog payment_method_catalog_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_method_catalog
    ADD CONSTRAINT payment_method_catalog_code_key UNIQUE (code);


--
-- Name: payment_method_catalog payment_method_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_method_catalog
    ADD CONSTRAINT payment_method_catalog_pkey PRIMARY KEY (id);


--
-- Name: payment_method_ui_alias payment_method_ui_alias_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_method_ui_alias
    ADD CONSTRAINT payment_method_ui_alias_pkey PRIMARY KEY (id);


--
-- Name: payment_method_ui_alias payment_method_ui_alias_ui_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_method_ui_alias
    ADD CONSTRAINT payment_method_ui_alias_ui_code_key UNIQUE (ui_code);


--
-- Name: payment_splits payment_splits_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_splits
    ADD CONSTRAINT payment_splits_pkey PRIMARY KEY (id);


--
-- Name: payment_transactions payment_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_transactions
    ADD CONSTRAINT payment_transactions_pkey PRIMARY KEY (id);


--
-- Name: pickup_events pickup_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.pickup_events
    ADD CONSTRAINT pickup_events_pkey PRIMARY KEY (id);


--
-- Name: pickup_tokens pickup_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.pickup_tokens
    ADD CONSTRAINT pickup_tokens_pkey PRIMARY KEY (id);


--
-- Name: pickups pickups_order_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.pickups
    ADD CONSTRAINT pickups_order_id_key UNIQUE (order_id);


--
-- Name: pickups pickups_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.pickups
    ADD CONSTRAINT pickups_pkey PRIMARY KEY (id);


--
-- Name: pricing_rules pricing_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.pricing_rules
    ADD CONSTRAINT pricing_rules_pkey PRIMARY KEY (id);


--
-- Name: privacy_consents privacy_consents_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.privacy_consents
    ADD CONSTRAINT privacy_consents_pkey PRIMARY KEY (id);


--
-- Name: product_categories product_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_pkey PRIMARY KEY (id);


--
-- Name: product_locker_configs product_locker_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.product_locker_configs
    ADD CONSTRAINT product_locker_configs_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: reconciliation_pending reconciliation_pending_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.reconciliation_pending
    ADD CONSTRAINT reconciliation_pending_pkey PRIMARY KEY (id);


--
-- Name: rental_contracts rental_contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.rental_contracts
    ADD CONSTRAINT rental_contracts_pkey PRIMARY KEY (id);


--
-- Name: rental_plans rental_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.rental_plans
    ADD CONSTRAINT rental_plans_pkey PRIMARY KEY (id);


--
-- Name: risk_events risk_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.risk_events
    ADD CONSTRAINT risk_events_pkey PRIMARY KEY (id);


--
-- Name: runtime_locker_features runtime_locker_features_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.runtime_locker_features
    ADD CONSTRAINT runtime_locker_features_pkey PRIMARY KEY (locker_id);


--
-- Name: runtime_locker_slots runtime_locker_slots_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.runtime_locker_slots
    ADD CONSTRAINT runtime_locker_slots_pkey PRIMARY KEY (locker_id, slot_number);


--
-- Name: runtime_lockers runtime_lockers_machine_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.runtime_lockers
    ADD CONSTRAINT runtime_lockers_machine_id_key UNIQUE (machine_id);


--
-- Name: runtime_lockers runtime_lockers_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.runtime_lockers
    ADD CONSTRAINT runtime_lockers_pkey PRIMARY KEY (locker_id);


--
-- Name: saved_payment_methods saved_payment_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.saved_payment_methods
    ADD CONSTRAINT saved_payment_methods_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (name);


--
-- Name: slot_occupancy_history slot_occupancy_history_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.slot_occupancy_history
    ADD CONSTRAINT slot_occupancy_history_pkey PRIMARY KEY (id);


--
-- Name: analytics_facts uq_analytics_facts_fact_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.analytics_facts
    ADD CONSTRAINT uq_analytics_facts_fact_key UNIQUE (fact_key);


--
-- Name: billing_processed_events uq_billing_processed_event_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.billing_processed_events
    ADD CONSTRAINT uq_billing_processed_event_key UNIQUE (event_key);


--
-- Name: capability_context uq_capability_context_channel_code; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_context
    ADD CONSTRAINT uq_capability_context_channel_code UNIQUE (channel_id, code);


--
-- Name: capability_profile_action uq_capability_profile_action; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_action
    ADD CONSTRAINT uq_capability_profile_action UNIQUE (profile_id, action_code);


--
-- Name: capability_profile_constraint uq_capability_profile_constraint; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_constraint
    ADD CONSTRAINT uq_capability_profile_constraint UNIQUE (profile_id, code);


--
-- Name: capability_profile_method uq_capability_profile_method; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method
    ADD CONSTRAINT uq_capability_profile_method UNIQUE (profile_id, payment_method_id);


--
-- Name: capability_profile_method_interface uq_capability_profile_method_interface; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_interface
    ADD CONSTRAINT uq_capability_profile_method_interface UNIQUE (profile_method_id, payment_interface_id);


--
-- Name: capability_profile_method_requirement uq_capability_profile_method_requirement; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_requirement
    ADD CONSTRAINT uq_capability_profile_method_requirement UNIQUE (profile_method_id, requirement_id);


--
-- Name: capability_profile uq_capability_profile_region_channel_context; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile
    ADD CONSTRAINT uq_capability_profile_region_channel_context UNIQUE (region_id, channel_id, context_id);


--
-- Name: capability_profile_snapshot_old uq_capability_profile_snapshot; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_snapshot_old
    ADD CONSTRAINT uq_capability_profile_snapshot UNIQUE (profile_id, snapshot_version);


--
-- Name: capability_profile_target uq_capability_profile_target; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_target
    ADD CONSTRAINT uq_capability_profile_target UNIQUE (profile_id, target_type, target_key);


--
-- Name: domain_events uq_domain_events_event_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.domain_events
    ADD CONSTRAINT uq_domain_events_event_key UNIQUE (event_key);


--
-- Name: invoices uq_invoice_order; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT uq_invoice_order UNIQUE (order_id);


--
-- Name: lifecycle_deadlines uq_lifecycle_deadlines_deadline_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.lifecycle_deadlines
    ADD CONSTRAINT uq_lifecycle_deadlines_deadline_key UNIQUE (deadline_key);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: user_wallets user_wallets_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.user_wallets
    ADD CONSTRAINT user_wallets_pkey PRIMARY KEY (id);


--
-- Name: user_wallets user_wallets_user_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.user_wallets
    ADD CONSTRAINT user_wallets_user_id_key UNIQUE (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: wallet_provider_catalog wallet_provider_catalog_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.wallet_provider_catalog
    ADD CONSTRAINT wallet_provider_catalog_code_key UNIQUE (code);


--
-- Name: wallet_provider_catalog wallet_provider_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.wallet_provider_catalog
    ADD CONSTRAINT wallet_provider_catalog_pkey PRIMARY KEY (id);


--
-- Name: wallet_transactions wallet_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.wallet_transactions
    ADD CONSTRAINT wallet_transactions_pkey PRIMARY KEY (id);


--
-- Name: webhook_deliveries webhook_deliveries_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.webhook_deliveries
    ADD CONSTRAINT webhook_deliveries_pkey PRIMARY KEY (id);


--
-- Name: webhook_endpoints webhook_endpoints_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.webhook_endpoints
    ADD CONSTRAINT webhook_endpoints_pkey PRIMARY KEY (id);


--
-- Name: idx_allocations_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_allocations_created_at ON public.allocations USING btree (created_at);


--
-- Name: idx_allocations_locker_slot_state; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_allocations_locker_slot_state ON public.allocations USING btree (locker_id, slot, state);


--
-- Name: idx_allocations_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_allocations_order_id ON public.allocations USING btree (order_id);


--
-- Name: idx_allocations_state; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_allocations_state ON public.allocations USING btree (state);


--
-- Name: idx_country_code; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_country_code ON public.capability_country USING btree (code);


--
-- Name: idx_country_continent; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_country_continent ON public.capability_country USING btree (continent);


--
-- Name: idx_country_continent_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_country_continent_active ON public.capability_country USING btree (continent, is_active);


--
-- Name: idx_country_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_country_created_at ON public.capability_country USING btree (created_at);


--
-- Name: idx_country_is_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_country_is_active ON public.capability_country USING btree (is_active);


--
-- Name: idx_country_metadata_gin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_country_metadata_gin ON public.capability_country USING gin (metadata_json);


--
-- Name: idx_door_state_machine; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_door_state_machine ON public.door_state USING btree (machine_id);


--
-- Name: idx_door_state_machine_state; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_door_state_machine_state ON public.door_state USING btree (machine_id, state);


--
-- Name: idx_fiscal_order_attempt; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_fiscal_order_attempt ON public.fiscal_documents USING btree (order_id, attempt);


--
-- Name: idx_locker_24h_only; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_24h_only ON public.capability_locker_location USING btree (id) WHERE ((metadata_json ->> 'is_24h'::text) = 'true'::text);


--
-- Name: idx_locker_active_only; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_active_only ON public.capability_locker_location USING btree (id) WHERE (is_active = true);


--
-- Name: idx_locker_address_search_en; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_address_search_en ON public.capability_locker_location USING gin (to_tsvector('english'::regconfig, (((((COALESCE(address_street, ''::character varying))::text || ' '::text) || (COALESCE(city_name, ''::character varying))::text) || ' '::text) || (COALESCE(district, ''::character varying))::text)));


--
-- Name: idx_locker_address_search_pt; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_address_search_pt ON public.capability_locker_location USING gin (to_tsvector('portuguese'::regconfig, (((((((((COALESCE(address_street, ''::character varying))::text || ' '::text) || (COALESCE(address_number, ''::character varying))::text) || ' '::text) || (COALESCE(city_name, ''::character varying))::text) || ' '::text) || (COALESCE(district, ''::character varying))::text) || ' '::text) || (COALESCE(postal_code, ''::character varying))::text)));


--
-- Name: idx_locker_city_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_city_active ON public.capability_locker_location USING btree (city_name, is_active);


--
-- Name: idx_locker_city_district; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_city_district ON public.capability_locker_location USING btree (city_name, district);


--
-- Name: idx_locker_city_name; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_city_name ON public.capability_locker_location USING btree (city_name);


--
-- Name: idx_locker_coords; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_coords ON public.capability_locker_location USING btree (latitude, longitude);


--
-- Name: idx_locker_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_created_at ON public.capability_locker_location USING btree (created_at);


--
-- Name: idx_locker_district; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_district ON public.capability_locker_location USING btree (district);


--
-- Name: idx_locker_external_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_external_id ON public.capability_locker_location USING btree (external_id);


--
-- Name: idx_locker_geom_bbox; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_geom_bbox ON public.capability_locker_location USING gist (geom public.gist_geometry_ops_nd);


--
-- Name: idx_locker_geom_gist; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_geom_gist ON public.capability_locker_location USING gist (geom);


--
-- Name: idx_locker_has_geom; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_has_geom ON public.capability_locker_location USING btree (id) WHERE (geom IS NOT NULL);


--
-- Name: idx_locker_hours_gin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_hours_gin ON public.capability_locker_location USING gin (operating_hours_json);


--
-- Name: idx_locker_is_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_is_active ON public.capability_locker_location USING btree (is_active);


--
-- Name: idx_locker_metadata_gin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_metadata_gin ON public.capability_locker_location USING gin (metadata_json);


--
-- Name: idx_locker_metadata_is_24h; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_metadata_is_24h ON public.capability_locker_location USING btree (((metadata_json ->> 'is_24h'::text)));


--
-- Name: idx_locker_metadata_locker_size; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_metadata_locker_size ON public.capability_locker_location USING btree (((metadata_json ->> 'locker_size'::text)));


--
-- Name: idx_locker_postal_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_postal_active ON public.capability_locker_location USING btree (postal_code, is_active);


--
-- Name: idx_locker_postal_code; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_postal_code ON public.capability_locker_location USING btree (postal_code);


--
-- Name: idx_locker_province_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_province_active ON public.capability_locker_location USING btree (province_code, is_active);


--
-- Name: idx_locker_province_code; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_province_code ON public.capability_locker_location USING btree (province_code);


--
-- Name: idx_locker_slot_locker; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_locker_slot_locker ON public.locker_slot_configs USING btree (locker_id);


--
-- Name: idx_lockers_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_lockers_active ON public.lockers USING btree (active);


--
-- Name: idx_lockers_operator; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_lockers_operator ON public.lockers USING btree (operator_id);


--
-- Name: idx_lockers_region; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_lockers_region ON public.lockers USING btree (region);


--
-- Name: idx_lockers_site_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_lockers_site_id ON public.lockers USING btree (site_id);


--
-- Name: idx_operator_document; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_operator_document ON public.locker_operators USING btree (document);


--
-- Name: idx_orders_channel_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_channel_status ON public.orders USING btree (channel, status);


--
-- Name: idx_orders_paid_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_paid_at ON public.orders USING btree (paid_at);


--
-- Name: idx_orders_picked_up_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_picked_up_at ON public.orders USING btree (picked_up_at);


--
-- Name: idx_orders_public_access_token_hash; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_public_access_token_hash ON public.orders USING btree (public_access_token_hash);


--
-- Name: idx_orders_region_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_region_status ON public.orders USING btree (region, status);


--
-- Name: idx_orders_region_totem_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_region_totem_created_at ON public.orders USING btree (region, totem_id, created_at);


--
-- Name: idx_orders_region_totem_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_region_totem_status ON public.orders USING btree (region, totem_id, status);


--
-- Name: idx_orders_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_status ON public.orders USING btree (status);


--
-- Name: idx_orders_status_picked_up; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_status_picked_up ON public.orders USING btree (status, picked_up_at);


--
-- Name: idx_orders_totem_picked_up; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_orders_totem_picked_up ON public.orders USING btree (totem_id, picked_up_at);


--
-- Name: idx_pmui_ui_code; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_pmui_ui_code ON public.payment_method_ui_alias USING btree (ui_code);


--
-- Name: idx_product_categories_parent; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_product_categories_parent ON public.product_categories USING btree (parent_category);


--
-- Name: idx_product_config_category; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_product_config_category ON public.product_locker_configs USING btree (category);


--
-- Name: idx_product_config_locker; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_product_config_locker ON public.product_locker_configs USING btree (locker_id);


--
-- Name: idx_products_category; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_products_category ON public.products USING btree (category_id);


--
-- Name: idx_products_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_products_created_at ON public.products USING btree (created_at);


--
-- Name: idx_products_is_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_products_is_active ON public.products USING btree (is_active);


--
-- Name: idx_province_active_only; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_active_only ON public.capability_province USING btree (country_code) WHERE (is_active = true);


--
-- Name: idx_province_code; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_code ON public.capability_province USING btree (code);


--
-- Name: idx_province_country_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_country_active ON public.capability_province USING btree (country_code, is_active);


--
-- Name: idx_province_country_code; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_country_code ON public.capability_province USING btree (country_code);


--
-- Name: idx_province_country_region; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_country_region ON public.capability_province USING btree (country_code, region);


--
-- Name: idx_province_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_created_at ON public.capability_province USING btree (created_at);


--
-- Name: idx_province_is_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_is_active ON public.capability_province USING btree (is_active);


--
-- Name: idx_province_metadata_gin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_metadata_gin ON public.capability_province USING gin (metadata_json);


--
-- Name: idx_province_province_code_original; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_province_code_original ON public.capability_province USING btree (province_code_original);


--
-- Name: idx_province_region; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_province_region ON public.capability_province USING btree (region);


--
-- Name: idx_runtime_locker_slots_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_runtime_locker_slots_active ON public.runtime_locker_slots USING btree (locker_id, is_active, slot_number);


--
-- Name: idx_runtime_lockers_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_runtime_lockers_active ON public.runtime_lockers USING btree (active, runtime_enabled);


--
-- Name: idx_runtime_lockers_region; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_runtime_lockers_region ON public.runtime_lockers USING btree (region);


--
-- Name: ix_alloc_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_alloc_created_at ON public.allocations USING btree (created_at);


--
-- Name: ix_alloc_locker_slot_state; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_alloc_locker_slot_state ON public.allocations USING btree (locker_id, slot, state);


--
-- Name: ix_alloc_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_alloc_order_id ON public.allocations USING btree (order_id);


--
-- Name: ix_alloc_state; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_alloc_state ON public.allocations USING btree (state);


--
-- Name: ix_allocations_allocated_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_allocations_allocated_at ON public.allocations USING btree (allocated_at);


--
-- Name: ix_allocations_released_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_allocations_released_at ON public.allocations USING btree (released_at);


--
-- Name: ix_analytics_facts_fact_name_occurred_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_analytics_facts_fact_name_occurred_at ON public.analytics_facts USING btree (fact_name, occurred_at);


--
-- Name: ix_analytics_facts_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_analytics_facts_order_id ON public.analytics_facts USING btree (order_id);


--
-- Name: ix_audit_actor_time; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_audit_actor_time ON public.audit_logs USING btree (actor_id, occurred_at DESC);


--
-- Name: ix_audit_logs_new_state_gin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_audit_logs_new_state_gin ON public.audit_logs USING gin (new_state);


--
-- Name: ix_audit_logs_old_state_gin; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_audit_logs_old_state_gin ON public.audit_logs USING gin (old_state);


--
-- Name: ix_audit_target; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_audit_target ON public.audit_logs USING btree (target_type, target_id);


--
-- Name: ix_auth_sessions_expires_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_auth_sessions_expires_at ON public.auth_sessions USING btree (expires_at) WHERE (revoked_at IS NULL);


--
-- Name: ix_auth_sessions_session_token_hash; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_auth_sessions_session_token_hash ON public.auth_sessions USING btree (session_token_hash);


--
-- Name: ix_auth_sessions_user_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_auth_sessions_user_id ON public.auth_sessions USING btree (user_id);


--
-- Name: ix_billing_processed_events_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_billing_processed_events_order_id ON public.billing_processed_events USING btree (order_id);


--
-- Name: ix_cap_context_channel; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_context_channel ON public.capability_context USING btree (channel_id);


--
-- Name: ix_cap_profile_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_profile_active ON public.capability_profile USING btree (is_active, valid_from, valid_until);


--
-- Name: ix_cap_profile_channel; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_profile_channel ON public.capability_profile USING btree (channel_id);


--
-- Name: ix_cap_profile_region; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_profile_region ON public.capability_profile USING btree (region_id);


--
-- Name: ix_cap_region_country; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_region_country ON public.capability_region USING btree (country_code);


--
-- Name: ix_cap_snapshot_code_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_snapshot_code_status ON public.capability_profile_snapshot USING btree (profile_code, status);


--
-- Name: ix_cap_snapshot_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_snapshot_created_at ON public.capability_profile_snapshot USING btree (created_at);


--
-- Name: ix_cap_snapshot_locker; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_snapshot_locker ON public.capability_profile_snapshot USING btree (locker_id, status);


--
-- Name: ix_cap_snapshot_profile_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_snapshot_profile_id ON public.capability_profile_snapshot USING btree (profile_id);


--
-- Name: ix_cap_snapshot_profile_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cap_snapshot_profile_status ON public.capability_profile_snapshot USING btree (profile_id, status);


--
-- Name: ix_capability_channel_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_channel_active ON public.capability_channel USING btree (is_active);


--
-- Name: ix_capability_context_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_context_active ON public.capability_context USING btree (is_active);


--
-- Name: ix_capability_context_channel; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_context_channel ON public.capability_context USING btree (channel_id);


--
-- Name: ix_capability_profile_action_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_action_active ON public.capability_profile_action USING btree (is_active);


--
-- Name: ix_capability_profile_action_profile; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_action_profile ON public.capability_profile_action USING btree (profile_id);


--
-- Name: ix_capability_profile_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_active ON public.capability_profile USING btree (is_active);


--
-- Name: ix_capability_profile_channel; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_channel ON public.capability_profile USING btree (channel_id);


--
-- Name: ix_capability_profile_constraint_profile; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_constraint_profile ON public.capability_profile_constraint USING btree (profile_id);


--
-- Name: ix_capability_profile_context; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_context ON public.capability_profile USING btree (context_id);


--
-- Name: ix_capability_profile_method_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_method_active ON public.capability_profile_method USING btree (is_active);


--
-- Name: ix_capability_profile_method_interface_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_method_interface_active ON public.capability_profile_method_interface USING btree (is_active);


--
-- Name: ix_capability_profile_method_interface_interface; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_method_interface_interface ON public.capability_profile_method_interface USING btree (payment_interface_id);


--
-- Name: ix_capability_profile_method_interface_profile_method; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_method_interface_profile_method ON public.capability_profile_method_interface USING btree (profile_method_id);


--
-- Name: ix_capability_profile_method_payment_method; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_method_payment_method ON public.capability_profile_method USING btree (payment_method_id);


--
-- Name: ix_capability_profile_method_profile; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_method_profile ON public.capability_profile_method USING btree (profile_id);


--
-- Name: ix_capability_profile_method_requirement_profile_method; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_method_requirement_profile_method ON public.capability_profile_method_requirement USING btree (profile_method_id);


--
-- Name: ix_capability_profile_method_requirement_requirement; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_method_requirement_requirement ON public.capability_profile_method_requirement USING btree (requirement_id);


--
-- Name: ix_capability_profile_method_wallet_provider; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_method_wallet_provider ON public.capability_profile_method USING btree (wallet_provider_id);


--
-- Name: ix_capability_profile_priority; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_priority ON public.capability_profile USING btree (priority);


--
-- Name: ix_capability_profile_region; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_region ON public.capability_profile USING btree (region_id);


--
-- Name: ix_capability_profile_snapshot_profile; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_snapshot_profile ON public.capability_profile_snapshot_old USING btree (profile_id);


--
-- Name: ix_capability_profile_target_profile; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_target_profile ON public.capability_profile_target USING btree (profile_id);


--
-- Name: ix_capability_profile_target_type_key; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_profile_target_type_key ON public.capability_profile_target USING btree (target_type, target_key);


--
-- Name: ix_capability_region_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_region_active ON public.capability_region USING btree (is_active);


--
-- Name: ix_capability_region_country; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_region_country ON public.capability_region USING btree (country_code);


--
-- Name: ix_capability_requirement_catalog_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_capability_requirement_catalog_active ON public.capability_requirement_catalog USING btree (is_active);


--
-- Name: ix_consents_guest; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_consents_guest ON public.privacy_consents USING btree (guest_identifier);


--
-- Name: ix_consents_type; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_consents_type ON public.privacy_consents USING btree (consent_type);


--
-- Name: ix_consents_user; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_consents_user ON public.privacy_consents USING btree (user_id);


--
-- Name: ix_cpa_profile; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cpa_profile ON public.capability_profile_action USING btree (profile_id, is_active);


--
-- Name: ix_cpconstraint_profile; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cpconstraint_profile ON public.capability_profile_constraint USING btree (profile_id);


--
-- Name: ix_cpm_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cpm_active ON public.capability_profile_method USING btree (profile_id, is_active);


--
-- Name: ix_cpm_method; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cpm_method ON public.capability_profile_method USING btree (payment_method_id);


--
-- Name: ix_cpm_profile; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cpm_profile ON public.capability_profile_method USING btree (profile_id);


--
-- Name: ix_cpmi_method; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cpmi_method ON public.capability_profile_method_interface USING btree (profile_method_id);


--
-- Name: ix_cpmr_method; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cpmr_method ON public.capability_profile_method_requirement USING btree (profile_method_id);


--
-- Name: ix_cpt_locker_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cpt_locker_id ON public.capability_profile_target USING btree (locker_id);


--
-- Name: ix_cpt_target; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_cpt_target ON public.capability_profile_target USING btree (target_type, target_key);


--
-- Name: ix_credits_expires_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_credits_expires_at ON public.credits USING btree (expires_at);


--
-- Name: ix_credits_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_credits_status ON public.credits USING btree (status);


--
-- Name: ix_credits_user_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_credits_user_id ON public.credits USING btree (user_id);


--
-- Name: ix_credits_user_status_expires; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_credits_user_status_expires ON public.credits USING btree (user_id, status, expires_at);


--
-- Name: ix_deletion_req_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_deletion_req_status ON public.data_deletion_requests USING btree (status);


--
-- Name: ix_deletion_req_user; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_deletion_req_user ON public.data_deletion_requests USING btree (user_id);


--
-- Name: ix_device_last_seen; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_device_last_seen ON public.device_registry USING btree (last_seen_at);


--
-- Name: ix_domain_events_aggregate_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_domain_events_aggregate_id ON public.domain_events USING btree (aggregate_id);


--
-- Name: ix_domain_events_status_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_domain_events_status_created_at ON public.domain_events USING btree (status, created_at);


--
-- Name: ix_fiscal_docs_issued; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fiscal_docs_issued ON public.fiscal_documents USING btree (issued_at);


--
-- Name: ix_fiscal_docs_receipt; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fiscal_docs_receipt ON public.fiscal_documents USING btree (receipt_code);


--
-- Name: ix_fiscal_documents_chave_acesso; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fiscal_documents_chave_acesso ON public.fiscal_documents USING btree (chave_acesso);


--
-- Name: ix_fiscal_documents_tenant_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_fiscal_documents_tenant_id ON public.fiscal_documents USING btree (tenant_id);


--
-- Name: ix_idem_expires; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_idem_expires ON public.idempotency_keys USING btree (expires_at);


--
-- Name: ix_inbound_deadline; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_inbound_deadline ON public.inbound_deliveries USING btree (pickup_deadline_at) WHERE ((status)::text <> ALL ((ARRAY['PICKED_UP'::character varying, 'RETURNED'::character varying, 'EXPIRED'::character varying])::text[]));


--
-- Name: ix_inbound_locker_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_inbound_locker_status ON public.inbound_deliveries USING btree (locker_id, status);


--
-- Name: ix_inbound_recipient_phone; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_inbound_recipient_phone ON public.inbound_deliveries USING btree (recipient_phone);


--
-- Name: ix_inbound_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_inbound_status ON public.inbound_deliveries USING btree (status);


--
-- Name: ix_invoice_country_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_invoice_country_status ON public.invoices USING btree (country, status);


--
-- Name: ix_invoice_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_invoice_created_at ON public.invoices USING btree (created_at);


--
-- Name: ix_invoice_next_retry_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_invoice_next_retry_at ON public.invoices USING btree (next_retry_at);


--
-- Name: ix_invoice_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_invoice_order_id ON public.invoices USING btree (order_id);


--
-- Name: ix_invoice_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_invoice_status ON public.invoices USING btree (status);


--
-- Name: ix_kiosk_antifraud_events_fp_hash; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_kiosk_antifraud_events_fp_hash ON public.kiosk_antifraud_events USING btree (fp_hash);


--
-- Name: ix_kiosk_antifraud_events_ip_hash; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_kiosk_antifraud_events_ip_hash ON public.kiosk_antifraud_events USING btree (ip_hash);


--
-- Name: ix_ledger_created; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_ledger_created ON public.financial_ledger USING btree (created_at DESC);


--
-- Name: ix_ledger_order; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_ledger_order ON public.financial_ledger USING btree (order_id);


--
-- Name: ix_ledger_type_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_ledger_type_status ON public.financial_ledger USING btree (entry_type, status);


--
-- Name: ix_lifecycle_deadlines_due_at_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lifecycle_deadlines_due_at_status ON public.lifecycle_deadlines USING btree (due_at, status);


--
-- Name: ix_lifecycle_deadlines_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lifecycle_deadlines_order_id ON public.lifecycle_deadlines USING btree (order_id);


--
-- Name: ix_locker_operators_document; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_locker_operators_document ON public.locker_operators USING btree (document);


--
-- Name: ix_locker_slots_locker_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_locker_slots_locker_status ON public.locker_slots USING btree (locker_id, status);


--
-- Name: ix_locker_slots_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_locker_slots_status ON public.locker_slots USING btree (status);


--
-- Name: ix_locker_telemetry_event_time; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_locker_telemetry_event_time ON public.locker_telemetry USING btree (event_type, occurred_at DESC);


--
-- Name: ix_locker_telemetry_locker_time; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_locker_telemetry_locker_time ON public.locker_telemetry USING btree (locker_id, occurred_at DESC);


--
-- Name: ix_lockers_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_active ON public.lockers USING btree (active);


--
-- Name: ix_lockers_has_kiosk; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_has_kiosk ON public.lockers USING btree (has_kiosk);


--
-- Name: ix_lockers_has_nfc; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_has_nfc ON public.lockers USING btree (has_nfc);


--
-- Name: ix_lockers_lat_lng; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_lat_lng ON public.lockers USING btree (latitude, longitude);


--
-- Name: ix_lockers_machine_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_machine_id ON public.lockers USING btree (machine_id);


--
-- Name: ix_lockers_operator; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_operator ON public.lockers USING btree (operator_id);


--
-- Name: ix_lockers_pickup_code_length; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_pickup_code_length ON public.lockers USING btree (pickup_code_length);


--
-- Name: ix_lockers_pickup_reuse_policy; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_pickup_reuse_policy ON public.lockers USING btree (pickup_reuse_policy);


--
-- Name: ix_lockers_region; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_region ON public.lockers USING btree (region);


--
-- Name: ix_lockers_site_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_site_id ON public.lockers USING btree (site_id);


--
-- Name: ix_lockers_slots_available; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_slots_available ON public.lockers USING btree (slots_available);


--
-- Name: ix_lockers_tenant_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_lockers_tenant_id ON public.lockers USING btree (tenant_id);


--
-- Name: ix_login_otps_email; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_login_otps_email ON public.login_otps USING btree (email);


--
-- Name: ix_login_otps_expires_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_login_otps_expires_at ON public.login_otps USING btree (expires_at);


--
-- Name: ix_login_otps_phone; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_login_otps_phone ON public.login_otps USING btree (phone);


--
-- Name: ix_notif_delivery; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notif_delivery ON public.notification_logs USING btree (delivery_id);


--
-- Name: ix_notif_next_attempt; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notif_next_attempt ON public.notification_logs USING btree (next_attempt_at);


--
-- Name: ix_notif_order; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notif_order ON public.notification_logs USING btree (order_id);


--
-- Name: ix_notif_pickup; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notif_pickup ON public.notification_logs USING btree (pickup_id);


--
-- Name: ix_notif_provider_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notif_provider_status ON public.notification_logs USING btree (provider_status);


--
-- Name: ix_notif_rental; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notif_rental ON public.notification_logs USING btree (rental_id);


--
-- Name: ix_notif_status_next; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notif_status_next ON public.notification_logs USING btree (status, next_attempt_at) WHERE ((status)::text = ANY ((ARRAY['QUEUED'::character varying, 'FAILED'::character varying])::text[]));


--
-- Name: ix_notification_logs_dedupe_key; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notification_logs_dedupe_key ON public.notification_logs USING btree (dedupe_key);


--
-- Name: ix_notification_logs_next_attempt_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notification_logs_next_attempt_at ON public.notification_logs USING btree (next_attempt_at);


--
-- Name: ix_notification_logs_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notification_logs_order_id ON public.notification_logs USING btree (order_id);


--
-- Name: ix_notification_logs_status_next_attempt_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notification_logs_status_next_attempt_at ON public.notification_logs USING btree (status, next_attempt_at);


--
-- Name: ix_notification_logs_user_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_notification_logs_user_id ON public.notification_logs USING btree (user_id);


--
-- Name: ix_ops_audit_action_result; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_ops_audit_action_result ON public.ops_action_audit USING btree (action, result);


--
-- Name: ix_ops_audit_corr_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_ops_audit_corr_id ON public.ops_action_audit USING btree (correlation_id);


--
-- Name: ix_ops_audit_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_ops_audit_created_at ON public.ops_action_audit USING btree (created_at);


--
-- Name: ix_ops_audit_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_ops_audit_order_id ON public.ops_action_audit USING btree (order_id);


--
-- Name: ix_order_items_item_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_order_items_item_status ON public.order_items USING btree (item_status);


--
-- Name: ix_order_items_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_order_items_order_id ON public.order_items USING btree (order_id);


--
-- Name: ix_order_items_order_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_order_items_order_status ON public.order_items USING btree (order_id, item_status);


--
-- Name: ix_order_items_sku_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_order_items_sku_id ON public.order_items USING btree (sku_id);


--
-- Name: ix_order_items_slot_preference; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_order_items_slot_preference ON public.order_items USING btree (slot_preference);


--
-- Name: ix_order_items_slot_size; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_order_items_slot_size ON public.order_items USING btree (slot_size);


--
-- Name: ix_orders_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_active ON public.orders USING btree (deleted_at) WHERE (deleted_at IS NULL);


--
-- Name: ix_orders_channel_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_channel_status ON public.orders USING btree (channel, status);


--
-- Name: ix_orders_ecommerce_partner; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_ecommerce_partner ON public.orders USING btree (ecommerce_partner_id);


--
-- Name: ix_orders_paid_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_paid_at ON public.orders USING btree (paid_at);


--
-- Name: ix_orders_picked_up_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_picked_up_at ON public.orders USING btree (picked_up_at);


--
-- Name: ix_orders_pickup_deadline; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_pickup_deadline ON public.orders USING btree (pickup_deadline_at);


--
-- Name: ix_orders_public_token_hash; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_public_token_hash ON public.orders USING btree (public_access_token_hash);


--
-- Name: ix_orders_region_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_region_status ON public.orders USING btree (region, status);


--
-- Name: ix_orders_region_totem_created; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_region_totem_created ON public.orders USING btree (region, totem_id, created_at);


--
-- Name: ix_orders_region_totem_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_region_totem_status ON public.orders USING btree (region, totem_id, status);


--
-- Name: ix_orders_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_status ON public.orders USING btree (status);


--
-- Name: ix_orders_status_picked_up; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_status_picked_up ON public.orders USING btree (status, picked_up_at);


--
-- Name: ix_orders_totem_picked_up; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_totem_picked_up ON public.orders USING btree (totem_id, picked_up_at);


--
-- Name: ix_orders_user_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_orders_user_id ON public.orders USING btree (user_id);


--
-- Name: ix_outbox_aggregate; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_outbox_aggregate ON public.domain_event_outbox USING btree (aggregate_type, aggregate_id);


--
-- Name: ix_outbox_status_occurred; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_outbox_status_occurred ON public.domain_event_outbox USING btree (status, occurred_at) WHERE ((status)::text = 'PENDING'::text);


--
-- Name: ix_payment_interface_catalog_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_interface_catalog_active ON public.payment_interface_catalog USING btree (is_active);


--
-- Name: ix_payment_interface_catalog_type; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_interface_catalog_type ON public.payment_interface_catalog USING btree (interface_type);


--
-- Name: ix_payment_interface_requires_hw; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_interface_requires_hw ON public.payment_interface_catalog USING btree (requires_hw);


--
-- Name: ix_payment_method_catalog_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_method_catalog_active ON public.payment_method_catalog USING btree (is_active);


--
-- Name: ix_payment_method_catalog_family; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_method_catalog_family ON public.payment_method_catalog USING btree (family);


--
-- Name: ix_payment_method_catalog_is_instant; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_method_catalog_is_instant ON public.payment_method_catalog USING btree (is_instant);


--
-- Name: ix_payment_tx_gateway_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_tx_gateway_id ON public.payment_transactions USING btree (gateway, gateway_transaction_id);


--
-- Name: ix_payment_tx_nsu; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_tx_nsu ON public.payment_transactions USING btree (nsu);


--
-- Name: ix_payment_tx_order; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_tx_order ON public.payment_transactions USING btree (order_id);


--
-- Name: ix_payment_tx_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_payment_tx_status ON public.payment_transactions USING btree (status);


--
-- Name: ix_pg_gateway_device_last_seen_epoch; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_device_last_seen_epoch ON public.payment_gateway_device_registry USING btree (last_seen_at_epoch);


--
-- Name: ix_pg_gateway_device_region_locker; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_device_region_locker ON public.payment_gateway_device_registry USING btree (region_code, locker_id);


--
-- Name: ix_pg_gateway_idem_expires_epoch; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_idem_expires_epoch ON public.payment_gateway_idempotency_keys USING btree (expires_at_epoch);


--
-- Name: ix_pg_gateway_idem_region_channel; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_idem_region_channel ON public.payment_gateway_idempotency_keys USING btree (region_code, sales_channel);


--
-- Name: ix_pg_gateway_risk_created_at_epoch; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_risk_created_at_epoch ON public.payment_gateway_risk_events USING btree (created_at_epoch);


--
-- Name: ix_pg_gateway_risk_decision; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_risk_decision ON public.payment_gateway_risk_events USING btree (decision);


--
-- Name: ix_pg_gateway_risk_event_type; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_risk_event_type ON public.payment_gateway_risk_events USING btree (event_type);


--
-- Name: ix_pg_gateway_risk_policy_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_risk_policy_id ON public.payment_gateway_risk_events USING btree (policy_id);


--
-- Name: ix_pg_gateway_risk_region_locker_slot; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_risk_region_locker_slot ON public.payment_gateway_risk_events USING btree (region_code, locker_id, slot);


--
-- Name: ix_pg_gateway_risk_request_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pg_gateway_risk_request_id ON public.payment_gateway_risk_events USING btree (request_id);


--
-- Name: ix_pi_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pi_order_id ON public.payment_instructions USING btree (order_id);


--
-- Name: ix_pi_status_expires; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pi_status_expires ON public.payment_instructions USING btree (status, expires_at) WHERE ((status)::text = 'PENDING'::text);


--
-- Name: ix_pickup_tokens_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickup_tokens_active ON public.pickup_tokens USING btree (pickup_id, is_active) WHERE (is_active = true);


--
-- Name: ix_pickup_tokens_active_only; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickup_tokens_active_only ON public.pickup_tokens USING btree (is_active);


--
-- Name: ix_pickup_tokens_expires; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickup_tokens_expires ON public.pickup_tokens USING btree (expires_at) WHERE (is_active = true);


--
-- Name: ix_pickup_tokens_pickup; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickup_tokens_pickup ON public.pickup_tokens USING btree (pickup_id);


--
-- Name: ix_pickup_tokens_pickup_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickup_tokens_pickup_id ON public.pickup_tokens USING btree (pickup_id);


--
-- Name: ix_pickup_tokens_token_hash; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickup_tokens_token_hash ON public.pickup_tokens USING btree (token_hash);


--
-- Name: ix_pickups_channel_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_channel_status ON public.pickups USING btree (channel, status);


--
-- Name: ix_pickups_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_created_at ON public.pickups USING btree (created_at);


--
-- Name: ix_pickups_dispute_state; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_dispute_state ON public.pickups USING btree (dispute_state);


--
-- Name: ix_pickups_expires_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_expires_at ON public.pickups USING btree (expires_at);


--
-- Name: ix_pickups_lifecycle; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_lifecycle ON public.pickups USING btree (lifecycle_stage);


--
-- Name: ix_pickups_lifecycle_stage; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_lifecycle_stage ON public.pickups USING btree (lifecycle_stage);


--
-- Name: ix_pickups_locker_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_locker_status ON public.pickups USING btree (locker_id, status);


--
-- Name: ix_pickups_machine_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_machine_status ON public.pickups USING btree (machine_id, status);


--
-- Name: ix_pickups_operator; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_operator ON public.pickups USING btree (operator_id);


--
-- Name: ix_pickups_operator_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_operator_status ON public.pickups USING btree (operator_id, status);


--
-- Name: ix_pickups_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_order_id ON public.pickups USING btree (order_id);


--
-- Name: ix_pickups_pickup_phase; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_pickup_phase ON public.pickups USING btree (pickup_phase);


--
-- Name: ix_pickups_redeemed_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_redeemed_at ON public.pickups USING btree (redeemed_at);


--
-- Name: ix_pickups_region_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_region_status ON public.pickups USING btree (region, status);


--
-- Name: ix_pickups_site; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_site ON public.pickups USING btree (site_id);


--
-- Name: ix_pickups_site_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_site_status ON public.pickups USING btree (site_id, status);


--
-- Name: ix_pickups_slot_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_slot_status ON public.pickups USING btree (slot, status);


--
-- Name: ix_pickups_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_status ON public.pickups USING btree (status);


--
-- Name: ix_pickups_tenant; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_tenant ON public.pickups USING btree (tenant_id);


--
-- Name: ix_pickups_tenant_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pickups_tenant_status ON public.pickups USING btree (tenant_id, status);


--
-- Name: ix_pmc_family; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pmc_family ON public.payment_method_catalog USING btree (family);


--
-- Name: ix_pricing_region_cat_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pricing_region_cat_active ON public.pricing_rules USING btree (region, product_category, is_active, valid_from) WHERE (is_active = true);


--
-- Name: ix_product_categories_parent; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_product_categories_parent ON public.product_categories USING btree (parent_category);


--
-- Name: ix_product_cfg_category; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_product_cfg_category ON public.product_locker_configs USING btree (category);


--
-- Name: ix_product_cfg_locker; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_product_cfg_locker ON public.product_locker_configs USING btree (locker_id);


--
-- Name: ix_ps_order; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_ps_order ON public.payment_splits USING btree (order_id);


--
-- Name: ix_ps_recipient; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_ps_recipient ON public.payment_splits USING btree (recipient_type, recipient_id, status);


--
-- Name: ix_pt_reconciliation; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pt_reconciliation ON public.payment_transactions USING btree (reconciliation_status) WHERE ((reconciliation_status)::text = 'PENDING'::text);


--
-- Name: ix_pt_webhook_pending; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_pt_webhook_pending ON public.payment_transactions USING btree (gateway_webhook_received_at) WHERE (gateway_webhook_received_at IS NULL);


--
-- Name: ix_recon_pending_order_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_recon_pending_order_id ON public.reconciliation_pending USING btree (order_id);


--
-- Name: ix_recon_pending_status_next; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_recon_pending_status_next ON public.reconciliation_pending USING btree (status, next_retry_at);


--
-- Name: ix_rental_locker_slot; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_rental_locker_slot ON public.rental_contracts USING btree (locker_id, slot_label);


--
-- Name: ix_rental_next_billing; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_rental_next_billing ON public.rental_contracts USING btree (next_billing_at) WHERE ((status)::text = 'ACTIVE'::text);


--
-- Name: ix_rental_plans_locker; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_rental_plans_locker ON public.rental_plans USING btree (locker_id);


--
-- Name: ix_rental_renter_user; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_rental_renter_user ON public.rental_contracts USING btree (renter_user_id);


--
-- Name: ix_rental_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_rental_status ON public.rental_contracts USING btree (status);


--
-- Name: ix_risk_created_at; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_risk_created_at ON public.risk_events USING btree (created_at);


--
-- Name: ix_risk_region_locker_porta; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_risk_region_locker_porta ON public.risk_events USING btree (region, locker_id, porta);


--
-- Name: ix_slot_cfg_dimensions; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_slot_cfg_dimensions ON public.locker_slot_configs USING btree (locker_id, slot_size, width_mm, height_mm, depth_mm);


--
-- Name: ix_slot_configs_locker; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_slot_configs_locker ON public.locker_slot_configs USING btree (locker_id);


--
-- Name: ix_slot_hist_allocation; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_slot_hist_allocation ON public.slot_occupancy_history USING btree (allocation_id);


--
-- Name: ix_slot_hist_locker_slot; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_slot_hist_locker_slot ON public.slot_occupancy_history USING btree (locker_id, slot_label, occurred_at DESC);


--
-- Name: ix_spm_user_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_spm_user_active ON public.saved_payment_methods USING btree (user_id, is_active);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_phone; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_users_phone ON public.users USING btree (phone);


--
-- Name: ix_users_totp_enabled; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_users_totp_enabled ON public.users USING btree (totp_enabled);


--
-- Name: ix_wallet_provider_catalog_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_wallet_provider_catalog_active ON public.wallet_provider_catalog USING btree (is_active);


--
-- Name: ix_webhook_del_aggregate; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_webhook_del_aggregate ON public.webhook_deliveries USING btree (aggregate_type, aggregate_id);


--
-- Name: ix_webhook_del_endpoint; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_webhook_del_endpoint ON public.webhook_deliveries USING btree (endpoint_id);


--
-- Name: ix_webhook_del_status_next; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_webhook_del_status_next ON public.webhook_deliveries USING btree (status, next_attempt_at) WHERE ((status)::text = ANY ((ARRAY['PENDING'::character varying, 'FAILED'::character varying])::text[]));


--
-- Name: ix_webhook_ep_partner; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_webhook_ep_partner ON public.webhook_endpoints USING btree (partner_type, partner_id);


--
-- Name: ix_wt_order; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_wt_order ON public.wallet_transactions USING btree (order_id);


--
-- Name: ix_wt_wallet; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_wt_wallet ON public.wallet_transactions USING btree (wallet_id, created_at DESC);


--
-- Name: uq_locker_category; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX uq_locker_category ON public.product_locker_configs USING btree (locker_id, category);


--
-- Name: uq_pickup_events_pickup_idempotency; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX uq_pickup_events_pickup_idempotency ON public.pickup_events USING btree (pickup_id, idempotency_key) WHERE (idempotency_key IS NOT NULL);


--
-- Name: uq_pickup_events_pickup_version; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX uq_pickup_events_pickup_version ON public.pickup_events USING btree (pickup_id, version);


--
-- Name: uq_user_default_method; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX uq_user_default_method ON public.saved_payment_methods USING btree (user_id) WHERE (is_default = true);


--
-- Name: ux_auth_sessions_token_hash; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_auth_sessions_token_hash ON public.auth_sessions USING btree (session_token_hash);


--
-- Name: ux_cap_profile_method_interface_default; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_cap_profile_method_interface_default ON public.capability_profile_method_interface USING btree (profile_method_id) WHERE ((is_default = true) AND (is_active = true));


--
-- Name: ux_capability_profile_method_default_per_profile; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_capability_profile_method_default_per_profile ON public.capability_profile_method USING btree (profile_id) WHERE ((is_default = true) AND (is_active = true));


--
-- Name: ux_idem_endpoint_key; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_idem_endpoint_key ON public.idempotency_keys USING btree (endpoint, idem_key);


--
-- Name: ux_inbound_tracking; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_inbound_tracking ON public.inbound_deliveries USING btree (logistics_partner_id, tracking_code);


--
-- Name: ux_notification_logs_dedupe; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_notification_logs_dedupe ON public.notification_logs USING btree (dedupe_key);


--
-- Name: ux_pg_gateway_idem_endpoint_key; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_pg_gateway_idem_endpoint_key ON public.payment_gateway_idempotency_keys USING btree (endpoint, idem_key);


--
-- Name: ux_recon_pending_dedupe; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_recon_pending_dedupe ON public.reconciliation_pending USING btree (dedupe_key);


--
-- Name: ux_user_role_active; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_user_role_active ON public.user_roles USING btree (user_id, role, scope_type, scope_id) WHERE (revoked_at IS NULL);


--
-- Name: ux_users_email; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ux_users_email ON public.users USING btree (email) WHERE (anonymized_at IS NULL);


--
-- Name: payment_gateway_device_registry trg_pg_gateway_device_registry_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trg_pg_gateway_device_registry_updated_at BEFORE UPDATE ON public.payment_gateway_device_registry FOR EACH ROW EXECUTE FUNCTION public.set_row_updated_at();


--
-- Name: payment_gateway_idempotency_keys trg_pg_gateway_idempotency_keys_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trg_pg_gateway_idempotency_keys_updated_at BEFORE UPDATE ON public.payment_gateway_idempotency_keys FOR EACH ROW EXECUTE FUNCTION public.set_row_updated_at();


--
-- Name: payment_gateway_risk_events trg_pg_gateway_risk_events_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trg_pg_gateway_risk_events_updated_at BEFORE UPDATE ON public.payment_gateway_risk_events FOR EACH ROW EXECUTE FUNCTION public.set_row_updated_at();


--
-- Name: payment_instructions trg_pi_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trg_pi_updated_at BEFORE UPDATE ON public.payment_instructions FOR EACH ROW EXECUTE FUNCTION public.set_row_updated_at();


--
-- Name: pickups trg_pickups_sync_v2_derived; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trg_pickups_sync_v2_derived BEFORE INSERT OR UPDATE OF evidence_score, pickup_phase, dispute_state ON public.pickups FOR EACH ROW EXECUTE FUNCTION public.trg_pickups_sync_v2_derived();


--
-- Name: locker_slots trg_slot_occupancy_history; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trg_slot_occupancy_history AFTER UPDATE ON public.locker_slots FOR EACH ROW EXECUTE FUNCTION public.trg_log_slot_state_change();


--
-- Name: saved_payment_methods trg_spm_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trg_spm_updated_at BEFORE UPDATE ON public.saved_payment_methods FOR EACH ROW EXECUTE FUNCTION public.set_row_updated_at();


--
-- Name: user_wallets trg_uw_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trg_uw_updated_at BEFORE UPDATE ON public.user_wallets FOR EACH ROW EXECUTE FUNCTION public.set_row_updated_at();


--
-- Name: capability_country trigger_country_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trigger_country_updated_at BEFORE UPDATE ON public.capability_country FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: capability_locker_location trigger_locker_update_geom; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trigger_locker_update_geom BEFORE INSERT OR UPDATE OF latitude, longitude ON public.capability_locker_location FOR EACH ROW EXECUTE FUNCTION public.update_geom_from_coords();


--
-- Name: capability_locker_location trigger_locker_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trigger_locker_updated_at BEFORE UPDATE ON public.capability_locker_location FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: capability_province trigger_province_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--

CREATE TRIGGER trigger_province_updated_at BEFORE UPDATE ON public.capability_province FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: allocations allocations_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.allocations
    ADD CONSTRAINT allocations_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: audit_logs audit_logs_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.users(id);


--
-- Name: auth_sessions auth_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: capability_context capability_context_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_context
    ADD CONSTRAINT capability_context_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.capability_channel(id) ON DELETE RESTRICT;


--
-- Name: capability_locker_location capability_locker_location_province_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_locker_location
    ADD CONSTRAINT capability_locker_location_province_code_fkey FOREIGN KEY (province_code) REFERENCES public.capability_province(code) ON DELETE SET NULL;


--
-- Name: capability_profile_action capability_profile_action_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_action
    ADD CONSTRAINT capability_profile_action_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.capability_profile(id) ON DELETE CASCADE;


--
-- Name: capability_profile capability_profile_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile
    ADD CONSTRAINT capability_profile_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.capability_channel(id) ON DELETE RESTRICT;


--
-- Name: capability_profile_constraint capability_profile_constraint_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_constraint
    ADD CONSTRAINT capability_profile_constraint_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.capability_profile(id) ON DELETE CASCADE;


--
-- Name: capability_profile capability_profile_context_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile
    ADD CONSTRAINT capability_profile_context_id_fkey FOREIGN KEY (context_id) REFERENCES public.capability_context(id) ON DELETE RESTRICT;


--
-- Name: capability_profile_method_interface capability_profile_method_interface_payment_interface_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_interface
    ADD CONSTRAINT capability_profile_method_interface_payment_interface_id_fkey FOREIGN KEY (payment_interface_id) REFERENCES public.payment_interface_catalog(id) ON DELETE RESTRICT;


--
-- Name: capability_profile_method_interface capability_profile_method_interface_profile_method_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_interface
    ADD CONSTRAINT capability_profile_method_interface_profile_method_id_fkey FOREIGN KEY (profile_method_id) REFERENCES public.capability_profile_method(id) ON DELETE CASCADE;


--
-- Name: capability_profile_method capability_profile_method_payment_method_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method
    ADD CONSTRAINT capability_profile_method_payment_method_id_fkey FOREIGN KEY (payment_method_id) REFERENCES public.payment_method_catalog(id) ON DELETE RESTRICT;


--
-- Name: capability_profile_method capability_profile_method_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method
    ADD CONSTRAINT capability_profile_method_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.capability_profile(id) ON DELETE CASCADE;


--
-- Name: capability_profile_method_requirement capability_profile_method_requirement_profile_method_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_requirement
    ADD CONSTRAINT capability_profile_method_requirement_profile_method_id_fkey FOREIGN KEY (profile_method_id) REFERENCES public.capability_profile_method(id) ON DELETE CASCADE;


--
-- Name: capability_profile_method_requirement capability_profile_method_requirement_requirement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method_requirement
    ADD CONSTRAINT capability_profile_method_requirement_requirement_id_fkey FOREIGN KEY (requirement_id) REFERENCES public.capability_requirement_catalog(id) ON DELETE RESTRICT;


--
-- Name: capability_profile_method capability_profile_method_wallet_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_method
    ADD CONSTRAINT capability_profile_method_wallet_provider_id_fkey FOREIGN KEY (wallet_provider_id) REFERENCES public.wallet_provider_catalog(id) ON DELETE RESTRICT;


--
-- Name: capability_profile capability_profile_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile
    ADD CONSTRAINT capability_profile_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.capability_region(id) ON DELETE RESTRICT;


--
-- Name: capability_profile_target capability_profile_target_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_target
    ADD CONSTRAINT capability_profile_target_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.capability_profile(id) ON DELETE CASCADE;


--
-- Name: capability_province capability_province_country_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_province
    ADD CONSTRAINT capability_province_country_code_fkey FOREIGN KEY (country_code) REFERENCES public.capability_country(code) ON DELETE CASCADE;


--
-- Name: data_deletion_requests data_deletion_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.data_deletion_requests
    ADD CONSTRAINT data_deletion_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: financial_ledger financial_ledger_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.financial_ledger
    ADD CONSTRAINT financial_ledger_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: financial_ledger financial_ledger_payment_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.financial_ledger
    ADD CONSTRAINT financial_ledger_payment_transaction_id_fkey FOREIGN KEY (payment_transaction_id) REFERENCES public.payment_transactions(id);


--
-- Name: financial_ledger financial_ledger_wallet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.financial_ledger
    ADD CONSTRAINT financial_ledger_wallet_id_fkey FOREIGN KEY (wallet_id) REFERENCES public.user_wallets(id);


--
-- Name: capability_profile_snapshot fk_cap_snapshot_locker; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_snapshot
    ADD CONSTRAINT fk_cap_snapshot_locker FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: capability_profile_snapshot fk_cap_snapshot_profile; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.capability_profile_snapshot
    ADD CONSTRAINT fk_cap_snapshot_profile FOREIGN KEY (profile_id) REFERENCES public.capability_profile(id);


--
-- Name: pickup_events fk_pickup_events_pickup; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.pickup_events
    ADD CONSTRAINT fk_pickup_events_pickup FOREIGN KEY (pickup_id) REFERENCES public.pickups(id) ON DELETE CASCADE;


--
-- Name: inbound_deliveries inbound_deliveries_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.inbound_deliveries
    ADD CONSTRAINT inbound_deliveries_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: inbound_deliveries inbound_deliveries_logistics_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.inbound_deliveries
    ADD CONSTRAINT inbound_deliveries_logistics_partner_id_fkey FOREIGN KEY (logistics_partner_id) REFERENCES public.logistics_partners(id);


--
-- Name: locker_payment_methods locker_payment_methods_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_payment_methods
    ADD CONSTRAINT locker_payment_methods_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id) ON DELETE CASCADE;


--
-- Name: locker_slot_configs locker_slot_configs_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_slot_configs
    ADD CONSTRAINT locker_slot_configs_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: locker_slots locker_slots_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.locker_slots
    ADD CONSTRAINT locker_slots_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: notification_logs notification_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.notification_logs
    ADD CONSTRAINT notification_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: payment_instructions payment_instructions_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_instructions
    ADD CONSTRAINT payment_instructions_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: payment_splits payment_splits_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_splits
    ADD CONSTRAINT payment_splits_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: payment_transactions payment_transactions_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payment_transactions
    ADD CONSTRAINT payment_transactions_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: pickup_tokens pickup_tokens_pickup_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.pickup_tokens
    ADD CONSTRAINT pickup_tokens_pickup_id_fkey FOREIGN KEY (pickup_id) REFERENCES public.pickups(id);


--
-- Name: pickups pickups_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.pickups
    ADD CONSTRAINT pickups_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: privacy_consents privacy_consents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.privacy_consents
    ADD CONSTRAINT privacy_consents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: product_locker_configs product_locker_configs_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.product_locker_configs
    ADD CONSTRAINT product_locker_configs_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: products products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- Name: reconciliation_pending reconciliation_pending_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.reconciliation_pending
    ADD CONSTRAINT reconciliation_pending_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: rental_contracts rental_contracts_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.rental_contracts
    ADD CONSTRAINT rental_contracts_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: rental_contracts rental_contracts_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.rental_contracts
    ADD CONSTRAINT rental_contracts_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.rental_plans(id);


--
-- Name: rental_contracts rental_contracts_renter_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.rental_contracts
    ADD CONSTRAINT rental_contracts_renter_user_id_fkey FOREIGN KEY (renter_user_id) REFERENCES public.users(id);


--
-- Name: rental_plans rental_plans_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.rental_plans
    ADD CONSTRAINT rental_plans_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: runtime_locker_features runtime_locker_features_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.runtime_locker_features
    ADD CONSTRAINT runtime_locker_features_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.runtime_lockers(locker_id) ON DELETE CASCADE;


--
-- Name: runtime_locker_slots runtime_locker_slots_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.runtime_locker_slots
    ADD CONSTRAINT runtime_locker_slots_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.runtime_lockers(locker_id) ON DELETE CASCADE;


--
-- Name: saved_payment_methods saved_payment_methods_method_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.saved_payment_methods
    ADD CONSTRAINT saved_payment_methods_method_code_fkey FOREIGN KEY (method_code) REFERENCES public.payment_method_catalog(code);


--
-- Name: saved_payment_methods saved_payment_methods_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.saved_payment_methods
    ADD CONSTRAINT saved_payment_methods_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_wallets user_wallets_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.user_wallets
    ADD CONSTRAINT user_wallets_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: wallet_transactions wallet_transactions_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.wallet_transactions
    ADD CONSTRAINT wallet_transactions_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: wallet_transactions wallet_transactions_wallet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.wallet_transactions
    ADD CONSTRAINT wallet_transactions_wallet_id_fkey FOREIGN KEY (wallet_id) REFERENCES public.user_wallets(id);


--
-- Name: webhook_deliveries webhook_deliveries_endpoint_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.webhook_deliveries
    ADD CONSTRAINT webhook_deliveries_endpoint_id_fkey FOREIGN KEY (endpoint_id) REFERENCES public.webhook_endpoints(id);


--
-- PostgreSQL database dump complete
--

