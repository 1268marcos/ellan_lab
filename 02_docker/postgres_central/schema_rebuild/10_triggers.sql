-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 10_triggers.sql
-- Execução: ver README.md e run_rebuild.sh

--
-- Name: cost_center_monthly trg_cost_center_monthly_updated; Type: TRIGGER; Schema: public; Owner: admin
--


CREATE TRIGGER trg_cost_center_monthly_updated BEFORE UPDATE ON public.cost_center_monthly FOR EACH ROW EXECUTE FUNCTION public.trg_cost_center_monthly_updated();


--
-- Name: customer_subscriptions trg_customer_subscriptions_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--


CREATE TRIGGER trg_customer_subscriptions_updated_at BEFORE UPDATE ON public.customer_subscriptions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: locker_capex_details trg_locker_capex_details_updated; Type: TRIGGER; Schema: public; Owner: admin
--


CREATE TRIGGER trg_locker_capex_details_updated BEFORE UPDATE ON public.locker_capex_details FOR EACH ROW EXECUTE FUNCTION public.trg_cost_center_monthly_updated();


--
-- Name: lockers trg_locker_cost_init; Type: TRIGGER; Schema: public; Owner: admin
--


CREATE TRIGGER trg_locker_cost_init AFTER INSERT OR UPDATE OF active ON public.lockers FOR EACH ROW EXECUTE FUNCTION public.fn_init_locker_costs();


--
-- Name: omnichannel_orders trg_omnichannel_orders_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--


CREATE TRIGGER trg_omnichannel_orders_updated_at BEFORE UPDATE ON public.omnichannel_orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: partner_stores trg_partner_stores_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--


CREATE TRIGGER trg_partner_stores_updated_at BEFORE UPDATE ON public.partner_stores FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: payment_transactions trg_payment_transactions_calc_fees; Type: TRIGGER; Schema: public; Owner: admin
--


CREATE TRIGGER trg_payment_transactions_calc_fees BEFORE INSERT OR UPDATE OF status ON public.payment_transactions FOR EACH ROW EXECUTE FUNCTION public.trg_payment_transactions_calc_fees();


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
-- Name: store_inventory trg_store_inventory_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--


CREATE TRIGGER trg_store_inventory_updated_at BEFORE UPDATE ON public.store_inventory FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: subscription_plans trg_subscription_plans_updated_at; Type: TRIGGER; Schema: public; Owner: admin
--


CREATE TRIGGER trg_subscription_plans_updated_at BEFORE UPDATE ON public.subscription_plans FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


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


