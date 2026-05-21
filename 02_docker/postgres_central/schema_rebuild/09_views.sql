-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 09_views.sql
-- Execução: ver README.md e run_rebuild.sh

--
-- Name: invoice_order_view; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.invoice_order_view AS
 SELECT i.id AS invoice_id,
    i.order_id,
    i.tenant_id,
    i.region,
    i.country,
    (i.status)::text AS invoice_status,
    i.locker_id,
    i.totem_id,
    i.slot_label,
    i.amount_cents,
    i.currency,
    i.created_at,
    i.issued_at,
    i.items_json,
    i.order_snapshot,
    (i.order_snapshot -> 'order'::text) AS order_json,
    (i.order_snapshot -> 'order_items'::text) AS order_items_snapshot,
    COALESCE((i.items_json -> 'lines'::text), '[]'::jsonb) AS items_lines
   FROM public.invoices i;


ALTER TABLE public.invoice_order_view OWNER TO admin;

--
-- Name: ml_features_daily_mv; Type: MATERIALIZED VIEW; Schema: public; Owner: admin
--


CREATE MATERIALIZED VIEW public.ml_features_daily_mv AS
 SELECT ml_features_daily.locker_id,
    ml_features_daily.feature_date,
    avg(ml_features_daily.temperature_mean) AS temperature_avg_70d,
    avg(ml_features_daily.humidity_mean) AS humidity_avg_70d,
    min(ml_features_daily.battery_min) AS battery_min_70d,
    sum(ml_features_daily.door_failures_7d) AS door_failures_70d,
    sum(ml_features_daily.usage_events_7d) AS usage_events_70d,
    sum(ml_features_daily.uptime_hours_7d) AS uptime_hours_70d,
    max(ml_features_daily.failure_label_7d) AS failure_label_70d
   FROM public.ml_features_daily
  WHERE (ml_features_daily.feature_date >= (CURRENT_DATE - '70 days'::interval))
  GROUP BY ml_features_daily.locker_id, ml_features_daily.feature_date
  WITH NO DATA;


ALTER TABLE public.ml_features_daily_mv OWNER TO admin;

--
-- Name: mv_locker_monthly_pnl; Type: MATERIALIZED VIEW; Schema: public; Owner: admin
--


CREATE MATERIALIZED VIEW public.mv_locker_monthly_pnl AS
 WITH rev AS (
         SELECT (date_trunc('month'::text, (ellanlab_revenue_recognition.recognition_date)::timestamp with time zone))::date AS month_ref,
            ellanlab_revenue_recognition.locker_id,
            ellanlab_revenue_recognition.partner_id,
            sum(ellanlab_revenue_recognition.recognized_amount_cents) AS revenue_cents
           FROM public.ellanlab_revenue_recognition
          WHERE (ellanlab_revenue_recognition.locker_id IS NOT NULL)
          GROUP BY ((date_trunc('month'::text, (ellanlab_revenue_recognition.recognition_date)::timestamp with time zone))::date), ellanlab_revenue_recognition.locker_id, ellanlab_revenue_recognition.partner_id
        ), opex AS (
         SELECT ellanlab_opex_entries.expense_month AS month_ref,
            ellanlab_opex_entries.locker_id,
            sum(ellanlab_opex_entries.amount_cents) AS opex_cents
           FROM public.ellanlab_opex_entries
          WHERE (ellanlab_opex_entries.locker_id IS NOT NULL)
          GROUP BY ellanlab_opex_entries.expense_month, ellanlab_opex_entries.locker_id
        ), depr AS (
         SELECT ds.depreciation_month AS month_ref,
            ha.locker_id,
            sum(ds.depreciation_amount_cents) AS depreciation_cents
           FROM (public.ellanlab_depreciation_schedule ds
             JOIN public.ellanlab_hardware_assets ha ON (((ds.asset_id)::text = (ha.id)::text)))
          WHERE (ha.locker_id IS NOT NULL)
          GROUP BY ds.depreciation_month, ha.locker_id
        ), all_months AS (
         SELECT DISTINCT rev.month_ref,
            rev.locker_id
           FROM rev
        UNION
         SELECT opex.month_ref,
            opex.locker_id
           FROM opex
        UNION
         SELECT depr.month_ref,
            depr.locker_id
           FROM depr
        )
 SELECT am.month_ref,
    am.locker_id,
    COALESCE(r.revenue_cents, (0)::numeric) AS revenue_cents,
    COALESCE(o.opex_cents, (0)::numeric) AS opex_cents,
    COALESCE(d.depreciation_cents, (0)::numeric) AS depreciation_cents,
    (COALESCE(o.opex_cents, (0)::numeric) + COALESCE(d.depreciation_cents, (0)::numeric)) AS total_cost_cents,
    ((COALESCE(r.revenue_cents, (0)::numeric) - COALESCE(o.opex_cents, (0)::numeric)) - COALESCE(d.depreciation_cents, (0)::numeric)) AS net_profit_cents,
        CASE
            WHEN (COALESCE(r.revenue_cents, (0)::numeric) = (0)::numeric) THEN (0)::numeric
            ELSE round(((((COALESCE(r.revenue_cents, (0)::numeric) - COALESCE(o.opex_cents, (0)::numeric)) - COALESCE(d.depreciation_cents, (0)::numeric)) / COALESCE(r.revenue_cents, (0)::numeric)) * (100)::numeric), 2)
        END AS margin_pct
   FROM (((all_months am
     LEFT JOIN rev r ON (((am.month_ref = r.month_ref) AND ((am.locker_id)::text = (r.locker_id)::text))))
     LEFT JOIN opex o ON (((am.month_ref = o.month_ref) AND ((am.locker_id)::text = (o.locker_id)::text))))
     LEFT JOIN depr d ON (((am.month_ref = d.month_ref) AND ((am.locker_id)::text = (d.locker_id)::text))))
  WITH NO DATA;


ALTER TABLE public.mv_locker_monthly_pnl OWNER TO admin;

--
-- Name: mv_locker_monthly_profitability; Type: MATERIALIZED VIEW; Schema: public; Owner: admin
--


CREATE MATERIALIZED VIEW public.mv_locker_monthly_profitability AS
 WITH revenue_sales AS (
         SELECT a.locker_id,
            (date_trunc('month'::text, o.picked_up_at))::date AS month,
            sum(o.amount_cents) AS sales_revenue_cents,
            count(DISTINCT o.id) AS total_pickups
           FROM (public.allocations a
             JOIN public.orders o ON (((o.id)::text = (a.order_id)::text)))
          WHERE ((o.status = ANY (ARRAY['PICKED_UP'::public.orderstatus, 'REFUNDED'::public.orderstatus])) AND (o.picked_up_at IS NOT NULL) AND (o.deleted_at IS NULL) AND (a.locker_id IS NOT NULL))
          GROUP BY a.locker_id, ((date_trunc('month'::text, o.picked_up_at))::date)
        ), revenue_openings AS (
         SELECT a.locker_id,
            (date_trunc('month'::text, a.allocated_at))::date AS month,
            count(*) AS total_openings,
            sum(
                CASE
                    WHEN (a.state = ANY (ARRAY['RESERVED_PAID_PENDING_PICKUP'::public.allocationstate, 'OPENED_FOR_PICKUP'::public.allocationstate])) THEN 1
                    ELSE 0
                END) AS paid_openings
           FROM public.allocations a
          WHERE (a.allocated_at IS NOT NULL)
          GROUP BY a.locker_id, ((date_trunc('month'::text, a.allocated_at))::date)
        ), revenue_rental AS (
         SELECT rc.locker_id,
            (date_trunc('month'::text, rc.started_at))::date AS month,
            count(DISTINCT rc.id) AS active_rentals,
            sum(rc.amount_cents) AS rental_revenue_cents
           FROM public.rental_contracts rc
          WHERE (((rc.status)::text = 'ACTIVE'::text) AND (rc.started_at IS NOT NULL))
          GROUP BY rc.locker_id, ((date_trunc('month'::text, rc.started_at))::date)
        ), operational_costs AS (
         SELECT ccm.locker_id,
            ccm.month,
            ccm.total_opex_cents,
            ccm.depreciation_cents,
            ccm.total_costs_cents
           FROM public.cost_center_monthly ccm
        ), marketplace_revenue AS (
         SELECT sp.locker_id,
            (date_trunc('month'::text, o.paid_at))::date AS month,
            sum(mc.commission_amount_cents) AS marketplace_commission_cents,
            sum(o.amount_cents) AS marketplace_gmv_cents
           FROM ((public.marketplace_commissions mc
             JOIN public.orders o ON (((o.id)::text = (mc.order_id)::text)))
             JOIN public.seller_products sp ON (((sp.product_id)::text = (o.sku_id)::text)))
          WHERE ((mc.status)::text = 'SETTLED'::text)
          GROUP BY sp.locker_id, ((date_trunc('month'::text, o.paid_at))::date)
        ), active_lockers AS (
         SELECT l.id AS locker_id,
            (date_trunc('month'::text, l.created_at))::date AS activation_month,
            (COALESCE(l.deleted_at, (CURRENT_DATE)::timestamp with time zone))::date AS deactivation_date
           FROM public.lockers l
          WHERE ((l.active = true) OR (l.deleted_at IS NULL))
        ), all_months AS (
         SELECT DISTINCT l.id AS locker_id,
            (generate_series(((date_trunc('month'::text, min(l.created_at)))::date)::timestamp with time zone, ((date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))::date)::timestamp with time zone, '1 mon'::interval))::date AS month
           FROM public.lockers l
          GROUP BY l.id
        )
 SELECT am.locker_id,
    am.month,
    COALESCE(rs.sales_revenue_cents, (0)::bigint) AS sales_revenue_cents,
    COALESCE(ro.total_openings, (0)::bigint) AS pickup_openings,
    COALESCE(rr.rental_revenue_cents, (0)::bigint) AS rental_revenue_cents,
    COALESCE(mr.marketplace_commission_cents, (0)::bigint) AS marketplace_commission_cents,
    COALESCE(mr.marketplace_gmv_cents, (0)::bigint) AS marketplace_gmv_cents,
    ((COALESCE(rs.sales_revenue_cents, (0)::bigint) + COALESCE(rr.rental_revenue_cents, (0)::bigint)) + COALESCE(mr.marketplace_commission_cents, (0)::bigint)) AS total_revenue_cents,
    COALESCE(oc.total_opex_cents, (0)::bigint) AS total_opex_cents,
    COALESCE(oc.depreciation_cents, (0)::bigint) AS depreciation_cents,
    COALESCE(oc.total_costs_cents, (0)::bigint) AS total_costs_cents,
    (((COALESCE(rs.sales_revenue_cents, (0)::bigint) + COALESCE(rr.rental_revenue_cents, (0)::bigint)) + COALESCE(mr.marketplace_commission_cents, (0)::bigint)) - COALESCE(oc.total_costs_cents, (0)::bigint)) AS net_profit_cents,
        CASE
            WHEN (((COALESCE(rs.sales_revenue_cents, (0)::bigint) + COALESCE(rr.rental_revenue_cents, (0)::bigint)) + COALESCE(mr.marketplace_commission_cents, (0)::bigint)) > 0) THEN round(((100.0 * ((((COALESCE(rs.sales_revenue_cents, (0)::bigint) + COALESCE(rr.rental_revenue_cents, (0)::bigint)) + COALESCE(mr.marketplace_commission_cents, (0)::bigint)) - COALESCE(oc.total_costs_cents, (0)::bigint)))::numeric) / (NULLIF(((COALESCE(rs.sales_revenue_cents, (0)::bigint) + COALESCE(rr.rental_revenue_cents, (0)::bigint)) + COALESCE(mr.marketplace_commission_cents, (0)::bigint)), 0))::numeric), 2)
            ELSE (0)::numeric
        END AS net_margin_pct,
    COALESCE(rs.total_pickups, (0)::bigint) AS total_pickups,
    COALESCE(rr.active_rentals, (0)::bigint) AS active_rentals,
        CASE
            WHEN (COALESCE(rs.total_pickups, (0)::bigint) > 0) THEN round(((COALESCE(rs.sales_revenue_cents, (0)::bigint))::numeric / (NULLIF(rs.total_pickups, 0))::numeric), 2)
            ELSE (0)::numeric
        END AS avg_revenue_per_pickup_cents,
    now() AS computed_at
   FROM (((((all_months am
     LEFT JOIN revenue_sales rs ON ((((rs.locker_id)::text = (am.locker_id)::text) AND (rs.month = am.month))))
     LEFT JOIN revenue_openings ro ON ((((ro.locker_id)::text = (am.locker_id)::text) AND (ro.month = am.month))))
     LEFT JOIN revenue_rental rr ON ((((rr.locker_id)::text = (am.locker_id)::text) AND (rr.month = am.month))))
     LEFT JOIN marketplace_revenue mr ON ((((mr.locker_id)::text = (am.locker_id)::text) AND (mr.month = am.month))))
     LEFT JOIN operational_costs oc ON ((((oc.locker_id)::text = (am.locker_id)::text) AND (oc.month = am.month))))
  WHERE (am.month <= (date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))::date)
  ORDER BY am.locker_id, am.month DESC
  WITH NO DATA;


