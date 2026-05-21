-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 06_constraints_pk_unique_check.sql
-- Execução: ver README.md e run_rebuild.sh

--
-- Name: action action_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.action
    ADD CONSTRAINT action_entity_id_key UNIQUE (entity_id);


--
-- Name: action action_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.action
    ADD CONSTRAINT action_pkey PRIMARY KEY (id);


--
-- Name: action action_public_uuid_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.action
    ADD CONSTRAINT action_public_uuid_key UNIQUE (public_uuid);


--
-- Name: activity activity_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_pkey PRIMARY KEY (id);


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
-- Name: api_key api_key_key_prefix_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_key_prefix_key UNIQUE (key_prefix);


--
-- Name: api_key api_key_name_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_name_key UNIQUE (name);


--
-- Name: api_key api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_pkey PRIMARY KEY (id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


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
-- Name: ble_handshake_logs ble_handshake_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ble_handshake_logs
    ADD CONSTRAINT ble_handshake_logs_pkey PRIMARY KEY (id);


--
-- Name: bookmark_ordering bookmark_ordering_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.bookmark_ordering
    ADD CONSTRAINT bookmark_ordering_pkey PRIMARY KEY (id);


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
-- Name: card_bookmark card_bookmark_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.card_bookmark
    ADD CONSTRAINT card_bookmark_pkey PRIMARY KEY (id);


--
-- Name: card_label card_label_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.card_label
    ADD CONSTRAINT card_label_pkey PRIMARY KEY (id);


--
-- Name: chart_of_accounts chart_of_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.chart_of_accounts
    ADD CONSTRAINT chart_of_accounts_pkey PRIMARY KEY (id);


--
-- Name: collection_bookmark collection_bookmark_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection_bookmark
    ADD CONSTRAINT collection_bookmark_pkey PRIMARY KEY (id);


--
-- Name: collection collection_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection
    ADD CONSTRAINT collection_entity_id_key UNIQUE (entity_id);


--
-- Name: collection collection_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection
    ADD CONSTRAINT collection_pkey PRIMARY KEY (id);


--
-- Name: collection_permission_graph_revision collection_revision_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection_permission_graph_revision
    ADD CONSTRAINT collection_revision_pkey PRIMARY KEY (id);


--
-- Name: connection_impersonations conn_impersonation_unique_group_id_db_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.connection_impersonations
    ADD CONSTRAINT conn_impersonation_unique_group_id_db_id UNIQUE (group_id, db_id);


--
-- Name: connection_impersonations connection_impersonations_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.connection_impersonations
    ADD CONSTRAINT connection_impersonations_pkey PRIMARY KEY (id);


--
-- Name: core_session core_session_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.core_session
    ADD CONSTRAINT core_session_pkey PRIMARY KEY (id);


--
-- Name: core_user core_user_email_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.core_user
    ADD CONSTRAINT core_user_email_key UNIQUE (email);


--
-- Name: core_user core_user_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.core_user
    ADD CONSTRAINT core_user_pkey PRIMARY KEY (id);


--
-- Name: cost_center_monthly cost_center_monthly_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.cost_center_monthly
    ADD CONSTRAINT cost_center_monthly_pkey PRIMARY KEY (id);


--
-- Name: cost_centers cost_centers_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.cost_centers
    ADD CONSTRAINT cost_centers_pkey PRIMARY KEY (id);


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
-- Name: custom_domains custom_domains_domain_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.custom_domains
    ADD CONSTRAINT custom_domains_domain_key UNIQUE (domain);


--
-- Name: custom_domains custom_domains_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.custom_domains
    ADD CONSTRAINT custom_domains_pkey PRIMARY KEY (id);


--
-- Name: customer_feedback customer_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.customer_feedback
    ADD CONSTRAINT customer_feedback_pkey PRIMARY KEY (id);


--
-- Name: customer_subscriptions customer_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.customer_subscriptions
    ADD CONSTRAINT customer_subscriptions_pkey PRIMARY KEY (id);


--
-- Name: dashboard_bookmark dashboard_bookmark_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_bookmark
    ADD CONSTRAINT dashboard_bookmark_pkey PRIMARY KEY (id);


--
-- Name: dashboard_favorite dashboard_favorite_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_favorite
    ADD CONSTRAINT dashboard_favorite_pkey PRIMARY KEY (id);


--
-- Name: dashboard_tab dashboard_tab_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_tab
    ADD CONSTRAINT dashboard_tab_entity_id_key UNIQUE (entity_id);


--
-- Name: dashboard_tab dashboard_tab_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_tab
    ADD CONSTRAINT dashboard_tab_pkey PRIMARY KEY (id);


--
-- Name: dashboardcard_series dashboardcard_series_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboardcard_series
    ADD CONSTRAINT dashboardcard_series_pkey PRIMARY KEY (id);


--
-- Name: data_deletion_requests data_deletion_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.data_deletion_requests
    ADD CONSTRAINT data_deletion_requests_pkey PRIMARY KEY (id);


--
-- Name: databasechangeloglock databasechangeloglock_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.databasechangeloglock
    ADD CONSTRAINT databasechangeloglock_pkey PRIMARY KEY (id);


--
-- Name: demand_forecast demand_forecast_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.demand_forecast
    ADD CONSTRAINT demand_forecast_pkey PRIMARY KEY (id);


--
-- Name: dependency dependency_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dependency
    ADD CONSTRAINT dependency_pkey PRIMARY KEY (id);


--
-- Name: device_registry device_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.device_registry
    ADD CONSTRAINT device_registry_pkey PRIMARY KEY (device_hash);


--
-- Name: dimension dimension_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dimension
    ADD CONSTRAINT dimension_entity_id_key UNIQUE (entity_id);


--
-- Name: dimension dimension_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dimension
    ADD CONSTRAINT dimension_pkey PRIMARY KEY (id);


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
-- Name: dynamic_pricing_rules dynamic_pricing_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dynamic_pricing_rules
    ADD CONSTRAINT dynamic_pricing_rules_pkey PRIMARY KEY (id);


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
-- Name: ellanlab_depreciation_schedule ellanlab_depreciation_schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_depreciation_schedule
    ADD CONSTRAINT ellanlab_depreciation_schedule_pkey PRIMARY KEY (id);


--
-- Name: ellanlab_hardware_assets ellanlab_hardware_assets_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_hardware_assets
    ADD CONSTRAINT ellanlab_hardware_assets_pkey PRIMARY KEY (id);


--
-- Name: ellanlab_monthly_pnl ellanlab_monthly_pnl_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_monthly_pnl
    ADD CONSTRAINT ellanlab_monthly_pnl_pkey PRIMARY KEY (pnl_month, id);


--
-- Name: ellanlab_opex_entries ellanlab_opex_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_opex_entries
    ADD CONSTRAINT ellanlab_opex_entries_pkey PRIMARY KEY (id);


--
-- Name: ellanlab_revenue_recognition ellanlab_revenue_recognition_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_revenue_recognition
    ADD CONSTRAINT ellanlab_revenue_recognition_pkey PRIMARY KEY (recognition_date, id);


--
-- Name: financial_kpi_daily financial_kpi_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.financial_kpi_daily
    ADD CONSTRAINT financial_kpi_daily_pkey PRIMARY KEY (snapshot_date, id);


--
-- Name: financial_ledger financial_ledger_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.financial_ledger
    ADD CONSTRAINT financial_ledger_pkey PRIMARY KEY (id);


--
-- Name: fiscal_accounting_approvals fiscal_accounting_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fiscal_accounting_approvals
    ADD CONSTRAINT fiscal_accounting_approvals_pkey PRIMARY KEY (id);


--
-- Name: fiscal_authority_callbacks fiscal_authority_callbacks_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fiscal_authority_callbacks
    ADD CONSTRAINT fiscal_authority_callbacks_pkey PRIMARY KEY (id);


--
-- Name: fiscal_auto_classification_log fiscal_auto_classification_log_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fiscal_auto_classification_log
    ADD CONSTRAINT fiscal_auto_classification_log_pkey PRIMARY KEY (id);


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
-- Name: fiscal_provider_health_status fiscal_provider_health_status_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fiscal_provider_health_status
    ADD CONSTRAINT fiscal_provider_health_status_pkey PRIMARY KEY (country);


--
-- Name: fiscal_reconciliation_gaps fiscal_reconciliation_gaps_dedupe_key_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fiscal_reconciliation_gaps
    ADD CONSTRAINT fiscal_reconciliation_gaps_dedupe_key_key UNIQUE (dedupe_key);


--
-- Name: fiscal_reconciliation_gaps fiscal_reconciliation_gaps_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fiscal_reconciliation_gaps
    ADD CONSTRAINT fiscal_reconciliation_gaps_pkey PRIMARY KEY (id);


--
-- Name: fulfillment_centers fulfillment_centers_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_centers
    ADD CONSTRAINT fulfillment_centers_code_key UNIQUE (code);


--
-- Name: fulfillment_centers fulfillment_centers_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_centers
    ADD CONSTRAINT fulfillment_centers_pkey PRIMARY KEY (id);


--
-- Name: fulfillment_inventory fulfillment_inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_inventory
    ADD CONSTRAINT fulfillment_inventory_pkey PRIMARY KEY (id);


--
-- Name: fulfillment_orders fulfillment_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_orders
    ADD CONSTRAINT fulfillment_orders_pkey PRIMARY KEY (id);


--
-- Name: application_permissions_revision general_permissions_revision_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.application_permissions_revision
    ADD CONSTRAINT general_permissions_revision_pkey PRIMARY KEY (id);


--
-- Name: sandboxes group_table_access_policy_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sandboxes
    ADD CONSTRAINT group_table_access_policy_pkey PRIMARY KEY (id);


--
-- Name: idempotency_keys idempotency_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.idempotency_keys
    ADD CONSTRAINT idempotency_keys_pkey PRIMARY KEY (id);


--
-- Name: databasechangelog idx_databasechangelog_id_author_filename; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.databasechangelog
    ADD CONSTRAINT idx_databasechangelog_id_author_filename UNIQUE (id, author, filename);


--
-- Name: metabase_field idx_uniq_field_table_id_parent_id_name; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_field
    ADD CONSTRAINT idx_uniq_field_table_id_parent_id_name UNIQUE (table_id, parent_id, name);


--
-- Name: metabase_table idx_uniq_table_db_id_schema_name; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_table
    ADD CONSTRAINT idx_uniq_table_db_id_schema_name UNIQUE (db_id, schema, name);


--
-- Name: report_cardfavorite idx_unique_cardfavorite_card_id_owner_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_cardfavorite
    ADD CONSTRAINT idx_unique_cardfavorite_card_id_owner_id UNIQUE (card_id, owner_id);


--
-- Name: inbound_deliveries inbound_deliveries_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.inbound_deliveries
    ADD CONSTRAINT inbound_deliveries_pkey PRIMARY KEY (id);


--
-- Name: inventory_movements inventory_movements_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT inventory_movements_pkey PRIMARY KEY (id);


--
-- Name: inventory_reservations inventory_reservations_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.inventory_reservations
    ADD CONSTRAINT inventory_reservations_pkey PRIMARY KEY (id);


--
-- Name: invoice_delivery_log invoice_delivery_log_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.invoice_delivery_log
    ADD CONSTRAINT invoice_delivery_log_pkey PRIMARY KEY (id);


--
-- Name: invoice_email_outbox invoice_email_outbox_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.invoice_email_outbox
    ADD CONSTRAINT invoice_email_outbox_pkey PRIMARY KEY (id);


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);


