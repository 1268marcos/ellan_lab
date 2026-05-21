-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 12_comments_misc.sql
-- Execução: ver README.md e run_rebuild.sh

--
-- Name: EXTENSION timescaledb; Type: COMMENT; Schema: -; Owner: 
--


COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Community Edition)';


--
-- Name: EXTENSION pg_cron; Type: COMMENT; Schema: -; Owner: 
--


COMMENT ON EXTENSION pg_cron IS 'Job scheduler for PostgreSQL';


--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: admin
--


COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: EXTENSION address_standardizer; Type: COMMENT; Schema: -; Owner: 
--


COMMENT ON EXTENSION address_standardizer IS 'Used to parse an address into constituent elements. Generally used to support geocoding address normalization step.';


--
-- Name: EXTENSION citext; Type: COMMENT; Schema: -; Owner: 
--


COMMENT ON EXTENSION citext IS 'data type for case-insensitive character strings';


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--


COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--


COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--


COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--


COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Name: FUNCTION calculate_locker_gateway_fees(p_locker_id character varying, p_month date); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.calculate_locker_gateway_fees(p_locker_id character varying, p_month date) IS 'Calcula o total de gateway fees para um locker em um determinado mês';


--
-- Name: FUNCTION fn_allocate_fulfillment_inventory(p_order_id character varying, p_product_id character varying, p_quantity integer); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_allocate_fulfillment_inventory(p_order_id character varying, p_product_id character varying, p_quantity integer) IS 'Aloca inventário para um pedido no fulfillment center mais próximo';


--
-- Name: FUNCTION fn_calculate_dynamic_price(p_product_id character varying, p_locker_id character varying, p_base_price_cents integer); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_calculate_dynamic_price(p_product_id character varying, p_locker_id character varying, p_base_price_cents integer) IS 'Calcula preço baseado em demanda, estoque e horário';


--
-- Name: FUNCTION fn_calculate_seller_net(p_price_cents integer, p_commission_pct numeric); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_calculate_seller_net(p_price_cents integer, p_commission_pct numeric) IS 'Calcula splits do marketplace';


--
-- Name: FUNCTION fn_check_subscription_benefit(p_user_id character varying, p_benefit_type character varying); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_check_subscription_benefit(p_user_id character varying, p_benefit_type character varying) IS 'Verifica se usuário tem direito a benefício da assinatura';


--
-- Name: FUNCTION fn_find_nearest_store(p_product_id character varying, p_latitude numeric, p_longitude numeric, p_radius_km numeric); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_find_nearest_store(p_product_id character varying, p_latitude numeric, p_longitude numeric, p_radius_km numeric) IS 'Encontra lojas mais próximas com estoque do produto';


--
-- Name: FUNCTION fn_get_tenant_by_domain(p_domain character varying); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_get_tenant_by_domain(p_domain character varying) IS 'Resolve tenant a partir do domínio para white label';


--
-- Name: FUNCTION fn_locker_health(p_locker_id character varying); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_locker_health(p_locker_id character varying) IS 'Retorna score de saúde baseado em telemetria dos últimos 7 dias.';


--
-- Name: FUNCTION fn_locker_heartbeat(p_locker_id character varying); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_locker_heartbeat(p_locker_id character varying) IS 'Retorna timestamp do último heartbeat recebido do locker.';


--
-- Name: FUNCTION fn_locker_occupancy(p_locker_id character varying); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_locker_occupancy(p_locker_id character varying) IS 'Retorna ocupação atual de um locker específico.';


--
-- Name: FUNCTION fn_mrr(p_month date); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_mrr(p_month date) IS 'Calcula MRR baseado em ciclos de faturamento aprovados.';


--
-- Name: FUNCTION fn_predict_demand(p_locker_id character varying, p_forecast_date date); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_predict_demand(p_locker_id character varying, p_forecast_date date) IS 'Prevê demanda para um locker em uma data específica';


--
-- Name: FUNCTION fn_recommend_products(p_user_id character varying, p_locker_id character varying, p_limit integer); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_recommend_products(p_user_id character varying, p_locker_id character varying, p_limit integer) IS 'Retorna recomendações de produtos para um usuário/locker';


