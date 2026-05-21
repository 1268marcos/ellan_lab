-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: 05_functions.sql
-- Execução: ver README.md e run_rebuild.sh

--
-- Name: calculate_gateway_fee(integer, character varying, character varying, integer); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.calculate_gateway_fee(p_amount_cents integer, p_payment_method character varying, p_card_brand character varying, p_installments integer DEFAULT 1) RETURNS integer
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    v_fee_pct DECIMAL(5,4);
    v_fee_cents INTEGER;
    v_installment_fee_cents INTEGER := 0;
BEGIN
    -- Taxa percentual base (modelo simplificado)
    v_fee_pct := CASE 
        WHEN p_payment_method IN ('creditCard', 'CARTAO_CREDITO') THEN 
            CASE 
                WHEN p_card_brand IN ('amex', 'elite') THEN 0.045 -- 4.5% para Amex
                ELSE 0.039  -- 3.9% para outras bandeiras
            END
        WHEN p_payment_method IN ('debitCard', 'CARTAO_DEBITO') THEN 0.025  -- 2.5%
        WHEN p_payment_method = 'pix' THEN 0.008  -- 0.8%
        WHEN p_payment_method = 'boleto' THEN 0.025  -- 2.5%
        WHEN p_payment_method IN ('apple_pay', 'google_pay') THEN 0.035  -- 3.5%
        ELSE 0.03  -- 3% padrão
    END;
    
    -- Taxa por parcela (ex: 0.5% por parcela além da 1ª)
    IF p_installments > 1 THEN
        v_installment_fee_cents := ROUND(p_amount_cents * 0.005 * (p_installments - 1));
    END IF;
    
    v_fee_cents := ROUND(p_amount_cents * v_fee_pct) + v_installment_fee_cents;
    
    RETURN LEAST(v_fee_cents, p_amount_cents * 0.1); -- Limite de 10% do valor
END;
$$;


ALTER FUNCTION public.calculate_gateway_fee(p_amount_cents integer, p_payment_method character varying, p_card_brand character varying, p_installments integer) OWNER TO admin;

--
-- Name: calculate_locker_gateway_fees(character varying, date); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.calculate_locker_gateway_fees(p_locker_id character varying, p_month date DEFAULT (date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))::date) RETURNS bigint
    LANGUAGE plpgsql STABLE
    AS $$
DECLARE
    v_total_fee_cents BIGINT;
BEGIN
    -- Calcula o total de gateway fees para o locker no mês
    SELECT COALESCE(SUM(pt.gateway_fee_cents), 0)
    INTO v_total_fee_cents
    FROM public.payment_transactions pt
    JOIN public.orders o ON o.id = pt.order_id
    JOIN public.allocations a ON a.order_id = o.id
    WHERE a.locker_id = p_locker_id
        AND pt.status = 'APPROVED'
        AND DATE_TRUNC('month', pt.approved_at)::DATE = p_month;
    
    RETURN v_total_fee_cents;
END;
$$;


ALTER FUNCTION public.calculate_locker_gateway_fees(p_locker_id character varying, p_month date) OWNER TO admin;

