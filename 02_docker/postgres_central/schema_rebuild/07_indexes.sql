-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 07_indexes.sql
-- Execução: ver README.md e run_rebuild.sh

--
-- Name: ellanlab_revenue_recognition_recognition_date_idx; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ellanlab_revenue_recognition_recognition_date_idx ON public.ellanlab_revenue_recognition USING btree (recognition_date DESC);


--
-- Name: idx_action_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_action_creator_id ON public.action USING btree (creator_id);


--
-- Name: idx_action_made_public_by_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_action_made_public_by_id ON public.action USING btree (made_public_by_id);


--
-- Name: idx_action_model_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_action_model_id ON public.action USING btree (model_id);


--
-- Name: idx_action_public_uuid; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_action_public_uuid ON public.action USING btree (public_uuid);


--
-- Name: idx_activity_custom_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_activity_custom_id ON public.activity USING btree (custom_id);


--
-- Name: idx_activity_entity_qualified_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_activity_entity_qualified_id ON public.activity USING btree ((
CASE
    WHEN ((model)::text = 'Dataset'::text) THEN ('card_'::text || model_id)
    WHEN (model_id IS NULL) THEN NULL::text
    ELSE ((lower((model)::text) || '_'::text) || model_id)
END));


--
-- Name: idx_activity_timestamp; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_activity_timestamp ON public.activity USING btree ("timestamp");


--
-- Name: idx_activity_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_activity_user_id ON public.activity USING btree (user_id);


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
-- Name: idx_api_key_created_by; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_api_key_created_by ON public.api_key USING btree (creator_id);


--
-- Name: idx_api_key_updated_by_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_api_key_updated_by_id ON public.api_key USING btree (updated_by_id);


--
-- Name: idx_api_key_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_api_key_user_id ON public.api_key USING btree (user_id);


--
-- Name: idx_application_permissions_revision_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_application_permissions_revision_user_id ON public.application_permissions_revision USING btree (user_id);


--
-- Name: idx_audit_log_entity_qualified_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_audit_log_entity_qualified_id ON public.audit_log USING btree ((
CASE
    WHEN ((model)::text = 'Dataset'::text) THEN ('card_'::text || model_id)
    WHEN (model_id IS NULL) THEN NULL::text
    ELSE ((lower((model)::text) || '_'::text) || model_id)
END));


--
-- Name: idx_ble_handshake_created_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ble_handshake_created_at ON public.ble_handshake_logs USING btree (created_at);


--
-- Name: idx_ble_handshake_locker_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ble_handshake_locker_created ON public.ble_handshake_logs USING btree (locker_id, created_at DESC);


--
-- Name: idx_ble_handshake_pickup; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ble_handshake_pickup ON public.ble_handshake_logs USING btree (pickup_id);


--
-- Name: idx_ble_handshake_status_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ble_handshake_status_created ON public.ble_handshake_logs USING btree (status, created_at DESC);


--
-- Name: idx_bookmark_ordering_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_bookmark_ordering_user_id ON public.bookmark_ordering USING btree (user_id);


--
-- Name: idx_capability_locker_location_geom_gist; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_capability_locker_location_geom_gist ON public.capability_locker_location USING gist (geom);


--
-- Name: idx_card_bookmark_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_card_bookmark_card_id ON public.card_bookmark USING btree (card_id);


--
-- Name: idx_card_bookmark_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_card_bookmark_user_id ON public.card_bookmark USING btree (user_id);


--
-- Name: idx_card_collection_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_card_collection_id ON public.report_card USING btree (collection_id);


--
-- Name: idx_card_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_card_creator_id ON public.report_card USING btree (creator_id);


--
-- Name: idx_card_label_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_card_label_card_id ON public.card_label USING btree (card_id);


--
-- Name: idx_card_label_label_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_card_label_label_id ON public.card_label USING btree (label_id);


--
-- Name: idx_card_public_uuid; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_card_public_uuid ON public.report_card USING btree (public_uuid);


--
-- Name: idx_cardfavorite_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_cardfavorite_card_id ON public.report_cardfavorite USING btree (card_id);


--
-- Name: idx_cardfavorite_owner_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_cardfavorite_owner_id ON public.report_cardfavorite USING btree (owner_id);


--
-- Name: idx_collection_bookmark_collection_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_collection_bookmark_collection_id ON public.collection_bookmark USING btree (collection_id);


--
-- Name: idx_collection_bookmark_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_collection_bookmark_user_id ON public.collection_bookmark USING btree (user_id);


--
-- Name: idx_collection_location; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_collection_location ON public.collection USING btree (location);


--
-- Name: idx_collection_permission_graph_revision_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_collection_permission_graph_revision_user_id ON public.collection_permission_graph_revision USING btree (user_id);


--
-- Name: idx_collection_personal_owner_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_collection_personal_owner_id ON public.collection USING btree (personal_owner_id);


--
-- Name: idx_conn_impersonations_db_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_conn_impersonations_db_id ON public.connection_impersonations USING btree (db_id);


--
-- Name: idx_conn_impersonations_group_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_conn_impersonations_group_id ON public.connection_impersonations USING btree (group_id);


--
-- Name: idx_core_session_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_core_session_user_id ON public.core_session USING btree (user_id);


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
-- Name: idx_dashboard_bookmark_dashboard_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboard_bookmark_dashboard_id ON public.dashboard_bookmark USING btree (dashboard_id);


--
-- Name: idx_dashboard_bookmark_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboard_bookmark_user_id ON public.dashboard_bookmark USING btree (user_id);


--
-- Name: idx_dashboard_collection_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboard_collection_id ON public.report_dashboard USING btree (collection_id);


--
-- Name: idx_dashboard_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboard_creator_id ON public.report_dashboard USING btree (creator_id);


--
-- Name: idx_dashboard_favorite_dashboard_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboard_favorite_dashboard_id ON public.dashboard_favorite USING btree (dashboard_id);


--
-- Name: idx_dashboard_favorite_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboard_favorite_user_id ON public.dashboard_favorite USING btree (user_id);


--
-- Name: idx_dashboard_public_uuid; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboard_public_uuid ON public.report_dashboard USING btree (public_uuid);


--
-- Name: idx_dashboard_tab_dashboard_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboard_tab_dashboard_id ON public.dashboard_tab USING btree (dashboard_id);


--
-- Name: idx_dashboardcard_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboardcard_card_id ON public.report_dashboardcard USING btree (card_id);


--
-- Name: idx_dashboardcard_dashboard_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboardcard_dashboard_id ON public.report_dashboardcard USING btree (dashboard_id);


--
-- Name: idx_dashboardcard_series_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboardcard_series_card_id ON public.dashboardcard_series USING btree (card_id);


--
-- Name: idx_dashboardcard_series_dashboardcard_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dashboardcard_series_dashboardcard_id ON public.dashboardcard_series USING btree (dashboardcard_id);


--
-- Name: idx_dependency_dependent_on_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dependency_dependent_on_id ON public.dependency USING btree (dependent_on_id);


--
-- Name: idx_dependency_dependent_on_model; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dependency_dependent_on_model ON public.dependency USING btree (dependent_on_model);


--
-- Name: idx_dependency_model; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dependency_model ON public.dependency USING btree (model);