--
-- Name: FUNCTION fn_refresh_realtime_kpis(); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_refresh_realtime_kpis() IS 'Atualiza a materialized view de KPIs em tempo real';


--
-- Name: FUNCTION fn_renew_subscriptions(); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.fn_renew_subscriptions() IS 'Job diário para renovar assinaturas ativas';


--
-- Name: FUNCTION generate_locker_financial_report(p_locker_id character varying, p_start_month date, p_end_month date); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.generate_locker_financial_report(p_locker_id character varying, p_start_month date, p_end_month date) IS 'Gera relatório financeiro detalhado para lockers específicos ou todos';


--
-- Name: FUNCTION simulate_expansion_scenario_v2(p_target_city character varying, p_lockers_count integer, p_estimated_monthly_revenue_per_locker_cents integer, p_estimated_monthly_opex_per_locker_cents integer, p_installation_cost_per_locker_cents integer, p_hardware_cost_per_locker_cents integer, p_useful_life_months integer, p_expected_occupancy_rate_pct numeric); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.simulate_expansion_scenario_v2(p_target_city character varying, p_lockers_count integer, p_estimated_monthly_revenue_per_locker_cents integer, p_estimated_monthly_opex_per_locker_cents integer, p_installation_cost_per_locker_cents integer, p_hardware_cost_per_locker_cents integer, p_useful_life_months integer, p_expected_occupancy_rate_pct numeric) IS 'Simulação avançada de expansão com NPV, IRR e breakeven analysis';


--
-- Name: FUNCTION sp_refresh_financial_materialized_views(); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.sp_refresh_financial_materialized_views() IS 'Atualiza todas as materialized views financeiras do sistema';


--
-- Name: sp_refresh_locker_pnl_view(); Type: PROCEDURE; Schema: public; Owner: admin
--


CREATE PROCEDURE public.sp_refresh_locker_pnl_view()
    LANGUAGE plpgsql
    AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_locker_monthly_pnl;
  RAISE NOTICE 'MV mv_locker_monthly_pnl atualizada com sucesso.';
END;
$$;


ALTER PROCEDURE public.sp_refresh_locker_pnl_view() OWNER TO admin;

--
-- Name: sp_sync_locker_monthly_costs(date); Type: PROCEDURE; Schema: public; Owner: admin
--


CREATE PROCEDURE public.sp_sync_locker_monthly_costs(IN p_target_month date)
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- Atualização em lote (set-based) para performance e atomicidade
  WITH opex_agg AS (
    SELECT 
      locker_id,
      COALESCE(SUM(CASE WHEN category IN ('RENT', 'LOGISTICS', 'OTHER') THEN amount_cents ELSE 0 END), 0) AS operational_cents,
      COALESCE(SUM(CASE WHEN category IN ('MAINTENANCE', 'REPAIR', 'SUPPORT') THEN amount_cents ELSE 0 END), 0) AS maint_cents,
      COALESCE(SUM(CASE WHEN category IN ('ENERGY', 'CONNECTIVITY') THEN amount_cents ELSE 0 END), 0) AS utilities_cents
    FROM ellanlab_opex_entries
    WHERE expense_month = p_target_month 
      AND locker_id IS NOT NULL
    GROUP BY locker_id
  ),
  depr_agg AS (
    SELECT 
      ha.locker_id,
      COALESCE(SUM(ds.depreciation_amount_cents), 0) AS depr_cents
    FROM ellanlab_depreciation_schedule ds
    JOIN ellanlab_hardware_assets ha ON ds.asset_id = ha.id
    WHERE ds.depreciation_month = p_target_month 
      AND ha.locker_id IS NOT NULL
    GROUP BY ha.locker_id
  )
  UPDATE cost_centers cc
  SET 
    operational_cost_monthly_cents  = COALESCE(op.operational_cents, 0),
    maintenance_cost_annual_cents   = COALESCE(op.maint_cents, 0) * 12,   -- Projeção anual
    utilities_cost_monthly_cents    = COALESCE(op.utilities_cents, 0),
    depreciation_cost_annual_cents  = COALESCE(d.depr_cents, 0) * 12,     -- Projeção anual
    updated_at                      = now()
  FROM opex_agg op
  LEFT JOIN depr_agg d ON cc.locker_id = d.locker_id
  WHERE cc.locker_id = op.locker_id;
  
  RAISE NOTICE 'Custos atualizados para o mês: %', p_target_month;
