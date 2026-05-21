-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 02_types.sql
-- Execução: ver README.md e run_rebuild.sh

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
    'CANCELLED',
    'CANCELLING',
    'CORRECTION_REQUESTED',
    'COMPLEMENTARY_ISSUED'
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
    'OPERATOR',
    'BLE'
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