--
-- Name: idx_dependency_model_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dependency_model_id ON public.dependency USING btree (model_id);


--
-- Name: idx_dimension_field_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dimension_field_id ON public.dimension USING btree (field_id);


--
-- Name: idx_dimension_human_readable_field_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_dimension_human_readable_field_id ON public.dimension USING btree (human_readable_field_id);


--
-- Name: idx_door_state_machine; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_door_state_machine ON public.door_state USING btree (machine_id);


--
-- Name: idx_door_state_machine_state; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_door_state_machine_state ON public.door_state USING btree (machine_id, state);


--
-- Name: idx_facl_order; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_facl_order ON public.fiscal_auto_classification_log USING btree (order_id);


--
-- Name: idx_facl_source_classified; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_facl_source_classified ON public.fiscal_auto_classification_log USING btree (source, classified_at DESC);


--
-- Name: idx_field_entity_qualified_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_field_entity_qualified_id ON public.metabase_field USING btree ((('field_'::text || id)));


--
-- Name: idx_field_parent_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_field_parent_id ON public.metabase_field USING btree (parent_id);


--
-- Name: idx_field_table_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_field_table_id ON public.metabase_field USING btree (table_id);


--
-- Name: idx_fieldvalues_field_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_fieldvalues_field_id ON public.metabase_fieldvalues USING btree (field_id);


--
-- Name: idx_fiscal_order_attempt; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_fiscal_order_attempt ON public.fiscal_documents USING btree (order_id, attempt);


--
-- Name: idx_gtap_table_id_group_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_gtap_table_id_group_id ON public.sandboxes USING btree (table_id, group_id);


--
-- Name: idx_im_locker_occurred; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_im_locker_occurred ON public.inventory_movements USING btree (locker_id, occurred_at DESC);


--
-- Name: idx_im_product_locker_occurred; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_im_product_locker_occurred ON public.inventory_movements USING btree (product_id, locker_id, occurred_at DESC);


--
-- Name: idx_invoices_ecommerce_partner_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_invoices_ecommerce_partner_id ON public.invoices USING btree (ecommerce_partner_id);


--
-- Name: idx_ir_expiry_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ir_expiry_active ON public.inventory_reservations USING btree (expires_at) WHERE ((status)::text = 'ACTIVE'::text);


--
-- Name: idx_ir_order_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ir_order_status ON public.inventory_reservations USING btree (order_id, status, updated_at DESC);


--
-- Name: idx_ir_product_locker_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ir_product_locker_status ON public.inventory_reservations USING btree (product_id, locker_id, slot_size, status);


--
-- Name: idx_label_slug; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_label_slug ON public.label USING btree (slug);


--
-- Name: idx_lca_active_window; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lca_active_window ON public.logistics_capacity_allocations USING btree (is_active, valid_from, valid_until);


--
-- Name: idx_lca_partner_locker_slot; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lca_partner_locker_slot ON public.logistics_capacity_allocations USING btree (logistics_partner_id, locker_id, slot_size);


--
-- Name: idx_lcr_lookup; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lcr_lookup ON public.logistics_carrier_rates USING btree (carrier_code, origin_zone, destination_zone, is_active);


--
-- Name: idx_lcr_validity; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lcr_validity ON public.logistics_carrier_rates USING btree (valid_from, valid_until);


--
-- Name: idx_lcsm_carrier; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lcsm_carrier ON public.logistics_carrier_status_map USING btree (carrier_code, active);


--
-- Name: idx_lda_delivery_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lda_delivery_time ON public.logistics_delivery_attempts USING btree (delivery_id, attempted_at DESC);


--
-- Name: idx_lm_locker_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lm_locker_status ON public.logistics_manifests USING btree (locker_id, status, manifest_date DESC);


--
-- Name: idx_lm_partner_date; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lm_partner_date ON public.logistics_manifests USING btree (logistics_partner_id, manifest_date DESC);


--
-- Name: idx_lmi_manifest; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lmi_manifest ON public.logistics_manifest_items USING btree (manifest_id);


--
-- Name: idx_location_ble_geom; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_location_ble_geom ON public.capability_locker_location USING gist (geom) WHERE ((has_ble = true) AND (is_active = true));


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
-- Name: idx_lockers_active_ble; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lockers_active_ble ON public.lockers USING btree (active, has_ble) WHERE (active = true);


--
-- Name: idx_lockers_external_id_ble; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lockers_external_id_ble ON public.lockers USING btree (external_id, has_ble) WHERE (has_ble = true);


--
-- Name: idx_lockers_has_ble; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lockers_has_ble ON public.lockers USING btree (has_ble) WHERE (has_ble = true);


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
-- Name: idx_lower_email; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lower_email ON public.core_user USING btree (lower((email)::text));


--
-- Name: idx_lr_order_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lr_order_created ON public.logistics_returns USING btree (order_id, created_at DESC);


--
-- Name: idx_lr_partner_status_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lr_partner_status_created ON public.logistics_returns USING btree (partner_id, status, created_at DESC);


--
-- Name: idx_lre_return_occurred; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lre_return_occurred ON public.logistics_return_events USING btree (return_id, occurred_at DESC);


--
-- Name: idx_lsl_delivery; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lsl_delivery ON public.logistics_shipment_labels USING btree (delivery_id, created_at DESC);


--
-- Name: idx_lte_delivery_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lte_delivery_time ON public.logistics_tracking_events USING btree (delivery_id, occurred_at DESC);


--
-- Name: idx_lte_source_ref; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_lte_source_ref ON public.logistics_tracking_events USING btree (source, source_ref);


--
-- Name: idx_metabase_database_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_metabase_database_creator_id ON public.metabase_database USING btree (creator_id);


--
-- Name: idx_metabase_table_db_id_schema; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_metabase_table_db_id_schema ON public.metabase_table USING btree (db_id, schema);


--
-- Name: idx_metabase_table_show_in_getting_started; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_metabase_table_show_in_getting_started ON public.metabase_table USING btree (show_in_getting_started);


--
-- Name: idx_metric_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_metric_creator_id ON public.metric USING btree (creator_id);


--
-- Name: idx_metric_important_field_field_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_metric_important_field_field_id ON public.metric_important_field USING btree (field_id);


--
-- Name: idx_metric_important_field_metric_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_metric_important_field_metric_id ON public.metric_important_field USING btree (metric_id);


--
-- Name: idx_metric_show_in_getting_started; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_metric_show_in_getting_started ON public.metric USING btree (show_in_getting_started);


--
-- Name: idx_metric_table_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_metric_table_id ON public.metric USING btree (table_id);


--
-- Name: idx_ml_features_70d_locker_date; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ml_features_70d_locker_date ON public.ml_features_daily USING btree (locker_id, feature_date DESC);


--
-- Name: idx_ml_feedback_feedback_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ml_feedback_feedback_at ON public.ml_prediction_feedback USING btree (feedback_at);


--
-- Name: idx_ml_feedback_prediction; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ml_feedback_prediction ON public.ml_prediction_feedback USING btree (prediction_id);


--
-- Name: idx_ml_feedback_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ml_feedback_status ON public.ml_prediction_feedback USING btree (model_performance_status);


--
-- Name: idx_model_index_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_model_index_creator_id ON public.model_index USING btree (creator_id);


