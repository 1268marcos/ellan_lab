SELECT 
       region,
       COUNT(*) as total_lockers
FROM public.lockers
WHERE active = 'True'
GROUP BY region
ORDER BY region;

-- OU
-- SELECT 
--        region,
--        COUNT(*) as total_lockers
-- FROM public.runtime_lockers
-- WHERE active = 'True'
-- GROUP BY region
-- ORDER BY region;