--
-- Name: journal_entries journal_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_pkey PRIMARY KEY (id);


--
-- Name: journal_entry_lines journal_entry_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.journal_entry_lines
    ADD CONSTRAINT journal_entry_lines_pkey PRIMARY KEY (id);


--
-- Name: kiosk_antifraud_events kiosk_antifraud_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.kiosk_antifraud_events
    ADD CONSTRAINT kiosk_antifraud_events_pkey PRIMARY KEY (id);


--
-- Name: label label_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.label
    ADD CONSTRAINT label_pkey PRIMARY KEY (id);


--
-- Name: label label_slug_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.label
    ADD CONSTRAINT label_slug_key UNIQUE (slug);


--
-- Name: lifecycle_deadlines lifecycle_deadlines_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.lifecycle_deadlines
    ADD CONSTRAINT lifecycle_deadlines_pkey PRIMARY KEY (id);


--
-- Name: locker_capex_details locker_capex_details_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_capex_details
    ADD CONSTRAINT locker_capex_details_pkey PRIMARY KEY (id);


--
-- Name: locker_capex locker_capex_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_capex
    ADD CONSTRAINT locker_capex_pkey PRIMARY KEY (id);


--
-- Name: locker_operators locker_operators_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_operators
    ADD CONSTRAINT locker_operators_pkey PRIMARY KEY (id);