--
-- Name: create_future_order_partitions(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.create_future_order_partitions() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    future_months INT := 3;  -- Criar 3 meses à frente
    base_date DATE;
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    FOR i IN 1..future_months LOOP
        base_date := DATE_TRUNC('month', CURRENT_DATE + (i || ' months')::INTERVAL);
        partition_name := 'orders_' || TO_CHAR(base_date, 'YYYY_MM');
        start_date := base_date;
        end_date := base_date + INTERVAL '1 month';
        
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF orders_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END LOOP;
END;
$$;


ALTER FUNCTION public.create_future_order_partitions() OWNER TO admin;

--
-- Name: find_lockers_by_distance(numeric, numeric, numeric, integer, boolean); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.find_lockers_by_distance(ref_lat numeric, ref_lon numeric, radius_meters numeric, max_results integer DEFAULT 50, ble_only boolean DEFAULT false) RETURNS TABLE(locker_id integer, external_id character varying, address_street character varying, city_name character varying, district character varying, postal_code character varying, distance_meters numeric, is_24h boolean, has_ble boolean, supports_ble boolean)
    LANGUAGE plpgsql STABLE
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
        COALESCE((l.metadata_json->>'is_24h')::BOOLEAN, false) AS is_24h,
        COALESCE(locker.has_ble, false) AS has_ble,
        COALESCE(rlf.supports_ble, false) AS supports_ble
    FROM public.capability_locker_location l
    LEFT JOIN public.lockers locker ON locker.external_id = l.external_id
    LEFT JOIN public.runtime_locker_features rlf ON rlf.locker_id = locker.id
    WHERE l.is_active = true
      AND l.geom IS NOT NULL
      AND (NOT ble_only OR COALESCE(locker.has_ble, false) = true)
      AND ST_DWithin(
            l.geom::geography,
            ST_SetSRID(ST_MakePoint(ref_lon, ref_lat), 4326)::geography,
            radius_meters
          )
    ORDER BY l.geom <-> ST_SetSRID(ST_MakePoint(ref_lon, ref_lat), 4326)
    LIMIT max_results;
END;
$$;


ALTER FUNCTION public.find_lockers_by_distance(ref_lat numeric, ref_lon numeric, radius_meters numeric, max_results integer, ble_only boolean) OWNER TO admin;

--
-- Name: fn_allocate_fulfillment_inventory(character varying, character varying, integer); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_allocate_fulfillment_inventory(p_order_id character varying, p_product_id character varying, p_quantity integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_center_id VARCHAR;
    v_current_qty INTEGER;
BEGIN
    -- Encontrar centro mais próximo (baseado no locker do pedido)
    SELECT fc.id INTO v_center_id
    FROM fulfillment_centers fc
    CROSS JOIN orders o
    CROSS JOIN lockers l
    WHERE o.id = p_order_id
        AND l.id = o.locker_id
        AND fc.active = true
    ORDER BY fc.latitude <-> l.latitude, fc.longitude <-> l.longitude
    LIMIT 1;
    
    IF v_center_id IS NULL THEN
        RETURN false;
    END IF;
    
    -- Reservar estoque
    UPDATE fulfillment_inventory
    SET quantity_reserved = quantity_reserved + p_quantity,
        updated_at = now()
    WHERE fulfillment_center_id = v_center_id
        AND product_id = p_product_id
        AND quantity_available >= p_quantity;
    
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    
    -- Criar ordem de fulfillment
    INSERT INTO fulfillment_orders (order_id, fulfillment_center_id, status)
    VALUES (p_order_id, v_center_id, 'PENDING');
    
    RETURN true;
END $$;


ALTER FUNCTION public.fn_allocate_fulfillment_inventory(p_order_id character varying, p_product_id character varying, p_quantity integer) OWNER TO admin;

--
-- Name: fn_calculate_dynamic_price(character varying, character varying, integer); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_calculate_dynamic_price(p_product_id character varying, p_locker_id character varying, p_base_price_cents integer) RETURNS integer
    LANGUAGE plpgsql STABLE
    AS $$
DECLARE
    v_final_price INTEGER;
    v_demand_factor DECIMAL;
    v_inventory_factor DECIMAL;
    v_time_factor DECIMAL;
    v_demand_7d INTEGER;
    v_inventory_count INTEGER;
    v_hour INTEGER;
BEGIN
    -- Demanda últimos 7 dias
    SELECT COUNT(*) INTO v_demand_7d
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    WHERE oi.sku_id = p_product_id
        AND o.created_at >= CURRENT_DATE - 7
        AND o.status = 'PICKED_UP';
    
    -- Inventário atual
    SELECT quantity_available INTO v_inventory_count
    FROM product_inventory
    WHERE product_id = p_product_id AND locker_id = p_locker_id;
    
    -- Fator de demanda
    v_demand_factor := CASE 
        WHEN v_demand_7d > 100 THEN 1.15
        WHEN v_demand_7d > 50 THEN 1.10
        WHEN v_demand_7d > 20 THEN 1.05
        ELSE 1.00
    END;
    
    -- Fator de inventário (quanto menor o estoque, maior o preço)
    v_inventory_factor := CASE 
        WHEN v_inventory_count < 5 THEN 1.20
        WHEN v_inventory_count < 10 THEN 1.10
        WHEN v_inventory_count < 20 THEN 1.05
        ELSE 1.00
    END;
    
    -- Fator horário (horário de pico)
    v_hour := EXTRACT(HOUR FROM CURRENT_TIME);
    v_time_factor := CASE 
        WHEN v_hour BETWEEN 17 AND 20 THEN 1.08  -- Horário de pico
        WHEN v_hour BETWEEN 12 AND 14 THEN 1.05  -- Almoço
        ELSE 1.00
    END;
    
    -- Preço final
    v_final_price := ROUND(p_base_price_cents * v_demand_factor * v_inventory_factor * v_time_factor);
    
    -- Aplicar limites
    v_final_price := GREATEST(v_final_price, p_base_price_cents * 0.7); -- -30% mínimo
    v_final_price := LEAST(v_final_price, p_base_price_cents * 1.5);    -- +50% máximo
    
    RETURN v_final_price;
END $$;


ALTER FUNCTION public.fn_calculate_dynamic_price(p_product_id character varying, p_locker_id character varying, p_base_price_cents integer) OWNER TO admin;

--
-- Name: fn_calculate_seller_net(integer, numeric); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_calculate_seller_net(p_price_cents integer, p_commission_pct numeric) RETURNS TABLE(commission_cents integer, ellan_fee_cents integer, gateway_fee_cents integer, net_cents integer)
    LANGUAGE sql IMMUTABLE
    AS $$
    SELECT 
        ROUND(p_price_cents * p_commission_pct / 100)::INTEGER,
        ROUND(p_price_cents * 2.99 / 100)::INTEGER, -- Ellan platform fee
        ROUND(p_price_cents * 2.5 / 100)::INTEGER,  -- Gateway fee estimado
        p_price_cents - ROUND(p_price_cents * (p_commission_pct + 2.99 + 2.5) / 100)::INTEGER
$$;


ALTER FUNCTION public.fn_calculate_seller_net(p_price_cents integer, p_commission_pct numeric) OWNER TO admin;

--
-- Name: fn_check_subscription_benefit(character varying, character varying); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_check_subscription_benefit(p_user_id character varying, p_benefit_type character varying) RETURNS boolean
    LANGUAGE plpgsql STABLE
    AS $$
DECLARE
    v_has_benefit BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM customer_subscriptions cs
        WHERE cs.user_id = p_user_id
            AND cs.status = 'ACTIVE'
            AND cs.current_period_start <= now()
            AND cs.current_period_end >= now()
            AND CASE p_benefit_type
                WHEN 'FREE_SHIPPING' THEN cs.free_shipping
                WHEN 'PRIORITY_SHELF' THEN cs.priority_shelf
                WHEN 'EXCLUSIVE_DEAL' THEN cs.exclusive_deals
                ELSE false
            END = true
    ) INTO v_has_benefit;
    
    RETURN COALESCE(v_has_benefit, false);
END $$;


ALTER FUNCTION public.fn_check_subscription_benefit(p_user_id character varying, p_benefit_type character varying) OWNER TO admin;

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
-- Name: fn_find_nearest_store(character varying, numeric, numeric, numeric); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_find_nearest_store(p_product_id character varying, p_latitude numeric, p_longitude numeric, p_radius_km numeric DEFAULT 10) RETURNS TABLE(store_id character varying, store_name character varying, distance_km numeric, quantity integer, price_cents integer)
    LANGUAGE sql STABLE
    AS $$
    SELECT 
        ps.id,
        ps.name,
        ROUND(CAST(ST_Distance(
            ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography,
            ST_SetSRID(ST_MakePoint(ps.longitude, ps.latitude), 4326)::geography
        ) / 1000 AS NUMERIC), 2) AS distance_km,
        si.quantity,
        COALESCE(si.price_cents, p.amount_cents) AS price_cents
    FROM partner_stores ps
    JOIN store_inventory si ON si.store_id = ps.id AND si.product_id = p_product_id
    JOIN products p ON p.id = p_product_id
    WHERE ps.active = true
        AND si.quantity > 0
        AND ST_DWithin(
            ST_SetSRID(ST_MakePoint(ps.longitude, ps.latitude), 4326)::geography,
            ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography,
            p_radius_km * 1000
        )
    ORDER BY distance_km
    LIMIT 5;
$$;


ALTER FUNCTION public.fn_find_nearest_store(p_product_id character varying, p_latitude numeric, p_longitude numeric, p_radius_km numeric) OWNER TO admin;

--
-- Name: fn_get_tenant_by_domain(character varying); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_get_tenant_by_domain(p_domain character varying) RETURNS character varying
    LANGUAGE sql STABLE
    AS $$
    SELECT tenant_id
    FROM custom_domains
    WHERE domain = p_domain AND verified = true
    UNION ALL
    SELECT 'default' WHERE NOT EXISTS (SELECT 1 FROM custom_domains WHERE domain = p_domain)
    LIMIT 1
$$;


ALTER FUNCTION public.fn_get_tenant_by_domain(p_domain character varying) OWNER TO admin;

--
-- Name: fn_init_locker_costs(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_init_locker_costs() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- Dispara apenas na inserção com active=true ou na mudança de false -> true
  IF (TG_OP = 'INSERT' AND NEW.active = true) OR 
     (TG_OP = 'UPDATE' AND OLD.active = false AND NEW.active = true) THEN
    
    -- Evita duplicatas em caso de re-execução ou atualização acidental
    IF NOT EXISTS (SELECT 1 FROM cost_centers WHERE locker_id = NEW.id) THEN
      INSERT INTO cost_centers (
        id, locker_id, operational_cost_monthly_cents, 
        maintenance_cost_annual_cents, depreciation_cost_annual_cents, 
        utilities_cost_monthly_cents, created_at, updated_at
      ) VALUES (
        gen_random_uuid(),
        NEW.id,
        0, 0, 0, 0, 
        now(), now()
      );
    END IF;
  END IF;
  
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.fn_init_locker_costs() OWNER TO admin;

--
-- Name: fn_locker_health(character varying); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_locker_health(p_locker_id character varying) RETURNS TABLE(health_score numeric, status character varying, last_telemetry_at timestamp without time zone)
    LANGUAGE sql STABLE
    AS $$
    SELECT 
        100 - COALESCE(SUM(CASE WHEN event_type IN ('DOOR_FAILURE', 'SIGNAL_LOST') THEN 10 ELSE 0 END), 0),
        CASE 
            WHEN 100 - COALESCE(SUM(CASE WHEN event_type IN ('DOOR_FAILURE', 'SIGNAL_LOST') THEN 10 ELSE 0 END), 0) >= 80 THEN 'SAUDAVEL'
            WHEN 100 - COALESCE(SUM(CASE WHEN event_type IN ('DOOR_FAILURE', 'SIGNAL_LOST') THEN 10 ELSE 0 END), 0) >= 50 THEN 'ATENCAO'
            ELSE 'CRITICO'
        END,
        MAX(occurred_at)
    FROM locker_telemetry
    WHERE locker_id = p_locker_id AND occurred_at >= CURRENT_DATE - INTERVAL '7 days'
$$;


ALTER FUNCTION public.fn_locker_health(p_locker_id character varying) OWNER TO admin;

--
-- Name: fn_locker_heartbeat(character varying); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_locker_heartbeat(p_locker_id character varying) RETURNS timestamp without time zone
    LANGUAGE sql STABLE
    AS $$
    SELECT MAX(occurred_at)
    FROM locker_telemetry
    WHERE locker_id = p_locker_id AND event_type = 'HEARTBEAT'
$$;


ALTER FUNCTION public.fn_locker_heartbeat(p_locker_id character varying) OWNER TO admin;

--
-- Name: fn_locker_occupancy(character varying); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_locker_occupancy(p_locker_id character varying) RETURNS TABLE(total_slots integer, occupied_slots integer, available_slots integer, occupancy_pct numeric)
    LANGUAGE sql STABLE
    AS $$
    SELECT 
        COUNT(*)::INTEGER,
        COUNT(CASE WHEN status = 'OCCUPIED' THEN 1 END)::INTEGER,
        COUNT(CASE WHEN status = 'AVAILABLE' THEN 1 END)::INTEGER,
        ROUND(COUNT(CASE WHEN status = 'OCCUPIED' THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2)
    FROM locker_slots
    WHERE locker_id = p_locker_id
$$;


ALTER FUNCTION public.fn_locker_occupancy(p_locker_id character varying) OWNER TO admin;

--
-- Name: fn_mrr(date); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_mrr(p_month date DEFAULT (date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))::date) RETURNS numeric
    LANGUAGE sql STABLE
    AS $$
    SELECT COALESCE(SUM(total_cents) / 100, 0)::NUMERIC
    FROM partner_billing_line_items
    WHERE line_type = 'BASE_FEE'
        AND period_from <= p_month
        AND period_to >= p_month
$$;


ALTER FUNCTION public.fn_mrr(p_month date) OWNER TO admin;

--
-- Name: fn_predict_demand(character varying, date); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_predict_demand(p_locker_id character varying, p_forecast_date date) RETURNS integer
    LANGUAGE plpgsql STABLE
    AS $$
DECLARE
    v_prediction INTEGER;
BEGIN
    -- Usar previsão existente ou calcular baseada em histórico
    SELECT predicted_orders INTO v_prediction
    FROM demand_forecast
    WHERE locker_id = p_locker_id AND forecast_date = p_forecast_date;
    
    IF v_prediction IS NOT NULL THEN
        RETURN v_prediction;
    END IF;
    
    -- Fallback: média dos últimos 30 dias
    SELECT COALESCE(ROUND(AVG(daily_orders)), 10) INTO v_prediction
    FROM (
        SELECT COUNT(*) AS daily_orders
        FROM orders o
        WHERE o.locker_id = p_locker_id
            AND o.created_at >= p_forecast_date - INTERVAL '30 days'
            AND o.created_at < p_forecast_date
        GROUP BY DATE_TRUNC('day', o.created_at)
    ) daily;
    
    RETURN COALESCE(v_prediction, 10);
END $$;


ALTER FUNCTION public.fn_predict_demand(p_locker_id character varying, p_forecast_date date) OWNER TO admin;

--
-- Name: fn_recommend_products(character varying, character varying, integer); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_recommend_products(p_user_id character varying, p_locker_id character varying, p_limit integer DEFAULT 10) RETURNS TABLE(product_id character varying, product_name character varying, score numeric, price_cents integer)
    LANGUAGE sql STABLE
    AS $$
    SELECT 
        pr.product_id,
        p.name AS product_name,
        pr.score,
        p.amount_cents AS price_cents
    FROM product_recommendations pr
    JOIN products p ON p.id = pr.product_id AND p.is_active = true
    WHERE (pr.user_id = p_user_id OR pr.user_id IS NULL)
        AND (pr.locker_id = p_locker_id OR pr.locker_id IS NULL)
        AND pr.expires_at > now()
        AND p.is_active = true
    ORDER BY pr.score DESC
    LIMIT p_limit;
$$;


ALTER FUNCTION public.fn_recommend_products(p_user_id character varying, p_locker_id character varying, p_limit integer) OWNER TO admin;

--
-- Name: fn_refresh_realtime_kpis(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_refresh_realtime_kpis() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_realtime_kpis;
    RAISE NOTICE '✅ mv_realtime_kpis atualizado em %', now();
END $$;


ALTER FUNCTION public.fn_refresh_realtime_kpis() OWNER TO admin;

--
-- Name: fn_renew_subscriptions(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.fn_renew_subscriptions() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_renewed_count INTEGER := 0;
    v_subscription RECORD;
    v_plan_fee INTEGER;
BEGIN
    FOR v_subscription IN
        SELECT cs.*
        FROM customer_subscriptions cs
        WHERE cs.status = 'ACTIVE'
            AND cs.cancel_at_period_end = false
            AND cs.current_period_end < now()
    LOOP
        -- Determinar fee baseado no plan_type
        v_plan_fee := CASE v_subscription.plan_type
            WHEN 'BASIC' THEN 0
            WHEN 'PREMIUM' THEN 2990
            WHEN 'PRO' THEN 4990
            WHEN 'ENTERPRISE' THEN 9990
            ELSE 2990
        END;
        
        -- Atualizar período
        UPDATE customer_subscriptions
        SET 
            current_period_start = current_period_end,
            current_period_end = CASE 
                WHEN billing_cycle = 'MONTHLY' THEN current_period_end + INTERVAL '1 month'
                ELSE current_period_end + INTERVAL '1 year'
            END,
            next_billing_at = CASE 
                WHEN billing_cycle = 'MONTHLY' THEN next_billing_at + INTERVAL '1 month'
                ELSE next_billing_at + INTERVAL '1 year'
            END,
            updated_at = now()
        WHERE id = v_subscription.id;
        
        v_renewed_count := v_renewed_count + 1;
        
        -- Registrar renovação no financial_ledger
        INSERT INTO financial_ledger (order_id, entry_type, amount_cents, currency, metadata)
        VALUES (
            NULL,
            'SUBSCRIPTION_RENEWAL',
            v_plan_fee,
            'BRL',
            jsonb_build_object('subscription_id', v_subscription.id, 'user_id', v_subscription.user_id, 'plan_type', v_subscription.plan_type)
        );
    END LOOP;
    
    RETURN v_renewed_count;
END $$;


ALTER FUNCTION public.fn_renew_subscriptions() OWNER TO admin;

--
-- Name: generate_locker_financial_report(character varying, date, date); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.generate_locker_financial_report(p_locker_id character varying DEFAULT NULL::character varying, p_start_month date DEFAULT NULL::date, p_end_month date DEFAULT NULL::date) RETURNS TABLE(locker_id character varying, locker_name character varying, city character varying, month date, revenue_brl numeric, costs_brl numeric, profit_brl numeric, margin_pct numeric, pickups integer, payback_months numeric, roi_annual_pct numeric, viability character varying)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mp.locker_id,
        l.display_name AS locker_name,
        l.city,
        mp.month,
        mp.sales_revenue_cents / 100.0 AS revenue_brl,
        mp.total_costs_cents / 100.0 AS costs_brl,
        mp.net_profit_cents / 100.0 AS profit_brl,
        mp.net_margin_pct AS margin_pct,
        mp.total_pickups::INTEGER,
        ra.payback_months,
        ra.annual_roi_pct,
        ra.viability_classification AS viability
    FROM public.mv_locker_monthly_profitability mp
    JOIN public.lockers l ON l.id = mp.locker_id
    LEFT JOIN public.v_locker_roi_analysis ra ON ra.locker_id = mp.locker_id
    WHERE (p_locker_id IS NULL OR mp.locker_id = p_locker_id)
        AND (p_start_month IS NULL OR mp.month >= p_start_month)
        AND (p_end_month IS NULL OR mp.month <= p_end_month)
    ORDER BY mp.locker_id, mp.month DESC;
END;
$$;


ALTER FUNCTION public.generate_locker_financial_report(p_locker_id character varying, p_start_month date, p_end_month date) OWNER TO admin;

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
-- Name: get_current_partner_id(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.get_current_partner_id() RETURNS character varying
    LANGUAGE sql STABLE
    AS $$
    SELECT NULLIF(current_setting('app.current_partner_id', TRUE), '')::VARCHAR;
$$;


ALTER FUNCTION public.get_current_partner_id() OWNER TO admin;

--
-- Name: get_current_tenant_id(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.get_current_tenant_id() RETURNS character varying
    LANGUAGE sql STABLE
    AS $$
    SELECT NULLIF(current_setting('app.current_tenant_id', TRUE), '')::VARCHAR;
$$;


ALTER FUNCTION public.get_current_tenant_id() OWNER TO admin;

--
-- Name: get_current_user_role(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.get_current_user_role() RETURNS character varying
    LANGUAGE sql STABLE
    AS $$
    SELECT NULLIF(current_setting('app.user_role', TRUE), '')::VARCHAR;
$$;


ALTER FUNCTION public.get_current_user_role() OWNER TO admin;

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
-- Name: simulate_expansion_scenario(character varying, integer, integer, integer, integer, integer); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.simulate_expansion_scenario(p_target_city character varying, p_estimated_monthly_revenue_cents integer, p_estimated_monthly_opex_cents integer, p_installation_cost_cents integer, p_hardware_cost_cents integer, p_useful_life_months integer DEFAULT 60) RETURNS TABLE(scenario_metric character varying, value numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_total_investment_cents INTEGER;
    v_monthly_depreciation_cents INTEGER;
    v_monthly_profit_cents INTEGER;
    v_payback_months NUMERIC;
    v_annual_roi_pct NUMERIC;
    v_breakeven_occupancy_rate NUMERIC;
BEGIN
    -- Cálculo do investimento total
    v_total_investment_cents := p_installation_cost_cents + p_hardware_cost_cents;
    
    -- Depreciação mensal (linear)
    v_monthly_depreciation_cents := v_total_investment_cents / p_useful_life_months;
    
    -- Lucro mensal projetado
    v_monthly_profit_cents := p_estimated_monthly_revenue_cents - p_estimated_monthly_opex_cents - v_monthly_depreciation_cents;
    
    -- Payback em meses
    IF v_monthly_profit_cents > 0 THEN
        v_payback_months := ROUND(v_total_investment_cents::NUMERIC / v_monthly_profit_cents, 1);
    ELSE
        v_payback_months := NULL;
    END IF;
    
    -- ROI anual
    IF v_total_investment_cents > 0 THEN
        v_annual_roi_pct := ROUND((v_monthly_profit_cents * 12 * 100.0) / v_total_investment_cents, 2);
    ELSE
        v_annual_roi_pct := NULL;
    END IF;
    
    -- Taxa de ocupação necessária para breakeven
    v_breakeven_occupancy_rate := ROUND(
        (p_estimated_monthly_opex_cents + v_monthly_depreciation_cents)::NUMERIC / 
        NULLIF(p_estimated_monthly_revenue_cents, 0) * 100, 2
    );
    
    -- Retorno da tabela
    RETURN QUERY SELECT 'target_city'::VARCHAR, p_target_city::NUMERIC;
    RETURN QUERY SELECT 'total_investment_brl', ROUND(v_total_investment_cents / 100.0, 2);
    RETURN QUERY SELECT 'estimated_monthly_revenue_brl', ROUND(p_estimated_monthly_revenue_cents / 100.0, 2);
    RETURN QUERY SELECT 'estimated_monthly_opex_brl', ROUND(p_estimated_monthly_opex_cents / 100.0, 2);
    RETURN QUERY SELECT 'monthly_depreciation_brl', ROUND(v_monthly_depreciation_cents / 100.0, 2);
    RETURN QUERY SELECT 'estimated_monthly_profit_brl', ROUND(v_monthly_profit_cents / 100.0, 2);
    RETURN QUERY SELECT 'payback_months', v_payback_months;
    RETURN QUERY SELECT 'annual_roi_pct', v_annual_roi_pct;
    RETURN QUERY SELECT 'breakeven_occupancy_rate_pct', v_breakeven_occupancy_rate;
    RETURN QUERY SELECT 'viability', 
        CASE WHEN v_monthly_profit_cents > 0 AND v_payback_months <= 24 THEN 1::NUMERIC ELSE 0::NUMERIC END;
END;
$$;


ALTER FUNCTION public.simulate_expansion_scenario(p_target_city character varying, p_estimated_monthly_revenue_cents integer, p_estimated_monthly_opex_cents integer, p_installation_cost_cents integer, p_hardware_cost_cents integer, p_useful_life_months integer) OWNER TO admin;

--
-- Name: simulate_expansion_scenario_v2(character varying, integer, integer, integer, integer, integer, integer, numeric); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.simulate_expansion_scenario_v2(p_target_city character varying, p_lockers_count integer, p_estimated_monthly_revenue_per_locker_cents integer, p_estimated_monthly_opex_per_locker_cents integer, p_installation_cost_per_locker_cents integer, p_hardware_cost_per_locker_cents integer, p_useful_life_months integer DEFAULT 60, p_expected_occupancy_rate_pct numeric DEFAULT 70) RETURNS TABLE(scenario_metric character varying, value numeric, description text)
    LANGUAGE plpgsql
    AS $_$
DECLARE
    v_total_investment_cents BIGINT;
    v_monthly_depreciation_cents BIGINT;
    v_total_monthly_revenue_cents BIGINT;
    v_total_monthly_opex_cents BIGINT;
    v_monthly_profit_cents BIGINT;
    v_payback_months NUMERIC;
    v_annual_roi_pct NUMERIC;
    v_breakeven_occupancy_rate NUMERIC;
    v_npv_36_months NUMERIC;
    v_irr_pct NUMERIC;
    v_daily_revenue_target_cents BIGINT;
BEGIN
    -- Cálculos base
    v_total_investment_cents := (p_installation_cost_per_locker_cents + p_hardware_cost_per_locker_cents) * p_lockers_count;
    v_monthly_depreciation_cents := v_total_investment_cents / p_useful_life_months;
    v_total_monthly_revenue_cents := p_estimated_monthly_revenue_per_locker_cents * p_lockers_count;
    v_total_monthly_opex_cents := p_estimated_monthly_opex_per_locker_cents * p_lockers_count;
    
    -- Ajuste pela ocupação esperada
    v_total_monthly_revenue_cents := (v_total_monthly_revenue_cents * p_expected_occupancy_rate_pct / 100)::BIGINT;
    
    -- Lucro mensal
    v_monthly_profit_cents := v_total_monthly_revenue_cents - v_total_monthly_opex_cents - v_monthly_depreciation_cents;
    
    -- Payback
    IF v_monthly_profit_cents > 0 THEN
        v_payback_months := ROUND(v_total_investment_cents::NUMERIC / v_monthly_profit_cents, 1);
    ELSE
        v_payback_months := NULL;
    END IF;
    
    -- ROI Anual
    IF v_total_investment_cents > 0 THEN
        v_annual_roi_pct := ROUND((v_monthly_profit_cents * 12 * 100.0) / v_total_investment_cents, 2);
    ELSE
        v_annual_roi_pct := NULL;
    END IF;
    
    -- Breakeven occupancy
    v_breakeven_occupancy_rate := ROUND(
        (v_total_monthly_opex_cents + v_monthly_depreciation_cents)::NUMERIC / 
        NULLIF((p_estimated_monthly_revenue_per_locker_cents * p_lockers_count)::NUMERIC, 0) * 100, 2
    );
    
    -- NPV para 36 meses (3 anos)
    v_npv_36_months := ROUND(
        v_monthly_profit_cents * (1 - POWER(1 / (1 + 0.10/12), 36)) / (0.10/12) - v_total_investment_cents,
        0
    );
    
    -- IRR aproximada (simplificada)
    IF v_total_investment_cents > 0 AND v_monthly_profit_cents > 0 THEN
        v_irr_pct := ROUND((v_monthly_profit_cents * 12 * 100.0) / v_total_investment_cents, 2);
    ELSE
        v_irr_pct := NULL;
    END IF;
    
    -- Receita diária necessária para breakeven
    v_daily_revenue_target_cents := (v_total_monthly_opex_cents + v_monthly_depreciation_cents) / 30;
    
    -- Retorno da tabela
    RETURN QUERY SELECT 'target_city'::VARCHAR, p_target_city::NUMERIC, 'Cidade alvo da expansão'::TEXT;
    RETURN QUERY SELECT 'lockers_count'::VARCHAR, p_lockers_count::NUMERIC, 'Número de lockers no cenário'::TEXT;
    RETURN QUERY SELECT 'expected_occupancy_rate_pct'::VARCHAR, p_expected_occupancy_rate_pct, 'Taxa de ocupação esperada (%)'::TEXT;
    RETURN QUERY SELECT 'total_investment_brl'::VARCHAR, ROUND(v_total_investment_cents / 100.0, 2), 'Investimento total (R$)'::TEXT;
    RETURN QUERY SELECT 'estimated_monthly_revenue_brl'::VARCHAR, ROUND(v_total_monthly_revenue_cents / 100.0, 2), 'Receita mensal estimada (R$)'::TEXT;
    RETURN QUERY SELECT 'estimated_monthly_opex_brl'::VARCHAR, ROUND(v_total_monthly_opex_cents / 100.0, 2), 'Custo operacional mensal (R$)'::TEXT;
    RETURN QUERY SELECT 'monthly_depreciation_brl'::VARCHAR, ROUND(v_monthly_depreciation_cents / 100.0, 2), 'Depreciação mensal (R$)'::TEXT;
    RETURN QUERY SELECT 'estimated_monthly_profit_brl'::VARCHAR, ROUND(v_monthly_profit_cents / 100.0, 2), 'Lucro mensal estimado (R$)'::TEXT;
    RETURN QUERY SELECT 'payback_months'::VARCHAR, COALESCE(v_payback_months, 0), 'Payback em meses'::TEXT;
    RETURN QUERY SELECT 'annual_roi_pct'::VARCHAR, COALESCE(v_annual_roi_pct, 0), 'ROI anual (%)'::TEXT;
    RETURN QUERY SELECT 'breakeven_occupancy_rate_pct'::VARCHAR, v_breakeven_occupancy_rate, 'Taxa de ocupação mínima para breakeven (%)'::TEXT;
    RETURN QUERY SELECT 'npv_36_months_brl'::VARCHAR, ROUND(v_npv_36_months / 100.0, 2), 'VPL em 36 meses (R$ - taxa 10% a.a.)'::TEXT;
    RETURN QUERY SELECT 'irr_pct'::VARCHAR, COALESCE(v_irr_pct, 0), 'Taxa interna de retorno anual estimada (%)'::TEXT;
    RETURN QUERY SELECT 'daily_revenue_target_brl'::VARCHAR, ROUND(v_daily_revenue_target_cents / 100.0, 2), 'Receita diária necessária para breakeven (R$)'::TEXT;
    RETURN QUERY SELECT 'viability'::VARCHAR, 
        CASE WHEN v_monthly_profit_cents > 0 AND v_payback_months <= 24 THEN 1::NUMERIC ELSE 0::NUMERIC END,
        'Viabilidade do cenário (1=Viável, 0=Inviável)'::TEXT;
END;
$_$;


ALTER FUNCTION public.simulate_expansion_scenario_v2(p_target_city character varying, p_lockers_count integer, p_estimated_monthly_revenue_per_locker_cents integer, p_estimated_monthly_opex_per_locker_cents integer, p_installation_cost_per_locker_cents integer, p_hardware_cost_per_locker_cents integer, p_useful_life_months integer, p_expected_occupancy_rate_pct numeric) OWNER TO admin;

--
-- Name: sp_refresh_financial_materialized_views(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.sp_refresh_financial_materialized_views() RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_start_time TIMESTAMPTZ;
    v_end_time TIMESTAMPTZ;
    v_duration TEXT;
BEGIN
    v_start_time := NOW();
    
    -- Atualiza a view de rentabilidade
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_locker_monthly_profitability;
    RAISE NOTICE '✅ mv_locker_monthly_profitability atualizada';
    
    -- Atualiza outras views financeiras existentes
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_realtime_kpis;
    RAISE NOTICE '✅ mv_realtime_kpis atualizada';
    
    -- Atualiza view de PnL se existir
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'mv_locker_monthly_pnl') THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_locker_monthly_pnl;
        RAISE NOTICE '✅ mv_locker_monthly_pnl atualizada';
    END IF;
    
    v_end_time := NOW();
    v_duration := EXTRACT(EPOCH FROM (v_end_time - v_start_time))::TEXT || ' segundos';
    
    RAISE NOTICE '✅ Todas as materialized views financeiras atualizadas em %', v_duration;
    
    RETURN 'Atualização concluída em ' || v_duration;
END;
$$;


ALTER FUNCTION public.sp_refresh_financial_materialized_views() OWNER TO admin;

--
-- Name: sp_sync_monthly_costs_from_entries(date); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.sp_sync_monthly_costs_from_entries(p_target_month date DEFAULT (date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))::date) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_updated_count INTEGER := 0;
    v_locker_record RECORD;
BEGIN
    -- Sincroniza custos a partir das tabelas existentes
    FOR v_locker_record IN
        SELECT DISTINCT locker_id 
        FROM public.ellanlab_opex_entries 
        WHERE expense_month = p_target_month AND locker_id IS NOT NULL
        UNION
        SELECT locker_id 
        FROM public.locker_opex 
        WHERE reference_month = p_target_month AND locker_id IS NOT NULL
        UNION
        SELECT ha.locker_id 
        FROM public.ellanlab_depreciation_schedule ds
        JOIN public.ellanlab_hardware_assets ha ON ha.id = ds.asset_id
        WHERE ds.depreciation_month = p_target_month AND ha.locker_id IS NOT NULL
    LOOP
        -- UPSERT dos custos mensais
        INSERT INTO public.cost_center_monthly (
            locker_id, month,
            maintenance_preventive_cents, maintenance_corrective_cents,
            connectivity_cents, energy_cents, rent_cents,
            insurance_cents, depreciation_cents,
            updated_at
        )
        SELECT 
            v_locker_record.locker_id,
            p_target_month,
            -- Manutenção preventiva (de opex_entries)
            COALESCE(SUM(CASE WHEN oe.category = 'MAINTENANCE' AND oe.metadata_json->>'type' = 'preventive' 
                THEN oe.amount_cents ELSE 0 END), 0),
            -- Manutenção corretiva
            COALESCE(SUM(CASE WHEN oe.category = 'MAINTENANCE' AND (oe.metadata_json->>'type' = 'corrective' OR oe.metadata_json->>'type' IS NULL)
                THEN oe.amount_cents ELSE 0 END), 0),
            -- Conectividade
            COALESCE(SUM(CASE WHEN oe.category = 'CONNECTIVITY' THEN oe.amount_cents ELSE 0 END), 0),
            -- Energia
            COALESCE(SUM(CASE WHEN oe.category = 'ENERGY' THEN oe.amount_cents ELSE 0 END), 0),
            -- Aluguel (RENT)
            COALESCE(SUM(CASE WHEN oe.category = 'RENT' THEN oe.amount_cents ELSE 0 END), 0),
            -- Seguro (de locker_opex)
            COALESCE(SUM(CASE WHEN lo.cost_type = 'INSURANCE' THEN lo.amount_cents ELSE 0 END), 0),
            -- Depreciação
            COALESCE(SUM(ds.depreciation_amount_cents), 0),
            NOW()
        FROM public.ellanlab_opex_entries oe
        FULL JOIN public.locker_opex lo ON lo.locker_id = oe.locker_id AND lo.reference_month = oe.expense_month
        FULL JOIN public.ellanlab_depreciation_schedule ds ON ds.locker_id = oe.locker_id AND ds.depreciation_month = oe.expense_month
        WHERE (oe.locker_id = v_locker_record.locker_id AND oe.expense_month = p_target_month)
           OR (lo.locker_id = v_locker_record.locker_id AND lo.reference_month = p_target_month)
           OR (ds.locker_id = v_locker_record.locker_id AND ds.depreciation_month = p_target_month)
        GROUP BY v_locker_record.locker_id
        ON CONFLICT (locker_id, month) DO UPDATE SET
            maintenance_preventive_cents = EXCLUDED.maintenance_preventive_cents,
            maintenance_corrective_cents = EXCLUDED.maintenance_corrective_cents,
            connectivity_cents = EXCLUDED.connectivity_cents,
            energy_cents = EXCLUDED.energy_cents,
            rent_cents = EXCLUDED.rent_cents,
            insurance_cents = EXCLUDED.insurance_cents,
            depreciation_cents = EXCLUDED.depreciation_cents,
            updated_at = EXCLUDED.updated_at;
        
        v_updated_count := v_updated_count + 1;
    END LOOP;
    
    RAISE NOTICE '✅ Custos sincronizados para % lockers no mês %', v_updated_count, p_target_month;
    
    RETURN v_updated_count;
END;
$$;


ALTER FUNCTION public.sp_sync_monthly_costs_from_entries(p_target_month date) OWNER TO admin;

--
-- Name: trg_cost_center_monthly_updated(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.trg_cost_center_monthly_updated() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_cost_center_monthly_updated() OWNER TO admin;

--
-- Name: trg_log_slot_state_change(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.trg_log_slot_state_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO public.slot_occupancy_history (
            locker_id,
            slot_label,
            allocation_id,
            previous_state,
            current_state,
            triggered_by,
            metadata
        ) VALUES (
            NEW.locker_id,
            NEW.slot_label,
            NEW.current_allocation_id,
            OLD.status,
            NEW.status,
            'SYSTEM',
            jsonb_build_object('fault_code', NEW.fault_code)
        );
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_log_slot_state_change() OWNER TO admin;

--
-- Name: trg_payment_transactions_calc_fees(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.trg_payment_transactions_calc_fees() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.status = 'APPROVED' AND NEW.gateway_fee_cents IS NULL THEN
        NEW.gateway_fee_cents := public.calculate_gateway_fee(
            NEW.amount_cents,
            NEW.payment_method,
            NEW.card_brand,
            COALESCE(NEW.installments, 1)
        );
        NEW.net_amount_cents := NEW.amount_cents - NEW.gateway_fee_cents;
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_payment_transactions_calc_fees() OWNER TO admin;

--
-- Name: trg_pickups_sync_v2_derived(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.trg_pickups_sync_v2_derived() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.evidence_score := COALESCE(NEW.evidence_score, 0);

    IF NEW.dispute_state IS NULL THEN
        NEW.dispute_state := 'NONE'::public.dispute_state;
    END IF;

    NEW.evidence_strength := public.fn_derive_evidence_strength(NEW.evidence_score);

    IF NEW.pickup_phase = 'COMPLETED_VERIFIED'::public.pickup_phase
       AND NEW.verified_at IS NULL THEN
        NEW.verified_at := now();
    END IF;

    -- BLE é considerado evidência forte para verificação automática
    IF NEW.redeemed_via = 'BLE'::public.pickupredeemvia 
       AND NEW.pickup_phase = 'COMPLETED_UNVERIFIED'::public.pickup_phase THEN
        NEW.evidence_score := GREATEST(NEW.evidence_score, 85);
        NEW.evidence_strength := public.fn_derive_evidence_strength(NEW.evidence_score);
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

--
-- Name: validate_ml_predictions(); Type: FUNCTION; Schema: public; Owner: admin
--


CREATE FUNCTION public.validate_ml_predictions() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
  rows_affected INTEGER;
BEGIN
  INSERT INTO ml_prediction_feedback (prediction_id, actual_value, error_pct, model_performance_status)
  SELECT 
    mlp.id,
    ROUND(COALESCE(AVG(CASE WHEN lt.is_occupied THEN 100 ELSE 0 END), 0), 2) as actual_value,
    CASE 
      WHEN mlp.failure_probability > 0 AND COUNT(lt.id) > 0 THEN 
        ROUND(ABS((mlp.failure_probability - AVG(CASE WHEN lt.is_occupied THEN 100 ELSE 0 END)) / mlp.failure_probability) * 100, 2)
      ELSE 
        NULL
    END as error_pct,
    CASE 
      WHEN COUNT(lt.id) = 0 THEN 'NO_OCCUPANCY_DATA'
      WHEN AVG(CASE WHEN lt.is_occupied THEN 100 ELSE 0 END) = 0 THEN 'NO_ACTUAL_DATA'
      WHEN ABS((mlp.failure_probability - AVG(CASE WHEN lt.is_occupied THEN 100 ELSE 0 END)) / NULLIF(mlp.failure_probability, 0)) * 100 < 10 THEN 'GOOD'
      WHEN ABS((mlp.failure_probability - AVG(CASE WHEN lt.is_occupied THEN 100 ELSE 0 END)) / NULLIF(mlp.failure_probability, 0)) * 100 < 30 THEN 'ACCEPTABLE'
      ELSE 'POOR'
    END as performance_status
  FROM ml_predictions_log mlp
  LEFT JOIN locker_slot_hourly_occupancy lt 
    ON mlp.locker_id = lt.locker_id 
    AND DATE(mlp.predicted_at) = DATE(lt.hour_bucket)
  WHERE mlp.model_version = 'current'
    AND mlp.predicted_at < NOW() - INTERVAL '24 hours'
    AND NOT EXISTS (
      SELECT 1 FROM ml_prediction_feedback 
      WHERE prediction_id = mlp.id
    )
  GROUP BY mlp.id, mlp.failure_probability;
    
  GET DIAGNOSTICS rows_affected = ROW_COUNT;
  
  IF rows_affected > 0 THEN
    RAISE NOTICE '✓ Processed % predictions with feedback', rows_affected;
  ELSE
    RAISE NOTICE 'ℹ No new predictions to process (waiting 24h after prediction)';
  END IF;
END;
$$;


ALTER FUNCTION public.validate_ml_predictions() OWNER TO admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