END;
$$;


ALTER PROCEDURE public.sp_sync_locker_monthly_costs(IN p_target_month date) OWNER TO admin;

--
-- Name: FUNCTION sp_sync_monthly_costs_from_entries(p_target_month date); Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON FUNCTION public.sp_sync_monthly_costs_from_entries(p_target_month date) IS 'Sincroniza custos operacionais das tabelas de origem para cost_center_monthly';


--
-- Name: TABLE action; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.action IS 'An action is something you can do, such as run a readwrite query';


--
-- Name: COLUMN action.created_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.created_at IS 'The timestamp of when the action was created';


--
-- Name: COLUMN action.updated_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.updated_at IS 'The timestamp of when the action was updated';


--
-- Name: COLUMN action.type; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.type IS 'Type of action';


--
-- Name: COLUMN action.model_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.model_id IS 'The associated model';


--
-- Name: COLUMN action.name; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.name IS 'The name of the action';


--
-- Name: COLUMN action.description; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.description IS 'The description of the action';


--
-- Name: COLUMN action.parameters; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.parameters IS 'The saved parameters for this action';


--
-- Name: COLUMN action.parameter_mappings; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.parameter_mappings IS 'The saved parameter mappings for this action';


--
-- Name: COLUMN action.visualization_settings; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.visualization_settings IS 'The UI visualization_settings for this action';


--
-- Name: COLUMN action.public_uuid; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.public_uuid IS 'Unique UUID used to in publically-accessible links to this Action.';


--
-- Name: COLUMN action.made_public_by_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.made_public_by_id IS 'The ID of the User who first publically shared this Action.';


--
-- Name: COLUMN action.creator_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.creator_id IS 'The user who created the action';


--
-- Name: COLUMN action.archived; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.archived IS 'Whether or not the action has been archived';


--
-- Name: COLUMN action.entity_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.action.entity_id IS 'Random NanoID tag for unique identity.';


--
-- Name: TABLE api_key; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.api_key IS 'An API Key';


--
-- Name: COLUMN api_key.id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.api_key.id IS 'The ID of the API Key itself';


--
-- Name: COLUMN api_key.user_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.api_key.user_id IS 'The ID of the user who this API Key acts as';


--
-- Name: COLUMN api_key.key; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.api_key.key IS 'The hashed API key';


--
-- Name: COLUMN api_key.key_prefix; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.api_key.key_prefix IS 'The first 7 characters of the unhashed key';


--
-- Name: COLUMN api_key.creator_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.api_key.creator_id IS 'The ID of the user that created this API key';


--
-- Name: COLUMN api_key.created_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.api_key.created_at IS 'The timestamp when the key was created';


--
-- Name: COLUMN api_key.updated_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.api_key.updated_at IS 'The timestamp when the key was last updated';


--
-- Name: COLUMN api_key.name; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.api_key.name IS 'The user-defined name of the API key.';


--
-- Name: COLUMN api_key.updated_by_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.api_key.updated_by_id IS 'The ID of the user that last updated this API key';


--
-- Name: TABLE audit_log; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.audit_log IS 'Used to store application events for auditing use cases';


--
-- Name: COLUMN audit_log.topic; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.audit_log.topic IS 'The topic of a given audit event';


--
-- Name: COLUMN audit_log."timestamp"; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.audit_log."timestamp" IS 'The time an event was recorded';


--
-- Name: COLUMN audit_log.end_timestamp; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.audit_log.end_timestamp IS 'The time an event ended, if applicable';


--
-- Name: COLUMN audit_log.user_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.audit_log.user_id IS 'The user who performed an action or triggered an event';


--
-- Name: COLUMN audit_log.model; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.audit_log.model IS 'The name of the model this event applies to (e.g. Card, Dashboard), if applicable';