--
-- Name: locker_opex locker_opex_locker_id_reference_month_cost_type_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_opex
    ADD CONSTRAINT locker_opex_locker_id_reference_month_cost_type_key UNIQUE (locker_id, reference_month, cost_type);


--
-- Name: locker_opex locker_opex_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_opex
    ADD CONSTRAINT locker_opex_pkey PRIMARY KEY (id);


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
-- Name: locker_slot_hourly_occupancy locker_slot_hourly_occupancy_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_slot_hourly_occupancy
    ADD CONSTRAINT locker_slot_hourly_occupancy_pkey PRIMARY KEY (id);


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
-- Name: locker_telemetry_partitioned locker_telemetry_partitioned_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_telemetry_partitioned
    ADD CONSTRAINT locker_telemetry_partitioned_pkey PRIMARY KEY (id, occurred_at);


--
-- Name: locker_telemetry locker_telemetry_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_telemetry
    ADD CONSTRAINT locker_telemetry_pkey PRIMARY KEY (id, occurred_at);


--
-- Name: locker_utilization_snapshots locker_utilization_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_utilization_snapshots
    ADD CONSTRAINT locker_utilization_snapshots_pkey PRIMARY KEY (id);


--
-- Name: lockers lockers_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.lockers
    ADD CONSTRAINT lockers_pkey PRIMARY KEY (id);


--
-- Name: login_history login_history_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_pkey PRIMARY KEY (id);


--
-- Name: login_otps login_otps_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.login_otps
    ADD CONSTRAINT login_otps_pkey PRIMARY KEY (id);


--
-- Name: logistics_capacity_allocations logistics_capacity_allocations_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_capacity_allocations
    ADD CONSTRAINT logistics_capacity_allocations_pkey PRIMARY KEY (id);


--
-- Name: logistics_carrier_auth_config logistics_carrier_auth_config_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_carrier_auth_config
    ADD CONSTRAINT logistics_carrier_auth_config_pkey PRIMARY KEY (id);


--
-- Name: logistics_carrier_rates logistics_carrier_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_carrier_rates
    ADD CONSTRAINT logistics_carrier_rates_pkey PRIMARY KEY (id);


--
-- Name: logistics_carrier_status_map logistics_carrier_status_map_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_carrier_status_map
    ADD CONSTRAINT logistics_carrier_status_map_pkey PRIMARY KEY (id);


--
-- Name: logistics_delivery_attempts logistics_delivery_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_delivery_attempts
    ADD CONSTRAINT logistics_delivery_attempts_pkey PRIMARY KEY (id);


--
-- Name: logistics_manifest_items logistics_manifest_items_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_manifest_items
    ADD CONSTRAINT logistics_manifest_items_pkey PRIMARY KEY (id);


--
-- Name: logistics_manifests logistics_manifests_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_manifests
    ADD CONSTRAINT logistics_manifests_pkey PRIMARY KEY (id);


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
-- Name: logistics_return_events logistics_return_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_return_events
    ADD CONSTRAINT logistics_return_events_pkey PRIMARY KEY (id);


--
-- Name: logistics_returns logistics_returns_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_returns
    ADD CONSTRAINT logistics_returns_pkey PRIMARY KEY (id);


--
-- Name: logistics_shipment_labels logistics_shipment_labels_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_shipment_labels
    ADD CONSTRAINT logistics_shipment_labels_pkey PRIMARY KEY (id);


--
-- Name: logistics_tracking_events logistics_tracking_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_tracking_events
    ADD CONSTRAINT logistics_tracking_events_pkey PRIMARY KEY (id);


--
-- Name: marketplace_commissions marketplace_commissions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.marketplace_commissions
    ADD CONSTRAINT marketplace_commissions_pkey PRIMARY KEY (id);


--
-- Name: marketplace_sellers marketplace_sellers_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.marketplace_sellers
    ADD CONSTRAINT marketplace_sellers_pkey PRIMARY KEY (id);


--
-- Name: marketplace_sellers marketplace_sellers_tax_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.marketplace_sellers
    ADD CONSTRAINT marketplace_sellers_tax_id_key UNIQUE (tax_id);


--
-- Name: metabase_database metabase_database_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_database
    ADD CONSTRAINT metabase_database_pkey PRIMARY KEY (id);


--
-- Name: metabase_field metabase_field_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_field
    ADD CONSTRAINT metabase_field_pkey PRIMARY KEY (id);