--
-- Name: idx_model_index_model_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_model_index_model_id ON public.model_index USING btree (model_id);


--
-- Name: idx_moderation_review_item_type_item_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_moderation_review_item_type_item_id ON public.moderation_review USING btree (moderated_item_type, moderated_item_id);


--
-- Name: idx_mv_locker_pnl_pk; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX idx_mv_locker_pnl_pk ON public.mv_locker_monthly_pnl USING btree (month_ref, locker_id);


--
-- Name: idx_native_query_snippet_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_native_query_snippet_creator_id ON public.native_query_snippet USING btree (creator_id);


--
-- Name: idx_oft_partner_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_oft_partner_status ON public.order_fulfillment_tracking USING btree (partner_id, status);


--
-- Name: idx_oft_status_updated; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_oft_status_updated ON public.order_fulfillment_tracking USING btree (status, updated_at);


--
-- Name: idx_oorp_runs_created_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_oorp_runs_created_at ON public.ops_outbox_replay_priority_runs USING btree (created_at DESC);


--
-- Name: idx_oorp_runs_dry_mode; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_oorp_runs_dry_mode ON public.ops_outbox_replay_priority_runs USING btree (dry_run, run_after_replay, created_at DESC);


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
-- Name: idx_pak_partner; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pak_partner ON public.partner_api_keys USING btree (partner_id, partner_type);


--
-- Name: idx_parameter_card_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_parameter_card_card_id ON public.parameter_card USING btree (card_id);


--
-- Name: idx_parameter_card_parameterized_object_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_parameter_card_parameterized_object_id ON public.parameter_card USING btree (parameterized_object_id);


--
-- Name: idx_pb_active_window; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pb_active_window ON public.product_bundles USING btree (is_active, valid_from, valid_until);


--
-- Name: idx_pb_primary; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pb_primary ON public.product_barcodes USING btree (product_id, is_primary);


--
-- Name: idx_pb_product_type; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pb_product_type ON public.product_barcodes USING btree (product_id, barcode_type, created_at DESC);


--
-- Name: idx_pbi_bundle_sort; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pbi_bundle_sort ON public.product_bundle_items USING btree (bundle_id, sort_order);


--
-- Name: idx_pc_partner; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pc_partner ON public.partner_contacts USING btree (partner_id, contact_type);


--
-- Name: idx_permissions_group_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_permissions_group_id ON public.permissions USING btree (group_id);


--
-- Name: idx_permissions_group_id_object; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_permissions_group_id_object ON public.permissions USING btree (group_id, object);


--
-- Name: idx_permissions_group_membership_group_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_permissions_group_membership_group_id ON public.permissions_group_membership USING btree (group_id);


--
-- Name: idx_permissions_group_membership_group_id_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_permissions_group_membership_group_id_user_id ON public.permissions_group_membership USING btree (group_id, user_id);


--
-- Name: idx_permissions_group_membership_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_permissions_group_membership_user_id ON public.permissions_group_membership USING btree (user_id);


--
-- Name: idx_permissions_group_name; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_permissions_group_name ON public.permissions_group USING btree (name);


--
-- Name: idx_permissions_object; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_permissions_object ON public.permissions USING btree (object);


--
-- Name: idx_permissions_revision_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_permissions_revision_user_id ON public.permissions_revision USING btree (user_id);


--
-- Name: idx_persisted_info_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_persisted_info_creator_id ON public.persisted_info USING btree (creator_id);


--
-- Name: idx_persisted_info_database_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_persisted_info_database_id ON public.persisted_info USING btree (database_id);


--
-- Name: idx_pfc_is_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pfc_is_active ON public.product_fiscal_config USING btree (is_active);


--
-- Name: idx_pfc_origin_cfop_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pfc_origin_cfop_active ON public.product_fiscal_config USING btree (origin_type, cfop, is_active);


--
-- Name: idx_pfc_updated_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pfc_updated_at ON public.product_fiscal_config USING btree (updated_at DESC);


--
-- Name: idx_pi_locker_available; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pi_locker_available ON public.product_inventory USING btree (locker_id, quantity_available, updated_at DESC);


--
-- Name: idx_pi_product_updated; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pi_product_updated ON public.product_inventory USING btree (product_id, updated_at DESC);


--
-- Name: idx_pickups_ble_redeemed; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pickups_ble_redeemed ON public.pickups USING btree (locker_id, redeemed_at DESC) WHERE (redeemed_via = 'BLE'::public.pickupredeemvia);


--
-- Name: idx_pih_partner_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pih_partner_time ON public.partner_integration_health USING btree (partner_id, checked_at DESC);


--
-- Name: idx_pm_primary; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pm_primary ON public.product_media USING btree (product_id, is_primary);


--
-- Name: idx_pm_product_sort; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pm_product_sort ON public.product_media USING btree (product_id, sort_order, created_at DESC);


--
-- Name: idx_pmui_ui_code; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pmui_ui_code ON public.payment_method_ui_alias USING btree (ui_code);


--
-- Name: idx_poeo_partner_order; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_poeo_partner_order ON public.partner_order_events_outbox USING btree (partner_id, order_id);


--
-- Name: idx_poeo_status_retry; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_poeo_status_retry ON public.partner_order_events_outbox USING btree (status, next_retry_at);


--
-- Name: idx_ppm_partner_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_ppm_partner_month ON public.partner_performance_metrics USING btree (partner_id, period_month DESC);


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
-- Name: idx_promotions_active_window; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_promotions_active_window ON public.promotions USING btree (is_active, valid_from, valid_until);


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
-- Name: idx_prsh_product; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_prsh_product ON public.product_status_history USING btree (product_id, changed_at DESC);


--
-- Name: idx_psa_partner_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_psa_partner_active ON public.partner_sla_agreements USING btree (partner_id, is_active);


--
-- Name: idx_psa_partner_locker_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX idx_psa_partner_locker_active ON public.partner_service_areas USING btree (partner_id, locker_id) WHERE (is_active IS TRUE);


--
-- Name: idx_psa_partner_priority; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_psa_partner_priority ON public.partner_service_areas USING btree (partner_id, priority, created_at DESC);


--
-- Name: idx_psb_partner_period; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_psb_partner_period ON public.partner_settlement_batches USING btree (partner_id, period_start, period_end);


--
-- Name: idx_psh_partner; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_psh_partner ON public.partner_status_history USING btree (partner_id, changed_at DESC);


--
-- Name: idx_psi_batch; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_psi_batch ON public.partner_settlement_items USING btree (batch_id);


--
-- Name: idx_pulse_card_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_card_card_id ON public.pulse_card USING btree (card_id);


--
-- Name: idx_pulse_card_dashboard_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_card_dashboard_card_id ON public.pulse_card USING btree (dashboard_card_id);


--
-- Name: idx_pulse_card_pulse_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_card_pulse_id ON public.pulse_card USING btree (pulse_id);


--
-- Name: idx_pulse_channel_pulse_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_channel_pulse_id ON public.pulse_channel USING btree (pulse_id);


--
-- Name: idx_pulse_channel_recipient_pulse_channel_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_channel_recipient_pulse_channel_id ON public.pulse_channel_recipient USING btree (pulse_channel_id);


