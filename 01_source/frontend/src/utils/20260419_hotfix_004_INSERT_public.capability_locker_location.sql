-- Inserir lockers (convertendo os códigos de estado para ISO)
INSERT INTO public.capability_locker_location (
    external_id,
    province_code,
    city_name,
    district,
    postal_code,
    latitude,
    longitude,
    timezone,
    address_street,
    address_number,
    address_complement,
    operating_hours_json,
    is_active,
    metadata_json,
    created_at,
    updated_at
) VALUES
-- SP - Osasco (BR-SP)
(
    'SP-OSASCO-CENTRO-LK-001', 'BR-SP', 'Osasco', 'Centro', '06086-040',
    -23.53245, -46.79162, 'America/Sao_Paulo',
    'Rua Antonio Aguilar', '500', 'Em frente ao Mercado Municipal',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    true,
    '{"is_24h": true, "security_level": "STANDARD", "has_camera": true, "has_alarm": false, "temperature_zone": "AMBIENT", "slots_count": 24, "pickup_code_length": 6, "pickup_reuse_policy": "NO_REUSE"}',
    '2026-03-29 23:54:21.419098', '2026-04-16 18:49:35.860767'
),
-- SP - Carapicuíba JD Marilu Locker 001 (BR-SP)
(
    'SP-CARAPICUIBA-JDMARILU-LK-001', 'BR-SP', 'Carapicuíba', 'Jardim Marilú', '06340-050',
    -23.52262, -46.83552, 'America/Sao_Paulo',
    'Rua Marilú', '120', 'Próximo ao supermercado',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    true,
    '{"is_24h": true, "security_level": "STANDARD", "has_camera": false, "has_alarm": false, "temperature_zone": "AMBIENT", "slots_count": 24}',
    '2026-03-29 23:54:21.425648', '2026-04-16 18:49:35.860767'
),
-- SP - Carapicuíba JD Marilu Locker 002 (BR-SP)
(
    'SP-CARAPICUIBA-JDMARILU-LK-002', 'BR-SP', 'Carapicuíba', 'Jardim Marilú', '06340-050',
    -23.52263, -46.83553, 'America/Sao_Paulo',
    'Rua Marilú', '122', 'Ao lado da farmácia',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    true,
    '{"is_24h": true, "security_level": "STANDARD", "has_camera": false, "has_alarm": false, "temperature_zone": "AMBIENT", "slots_count": 24}',
    '2026-03-29 23:54:21.448929', '2026-04-16 18:49:35.860767'
),
-- SP - Alphaville Shopping (BR-SP)
(
    'SP-ALPHAVILLE-SHOP-LK-001', 'BR-SP', 'Barueri', 'Alphaville', '06454-000',
    -23.51185, -46.87705, 'America/Sao_Paulo',
    'Alameda Rio Negro', '500', 'Shopping Alphaville - Piso G1',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    true,
    '{"is_24h": true, "security_level": "HIGH", "has_camera": true, "has_alarm": true, "temperature_zone": "AMBIENT", "slots_count": 24}',
    '2026-03-29 23:54:21.459495', '2026-04-16 18:49:35.860767'
),
-- SP - Vila Olímpia (BR-SP)
(
    'SP-VILAOLIMPIA-FOOD-LK-001', 'BR-SP', 'São Paulo', 'Vila Olímpia', '04545-004',
    -23.59015, -46.68025, 'America/Sao_Paulo',
    'Rua Fidêncio Ramos', '308', 'Torre B - Térreo',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    true,
    '{"is_24h": true, "security_level": "STANDARD", "has_camera": true, "has_alarm": false, "temperature_zone": "REFRIGERATED", "slots_count": 24}',
    '2026-03-29 23:54:21.469648', '2026-04-16 18:49:35.860767'
),
-- PT - Maia Centro (PT-13 - Porto)
(
    'PT-MAIA-CENTRO-LK-001', 'PT-13', 'Maia', 'Centro', '4470-157',
    41.23572, -8.61905, 'Europe/Lisbon',
    'Avenida Visconde de Barreiros', '250', 'Estação de Metro',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    true,
    '{"is_24h": true, "security_level": "STANDARD", "has_camera": true, "has_alarm": false, "temperature_zone": "AMBIENT", "slots_count": 24}',
    '2026-03-29 23:54:21.480078', '2026-04-16 18:49:35.860767'
),
-- PT - Guimarães Azurém (PT-03 - Braga)
(
    'PT-GUIMARAES-AZUREM-LK-001', 'PT-03', 'Guimarães', 'Azurém', '4805-194',
    41.44715, -8.29105, 'Europe/Lisbon',
    'Rua da Azurém', '45', 'Universidade do Minho',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    true,
    '{"is_24h": true, "security_level": "STANDARD", "has_camera": false, "has_alarm": false, "temperature_zone": "REFRIGERATED", "slots_count": 24}',
    '2026-03-29 23:54:21.490154', '2026-04-16 18:49:35.860767'
),
-- PT - Lisboa (PT-11 - Lisboa)
(
    'PT-LISBOA-PHARMA-LK-001', 'PT-11', 'Lisboa', 'Santo António', '1269-150',
    38.72235, -9.13935, 'Europe/Lisbon',
    'Avenida da Liberdade', '185', 'Farmácia Central',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    true,
    '{"is_24h": true, "security_level": "ENHANCED", "has_camera": true, "has_alarm": true, "temperature_zone": "AMBIENT", "slots_count": 24}',
    '2026-03-29 23:54:21.500272', '2026-04-16 18:49:35.860767'
),
-- ES - Madrid (ES-M - Madrid)
(
    'ES-MADRID-CENTRO-LK-001', 'ES-M', 'Madrid', 'Centro', '28013',
    40.41682, -3.70385, 'Europe/Madrid',
    'Calle Mayor', '25', 'Plaza Mayor',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    false, -- Inativo
    '{"is_24h": true, "security_level": "STANDARD", "has_camera": true, "has_alarm": false, "temperature_zone": "AMBIENT", "slots_count": 24}',
    '2026-03-29 23:54:21.510907', '2026-04-16 18:49:35.860767'
),
-- RJ - Rio de Janeiro (BR-RJ)
(
    'RJ-CAPITAL-CENTRO-LK-001', 'BR-RJ', 'Rio de Janeiro', 'Centro', '20040-009',
    -22.90685, -43.17295, 'America/Sao_Paulo',
    'Avenida Rio Branco', '45', 'Estação Central do Brasil',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    false, -- Inativo
    '{"is_24h": true, "security_level": "STANDARD", "has_camera": true, "has_alarm": false, "temperature_zone": "AMBIENT", "slots_count": 24}',
    '2026-03-29 23:54:21.520876', '2026-04-16 18:49:35.860767'
),
-- PR - Curitiba (BR-PR)
(
    'PR-CAPITAL-SANTAFELICIDADE-LK-001', 'BR-PR', 'Curitiba', 'Santa Felicidade', '82030-015',
    -25.4284, -49.27345, 'America/Sao_Paulo',
    'Rua Santa Felicidade', '950', 'Rua de Lazer',
    '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}',
    false, -- Inativo
    '{"is_24h": true, "security_level": "STANDARD", "has_camera": false, "has_alarm": false, "temperature_zone": "AMBIENT", "slots_count": 24}',
    '2026-03-29 23:54:21.530798', '2026-04-16 18:49:35.860767'
);

-- Verificar inserção
SELECT COUNT(*) as total_lockers FROM public.capability_locker_location;
SELECT province_code, COUNT(*) as count FROM public.capability_locker_location GROUP BY province_code ORDER BY province_code;