--
-- Name: metabase_fieldvalues metabase_fieldvalues_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_fieldvalues
    ADD CONSTRAINT metabase_fieldvalues_pkey PRIMARY KEY (id);


--
-- Name: metabase_table metabase_table_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_table
    ADD CONSTRAINT metabase_table_pkey PRIMARY KEY (id);


--
-- Name: metric metric_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metric
    ADD CONSTRAINT metric_entity_id_key UNIQUE (entity_id);


--
-- Name: metric_important_field metric_important_field_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metric_important_field
    ADD CONSTRAINT metric_important_field_pkey PRIMARY KEY (id);


--
-- Name: metric metric_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metric
    ADD CONSTRAINT metric_pkey PRIMARY KEY (id);


--
-- Name: ml_features_daily ml_features_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_features_daily
    ADD CONSTRAINT ml_features_daily_pkey PRIMARY KEY (id);


--
-- Name: ml_model_metadata ml_model_metadata_model_version_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_model_metadata
    ADD CONSTRAINT ml_model_metadata_model_version_key UNIQUE (model_version);


--
-- Name: ml_model_metadata ml_model_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_model_metadata
    ADD CONSTRAINT ml_model_metadata_pkey PRIMARY KEY (id);


--
-- Name: ml_prediction_feedback ml_prediction_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_prediction_feedback
    ADD CONSTRAINT ml_prediction_feedback_pkey PRIMARY KEY (id);


--
-- Name: ml_predictions_log ml_predictions_log_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_predictions_log
    ADD CONSTRAINT ml_predictions_log_pkey PRIMARY KEY (id);


--
-- Name: model_index model_index_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.model_index
    ADD CONSTRAINT model_index_pkey PRIMARY KEY (id);


--
-- Name: moderation_review moderation_review_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.moderation_review
    ADD CONSTRAINT moderation_review_pkey PRIMARY KEY (id);


--
-- Name: native_query_snippet native_query_snippet_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.native_query_snippet
    ADD CONSTRAINT native_query_snippet_entity_id_key UNIQUE (entity_id);


--
-- Name: native_query_snippet native_query_snippet_name_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.native_query_snippet
    ADD CONSTRAINT native_query_snippet_name_key UNIQUE (name);


--
-- Name: native_query_snippet native_query_snippet_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.native_query_snippet
    ADD CONSTRAINT native_query_snippet_pkey PRIMARY KEY (id);


--
-- Name: notification_logs notification_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.notification_logs
    ADD CONSTRAINT notification_logs_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: omnichannel_orders omnichannel_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.omnichannel_orders
    ADD CONSTRAINT omnichannel_orders_pkey PRIMARY KEY (id);


--
-- Name: ops_action_audit ops_action_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ops_action_audit
    ADD CONSTRAINT ops_action_audit_pkey PRIMARY KEY (id);


--
-- Name: ops_outbox_replay_priority_runs ops_outbox_replay_priority_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ops_outbox_replay_priority_runs
    ADD CONSTRAINT ops_outbox_replay_priority_runs_pkey PRIMARY KEY (id);


--
-- Name: ops_temp_recon_seed_levels ops_temp_recon_seed_levels_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ops_temp_recon_seed_levels
    ADD CONSTRAINT ops_temp_recon_seed_levels_pkey PRIMARY KEY (tag);


--
-- Name: ops_temp_recon_seed ops_temp_recon_seed_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ops_temp_recon_seed
    ADD CONSTRAINT ops_temp_recon_seed_pkey PRIMARY KEY (tag);


--
-- Name: order_fulfillment_tracking order_fulfillment_tracking_order_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.order_fulfillment_tracking
    ADD CONSTRAINT order_fulfillment_tracking_order_id_key UNIQUE (order_id);


--
-- Name: order_fulfillment_tracking order_fulfillment_tracking_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.order_fulfillment_tracking
    ADD CONSTRAINT order_fulfillment_tracking_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders_partitioned orders_partitioned_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_partitioned
    ADD CONSTRAINT orders_partitioned_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2025_06 orders_2025_06_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2025_06
    ADD CONSTRAINT orders_2025_06_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2025_07 orders_2025_07_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2025_07
    ADD CONSTRAINT orders_2025_07_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2025_08 orders_2025_08_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2025_08
    ADD CONSTRAINT orders_2025_08_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2025_09 orders_2025_09_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2025_09
    ADD CONSTRAINT orders_2025_09_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2025_10 orders_2025_10_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2025_10
    ADD CONSTRAINT orders_2025_10_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2025_11 orders_2025_11_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2025_11
    ADD CONSTRAINT orders_2025_11_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2025_12 orders_2025_12_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2025_12
    ADD CONSTRAINT orders_2025_12_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2026_01 orders_2026_01_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2026_01
    ADD CONSTRAINT orders_2026_01_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2026_02 orders_2026_02_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2026_02
    ADD CONSTRAINT orders_2026_02_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2026_03 orders_2026_03_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2026_03
    ADD CONSTRAINT orders_2026_03_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2026_04 orders_2026_04_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2026_04
    ADD CONSTRAINT orders_2026_04_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders_2026_05 orders_2026_05_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders_2026_05
    ADD CONSTRAINT orders_2026_05_pkey PRIMARY KEY (id, created_at);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: parameter_card parameter_card_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.parameter_card
    ADD CONSTRAINT parameter_card_pkey PRIMARY KEY (id);


--
-- Name: partner_api_keys partner_api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_api_keys
    ADD CONSTRAINT partner_api_keys_pkey PRIMARY KEY (id);


--
-- Name: partner_b2b_invoices partner_b2b_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_b2b_invoices
    ADD CONSTRAINT partner_b2b_invoices_pkey PRIMARY KEY (id);