--
-- Name: COLUMN audit_log.model_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.audit_log.model_id IS 'The ID of the model this event applies to, if applicable';


--
-- Name: COLUMN audit_log.details; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.audit_log.details IS 'A JSON map with metadata about the event';


--
-- Name: TABLE capability_country; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.capability_country IS 'Países operacionais para o sistema de lockers';


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
-- Name: TABLE capability_province; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.capability_province IS 'Estados/Províncias com hierarquia ISO 3166-2 (ex: BR-SP)';


--
-- Name: COLUMN collection.created_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.collection.created_at IS 'Timestamp of when this Collection was created.';


--
-- Name: COLUMN collection.type; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.collection.type IS 'This is used to differentiate instance-analytics collections from all other collections.';


--
-- Name: TABLE connection_impersonations; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.connection_impersonations IS 'Table for holding connection impersonation policies';


--
-- Name: COLUMN connection_impersonations.db_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.connection_impersonations.db_id IS 'ID of the database this connection impersonation policy affects';


--
-- Name: COLUMN connection_impersonations.group_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.connection_impersonations.group_id IS 'ID of the permissions group this connection impersonation policy affects';


--
-- Name: COLUMN connection_impersonations.attribute; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.connection_impersonations.attribute IS 'User attribute associated with the database role to use for this connection impersonation policy';


--
-- Name: COLUMN core_user.type; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.core_user.type IS 'The type of user';


--
-- Name: TABLE cost_center_monthly; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.cost_center_monthly IS 'Custos operacionais mensais por locker para cálculo de rentabilidade';


--
-- Name: COLUMN cost_center_monthly.rent_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.cost_center_monthly.rent_cents IS 'Aluguel do espaço (R$ em centavos)';


--
-- Name: COLUMN cost_center_monthly.maintenance_preventive_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.cost_center_monthly.maintenance_preventive_cents IS 'Manutenção preventiva mensal (R$ 200-500 recomendado)';


--
-- Name: COLUMN cost_center_monthly.maintenance_corrective_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.cost_center_monthly.maintenance_corrective_cents IS 'Manutenção corretiva (buffer R$ 500-2000)';


--
-- Name: COLUMN cost_center_monthly.connectivity_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.cost_center_monthly.connectivity_cents IS 'Conectividade 4G (R$ 300 estimado)';


--
-- Name: COLUMN cost_center_monthly.energy_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.cost_center_monthly.energy_cents IS 'Energia elétrica (R$ 200-400)';


--
-- Name: COLUMN cost_center_monthly.insurance_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.cost_center_monthly.insurance_cents IS 'Seguro do equipamento (R$ 500 estimado)';


--
-- Name: COLUMN cost_center_monthly.payment_gateway_fee_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.cost_center_monthly.payment_gateway_fee_cents IS 'Taxa do gateway de pagamento (% do GMV)';


--
-- Name: COLUMN cost_center_monthly.depreciation_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.cost_center_monthly.depreciation_cents IS 'Depreciação mensal do ativo (CAPEX)';


--
-- Name: TABLE custom_domains; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.custom_domains IS 'Domínios customizados para white label';


--
-- Name: TABLE dashboard_tab; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.dashboard_tab IS 'Join table connecting dashboard to dashboardcards';


--
-- Name: COLUMN dashboard_tab.dashboard_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.dashboard_tab.dashboard_id IS 'The dashboard that a tab is on';


--
-- Name: COLUMN dashboard_tab.name; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.dashboard_tab.name IS 'Displayed name of the tab';


--
-- Name: COLUMN dashboard_tab."position"; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.dashboard_tab."position" IS 'Position of the tab with respect to others tabs in dashboard';


--
-- Name: COLUMN dashboard_tab.entity_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.dashboard_tab.entity_id IS 'Random NanoID tag for unique identity.';


--
-- Name: COLUMN dashboard_tab.created_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.dashboard_tab.created_at IS 'The timestamp at which the tab was created';


--
-- Name: COLUMN dashboard_tab.updated_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.dashboard_tab.updated_at IS 'The timestamp at which the tab was last updated';


--
-- Name: TABLE demand_forecast; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.demand_forecast IS 'Previsão de demanda por locker gerada por ML';


