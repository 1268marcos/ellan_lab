-- Inserir estados brasileiros (ISO 3166-2)
INSERT INTO public.capability_province (code, name, country_code, province_code_original, region, timezone, is_active) VALUES
('BR-SP', 'São Paulo', 'BR', 'SP', 'Sudeste', 'America/Sao_Paulo', true),
('BR-RJ', 'Rio de Janeiro', 'BR', 'RJ', 'Sudeste', 'America/Sao_Paulo', true),
('BR-PR', 'Paraná', 'BR', 'PR', 'Sul', 'America/Sao_Paulo', true),
('BR-DF', 'Distrito Federal', 'BR', 'DF', 'Centro-Oeste', 'America/Sao_Paulo', true),
('BR-BA', 'Bahia', 'BR', 'BA', 'Nordeste', 'America/Bahia', true),
('BR-RS', 'Rio Grande do Sul', 'BR', 'RS', 'Sul', 'America/Sao_Paulo', true),
('BR-MG', 'Minas Gerais', 'BR', 'MG', 'Sudeste', 'America/Sao_Paulo', true),
('BR-PE', 'Pernambuco', 'BR', 'PE', 'Nordeste', 'America/Recife', true)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    region = EXCLUDED.region,
    updated_at = NOW();

-- Inserir estados de Portugal (usando ISO PT-XX)
INSERT INTO public.capability_province (code, name, country_code, province_code_original, region, timezone, is_active) VALUES
('PT-11', 'Lisboa', 'PT', '11', 'Lisboa', 'Europe/Lisbon', true),
('PT-13', 'Porto', 'PT', '13', 'Norte', 'Europe/Lisbon', true),
('PT-03', 'Braga', 'PT', '03', 'Norte', 'Europe/Lisbon', true)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    region = EXCLUDED.region,
    updated_at = NOW();

-- Inserir províncias da Espanha
INSERT INTO public.capability_province (code, name, country_code, province_code_original, region, timezone, is_active) VALUES
('ES-M', 'Madrid', 'ES', 'M', 'Comunidad de Madrid', 'Europe/Madrid', true)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    region = EXCLUDED.region,
    updated_at = NOW();

-- Verificar
SELECT code, name, country_code, region, is_active FROM public.capability_province ORDER BY country_code, code;
