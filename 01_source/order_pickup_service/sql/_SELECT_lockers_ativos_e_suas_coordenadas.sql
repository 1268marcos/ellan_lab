SELECT 
    external_id,
    city_name,
    latitude,
    longitude,
    ST_AsText(geom) as geometry_wkt,
    is_active,
    metadata_json->>'is_24h' as is_24h,
    metadata_json->>'temperature_zone' as temp_zone
FROM public.capability_locker_location
WHERE is_active = true
ORDER BY city_name;