ALTER TABLE public.mv_locker_monthly_profitability OWNER TO admin;

--
-- Name: mv_realtime_kpis; Type: MATERIALIZED VIEW; Schema: public; Owner: admin
--


CREATE MATERIALIZED VIEW public.mv_realtime_kpis AS
 WITH last_hour_stats AS (
         SELECT count(DISTINCT o.id) AS orders_last_hour,
            (sum(o.amount_cents) / 100) AS revenue_last_hour
           FROM public.orders o
          WHERE ((o.created_at >= (now() - '01:00:00'::interval)) AND (o.deleted_at IS NULL))
        ), last_24h_stats AS (
         SELECT count(DISTINCT o.id) AS orders_last_24h,
            count(DISTINCT o.user_id) AS unique_customers_24h,
            (sum(o.amount_cents) / 100) AS revenue_last_24h
           FROM public.orders o
          WHERE ((o.created_at >= (now() - '24:00:00'::interval)) AND (o.deleted_at IS NULL))
        ), pickup_stats AS (
         SELECT (avg((EXTRACT(epoch FROM (p.redeemed_at - p.activated_at)) / (60)::numeric)))::integer AS avg_pickup_minutes
           FROM public.pickups p
          WHERE (p.redeemed_at >= (now() - '24:00:00'::interval))
        ), offline_lockers AS (
         SELECT count(DISTINCT l.id) AS offline_lockers
           FROM public.lockers l
          WHERE ((l.active = false) AND (l.deleted_at IS NULL))
        ), active_sellers AS (
         SELECT count(DISTINCT ms.id) AS active_sellers
           FROM public.marketplace_sellers ms
          WHERE ((ms.status)::text = 'ACTIVE'::text)
        ), pending_orders AS (
         SELECT count(
                CASE
                    WHEN (o.status = 'PAYMENT_PENDING'::public.orderstatus) THEN 1
                    ELSE NULL::integer
                END) AS pending_payment,
            count(
                CASE
                    WHEN ((o.status = 'PAID_PENDING_PICKUP'::public.orderstatus) AND (o.pickup_deadline_at < now())) THEN 1
                    ELSE NULL::integer
                END) AS expired_pickup
           FROM public.orders o
          WHERE (o.deleted_at IS NULL)
        ), alert_summary AS (
         SELECT count(
                CASE
                    WHEN (((sla_breach_events.severity)::text = 'CRITICAL'::text) AND (sla_breach_events.resolved_at IS NULL)) THEN 1
                    ELSE NULL::integer
                END) AS critical_alerts,
            count(
                CASE
                    WHEN (((sla_breach_events.severity)::text = 'HIGH'::text) AND (sla_breach_events.resolved_at IS NULL)) THEN 1
                    ELSE NULL::integer
                END) AS high_alerts
           FROM public.sla_breach_events
          WHERE (sla_breach_events.detected_at >= (now() - '24:00:00'::interval))
        )
 SELECT now() AS snapshot_time,
    lh.orders_last_hour,
    lh.revenue_last_hour,
    l24.orders_last_24h,
    l24.unique_customers_24h,
    l24.revenue_last_24h,
    ps.avg_pickup_minutes,
    ol.offline_lockers,
    asellers.active_sellers,
    po.pending_payment,
    po.expired_pickup,
    als.critical_alerts,
    als.high_alerts
   FROM ((((((last_hour_stats lh
     CROSS JOIN last_24h_stats l24)
     CROSS JOIN pickup_stats ps)
     CROSS JOIN offline_lockers ol)
     CROSS JOIN active_sellers asellers)
     CROSS JOIN pending_orders po)
     CROSS JOIN alert_summary als)
  WITH NO DATA;


ALTER TABLE public.mv_realtime_kpis OWNER TO admin;

--
-- Name: v_alerts; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_alerts AS
 WITH agg_recipients AS (
         SELECT pulse_channel_recipient.pulse_channel_id,
            string_agg((core_user.email)::text, ','::text) AS recipients
           FROM (public.pulse_channel_recipient
             LEFT JOIN public.core_user ON ((pulse_channel_recipient.user_id = core_user.id)))
          GROUP BY pulse_channel_recipient.pulse_channel_id
        )
 SELECT pulse.id AS entity_id,
    ('pulse_'::text || pulse.id) AS entity_qualified_id,
    pulse.created_at,
    pulse.updated_at,
    pulse.creator_id,
    pulse_card.card_id,
    ('card_'::text || pulse_card.card_id) AS card_qualified_id,
    pulse.alert_condition,
    pulse_channel.schedule_type,
    pulse_channel.schedule_day,
    pulse_channel.schedule_hour,
    pulse.archived,
    pulse_channel.channel_type AS recipient_type,
    agg_recipients.recipients,
    pulse_channel.details AS recipient_external
   FROM (((public.pulse
     LEFT JOIN public.pulse_card ON ((pulse.id = pulse_card.pulse_id)))
     LEFT JOIN public.pulse_channel ON ((pulse.id = pulse_channel.pulse_id)))
     LEFT JOIN agg_recipients ON ((pulse_channel.id = agg_recipients.pulse_channel_id)))
  WHERE (pulse.alert_condition IS NOT NULL);


ALTER TABLE public.v_alerts OWNER TO admin;

--
-- Name: v_audit_log; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_audit_log AS
 SELECT audit_log.id,
        CASE
            WHEN ((audit_log.topic)::text = 'card-create'::text) THEN 'card-create'::character varying
            WHEN ((audit_log.topic)::text = 'card-delete'::text) THEN 'card-delete'::character varying
            WHEN ((audit_log.topic)::text = 'card-update'::text) THEN 'card-update'::character varying
            WHEN ((audit_log.topic)::text = 'pulse-create'::text) THEN 'subscription-create'::character varying
            WHEN ((audit_log.topic)::text = 'pulse-delete'::text) THEN 'subscription-delete'::character varying
            ELSE audit_log.topic
        END AS topic,
    audit_log."timestamp",
    NULL::text AS end_timestamp,
    audit_log.user_id,
    lower((audit_log.model)::text) AS entity_type,
    audit_log.model_id AS entity_id,
        CASE
            WHEN ((audit_log.model)::text = 'Dataset'::text) THEN ('card_'::text || audit_log.model_id)
            WHEN (audit_log.model_id IS NULL) THEN NULL::text
            ELSE ((lower((audit_log.model)::text) || '_'::text) || audit_log.model_id)
        END AS entity_qualified_id,
    audit_log.details
   FROM public.audit_log
  WHERE ((audit_log.topic)::text <> ALL ((ARRAY['card-read'::character varying, 'card-query'::character varying, 'dashboard-read'::character varying, 'dashboard-query'::character varying, 'table-read'::character varying])::text[]));


ALTER TABLE public.v_audit_log OWNER TO admin;

--
-- Name: v_content; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_content AS
 SELECT action.id AS entity_id,
    ('action_'::text || action.id) AS entity_qualified_id,
    'action'::text AS entity_type,
    action.created_at,
    action.updated_at,
    action.creator_id,
    action.name,
    action.description,
    NULL::integer AS collection_id,
    action.made_public_by_id AS made_public_by_user,
    NULL::boolean AS is_embedding_enabled,
    action.archived,
    action.type AS action_type,
    action.model_id AS action_model_id,
    NULL::boolean AS collection_is_official,
    NULL::boolean AS collection_is_personal,
    NULL::text AS question_viz_type,
    NULL::text AS question_database_id,
    NULL::boolean AS question_is_native,
    NULL::timestamp without time zone AS event_timestamp
   FROM public.action
UNION
 SELECT collection.id AS entity_id,
    ('collection_'::text || collection.id) AS entity_qualified_id,
    'collection'::text AS entity_type,
    collection.created_at,
    NULL::timestamp with time zone AS updated_at,
    NULL::integer AS creator_id,
    collection.name,
    collection.description,
    NULL::integer AS collection_id,
    NULL::integer AS made_public_by_user,
    NULL::boolean AS is_embedding_enabled,
    collection.archived,
    NULL::text AS action_type,
    NULL::integer AS action_model_id,
        CASE
            WHEN ((collection.authority_level)::text = 'official'::text) THEN true
            ELSE false
        END AS collection_is_official,
        CASE
            WHEN (collection.personal_owner_id IS NOT NULL) THEN true
            ELSE false
        END AS collection_is_personal,
    NULL::text AS question_viz_type,
    NULL::text AS question_database_id,
    NULL::boolean AS question_is_native,
    NULL::timestamp without time zone AS event_timestamp
   FROM public.collection
