-- HOTFIX: Atualização de endereços, localização e horários de acesso para todos os lockers
-- Data: 2026-04-16
-- CORREÇÃO: Usando display_name como referência (já que external_id está NULL)

UPDATE public.lockers
SET 
    -- Endereços reais por locker
    address_line = CASE
        WHEN display_name = 'Osasco Centro - Locker 001' THEN 'Rua Antonio Aguilar'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 001' THEN 'Rua Marilú'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 002' THEN 'Rua Marilú'
        WHEN display_name = 'Alphaville Shopping - Locker Premium' THEN 'Alameda Rio Negro'
        WHEN display_name = 'Vila Olímpia - Locker Refrigerado' THEN 'Rua Fidêncio Ramos'
        WHEN display_name = 'Maia Centro - Locker 001' THEN 'Avenida Visconde de Barreiros'
        WHEN display_name = 'Guimarães Azurém - Locker Refrigerado' THEN 'Rua da Azurém'
        WHEN display_name = 'Lisboa - Locker Farmácia' THEN 'Avenida da Liberdade'
        WHEN display_name = 'Madrid Centro - Locker 001' THEN 'Calle Mayor'
        WHEN display_name = 'Rio Centro - Locker 001' THEN 'Avenida Rio Branco'
        WHEN display_name = 'Curitiba Santa Felicidade - Locker 001' THEN 'Rua Santa Felicidade'
        ELSE CONCAT('Rua Principal de ', city)
    END,
    
    address_number = CASE
        WHEN display_name = 'Osasco Centro - Locker 001' THEN '500'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 001' THEN '120'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 002' THEN '122'
        WHEN display_name = 'Alphaville Shopping - Locker Premium' THEN '500'
        WHEN display_name = 'Vila Olímpia - Locker Refrigerado' THEN '308'
        WHEN display_name = 'Maia Centro - Locker 001' THEN '250'
        WHEN display_name = 'Guimarães Azurém - Locker Refrigerado' THEN '45'
        WHEN display_name = 'Lisboa - Locker Farmácia' THEN '185'
        WHEN display_name = 'Madrid Centro - Locker 001' THEN '25'
        WHEN display_name = 'Rio Centro - Locker 001' THEN '45'
        WHEN display_name = 'Curitiba Santa Felicidade - Locker 001' THEN '950'
        ELSE 'S/N'
    END,
    
    address_extra = CASE
        WHEN display_name = 'Osasco Centro - Locker 001' THEN 'Em frente ao Mercado Municipal'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 001' THEN 'Próximo ao supermercado'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 002' THEN 'Ao lado da farmácia'
        WHEN display_name = 'Alphaville Shopping - Locker Premium' THEN 'Shopping Alphaville - Piso G1'
        WHEN display_name = 'Vila Olímpia - Locker Refrigerado' THEN 'Torre B - Térreo'
        WHEN display_name = 'Maia Centro - Locker 001' THEN 'Estação de Metro'
        WHEN display_name = 'Guimarães Azurém - Locker Refrigerado' THEN 'Universidade do Minho'
        WHEN display_name = 'Lisboa - Locker Farmácia' THEN 'Farmácia Central'
        WHEN display_name = 'Madrid Centro - Locker 001' THEN 'Plaza Mayor'
        WHEN display_name = 'Rio Centro - Locker 001' THEN 'Estação Central do Brasil'
        WHEN display_name = 'Curitiba Santa Felicidade - Locker 001' THEN 'Rua de Lazer'
        ELSE ''
    END,
    
    district = CASE
        WHEN display_name = 'Osasco Centro - Locker 001' THEN 'Centro'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 001' THEN 'Jardim Marilú'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 002' THEN 'Jardim Marilú'
        WHEN display_name = 'Alphaville Shopping - Locker Premium' THEN 'Alphaville'
        WHEN display_name = 'Vila Olímpia - Locker Refrigerado' THEN 'Vila Olímpia'
        WHEN display_name = 'Maia Centro - Locker 001' THEN 'Centro'
        WHEN display_name = 'Guimarães Azurém - Locker Refrigerado' THEN 'Azurém'
        WHEN display_name = 'Lisboa - Locker Farmácia' THEN 'Santo António'
        WHEN display_name = 'Madrid Centro - Locker 001' THEN 'Centro'
        WHEN display_name = 'Rio Centro - Locker 001' THEN 'Centro'
        WHEN display_name = 'Curitiba Santa Felicidade - Locker 001' THEN 'Santa Felicidade'
        ELSE city
    END,
    
    postal_code = CASE
        WHEN display_name = 'Osasco Centro - Locker 001' THEN '06086-040'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 001' THEN '06340-050'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 002' THEN '06340-050'
        WHEN display_name = 'Alphaville Shopping - Locker Premium' THEN '06454-000'
        WHEN display_name = 'Vila Olímpia - Locker Refrigerado' THEN '04545-004'
        WHEN display_name = 'Maia Centro - Locker 001' THEN '4470-157'
        WHEN display_name = 'Guimarães Azurém - Locker Refrigerado' THEN '4805-194'
        WHEN display_name = 'Lisboa - Locker Farmácia' THEN '1269-150'
        WHEN display_name = 'Madrid Centro - Locker 001' THEN '28013'
        WHEN display_name = 'Rio Centro - Locker 001' THEN '20040-009'
        WHEN display_name = 'Curitiba Santa Felicidade - Locker 001' THEN '82030-015'
        ELSE '00000-000'
    END,
    
    latitude = CASE
        WHEN display_name = 'Osasco Centro - Locker 001' THEN -23.532450
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 001' THEN -23.522620
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 002' THEN -23.522630
        WHEN display_name = 'Alphaville Shopping - Locker Premium' THEN -23.511850
        WHEN display_name = 'Vila Olímpia - Locker Refrigerado' THEN -23.590150
        WHEN display_name = 'Maia Centro - Locker 001' THEN 41.235720
        WHEN display_name = 'Guimarães Azurém - Locker Refrigerado' THEN 41.447150
        WHEN display_name = 'Lisboa - Locker Farmácia' THEN 38.722350
        WHEN display_name = 'Madrid Centro - Locker 001' THEN 40.416820
        WHEN display_name = 'Rio Centro - Locker 001' THEN -22.906850
        WHEN display_name = 'Curitiba Santa Felicidade - Locker 001' THEN -25.428400
        ELSE 0.000000
    END,
    
    longitude = CASE
        WHEN display_name = 'Osasco Centro - Locker 001' THEN -46.791620
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 001' THEN -46.835520
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 002' THEN -46.835530
        WHEN display_name = 'Alphaville Shopping - Locker Premium' THEN -46.877050
        WHEN display_name = 'Vila Olímpia - Locker Refrigerado' THEN -46.680250
        WHEN display_name = 'Maia Centro - Locker 001' THEN -8.619050
        WHEN display_name = 'Guimarães Azurém - Locker Refrigerado' THEN -8.291050
        WHEN display_name = 'Lisboa - Locker Farmácia' THEN -9.139350
        WHEN display_name = 'Madrid Centro - Locker 001' THEN -3.703850
        WHEN display_name = 'Rio Centro - Locker 001' THEN -43.172950
        WHEN display_name = 'Curitiba Santa Felicidade - Locker 001' THEN -49.273450
        ELSE 0.000000
    END,
    
    access_hours = '00:00-23:59',
    
    finding_instructions = CASE
        WHEN display_name = 'Osasco Centro - Locker 001' THEN 'Ao lado da praça central, próximo ao Banco do Brasil'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 001' THEN 'Entrada pela Rua Marilú, próximo à padaria'
        WHEN display_name = 'Carapicuíba JD Marilu - Locker 002' THEN '50m após o primeiro locker, do outro lado da rua'
        WHEN display_name = 'Alphaville Shopping - Locker Premium' THEN 'Acesso pelo estacionamento G1, próximo às escadas'
        WHEN display_name = 'Vila Olímpia - Locker Refrigerado' THEN 'Torre B, térreo - ao lado da lanchonete'
        WHEN display_name = 'Maia Centro - Locker 001' THEN 'Estação de Metro Maia - plataforma sentido centro'
        WHEN display_name = 'Guimarães Azurém - Locker Refrigerado' THEN 'Campus da Universidade - bloco C'
        WHEN display_name = 'Lisboa - Locker Farmácia' THEN 'Farmácia Central - interior à direita'
        WHEN display_name = 'Madrid Centro - Locker 001' THEN 'Plaza Mayor - entrada pela Calle Mayor 25'
        WHEN display_name = 'Rio Centro - Locker 001' THEN 'Estação Central - hall principal, próximo aos lockers antigos'
        WHEN display_name = 'Curitiba Santa Felicidade - Locker 001' THEN 'Rua Santa Felicidade, 950 - dentro do restaurante'
        ELSE 'Siga as placas indicativas do locker'
    END,
    
    updated_at = NOW()
    