--
-- Name: idx_pulse_channel_recipient_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_channel_recipient_user_id ON public.pulse_channel_recipient USING btree (user_id);


--
-- Name: idx_pulse_channel_schedule_type; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_channel_schedule_type ON public.pulse_channel USING btree (schedule_type);


--
-- Name: idx_pulse_collection_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_collection_id ON public.pulse USING btree (collection_id);


--
-- Name: idx_pulse_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_creator_id ON public.pulse USING btree (creator_id);


--
-- Name: idx_pulse_dashboard_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pulse_dashboard_id ON public.pulse USING btree (dashboard_id);


--
-- Name: idx_pwd_endpoint; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pwd_endpoint ON public.partner_webhook_deliveries USING btree (endpoint_id);


--
-- Name: idx_pwd_status_retry; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pwd_status_retry ON public.partner_webhook_deliveries USING btree (status, next_retry_at);


--
-- Name: idx_pwe_partner; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_pwe_partner ON public.partner_webhook_endpoints USING btree (partner_id, partner_type);


--
-- Name: idx_qrtz_ft_inst_job_req_rcvry; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_ft_inst_job_req_rcvry ON public.qrtz_fired_triggers USING btree (sched_name, instance_name, requests_recovery);


--
-- Name: idx_qrtz_ft_j_g; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_ft_j_g ON public.qrtz_fired_triggers USING btree (sched_name, job_name, job_group);


--
-- Name: idx_qrtz_ft_jg; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_ft_jg ON public.qrtz_fired_triggers USING btree (sched_name, job_group);


--
-- Name: idx_qrtz_ft_t_g; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_ft_t_g ON public.qrtz_fired_triggers USING btree (sched_name, trigger_name, trigger_group);


--
-- Name: idx_qrtz_ft_tg; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_ft_tg ON public.qrtz_fired_triggers USING btree (sched_name, trigger_group);


--
-- Name: idx_qrtz_ft_trig_inst_name; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_ft_trig_inst_name ON public.qrtz_fired_triggers USING btree (sched_name, instance_name);


--
-- Name: idx_qrtz_j_grp; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_j_grp ON public.qrtz_job_details USING btree (sched_name, job_group);


--
-- Name: idx_qrtz_j_req_recovery; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_j_req_recovery ON public.qrtz_job_details USING btree (sched_name, requests_recovery);


--
-- Name: idx_qrtz_t_c; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_c ON public.qrtz_triggers USING btree (sched_name, calendar_name);


--
-- Name: idx_qrtz_t_g; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_g ON public.qrtz_triggers USING btree (sched_name, trigger_group);


--
-- Name: idx_qrtz_t_j; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_j ON public.qrtz_triggers USING btree (sched_name, job_name, job_group);


--
-- Name: idx_qrtz_t_jg; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_jg ON public.qrtz_triggers USING btree (sched_name, job_group);


--
-- Name: idx_qrtz_t_n_g_state; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_n_g_state ON public.qrtz_triggers USING btree (sched_name, trigger_group, trigger_state);


--
-- Name: idx_qrtz_t_n_state; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_n_state ON public.qrtz_triggers USING btree (sched_name, trigger_name, trigger_group, trigger_state);


--
-- Name: idx_qrtz_t_next_fire_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_next_fire_time ON public.qrtz_triggers USING btree (sched_name, next_fire_time);


--
-- Name: idx_qrtz_t_nft_misfire; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_nft_misfire ON public.qrtz_triggers USING btree (sched_name, misfire_instr, next_fire_time);


--
-- Name: idx_qrtz_t_nft_st; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_nft_st ON public.qrtz_triggers USING btree (sched_name, trigger_state, next_fire_time);


--
-- Name: idx_qrtz_t_nft_st_misfire; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_nft_st_misfire ON public.qrtz_triggers USING btree (sched_name, misfire_instr, next_fire_time, trigger_state);


--
-- Name: idx_qrtz_t_nft_st_misfire_grp; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_nft_st_misfire_grp ON public.qrtz_triggers USING btree (sched_name, misfire_instr, next_fire_time, trigger_group, trigger_state);


--
-- Name: idx_qrtz_t_state; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_qrtz_t_state ON public.qrtz_triggers USING btree (sched_name, trigger_state);


--
-- Name: idx_query_action_database_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_action_database_id ON public.query_action USING btree (database_id);


--
-- Name: idx_query_cache_updated_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_cache_updated_at ON public.query_cache USING btree (updated_at);


--
-- Name: idx_query_execution_action_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_execution_action_id ON public.query_execution USING btree (action_id);


--
-- Name: idx_query_execution_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_execution_card_id ON public.query_execution USING btree (card_id);


--
-- Name: idx_query_execution_card_id_started_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_execution_card_id_started_at ON public.query_execution USING btree (card_id, started_at);


--
-- Name: idx_query_execution_card_qualified_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_execution_card_qualified_id ON public.query_execution USING btree ((('card_'::text || card_id)));


--
-- Name: idx_query_execution_context; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_execution_context ON public.query_execution USING btree (context);


--
-- Name: idx_query_execution_executor_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_execution_executor_id ON public.query_execution USING btree (executor_id);


--
-- Name: idx_query_execution_query_hash_started_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_execution_query_hash_started_at ON public.query_execution USING btree (hash, started_at);


--
-- Name: idx_query_execution_started_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_query_execution_started_at ON public.query_execution USING btree (started_at);


--
-- Name: idx_recent_views_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_recent_views_user_id ON public.recent_views USING btree (user_id);


--
-- Name: idx_report_card_database_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_report_card_database_id ON public.report_card USING btree (database_id);


--
-- Name: idx_report_card_made_public_by_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_report_card_made_public_by_id ON public.report_card USING btree (made_public_by_id);


--
-- Name: idx_report_card_table_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_report_card_table_id ON public.report_card USING btree (table_id);


--
-- Name: idx_report_dashboard_made_public_by_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_report_dashboard_made_public_by_id ON public.report_dashboard USING btree (made_public_by_id);


--
-- Name: idx_report_dashboard_show_in_getting_started; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_report_dashboard_show_in_getting_started ON public.report_dashboard USING btree (show_in_getting_started);


--
-- Name: idx_report_dashboardcard_action_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_report_dashboardcard_action_id ON public.report_dashboardcard USING btree (action_id);


--
-- Name: idx_report_dashboardcard_dashboard_tab_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_report_dashboardcard_dashboard_tab_id ON public.report_dashboardcard USING btree (dashboard_tab_id);


--
-- Name: idx_revision_model_model_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_revision_model_model_id ON public.revision USING btree (model, model_id);


--
-- Name: idx_revision_most_recent; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_revision_most_recent ON public.revision USING btree (most_recent);


--
-- Name: idx_revision_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_revision_user_id ON public.revision USING btree (user_id);


--
-- Name: idx_rl_return_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_rl_return_status ON public.return_legs USING btree (return_request_id, status);


--
-- Name: idx_rr_delivery_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_rr_delivery_created ON public.return_requests USING btree (original_delivery_id, created_at DESC);


--
-- Name: idx_rr_status_requested; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_rr_status_requested ON public.return_requests USING btree (status, requested_at DESC);


--
-- Name: idx_rte_leg_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_rte_leg_time ON public.return_tracking_events USING btree (return_leg_id, occurred_at DESC);