UNION
 SELECT report_card.id AS entity_id,
    ('card_'::text || report_card.id) AS entity_qualified_id,
        CASE
            WHEN report_card.dataset THEN 'model'::text
            ELSE 'question'::text
        END AS entity_type,
    report_card.created_at,
    report_card.updated_at,
    report_card.creator_id,
    report_card.name,
    report_card.description,
    report_card.collection_id,
    report_card.made_public_by_id AS made_public_by_user,
    report_card.enable_embedding AS is_embedding_enabled,
    report_card.archived,
    NULL::text AS action_type,
    NULL::integer AS action_model_id,
    NULL::boolean AS collection_is_official,
    NULL::boolean AS collection_is_personal,
    report_card.display AS question_viz_type,
    ('database_'::text || report_card.database_id) AS question_database_id,
        CASE
            WHEN ((report_card.query_type)::text = 'native'::text) THEN true
            ELSE false
        END AS question_is_native,
    NULL::timestamp without time zone AS event_timestamp
   FROM public.report_card
UNION
 SELECT report_dashboard.id AS entity_id,
    ('dashboard_'::text || report_dashboard.id) AS entity_qualified_id,
    'dashboard'::text AS entity_type,
    report_dashboard.created_at,
    report_dashboard.updated_at,
    report_dashboard.creator_id,
    report_dashboard.name,
    report_dashboard.description,
    report_dashboard.collection_id,
    report_dashboard.made_public_by_id AS made_public_by_user,
    report_dashboard.enable_embedding AS is_embedding_enabled,
    report_dashboard.archived,
    NULL::text AS action_type,
    NULL::integer AS action_model_id,
    NULL::boolean AS collection_is_official,
    NULL::boolean AS collection_is_personal,
    NULL::text AS question_viz_type,
    NULL::text AS question_database_id,
    NULL::boolean AS question_is_native,
    NULL::timestamp without time zone AS event_timestamp
   FROM public.report_dashboard
UNION
 SELECT event.id AS entity_id,
    ('event_'::text || event.id) AS entity_qualified_id,
    'event'::text AS entity_type,
    event.created_at,
    event.updated_at,
    event.creator_id,
    event.name,
    event.description,
    timeline.collection_id,
    NULL::integer AS made_public_by_user,
    NULL::boolean AS is_embedding_enabled,
    event.archived,
    NULL::text AS action_type,
    NULL::integer AS action_model_id,
    NULL::boolean AS collection_is_official,
    NULL::boolean AS collection_is_personal,
    NULL::text AS question_viz_type,
    NULL::text AS question_database_id,
    NULL::boolean AS question_is_native,
    event."timestamp" AS event_timestamp
   FROM (public.timeline_event event
     LEFT JOIN public.timeline ON ((event.timeline_id = timeline.id)));


ALTER TABLE public.v_content OWNER TO admin;

--
-- Name: v_dashboardcard; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_dashboardcard AS
 SELECT report_dashboardcard.id AS entity_id,
    concat('dashboardcard_', report_dashboardcard.id) AS entity_qualified_id,
    concat('dashboard_', report_dashboardcard.dashboard_id) AS dashboard_qualified_id,
    concat('dashboardtab_', report_dashboardcard.dashboard_tab_id) AS dashboardtab_id,
    concat('card_', report_dashboardcard.card_id) AS card_qualified_id,
    report_dashboardcard.created_at,
    report_dashboardcard.updated_at,
    report_dashboardcard.size_x,
    report_dashboardcard.size_y,
    report_dashboardcard.visualization_settings,
    report_dashboardcard.parameter_mappings
   FROM public.report_dashboardcard;


ALTER TABLE public.v_dashboardcard OWNER TO admin;

--
-- Name: v_databases; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_databases AS
 SELECT metabase_database.id AS entity_id,
    concat('database_', metabase_database.id) AS entity_qualified_id,
    metabase_database.created_at,
    metabase_database.updated_at,
    metabase_database.name,
    metabase_database.description,
    metabase_database.engine AS database_type,
    metabase_database.metadata_sync_schedule,
    metabase_database.cache_field_values_schedule,
    metabase_database.timezone,
    metabase_database.is_on_demand,
    metabase_database.auto_run_queries,
    metabase_database.cache_ttl,
    metabase_database.creator_id,
    metabase_database.dbms_version AS db_version
   FROM public.metabase_database
  WHERE (metabase_database.id <> 13371337);


ALTER TABLE public.v_databases OWNER TO admin;

--
-- Name: v_fields; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_fields AS
 SELECT metabase_field.id AS entity_id,
    ('field_'::text || metabase_field.id) AS entity_qualified_id,
    metabase_field.created_at,
    metabase_field.updated_at,
    metabase_field.name,
    metabase_field.display_name,
    metabase_field.description,
    metabase_field.base_type,
    metabase_field.visibility_type,
    metabase_field.fk_target_field_id,
    metabase_field.has_field_values,
    metabase_field.active,
    metabase_field.table_id
   FROM public.metabase_field;


ALTER TABLE public.v_fields OWNER TO admin;

--
-- Name: v_locker_roi_analysis; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_locker_roi_analysis AS
 WITH locker_investment AS (
         SELECT l.id AS locker_id,
            l.external_id,
            l.display_name,
            l.city,
            l.region,
            l.created_at AS installation_date,
            (((COALESCE(lcd.equipment_cost_cents, (0)::bigint) + COALESCE(lcd.installation_cost_cents, (0)::bigint)) + COALESCE(lcd.connectivity_setup_cents, (0)::bigint)) + COALESCE(lcd.go_live_cost_cents, (0)::bigint)) AS total_capex_cents,
            lcd.useful_life_months,
            lcd.salvage_value_cents
           FROM (public.lockers l
             LEFT JOIN public.locker_capex_details lcd ON (((lcd.locker_id)::text = (l.id)::text)))
          WHERE ((l.active = true) OR (l.deleted_at IS NULL))
        ), locker_profitability AS (
         SELECT mv_locker_monthly_profitability.locker_id,
            avg(mv_locker_monthly_profitability.net_profit_cents) AS avg_monthly_profit_cents,
            stddev(mv_locker_monthly_profitability.net_profit_cents) AS profit_volatility_cents,
            min(mv_locker_monthly_profitability.month) AS first_profit_month,
            count(*) AS months_operating,
            sum(mv_locker_monthly_profitability.net_profit_cents) AS cumulative_profit_cents
           FROM public.mv_locker_monthly_profitability
          WHERE (mv_locker_monthly_profitability.net_profit_cents > 0)
          GROUP BY mv_locker_monthly_profitability.locker_id
        ), locker_performance AS (
         SELECT mv_locker_monthly_profitability.locker_id,
            count(*) AS total_months,
            sum(mv_locker_monthly_profitability.sales_revenue_cents) AS lifetime_revenue_cents,
            sum(mv_locker_monthly_profitability.total_costs_cents) AS lifetime_costs_cents,
            sum(mv_locker_monthly_profitability.net_profit_cents) AS lifetime_profit_cents,
            avg(mv_locker_monthly_profitability.net_margin_pct) AS avg_margin_pct,
            max(
                CASE
                    WHEN (mv_locker_monthly_profitability.net_profit_cents > 0) THEN mv_locker_monthly_profitability.month
                    ELSE NULL::date
                END) AS last_profitable_month
           FROM public.mv_locker_monthly_profitability
          GROUP BY mv_locker_monthly_profitability.locker_id
        )
 SELECT li.locker_id,
    li.external_id,
    li.display_name,
    li.city,
    li.region,
    li.installation_date,
    round(((li.total_capex_cents)::numeric / 100.0), 2) AS total_investment_brl,
    li.useful_life_months AS expected_life_months,
    round(((COALESCE(li.salvage_value_cents, (0)::bigint))::numeric / 100.0), 2) AS salvage_value_brl,
    (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) / 100.0) AS avg_monthly_profit_brl,
    (COALESCE(lp.profit_volatility_cents, (0)::numeric) / 100.0) AS profit_volatility_brl,
    COALESCE((lp.first_profit_month)::text, 'N/A'::text) AS first_profit_month,
    COALESCE(lp.months_operating, (0)::bigint) AS months_to_profitability,
    (COALESCE(lperf.lifetime_revenue_cents, (0)::numeric) / 100.0) AS lifetime_revenue_brl,
    (COALESCE(lperf.lifetime_costs_cents, (0)::numeric) / 100.0) AS lifetime_costs_brl,
    (COALESCE(lperf.lifetime_profit_cents, (0)::numeric) / 100.0) AS lifetime_profit_brl,
    round(COALESCE(lperf.avg_margin_pct, (0)::numeric), 2) AS avg_margin_pct,
        CASE
            WHEN (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) > (0)::numeric) THEN round(((li.total_capex_cents)::numeric / NULLIF(lp.avg_monthly_profit_cents, (0)::numeric)), 1)
            ELSE NULL::numeric
        END AS payback_months,
        CASE
            WHEN (li.total_capex_cents > 0) THEN round(((100.0 * (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) * (12)::numeric)) / (li.total_capex_cents)::numeric), 2)
            ELSE NULL::numeric
        END AS annual_roi_pct,
        CASE
            WHEN (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) <= (0)::numeric) THEN 'INVIABLE'::text
            WHEN (((li.total_capex_cents)::numeric / NULLIF(lp.avg_monthly_profit_cents, (0)::numeric)) <= (12)::numeric) THEN 'HIGH_PERFORMANCE'::text
            WHEN (((li.total_capex_cents)::numeric / NULLIF(lp.avg_monthly_profit_cents, (0)::numeric)) <= (24)::numeric) THEN 'MODERATE'::text
            WHEN (((li.total_capex_cents)::numeric / NULLIF(lp.avg_monthly_profit_cents, (0)::numeric)) <= (36)::numeric) THEN 'LOW_PERFORMANCE'::text
            ELSE 'UNDERPERFORMING'::text
        END AS viability_classification,
        CASE
            WHEN (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) <= (0)::numeric) THEN 'CONSIDER_RELOCATION_OR_RETIREMENT'::text
            WHEN (((li.total_capex_cents)::numeric / NULLIF(lp.avg_monthly_profit_cents, (0)::numeric)) <= (12)::numeric) THEN 'EXPAND_NETWORK'::text
            WHEN (((li.total_capex_cents)::numeric / NULLIF(lp.avg_monthly_profit_cents, (0)::numeric)) <= (24)::numeric) THEN 'OPTIMIZE_OPERATIONS'::text
            ELSE 'REVIEW_PRICING_AND_COSTS'::text
        END AS recommendation,
        CASE
            WHEN (lperf.last_profitable_month < ((CURRENT_DATE - '3 mons'::interval))::date) THEN 'CONSECUTIVE_LOSSES'::text
            WHEN (COALESCE(lperf.avg_margin_pct, (0)::numeric) < (15)::numeric) THEN 'LOW_MARGIN'::text
            ELSE 'OK'::text
        END AS alert_status,
    now() AS computed_at
   FROM ((locker_investment li
     LEFT JOIN locker_profitability lp ON (((lp.locker_id)::text = (li.locker_id)::text)))
     LEFT JOIN locker_performance lperf ON (((lperf.locker_id)::text = (li.locker_id)::text)))
  ORDER BY
        CASE
            WHEN (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) <= (0)::numeric) THEN 3
            WHEN (((li.total_capex_cents)::numeric / NULLIF(lp.avg_monthly_profit_cents, (0)::numeric)) <= (12)::numeric) THEN 1
            WHEN (((li.total_capex_cents)::numeric / NULLIF(lp.avg_monthly_profit_cents, (0)::numeric)) <= (24)::numeric) THEN 2
            ELSE 4
        END, COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) DESC;