--
-- Name: TABLE dynamic_pricing_rules; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.dynamic_pricing_rules IS 'Regras para precificação dinâmica';


--
-- Name: TABLE fulfillment_centers; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.fulfillment_centers IS 'Centros de distribuição para fulfillment';


--
-- Name: TABLE fulfillment_inventory; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.fulfillment_inventory IS 'Estoque disponível nos centros de distribuição';


--
-- Name: TABLE fulfillment_orders; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.fulfillment_orders IS 'Ordens de fulfillment processadas nos centros';


--
-- Name: COLUMN sandboxes.permission_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.sandboxes.permission_id IS 'The ID of the corresponding permissions path for this sandbox';


--
-- Name: TABLE http_action; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.http_action IS 'An http api call type of action';


--
-- Name: COLUMN http_action.action_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.http_action.action_id IS 'The related action';


--
-- Name: COLUMN http_action.template; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.http_action.template IS 'A template that defines method,url,body,headers required to make an api call';


--
-- Name: COLUMN http_action.response_handle; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.http_action.response_handle IS 'A program to take an api response and transform to an appropriate response for emitters';


--
-- Name: COLUMN http_action.error_handle; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.http_action.error_handle IS 'A program to take an api response to determine if an error occurred';


--
-- Name: TABLE implicit_action; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.implicit_action IS 'An action with dynamic parameters based on the underlying model';


--
-- Name: COLUMN implicit_action.action_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.implicit_action.action_id IS 'The associated action';


--
-- Name: COLUMN implicit_action.kind; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.implicit_action.kind IS 'The kind of implicit action create/update/delete';


--
-- Name: TABLE locker_capex_details; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.locker_capex_details IS 'Detalhamento CAPEX por locker para investimento e ROI';


--
-- Name: COLUMN locker_capex_details.equipment_cost_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.locker_capex_details.equipment_cost_cents IS 'Custo do equipamento (hardware)';


--
-- Name: COLUMN locker_capex_details.installation_cost_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.locker_capex_details.installation_cost_cents IS 'Custo de instalação física';


--
-- Name: COLUMN locker_capex_details.connectivity_setup_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.locker_capex_details.connectivity_setup_cents IS 'Custo de setup de conectividade';


--
-- Name: COLUMN locker_capex_details.go_live_cost_cents; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.locker_capex_details.go_live_cost_cents IS 'Custos de testes, documentação e go-live';


--
-- Name: TABLE marketplace_commissions; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.marketplace_commissions IS 'Cálculo de comissões do marketplace';


--
-- Name: TABLE marketplace_sellers; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.marketplace_sellers IS 'Vendedores do marketplace aberto';


--
-- Name: COLUMN metabase_database.dbms_version; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.metabase_database.dbms_version IS 'A JSON object describing the flavor and version of the DBMS.';


--
-- Name: COLUMN metabase_database.is_audit; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.metabase_database.is_audit IS 'Only the app db, visible to admins via auditing should have this set true.';


--
-- Name: COLUMN metabase_field.json_unfolding; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.metabase_field.json_unfolding IS 'Enable/disable JSON unfolding for a field';


--
-- Name: COLUMN metabase_field.database_is_auto_increment; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.metabase_field.database_is_auto_increment IS 'Indicates this field is auto incremented';


--
-- Name: COLUMN metabase_field.database_indexed; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.metabase_field.database_indexed IS 'If the database supports indexing, this column indicate whether or not a field is indexed, or is the 1st column in a composite index';


--
-- Name: COLUMN metabase_field.database_partitioned; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.metabase_field.database_partitioned IS 'Whether the table is partitioned by this field';


--
-- Name: COLUMN metabase_fieldvalues.last_used_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.metabase_fieldvalues.last_used_at IS 'Timestamp of when these FieldValues were last used.';


--
-- Name: COLUMN metabase_table.is_upload; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.metabase_table.is_upload IS 'Was the table created from user-uploaded (i.e., from a CSV) data?';


--
-- Name: COLUMN metabase_table.database_require_filter; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.metabase_table.database_require_filter IS 'If true, the table requires a filter to be able to query it';


