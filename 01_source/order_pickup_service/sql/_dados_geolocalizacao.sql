-- Verificar países
SELECT 'COUNTRIES' as table_name, COUNT(*) as total FROM public.capability_country
UNION ALL
SELECT 'PROVINCES', COUNT(*) FROM public.capability_province
UNION ALL
SELECT 'LOCKERS', COUNT(*) FROM public.capability_locker_location;

-- Verificar lockers ativos por país
SELECT 
    c.code as country,
    c.name as country_name,
    COUNT(l.id) as total_lockers,
    SUM(CASE WHEN l.is_active THEN 1 ELSE 0 END) as active_lockers
FROM public.capability_country c
LEFT JOIN public.capability_province p ON p.country_code = c.code
LEFT JOIN public.capability_locker_location l ON l.province_code = p.code
GROUP BY c.code, c.name
ORDER BY total_lockers DESC;

-- Teste de busca por proximidade (lockers perto do centro Jardim Marilu)
SELECT 
    external_id,
    city_name,
    district,
    address_street,
    ROUND(CAST(ST_Distance(
        geom::geography,
        ST_SetSRID(ST_MakePoint(-46.82675, -23.58090), 4326)::geography
    ) AS NUMERIC), 2) as distance_meters,
    is_active,
    metadata_json->>'is_24h' as is_24h
FROM public.capability_locker_location
WHERE geom IS NOT NULL AND is_active = true
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(-46.82675, -23.58090), 4326)
LIMIT 5;

-- Estatísticas de temperatura zone
SELECT 
    metadata_json->>'temperature_zone' as temperature_zone,
    COUNT(*) as count
FROM public.capability_locker_location
GROUP BY metadata_json->>'temperature_zone'
ORDER BY count DESC;

-- Buscar lockers próximos ao centro de São Paulo (raio 10km)
SELECT * FROM find_lockers_by_distance(-23.5505, -46.6333, 10000, 10);

-- Buscar lockers próximos ao centro de Lisboa (raio 5km)
SELECT * FROM find_lockers_by_distance(38.7223, -9.1393, 5000, 10);

-- Buscar lockers próximos ao centro de Jardim Marilu (raio 7km)
SELECT * FROM find_lockers_by_distance(-23.58090, -46.82675, 7000, 10);