ALTER TABLE public.v_locker_roi_analysis OWNER TO admin;

--
-- Name: v_financial_dashboard; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_financial_dashboard AS
 WITH current_month_metrics AS (
         SELECT (date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))::date AS current_month,
            sum(mv_locker_monthly_profitability.sales_revenue_cents) AS mtd_revenue_cents,
            sum(mv_locker_monthly_profitability.total_costs_cents) AS mtd_costs_cents,
            sum(mv_locker_monthly_profitability.net_profit_cents) AS mtd_profit_cents,
            avg(mv_locker_monthly_profitability.net_margin_pct) AS avg_margin_pct,
            count(DISTINCT mv_locker_monthly_profitability.locker_id) AS active_lockers
           FROM public.mv_locker_monthly_profitability
          WHERE (mv_locker_monthly_profitability.month = (date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))::date)
        ), rolling_12m AS (
         SELECT sum(mv_locker_monthly_profitability.sales_revenue_cents) AS last_12m_revenue_cents,
            sum(mv_locker_monthly_profitability.net_profit_cents) AS last_12m_profit_cents,
            sum(mv_locker_monthly_profitability.total_pickups) AS last_12m_pickups
           FROM public.mv_locker_monthly_profitability
          WHERE (mv_locker_monthly_profitability.month >= (date_trunc('month'::text, (CURRENT_DATE - '1 year'::interval)))::date)
        ), underperforming_lockers AS (
         SELECT count(*) AS underperforming_count
           FROM public.v_locker_roi_analysis
          WHERE (v_locker_roi_analysis.viability_classification = ANY (ARRAY['UNDERPERFORMING'::text, 'INVIABLE'::text]))
        )
 SELECT COALESCE((( SELECT current_month_metrics.mtd_revenue_cents
           FROM current_month_metrics) / 100.0), (0)::numeric) AS revenue_mtd_brl,
    COALESCE((( SELECT current_month_metrics.mtd_costs_cents
           FROM current_month_metrics) / 100.0), (0)::numeric) AS costs_mtd_brl,
    COALESCE((( SELECT current_month_metrics.mtd_profit_cents
           FROM current_month_metrics) / 100.0), (0)::numeric) AS profit_mtd_brl,
    COALESCE(round(( SELECT current_month_metrics.avg_margin_pct
           FROM current_month_metrics), 2), (0)::numeric) AS margin_mtd_pct,
    COALESCE((( SELECT rolling_12m.last_12m_revenue_cents
           FROM rolling_12m) / 100.0), (0)::numeric) AS revenue_ltm_brl,
    COALESCE((( SELECT rolling_12m.last_12m_profit_cents
           FROM rolling_12m) / 100.0), (0)::numeric) AS profit_ltm_brl,
    COALESCE(( SELECT rolling_12m.last_12m_pickups
           FROM rolling_12m), (0)::numeric) AS total_pickups_ltm,
    COALESCE(round(((( SELECT rolling_12m.last_12m_profit_cents
           FROM rolling_12m) / NULLIF(( SELECT rolling_12m.last_12m_revenue_cents
           FROM rolling_12m), (0)::numeric)) * (100)::numeric), 2), (0)::numeric) AS ltm_margin_pct,
    COALESCE(( SELECT count(*) AS count
           FROM public.lockers
          WHERE (lockers.active = true)), (0)::bigint) AS total_active_lockers,
    COALESCE(( SELECT underperforming_lockers.underperforming_count
           FROM underperforming_lockers), (0)::bigint) AS underperforming_lockers,
    COALESCE(round(((100.0 * (( SELECT underperforming_lockers.underperforming_count
           FROM underperforming_lockers))::numeric) / (NULLIF(( SELECT count(*) AS count
           FROM public.lockers
          WHERE (lockers.active = true)), 0))::numeric), 2), (0)::numeric) AS pct_underperforming,
    40.0 AS target_ebitda_margin_pct,
    12.0 AS target_payback_months,
    24.0 AS max_acceptable_payback,
    now() AS computed_at;


ALTER TABLE public.v_financial_dashboard OWNER TO admin;

--
-- Name: v_group_members; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_group_members AS
 SELECT permissions_group_membership.user_id,
    permissions_group.id AS group_id,
    permissions_group.name AS group_name
   FROM (public.permissions_group_membership
     LEFT JOIN public.permissions_group ON ((permissions_group_membership.group_id = permissions_group.id)));


ALTER TABLE public.v_group_members OWNER TO admin;

--
-- Name: v_query_log; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_query_log AS
 SELECT query_execution.id AS entity_id,
    query_execution.started_at,
    ((query_execution.running_time)::double precision / (1000)::double precision) AS running_time_seconds,
    query_execution.result_rows,
    query_execution.native AS is_native,
    query_execution.context AS query_source,
    query_execution.error,
    query_execution.executor_id AS user_id,
    query_execution.card_id,
    ('card_'::text || query_execution.card_id) AS card_qualified_id,
    query_execution.dashboard_id,
    ('dashboard_'::text || query_execution.dashboard_id) AS dashboard_qualified_id,
    query_execution.pulse_id,
    query_execution.database_id,
    ('database_'::text || query_execution.database_id) AS database_qualified_id,
    query_execution.cache_hit,
    query_execution.action_id,
    ('action_'::text || query_execution.action_id) AS action_qualified_id
   FROM public.query_execution;


ALTER TABLE public.v_query_log OWNER TO admin;

--
-- Name: v_subscriptions; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_subscriptions AS
 WITH agg_recipients AS (
         SELECT pulse_channel_recipient.pulse_channel_id,
            string_agg((core_user.email)::text, ','::text) AS recipients
           FROM (public.pulse_channel_recipient
             LEFT JOIN public.core_user ON ((pulse_channel_recipient.user_id = core_user.id)))
          GROUP BY pulse_channel_recipient.pulse_channel_id
        )
 SELECT pulse.id AS entity_id,
    ('pulse_'::text || pulse.id) AS entity_qualified_id,
    pulse.created_at,
    pulse.updated_at,
    pulse.creator_id,
    pulse.archived,
    ('dashboard_'::text || pulse.dashboard_id) AS dashboard_qualified_id,
    pulse_channel.schedule_type,
    pulse_channel.schedule_day,
    pulse_channel.schedule_hour,
    pulse_channel.channel_type AS recipient_type,
    agg_recipients.recipients,
    pulse_channel.details AS recipient_external,
    pulse.parameters
   FROM ((public.pulse
     LEFT JOIN public.pulse_channel ON ((pulse.id = pulse_channel.pulse_id)))
     LEFT JOIN agg_recipients ON ((pulse_channel.id = agg_recipients.pulse_channel_id)))
  WHERE (pulse.alert_condition IS NULL);


ALTER TABLE public.v_subscriptions OWNER TO admin;

--
-- Name: v_tables; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_tables AS
 SELECT metabase_table.id AS entity_id,
    ('table_'::text || metabase_table.id) AS entity_qualified_id,
    metabase_table.created_at,
    metabase_table.updated_at,
    metabase_table.name,
    metabase_table.display_name,
    metabase_table.description,
    metabase_table.active,
    metabase_table.db_id AS database_id,
    metabase_table.schema,
    metabase_table.is_upload
   FROM public.metabase_table;


ALTER TABLE public.v_tables OWNER TO admin;

--
-- Name: v_tasks; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_tasks AS
 SELECT task_history.id,
    task_history.task,
    ('database_'::text || task_history.db_id) AS database_qualified_id,
    task_history.started_at,
    task_history.ended_at,
    ((task_history.duration)::double precision / (1000)::double precision) AS duration_seconds,
    task_history.task_details AS details
   FROM public.task_history;


ALTER TABLE public.v_tasks OWNER TO admin;

--
-- Name: v_users; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_users AS
 SELECT core_user.id AS user_id,
    ('user_'::text || core_user.id) AS entity_qualified_id,
    core_user.email,
    core_user.first_name,
    core_user.last_name,
    (((core_user.first_name)::text || ' '::text) || (core_user.last_name)::text) AS full_name,
    core_user.date_joined,
    core_user.last_login,
    core_user.updated_at,
    core_user.is_superuser AS is_admin,
    core_user.is_active,
    core_user.sso_source,
    core_user.locale
   FROM public.core_user;


ALTER TABLE public.v_users OWNER TO admin;

--
-- Name: v_view_log; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.v_view_log AS
 SELECT view_log.id,
    view_log."timestamp",
    view_log.user_id,
    view_log.model AS entity_type,
    view_log.model_id AS entity_id,
    (((view_log.model)::text || '_'::text) || view_log.model_id) AS entity_qualified_id
   FROM public.view_log;


ALTER TABLE public.v_view_log OWNER TO admin;

--
-- Name: vw_ceo_occupancy; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_ceo_occupancy AS
 WITH current_occupancy AS (
         SELECT l.id AS locker_id,
            l.external_id,
            l.region,
            l.city,
            l.address_line,
            count(ls.id) AS total_slots,
            count(
                CASE
                    WHEN ((ls.status)::text = 'OCCUPIED'::text) THEN 1
                    ELSE NULL::integer
                END) AS occupied_slots,
            count(
                CASE
                    WHEN ((ls.status)::text = 'MAINTENANCE'::text) THEN 1
                    ELSE NULL::integer
                END) AS maintenance_slots,
            max(
                CASE
                    WHEN ((o.status = 'PAID_PENDING_PICKUP'::public.orderstatus) AND (o.picked_up_at IS NULL)) THEN 1
                    ELSE 0
                END) AS has_pending_pickup
           FROM (((public.lockers l
             LEFT JOIN public.locker_slots ls ON (((ls.locker_id)::text = (l.id)::text)))
             LEFT JOIN public.allocations a ON ((((a.locker_id)::text = (l.id)::text) AND (a.state = ANY (ARRAY['RESERVED_PAID_PENDING_PICKUP'::public.allocationstate, 'OPENED_FOR_PICKUP'::public.allocationstate])))))
             LEFT JOIN public.orders o ON ((((o.id)::text = (a.order_id)::text) AND (o.picked_up_at IS NULL))))
          WHERE ((l.active = true) AND (l.deleted_at IS NULL))
          GROUP BY l.id, l.external_id, l.region, l.city, l.address_line
        )
 SELECT current_occupancy.locker_id,
    current_occupancy.external_id,
    current_occupancy.region,
    current_occupancy.city,
    current_occupancy.address_line,
    current_occupancy.total_slots,
    current_occupancy.occupied_slots,
    current_occupancy.maintenance_slots,
    round((((current_occupancy.occupied_slots)::numeric / (NULLIF(current_occupancy.total_slots, 0))::numeric) * (100)::numeric), 2) AS occupancy_pct,
    (current_occupancy.has_pending_pickup = 1) AS has_urgent_pickup,
        CASE
            WHEN (((current_occupancy.occupied_slots)::numeric / (NULLIF(current_occupancy.total_slots, 0))::numeric) >= 0.8) THEN 'HIGH'::text
            WHEN (((current_occupancy.occupied_slots)::numeric / (NULLIF(current_occupancy.total_slots, 0))::numeric) >= 0.5) THEN 'MEDIUM'::text
            ELSE 'LOW'::text
        END AS occupancy_level
   FROM current_occupancy;