--
-- Name: TABLE model_index; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.model_index IS 'Used to keep track of which models have indexed columns.';


--
-- Name: COLUMN model_index.model_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index.model_id IS 'The ID of the indexed model.';


--
-- Name: COLUMN model_index.pk_ref; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index.pk_ref IS 'Serialized JSON of the primary key field ref.';


--
-- Name: COLUMN model_index.value_ref; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index.value_ref IS 'Serialized JSON of the label field ref.';


--
-- Name: COLUMN model_index.schedule; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index.schedule IS 'The cron schedule for when value syncing should happen.';


--
-- Name: COLUMN model_index.state; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index.state IS 'The status of the index: initializing, indexed, error, overflow.';


--
-- Name: COLUMN model_index.indexed_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index.indexed_at IS 'When the status changed';


--
-- Name: COLUMN model_index.error; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index.error IS 'The error message if the status is error.';


--
-- Name: COLUMN model_index.created_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index.created_at IS 'The timestamp of when these changes were made.';


--
-- Name: COLUMN model_index.creator_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index.creator_id IS 'ID of the user who created the event';


--
-- Name: TABLE model_index_value; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.model_index_value IS 'Used to keep track of the values indexed in a model';


--
-- Name: COLUMN model_index_value.model_index_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index_value.model_index_id IS 'The ID of the indexed model.';


--
-- Name: COLUMN model_index_value.model_pk; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index_value.model_pk IS 'The primary key of the indexed value';


--
-- Name: COLUMN model_index_value.name; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.model_index_value.name IS 'The label to display identifying the indexed value.';


--
-- Name: TABLE seller_products; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.seller_products IS 'Produtos oferecidos por cada seller em cada locker';


--
-- Name: MATERIALIZED VIEW mv_locker_monthly_profitability; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON MATERIALIZED VIEW public.mv_locker_monthly_profitability IS 'Rentabilidade mensal por locker - base para análise financeira e ROI';


--
-- Name: MATERIALIZED VIEW mv_realtime_kpis; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON MATERIALIZED VIEW public.mv_realtime_kpis IS 'KPIs em tempo real para dashboard executivo';


--
-- Name: TABLE omnichannel_orders; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.omnichannel_orders IS 'Ordens processadas via canal omnichannel';


--
-- Name: TABLE orders_partitioned; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.orders_partitioned IS 'Tabela orders particionada por mês para escalabilidade';


--
-- Name: TABLE parameter_card; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.parameter_card IS 'Join table connecting cards to entities (dashboards, other cards, etc.) that use the values generated by the card for filter values';


--
-- Name: COLUMN parameter_card.updated_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.parameter_card.updated_at IS 'most recent modification time';


--
-- Name: COLUMN parameter_card.created_at; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.parameter_card.created_at IS 'creation time';


--
-- Name: COLUMN parameter_card.card_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.parameter_card.card_id IS 'ID of the card generating the values';


--
-- Name: COLUMN parameter_card.parameterized_object_type; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.parameter_card.parameterized_object_type IS 'Type of the entity consuming the values (dashboard, card, etc.)';


--
-- Name: COLUMN parameter_card.parameterized_object_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.parameter_card.parameterized_object_id IS 'ID of the entity consuming the values';


--
-- Name: COLUMN parameter_card.parameter_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.parameter_card.parameter_id IS 'The parameter ID';


--
-- Name: TABLE partner_stores; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.partner_stores IS 'Lojas parceiras para click & collect';


--
-- Name: TABLE price_history; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.price_history IS 'Histórico de alterações de preço';


--
-- Name: TABLE product_recommendations; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.product_recommendations IS 'Recomendações de produtos personalizadas';


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
-- Name: TABLE query_action; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.query_action IS 'A readwrite query type of action';


--
-- Name: COLUMN query_action.action_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.query_action.action_id IS 'The related action';


--
-- Name: COLUMN query_action.database_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.query_action.database_id IS 'The associated database';


--
-- Name: COLUMN query_action.dataset_query; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.query_action.dataset_query IS 'The MBQL writeback query';