--
-- Name: idx_runtime_locker_features_ble; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_runtime_locker_features_ble ON public.runtime_locker_features USING btree (supports_ble) WHERE (supports_ble = true);


--
-- Name: idx_runtime_locker_slots_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_runtime_locker_slots_active ON public.runtime_locker_slots USING btree (locker_id, is_active, slot_number);


--
-- Name: idx_runtime_lockers_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_runtime_lockers_active ON public.runtime_lockers USING btree (active, runtime_enabled);


--
-- Name: idx_runtime_lockers_ble; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_runtime_lockers_ble ON public.runtime_lockers USING btree (runtime_enabled, locker_id) WHERE (runtime_enabled = true);


--
-- Name: idx_runtime_lockers_region; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_runtime_lockers_region ON public.runtime_lockers USING btree (region);


--
-- Name: idx_sandboxes_card_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_sandboxes_card_id ON public.sandboxes USING btree (card_id);


--
-- Name: idx_sandboxes_permission_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_sandboxes_permission_id ON public.sandboxes USING btree (permission_id);


--
-- Name: idx_sbe_detected; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_sbe_detected ON public.sla_breach_events USING btree (detected_at DESC);


--
-- Name: idx_sbe_type_severity; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_sbe_type_severity ON public.sla_breach_events USING btree (breach_type, severity);


--
-- Name: idx_secret_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_secret_creator_id ON public.secret USING btree (creator_id);


--
-- Name: idx_segment_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_segment_creator_id ON public.segment USING btree (creator_id);


--
-- Name: idx_segment_show_in_getting_started; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_segment_show_in_getting_started ON public.segment USING btree (show_in_getting_started);


--
-- Name: idx_segment_table_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_segment_table_id ON public.segment USING btree (table_id);


--
-- Name: idx_session_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_session_id ON public.login_history USING btree (session_id);


--
-- Name: idx_snippet_collection_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_snippet_collection_id ON public.native_query_snippet USING btree (collection_id);


--
-- Name: idx_snippet_name; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_snippet_name ON public.native_query_snippet USING btree (name);


--
-- Name: idx_table_db_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_table_db_id ON public.metabase_table USING btree (db_id);


--
-- Name: idx_table_privileges_role; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_table_privileges_role ON public.table_privileges USING btree (role);


--
-- Name: idx_table_privileges_table_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_table_privileges_table_id ON public.table_privileges USING btree (table_id);


--
-- Name: idx_task_history_db_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_task_history_db_id ON public.task_history USING btree (db_id);


--
-- Name: idx_task_history_end_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_task_history_end_time ON public.task_history USING btree (ended_at);


--
-- Name: idx_task_history_started_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_task_history_started_at ON public.task_history USING btree (started_at);


--
-- Name: idx_timeline_collection_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_timeline_collection_id ON public.timeline USING btree (collection_id);


--
-- Name: idx_timeline_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_timeline_creator_id ON public.timeline USING btree (creator_id);


--
-- Name: idx_timeline_event_creator_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_timeline_event_creator_id ON public.timeline_event USING btree (creator_id);


--
-- Name: idx_timeline_event_timeline_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_timeline_event_timeline_id ON public.timeline_event USING btree (timeline_id);


--
-- Name: idx_timeline_event_timeline_id_timestamp; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_timeline_event_timeline_id_timestamp ON public.timeline_event USING btree (timeline_id, "timestamp");


--
-- Name: idx_timestamp; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_timestamp ON public.login_history USING btree ("timestamp");


--
-- Name: idx_uniq_field_table_id_parent_id_name_2col; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX idx_uniq_field_table_id_parent_id_name_2col ON public.metabase_field USING btree (table_id, name) WHERE (parent_id IS NULL);


--
-- Name: idx_uniq_table_db_id_schema_name_2col; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX idx_uniq_table_db_id_schema_name_2col ON public.metabase_table USING btree (db_id, name) WHERE (schema IS NULL);


--
-- Name: idx_user_full_name; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_user_full_name ON public.core_user USING btree (((((first_name)::text || ' '::text) || (last_name)::text)));


--
-- Name: idx_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_user_id ON public.login_history USING btree (user_id);


--
-- Name: idx_user_id_device_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_user_id_device_id ON public.login_history USING btree (session_id, device_id);


--
-- Name: idx_user_id_timestamp; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_user_id_timestamp ON public.login_history USING btree (user_id, "timestamp");


--
-- Name: idx_user_qualified_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_user_qualified_id ON public.core_user USING btree ((('user_'::text || id)));


--
-- Name: idx_view_log_entity_qualified_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_view_log_entity_qualified_id ON public.view_log USING btree (((((model)::text || '_'::text) || model_id)));


--
-- Name: idx_view_log_model_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_view_log_model_id ON public.view_log USING btree (model_id);


--
-- Name: idx_view_log_timestamp; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_view_log_timestamp ON public.view_log USING btree ("timestamp");


--
-- Name: idx_view_log_user_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX idx_view_log_user_id ON public.view_log USING btree (user_id);


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
-- Name: ix_allocations_deadline_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_allocations_deadline_status ON public.allocations USING btree (locked_until, state);


--
-- Name: ix_allocations_locker_slot_state; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_allocations_locker_slot_state ON public.allocations USING btree (locker_id, slot, state);


--
-- Name: ix_allocations_order_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_allocations_order_id ON public.allocations USING btree (order_id);


--
-- Name: ix_allocations_released_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_allocations_released_at ON public.allocations USING btree (released_at);


--
-- Name: ix_allocations_state_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_allocations_state_created ON public.allocations USING btree (state, created_at);


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
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action, occurred_at);


--
-- Name: ix_audit_logs_actor_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_audit_logs_actor_time ON public.audit_logs USING btree (actor_id, occurred_at DESC);


--
-- Name: ix_audit_logs_new_state_gin; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_audit_logs_new_state_gin ON public.audit_logs USING gin (new_state);


--
-- Name: ix_audit_logs_old_state_gin; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_audit_logs_old_state_gin ON public.audit_logs USING gin (old_state);


--
-- Name: ix_audit_logs_target_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_audit_logs_target_time ON public.audit_logs USING btree (target_type, target_id, occurred_at DESC);


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
-- Name: ix_capability_locker_location_geom; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_capability_locker_location_geom ON public.capability_locker_location USING gist (geom);


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
-- Name: ix_capex_locker_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ix_capex_locker_id ON public.locker_capex_details USING btree (locker_id);


--
-- Name: ix_ccm_locker_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_ccm_locker_id ON public.cost_center_monthly USING btree (locker_id);


--
-- Name: ix_ccm_locker_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ix_ccm_locker_month ON public.cost_center_monthly USING btree (locker_id, month);


--
-- Name: ix_ccm_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_ccm_month ON public.cost_center_monthly USING btree (month DESC);


--
-- Name: ix_coa_country_jurisdiction; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_coa_country_jurisdiction ON public.chart_of_accounts USING btree (country_code, jurisdiction_code);


--
-- Name: ix_coa_type_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_coa_type_active ON public.chart_of_accounts USING btree (account_type, is_active);


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
-- Name: ix_customer_feedback_created_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_customer_feedback_created_at ON public.customer_feedback USING btree (created_at DESC);