ALTER TABLE public.vw_ceo_occupancy OWNER TO admin;

--
-- Name: vw_ceo_revenue; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_ceo_revenue AS
 WITH revenue_data AS (
         SELECT date_trunc('month'::text, o.picked_up_at) AS month_ref,
            o.region,
            o.channel,
            count(DISTINCT o.id) AS total_orders,
            sum(o.amount_cents) AS gross_revenue_cents,
            count(DISTINCT o.user_id) AS unique_customers,
            sum(
                CASE
                    WHEN (o.status = 'REFUNDED'::public.orderstatus) THEN o.amount_cents
                    ELSE 0
                END) AS refunded_cents
           FROM public.orders o
          WHERE ((o.picked_up_at IS NOT NULL) AND (o.deleted_at IS NULL) AND (o.status = ANY (ARRAY['PICKED_UP'::public.orderstatus, 'REFUNDED'::public.orderstatus])))
          GROUP BY (date_trunc('month'::text, o.picked_up_at)), o.region, o.channel
        )
 SELECT revenue_data.month_ref,
    revenue_data.region,
    revenue_data.channel,
    revenue_data.total_orders,
    (revenue_data.gross_revenue_cents / 100) AS gross_revenue,
    (revenue_data.refunded_cents / 100) AS refunded_amount,
    ((revenue_data.gross_revenue_cents - revenue_data.refunded_cents) / 100) AS net_revenue,
    revenue_data.unique_customers,
    round(((((revenue_data.gross_revenue_cents - revenue_data.refunded_cents))::numeric / (NULLIF(revenue_data.total_orders, 0))::numeric) / (100)::numeric), 2) AS avg_ticket
   FROM revenue_data
  ORDER BY revenue_data.month_ref DESC, revenue_data.region, revenue_data.channel;


ALTER TABLE public.vw_ceo_revenue OWNER TO admin;

--
-- Name: vw_cfo_financial; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_cfo_financial AS
 WITH wallet_balance AS (
         SELECT sum(user_wallets.balance_cents) AS total_wallet_balance_cents,
            count(DISTINCT user_wallets.user_id) AS users_with_balance
           FROM public.user_wallets
          WHERE ((user_wallets.status)::text = 'ACTIVE'::text)
        ), disputes AS (
         SELECT count(*) AS open_disputes,
            sum(partner_payment_holds.hold_amount_cents) AS total_hold_cents
           FROM public.partner_payment_holds
          WHERE ((partner_payment_holds.status)::text = 'HELD'::text)
        ), pending_credits AS (
         SELECT count(*) AS pending_credit_notes,
            sum(partner_credit_notes.amount_cents) AS total_credit_cents
           FROM public.partner_credit_notes
          WHERE ((partner_credit_notes.status)::text = 'PENDING'::text)
        )
 SELECT (COALESCE(sum(o.amount_cents), (0)::bigint) / 100) AS gross_revenue_mtd,
    (COALESCE(sum(
        CASE
            WHEN (o.status = 'REFUNDED'::public.orderstatus) THEN o.amount_cents
            ELSE 0
        END), (0)::bigint) / 100) AS refunds_mtd,
    ((COALESCE(sum(o.amount_cents), (0)::bigint) - COALESCE(sum(
        CASE
            WHEN (o.status = 'REFUNDED'::public.orderstatus) THEN o.amount_cents
            ELSE 0
        END), (0)::bigint)) / 100) AS net_revenue_mtd,
    (wb.total_wallet_balance_cents / (100)::numeric) AS total_wallet_balance,
    wb.users_with_balance,
    d.open_disputes,
    (d.total_hold_cents / (100)::numeric) AS total_dispute_holds,
    pc.pending_credit_notes,
    (pc.total_credit_cents / (100)::numeric) AS pending_credits_total
   FROM (((public.orders o
     CROSS JOIN wallet_balance wb)
     CROSS JOIN disputes d)
     CROSS JOIN pending_credits pc)
  WHERE ((o.picked_up_at >= date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone)) AND (o.picked_up_at IS NOT NULL) AND (o.deleted_at IS NULL))
  GROUP BY wb.total_wallet_balance_cents, wb.users_with_balance, d.open_disputes, d.total_hold_cents, pc.pending_credit_notes, pc.total_credit_cents;


ALTER TABLE public.vw_cfo_financial OWNER TO admin;

--
-- Name: vw_coo_operations; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_coo_operations AS
 SELECT CURRENT_DATE AS snapshot_date,
    count(DISTINCT o.id) FILTER (WHERE (o.created_at >= CURRENT_DATE)) AS orders_created_today,
    count(DISTINCT o.id) FILTER (WHERE (o.paid_at >= CURRENT_DATE)) AS orders_paid_today,
    count(DISTINCT o.id) FILTER (WHERE (o.picked_up_at >= CURRENT_DATE)) AS orders_picked_up_today,
    count(DISTINCT p.id) FILTER (WHERE (p.redeemed_at >= CURRENT_DATE)) AS pickups_completed_today,
    count(DISTINCT sbe.id) FILTER (WHERE ((sbe.detected_at >= CURRENT_DATE) AND ((sbe.severity)::text = 'CRITICAL'::text))) AS critical_sla_breaches_today,
    (avg((EXTRACT(epoch FROM (p.redeemed_at - p.activated_at)) / (60)::numeric)))::integer AS avg_pickup_minutes_last_24h,
    count(DISTINCT l.id) FILTER (WHERE (l.active = false)) AS offline_lockers
   FROM (((public.orders o
     LEFT JOIN public.pickups p ON (((p.order_id)::text = (o.id)::text)))
     LEFT JOIN public.sla_breach_events sbe ON (((sbe.delivery_id)::text = (p.id)::text)))
     CROSS JOIN public.lockers l)
  WHERE (o.deleted_at IS NULL);


ALTER TABLE public.vw_coo_operations OWNER TO admin;

--
-- Name: vw_depot_inventory; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_depot_inventory AS
 SELECT inbound_deliveries.id AS delivery_id,
    inbound_deliveries.locker_id,
    inbound_deliveries.slot_label,
    inbound_deliveries.tracking_code,
    inbound_deliveries.status,
    inbound_deliveries.created_at,
    inbound_deliveries.pickup_deadline_at,
    inbound_deliveries.notification_count,
        CASE
            WHEN ((inbound_deliveries.pickup_deadline_at < (CURRENT_TIMESTAMP + '06:00:00'::interval)) AND ((inbound_deliveries.status)::text <> ALL ((ARRAY['PICKED_UP'::character varying, 'RETURNED'::character varying])::text[]))) THEN 'URGENTE_6H'::text
            WHEN ((inbound_deliveries.pickup_deadline_at < (CURRENT_TIMESTAMP + '24:00:00'::interval)) AND ((inbound_deliveries.status)::text <> ALL ((ARRAY['PICKED_UP'::character varying, 'RETURNED'::character varying])::text[]))) THEN 'URGENTE_24H'::text
            WHEN ((inbound_deliveries.status)::text = 'STORED'::text) THEN 'ARMAZENADO'::text
            WHEN ((inbound_deliveries.status)::text = 'PENDING'::text) THEN 'AGUARDANDO'::text
            ELSE 'OUTRO'::text
        END AS urgency_level,
        CASE
            WHEN (inbound_deliveries.pickup_deadline_at < CURRENT_TIMESTAMP) THEN 'ATRASADO'::text
            WHEN (inbound_deliveries.pickup_deadline_at < (CURRENT_TIMESTAMP + '06:00:00'::interval)) THEN 'CRITICO'::text
            WHEN (inbound_deliveries.pickup_deadline_at < (CURRENT_TIMESTAMP + '24:00:00'::interval)) THEN 'ALERTA'::text
            ELSE 'NORMAL'::text
        END AS deadline_status,
    (EXTRACT(epoch FROM (COALESCE(inbound_deliveries.pickup_deadline_at, (CURRENT_TIMESTAMP + '1 year'::interval)) - CURRENT_TIMESTAMP)) / (3600)::numeric) AS hours_until_deadline
   FROM public.inbound_deliveries
  WHERE (((inbound_deliveries.status)::text <> ALL ((ARRAY['PICKED_UP'::character varying, 'RETURNED'::character varying])::text[])) AND (inbound_deliveries.created_at >= (CURRENT_DATE - '14 days'::interval)))
  ORDER BY inbound_deliveries.pickup_deadline_at;


ALTER TABLE public.vw_depot_inventory OWNER TO admin;

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
-- Name: vw_fulfillment_metrics; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_fulfillment_metrics AS
 SELECT date_trunc('day'::text, fo.created_at) AS day_ref,
    fc.name AS center_name,
    count(*) AS total_orders,
    count(
        CASE
            WHEN ((fo.status)::text = 'PICKING'::text) THEN 1
            ELSE NULL::integer
        END) AS picking,
    count(
        CASE
            WHEN ((fo.status)::text = 'PACKING'::text) THEN 1
            ELSE NULL::integer
        END) AS packing,
    count(
        CASE
            WHEN ((fo.status)::text = 'SHIPPED'::text) THEN 1
            ELSE NULL::integer
        END) AS shipped,
    count(
        CASE
            WHEN ((fo.status)::text = 'DELIVERED'::text) THEN 1
            ELSE NULL::integer
        END) AS delivered,
    (avg(EXTRACT(epoch FROM (fo.shipped_at - fo.picked_at))) / (3600)::numeric) AS avg_pick_to_ship_hours,
    (avg(EXTRACT(epoch FROM (fo.delivered_to_locker_at - fo.shipped_at))) / (3600)::numeric) AS avg_ship_to_delivery_hours
   FROM (public.fulfillment_orders fo
     JOIN public.fulfillment_centers fc ON (((fc.id)::text = (fo.fulfillment_center_id)::text)))
  WHERE (fo.created_at >= (CURRENT_DATE - '30 days'::interval))
  GROUP BY (date_trunc('day'::text, fo.created_at)), fc.name, fc.id
  ORDER BY (date_trunc('day'::text, fo.created_at)) DESC, fc.name;


ALTER TABLE public.vw_fulfillment_metrics OWNER TO admin;

