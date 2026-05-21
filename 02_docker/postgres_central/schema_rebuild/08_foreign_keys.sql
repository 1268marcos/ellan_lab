-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 08_foreign_keys.sql
-- Execução: ver README.md e run_rebuild.sh

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
-- Name: cost_center_monthly cost_center_monthly_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.cost_center_monthly
    ADD CONSTRAINT cost_center_monthly_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: cost_center_monthly cost_center_monthly_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.cost_center_monthly
    ADD CONSTRAINT cost_center_monthly_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id) ON DELETE CASCADE;


--
-- Name: cost_center_monthly cost_center_monthly_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.cost_center_monthly
    ADD CONSTRAINT cost_center_monthly_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- Name: cost_centers cost_centers_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.cost_centers
    ADD CONSTRAINT cost_centers_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: custom_domains custom_domains_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.custom_domains
    ADD CONSTRAINT custom_domains_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenant_fiscal_config(tenant_id);


--
-- Name: customer_subscriptions customer_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.customer_subscriptions
    ADD CONSTRAINT customer_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: data_deletion_requests data_deletion_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.data_deletion_requests
    ADD CONSTRAINT data_deletion_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: demand_forecast demand_forecast_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.demand_forecast
    ADD CONSTRAINT demand_forecast_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: dynamic_pricing_rules dynamic_pricing_rules_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dynamic_pricing_rules
    ADD CONSTRAINT dynamic_pricing_rules_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- Name: dynamic_pricing_rules dynamic_pricing_rules_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dynamic_pricing_rules
    ADD CONSTRAINT dynamic_pricing_rules_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: dynamic_pricing_rules dynamic_pricing_rules_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dynamic_pricing_rules
    ADD CONSTRAINT dynamic_pricing_rules_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: ellanlab_depreciation_schedule ellanlab_depreciation_schedule_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ellanlab_depreciation_schedule
    ADD CONSTRAINT ellanlab_depreciation_schedule_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.ellanlab_hardware_assets(id) ON DELETE CASCADE;


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
-- Name: fiscal_authority_callbacks fiscal_authority_callbacks_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fiscal_authority_callbacks
    ADD CONSTRAINT fiscal_authority_callbacks_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(id) ON DELETE CASCADE;


--
-- Name: action fk_action_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.action
    ADD CONSTRAINT fk_action_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id);


--
-- Name: action fk_action_made_public_by_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.action
    ADD CONSTRAINT fk_action_made_public_by_id FOREIGN KEY (made_public_by_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: action fk_action_model_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.action
    ADD CONSTRAINT fk_action_model_id FOREIGN KEY (model_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: activity fk_activity_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.activity
    ADD CONSTRAINT fk_activity_ref_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: api_key fk_api_key_created_by_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT fk_api_key_created_by_user_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id);


--
-- Name: api_key fk_api_key_updated_by_id_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT fk_api_key_updated_by_id_user_id FOREIGN KEY (updated_by_id) REFERENCES public.core_user(id);


--
-- Name: api_key fk_api_key_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT fk_api_key_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id);


--
-- Name: ble_handshake_logs fk_ble_handshake_locker; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ble_handshake_logs
    ADD CONSTRAINT fk_ble_handshake_locker FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: ble_handshake_logs fk_ble_handshake_pickup; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ble_handshake_logs
    ADD CONSTRAINT fk_ble_handshake_pickup FOREIGN KEY (pickup_id) REFERENCES public.pickups(id) ON DELETE CASCADE;