--
-- Name: partner_billing_cycles partner_billing_cycles_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_billing_cycles
    ADD CONSTRAINT partner_billing_cycles_pkey PRIMARY KEY (id);


--
-- Name: partner_billing_line_items partner_billing_line_items_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_billing_line_items
    ADD CONSTRAINT partner_billing_line_items_pkey PRIMARY KEY (id);


--
-- Name: partner_billing_plans partner_billing_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_billing_plans
    ADD CONSTRAINT partner_billing_plans_pkey PRIMARY KEY (id);


--
-- Name: partner_commission_structure partner_commission_structure_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_commission_structure
    ADD CONSTRAINT partner_commission_structure_pkey PRIMARY KEY (id);


--
-- Name: partner_contacts partner_contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_contacts
    ADD CONSTRAINT partner_contacts_pkey PRIMARY KEY (id);


--
-- Name: partner_credit_notes partner_credit_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_credit_notes
    ADD CONSTRAINT partner_credit_notes_pkey PRIMARY KEY (id);


--
-- Name: partner_integration_health partner_integration_health_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_integration_health
    ADD CONSTRAINT partner_integration_health_pkey PRIMARY KEY (id);


--
-- Name: partner_order_events_outbox partner_order_events_outbox_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_order_events_outbox
    ADD CONSTRAINT partner_order_events_outbox_pkey PRIMARY KEY (id);


--
-- Name: partner_payment_holds partner_payment_holds_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_payment_holds
    ADD CONSTRAINT partner_payment_holds_pkey PRIMARY KEY (id);


--
-- Name: partner_performance_metrics partner_performance_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_performance_metrics
    ADD CONSTRAINT partner_performance_metrics_pkey PRIMARY KEY (id);


--
-- Name: partner_service_areas partner_service_areas_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_service_areas
    ADD CONSTRAINT partner_service_areas_pkey PRIMARY KEY (id);


--
-- Name: partner_settlement_batches partner_settlement_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_settlement_batches
    ADD CONSTRAINT partner_settlement_batches_pkey PRIMARY KEY (id);


--
-- Name: partner_settlement_items partner_settlement_items_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_settlement_items
    ADD CONSTRAINT partner_settlement_items_pkey PRIMARY KEY (id);


--
-- Name: partner_sla_agreements partner_sla_agreements_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_sla_agreements
    ADD CONSTRAINT partner_sla_agreements_pkey PRIMARY KEY (id);


--
-- Name: partner_status_history partner_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_status_history
    ADD CONSTRAINT partner_status_history_pkey PRIMARY KEY (id);


--
-- Name: partner_stores partner_stores_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_stores
    ADD CONSTRAINT partner_stores_pkey PRIMARY KEY (id);


--
-- Name: partner_stores partner_stores_tax_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_stores
    ADD CONSTRAINT partner_stores_tax_id_key UNIQUE (tax_id);


--
-- Name: partner_webhook_deliveries partner_webhook_deliveries_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_webhook_deliveries
    ADD CONSTRAINT partner_webhook_deliveries_pkey PRIMARY KEY (id);


--
-- Name: partner_webhook_endpoints partner_webhook_endpoints_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_webhook_endpoints
    ADD CONSTRAINT partner_webhook_endpoints_pkey PRIMARY KEY (id);


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
-- Name: permissions permissions_group_id_object_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_group_id_object_key UNIQUE (group_id, object);


--
-- Name: permissions_group_membership permissions_group_membership_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions_group_membership
    ADD CONSTRAINT permissions_group_membership_pkey PRIMARY KEY (id);


--
-- Name: permissions_group permissions_group_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions_group
    ADD CONSTRAINT permissions_group_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: permissions_revision permissions_revision_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions_revision
    ADD CONSTRAINT permissions_revision_pkey PRIMARY KEY (id);


--
-- Name: persisted_info persisted_info_card_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.persisted_info
    ADD CONSTRAINT persisted_info_card_id_key UNIQUE (card_id);


--
-- Name: persisted_info persisted_info_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.persisted_info
    ADD CONSTRAINT persisted_info_pkey PRIMARY KEY (id);


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
-- Name: http_action pk_http_action; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.http_action
    ADD CONSTRAINT pk_http_action PRIMARY KEY (action_id);


--
-- Name: implicit_action pk_implicit_action; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.implicit_action
    ADD CONSTRAINT pk_implicit_action PRIMARY KEY (action_id);


--
-- Name: qrtz_blob_triggers pk_qrtz_blob_triggers; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_blob_triggers
    ADD CONSTRAINT pk_qrtz_blob_triggers PRIMARY KEY (sched_name, trigger_name, trigger_group);


--
-- Name: qrtz_calendars pk_qrtz_calendars; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_calendars
    ADD CONSTRAINT pk_qrtz_calendars PRIMARY KEY (sched_name, calendar_name);


--
-- Name: qrtz_cron_triggers pk_qrtz_cron_triggers; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_cron_triggers
    ADD CONSTRAINT pk_qrtz_cron_triggers PRIMARY KEY (sched_name, trigger_name, trigger_group);


--
-- Name: qrtz_fired_triggers pk_qrtz_fired_triggers; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_fired_triggers
    ADD CONSTRAINT pk_qrtz_fired_triggers PRIMARY KEY (sched_name, entry_id);


--
-- Name: qrtz_job_details pk_qrtz_job_details; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_job_details
    ADD CONSTRAINT pk_qrtz_job_details PRIMARY KEY (sched_name, job_name, job_group);


--
-- Name: qrtz_locks pk_qrtz_locks; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_locks
    ADD CONSTRAINT pk_qrtz_locks PRIMARY KEY (sched_name, lock_name);


--
-- Name: qrtz_scheduler_state pk_qrtz_scheduler_state; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_scheduler_state
    ADD CONSTRAINT pk_qrtz_scheduler_state PRIMARY KEY (sched_name, instance_name);