--
-- Name: COLUMN query_execution.action_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.query_execution.action_id IS 'The ID of the action associated with this query execution, if any.';


--
-- Name: COLUMN query_execution.is_sandboxed; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.query_execution.is_sandboxed IS 'Is query from a sandboxed user';


--
-- Name: COLUMN query_execution.cache_hash; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.query_execution.cache_hash IS 'Hash of normalized query, calculated in middleware.cache';


--
-- Name: TABLE recent_views; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.recent_views IS 'Used to store recently viewed objects for each user';


--
-- Name: COLUMN recent_views.user_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.recent_views.user_id IS 'The user associated with this view';


--
-- Name: COLUMN recent_views.model; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.recent_views.model IS 'The name of the model that was viewed';


--
-- Name: COLUMN recent_views.model_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.recent_views.model_id IS 'The ID of the model that was viewed';


--
-- Name: COLUMN recent_views."timestamp"; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.recent_views."timestamp" IS 'The time a view was recorded';


--
-- Name: COLUMN report_card.metabase_version; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.report_card.metabase_version IS 'Metabase version used to create the card.';


--
-- Name: COLUMN report_dashboard.auto_apply_filters; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.report_dashboard.auto_apply_filters IS 'Whether or not to auto-apply filters on a dashboard';


--
-- Name: COLUMN report_dashboardcard.action_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.report_dashboardcard.action_id IS 'The related action';


--
-- Name: COLUMN report_dashboardcard.dashboard_tab_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.report_dashboardcard.dashboard_tab_id IS 'The referenced tab id that dashcard is on, it''s nullable for dashboard with no tab';


--
-- Name: COLUMN revision.most_recent; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.revision.most_recent IS 'Whether a revision is the most recent one';


--
-- Name: COLUMN revision.metabase_version; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.revision.metabase_version IS 'Metabase version used to create the revision.';


--
-- Name: TABLE seller_reviews; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.seller_reviews IS 'Avaliações dos compradores sobre os sellers';


--
-- Name: TABLE store_inventory; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.store_inventory IS 'Estoque disponível nas lojas parceiras';


--
-- Name: TABLE subscription_benefits_usage; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.subscription_benefits_usage IS 'Controle de uso dos benefícios por assinatura';


--
-- Name: TABLE subscription_plans; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.subscription_plans IS 'Planos de assinatura disponíveis para clientes';


--
-- Name: TABLE table_privileges; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON TABLE public.table_privileges IS 'Table for user and role privileges by table';


--
-- Name: COLUMN table_privileges.table_id; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.table_privileges.table_id IS 'Table ID';


--
-- Name: COLUMN table_privileges.role; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.table_privileges.role IS 'Role name. NULL indicates the privileges are the current user''s';


--
-- Name: COLUMN table_privileges."select"; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.table_privileges."select" IS 'Privilege to select from the table';


--
-- Name: COLUMN table_privileges.update; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.table_privileges.update IS 'Privilege to update records in the table';


--
-- Name: COLUMN table_privileges.insert; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.table_privileges.insert IS 'Privilege to insert records into the table';


--
-- Name: COLUMN table_privileges.delete; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.table_privileges.delete IS 'Privilege to delete records from the table';


--
-- Name: COLUMN tenant_fiscal_config.brand_config; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.tenant_fiscal_config.brand_config IS 'Configurações de branding white label';


--
-- Name: VIEW v_locker_roi_analysis; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.v_locker_roi_analysis IS 'Análise de ROI e viabilidade financeira por locker - para decisões de expansão';


--
-- Name: VIEW v_financial_dashboard; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.v_financial_dashboard IS 'Dashboard financeiro executivo - KPIs consolidados e benchmarks';


--
-- Name: COLUMN view_log.has_access; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.view_log.has_access IS 'Whether the user who initiated the view had read access to the item being viewed.';


--
-- Name: COLUMN view_log.context; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON COLUMN public.view_log.context IS 'The context of the view, can be collection, question, or dashboard. Only for cards.';


--
-- Name: VIEW vw_ceo_occupancy; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_ceo_occupancy IS 'CEO Dashboard: Ocupação de cada locker para mapa de rede.';


