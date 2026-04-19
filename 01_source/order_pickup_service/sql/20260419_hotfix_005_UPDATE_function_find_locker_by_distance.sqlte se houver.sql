-- Remover função existente se houver
DROP FUNCTION IF EXISTS find_lockers_by_distance(numeric, numeric, numeric, integer);

-- Recriar função com tipos corretos
CREATE OR REPLACE FUNCTION find_lockers_by_distance(
    ref_lat NUMERIC,
    ref_lon NUMERIC,
    radius_meters NUMERIC,
    max_results INTEGER DEFAULT 50
) RETURNS TABLE(
    id INTEGER,
    external_id VARCHAR,
    address_street VARCHAR,
    city_name VARCHAR,
    district VARCHAR,
    postal_code VARCHAR,
    distance_meters NUMERIC,
    is_24h BOOLEAN
) AS $$
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
        (l.metadata_json->>'is_24h')::BOOLEAN AS is_24h
    FROM public.capability_locker_location l
    WHERE l.is_active = true
      AND l.geom IS NOT NULL
      AND ST_DWithin(
            l.geom::geography,
            ST_SetSRID(ST_MakePoint(ref_lon, ref_lat), 4326)::geography,
            radius_meters
          )
    ORDER BY l.geom <-> ST_SetSRID(ST_MakePoint(ref_lon, ref_lat), 4326)
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

SELECT 'Função recriada com sucesso!' as status;