--
-- Name: qrtz_simple_triggers pk_qrtz_simple_triggers; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_simple_triggers
    ADD CONSTRAINT pk_qrtz_simple_triggers PRIMARY KEY (sched_name, trigger_name, trigger_group);


--
-- Name: qrtz_simprop_triggers pk_qrtz_simprop_triggers; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_simprop_triggers
    ADD CONSTRAINT pk_qrtz_simprop_triggers PRIMARY KEY (sched_name, trigger_name, trigger_group);


--
-- Name: qrtz_triggers pk_qrtz_triggers; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_triggers
    ADD CONSTRAINT pk_qrtz_triggers PRIMARY KEY (sched_name, trigger_name, trigger_group);


--
-- Name: query_action pk_query_action; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.query_action
    ADD CONSTRAINT pk_query_action PRIMARY KEY (action_id);


--
-- Name: qrtz_paused_trigger_grps pk_sched_name; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_paused_trigger_grps
    ADD CONSTRAINT pk_sched_name PRIMARY KEY (sched_name, trigger_group);


--
-- Name: price_history price_history_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.price_history
    ADD CONSTRAINT price_history_pkey PRIMARY KEY (id);


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
-- Name: product_barcodes product_barcodes_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_barcodes
    ADD CONSTRAINT product_barcodes_pkey PRIMARY KEY (id);


--
-- Name: product_bundle_items product_bundle_items_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_bundle_items
    ADD CONSTRAINT product_bundle_items_pkey PRIMARY KEY (id);


--
-- Name: product_bundles product_bundles_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_bundles
    ADD CONSTRAINT product_bundles_code_key UNIQUE (code);


--
-- Name: product_bundles product_bundles_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_bundles
    ADD CONSTRAINT product_bundles_pkey PRIMARY KEY (id);


--
-- Name: product_categories product_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_pkey PRIMARY KEY (id);


--
-- Name: product_cogs product_cogs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_cogs
    ADD CONSTRAINT product_cogs_pkey PRIMARY KEY (id);


--
-- Name: product_fiscal_config product_fiscal_config_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_fiscal_config
    ADD CONSTRAINT product_fiscal_config_pkey PRIMARY KEY (sku_id);


--
-- Name: product_inventory product_inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_inventory
    ADD CONSTRAINT product_inventory_pkey PRIMARY KEY (id);


--
-- Name: product_locker_compatibility product_locker_compatibility_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_locker_compatibility
    ADD CONSTRAINT product_locker_compatibility_pkey PRIMARY KEY (id);


--
-- Name: product_locker_configs product_locker_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_locker_configs
    ADD CONSTRAINT product_locker_configs_pkey PRIMARY KEY (id);


--
-- Name: product_media product_media_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_media
    ADD CONSTRAINT product_media_pkey PRIMARY KEY (id);


--
-- Name: product_recommendations product_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_recommendations
    ADD CONSTRAINT product_recommendations_pkey PRIMARY KEY (id);


--
-- Name: product_status_history product_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_status_history
    ADD CONSTRAINT product_status_history_pkey PRIMARY KEY (id);


