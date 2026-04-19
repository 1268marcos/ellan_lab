-- 001_postgis.sql
-- Este script executa automaticamente na primeira inicialização do container

-- Ativar extensões PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS address_standardizer;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Criar schema para dados geográficos
CREATE SCHEMA IF NOT EXISTS geodata;

-- Tabela de exemplo para teste
CREATE TABLE IF NOT EXISTS geodata.test_points (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Verificar instalação
DO $$
BEGIN
    RAISE NOTICE 'PostGIS version: %', (SELECT PostGIS_version());
    RAISE NOTICE 'PostGIS installed successfully!';
END $$;