--
-- Name: vw_locker_monthly_pnl; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_locker_monthly_pnl AS
 WITH pickup_revenue AS (
         SELECT l.id AS locker_id,
            date_trunc('month'::text, o.picked_up_at) AS month_ref,
            count(DISTINCT o.id) AS total_pickups,
            sum(o.amount_cents) AS revenue_pickup_cents
           FROM ((public.lockers l
             JOIN public.allocations a ON (((a.locker_id)::text = (l.id)::text)))
             JOIN public.orders o ON (((o.id)::text = (a.order_id)::text)))
          WHERE ((o.status = 'PICKED_UP'::public.orderstatus) AND (o.picked_up_at IS NOT NULL))
          GROUP BY l.id, (date_trunc('month'::text, o.picked_up_at))
        ), rental_revenue AS (
         SELECT rc.locker_id,
            date_trunc('month'::text, rc.started_at) AS month_ref,
            count(DISTINCT rc.id) AS active_rentals,
            sum(rc.amount_cents) AS revenue_rental_cents
           FROM public.rental_contracts rc
          WHERE ((rc.status)::text = 'ACTIVE'::text)
          GROUP BY rc.locker_id, (date_trunc('month'::text, rc.started_at))
        ), commission_revenue AS (
         SELECT sp.locker_id,
            date_trunc('month'::text, o.paid_at) AS month_ref,
            sum(mc.commission_amount_cents) AS revenue_commission_cents,
            sum(o.amount_cents) AS gmv_cents
           FROM ((public.marketplace_commissions mc
             JOIN public.orders o ON (((o.id)::text = (mc.order_id)::text)))
             JOIN public.seller_products sp ON (((sp.product_id)::text = (o.sku_id)::text)))
          WHERE ((mc.status)::text = 'SETTLED'::text)
          GROUP BY sp.locker_id, (date_trunc('month'::text, o.paid_at))
        ), capex_costs AS (
         SELECT lc.locker_id,
            (date_trunc('month'::text, (lc.depreciation_start_date)::timestamp with time zone) + ('1 mon'::interval * (s.month_offset)::double precision)) AS month_ref,
                CASE lc.depreciation_method
                    WHEN 'STRAIGHT_LINE'::text THEN ((((lc.acquisition_cost_cents + lc.installation_cost_cents) - COALESCE(lc.residual_value_cents, (0)::bigint)) / lc.useful_life_months))::numeric
                    ELSE ((((lc.acquisition_cost_cents + lc.installation_cost_cents))::numeric * power(0.8, ((s.month_offset)::numeric / 12.0))) / (12)::numeric)
                END AS depreciation_cents
           FROM (public.locker_capex lc
             CROSS JOIN LATERAL generate_series(0, (lc.useful_life_months - 1)) s(month_offset))
          WHERE ((lc.status)::text = 'ACTIVE'::text)
        ), opex_costs AS (
         SELECT locker_opex.locker_id,
            date_trunc('month'::text, (locker_opex.reference_month)::timestamp with time zone) AS month_ref,
            sum(locker_opex.amount_cents) AS total_opex_cents
           FROM public.locker_opex
          GROUP BY locker_opex.locker_id, (date_trunc('month'::text, (locker_opex.reference_month)::timestamp with time zone))
        ), gateway_fees AS (
         SELECT a.locker_id,
            date_trunc('month'::text, pt.approved_at) AS month_ref,
            sum(COALESCE(pt.gateway_fee_cents, 0)) AS gateway_fee_cents
           FROM ((public.payment_transactions pt
             JOIN public.orders o ON (((o.id)::text = (pt.order_id)::text)))
             JOIN public.allocations a ON (((a.order_id)::text = (o.id)::text)))
          WHERE (((pt.status)::text = 'APPROVED'::text) AND (a.locker_id IS NOT NULL))
          GROUP BY a.locker_id, (date_trunc('month'::text, pt.approved_at))
        )
 SELECT COALESCE(pr.locker_id, rr.locker_id, cr.locker_id) AS locker_id,
    COALESCE(pr.month_ref, rr.month_ref, cr.month_ref) AS month_ref,
    COALESCE(pr.revenue_pickup_cents, (0)::bigint) AS revenue_pickup_cents,
    COALESCE(rr.revenue_rental_cents, (0)::bigint) AS revenue_rental_cents,
    COALESCE(cr.revenue_commission_cents, (0)::bigint) AS revenue_commission_cents,
    ((COALESCE(pr.revenue_pickup_cents, (0)::bigint) + COALESCE(rr.revenue_rental_cents, (0)::bigint)) + COALESCE(cr.revenue_commission_cents, (0)::bigint)) AS total_revenue_cents,
    COALESCE(capex.depreciation_cents, (0)::numeric) AS depreciation_cents,
    COALESCE(opex.total_opex_cents, (0)::numeric) AS opex_cents,
    COALESCE(gf.gateway_fee_cents, (0)::bigint) AS gateway_fee_cents,
    ((COALESCE(capex.depreciation_cents, (0)::numeric) + COALESCE(opex.total_opex_cents, (0)::numeric)) + (COALESCE(gf.gateway_fee_cents, (0)::bigint))::numeric) AS total_costs_cents,
    ((((COALESCE(pr.revenue_pickup_cents, (0)::bigint) + COALESCE(rr.revenue_rental_cents, (0)::bigint)) + COALESCE(cr.revenue_commission_cents, (0)::bigint)))::numeric - ((COALESCE(capex.depreciation_cents, (0)::numeric) + COALESCE(opex.total_opex_cents, (0)::numeric)) + (COALESCE(gf.gateway_fee_cents, (0)::bigint))::numeric)) AS net_profit_cents,
        CASE
            WHEN (((COALESCE(pr.revenue_pickup_cents, (0)::bigint) + COALESCE(rr.revenue_rental_cents, (0)::bigint)) + COALESCE(cr.revenue_commission_cents, (0)::bigint)) > 0) THEN round(((((((COALESCE(pr.revenue_pickup_cents, (0)::bigint) + COALESCE(rr.revenue_rental_cents, (0)::bigint)) + COALESCE(cr.revenue_commission_cents, (0)::bigint)))::numeric - ((COALESCE(capex.depreciation_cents, (0)::numeric) + COALESCE(opex.total_opex_cents, (0)::numeric)) + (COALESCE(gf.gateway_fee_cents, (0)::bigint))::numeric)) * 100.0) / (NULLIF(((COALESCE(pr.revenue_pickup_cents, (0)::bigint) + COALESCE(rr.revenue_rental_cents, (0)::bigint)) + COALESCE(cr.revenue_commission_cents, (0)::bigint)), 0))::numeric), 2)
            ELSE (0)::numeric
        END AS margin_pct,
    COALESCE(pr.total_pickups, (0)::bigint) AS total_pickups,
    COALESCE(cr.gmv_cents, (0)::bigint) AS gmv_cents,
    COALESCE(rr.active_rentals, (0)::bigint) AS active_rentals,
        CASE
            WHEN (COALESCE(pr.total_pickups, (0)::bigint) > 0) THEN ((COALESCE(pr.revenue_pickup_cents, (0)::bigint) - COALESCE(gf.gateway_fee_cents, (0)::bigint)) / COALESCE(pr.total_pickups, (1)::bigint))
            ELSE (0)::bigint
        END AS net_revenue_per_pickup_cents,
    now() AS computed_at
   FROM (((((pickup_revenue pr
     FULL JOIN rental_revenue rr ON ((((rr.locker_id)::text = (pr.locker_id)::text) AND (rr.month_ref = pr.month_ref))))
     FULL JOIN commission_revenue cr ON ((((cr.locker_id)::text = (COALESCE(pr.locker_id, rr.locker_id))::text) AND (cr.month_ref = COALESCE(pr.month_ref, rr.month_ref)))))
     LEFT JOIN capex_costs capex ON ((((capex.locker_id)::text = (COALESCE(pr.locker_id, rr.locker_id, cr.locker_id))::text) AND (capex.month_ref = COALESCE(pr.month_ref, rr.month_ref, cr.month_ref)))))
     LEFT JOIN opex_costs opex ON ((((opex.locker_id)::text = (COALESCE(pr.locker_id, rr.locker_id, cr.locker_id))::text) AND (opex.month_ref = COALESCE(pr.month_ref, rr.month_ref, cr.month_ref)))))
     LEFT JOIN gateway_fees gf ON ((((gf.locker_id)::text = (COALESCE(pr.locker_id, rr.locker_id, cr.locker_id))::text) AND (gf.month_ref = COALESCE(pr.month_ref, rr.month_ref, cr.month_ref)))));


ALTER TABLE public.vw_locker_monthly_pnl OWNER TO admin;

--
-- Name: vw_locker_roi; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_locker_roi AS
 WITH locker_investment AS (
         SELECT l.id AS locker_id,
            l.external_id,
            l.city,
            l.region,
            l.created_at AS installation_date,
            sum((lc.acquisition_cost_cents + lc.installation_cost_cents)) AS total_investment_cents,
            avg(lc.useful_life_months) AS expected_life_months
           FROM (public.lockers l
             LEFT JOIN public.locker_capex lc ON (((lc.locker_id)::text = (l.id)::text)))
          GROUP BY l.id, l.external_id, l.city, l.region, l.created_at
        ), locker_profit AS (
         SELECT vw_locker_monthly_pnl.locker_id,
            avg(vw_locker_monthly_pnl.net_profit_cents) AS avg_monthly_profit_cents,
            stddev(vw_locker_monthly_pnl.net_profit_cents) AS profit_volatility_cents,
            min(vw_locker_monthly_pnl.month_ref) AS first_profit_month,
            count(*) AS months_operating
           FROM public.vw_locker_monthly_pnl
          WHERE (vw_locker_monthly_pnl.net_profit_cents > (0)::numeric)
          GROUP BY vw_locker_monthly_pnl.locker_id
        )
 SELECT li.locker_id,
    li.external_id,
    li.city,
    li.region,
    (li.total_investment_cents / 100.0) AS total_investment_brl,
    (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) / 100.0) AS avg_monthly_profit_brl,
        CASE
            WHEN (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) > (0)::numeric) THEN round((li.total_investment_cents / lp.avg_monthly_profit_cents), 1)
            ELSE NULL::numeric
        END AS payback_months,
        CASE
            WHEN (li.total_investment_cents > (0)::numeric) THEN round((((COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) * (12)::numeric) * 100.0) / li.total_investment_cents), 2)
            ELSE NULL::numeric
        END AS annual_roi_pct,
        CASE
            WHEN (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) <= (0)::numeric) THEN 'INVIABLE'::text
            WHEN ((li.total_investment_cents / lp.avg_monthly_profit_cents) <= (12)::numeric) THEN 'HIGH_PERFORMANCE'::text
            WHEN ((li.total_investment_cents / lp.avg_monthly_profit_cents) <= (24)::numeric) THEN 'MODERATE'::text
            WHEN ((li.total_investment_cents / lp.avg_monthly_profit_cents) <= (36)::numeric) THEN 'LOW_PERFORMANCE'::text
            ELSE 'UNDERPERFORMING'::text
        END AS viability_classification,
        CASE
            WHEN (COALESCE(lp.avg_monthly_profit_cents, (0)::numeric) <= (0)::numeric) THEN 'CONSIDER_RELOCATION'::text
            WHEN ((li.total_investment_cents / lp.avg_monthly_profit_cents) <= (12)::numeric) THEN 'EXPAND_NETWORK'::text
            WHEN ((li.total_investment_cents / lp.avg_monthly_profit_cents) <= (24)::numeric) THEN 'OPTIMIZE_COSTS'::text
            ELSE 'REVIEW_PRICING_STRATEGY'::text
        END AS recommendation,
    lp.months_operating,
    lp.first_profit_month,
    now() AS computed_at
   FROM (locker_investment li
     LEFT JOIN locker_profit lp ON (((lp.locker_id)::text = (li.locker_id)::text)));