--
-- Name: products_cache products_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.products_cache
    ADD CONSTRAINT products_cache_pkey PRIMARY KEY (sku_id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: promotion_product_exclusions promotion_product_exclusions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.promotion_product_exclusions
    ADD CONSTRAINT promotion_product_exclusions_pkey PRIMARY KEY (promotion_id, product_id);


--
-- Name: promotions promotions_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.promotions
    ADD CONSTRAINT promotions_code_key UNIQUE (code);


--
-- Name: promotions promotions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.promotions
    ADD CONSTRAINT promotions_pkey PRIMARY KEY (id);


--
-- Name: pulse_card pulse_card_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_card
    ADD CONSTRAINT pulse_card_entity_id_key UNIQUE (entity_id);


--
-- Name: pulse_card pulse_card_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_card
    ADD CONSTRAINT pulse_card_pkey PRIMARY KEY (id);


--
-- Name: pulse_channel pulse_channel_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_channel
    ADD CONSTRAINT pulse_channel_entity_id_key UNIQUE (entity_id);


--
-- Name: pulse_channel pulse_channel_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_channel
    ADD CONSTRAINT pulse_channel_pkey PRIMARY KEY (id);


--
-- Name: pulse_channel_recipient pulse_channel_recipient_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_channel_recipient
    ADD CONSTRAINT pulse_channel_recipient_pkey PRIMARY KEY (id);


--
-- Name: pulse pulse_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse
    ADD CONSTRAINT pulse_entity_id_key UNIQUE (entity_id);


--
-- Name: pulse pulse_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse
    ADD CONSTRAINT pulse_pkey PRIMARY KEY (id);


--
-- Name: query_cache query_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.query_cache
    ADD CONSTRAINT query_cache_pkey PRIMARY KEY (query_hash);


--
-- Name: query_execution query_execution_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.query_execution
    ADD CONSTRAINT query_execution_pkey PRIMARY KEY (id);


--
-- Name: query query_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.query
    ADD CONSTRAINT query_pkey PRIMARY KEY (query_hash);


--
-- Name: recent_views recent_views_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.recent_views
    ADD CONSTRAINT recent_views_pkey PRIMARY KEY (id);


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
-- Name: report_card report_card_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_card
    ADD CONSTRAINT report_card_entity_id_key UNIQUE (entity_id);


--
-- Name: report_card report_card_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_card
    ADD CONSTRAINT report_card_pkey PRIMARY KEY (id);


--
-- Name: report_card report_card_public_uuid_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_card
    ADD CONSTRAINT report_card_public_uuid_key UNIQUE (public_uuid);


--
-- Name: report_cardfavorite report_cardfavorite_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_cardfavorite
    ADD CONSTRAINT report_cardfavorite_pkey PRIMARY KEY (id);


--
-- Name: report_dashboard report_dashboard_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboard
    ADD CONSTRAINT report_dashboard_entity_id_key UNIQUE (entity_id);


--
-- Name: report_dashboard report_dashboard_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboard
    ADD CONSTRAINT report_dashboard_pkey PRIMARY KEY (id);


--
-- Name: report_dashboard report_dashboard_public_uuid_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboard
    ADD CONSTRAINT report_dashboard_public_uuid_key UNIQUE (public_uuid);


--
-- Name: report_dashboardcard report_dashboardcard_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboardcard
    ADD CONSTRAINT report_dashboardcard_entity_id_key UNIQUE (entity_id);


--
-- Name: report_dashboardcard report_dashboardcard_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboardcard
    ADD CONSTRAINT report_dashboardcard_pkey PRIMARY KEY (id);


--
-- Name: return_legs return_legs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_legs
    ADD CONSTRAINT return_legs_pkey PRIMARY KEY (id);


--
-- Name: return_reasons_catalog return_reasons_catalog_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_reasons_catalog
    ADD CONSTRAINT return_reasons_catalog_code_key UNIQUE (code);


--
-- Name: return_reasons_catalog return_reasons_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_reasons_catalog
    ADD CONSTRAINT return_reasons_catalog_pkey PRIMARY KEY (id);


--
-- Name: return_requests return_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_requests
    ADD CONSTRAINT return_requests_pkey PRIMARY KEY (id);


--
-- Name: return_tracking_events return_tracking_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_tracking_events
    ADD CONSTRAINT return_tracking_events_pkey PRIMARY KEY (id);


--
-- Name: revision revision_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.revision
    ADD CONSTRAINT revision_pkey PRIMARY KEY (id);


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
-- Name: runtime_sync_queue runtime_sync_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.runtime_sync_queue
    ADD CONSTRAINT runtime_sync_queue_pkey PRIMARY KEY (id);


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
-- Name: secret secret_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.secret
    ADD CONSTRAINT secret_pkey PRIMARY KEY (id, version);


--
-- Name: segment segment_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.segment
    ADD CONSTRAINT segment_entity_id_key UNIQUE (entity_id);


--
-- Name: segment segment_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.segment
    ADD CONSTRAINT segment_pkey PRIMARY KEY (id);


--
-- Name: seller_products seller_products_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.seller_products
    ADD CONSTRAINT seller_products_pkey PRIMARY KEY (id);


--
-- Name: seller_reviews seller_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.seller_reviews
    ADD CONSTRAINT seller_reviews_pkey PRIMARY KEY (id);


--
-- Name: setting setting_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.setting
    ADD CONSTRAINT setting_pkey PRIMARY KEY (key);


--
-- Name: sla_breach_events sla_breach_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sla_breach_events
    ADD CONSTRAINT sla_breach_events_pkey PRIMARY KEY (id);


--
-- Name: slot_occupancy_history slot_occupancy_history_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.slot_occupancy_history
    ADD CONSTRAINT slot_occupancy_history_pkey PRIMARY KEY (id);


--
-- Name: store_inventory store_inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.store_inventory
    ADD CONSTRAINT store_inventory_pkey PRIMARY KEY (id);


--
-- Name: subscription_benefits_usage subscription_benefits_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.subscription_benefits_usage
    ADD CONSTRAINT subscription_benefits_usage_pkey PRIMARY KEY (id);


--
-- Name: subscription_plans subscription_plans_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.subscription_plans
    ADD CONSTRAINT subscription_plans_code_key UNIQUE (code);


--
-- Name: subscription_plans subscription_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.subscription_plans
    ADD CONSTRAINT subscription_plans_pkey PRIMARY KEY (id);


--
-- Name: subscription_usage subscription_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.subscription_usage
    ADD CONSTRAINT subscription_usage_pkey PRIMARY KEY (id);


--
-- Name: task_history task_history_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.task_history
    ADD CONSTRAINT task_history_pkey PRIMARY KEY (id);


--
-- Name: templates templates_name_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_name_key UNIQUE (name);


--
-- Name: templates templates_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_pkey PRIMARY KEY (id);


--
-- Name: tenant_fiscal_config tenant_fiscal_config_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.tenant_fiscal_config
    ADD CONSTRAINT tenant_fiscal_config_pkey PRIMARY KEY (tenant_id);


--
-- Name: timeline timeline_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.timeline
    ADD CONSTRAINT timeline_entity_id_key UNIQUE (entity_id);


--
-- Name: timeline_event timeline_event_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.timeline_event
    ADD CONSTRAINT timeline_event_pkey PRIMARY KEY (id);


--
-- Name: timeline timeline_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.timeline
    ADD CONSTRAINT timeline_pkey PRIMARY KEY (id);


--
-- Name: ui_error_events ui_error_events_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ui_error_events
    ADD CONSTRAINT ui_error_events_pkey PRIMARY KEY (id);


--
-- Name: bookmark_ordering unique_bookmark_user_id_ordering; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.bookmark_ordering
    ADD CONSTRAINT unique_bookmark_user_id_ordering UNIQUE (user_id, ordering);


--
-- Name: bookmark_ordering unique_bookmark_user_id_type_item_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.bookmark_ordering
    ADD CONSTRAINT unique_bookmark_user_id_type_item_id UNIQUE (user_id, type, item_id);


--
-- Name: card_bookmark unique_card_bookmark_user_id_card_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.card_bookmark
    ADD CONSTRAINT unique_card_bookmark_user_id_card_id UNIQUE (user_id, card_id);


--
-- Name: card_label unique_card_label_card_id_label_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.card_label
    ADD CONSTRAINT unique_card_label_card_id_label_id UNIQUE (card_id, label_id);


--
-- Name: collection_bookmark unique_collection_bookmark_user_id_collection_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection_bookmark
    ADD CONSTRAINT unique_collection_bookmark_user_id_collection_id UNIQUE (user_id, collection_id);


--
-- Name: collection unique_collection_personal_owner_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection
    ADD CONSTRAINT unique_collection_personal_owner_id UNIQUE (personal_owner_id);


--
-- Name: dashboard_bookmark unique_dashboard_bookmark_user_id_dashboard_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_bookmark
    ADD CONSTRAINT unique_dashboard_bookmark_user_id_dashboard_id UNIQUE (user_id, dashboard_id);


--
-- Name: dashboard_favorite unique_dashboard_favorite_user_id_dashboard_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_favorite
    ADD CONSTRAINT unique_dashboard_favorite_user_id_dashboard_id UNIQUE (user_id, dashboard_id);


--
-- Name: dimension unique_dimension_field_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dimension
    ADD CONSTRAINT unique_dimension_field_id UNIQUE (field_id);


--
-- Name: sandboxes unique_gtap_table_id_group_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sandboxes
    ADD CONSTRAINT unique_gtap_table_id_group_id UNIQUE (table_id, group_id);


--
-- Name: metric_important_field unique_metric_important_field_metric_id_field_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metric_important_field
    ADD CONSTRAINT unique_metric_important_field_metric_id_field_id UNIQUE (metric_id, field_id);


--
-- Name: model_index_value unique_model_index_value_model_index_id_model_pk; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.model_index_value
    ADD CONSTRAINT unique_model_index_value_model_index_id_model_pk UNIQUE (model_index_id, model_pk);


--
-- Name: parameter_card unique_parameterized_object_card_parameter; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.parameter_card
    ADD CONSTRAINT unique_parameterized_object_card_parameter UNIQUE (parameterized_object_id, parameterized_object_type, parameter_id);


--
-- Name: permissions_group_membership unique_permissions_group_membership_user_id_group_id; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions_group_membership
    ADD CONSTRAINT unique_permissions_group_membership_user_id_group_id UNIQUE (user_id, group_id);


--
-- Name: permissions_group unique_permissions_group_name; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions_group
    ADD CONSTRAINT unique_permissions_group_name UNIQUE (name);


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
-- Name: chart_of_accounts uq_coa_account_code; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.chart_of_accounts
    ADD CONSTRAINT uq_coa_account_code UNIQUE (account_code);


--
-- Name: domain_events uq_domain_events_event_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.domain_events
    ADD CONSTRAINT uq_domain_events_event_key UNIQUE (event_key);


--
-- Name: ellanlab_hardware_assets uq_eha_asset_code; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_hardware_assets
    ADD CONSTRAINT uq_eha_asset_code UNIQUE (asset_code);


--
-- Name: demand_forecast uq_forecast_locker_date; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.demand_forecast
    ADD CONSTRAINT uq_forecast_locker_date UNIQUE (locker_id, forecast_date);


--
-- Name: fulfillment_inventory uq_fulfillment_product; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_inventory
    ADD CONSTRAINT uq_fulfillment_product UNIQUE (fulfillment_center_id, product_id);


--
-- Name: invoices uq_invoice_order; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT uq_invoice_order UNIQUE (order_id);


--
-- Name: journal_entry_lines uq_jel_journal_entry_line_number; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.journal_entry_lines
    ADD CONSTRAINT uq_jel_journal_entry_line_number UNIQUE (journal_entry_id, line_number);


--
-- Name: lifecycle_deadlines uq_lifecycle_deadlines_deadline_key; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.lifecycle_deadlines
    ADD CONSTRAINT uq_lifecycle_deadlines_deadline_key UNIQUE (deadline_key);


--
-- Name: locker_slot_hourly_occupancy uq_lsho_locker_slot_hour; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_slot_hourly_occupancy
    ADD CONSTRAINT uq_lsho_locker_slot_hour UNIQUE (locker_id, slot_number, hour_bucket);


--
-- Name: ml_features_daily uq_ml_features_daily_locker_day; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_features_daily
    ADD CONSTRAINT uq_ml_features_daily_locker_day UNIQUE (locker_id, feature_date);


--
-- Name: seller_products uq_seller_product_locker; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.seller_products
    ADD CONSTRAINT uq_seller_product_locker UNIQUE (seller_id, locker_id, product_id);


--
-- Name: store_inventory uq_store_product; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.store_inventory
    ADD CONSTRAINT uq_store_product UNIQUE (store_id, product_id);


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
-- Name: logistics_carrier_auth_config ux_lcac_carrier_code; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_carrier_auth_config
    ADD CONSTRAINT ux_lcac_carrier_code UNIQUE (carrier_code);


--
-- Name: logistics_carrier_status_map ux_lcsm_carrier_raw_status; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_carrier_status_map
    ADD CONSTRAINT ux_lcsm_carrier_raw_status UNIQUE (carrier_code, raw_status);


--
-- Name: logistics_delivery_attempts ux_lda_delivery_attempt; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_delivery_attempts
    ADD CONSTRAINT ux_lda_delivery_attempt UNIQUE (delivery_id, attempt_number);


--
-- Name: logistics_shipment_labels ux_lsl_tracking_code; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_shipment_labels
    ADD CONSTRAINT ux_lsl_tracking_code UNIQUE (tracking_code);


--
-- Name: product_inventory ux_pi_product_locker_size; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_inventory
    ADD CONSTRAINT ux_pi_product_locker_size UNIQUE (product_id, locker_id, slot_size);


--
-- Name: product_barcodes ux_product_barcodes_value; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_barcodes
    ADD CONSTRAINT ux_product_barcodes_value UNIQUE (barcode_value);


--
-- Name: view_log view_log_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.view_log
    ADD CONSTRAINT view_log_pkey PRIMARY KEY (id);


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


