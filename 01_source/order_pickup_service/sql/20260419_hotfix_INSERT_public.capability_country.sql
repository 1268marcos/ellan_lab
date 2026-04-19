-- Inserir países únicos do CSV
INSERT INTO public.capability_country (code, name, continent, default_currency, default_timezone, address_format, is_active) VALUES
('BR', 'Brasil', 'South America', 'BRL', 'America/Sao_Paulo', 'BR', true),
('PT', 'Portugal', 'Europe', 'EUR', 'Europe/Lisbon', 'PT', true),
('ES', 'Espanha', 'Europe', 'EUR', 'Europe/Madrid', 'ES', true)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    continent = EXCLUDED.continent,
    default_currency = EXCLUDED.default_currency,
    default_timezone = EXCLUDED.default_timezone,
    updated_at = NOW();

-- Verificar
SELECT code, name, continent, default_currency, is_active FROM public.capability_country;