--
-- Name: ix_customer_feedback_order_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_customer_feedback_order_id ON public.customer_feedback USING btree (order_id);


--
-- Name: ix_customer_feedback_sentiment; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_customer_feedback_sentiment ON public.customer_feedback USING btree (sentiment_label, created_at DESC);


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
-- Name: ix_domain_events_aggregate_id_type; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_domain_events_aggregate_id_type ON public.domain_events USING btree (aggregate_id, event_name, occurred_at DESC);


--
-- Name: ix_domain_events_status_created_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_domain_events_status_created_at ON public.domain_events USING btree (status, created_at);


--
-- Name: ix_door_state_machine; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_door_state_machine ON public.door_state USING btree (machine_id);


--
-- Name: ix_door_state_machine_state; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_door_state_machine_state ON public.door_state USING btree (machine_id, state);


--
-- Name: ix_eds_partner_locker_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_eds_partner_locker_month ON public.ellanlab_depreciation_schedule USING btree (partner_id, locker_id, depreciation_month);


--
-- Name: ix_eha_locker_partner; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_eha_locker_partner ON public.ellanlab_hardware_assets USING btree (locker_id, partner_id);


--
-- Name: ix_eha_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_eha_status ON public.ellanlab_hardware_assets USING btree (status);


--
-- Name: ix_emp_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_emp_month ON public.ellanlab_monthly_pnl USING btree (pnl_month);


--
-- Name: ix_emp_partner; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_emp_partner ON public.ellanlab_monthly_pnl USING btree (partner_id, pnl_month);


--
-- Name: ix_eoe_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_eoe_month ON public.ellanlab_opex_entries USING btree (expense_month);


--
-- Name: ix_eoe_partner_locker_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_eoe_partner_locker_month ON public.ellanlab_opex_entries USING btree (partner_id, locker_id, expense_month);


--
-- Name: ix_err_partner_locker_day; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_err_partner_locker_day ON public.ellanlab_revenue_recognition USING btree (partner_id, locker_id, recognition_date);


--
-- Name: ix_financial_ledger_created_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_financial_ledger_created_at ON public.financial_ledger USING btree (created_at);


--
-- Name: ix_financial_ledger_entry_type; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_financial_ledger_entry_type ON public.financial_ledger USING btree (entry_type);


--
-- Name: ix_financial_ledger_external_reference; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_financial_ledger_external_reference ON public.financial_ledger USING btree (external_reference);


--
-- Name: ix_fiscal_accounting_approvals_created_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_accounting_approvals_created_at ON public.fiscal_accounting_approvals USING btree (created_at DESC);


--
-- Name: ix_fiscal_accounting_approvals_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_accounting_approvals_status ON public.fiscal_accounting_approvals USING btree (status);


--
-- Name: ix_fiscal_cb_authority; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_cb_authority ON public.fiscal_authority_callbacks USING btree (authority);


--
-- Name: ix_fiscal_cb_invoice; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_cb_invoice ON public.fiscal_authority_callbacks USING btree (invoice_id);


--
-- Name: ix_fiscal_cb_received_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_cb_received_at ON public.fiscal_authority_callbacks USING btree (received_at);


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
-- Name: ix_fiscal_gap_invoice; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_gap_invoice ON public.fiscal_reconciliation_gaps USING btree (invoice_id);


--
-- Name: ix_fiscal_gap_order; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_gap_order ON public.fiscal_reconciliation_gaps USING btree (order_id);


--
-- Name: ix_fiscal_gap_status_last; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_gap_status_last ON public.fiscal_reconciliation_gaps USING btree (status, last_detected_at);


--
-- Name: ix_fiscal_gap_type; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_gap_type ON public.fiscal_reconciliation_gaps USING btree (gap_type);


--
-- Name: ix_fiscal_provider_health_checked_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_provider_health_checked_at ON public.fiscal_provider_health_status USING btree (checked_at);


--
-- Name: ix_fiscal_provider_health_country; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fiscal_provider_health_country ON public.fiscal_provider_health_status USING btree (country);


--
-- Name: ix_fkd_snapshot_day; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_fkd_snapshot_day ON public.financial_kpi_daily USING btree (snapshot_date);


--
-- Name: ix_idem_expires; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_idem_expires ON public.idempotency_keys USING btree (expires_at);


--
-- Name: ix_inbound_deadline; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_inbound_deadline ON public.inbound_deliveries USING btree (pickup_deadline_at) WHERE ((status)::text <> ALL ((ARRAY['PICKED_UP'::character varying, 'RETURNED'::character varying, 'EXPIRED'::character varying])::text[]));


--
-- Name: ix_inbound_deliveries_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_inbound_deliveries_created ON public.inbound_deliveries USING btree (created_at DESC);


--
-- Name: ix_inbound_deliveries_deadline; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_inbound_deliveries_deadline ON public.inbound_deliveries USING btree (pickup_deadline_at) WHERE ((status)::text <> ALL ((ARRAY['PICKED_UP'::character varying, 'RETURNED'::character varying])::text[]));


--
-- Name: ix_inbound_deliveries_locker_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_inbound_deliveries_locker_status ON public.inbound_deliveries USING btree (locker_id, status);


--
-- Name: ix_inbound_deliveries_tracking; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_inbound_deliveries_tracking ON public.inbound_deliveries USING btree (logistics_partner_id, tracking_code);


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
-- Name: ix_invoice_delivery_log_invoice; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_invoice_delivery_log_invoice ON public.invoice_delivery_log USING btree (invoice_id);


--
-- Name: ix_invoice_email_outbox_invoice; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_invoice_email_outbox_invoice ON public.invoice_email_outbox USING btree (invoice_id);


--
-- Name: ix_invoice_email_outbox_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_invoice_email_outbox_status ON public.invoice_email_outbox USING btree (status, next_retry_at);


--
-- Name: ix_invoice_fiscal_doc_subtype; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_invoice_fiscal_doc_subtype ON public.invoices USING btree (fiscal_doc_subtype);


--
-- Name: ix_invoice_locker_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_invoice_locker_id ON public.invoices USING btree (locker_id);


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
-- Name: ix_jel_account; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_jel_account ON public.journal_entry_lines USING btree (account_id);


--
-- Name: ix_jel_journal_entry; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_jel_journal_entry ON public.journal_entry_lines USING btree (journal_entry_id);


--
-- Name: ix_jel_partner_locker; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_jel_partner_locker ON public.journal_entry_lines USING btree (partner_id, locker_id);


--
-- Name: ix_journal_entries_reference; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_journal_entries_reference ON public.journal_entries USING btree (reference_source, reference_type, reference_id);


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
-- Name: ix_locker_telemetry_locker_occurred; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_locker_telemetry_locker_occurred ON public.locker_telemetry USING btree (locker_id, occurred_at DESC);


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
-- Name: ix_lockers_runtime_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_lockers_runtime_active ON public.runtime_lockers USING btree (active, runtime_enabled);


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
-- Name: ix_lsho_delivery_hour; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_lsho_delivery_hour ON public.locker_slot_hourly_occupancy USING btree (delivery_id, hour_bucket);


--
-- Name: ix_lsho_hour_bucket; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_lsho_hour_bucket ON public.locker_slot_hourly_occupancy USING btree (hour_bucket);


