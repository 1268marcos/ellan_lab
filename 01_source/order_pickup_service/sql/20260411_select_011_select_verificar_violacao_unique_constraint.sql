-- Verificar duplicatas na combinação (region_id, channel_id, context_id)
SELECT 
    region_id,
    channel_id,
    context_id,
    COUNT(*) AS duplicate_count,
    STRING_AGG(profile_code, ', ' ORDER BY profile_code) AS profile_codes
FROM public.capability_profile
GROUP BY region_id, channel_id, context_id
HAVING COUNT(*) > 1;

-- Verificar duplicatas no profile_code
SELECT 
    profile_code,
    COUNT(*) AS duplicate_count
FROM public.capability_profile
GROUP BY profile_code
HAVING COUNT(*) > 1;