--
-- Name: bookmark_ordering fk_bookmark_ordering_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.bookmark_ordering
    ADD CONSTRAINT fk_bookmark_ordering_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


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
-- Name: card_bookmark fk_card_bookmark_dashboard_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.card_bookmark
    ADD CONSTRAINT fk_card_bookmark_dashboard_id FOREIGN KEY (card_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: card_bookmark fk_card_bookmark_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.card_bookmark
    ADD CONSTRAINT fk_card_bookmark_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: report_card fk_card_collection_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_card
    ADD CONSTRAINT fk_card_collection_id FOREIGN KEY (collection_id) REFERENCES public.collection(id) ON DELETE SET NULL;


--
-- Name: card_label fk_card_label_ref_card_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.card_label
    ADD CONSTRAINT fk_card_label_ref_card_id FOREIGN KEY (card_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: card_label fk_card_label_ref_label_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.card_label
    ADD CONSTRAINT fk_card_label_ref_label_id FOREIGN KEY (label_id) REFERENCES public.label(id) ON DELETE CASCADE;


--
-- Name: report_card fk_card_made_public_by_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_card
    ADD CONSTRAINT fk_card_made_public_by_id FOREIGN KEY (made_public_by_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: report_card fk_card_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_card
    ADD CONSTRAINT fk_card_ref_user_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: report_cardfavorite fk_cardfavorite_ref_card_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_cardfavorite
    ADD CONSTRAINT fk_cardfavorite_ref_card_id FOREIGN KEY (card_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: report_cardfavorite fk_cardfavorite_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_cardfavorite
    ADD CONSTRAINT fk_cardfavorite_ref_user_id FOREIGN KEY (owner_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: collection_bookmark fk_collection_bookmark_collection_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection_bookmark
    ADD CONSTRAINT fk_collection_bookmark_collection_id FOREIGN KEY (collection_id) REFERENCES public.collection(id) ON DELETE CASCADE;


--
-- Name: collection_bookmark fk_collection_bookmark_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection_bookmark
    ADD CONSTRAINT fk_collection_bookmark_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: collection fk_collection_personal_owner_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection
    ADD CONSTRAINT fk_collection_personal_owner_id FOREIGN KEY (personal_owner_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: collection_permission_graph_revision fk_collection_revision_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.collection_permission_graph_revision
    ADD CONSTRAINT fk_collection_revision_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: connection_impersonations fk_conn_impersonation_db_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.connection_impersonations
    ADD CONSTRAINT fk_conn_impersonation_db_id FOREIGN KEY (db_id) REFERENCES public.metabase_database(id) ON DELETE CASCADE;


--
-- Name: connection_impersonations fk_conn_impersonation_group_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.connection_impersonations
    ADD CONSTRAINT fk_conn_impersonation_group_id FOREIGN KEY (group_id) REFERENCES public.permissions_group(id) ON DELETE CASCADE;


--
-- Name: dashboard_bookmark fk_dashboard_bookmark_dashboard_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_bookmark
    ADD CONSTRAINT fk_dashboard_bookmark_dashboard_id FOREIGN KEY (dashboard_id) REFERENCES public.report_dashboard(id) ON DELETE CASCADE;


--
-- Name: dashboard_bookmark fk_dashboard_bookmark_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_bookmark
    ADD CONSTRAINT fk_dashboard_bookmark_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: report_dashboard fk_dashboard_collection_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboard
    ADD CONSTRAINT fk_dashboard_collection_id FOREIGN KEY (collection_id) REFERENCES public.collection(id) ON DELETE SET NULL;


--
-- Name: dashboard_favorite fk_dashboard_favorite_dashboard_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_favorite
    ADD CONSTRAINT fk_dashboard_favorite_dashboard_id FOREIGN KEY (dashboard_id) REFERENCES public.report_dashboard(id) ON DELETE CASCADE;


--
-- Name: dashboard_favorite fk_dashboard_favorite_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_favorite
    ADD CONSTRAINT fk_dashboard_favorite_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: report_dashboard fk_dashboard_made_public_by_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboard
    ADD CONSTRAINT fk_dashboard_made_public_by_id FOREIGN KEY (made_public_by_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: report_dashboard fk_dashboard_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboard
    ADD CONSTRAINT fk_dashboard_ref_user_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: dashboard_tab fk_dashboard_tab_ref_dashboard_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboard_tab
    ADD CONSTRAINT fk_dashboard_tab_ref_dashboard_id FOREIGN KEY (dashboard_id) REFERENCES public.report_dashboard(id) ON DELETE CASCADE;


--
-- Name: report_dashboardcard fk_dashboardcard_ref_card_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboardcard
    ADD CONSTRAINT fk_dashboardcard_ref_card_id FOREIGN KEY (card_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: report_dashboardcard fk_dashboardcard_ref_dashboard_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboardcard
    ADD CONSTRAINT fk_dashboardcard_ref_dashboard_id FOREIGN KEY (dashboard_id) REFERENCES public.report_dashboard(id) ON DELETE CASCADE;


--
-- Name: dashboardcard_series fk_dashboardcard_series_ref_card_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboardcard_series
    ADD CONSTRAINT fk_dashboardcard_series_ref_card_id FOREIGN KEY (card_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: dashboardcard_series fk_dashboardcard_series_ref_dashboardcard_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dashboardcard_series
    ADD CONSTRAINT fk_dashboardcard_series_ref_dashboardcard_id FOREIGN KEY (dashboardcard_id) REFERENCES public.report_dashboardcard(id) ON DELETE CASCADE;


--
-- Name: metabase_database fk_database_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_database
    ADD CONSTRAINT fk_database_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE SET NULL;


--
-- Name: dimension fk_dimension_displayfk_ref_field_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dimension
    ADD CONSTRAINT fk_dimension_displayfk_ref_field_id FOREIGN KEY (human_readable_field_id) REFERENCES public.metabase_field(id) ON DELETE CASCADE;


--
-- Name: dimension fk_dimension_ref_field_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.dimension
    ADD CONSTRAINT fk_dimension_ref_field_id FOREIGN KEY (field_id) REFERENCES public.metabase_field(id) ON DELETE CASCADE;


--
-- Name: timeline_event fk_event_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.timeline_event
    ADD CONSTRAINT fk_event_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: timeline_event fk_events_timeline_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.timeline_event
    ADD CONSTRAINT fk_events_timeline_id FOREIGN KEY (timeline_id) REFERENCES public.timeline(id) ON DELETE CASCADE;


--
-- Name: metabase_field fk_field_parent_ref_field_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_field
    ADD CONSTRAINT fk_field_parent_ref_field_id FOREIGN KEY (parent_id) REFERENCES public.metabase_field(id) ON DELETE CASCADE;


--
-- Name: metabase_field fk_field_ref_table_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_field
    ADD CONSTRAINT fk_field_ref_table_id FOREIGN KEY (table_id) REFERENCES public.metabase_table(id) ON DELETE CASCADE;


--
-- Name: metabase_fieldvalues fk_fieldvalues_ref_field_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_fieldvalues
    ADD CONSTRAINT fk_fieldvalues_ref_field_id FOREIGN KEY (field_id) REFERENCES public.metabase_field(id) ON DELETE CASCADE;


--
-- Name: application_permissions_revision fk_general_permissions_revision_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.application_permissions_revision
    ADD CONSTRAINT fk_general_permissions_revision_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id);


--
-- Name: sandboxes fk_gtap_card_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sandboxes
    ADD CONSTRAINT fk_gtap_card_id FOREIGN KEY (card_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: sandboxes fk_gtap_group_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sandboxes
    ADD CONSTRAINT fk_gtap_group_id FOREIGN KEY (group_id) REFERENCES public.permissions_group(id) ON DELETE CASCADE;


--
-- Name: sandboxes fk_gtap_table_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sandboxes
    ADD CONSTRAINT fk_gtap_table_id FOREIGN KEY (table_id) REFERENCES public.metabase_table(id) ON DELETE CASCADE;


--
-- Name: http_action fk_http_action_ref_action_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.http_action
    ADD CONSTRAINT fk_http_action_ref_action_id FOREIGN KEY (action_id) REFERENCES public.action(id) ON DELETE CASCADE;


--
-- Name: implicit_action fk_implicit_action_action_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.implicit_action
    ADD CONSTRAINT fk_implicit_action_action_id FOREIGN KEY (action_id) REFERENCES public.action(id) ON DELETE CASCADE;


--
-- Name: login_history fk_login_history_session_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT fk_login_history_session_id FOREIGN KEY (session_id) REFERENCES public.core_session(id) ON DELETE SET NULL;


--
-- Name: login_history fk_login_history_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT fk_login_history_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: metric_important_field fk_metric_important_field_metabase_field_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metric_important_field
    ADD CONSTRAINT fk_metric_important_field_metabase_field_id FOREIGN KEY (field_id) REFERENCES public.metabase_field(id) ON DELETE CASCADE;


--
-- Name: metric_important_field fk_metric_important_field_metric_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metric_important_field
    ADD CONSTRAINT fk_metric_important_field_metric_id FOREIGN KEY (metric_id) REFERENCES public.metric(id) ON DELETE CASCADE;


--
-- Name: metric fk_metric_ref_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metric
    ADD CONSTRAINT fk_metric_ref_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: metric fk_metric_ref_table_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metric
    ADD CONSTRAINT fk_metric_ref_table_id FOREIGN KEY (table_id) REFERENCES public.metabase_table(id) ON DELETE CASCADE;


--
-- Name: model_index fk_model_index_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.model_index
    ADD CONSTRAINT fk_model_index_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: model_index fk_model_index_model_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.model_index
    ADD CONSTRAINT fk_model_index_model_id FOREIGN KEY (model_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: model_index_value fk_model_index_value_model_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.model_index_value
    ADD CONSTRAINT fk_model_index_value_model_id FOREIGN KEY (model_index_id) REFERENCES public.model_index(id) ON DELETE CASCADE;


--
-- Name: parameter_card fk_parameter_card_ref_card_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.parameter_card
    ADD CONSTRAINT fk_parameter_card_ref_card_id FOREIGN KEY (card_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: permissions_group_membership fk_permissions_group_group_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions_group_membership
    ADD CONSTRAINT fk_permissions_group_group_id FOREIGN KEY (group_id) REFERENCES public.permissions_group(id) ON DELETE CASCADE;


--
-- Name: permissions fk_permissions_group_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT fk_permissions_group_id FOREIGN KEY (group_id) REFERENCES public.permissions_group(id) ON DELETE CASCADE;


--
-- Name: permissions_group_membership fk_permissions_group_membership_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions_group_membership
    ADD CONSTRAINT fk_permissions_group_membership_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: permissions_revision fk_permissions_revision_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.permissions_revision
    ADD CONSTRAINT fk_permissions_revision_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: persisted_info fk_persisted_info_card_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.persisted_info
    ADD CONSTRAINT fk_persisted_info_card_id FOREIGN KEY (card_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: persisted_info fk_persisted_info_database_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.persisted_info
    ADD CONSTRAINT fk_persisted_info_database_id FOREIGN KEY (database_id) REFERENCES public.metabase_database(id) ON DELETE CASCADE;


--
-- Name: persisted_info fk_persisted_info_ref_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.persisted_info
    ADD CONSTRAINT fk_persisted_info_ref_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id);


--
-- Name: pickup_events fk_pickup_events_pickup; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pickup_events
    ADD CONSTRAINT fk_pickup_events_pickup FOREIGN KEY (pickup_id) REFERENCES public.pickups(id) ON DELETE CASCADE;


--
-- Name: pulse_card fk_pulse_card_ref_card_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_card
    ADD CONSTRAINT fk_pulse_card_ref_card_id FOREIGN KEY (card_id) REFERENCES public.report_card(id) ON DELETE CASCADE;


--
-- Name: pulse_card fk_pulse_card_ref_pulse_card_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_card
    ADD CONSTRAINT fk_pulse_card_ref_pulse_card_id FOREIGN KEY (dashboard_card_id) REFERENCES public.report_dashboardcard(id) ON DELETE CASCADE;


--
-- Name: pulse_card fk_pulse_card_ref_pulse_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_card
    ADD CONSTRAINT fk_pulse_card_ref_pulse_id FOREIGN KEY (pulse_id) REFERENCES public.pulse(id) ON DELETE CASCADE;


--
-- Name: pulse_channel_recipient fk_pulse_channel_recipient_ref_pulse_channel_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_channel_recipient
    ADD CONSTRAINT fk_pulse_channel_recipient_ref_pulse_channel_id FOREIGN KEY (pulse_channel_id) REFERENCES public.pulse_channel(id) ON DELETE CASCADE;


--
-- Name: pulse_channel_recipient fk_pulse_channel_recipient_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_channel_recipient
    ADD CONSTRAINT fk_pulse_channel_recipient_ref_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: pulse_channel fk_pulse_channel_ref_pulse_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse_channel
    ADD CONSTRAINT fk_pulse_channel_ref_pulse_id FOREIGN KEY (pulse_id) REFERENCES public.pulse(id) ON DELETE CASCADE;


--
-- Name: pulse fk_pulse_collection_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse
    ADD CONSTRAINT fk_pulse_collection_id FOREIGN KEY (collection_id) REFERENCES public.collection(id) ON DELETE SET NULL;


--
-- Name: pulse fk_pulse_ref_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse
    ADD CONSTRAINT fk_pulse_ref_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: pulse fk_pulse_ref_dashboard_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.pulse
    ADD CONSTRAINT fk_pulse_ref_dashboard_id FOREIGN KEY (dashboard_id) REFERENCES public.report_dashboard(id) ON DELETE CASCADE;


--
-- Name: qrtz_blob_triggers fk_qrtz_blob_triggers_triggers; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_blob_triggers
    ADD CONSTRAINT fk_qrtz_blob_triggers_triggers FOREIGN KEY (sched_name, trigger_name, trigger_group) REFERENCES public.qrtz_triggers(sched_name, trigger_name, trigger_group);


--
-- Name: qrtz_cron_triggers fk_qrtz_cron_triggers_triggers; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_cron_triggers
    ADD CONSTRAINT fk_qrtz_cron_triggers_triggers FOREIGN KEY (sched_name, trigger_name, trigger_group) REFERENCES public.qrtz_triggers(sched_name, trigger_name, trigger_group);


--
-- Name: qrtz_simple_triggers fk_qrtz_simple_triggers_triggers; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_simple_triggers
    ADD CONSTRAINT fk_qrtz_simple_triggers_triggers FOREIGN KEY (sched_name, trigger_name, trigger_group) REFERENCES public.qrtz_triggers(sched_name, trigger_name, trigger_group);


--
-- Name: qrtz_simprop_triggers fk_qrtz_simprop_triggers_triggers; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_simprop_triggers
    ADD CONSTRAINT fk_qrtz_simprop_triggers_triggers FOREIGN KEY (sched_name, trigger_name, trigger_group) REFERENCES public.qrtz_triggers(sched_name, trigger_name, trigger_group);


--
-- Name: qrtz_triggers fk_qrtz_triggers_job_details; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.qrtz_triggers
    ADD CONSTRAINT fk_qrtz_triggers_job_details FOREIGN KEY (sched_name, job_name, job_group) REFERENCES public.qrtz_job_details(sched_name, job_name, job_group);


--
-- Name: query_action fk_query_action_database_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.query_action
    ADD CONSTRAINT fk_query_action_database_id FOREIGN KEY (database_id) REFERENCES public.metabase_database(id) ON DELETE CASCADE;


--
-- Name: query_action fk_query_action_ref_action_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.query_action
    ADD CONSTRAINT fk_query_action_ref_action_id FOREIGN KEY (action_id) REFERENCES public.action(id) ON DELETE CASCADE;


--
-- Name: recent_views fk_recent_views_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.recent_views
    ADD CONSTRAINT fk_recent_views_ref_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: report_card fk_report_card_ref_database_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_card
    ADD CONSTRAINT fk_report_card_ref_database_id FOREIGN KEY (database_id) REFERENCES public.metabase_database(id) ON DELETE CASCADE;


--
-- Name: report_card fk_report_card_ref_table_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_card
    ADD CONSTRAINT fk_report_card_ref_table_id FOREIGN KEY (table_id) REFERENCES public.metabase_table(id) ON DELETE CASCADE;


--
-- Name: report_dashboardcard fk_report_dashboardcard_ref_action_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboardcard
    ADD CONSTRAINT fk_report_dashboardcard_ref_action_id FOREIGN KEY (action_id) REFERENCES public.action(id) ON DELETE CASCADE;


--
-- Name: report_dashboardcard fk_report_dashboardcard_ref_dashboard_tab_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.report_dashboardcard
    ADD CONSTRAINT fk_report_dashboardcard_ref_dashboard_tab_id FOREIGN KEY (dashboard_tab_id) REFERENCES public.dashboard_tab(id) ON DELETE CASCADE;


--
-- Name: revision fk_revision_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.revision
    ADD CONSTRAINT fk_revision_ref_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: sandboxes fk_sandboxes_ref_permissions; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sandboxes
    ADD CONSTRAINT fk_sandboxes_ref_permissions FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: secret fk_secret_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.secret
    ADD CONSTRAINT fk_secret_ref_user_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id);


--
-- Name: segment fk_segment_ref_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.segment
    ADD CONSTRAINT fk_segment_ref_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: segment fk_segment_ref_table_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.segment
    ADD CONSTRAINT fk_segment_ref_table_id FOREIGN KEY (table_id) REFERENCES public.metabase_table(id) ON DELETE CASCADE;


--
-- Name: core_session fk_session_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.core_session
    ADD CONSTRAINT fk_session_ref_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: native_query_snippet fk_snippet_collection_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.native_query_snippet
    ADD CONSTRAINT fk_snippet_collection_id FOREIGN KEY (collection_id) REFERENCES public.collection(id) ON DELETE SET NULL;


--
-- Name: native_query_snippet fk_snippet_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.native_query_snippet
    ADD CONSTRAINT fk_snippet_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: table_privileges fk_table_privileges_table_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.table_privileges
    ADD CONSTRAINT fk_table_privileges_table_id FOREIGN KEY (table_id) REFERENCES public.metabase_table(id) ON DELETE CASCADE;


--
-- Name: metabase_table fk_table_ref_database_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.metabase_table
    ADD CONSTRAINT fk_table_ref_database_id FOREIGN KEY (db_id) REFERENCES public.metabase_database(id) ON DELETE CASCADE;


--
-- Name: timeline fk_timeline_collection_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.timeline
    ADD CONSTRAINT fk_timeline_collection_id FOREIGN KEY (collection_id) REFERENCES public.collection(id) ON DELETE CASCADE;


--
-- Name: timeline fk_timeline_creator_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.timeline
    ADD CONSTRAINT fk_timeline_creator_id FOREIGN KEY (creator_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: view_log fk_view_log_ref_user_id; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.view_log
    ADD CONSTRAINT fk_view_log_ref_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) ON DELETE CASCADE;


--
-- Name: fulfillment_inventory fulfillment_inventory_fulfillment_center_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_inventory
    ADD CONSTRAINT fulfillment_inventory_fulfillment_center_id_fkey FOREIGN KEY (fulfillment_center_id) REFERENCES public.fulfillment_centers(id);


--
-- Name: fulfillment_inventory fulfillment_inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_inventory
    ADD CONSTRAINT fulfillment_inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: fulfillment_orders fulfillment_orders_fulfillment_center_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_orders
    ADD CONSTRAINT fulfillment_orders_fulfillment_center_id_fkey FOREIGN KEY (fulfillment_center_id) REFERENCES public.fulfillment_centers(id);


--
-- Name: fulfillment_orders fulfillment_orders_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.fulfillment_orders
    ADD CONSTRAINT fulfillment_orders_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


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
-- Name: inventory_movements inventory_movements_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT inventory_movements_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: inventory_movements inventory_movements_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT inventory_movements_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: inventory_reservations inventory_reservations_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.inventory_reservations
    ADD CONSTRAINT inventory_reservations_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: inventory_reservations inventory_reservations_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.inventory_reservations
    ADD CONSTRAINT inventory_reservations_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: invoice_delivery_log invoice_delivery_log_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.invoice_delivery_log
    ADD CONSTRAINT invoice_delivery_log_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(id) ON DELETE CASCADE;


--
-- Name: invoice_email_outbox invoice_email_outbox_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.invoice_email_outbox
    ADD CONSTRAINT invoice_email_outbox_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(id) ON DELETE CASCADE;


--
-- Name: journal_entry_lines journal_entry_lines_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.journal_entry_lines
    ADD CONSTRAINT journal_entry_lines_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.chart_of_accounts(id);


--
-- Name: journal_entry_lines journal_entry_lines_journal_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.journal_entry_lines
    ADD CONSTRAINT journal_entry_lines_journal_entry_id_fkey FOREIGN KEY (journal_entry_id) REFERENCES public.journal_entries(id) ON DELETE CASCADE;


--
-- Name: locker_capex locker_capex_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_capex
    ADD CONSTRAINT locker_capex_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.ellanlab_hardware_assets(id);


--
-- Name: locker_capex_details locker_capex_details_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_capex_details
    ADD CONSTRAINT locker_capex_details_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id) ON DELETE CASCADE;


--
-- Name: locker_capex locker_capex_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_capex
    ADD CONSTRAINT locker_capex_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: locker_opex locker_opex_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.locker_opex
    ADD CONSTRAINT locker_opex_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


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
-- Name: logistics_capacity_allocations logistics_capacity_allocations_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_capacity_allocations
    ADD CONSTRAINT logistics_capacity_allocations_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: logistics_capacity_allocations logistics_capacity_allocations_logistics_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_capacity_allocations
    ADD CONSTRAINT logistics_capacity_allocations_logistics_partner_id_fkey FOREIGN KEY (logistics_partner_id) REFERENCES public.logistics_partners(id);


--
-- Name: logistics_delivery_attempts logistics_delivery_attempts_delivery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_delivery_attempts
    ADD CONSTRAINT logistics_delivery_attempts_delivery_id_fkey FOREIGN KEY (delivery_id) REFERENCES public.inbound_deliveries(id);


--
-- Name: logistics_manifest_items logistics_manifest_items_delivery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_manifest_items
    ADD CONSTRAINT logistics_manifest_items_delivery_id_fkey FOREIGN KEY (delivery_id) REFERENCES public.inbound_deliveries(id);


--
-- Name: logistics_manifest_items logistics_manifest_items_manifest_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_manifest_items
    ADD CONSTRAINT logistics_manifest_items_manifest_id_fkey FOREIGN KEY (manifest_id) REFERENCES public.logistics_manifests(id);


--
-- Name: logistics_manifests logistics_manifests_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_manifests
    ADD CONSTRAINT logistics_manifests_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: logistics_manifests logistics_manifests_logistics_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_manifests
    ADD CONSTRAINT logistics_manifests_logistics_partner_id_fkey FOREIGN KEY (logistics_partner_id) REFERENCES public.logistics_partners(id);


--
-- Name: logistics_return_events logistics_return_events_return_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_return_events
    ADD CONSTRAINT logistics_return_events_return_id_fkey FOREIGN KEY (return_id) REFERENCES public.logistics_returns(id);


--
-- Name: logistics_shipment_labels logistics_shipment_labels_delivery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_shipment_labels
    ADD CONSTRAINT logistics_shipment_labels_delivery_id_fkey FOREIGN KEY (delivery_id) REFERENCES public.inbound_deliveries(id);


--
-- Name: logistics_tracking_events logistics_tracking_events_delivery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.logistics_tracking_events
    ADD CONSTRAINT logistics_tracking_events_delivery_id_fkey FOREIGN KEY (delivery_id) REFERENCES public.inbound_deliveries(id);


--
-- Name: marketplace_commissions marketplace_commissions_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.marketplace_commissions
    ADD CONSTRAINT marketplace_commissions_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: marketplace_commissions marketplace_commissions_order_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.marketplace_commissions
    ADD CONSTRAINT marketplace_commissions_order_item_id_fkey FOREIGN KEY (order_item_id) REFERENCES public.order_items(id);


--
-- Name: marketplace_commissions marketplace_commissions_seller_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.marketplace_commissions
    ADD CONSTRAINT marketplace_commissions_seller_id_fkey FOREIGN KEY (seller_id) REFERENCES public.marketplace_sellers(id);


--
-- Name: ml_features_daily ml_features_daily_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_features_daily
    ADD CONSTRAINT ml_features_daily_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id) ON DELETE CASCADE;


--
-- Name: ml_prediction_feedback ml_prediction_feedback_prediction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.ml_prediction_feedback
    ADD CONSTRAINT ml_prediction_feedback_prediction_id_fkey FOREIGN KEY (prediction_id) REFERENCES public.ml_predictions_log(id) ON DELETE CASCADE;


--
-- Name: notification_logs notification_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.notification_logs
    ADD CONSTRAINT notification_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: omnichannel_orders omnichannel_orders_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.omnichannel_orders
    ADD CONSTRAINT omnichannel_orders_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: omnichannel_orders omnichannel_orders_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.omnichannel_orders
    ADD CONSTRAINT omnichannel_orders_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.partner_stores(id);


--
-- Name: order_fulfillment_tracking order_fulfillment_tracking_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.order_fulfillment_tracking
    ADD CONSTRAINT order_fulfillment_tracking_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- Name: partner_b2b_invoices partner_b2b_invoices_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_b2b_invoices
    ADD CONSTRAINT partner_b2b_invoices_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.partner_billing_cycles(id);


--
-- Name: partner_billing_cycles partner_billing_cycles_billing_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_billing_cycles
    ADD CONSTRAINT partner_billing_cycles_billing_plan_id_fkey FOREIGN KEY (billing_plan_id) REFERENCES public.partner_billing_plans(id);


--
-- Name: partner_billing_line_items partner_billing_line_items_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_billing_line_items
    ADD CONSTRAINT partner_billing_line_items_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.partner_billing_cycles(id) ON DELETE CASCADE;


--
-- Name: partner_commission_structure partner_commission_structure_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_commission_structure
    ADD CONSTRAINT partner_commission_structure_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.ecommerce_partners(id);


--
-- Name: partner_credit_notes partner_credit_notes_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_credit_notes
    ADD CONSTRAINT partner_credit_notes_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.partner_billing_cycles(id);


--
-- Name: partner_credit_notes partner_credit_notes_original_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_credit_notes
    ADD CONSTRAINT partner_credit_notes_original_invoice_id_fkey FOREIGN KEY (original_invoice_id) REFERENCES public.partner_b2b_invoices(id);


--
-- Name: partner_service_areas partner_service_areas_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_service_areas
    ADD CONSTRAINT partner_service_areas_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: partner_settlement_items partner_settlement_items_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_settlement_items
    ADD CONSTRAINT partner_settlement_items_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES public.partner_settlement_batches(id);


--
-- Name: partner_webhook_deliveries partner_webhook_deliveries_endpoint_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.partner_webhook_deliveries
    ADD CONSTRAINT partner_webhook_deliveries_endpoint_id_fkey FOREIGN KEY (endpoint_id) REFERENCES public.partner_webhook_endpoints(id);


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
-- Name: price_history price_history_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.price_history
    ADD CONSTRAINT price_history_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: price_history price_history_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.price_history
    ADD CONSTRAINT price_history_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: price_history price_history_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.price_history
    ADD CONSTRAINT price_history_rule_id_fkey FOREIGN KEY (rule_id) REFERENCES public.dynamic_pricing_rules(id);


--
-- Name: privacy_consents privacy_consents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.privacy_consents
    ADD CONSTRAINT privacy_consents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: product_barcodes product_barcodes_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_barcodes
    ADD CONSTRAINT product_barcodes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: product_bundle_items product_bundle_items_bundle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_bundle_items
    ADD CONSTRAINT product_bundle_items_bundle_id_fkey FOREIGN KEY (bundle_id) REFERENCES public.product_bundles(id) ON DELETE CASCADE;


--
-- Name: product_bundle_items product_bundle_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_bundle_items
    ADD CONSTRAINT product_bundle_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: product_cogs product_cogs_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_cogs
    ADD CONSTRAINT product_cogs_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: product_inventory product_inventory_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_inventory
    ADD CONSTRAINT product_inventory_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: product_inventory product_inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_inventory
    ADD CONSTRAINT product_inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: product_locker_compatibility product_locker_compatibility_locker_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_locker_compatibility
    ADD CONSTRAINT product_locker_compatibility_locker_type_id_fkey FOREIGN KEY (locker_type_id) REFERENCES public.capability_profile(id);


--
-- Name: product_locker_compatibility product_locker_compatibility_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_locker_compatibility
    ADD CONSTRAINT product_locker_compatibility_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: product_locker_configs product_locker_configs_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_locker_configs
    ADD CONSTRAINT product_locker_configs_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: product_media product_media_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_media
    ADD CONSTRAINT product_media_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: product_recommendations product_recommendations_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_recommendations
    ADD CONSTRAINT product_recommendations_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: product_recommendations product_recommendations_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_recommendations
    ADD CONSTRAINT product_recommendations_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: product_recommendations product_recommendations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.product_recommendations
    ADD CONSTRAINT product_recommendations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: products products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- Name: promotion_product_exclusions promotion_product_exclusions_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.promotion_product_exclusions
    ADD CONSTRAINT promotion_product_exclusions_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: promotion_product_exclusions promotion_product_exclusions_promotion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.promotion_product_exclusions
    ADD CONSTRAINT promotion_product_exclusions_promotion_id_fkey FOREIGN KEY (promotion_id) REFERENCES public.promotions(id) ON DELETE CASCADE;


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
-- Name: return_legs return_legs_from_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_legs
    ADD CONSTRAINT return_legs_from_locker_id_fkey FOREIGN KEY (from_locker_id) REFERENCES public.lockers(id);


--
-- Name: return_legs return_legs_label_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_legs
    ADD CONSTRAINT return_legs_label_id_fkey FOREIGN KEY (label_id) REFERENCES public.logistics_shipment_labels(id);


--
-- Name: return_legs return_legs_logistics_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_legs
    ADD CONSTRAINT return_legs_logistics_partner_id_fkey FOREIGN KEY (logistics_partner_id) REFERENCES public.logistics_partners(id);


--
-- Name: return_legs return_legs_return_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_legs
    ADD CONSTRAINT return_legs_return_request_id_fkey FOREIGN KEY (return_request_id) REFERENCES public.return_requests(id);


--
-- Name: return_requests return_requests_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_requests
    ADD CONSTRAINT return_requests_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: return_requests return_requests_original_delivery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_requests
    ADD CONSTRAINT return_requests_original_delivery_id_fkey FOREIGN KEY (original_delivery_id) REFERENCES public.inbound_deliveries(id);


--
-- Name: return_tracking_events return_tracking_events_return_leg_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.return_tracking_events
    ADD CONSTRAINT return_tracking_events_return_leg_id_fkey FOREIGN KEY (return_leg_id) REFERENCES public.return_legs(id);


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
-- Name: seller_products seller_products_locker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.seller_products
    ADD CONSTRAINT seller_products_locker_id_fkey FOREIGN KEY (locker_id) REFERENCES public.lockers(id);


--
-- Name: seller_products seller_products_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.seller_products
    ADD CONSTRAINT seller_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: seller_products seller_products_seller_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.seller_products
    ADD CONSTRAINT seller_products_seller_id_fkey FOREIGN KEY (seller_id) REFERENCES public.marketplace_sellers(id);


--
-- Name: seller_reviews seller_reviews_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.seller_reviews
    ADD CONSTRAINT seller_reviews_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: seller_reviews seller_reviews_seller_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.seller_reviews
    ADD CONSTRAINT seller_reviews_seller_id_fkey FOREIGN KEY (seller_id) REFERENCES public.marketplace_sellers(id);


--
-- Name: seller_reviews seller_reviews_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.seller_reviews
    ADD CONSTRAINT seller_reviews_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: sla_breach_events sla_breach_events_delivery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sla_breach_events
    ADD CONSTRAINT sla_breach_events_delivery_id_fkey FOREIGN KEY (delivery_id) REFERENCES public.inbound_deliveries(id);


--
-- Name: sla_breach_events sla_breach_events_logistics_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sla_breach_events
    ADD CONSTRAINT sla_breach_events_logistics_partner_id_fkey FOREIGN KEY (logistics_partner_id) REFERENCES public.logistics_partners(id);


--
-- Name: sla_breach_events sla_breach_events_return_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.sla_breach_events
    ADD CONSTRAINT sla_breach_events_return_request_id_fkey FOREIGN KEY (return_request_id) REFERENCES public.return_requests(id);


--
-- Name: store_inventory store_inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.store_inventory
    ADD CONSTRAINT store_inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: store_inventory store_inventory_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE ONLY public.store_inventory
    ADD CONSTRAINT store_inventory_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.partner_stores(id);


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


