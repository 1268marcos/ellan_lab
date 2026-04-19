-- =====================================================
-- SCRIPT COMPLETO PARA TABELAS DE CAPABILIDADE
-- Sistema de Lockers - Nível Amazon/SingPost
-- =====================================================

-- =====================================================
-- 1. ATIVAR EXTENSÃO POSTGIS (GEOLOCALIZAÇÃO PESADA)
-- =====================================================
-- Verifica se a extensão já existe, se não, cria
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- =====================================================
-- 2. TABELA: capability_country (Países)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.capability_country (
    id SERIAL PRIMARY KEY,
    code CHAR(2) UNIQUE NOT NULL, -- ISO 3166-1 alpha-2 (BR, US, ZA)
    name VARCHAR(100) NOT NULL,
    continent VARCHAR(50),
    default_currency CHAR(3), -- ISO 4217
    default_timezone VARCHAR(50), -- Ex: 'America/Sao_Paulo'
    address_format VARCHAR(20), -- Ex: 'BR', 'US' (para saber se é [Street, Number] ou [Number, Street])
    metadata_json JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 3. TABELA: capability_province (Estados/Províncias)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.capability_province (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL, -- ISO 3166-2: BR-SP, US-CA, ZA-WC
    name VARCHAR(100) NOT NULL,
    country_code CHAR(2) REFERENCES public.capability_country(code) ON DELETE CASCADE,
    province_code_original CHAR(2), -- Código original da UF (SP, RJ, AC) para compatibilidade
    region VARCHAR(50), -- Sudeste, Centro-Oeste (nível de agrupamento)
    timezone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    metadata_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 4. TABELA: capability_locker_location (Lockers Físicos)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.capability_locker_location (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE, -- ID do parceiro (ex: código dos Correios)
    province_code VARCHAR(10) REFERENCES public.capability_province(code) ON DELETE SET NULL,
    city_name VARCHAR(100),
    district VARCHAR(100), -- Bairro
    postal_code VARCHAR(20), -- CEP. CRÍTICO para logística
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    geom GEOMETRY(Point, 4326), -- Coluna para PostGIS (geometria espacial)
    timezone VARCHAR(50), -- Pode herdar da província, mas permite overrides
    address_street VARCHAR(255),
    address_number VARCHAR(20),
    address_complement VARCHAR(100),
    operating_hours_json JSONB, -- Horário de funcionamento em JSON
    is_active BOOLEAN DEFAULT TRUE,
    metadata_json JSONB, -- Para flags como "24h", "Acessível", "Tamanhos de Locker"
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 5. TRIGGERS PARA updated_at (ATUALIZAÇÃO AUTOMÁTICA)
-- =====================================================
-- Função para atualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para cada tabela
CREATE TRIGGER trigger_country_updated_at 
    BEFORE UPDATE ON public.capability_country 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_province_updated_at 
    BEFORE UPDATE ON public.capability_province 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_locker_updated_at 
    BEFORE UPDATE ON public.capability_locker_location 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 6. ÍNDICES PARA capability_country
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_country_code ON public.capability_country (code);
CREATE INDEX IF NOT EXISTS idx_country_is_active ON public.capability_country (is_active);
CREATE INDEX IF NOT EXISTS idx_country_continent ON public.capability_country (continent);
CREATE INDEX IF NOT EXISTS idx_country_continent_active ON public.capability_country (continent, is_active);
CREATE INDEX IF NOT EXISTS idx_country_metadata_gin ON public.capability_country USING GIN (metadata_json);
CREATE INDEX IF NOT EXISTS idx_country_created_at ON public.capability_country (created_at);

-- =====================================================
-- 7. ÍNDICES PARA capability_province
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_province_code ON public.capability_province (code);
CREATE INDEX IF NOT EXISTS idx_province_country_code ON public.capability_province (country_code);
CREATE INDEX IF NOT EXISTS idx_province_region ON public.capability_province (region);
CREATE INDEX IF NOT EXISTS idx_province_province_code_original ON public.capability_province (province_code_original);
CREATE INDEX IF NOT EXISTS idx_province_is_active ON public.capability_province (is_active);
CREATE INDEX IF NOT EXISTS idx_province_country_region ON public.capability_province (country_code, region);
CREATE INDEX IF NOT EXISTS idx_province_country_active ON public.capability_province (country_code, is_active);
CREATE INDEX IF NOT EXISTS idx_province_metadata_gin ON public.capability_province USING GIN (metadata_json);
CREATE INDEX IF NOT EXISTS idx_province_created_at ON public.capability_province (created_at);

-- Índice parcial para províncias ativas (economiza espaço)
CREATE INDEX IF NOT EXISTS idx_province_active_only ON public.capability_province (country_code) 
WHERE is_active = true;

-- =====================================================
-- 8. ÍNDICES PARA capability_locker_location
-- =====================================================
-- Índices básicos
CREATE INDEX IF NOT EXISTS idx_locker_external_id ON public.capability_locker_location (external_id);
CREATE INDEX IF NOT EXISTS idx_locker_province_code ON public.capability_locker_location (province_code);
CREATE INDEX IF NOT EXISTS idx_locker_postal_code ON public.capability_locker_location (postal_code);
CREATE INDEX IF NOT EXISTS idx_locker_is_active ON public.capability_locker_location (is_active);
CREATE INDEX IF NOT EXISTS idx_locker_city_name ON public.capability_locker_location (city_name);
CREATE INDEX IF NOT EXISTS idx_locker_district ON public.capability_locker_location (district);
CREATE INDEX IF NOT EXISTS idx_locker_created_at ON public.capability_locker_location (created_at);

-- Índices compostos (alta performance)
CREATE INDEX IF NOT EXISTS idx_locker_province_active ON public.capability_locker_location (province_code, is_active);
CREATE INDEX IF NOT EXISTS idx_locker_city_district ON public.capability_locker_location (city_name, district);
CREATE INDEX IF NOT EXISTS idx_locker_postal_active ON public.capability_locker_location (postal_code, is_active);
CREATE INDEX IF NOT EXISTS idx_locker_city_active ON public.capability_locker_location (city_name, is_active);

-- Índices de coordenadas (para buscas sem PostGIS)
CREATE INDEX IF NOT EXISTS idx_locker_coords ON public.capability_locker_location (latitude, longitude);

-- =====================================================
-- 9. ÍNDICES POSTGIS (GEOLOCALIZAÇÃO PESADA)
-- =====================================================
-- Índice espacial GIST para consultas de proximidade
-- Este é o índice mais importante para geolocalização pesada
CREATE INDEX IF NOT EXISTS idx_locker_geom_gist ON public.capability_locker_location USING GIST (geom);

-- Índice auxiliar para bounding box (acelera consultas espaciais)
CREATE INDEX IF NOT EXISTS idx_locker_geom_bbox ON public.capability_locker_location USING GIST (geom gist_geometry_ops_nd);

-- =====================================================
-- 10. ÍNDICES JSONB (para buscas dentro de JSON)
-- =====================================================
-- Índices GIN para JSONB
CREATE INDEX IF NOT EXISTS idx_locker_hours_gin ON public.capability_locker_location USING GIN (operating_hours_json);
CREATE INDEX IF NOT EXISTS idx_locker_metadata_gin ON public.capability_locker_location USING GIN (metadata_json);

-- Índices específicos para campos comuns dentro do JSON (exemplo)
-- Isso acelera consultas como: WHERE metadata_json->>'is_24h' = 'true'
CREATE INDEX IF NOT EXISTS idx_locker_metadata_is_24h ON public.capability_locker_location ((metadata_json->>'is_24h'));
CREATE INDEX IF NOT EXISTS idx_locker_metadata_locker_size ON public.capability_locker_location ((metadata_json->>'locker_size'));

-- =====================================================
-- 11. ÍNDICES DE BUSCA TEXTUAL (Full-Text Search)
-- =====================================================
-- Índice para busca em português (endereços, cidades, bairros)
CREATE INDEX IF NOT EXISTS idx_locker_address_search_pt ON public.capability_locker_location 
USING GIN (to_tsvector('portuguese', 
    COALESCE(address_street, '') || ' ' || 
    COALESCE(address_number, '') || ' ' ||
    COALESCE(city_name, '') || ' ' || 
    COALESCE(district, '') || ' ' ||
    COALESCE(postal_code, '')
));

-- Índice para busca em inglês (fallback)
CREATE INDEX IF NOT EXISTS idx_locker_address_search_en ON public.capability_locker_location 
USING GIN (to_tsvector('english', 
    COALESCE(address_street, '') || ' ' || 
    COALESCE(city_name, '') || ' ' || 
    COALESCE(district, '')
));

-- =====================================================
-- 12. ÍNDICES PARCIAIS (Para cenários específicos)
-- =====================================================
-- Apenas lockers ativos
CREATE INDEX IF NOT EXISTS idx_locker_active_only ON public.capability_locker_location (id) 
WHERE is_active = true;

-- Apenas lockers 24 horas
CREATE INDEX IF NOT EXISTS idx_locker_24h_only ON public.capability_locker_location (id) 
WHERE metadata_json->>'is_24h' = 'true';

-- Apenas lockers com geolocalização definida
CREATE INDEX IF NOT EXISTS idx_locker_has_geom ON public.capability_locker_location (id) 
WHERE geom IS NOT NULL;

-- =====================================================
-- 13. FUNÇÃO PARA ATUALIZAR COLUNA GEOM AUTOMATICAMENTE
-- =====================================================
-- Trigger para manter geom sincronizado com latitude/longitude
CREATE OR REPLACE FUNCTION update_geom_from_coords()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    ELSIF NEW.latitude IS NULL OR NEW.longitude IS NULL THEN
        NEW.geom = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_locker_update_geom
    BEFORE INSERT OR UPDATE OF latitude, longitude ON public.capability_locker_location
    FOR EACH ROW
    EXECUTE FUNCTION update_geom_from_coords();

-- =====================================================
-- 14. COMENTÁRIOS NAS TABELAS (Documentação)
-- =====================================================
COMMENT ON TABLE public.capability_country IS 'Países operacionais para o sistema de lockers';
COMMENT ON TABLE public.capability_province IS 'Estados/Províncias com hierarquia ISO 3166-2 (ex: BR-SP)';
COMMENT ON TABLE public.capability_locker_location IS 'Localizações físicas dos lockers com suporte a geolocalização';

COMMENT ON COLUMN public.capability_locker_location.geom IS 'Geometria PostGIS (Point, SRID 4326) para consultas espaciais avançadas';
COMMENT ON COLUMN public.capability_locker_location.operating_hours_json IS 'JSON com horários: {"monday": "08:00-22:00", "saturday": "09:00-14:00"}';
COMMENT ON COLUMN public.capability_locker_location.metadata_json IS 'Metadados extensíveis: {"is_24h": true, "locker_size": "large", "accessibility": "wheelchair"}';

-- =====================================================
-- 15. EXEMPLOS DE CONSULTAS (Para referência)
-- =====================================================
-- Exemplo 1: Buscar lockers num raio de 5km a partir de uma coordenada
-- SELECT * FROM capability_locker_location 
-- WHERE is_active = true 
--   AND ST_DWithin(geom, ST_SetSRID(ST_MakePoint(-46.6333, -23.5505), 4326), 5000);

-- Exemplo 2: Buscar lockers por CEP
-- SELECT * FROM capability_locker_location WHERE postal_code = '01310-000' AND is_active = true;

-- Exemplo 3: Buscar lockers por texto (endereço)
-- SELECT * FROM capability_locker_location 
-- WHERE to_tsvector('portuguese', address_street || ' ' || city_name) @@ to_tsquery('paulista');

-- Exemplo 4: Buscar lockers 24h em São Paulo
-- SELECT * FROM capability_locker_location 
-- WHERE province_code = 'BR-SP' 
--   AND metadata_json->>'is_24h' = 'true' 
--   AND is_active = true;

-- =====================================================
-- 16. MANUTENÇÃO RECOMENDADA (Agendar no cron)
-- =====================================================
-- Atualizar estatísticas: ANALYZE capability_locker_location;
-- Reindexar mensalmente: REINDEX TABLE CONCURRENTLY capability_locker_location;
-- Limpar lockers antigos: DELETE FROM capability_locker_location WHERE is_active = false AND updated_at < NOW() - INTERVAL '180 days';

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================