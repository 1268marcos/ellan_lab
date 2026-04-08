
-- Inserts
-- First, ensure categories exist (you can query your existing ones)
-- INSERT INTO public.product_categories (id, name, default_temperature_zone, ...) VALUES ...;

-- Inserting products as per your example
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, metadata_json) VALUES
('cookie_laranja', 'Cookie de Laranja', 'Delicioso cookie artesanal com raspas de laranja.', 4850, 'BRL', 'BAKED_GOODS', 50, '{"origin": "São Paulo", "type": "cookie"}'),
('cookie_cenoura', 'Cookie de Cenoura', 'Cookie macio com pedaços de cenoura e cobertura de chocolate.', 4990, 'BRL', 'BAKED_GOODS', 55, '{"origin": "São Paulo", "type": "cookie"}'),
('cookie_chocolate', 'Cookie de Chocolate', 'Tradicional cookie com gotas de chocolate belga.', 5200, 'BRL', 'BAKED_GOODS', 60, '{"origin": "São Paulo", "type": "cookie"}'),
('bolo_cenoura', 'Bolo de Cenoura', 'Bolo fofo de cenoura com cobertura de chocolate.', 15000, 'BRL', 'CAKES_TARTS', 800, '{"origin": "São Paulo", "servings": 8}'),
('torta_limao', 'Torta de Limão', 'Torta refrescante de limão com merengue.', 18000, 'BRL', 'CAKES_TARTS', 750, '{"origin": "São Paulo", "servings": 8}'),
('bolo_rei', 'Bolo Rei', 'Traditional Portuguese King Cake with crystallized fruits.', 1485, 'EUR', 'CAKES_TARTS', 600, '{"origin": "Portugal", "seasonal": true}'),
('empada_bacalhau', 'Empada de Bacalhau', 'Savory codfish pie, a Portuguese classic.', 499, 'EUR', 'EMPADAS_PIES', 120, '{"origin": "Portugal", "type": "savory"}'),
('empada_frango', 'Empada de Frango', 'Classic chicken pie.', 295, 'EUR', 'EMPADAS_PIES', 110, '{"origin": "Portugal", "type": "savory"}'),
('bolo_chocolate_black_star', 'Bolo de Chocolate Black Star', 'Famous Black Star chocolate cake.', 1510, 'EUR', 'CAKES_TARTS', 200, '{"origin": "Portugal", "brand": "Black Star"}'),
('mini_cookie_chocolate', 'Mini Cookie de Chocolate Pack com 10', 'Pack of 10 mini chocolate chip cookies.', 1890, 'EUR', 'BAKED_GOODS', 250, '{"origin": "Portugal", "type": "mini_cookie", "quantity": 10}');