--
-- Name: ix_lsho_locker_hour; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_lsho_locker_hour ON public.locker_slot_hourly_occupancy USING btree (locker_id, hour_bucket);


--
-- Name: ix_lus_partner_locker; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_lus_partner_locker ON public.locker_utilization_snapshots USING btree (partner_id, locker_id);


--
-- Name: ix_lus_snapshot_date; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_lus_snapshot_date ON public.locker_utilization_snapshots USING btree (snapshot_date);


--
-- Name: ix_lus_status_date; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_lus_status_date ON public.locker_utilization_snapshots USING btree (divergence_status, snapshot_date);


--
-- Name: ix_marketplace_commissions_order; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_marketplace_commissions_order ON public.marketplace_commissions USING btree (order_id, status);


--
-- Name: ix_marketplace_sellers_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_marketplace_sellers_status ON public.marketplace_sellers USING btree (status);


--
-- Name: ix_ml_features_daily_date; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_ml_features_daily_date ON public.ml_features_daily USING btree (feature_date DESC);


--
-- Name: ix_ml_features_daily_locker_date; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_ml_features_daily_locker_date ON public.ml_features_daily USING btree (locker_id, feature_date DESC);


--
-- Name: ix_ml_predictions_locker_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_ml_predictions_locker_time ON public.ml_predictions_log USING btree (locker_id, predicted_at DESC);


--
-- Name: ix_ml_predictions_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_ml_predictions_time ON public.ml_predictions_log USING btree (predicted_at DESC);


--
-- Name: ix_mv_profitability_locker_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ix_mv_profitability_locker_month ON public.mv_locker_monthly_profitability USING btree (locker_id, month);


--
-- Name: ix_mv_profitability_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_mv_profitability_month ON public.mv_locker_monthly_profitability USING btree (month DESC);


--
-- Name: ix_mv_profitability_net_profit; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_mv_profitability_net_profit ON public.mv_locker_monthly_profitability USING btree (net_profit_cents DESC);


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
-- Name: ix_notification_logs_order_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_notification_logs_order_status ON public.notification_logs USING btree (order_id, status, next_attempt_at) WHERE ((status)::text = ANY ((ARRAY['QUEUED'::character varying, 'FAILED'::character varying])::text[]));


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
-- Name: ix_orders_channel; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_orders_channel ON public.orders USING btree (channel, status);


--
-- Name: ix_orders_channel_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_orders_channel_status ON public.orders USING btree (channel, status);


--
-- Name: ix_orders_created_at_partner_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_orders_created_at_partner_id ON public.orders USING btree (created_at DESC, partner_order_ref);


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
-- Name: ix_orders_status_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_orders_status_created ON public.orders USING btree (status, created_at DESC);


--
-- Name: ix_orders_status_created_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_orders_status_created_at ON public.orders USING btree (status, created_at DESC);


--
-- Name: ix_orders_status_picked_up; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_orders_status_picked_up ON public.orders USING btree (status, picked_up_at);


--
-- Name: ix_orders_tenant_partner; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_orders_tenant_partner ON public.orders USING btree (tenant_id, ecommerce_partner_id);


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
-- Name: ix_partner_payment_holds_created_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_partner_payment_holds_created_at ON public.partner_payment_holds USING btree (created_at);


--
-- Name: ix_partner_payment_holds_invoice; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_partner_payment_holds_invoice ON public.partner_payment_holds USING btree (invoice_id);


--
-- Name: ix_partner_payment_holds_partner_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_partner_payment_holds_partner_status ON public.partner_payment_holds USING btree (partner_id, status);


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
-- Name: ix_payment_transactions_gateway; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_payment_transactions_gateway ON public.payment_transactions USING btree (gateway, gateway_transaction_id);


--
-- Name: ix_payment_transactions_order_id; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_payment_transactions_order_id ON public.payment_transactions USING btree (order_id);


--
-- Name: ix_payment_transactions_reconciliation; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_payment_transactions_reconciliation ON public.payment_transactions USING btree (reconciliation_status) WHERE ((reconciliation_status)::text = 'PENDING'::text);


--
-- Name: ix_payment_transactions_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_payment_transactions_status ON public.payment_transactions USING btree (status, approved_at);


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
-- Name: ix_pbc_country_jurisdiction; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbc_country_jurisdiction ON public.partner_billing_cycles USING btree (country_code, jurisdiction_code);


--
-- Name: ix_pbc_partner_period; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbc_partner_period ON public.partner_billing_cycles USING btree (partner_id, period_start, period_end);


--
-- Name: ix_pbc_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbc_status ON public.partner_billing_cycles USING btree (status);


--
-- Name: ix_pbi_country_jurisdiction; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbi_country_jurisdiction ON public.partner_b2b_invoices USING btree (country_code, jurisdiction_code);


--
-- Name: ix_pbi_due_date; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbi_due_date ON public.partner_b2b_invoices USING btree (due_date);


--
-- Name: ix_pbi_partner_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbi_partner_status ON public.partner_b2b_invoices USING btree (partner_id, status);


--
-- Name: ix_pbli_country_jurisdiction; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbli_country_jurisdiction ON public.partner_billing_line_items USING btree (country_code, jurisdiction_code);


--
-- Name: ix_pbli_cycle; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbli_cycle ON public.partner_billing_line_items USING btree (cycle_id);


--
-- Name: ix_pbli_reference; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbli_reference ON public.partner_billing_line_items USING btree (reference_source, reference_type, reference_id);


--
-- Name: ix_pbp_country_jurisdiction; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbp_country_jurisdiction ON public.partner_billing_plans USING btree (country_code, jurisdiction_code);


--
-- Name: ix_pbp_partner_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbp_partner_active ON public.partner_billing_plans USING btree (partner_id, is_active);


--
-- Name: ix_pbp_validity; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pbp_validity ON public.partner_billing_plans USING btree (valid_from, valid_until);


--
-- Name: ix_pcn_country_jurisdiction; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pcn_country_jurisdiction ON public.partner_credit_notes USING btree (country_code, jurisdiction_code);


--
-- Name: ix_pcn_invoice; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pcn_invoice ON public.partner_credit_notes USING btree (original_invoice_id);


--
-- Name: ix_pcn_partner_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pcn_partner_status ON public.partner_credit_notes USING btree (partner_id, status);


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
-- Name: ix_pickups_status_expires; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_pickups_status_expires ON public.pickups USING btree (status, expires_at) WHERE (status = 'ACTIVE'::public.pickupstatus);


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
-- Name: ix_product_locker_compat_lookup; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_product_locker_compat_lookup ON public.product_locker_compatibility USING btree (product_id, locker_type_id, effective_from DESC);


--
-- Name: ix_products_cache_partner; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_products_cache_partner ON public.products_cache USING btree (partner_id);


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
-- Name: ix_runtime_sync_queue_locker; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_runtime_sync_queue_locker ON public.runtime_sync_queue USING btree (locker_id);


--
-- Name: ix_runtime_sync_queue_next_retry; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_runtime_sync_queue_next_retry ON public.runtime_sync_queue USING btree (next_retry_at) WHERE ((status)::text = 'PENDING'::text);


