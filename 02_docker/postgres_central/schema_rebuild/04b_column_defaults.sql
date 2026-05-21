-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 04b_column_defaults.sql
-- Execução: ver README.md e run_rebuild.sh

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
-- Name: demand_forecast id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.demand_forecast ALTER COLUMN id SET DEFAULT nextval('public.demand_forecast_id_seq'::regclass);


--
-- Name: ellanlab_depreciation_schedule id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_depreciation_schedule ALTER COLUMN id SET DEFAULT nextval('public.ellanlab_depreciation_schedule_id_seq'::regclass);


--
-- Name: ellanlab_monthly_pnl id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_monthly_pnl ALTER COLUMN id SET DEFAULT nextval('public.ellanlab_monthly_pnl_id_seq'::regclass);


--
-- Name: ellanlab_revenue_recognition id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_revenue_recognition ALTER COLUMN id SET DEFAULT nextval('public.ellanlab_revenue_recognition_id_seq'::regclass);


--
-- Name: financial_kpi_daily id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.financial_kpi_daily ALTER COLUMN id SET DEFAULT nextval('public.financial_kpi_daily_id_seq'::regclass);


--
-- Name: fiscal_auto_classification_log id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fiscal_auto_classification_log ALTER COLUMN id SET DEFAULT nextval('public.fiscal_auto_classification_log_id_seq'::regclass);


--
-- Name: fulfillment_inventory id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_inventory ALTER COLUMN id SET DEFAULT nextval('public.fulfillment_inventory_id_seq'::regclass);


--
-- Name: journal_entry_lines id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.journal_entry_lines ALTER COLUMN id SET DEFAULT nextval('public.journal_entry_lines_id_seq'::regclass);


--
-- Name: locker_slot_configs id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_slot_configs ALTER COLUMN id SET DEFAULT nextval('public.locker_slot_configs_id_seq'::regclass);


--
-- Name: locker_slot_hourly_occupancy id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_slot_hourly_occupancy ALTER COLUMN id SET DEFAULT nextval('public.locker_slot_hourly_occupancy_id_seq'::regclass);


--
-- Name: locker_telemetry id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_telemetry ALTER COLUMN id SET DEFAULT nextval('public.locker_telemetry_id_seq'::regclass);


--
-- Name: locker_utilization_snapshots id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_utilization_snapshots ALTER COLUMN id SET DEFAULT nextval('public.locker_utilization_snapshots_id_seq'::regclass);


--
-- Name: logistics_manifest_items id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_manifest_items ALTER COLUMN id SET DEFAULT nextval('public.logistics_manifest_items_id_seq'::regclass);


--
-- Name: ml_features_daily id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_features_daily ALTER COLUMN id SET DEFAULT nextval('public.ml_features_daily_id_seq'::regclass);


--
-- Name: ml_model_metadata id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_model_metadata ALTER COLUMN id SET DEFAULT nextval('public.ml_model_metadata_id_seq'::regclass);


--
-- Name: ml_predictions_log id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_predictions_log ALTER COLUMN id SET DEFAULT nextval('public.ml_predictions_log_id_seq'::regclass);


--
-- Name: notification_logs id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.notification_logs ALTER COLUMN id SET DEFAULT nextval('public.notification_logs_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: partner_billing_line_items id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_billing_line_items ALTER COLUMN id SET DEFAULT nextval('public.partner_billing_line_items_id_seq'::regclass);


--
-- Name: partner_integration_health id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_integration_health ALTER COLUMN id SET DEFAULT nextval('public.partner_integration_health_id_seq'::regclass);


--
-- Name: partner_settlement_items id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_settlement_items ALTER COLUMN id SET DEFAULT nextval('public.partner_settlement_items_id_seq'::regclass);


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
-- Name: price_history id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.price_history ALTER COLUMN id SET DEFAULT nextval('public.price_history_id_seq'::regclass);


--
-- Name: product_bundle_items id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_bundle_items ALTER COLUMN id SET DEFAULT nextval('public.product_bundle_items_id_seq'::regclass);


--
-- Name: product_locker_configs id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_locker_configs ALTER COLUMN id SET DEFAULT nextval('public.product_locker_configs_id_seq'::regclass);


--
-- Name: product_recommendations id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_recommendations ALTER COLUMN id SET DEFAULT nextval('public.product_recommendations_id_seq'::regclass);


--
-- Name: store_inventory id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.store_inventory ALTER COLUMN id SET DEFAULT nextval('public.store_inventory_id_seq'::regclass);


--
-- Name: subscription_benefits_usage id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.subscription_benefits_usage ALTER COLUMN id SET DEFAULT nextval('public.subscription_benefits_usage_id_seq'::regclass);


--
-- Name: subscription_usage id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.subscription_usage ALTER COLUMN id SET DEFAULT nextval('public.subscription_usage_id_seq'::regclass);


--
-- Name: wallet_provider_catalog id; Type: DEFAULT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.wallet_provider_catalog ALTER COLUMN id SET DEFAULT nextval('public.wallet_provider_catalog_id_seq'::regclass);