-- =====================================================
-- PRODUTOS - BRASIL (SP) - Categoria BAKED_GOODS
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('cookie_limao_siciliano', 'Cookie de Limão Siciliano', 'Cookie crocante com raspas de limão siciliano e gotas de chocolate branco', 4750, 'BRL', 'BAKED_GOODS', 45, 80, 80, 40, false, false, false, false, true, '{"origin": "São Paulo", "type": "cookie", "vegan": false, "gluten_free": false}', NOW(), NOW()),
('cookie_coco_queimado', 'Cookie de Coco Queimado', 'Cookie com coco tostado e pedaços de chocolate meio amargo', 4850, 'BRL', 'BAKED_GOODS', 48, 80, 80, 40, false, false, false, false, true, '{"origin": "São Paulo", "type": "cookie", "vegan": false, "gluten_free": false}', NOW(), NOW()),
('cookie_aveia_mel', 'Cookie de Aveia e Mel', 'Cookie saudável com aveia, mel e castanhas', 4650, 'BRL', 'BAKED_GOODS', 50, 80, 80, 40, false, false, false, false, true, '{"origin": "São Paulo", "type": "cookie", "vegan": false, "gluten_free": false, "healthy": true}', NOW(), NOW()),
('cookie_chocolate_caramelado', 'Cookie de Chocolate Caramelado', 'Cookie com chocolate belga e pedaços de caramelo', 5350, 'BRL', 'BAKED_GOODS', 55, 85, 85, 45, false, false, false, false, true, '{"origin": "São Paulo", "type": "cookie", "limited_edition": true}', NOW(), NOW()),
('cookie_red_velvet', 'Cookie Red Velvet', 'Cookie red velvet com gotas de chocolate branco', 5100, 'BRL', 'BAKED_GOODS', 50, 80, 80, 40, false, false, false, false, true, '{"origin": "São Paulo", "type": "cookie", "seasonal": true}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - BRASIL (SP) - Categoria CAKES_TARTS
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('bolo_ninho_morango', 'Bolo Ninho com Morango', 'Bolo de leite ninho recheado com morango e cobertura de leite ninho', 16500, 'BRL', 'CAKES_TARTS', 850, 200, 150, 200, false, false, false, false, true, '{"origin": "São Paulo", "servings": 8, "refrigerated": true}', NOW(), NOW()),
('bolo_prestigio', 'Bolo Prestígio', 'Bolo de chocolate com recheio de coco e cobertura de chocolate', 15500, 'BRL', 'CAKES_TARTS', 820, 200, 150, 200, false, false, false, false, true, '{"origin": "São Paulo", "servings": 8, "refrigerated": true}', NOW(), NOW()),
('torta_morango_chocolate', 'Torta de Morango com Chocolate', 'Torta com base de chocolate, mousse de morango e cobertura de chocolate', 19500, 'BRL', 'CAKES_TARTS', 780, 220, 140, 220, false, false, false, false, true, '{"origin": "São Paulo", "servings": 8, "refrigerated": true}', NOW(), NOW()),
('cheesecake_frutas_vermelhas', 'Cheesecake de Frutas Vermelhas', 'Cheesecake cremoso com calda de frutas vermelhas', 21000, 'BRL', 'CAKES_TARTS', 750, 200, 120, 200, false, false, false, false, true, '{"origin": "São Paulo", "servings": 8, "refrigerated": true}', NOW(), NOW()),
('torta_alema', 'Torta Alemã', 'Torta com camadas de biscoito e creme de manteiga com chocolate', 17500, 'BRL', 'CAKES_TARTS', 800, 200, 130, 200, false, false, false, false, true, '{"origin": "São Paulo", "servings": 8, "refrigerated": true}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - BRASIL (SP) - Categoria SANDWICHES
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('sanduiche_frango_cheddar', 'Sanduíche de Frango com Cheddar', 'Pão brioche, frango desfiado, cheddar derretido, alface e tomate', 2850, 'BRL', 'SANDWICHES', 180, 150, 80, 150, false, false, false, false, false, '{"origin": "São Paulo", "type": "sandwich", "refrigerated": true}', NOW(), NOW()),
('sanduiche_vegano', 'Sanduíche Vegano', 'Pão integral, hambúrguer de grão-de-bico, alface, tomate e molho especial', 2950, 'BRL', 'SANDWICHES', 170, 150, 80, 150, false, false, false, false, false, '{"origin": "São Paulo", "type": "sandwich", "vegan": true, "refrigerated": true}', NOW(), NOW()),
('wrap_peru_creamcheese', 'Wrap de Peru com Cream Cheese', 'Wrap integral, peito de peru, cream cheese, rúcula e tomate seco', 3200, 'BRL', 'SANDWICHES', 190, 180, 60, 120, false, false, false, false, false, '{"origin": "São Paulo", "type": "wrap", "refrigerated": true}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - BRASIL (SP) - Categoria BEVERAGES_COLD
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('suco_laranja_limao', 'Suco de Laranja com Limão', 'Suco natural de laranja com toque de limão', 1250, 'BRL', 'BEVERAGES_COLD', 350, 60, 60, 60, false, false, false, false, false, '{"origin": "São Paulo", "volume_ml": 300, "refrigerated": true}', NOW(), NOW()),
('suco_detox_verde', 'Suco Detox Verde', 'Couve, limão, gengibre, maçã e pepino', 1450, 'BRL', 'BEVERAGES_COLD', 350, 60, 60, 60, false, false, false, false, false, '{"origin": "São Paulo", "volume_ml": 300, "vegan": true, "refrigerated": true}', NOW(), NOW()),
('smoothie_manga_maracuja', 'Smoothie de Manga com Maracujá', 'Smoothie cremoso de manga, maracujá e leite vegetal', 1650, 'BRL', 'BEVERAGES_COLD', 400, 65, 65, 65, false, false, false, false, false, '{"origin": "São Paulo", "volume_ml": 350, "vegan": true, "refrigerated": true}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - BRASIL (SP) - Categoria HEALTH_SUPPLEMENTS
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('whey_protein_900g', 'Whey Protein 900g - Chocolate', 'Suplemento proteico de alto valor biológico', 18900, 'BRL', 'HEALTH_SUPPLEMENTS', 1050, 150, 220, 100, false, false, false, false, false, '{"origin": "Brasil", "brand": "Growth", "flavor": "chocolate", "weight_g": 900}', NOW(), NOW()),
('colageno_verisol', 'Colágeno Verisol 210g', 'Colágeno hidrolisado para pele e articulações', 8900, 'BRL', 'HEALTH_SUPPLEMENTS', 260, 100, 150, 100, false, false, false, false, false, '{"origin": "Brasil", "brand": "Vital Proteins", "weight_g": 210}', NOW(), NOW()),
('multivitaminico', 'Multivitamínico Completo - 60 cápsulas', 'Multivitamínico com minerais essenciais', 4500, 'BRL', 'HEALTH_SUPPLEMENTS', 80, 60, 110, 60, false, false, false, false, false, '{"origin": "Brasil", "brand": "Now", "quantity": 60}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - BRASIL (SP) - Categoria ENERGY_DRINKS
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('red_bull_250ml', 'Red Bull 250ml', 'Bebida energética tradicional', 1090, 'BRL', 'ENERGY_DRINKS', 270, 55, 130, 55, true, false, false, false, false, '{"origin": "Áustria", "volume_ml": 250, "requires_age_verification": true}', NOW(), NOW()),
('monster_473ml', 'Monster Energy 473ml', 'Bebida energética sabor original', 1250, 'BRL', 'ENERGY_DRINKS', 490, 65, 170, 65, true, false, false, false, false, '{"origin": "EUA", "volume_ml": 473, "requires_age_verification": true}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - PORTUGAL (PT) - Categoria BAKED_GOODS
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('pastel_nata', 'Pastel de Nata', 'Tradicional pastel de nata português', 125, 'EUR', 'BAKED_GOODS', 60, 70, 40, 70, false, false, false, false, true, '{"origin": "Portugal", "type": "pastry", "refrigerated": false}', NOW(), NOW()),
('queijada_sintra', 'Queijada de Sintra', 'Doce conventual de queijo e canela', 150, 'EUR', 'BAKED_GOODS', 55, 65, 30, 65, false, false, false, false, true, '{"origin": "Sintra", "type": "pastry", "refrigerated": false}', NOW(), NOW()),
('travesseiro_sintra', 'Travesseiro de Sintra', 'Massa folhada recheada com creme de amêndoa', 185, 'EUR', 'BAKED_GOODS', 70, 80, 40, 60, false, false, false, false, true, '{"origin": "Sintra", "type": "pastry", "refrigerated": false}', NOW(), NOW()),
('croissant_amendoa', 'Croissant de Amêndoa', 'Croissant folhado com recheio de amêndoa', 195, 'EUR', 'BAKED_GOODS', 85, 120, 60, 80, false, false, false, false, true, '{"origin": "Portugal", "type": "croissant", "refrigerated": false}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - PORTUGAL (PT) - Categoria SANDWICHES
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('prego_no_pao', 'Prego no Pão', 'Bife grelhado no pão com alho e molho', 425, 'EUR', 'SANDWICHES', 220, 160, 85, 160, false, false, false, false, false, '{"origin": "Portugal", "type": "sandwich", "refrigerated": true}', NOW(), NOW()),
('bifana', 'Bifana', 'Sanduíche de carne de porco marinada', 390, 'EUR', 'SANDWICHES', 210, 160, 85, 160, false, false, false, false, false, '{"origin": "Portugal", "type": "sandwich", "refrigerated": true}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - PORTUGAL (PT) - Categoria ALCOHOLIC_BEER
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('super_bock_33cl', 'Super Bock 33cl', 'Cerveja portuguesa clássica', 125, 'EUR', 'ALCOHOLIC_BEER', 350, 65, 130, 65, true, true, false, false, false, '{"origin": "Portugal", "volume_ml": 330, "alcohol_percent": 5.0, "requires_age_verification": true}', NOW(), NOW()),
('sagres_33cl', 'Sagres 33cl', 'Cerveja portuguesa refrescante', 125, 'EUR', 'ALCOHOLIC_BEER', 350, 65, 130, 65, true, true, false, false, false, '{"origin": "Portugal", "volume_ml": 330, "alcohol_percent": 5.0, "requires_age_verification": true}', NOW(), NOW()),
('super_bock_stout', 'Super Bock Stout 33cl', 'Cerveja preta encorpada', 165, 'EUR', 'ALCOHOLIC_BEER', 350, 65, 130, 65, true, true, false, false, false, '{"origin": "Portugal", "volume_ml": 330, "alcohol_percent": 5.5, "requires_age_verification": true}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - PORTUGAL (PT) - Categoria ALCOHOLIC_WINE
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('vinho_verde_branco', 'Vinho Verde Branco 750ml', 'Vinho branco leve e fresco', 495, 'EUR', 'ALCOHOLIC_WINE', 1250, 75, 300, 75, true, true, false, false, true, '{"origin": "Portugal", "volume_ml": 750, "alcohol_percent": 11.0, "requires_age_verification": true, "type": "white"}', NOW(), NOW()),
('vinho_porto', 'Vinho do Porto 750ml', 'Vinho licoroso fortificado', 1850, 'EUR', 'ALCOHOLIC_WINE', 1350, 80, 320, 80, true, true, false, false, true, '{"origin": "Douro", "volume_ml": 750, "alcohol_percent": 19.0, "requires_age_verification": true, "type": "port"}', NOW(), NOW()),
('vinho_tinto_dao', 'Vinho Tinto Dão 750ml', 'Vinho tinto encorpado da região do Dão', 895, 'EUR', 'ALCOHOLIC_WINE', 1280, 75, 300, 75, true, true, false, false, true, '{"origin": "Dão", "volume_ml": 750, "alcohol_percent": 13.5, "requires_age_verification": true, "type": "red"}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - PORTUGAL (PT) - Categoria HEALTH_SUPPLEMENTS
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('whey_myprotein_1kg', 'Whey Protein 1kg - Baunilha', 'Suplemento proteico de alta qualidade', 3590, 'EUR', 'HEALTH_SUPPLEMENTS', 1150, 160, 230, 110, false, false, false, false, false, '{"origin": "Reino Unido", "brand": "MyProtein", "flavor": "vanilla", "weight_g": 1000}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - CATEGORIA ELECTRONICS_WEARABLES
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('apple_watch_se', 'Apple Watch SE GPS 40mm', 'Smartwatch com monitor cardíaco e GPS', 34900, 'BRL', 'ELECTRONICS_WEARABLES', 150, 40, 40, 10, false, false, false, false, true, '{"origin": "China", "brand": "Apple", "warranty_months": 12}', NOW(), NOW()),
('galaxy_watch_6', 'Samsung Galaxy Watch 6 44mm', 'Smartwatch com bioimpedância', 29900, 'BRL', 'ELECTRONICS_WEARABLES', 160, 44, 44, 10, false, false, false, false, true, '{"origin": "Coreia", "brand": "Samsung", "warranty_months": 12}', NOW(), NOW()),
('airpods_pro', 'AirPods Pro 2', 'Fones com cancelamento de ruído ativo', 22900, 'BRL', 'ELECTRONICS_AUDIO', 45, 60, 45, 45, false, false, false, false, true, '{"origin": "China", "brand": "Apple", "wireless": true}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - CATEGORIA BEAUTY_SKINCARE
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('protetor_solar_50', 'Protetor Solar FPS 50 200ml', 'Proteção solar de amplo espectro', 8900, 'BRL', 'BEAUTY_SKINCARE', 240, 60, 160, 40, false, false, false, false, true, '{"origin": "Brasil", "brand": "La Roche-Posay", "spf": 50}', NOW(), NOW()),
('serum_vitamina_c', 'Sérum Vitamina C 30ml', 'Sérum antioxidante e clareador', 15900, 'BRL', 'BEAUTY_SKINCARE', 80, 35, 95, 35, false, false, false, false, true, '{"origin": "França", "brand": "Vichy", "volume_ml": 30}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - CATEGORIA PETS_DOG e PETS_CAT
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('racao_golden_10kg', 'Ração Golden Fórmula para Cães Adultos 10kg', 'Ração completa e balanceada', 18900, 'BRL', 'PETS_DOG', 10100, 400, 600, 150, false, false, false, false, false, '{"origin": "Brasil", "brand": "Golden", "weight_kg": 10, "pet_type": "dog"}', NOW(), NOW()),
('racao_premier_2kg', 'Ração Premier para Gatos Castrados 2kg', 'Ração específica para gatos castrados', 6900, 'BRL', 'PETS_CAT', 2100, 250, 400, 80, false, false, false, false, false, '{"origin": "Brasil", "brand": "Premier", "weight_kg": 2, "pet_type": "cat"}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - CATEGORIA GIFT_CARDS_DIGITAL
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('giftcard_spotify', 'Gift Card Spotify Premium 3 meses', 'Voucher para 3 meses de Spotify Premium', 4490, 'BRL', 'GIFT_CARDS_DIGITAL', 0, 0, 0, 0, false, false, false, false, false, '{"origin": "Digital", "brand": "Spotify", "type": "digital", "delivery": "email"}', NOW(), NOW()),
('giftcard_netflix', 'Gift Card Netflix R$50', 'Voucher de R$50 para Netflix', 5000, 'BRL', 'GIFT_CARDS_DIGITAL', 0, 0, 0, 0, false, false, false, false, false, '{"origin": "Digital", "brand": "Netflix", "type": "digital", "delivery": "email"}', NOW(), NOW());

-- =====================================================
-- PRODUTOS - CATEGORIA MEDICAL_EQUIPMENT
-- =====================================================
INSERT INTO public.products (id, name, description, amount_cents, currency, category_id, weight_g, width_mm, height_mm, depth_mm, requires_age_verification, requires_id_check, requires_signature, is_hazardous, is_fragile, metadata_json, created_at, updated_at) VALUES
('glicosimetro', 'Glicosímetro Digital', 'Medidor digital de glicose', 12900, 'BRL', 'MEDICAL_EQUIPMENT', 120, 80, 120, 30, false, false, false, false, true, '{"origin": "China", "brand": "Accu-Chek", "anvisa_registry": "123456789"}', NOW(), NOW()),
('medidor_pressao', 'Medidor de Pressão Digital', 'Medidor de pressão arterial de braço', 15900, 'BRL', 'MEDICAL_EQUIPMENT', 350, 140, 100, 140, false, false, false, false, true, '{"origin": "China", "brand": "Omron", "anvisa_registry": "987654321"}', NOW(), NOW());

