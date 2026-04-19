SELECT 
    l.external_id,
    l.city_name,
    l.district,
    l.address_street,
    l.address_number,
    ROUND(CAST(ST_Distance(
        l.geom::geography,
        ST_SetSRID(ST_MakePoint(-46.6333, -23.5505), 4326)::geography
    ) AS NUMERIC), 2) AS distance_meters,
    l.is_active,
    l.metadata_json->>'is_24h' AS is_24h,
    l.metadata_json->>'temperature_zone' AS temperature_zone
FROM public.capability_locker_location l
WHERE l.is_active = true
  AND l.geom IS NOT NULL
  AND ST_DWithin(
        l.geom::geography,
        ST_SetSRID(ST_MakePoint(-46.6333, -23.5505), 4326)::geography,
        17000  -- 17km
      )
ORDER BY distance_meters
LIMIT 10;

-- LISBOA -- ST_SetSRID(ST_MakePoint(-9.13935, 38.72235), 4326)::geography