--
-- Name: ix_runtime_sync_queue_pending; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_runtime_sync_queue_pending ON public.runtime_sync_queue USING btree (created_at) WHERE ((status)::text = ANY ((ARRAY['PENDING'::character varying, 'PROCESSING'::character varying])::text[]));


--
-- Name: ix_runtime_sync_queue_status; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_runtime_sync_queue_status ON public.runtime_sync_queue USING btree (status);


--
-- Name: ix_seller_products_locker; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_seller_products_locker ON public.seller_products USING btree (locker_id, status);


--
-- Name: ix_seller_products_product; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_seller_products_product ON public.seller_products USING btree (product_id);


--
-- Name: ix_seller_products_seller; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_seller_products_seller ON public.seller_products USING btree (seller_id, status);


--
-- Name: ix_seller_reviews_seller; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_seller_reviews_seller ON public.seller_reviews USING btree (seller_id, rating);


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
-- Name: ix_tenant_fiscal_active; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_tenant_fiscal_active ON public.tenant_fiscal_config USING btree (is_active);


--
-- Name: ix_ui_error_events_created_at; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_ui_error_events_created_at ON public.ui_error_events USING btree (created_at);


--
-- Name: ix_ui_error_events_domain_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_ui_error_events_domain_created ON public.ui_error_events USING btree (domain, created_at);


--
-- Name: ix_ui_error_events_path_created; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX ix_ui_error_events_path_created ON public.ui_error_events USING btree (path, created_at);


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
-- Name: locker_telemetry_occurred_at_idx; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX locker_telemetry_occurred_at_idx ON public.locker_telemetry USING btree (occurred_at DESC);


--
-- Name: locker_telemetry_partitioned_occurred_at_idx; Type: INDEX; Schema: public; Owner: admin
--


CREATE INDEX locker_telemetry_partitioned_occurred_at_idx ON public.locker_telemetry_partitioned USING btree (occurred_at DESC);


--
-- Name: uq_locker_category; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX uq_locker_category ON public.product_locker_configs USING btree (locker_id, category);


--
-- Name: uq_ml_features_daily_mv_locker_date; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX uq_ml_features_daily_mv_locker_date ON public.ml_features_daily_mv USING btree (locker_id, feature_date);


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
-- Name: ux_eds_asset_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_eds_asset_month ON public.ellanlab_depreciation_schedule USING btree (asset_id, depreciation_month);


--
-- Name: ux_eds_dedupe_key; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_eds_dedupe_key ON public.ellanlab_depreciation_schedule USING btree (dedupe_key) WHERE (dedupe_key IS NOT NULL);


--
-- Name: ux_emp_partner_locker_month; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_emp_partner_locker_month ON public.ellanlab_monthly_pnl USING btree (partner_id, locker_id, pnl_month);


--
-- Name: ux_eoe_dedupe_key; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_eoe_dedupe_key ON public.ellanlab_opex_entries USING btree (dedupe_key) WHERE (dedupe_key IS NOT NULL);


--
-- Name: ux_err_dedupe_key_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_err_dedupe_key_time ON public.ellanlab_revenue_recognition USING btree (dedupe_key, recognition_date) WHERE (dedupe_key IS NOT NULL);


--
-- Name: ux_err_source_day; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_err_source_day ON public.ellanlab_revenue_recognition USING btree (source_type, source_id, recognition_date);


--
-- Name: ux_fkd_dedupe_key_time; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_fkd_dedupe_key_time ON public.financial_kpi_daily USING btree (dedupe_key, snapshot_date) WHERE (dedupe_key IS NOT NULL);


--
-- Name: ux_fkd_partner_locker_day; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_fkd_partner_locker_day ON public.financial_kpi_daily USING btree (partner_id, locker_id, snapshot_date);


--
-- Name: ux_idem_endpoint_key; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_idem_endpoint_key ON public.idempotency_keys USING btree (endpoint, idem_key);


--
-- Name: ux_inbound_tracking; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_inbound_tracking ON public.inbound_deliveries USING btree (logistics_partner_id, tracking_code);


--
-- Name: ux_journal_entries_dedupe_key; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_journal_entries_dedupe_key ON public.journal_entries USING btree (dedupe_key) WHERE (dedupe_key IS NOT NULL);


--
-- Name: ux_lus_dedupe_key; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_lus_dedupe_key ON public.locker_utilization_snapshots USING btree (dedupe_key) WHERE (dedupe_key IS NOT NULL);


--
-- Name: ux_lus_partner_locker_date; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_lus_partner_locker_date ON public.locker_utilization_snapshots USING btree (partner_id, locker_id, snapshot_date);


--
-- Name: ux_notification_logs_dedupe; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_notification_logs_dedupe ON public.notification_logs USING btree (dedupe_key);


--
-- Name: ux_partner_contacts_primary_type; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_partner_contacts_primary_type ON public.partner_contacts USING btree (partner_id, partner_type, contact_type) WHERE (is_primary = true);


--
-- Name: ux_pbc_dedupe_key; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_pbc_dedupe_key ON public.partner_billing_cycles USING btree (dedupe_key) WHERE (dedupe_key IS NOT NULL);


--
-- Name: ux_pbc_partner_global_period; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_pbc_partner_global_period ON public.partner_billing_cycles USING btree (partner_id, period_start, period_end) WHERE (locker_id IS NULL);


--
-- Name: ux_pbc_partner_locker_period; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_pbc_partner_locker_period ON public.partner_billing_cycles USING btree (partner_id, locker_id, period_start, period_end) WHERE (locker_id IS NOT NULL);


--
-- Name: ux_pbi_cycle; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_pbi_cycle ON public.partner_b2b_invoices USING btree (cycle_id);


--
-- Name: ux_pbi_dedupe_key; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_pbi_dedupe_key ON public.partner_b2b_invoices USING btree (dedupe_key) WHERE (dedupe_key IS NOT NULL);


--
-- Name: ux_pbli_dedupe_key; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_pbli_dedupe_key ON public.partner_billing_line_items USING btree (dedupe_key) WHERE (dedupe_key IS NOT NULL);


--
-- Name: ux_pcn_dedupe_key; Type: INDEX; Schema: public; Owner: admin
--


CREATE UNIQUE INDEX ux_pcn_dedupe_key ON public.partner_credit_notes USING btree (dedupe_key) WHERE (dedupe_key IS NOT NULL);


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
-- Name: orders_2025_06_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2025_06_pkey;


--
-- Name: orders_2025_07_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2025_07_pkey;


--
-- Name: orders_2025_08_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2025_08_pkey;


--
-- Name: orders_2025_09_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2025_09_pkey;


--
-- Name: orders_2025_10_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2025_10_pkey;


--
-- Name: orders_2025_11_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2025_11_pkey;


--
-- Name: orders_2025_12_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2025_12_pkey;


--
-- Name: orders_2026_01_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2026_01_pkey;


--
-- Name: orders_2026_02_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2026_02_pkey;


--
-- Name: orders_2026_03_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2026_03_pkey;


--
-- Name: orders_2026_04_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2026_04_pkey;


--
-- Name: orders_2026_05_pkey; Type: INDEX ATTACH; Schema: public; Owner: admin
--


ALTER INDEX public.orders_partitioned_pkey ATTACH PARTITION public.orders_2026_05_pkey;