--
-- Name: VIEW vw_ceo_revenue; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_ceo_revenue IS 'CEO Dashboard: Receita consolidada por mês/região/canal. Usar para KPIs globais.';


--
-- Name: VIEW vw_cfo_financial; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_cfo_financial IS 'CFO Dashboard: Métricas financeiras consolidadas (Receita, Wallet, Disputas). NOTA: Sem custos ainda.';


--
-- Name: VIEW vw_coo_operations; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_coo_operations IS 'COO Dashboard: Métricas operacionais diárias consolidadas.';


--
-- Name: VIEW vw_depot_inventory; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_depot_inventory IS 'Depot Manager: Encomendas com priorização por deadline.';


--
-- Name: VIEW vw_fulfillment_metrics; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_fulfillment_metrics IS 'Métricas de performance do fulfillment';


--
-- Name: VIEW vw_maintenance_alerts; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_maintenance_alerts IS 'Dashboard Técnico Manutenção: Alertas de equipamentos com priorização.';


--
-- Name: VIEW vw_ml_dashboard; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_ml_dashboard IS 'Dashboard de performance dos modelos de ML';


--
-- Name: VIEW vw_ml_features_complete; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_ml_features_complete IS 'Features completas para treinamento de modelos ML';


--
-- Name: VIEW vw_noc_alerts; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_noc_alerts IS 'NOC Dashboard: Alertas unificados (SLA, Offline, Risco) ordenados por prioridade.';


--
-- Name: VIEW vw_omnichannel_metrics; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_omnichannel_metrics IS 'Métricas de performance omnichannel';


--
-- Name: VIEW vw_proactive_alerts; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_proactive_alerts IS 'Alertas proativos para equipe de operações';


--
-- Name: VIEW vw_realtime_executive; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_realtime_executive IS 'Dashboard executivo em tempo real';


--
-- Name: VIEW vw_subscription_metrics; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_subscription_metrics IS 'Métricas consolidadas de assinaturas';


--
-- Name: VIEW vw_subscription_summary; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_subscription_summary IS 'Resumo rápido de assinaturas';


--
-- Name: VIEW vw_support_active_tickets; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_support_active_tickets IS 'Suporte N1 Dashboard: Tickets ativos prioritários para triagem.';


--
-- Name: VIEW vw_trending_metrics; Type: COMMENT; Schema: public; Owner: admin
--


COMMENT ON VIEW public.vw_trending_metrics IS 'Métricas de tendência (comparação semana a semana)';


--
-- Name: product_bundles ck_pb_amount_non_negative_v2; Type: CHECK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE public.product_bundles
    ADD CONSTRAINT ck_pb_amount_non_negative_v2 CHECK ((amount_cents >= 0)) NOT VALID;


--
-- Name: product_bundles ck_pb_valid_window_v2; Type: CHECK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE public.product_bundles
    ADD CONSTRAINT ck_pb_valid_window_v2 CHECK (((valid_until IS NULL) OR (valid_until >= valid_from))) NOT VALID;


--
-- Name: product_fiscal_config ck_pfc_tax_rate_pct_range_v2; Type: CHECK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE public.product_fiscal_config
    ADD CONSTRAINT ck_pfc_tax_rate_pct_range_v2 CHECK (((tax_rate_pct IS NULL) OR ((tax_rate_pct >= (0)::numeric) AND (tax_rate_pct <= (100)::numeric)))) NOT VALID;


--
-- Name: promotions ck_promotions_amounts_non_negative; Type: CHECK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE public.promotions
    ADD CONSTRAINT ck_promotions_amounts_non_negative CHECK (((min_order_cents >= 0) AND (uses_count >= 0) AND ((max_uses IS NULL) OR (max_uses >= 0)) AND ((max_discount_cents IS NULL) OR (max_discount_cents >= 0)))) NOT VALID;


--
-- Name: promotions ck_promotions_valid_window_v2; Type: CHECK CONSTRAINT; Schema: public; Owner: admin
--


ALTER TABLE public.promotions
    ADD CONSTRAINT ck_promotions_valid_window_v2 CHECK (((valid_until IS NULL) OR (valid_until >= valid_from))) NOT VALID;