ALTER TABLE public.vw_locker_roi OWNER TO admin;

--
-- Name: vw_maintenance_alerts; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_maintenance_alerts AS
 WITH telemetry_issues AS (
         SELECT DISTINCT ON (locker_telemetry.locker_id) locker_telemetry.locker_id,
            locker_telemetry.event_type,
            locker_telemetry.occurred_at,
            locker_telemetry.battery_pct,
                CASE
                    WHEN ((locker_telemetry.event_type)::text = 'DOOR_FAILURE'::text) THEN 'CRITICO'::text
                    WHEN (((locker_telemetry.event_type)::text = 'BATTERY_LOW'::text) AND (COALESCE(locker_telemetry.battery_pct, (100)::numeric) < (10)::numeric)) THEN 'CRITICO'::text
                    WHEN (((locker_telemetry.event_type)::text = 'BATTERY_LOW'::text) AND (COALESCE(locker_telemetry.battery_pct, (100)::numeric) < (20)::numeric)) THEN 'ALTA'::text
                    WHEN ((locker_telemetry.event_type)::text = 'SIGNAL_LOST'::text) THEN 'CRITICO'::text
                    WHEN ((locker_telemetry.event_type)::text = 'TEMPERATURE_ALERT'::text) THEN 'ALTA'::text
                    ELSE 'NORMAL'::text
                END AS severity,
                CASE
                    WHEN ((locker_telemetry.event_type)::text = 'DOOR_FAILURE'::text) THEN 'Falha na porta do locker'::character varying
                    WHEN ((locker_telemetry.event_type)::text = 'BATTERY_LOW'::text) THEN ((('Bateria fraca ('::text || (COALESCE(locker_telemetry.battery_pct, (0)::numeric))::integer) || '%)'::text))::character varying
                    WHEN ((locker_telemetry.event_type)::text = 'SIGNAL_LOST'::text) THEN 'Conexão perdida'::character varying
                    WHEN ((locker_telemetry.event_type)::text = 'TEMPERATURE_ALERT'::text) THEN 'Temperatura fora da faixa ideal'::character varying
                    ELSE locker_telemetry.event_type
                END AS description
           FROM public.locker_telemetry
          WHERE ((locker_telemetry.occurred_at >= (CURRENT_DATE - '2 days'::interval)) AND ((locker_telemetry.event_type)::text = ANY ((ARRAY['DOOR_FAILURE'::character varying, 'BATTERY_LOW'::character varying, 'SIGNAL_LOST'::character varying, 'TEMPERATURE_ALERT'::character varying])::text[])))
          ORDER BY locker_telemetry.locker_id, locker_telemetry.occurred_at DESC
        )
 SELECT ti.locker_id,
    l.display_name AS locker_name,
    l.address_line,
    l.city,
    ti.event_type,
    ti.severity,
    ti.description,
    ti.occurred_at,
    (EXTRACT(epoch FROM (CURRENT_TIMESTAMP - ti.occurred_at)) / (3600)::numeric) AS hours_ago,
    'Pendente'::text AS sla_status
   FROM (telemetry_issues ti
     LEFT JOIN public.lockers l ON (((l.id)::text = (ti.locker_id)::text)))
  WHERE (ti.severity = ANY (ARRAY['CRITICO'::text, 'ALTA'::text]))
  ORDER BY
        CASE ti.severity
            WHEN 'CRITICO'::text THEN 1
            WHEN 'ALTA'::text THEN 2
            ELSE 3
        END, ti.occurred_at;


ALTER TABLE public.vw_maintenance_alerts OWNER TO admin;

--
-- Name: vw_ml_dashboard; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_ml_dashboard AS
 SELECT mmm.model_version,
    mmm.trained_at,
    mmm.status,
    mmm.metrics_json,
    count(DISTINCT mpl.locker_id) AS active_lockers,
    avg(mpl.failure_probability) AS avg_failure_probability,
    avg(mpl.health_score) AS avg_health_score
   FROM (public.ml_model_metadata mmm
     LEFT JOIN public.ml_predictions_log mpl ON (((mpl.model_version)::text = (mmm.model_version)::text)))
  WHERE (((mmm.status)::text = 'ACTIVE'::text) AND (mpl.predicted_at >= (CURRENT_DATE - '7 days'::interval)))
  GROUP BY mmm.model_version, mmm.trained_at, mmm.status, mmm.metrics_json;


ALTER TABLE public.vw_ml_dashboard OWNER TO admin;

--
-- Name: vw_ml_features_complete; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_ml_features_complete AS
 SELECT mfd.locker_id,
    mfd.feature_date,
    mfd.temperature_mean,
    mfd.humidity_mean,
    mfd.battery_min,
    mfd.door_failures_7d,
    mfd.usage_events_7d,
    mfd.uptime_hours_7d,
    mfd.temperature_avg_70d,
    mfd.humidity_avg_70d,
    mfd.battery_min_70d,
    mfd.door_failures_70d,
    mfd.usage_events_70d,
    mfd.uptime_hours_70d,
    round((((mfd.door_failures_7d)::numeric / (NULLIF(mfd.usage_events_7d, 0))::numeric) * (100)::numeric), 2) AS failure_rate_pct,
    round(((mfd.uptime_hours_7d / (168)::numeric) * (100)::numeric), 2) AS uptime_pct,
    l.region,
    l.city,
    l.temperature_zone,
    l.security_level
   FROM (public.ml_features_daily mfd
     JOIN public.lockers l ON (((l.id)::text = (mfd.locker_id)::text)))
  WHERE (mfd.feature_date >= (CURRENT_DATE - '30 days'::interval));


ALTER TABLE public.vw_ml_features_complete OWNER TO admin;

--
-- Name: vw_noc_alerts; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_noc_alerts AS
 SELECT 'SLA_BREACH'::text AS alert_type,
    sbe.id AS alert_id,
    sbe.severity,
    sbe.breach_type,
    sbe.detected_at,
    sbe.expected_at,
    sbe.resolved_at,
    COALESCE(ld.display_name, sbe.delivery_id) AS locker_display_name,
    COALESCE(ld.external_id, sbe.delivery_id) AS reference_id,
        CASE
            WHEN (((sbe.severity)::text = ANY ((ARRAY['CRITICAL'::character varying, 'HIGH'::character varying])::text[])) AND (sbe.resolved_at IS NULL)) THEN 1
            ELSE 2
        END AS priority
   FROM ((public.sla_breach_events sbe
     LEFT JOIN public.inbound_deliveries ind ON (((ind.id)::text = (sbe.delivery_id)::text)))
     LEFT JOIN public.lockers ld ON (((ld.id)::text = (ind.locker_id)::text)))
  WHERE ((sbe.resolved_at IS NULL) AND (sbe.detected_at >= (CURRENT_DATE - '7 days'::interval)))
UNION ALL
 SELECT 'LOCKER_OFFLINE'::text AS alert_type,
    l.id AS alert_id,
    'CRITICAL'::character varying AS severity,
    'NETWORK_DOWN'::character varying AS breach_type,
    l.updated_at AS detected_at,
    (l.updated_at + '01:00:00'::interval) AS expected_at,
    NULL::timestamp with time zone AS resolved_at,
    l.display_name AS locker_display_name,
    l.external_id AS reference_id,
    1 AS priority
   FROM public.lockers l
  WHERE ((l.active = false) AND (l.deleted_at IS NULL))
UNION ALL
 SELECT 'RISK_EVENT'::text AS alert_type,
    pgre.id AS alert_id,
        CASE
            WHEN (pgre.decision = 'BLOCK'::text) THEN 'CRITICAL'::text
            WHEN (pgre.decision = 'CHALLENGE'::text) THEN 'HIGH'::text
            ELSE 'MEDIUM'::text
        END AS severity,
    pgre.event_type AS breach_type,
    pgre.created_at AS detected_at,
    NULL::timestamp with time zone AS expected_at,
    NULL::timestamp with time zone AS resolved_at,
    COALESCE(l.display_name, pgre.locker_id) AS locker_display_name,
    pgre.locker_id AS reference_id,
        CASE
            WHEN (pgre.decision = 'BLOCK'::text) THEN 1
            ELSE 2
        END AS priority
   FROM (public.payment_gateway_risk_events pgre
     LEFT JOIN public.lockers l ON (((l.id)::text = (pgre.locker_id)::text)))
  WHERE ((pgre.created_at >= (CURRENT_DATE - '1 day'::interval)) AND (pgre.decision = ANY (ARRAY['BLOCK'::text, 'CHALLENGE'::text])))
  ORDER BY 10, 5 DESC;


ALTER TABLE public.vw_noc_alerts OWNER TO admin;

--
-- Name: vw_omnichannel_metrics; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_omnichannel_metrics AS
 SELECT date_trunc('day'::text, oo.created_at) AS day_ref,
    ps.name AS store_name,
    count(DISTINCT oo.id) AS total_orders,
    count(DISTINCT oo.id) FILTER (WHERE ((oo.pickup_type)::text = 'STORE_PICKUP'::text)) AS store_pickup,
    count(DISTINCT oo.id) FILTER (WHERE ((oo.pickup_type)::text = 'LOCKER_DELIVERY'::text)) AS locker_delivery,
    count(DISTINCT oo.id) FILTER (WHERE ((oo.status)::text = 'PICKED_UP'::text)) AS completed,
    (avg(EXTRACT(epoch FROM (oo.picked_up_at - oo.ready_at))) / (3600)::numeric) AS avg_pickup_time_hours
   FROM (public.omnichannel_orders oo
     JOIN public.partner_stores ps ON (((ps.id)::text = (oo.store_id)::text)))
  WHERE (oo.created_at >= (CURRENT_DATE - '30 days'::interval))
  GROUP BY (date_trunc('day'::text, oo.created_at)), ps.name, ps.id
  ORDER BY (date_trunc('day'::text, oo.created_at)) DESC, ps.name;


ALTER TABLE public.vw_omnichannel_metrics OWNER TO admin;