WHERE display_name IN (
    'Osasco Centro - Locker 001',
    'Carapicuíba JD Marilu - Locker 001',
    'Carapicuíba JD Marilu - Locker 002',
    'Alphaville Shopping - Locker Premium',
    'Vila Olímpia - Locker Refrigerado',
    'Maia Centro - Locker 001',
    'Guimarães Azurém - Locker Refrigerado',
    'Lisboa - Locker Farmácia',
    'Madrid Centro - Locker 001',
    'Rio Centro - Locker 001',
    'Curitiba Santa Felicidade - Locker 001'
);

-- Verificar o resultado da atualização
SELECT 
    id,
    display_name,
    address_line,
    address_number,
    address_extra,
    district,
    city,
    state,
    postal_code,
    latitude,
    longitude,
    access_hours,
    finding_instructions
FROM public.lockers
WHERE display_name IN (
    'Osasco Centro - Locker 001',
    'Carapicuíba JD Marilu - Locker 001',
    'Carapicuíba JD Marilu - Locker 002',
    'Alphaville Shopping - Locker Premium',
    'Vila Olímpia - Locker Refrigerado',
    'Maia Centro - Locker 001',
    'Guimarães Azurém - Locker Refrigerado',
    'Lisboa - Locker Farmácia',
    'Madrid Centro - Locker 001',
    'Rio Centro - Locker 001',
    'Curitiba Santa Felicidade - Locker 001'
)
ORDER BY id;