--
-- Name: vw_proactive_alerts; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_proactive_alerts AS
 SELECT 'BAIXA_OCUPACAO'::text AS alert_type,
    l.id AS entity_id,
    l.display_name AS entity_name,
    round((((count(
        CASE
            WHEN ((ls.status)::text = 'OCCUPIED'::text) THEN 1
            ELSE NULL::integer
        END))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS metric_value,
    'Ocupação abaixo de 30% por mais de 7 dias'::text AS description,
    'MEDIUM'::text AS severity,
    now() AS detected_at
   FROM (public.lockers l
     JOIN public.locker_slots ls ON (((ls.locker_id)::text = (l.id)::text)))
  WHERE ((l.active = true) AND (l.created_at <= (CURRENT_DATE - '7 days'::interval)))
  GROUP BY l.id, l.display_name
 HAVING ((((count(
        CASE
            WHEN ((ls.status)::text = 'OCCUPIED'::text) THEN 1
            ELSE NULL::integer
        END))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric) < (30)::numeric)
UNION ALL
 SELECT 'ALTA_TAXA_FALHA'::text AS alert_type,
    l.id AS entity_id,
    l.display_name AS entity_name,
    round((((count(
        CASE
            WHEN ((lt.event_type)::text = 'DOOR_FAILURE'::text) THEN 1
            ELSE NULL::integer
        END))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS metric_value,
    'Taxa de falha de porta acima de 10% nos últimos 7 dias'::text AS description,
    'HIGH'::text AS severity,
    now() AS detected_at
   FROM (public.lockers l
     JOIN public.locker_telemetry lt ON (((lt.locker_id)::text = (l.id)::text)))
  WHERE ((lt.occurred_at >= (CURRENT_DATE - '7 days'::interval)) AND ((lt.event_type)::text = ANY ((ARRAY['DOOR_FAILURE'::character varying, 'SIGNAL_LOST'::character varying])::text[])))
  GROUP BY l.id, l.display_name
 HAVING ((((count(
        CASE
            WHEN ((lt.event_type)::text = 'DOOR_FAILURE'::text) THEN 1
            ELSE NULL::integer
        END))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric) > (10)::numeric)
UNION ALL
 SELECT 'CHURN_RISK'::text AS alert_type,
    ms.id AS entity_id,
    ms.legal_name AS entity_name,
    ((100)::numeric - (ms.seller_rating * (20)::numeric)) AS metric_value,
    'Seller com rating baixo e poucas vendas recentes'::text AS description,
    'MEDIUM'::text AS severity,
    now() AS detected_at
   FROM (public.marketplace_sellers ms
     LEFT JOIN public.orders o ON ((((o.ecommerce_partner_id)::text = (ms.id)::text) AND (o.created_at >= (CURRENT_DATE - '30 days'::interval)))))
  WHERE (((ms.status)::text = 'ACTIVE'::text) AND (ms.seller_rating < 3.5))
  GROUP BY ms.id, ms.legal_name, ms.seller_rating
 HAVING (count(o.id) < 5);


ALTER TABLE public.vw_proactive_alerts OWNER TO admin;

--
-- Name: vw_realtime_executive; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_realtime_executive AS
 SELECT mv_realtime_kpis.snapshot_time,
    mv_realtime_kpis.orders_last_hour,
    mv_realtime_kpis.revenue_last_hour,
    mv_realtime_kpis.orders_last_24h,
    mv_realtime_kpis.unique_customers_24h,
    mv_realtime_kpis.revenue_last_24h,
    mv_realtime_kpis.avg_pickup_minutes,
    mv_realtime_kpis.offline_lockers,
    mv_realtime_kpis.active_sellers,
    mv_realtime_kpis.pending_payment,
    mv_realtime_kpis.expired_pickup,
    mv_realtime_kpis.critical_alerts,
    mv_realtime_kpis.high_alerts
   FROM public.mv_realtime_kpis;


ALTER TABLE public.vw_realtime_executive OWNER TO admin;

--
-- Name: vw_subscription_metrics; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_subscription_metrics AS
 SELECT date_trunc('month'::text, COALESCE(cs.created_at, (cs.started_at)::timestamp with time zone)) AS month_ref,
    cs.plan_type,
    count(DISTINCT cs.user_id) AS active_subscribers,
    (sum(cs.monthly_fee_cents) / 100) AS mrr,
    count(
        CASE
            WHEN (COALESCE(cs.created_at, (cs.started_at)::timestamp with time zone) >= date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone)) THEN 1
            ELSE NULL::integer
        END) AS new_subscribers_month,
    count(
        CASE
            WHEN (cs.cancelled_at >= date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone)) THEN 1
            ELSE NULL::integer
        END) AS churned_month
   FROM public.customer_subscriptions cs
  WHERE (((cs.status)::text = 'ACTIVE'::text) AND (cs.current_period_start <= now()) AND (cs.current_period_end >= now()))
  GROUP BY (date_trunc('month'::text, COALESCE(cs.created_at, (cs.started_at)::timestamp with time zone))), cs.plan_type
  ORDER BY (date_trunc('month'::text, COALESCE(cs.created_at, (cs.started_at)::timestamp with time zone))) DESC, cs.plan_type;


ALTER TABLE public.vw_subscription_metrics OWNER TO admin;

--
-- Name: vw_subscription_summary; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_subscription_summary AS
 SELECT count(DISTINCT customer_subscriptions.user_id) AS total_active_subscribers,
    (sum(customer_subscriptions.monthly_fee_cents) / 100) AS total_mrr,
    count(DISTINCT customer_subscriptions.plan_type) AS active_plans,
    count(
        CASE
            WHEN ((customer_subscriptions.plan_type)::text = 'PREMIUM'::text) THEN 1
            ELSE NULL::integer
        END) AS premium_count,
    count(
        CASE
            WHEN ((customer_subscriptions.plan_type)::text = 'PRO'::text) THEN 1
            ELSE NULL::integer
        END) AS pro_count,
    count(
        CASE
            WHEN ((customer_subscriptions.plan_type)::text = 'ENTERPRISE'::text) THEN 1
            ELSE NULL::integer
        END) AS enterprise_count,
    count(
        CASE
            WHEN ((customer_subscriptions.plan_type)::text = 'BASIC'::text) THEN 1
            ELSE NULL::integer
        END) AS basic_count
   FROM public.customer_subscriptions
  WHERE (((customer_subscriptions.status)::text = 'ACTIVE'::text) AND (customer_subscriptions.current_period_start <= now()) AND (customer_subscriptions.current_period_end >= now()));


ALTER TABLE public.vw_subscription_summary OWNER TO admin;

--
-- Name: vw_support_active_tickets; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_support_active_tickets AS
 WITH open_tickets AS (
         SELECT o.id AS ticket_id,
            ('ORDER_'::text || (o.id)::text) AS ticket_number,
            o.user_id,
            (o.status)::text AS status,
            o.created_at,
            NULL::timestamp with time zone AS escalated_at,
            'OPEN'::text AS ticket_status,
                CASE
                    WHEN ((o.status = 'PAYMENT_PENDING'::public.orderstatus) AND (o.created_at < (CURRENT_DATE - '1 day'::interval))) THEN 'PAYMENT_OVERDUE'::text
                    WHEN ((o.status = 'PAID_PENDING_PICKUP'::public.orderstatus) AND (o.pickup_deadline_at < CURRENT_DATE)) THEN 'PICKUP_EXPIRED'::text
                    ELSE 'ORDER_ISSUE'::text
                END AS reason,
            2 AS priority
           FROM public.orders o
          WHERE ((o.deleted_at IS NULL) AND (o.status <> ALL (ARRAY['PICKED_UP'::public.orderstatus, 'CANCELLED'::public.orderstatus, 'REFUNDED'::public.orderstatus])) AND (((o.status = 'PAYMENT_PENDING'::public.orderstatus) AND (o.created_at < (CURRENT_DATE - '1 day'::interval))) OR ((o.status = 'PAID_PENDING_PICKUP'::public.orderstatus) AND (o.pickup_deadline_at < CURRENT_DATE))))
        UNION ALL
         SELECT sbe.id AS ticket_id,
            ('SLA_'::text || (sbe.id)::text) AS ticket_number,
            NULL::character varying AS user_id,
            sbe.breach_type AS status,
            sbe.detected_at AS created_at,
                CASE
                    WHEN ((sbe.severity)::text = 'CRITICAL'::text) THEN (sbe.detected_at + '00:30:00'::interval)
                    ELSE NULL::timestamp with time zone
                END AS escalated_at,
                CASE
                    WHEN (sbe.resolved_at IS NULL) THEN 'OPEN'::text
                    ELSE 'RESOLVED'::text
                END AS ticket_status,
            sbe.breach_type AS reason,
                CASE sbe.severity
                    WHEN 'CRITICAL'::text THEN 1
                    WHEN 'HIGH'::text THEN 2
                    ELSE 3
                END AS priority
           FROM public.sla_breach_events sbe
          WHERE (sbe.resolved_at IS NULL)
        )
 SELECT open_tickets.ticket_id,
    open_tickets.ticket_number,
    open_tickets.user_id,
    open_tickets.status,
    open_tickets.created_at,
    open_tickets.escalated_at,
    open_tickets.ticket_status,
    open_tickets.reason,
    open_tickets.priority,
        CASE
            WHEN (open_tickets.priority = 1) THEN 'CRITICO'::text
            WHEN (open_tickets.priority = 2) THEN 'ALTA'::text
            ELSE 'NORMAL'::text
        END AS priority_label,
    (EXTRACT(epoch FROM ((CURRENT_DATE)::timestamp with time zone - open_tickets.created_at)) / (3600)::numeric) AS hours_open
   FROM open_tickets
  ORDER BY open_tickets.priority, open_tickets.created_at;


ALTER TABLE public.vw_support_active_tickets OWNER TO admin;

--
-- Name: vw_trending_metrics; Type: VIEW; Schema: public; Owner: admin
--


CREATE VIEW public.vw_trending_metrics AS
 WITH daily_metrics AS (
         SELECT date_trunc('day'::text, orders.created_at) AS day_ref,
            count(*) AS total_orders,
            (sum(orders.amount_cents) / 100) AS total_revenue,
            count(DISTINCT orders.user_id) AS unique_users
           FROM public.orders
          WHERE ((orders.created_at >= (CURRENT_DATE - '30 days'::interval)) AND (orders.deleted_at IS NULL))
          GROUP BY (date_trunc('day'::text, orders.created_at))
        )
 SELECT daily_metrics.day_ref,
    daily_metrics.total_orders,
    daily_metrics.total_revenue,
    daily_metrics.unique_users,
    lag(daily_metrics.total_orders, 7) OVER (ORDER BY daily_metrics.day_ref) AS orders_7d_ago,
    round(((((daily_metrics.total_orders)::numeric / (NULLIF(lag(daily_metrics.total_orders, 7) OVER (ORDER BY daily_metrics.day_ref), 0))::numeric) - (1)::numeric) * (100)::numeric), 2) AS orders_growth_pct,
    lag(daily_metrics.total_revenue, 7) OVER (ORDER BY daily_metrics.day_ref) AS revenue_7d_ago,
    round(((((daily_metrics.total_revenue)::numeric / (NULLIF(lag(daily_metrics.total_revenue, 7) OVER (ORDER BY daily_metrics.day_ref), 0))::numeric) - (1)::numeric) * (100)::numeric), 2) AS revenue_growth_pct
   FROM daily_metrics
  ORDER BY daily_metrics.day_ref DESC;


ALTER TABLE public.vw_trending_metrics OWNER TO admin;

