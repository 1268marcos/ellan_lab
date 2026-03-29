# completo (dados + produtos)
# 01_source/order_pickup_service/app/core/locker_seed.py
"""
Seed inicial completo: Lockers, Operadores, Categorias de Produtos e Configurações.

Explicação das adições
BAKED_GOODS: Para cookies e bolos mais estáveis (sem creme), permitidos em lockers normais.
CAKES_TARTS: Bolos e tortas doces com recheio/creme – precisam de refrigeração para evitar derretimento ou mofo.
EMPADAS_PIES: Empadas (salgadas ou doces) – semi-perecíveis, exigem frio.
FOOD_DRY e SNACKS: Genéricos para itens secos/embalados do seu negócio.
Mantive campos como requires_temp_control para lockers especiais (ex: "refrigerated" ou "none").

Medicamentos: restrição crítica: medicamentos, especialmente os que requerem refrigeração, não devem ser enviados por correio ou armazenados em lockers padrão

Itens Proibidos e de Alto risco:
Dinheiro em Espécie: Mesmo em pequenas quantias, não é recomendado. Lockers não são cofres bancários. 
Animais Vivos: Totalmente proibido por questões éticas e sanitárias. 
Documentos Roubados ou Falsificados: Proibidos por lei.

PHARMACY, dividida em novas categorias (ANVISA e INFARMED):
PHARMACY_PRESCRIPTION_MEDS (Medicamentos com Prescrição): Deve ser proibido em lockers padrão.  Esses itens são de alto risco, muitas vezes controlados, e podem exigir temperaturas específicas. A entrega deve ser feita com assinatura e verificação de identidade, geralmente em mãos.
PHARMACY_OTC_MEDS (Medicamentos sem Prescrição - Over-the-Counter): Pode ser permitido em lockers padrão, como analgésicos comuns, vitaminas e medicamentos para resfriado.  A exigência de ID pode ser opcional, dependendo do valor e do fornecedor. 
Anterior para Farmácia - {"category": "PHARMACY", "allowed": True, "requires_id": False},

"""

from sqlalchemy.orm import Session
from app.models.locker import Locker, LockerSlotConfig, LockerOperator
from app.models.product_locker_config import ProductLockerConfig, ProductCategory
from datetime import datetime, timezone


def log(msg: str):
    print(f"[SEED] {msg}")


def seed_product_categories(db: Session):
    """Popula categorias mestre de produtos - Versão ampliada"""
    categories = [
        # ============================================================
        # ELETRÔNICOS E TECNOLOGIA
        # ============================================================
        ProductCategory(
            id="ELECTRONICS",
            name="Eletrônicos",
            description="Smartphones, tablets, notebooks, acessórios eletrônicos",
            default_temperature_zone="AMBIENT",
            default_security_level="ENHANCED",
            is_hazardous=False,
            # max_value=500000,  # R$ 5.000,00
            # requires_id=True,
        ),
        ProductCategory(
            id="ELECTRONICS_ACCESSORIES",
            name="Acessórios Eletrônicos",
            description="Fones de ouvido, cabos, carregadores, capas",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            # max_value=30000,  # R$ 300,00
        ),
        
        # ============================================================
        # MODA E VESTUÁRIO
        # ============================================================
        ProductCategory(
            id="FASHION",
            name="Moda e Vestuário",
            description="Roupas, calçados, acessórios de moda",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="FASHION_LUXURY",
            name="Moda Luxo",
            description="Grife, designer, edições limitadas",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            # max_value=500000,  # R$ 5.000,00
            # requires_id=True,
        ),
        ProductCategory(
            id="FOOTWEAR",
            name="Calçados",
            description="Sapatos, tênis, sandálias, botas",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="ACCESSORIES",
            name="Acessórios",
            description="Bolsas, cintos, óculos, bijuterias",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        
        # ============================================================
        # BELEZA E HIGIENE
        # ============================================================
        ProductCategory(
            id="BEAUTY",
            name="Beleza e Cosméticos",
            description="Maquiagem, skincare, perfumes, produtos de beleza",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="BEAUTY_PREMIUM",
            name="Beleza Premium",
            description="Perfumes importados, cosméticos de luxo",
            default_temperature_zone="AMBIENT",
            default_security_level="ENHANCED",
            is_hazardous=False,
            # max_value=100000,  # R$ 1.000,00
            # requires_id=True,
        ),
        ProductCategory(
            id="HYGIENE",
            name="Higiene Pessoal",
            description="Sabonetes, shampoos, cremes, itens de banho",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="ORAL_HYGIENE",
            name="Higiene Bucal",
            description="Escovas de dente, pastas, fio dental, enxaguante",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        
        # ============================================================
        # SAÚDE E FARMÁCIA
        # ============================================================
        ProductCategory(
            id="PHARMACY_OTC_MEDS",
            name="Medicamentos sem Prescrição",
            description="Medicamentos isentos de prescrição (OTC)",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=True,
            # requires_id=False,
        ),
        ProductCategory(
            id="PHARMACY_PRESCRIPTION_MEDS",
            name="Medicamentos com Prescrição",
            description="Medicamentos que exigem receita médica",
            default_temperature_zone="REFRIGERATED",
            default_security_level="HIGH",
            is_hazardous=False,
            requires_age_verification=True,
            # requires_id=True,
            # requires_signature=True,
        ),
        ProductCategory(
            id="MEDICAL_SUPPLIES",
            name="Suprimentos Médicos",
            description="Curativos, seringas, equipamentos médicos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="VITAMINS_SUPPLEMENTS",
            name="Vitaminas e Suplementos",
            description="Suplementos alimentares, vitaminas, minerais",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        
        # ============================================================
        # ALIMENTOS E BEBIDAS
        # ============================================================
        ProductCategory(
            id="FOOD_PERISHABLE",
            name="Alimentos Perecíveis",
            description="Frutas, verduras, laticínios, carnes frescas",
            default_temperature_zone="REFRIGERATED",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="FOOD_FROZEN",
            name="Alimentos Congelados",
            description="Pizzas congeladas, sorvetes, vegetais congelados",
            default_temperature_zone="FROZEN",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="BAKED_GOODS",
            name="Produtos de Panificação",
            description="Pães, biscoitos, bolos secos, cookies",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            # max_value=20000,  # R$ 200,00
        ),
        ProductCategory(
            id="CAKES_TARTS",
            name="Bolos e Tortas Cremosos",
            description="Bolos com recheio cremoso, tortas, sobremesas refrigeradas",
            default_temperature_zone="REFRIGERATED",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="EMPADAS_PIES",
            name="Empadas e Salgados Assados",
            description="Empadas, esfihas, salgados assados recheados",
            default_temperature_zone="REFRIGERATED",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="FOOD_DRY",
            name="Alimentos Não Perecíveis",
            description="Arroz, feijão, massas, enlatados, biscoitos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            # max_value=15000,  # R$ 150,00
        ),
        ProductCategory(
            id="SNACKS",
            name="Snacks e Petiscos",
            description="Salgadinhos, chocolates, balas, barras de cereal",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="BEVERAGES",
            name="Bebidas",
            description="Refrigerantes, sucos, águas, energéticos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            # max_value=10000,  # R$ 100,00
        ),
        ProductCategory(
            id="BEVERAGES_ALCOHOLIC",
            name="Bebidas Alcoólicas",
            description="Cervejas, vinhos, destilados",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=True,
            # max_value=50000,  # R$ 500,00
        ),
        
        # ============================================================
        # DOCUMENTOS E PAPELARIA
        # ============================================================
        ProductCategory(
            id="DOCUMENTS",
            name="Documentos",
            description="Contratos, certificados, documentos oficiais",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            # requires_id=True,
            # requires_signature=True,
        ),
        ProductCategory(
            id="STATIONERY",
            name="Papelaria",
            description="Cadernos, canetas, material escolar",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        
        # ============================================================
        # CASA E UTILIDADES
        # ============================================================
        ProductCategory(
            id="HOME_APPLIANCES",
            name="Eletrodomésticos",
            description="Pequenos eletrodomésticos, liquidificadores, air fryer",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="HOME_DECOR",
            name="Decoração",
            description="Quadros, velas, objetos decorativos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="CLEANING_SUPPLIES",
            name="Produtos de Limpeza",
            description="Detergentes, desinfetantes, produtos químicos domésticos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=True,  # Produtos químicos
        ),
        
        # ============================================================
        # BEBÊS E CRIANÇAS
        # ============================================================
        ProductCategory(
            id="BABY_PRODUCTS",
            name="Produtos para Bebês",
            description="Fraldas, mamadeiras, roupas de bebê",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="BABY_FOOD",
            name="Alimentos Infantis",
            description="Papinhas, fórmulas infantis, comidas de bebê",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="TOYS",
            name="Brinquedos",
            description="Brinquedos e jogos infantis",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        
        # ============================================================
        # ESPORTES E LAZER
        # ============================================================
        ProductCategory(
            id="SPORTS_EQUIPMENT",
            name="Equipamentos Esportivos",
            description="Bolas, raquetes, acessórios para esportes",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="SUPPLEMENTS_SPORTS",
            name="Suplementos Esportivos",
            description="Whey protein, creatina, pré-treino",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        
        # ============================================================
        # PET SHOP
        # ============================================================
        ProductCategory(
            id="PET_SUPPLIES",
            name="Produtos para Pets",
            description="Rações, brinquedos, acessórios para animais",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="PET_FOOD",
            name="Alimentos para Pets",
            description="Ração seca e úmida, petiscos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        
        # ============================================================
        # ALTO VALOR E SEGURANÇA
        # ============================================================
        ProductCategory(
            id="HIGH_VALUE",
            name="Alto Valor",
            description="Joias, relógios de luxo, itens colecionáveis",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            # max_value=1000000,  # R$ 10.000,00
            # requires_id=True,
            # requires_signature=True,
        ),
        ProductCategory(
            id="JEWELRY",
            name="Joias e Semijoias",
            description="Anéis, colares, pulseiras, brincos",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            # max_value=500000,  # R$ 5.000,00
            # requires_id=True,
        ),
        ProductCategory(
            id="WATCHES",
            name="Relógios",
            description="Relógios de pulso, smartwatches",
            default_temperature_zone="AMBIENT",
            default_security_level="ENHANCED",
            is_hazardous=False,
        ),
        
        # ============================================================
        # PRODUTOS ESPECIAIS
        # ============================================================
        ProductCategory(
            id="HAZARDOUS",
            name="Materiais Perigosos",
            description="Produtos químicos, inflamáveis, tóxicos",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=True,
        ),
        ProductCategory(
            id="MONEY",
            name="Dinheiro em Espécie",
            description="Cédulas, moedas, valores monetários",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            # requires_id=True,
            # requires_signature=True,
        ),
        ProductCategory(
            id="ANIMALS_ALIVE",
            name="Animais Vivos",
            description="Pets, animais de pequeno porte",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            # requires_id=True,
            # requires_signature=True,
        ),
        ProductCategory(
            id="WEAPONS",
            name="Armas e Munições",
            description="Armas de fogo, munições, armas brancas",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=True,
            # requires_id=True,
            # requires_signature=True,
            # requires_age_verification=True,
        ),
        
        # ============================================================
        # SERVIÇOS E VOUCHERS
        # ============================================================
        ProductCategory(
            id="GIFT_CARDS",
            name="Vouchers e Gift Cards",
            description="Cartões presente, vales compras",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="TICKETS",
            name="Ingressos",
            description="Ingressos para shows, eventos, viagens",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
    ]
    
    for cat in categories:
        existing = db.query(ProductCategory).filter(ProductCategory.id == cat.id).first()
        if not existing:
            db.add(cat)
            log(f"Categoria adicionada: {cat.id} - {cat.name}")
    
    db.commit()
    log(f"Seed concluído: {len([c for c in categories if not db.query(ProductCategory).filter(ProductCategory.id == c.id).first()])} novas categorias inseridas")


def seed_operators(db: Session):
    """Popula operadores de lockers - Versão ampliada para múltiplos países."""
    
    operators = [
        # ============================================================
        # OPERADORES BRASIL
        # ============================================================
        LockerOperator(
            id="OP-ELLAN-001",
            name="Ellan Lab Operações",
            document="00.000.000/0001-00",
            email="contato@ellanlab.com",
            phone="+5511981479374",
            operator_type="LOGISTICS",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-LOGGI-001",
            name="Loggi Partner",
            document="11.111.111/0001-11",
            email="contato@loggi.com",
            phone="+5511912340001",
            operator_type="LOGISTICS",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-SHOP-001",
            name="E-commerce Partner",
            document="22.222.222/0001-22",
            email="contato@shop.com",
            phone="+5511912340002",            
            operator_type="ECOMMERCE",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-PHARMA-001",
            name="Drogaria Partner",
            document="33.333.333/0001-33",
            email="contato@drogaria.com",
            phone="+5511912340002",             
            operator_type="ECOMMERCE",
            country="BR",
            active=True,
            commission_rate=0.02,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-MELI-001",
            name="Mercado Livre",
            document="88.888.888/0001-88",
            email="contato@meli.com",
            phone="+5511912340003",            
            operator_type="ECOMMERCE",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-ATACADAO-001",
            name="Atacadão Partner",
            document="44.444.444/0001-44",
            email="contato@atacadao.com,br",
            phone="+5511912340011",            
            operator_type="ECOMMERCE",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-CORREIOS-001",
            name="Correios Brasil",
            document="34.028.316/0001-03",
            email="contato@correios.com.br",
            phone="+5511912340111",
            operator_type="LOGISTICS",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-SHOPEE-001",
            name="Shopee Brasil",
            document="28.797.454/0001-64",
            email="contato@shopee.com.br",
            phone="+5511912341111",            
            operator_type="ECOMMERCE",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-AMAZON-001",
            name="Amazon Brasil",
            document="15.345.654/0001-00",
            email="contato@amazon.com.br",
            phone="+5511912340022",            
            operator_type="ECOMMERCE",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-MAGALU-001",
            name="Magazine Luiza",
            document="47.960.950/0001-87",
            email="contato@magalu.com.br",
            phone="+5511912340222",            
            operator_type="ECOMMERCE",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-VIAVAREJO-001",
            name="Via Varejo (Casas Bahia)",
            document="61.585.865/0001-51",
            email="contato@viavarejo.com.br",
            phone="+5511912342222",            
            operator_type="ECOMMERCE",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-RAPPI-001",
            name="Rappi Brasil",
            document="29.773.213/0001-06",
            email="contato@rappi.com.br",
            phone="+5511912340033",            
            operator_type="DELIVERY",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        LockerOperator(
            id="OP-IFOOD-001",
            name="iFood",
            document="14.381.582/0001-30",
            email="contato@ifood.com.br",
            phone="+5511912343333",
            operator_type="DELIVERY",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
        ),
        
        # ============================================================
        # OPERADORES PORTUGAL
        # ============================================================
        LockerOperator(
            id="OP-MOL-001",
            name="Marcos & Osineide Lda",
            document="518.474.828",
            email="pesquisa@molrealestate.pt",
            phone="+351915397725",
            operator_type="ECOMMERCE",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-LIDL-001",
            name="Lidl Portugal",
            document="502.502.502",
            email="contato@lidl.com",
            phone="+351900900900",
            operator_type="ECOMMERCE",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-SANTOBURACO-001",
            name="Comércio de Alimentos Lda",
            document="503.503.503",
            email="contato@santoburaco.pt",
            phone="+351900900901",
            operator_type="ECOMMERCE",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-EGIRO-001",
            name="É Giro Pastelaria Artesanal Lda",
            document="504.504.504",
            email="contato@egiro.pt",
            phone="+351900900922",            
            operator_type="ECOMMERCE",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-WORTEN-001",
            name="Worten Portugal",
            document="501.501.501",
            email="contato@worten.pt",
            phone="+351900900944",
            operator_type="ECOMMERCE",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-CTTPT-001",
            name="CTT Correios Portugal",
            document="501.082.977",
            email="contato@ctt.pt",
            phone="+351900900955",
            operator_type="LOGISTICS",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-DPD-001",
            name="DPD Portugal",
            document="502.789.456",
            email="contato@dpd.pt",
            phone="+351900900966",
            operator_type="LOGISTICS",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-UPS-001",
            name="UPS Portugal",
            document="503.456.789",
            email="contato@ups.pt",
            phone="+351900900977",
            operator_type="LOGISTICS",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-GLS-001",
            name="GLS Portugal",
            document="504.567.890",
            email="contato@gls.pt",
            phone="+351900900988",
            operator_type="LOGISTICS",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-UBER-001",
            name="Uber Eats Portugal",
            document="505.678.901",
            email="contato@ubereats.pt",
            phone="+351900900999",
            operator_type="DELIVERY",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-GLOVO-001",
            name="Glovo Portugal",
            document="506.789.012",
            email="contato@glovo.pt",
            phone="+351900911900",
            operator_type="DELIVERY",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-BOLT-001",
            name="Bolt Food Portugal",
            document="507.890.123",
            email="contato@bolt.pt",
            phone="+351900922900",
            operator_type="DELIVERY",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-FNAC-001",
            name="Fnac Portugal",
            document="508.901.234",
            email="contato@fnac.pt",
            phone="+351900944901",
            operator_type="ECOMMERCE",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-PINGODOECE-001",
            name="Pingo Doce",
            document="509.012.345",
            email="contato@pingodoce.pt",
            phone="+351900955900",
            operator_type="ECOMMERCE",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-CONTINENTE-001",
            name="Continente",
            document="510.123.456",
            email="contato@continente.pt",
            phone="+351900966966",
            operator_type="ECOMMERCE",
            country="PT",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        
        # ============================================================
        # OPERADORES ESPANHA (NOVOS)
        # ============================================================
        LockerOperator(
            id="OP-SEUR-001",
            name="Seur España",
            document="B-78945612",
            email="contato@seur.es",
            phone="+3493900900900",
            operator_type="LOGISTICS",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-MRW-001",
            name="MRW España",
            document="B-45612378",
            email="contato@mrw.es",
            phone="+3493900900901",
            operator_type="LOGISTICS",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-DHL-ES-001",
            name="DHL Spain",
            document="B-12378945",
            email="contato@dhl.es",
            phone="+3493900900911",
            operator_type="LOGISTICS",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-CORREOS-ES-001",
            name="Correos España",
            document="Q-2849001-B",
            email="contato@correos.es",
            phone="+3493900922922",
            operator_type="LOGISTICS",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-AMAZON-ES-001",
            name="Amazon España",
            document="B-85924956",
            email="contato@amazon.es",
            phone="+3493900900999",
            operator_type="ECOMMERCE",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-ELCORTE-001",
            name="El Corte Inglés",
            document="B-28011890",
            email="contato@elcorteingles.es",
            phone="+3493900933955",
            operator_type="ECOMMERCE",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-MEDIA-ES-001",
            name="MediaMarkt España",
            document="B-84192661",
            email="contato@mediamarkt.es",
            phone="+3493900977977",
            operator_type="ECOMMERCE",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-ZARA-001",
            name="Inditex (Zara)",
            document="A-15008200",
            email="contato@zara.es",
            phone="+3493955955900",
            operator_type="ECOMMERCE",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-GLOVO-ES-001",
            name="Glovo España",
            document="B-66802903",
            email="contato@glovo.es",
            phone="+3493900912912",
            operator_type="DELIVERY",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-JUSTEAT-ES-001",
            name="Just Eat España",
            document="B-85838351",
            email="contato@justeat.es",
            phone="+3493900934923",
            operator_type="DELIVERY",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-CARREFOUR-ES-001",
            name="Carrefour España",
            document="A-28362517",
            email="contato@carrefour.es",
            phone="+3493900978956",
            operator_type="ECOMMERCE",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-MERCABAR-ES-001",
            name="Mercadona España",
            document="A-46103872",
            email="contato@mercadona.es",
            phone="+3493900928964",
            operator_type="ECOMMERCE",
            country="ES",
            active=True,
            commission_rate=0.02,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-PACK-001",
            name="Packlink Spain",
            document="B-86641865",
            email="contato@packlink.es",
            phone="+3493912912900",
            operator_type="LOGISTICS",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        LockerOperator(
            id="OP-TOUS-001",
            name="Tous Joyeros",
            document="B-60457690",
            email="contato@tousjoyeros.es",
            phone="+3493900993993",
            operator_type="ECOMMERCE",
            country="ES",
            active=True,
            commission_rate=0.01,
            currency="EUR",
        ),
        
        # ============================================================
        # OPERADORES MÉXICO (FUTURO)
        # ============================================================
        LockerOperator(
            id="OP-MEX-001",
            name="Correos México",
            document="MX123456789",
            email="contato@correos.mx",
            phone="+52166412345678",
            operator_type="LOGISTICS",
            country="MX",
            active=False,
            commission_rate=0.01,
            currency="MXN",
        ),
        LockerOperator(
            id="OP-MEX-AMZN-001",
            name="Amazon México",
            document="MX987654321",
            email="contato@amazon.mx",
            phone="+52166412345600",
            operator_type="ECOMMERCE",
            country="MX",
            active=False,
            commission_rate=0.01,
            currency="MXN",        ),
        LockerOperator(
            id="OP-MEX-MELI-001",
            name="Mercado Libre México",
            document="MX456789123",
            email="contato@mercadolibre.mx",
            phone="+52166412345639",
            operator_type="ECOMMERCE",
            country="MX",
            active=False,
            commission_rate=0.01,
            currency="MXN",        ),
        
        # ============================================================
        # OPERADORES COLÔMBIA (FUTURO)
        # ============================================================
        LockerOperator(
            id="OP-COL-001",
            name="Servientrega Colombia",
            document="CO123456789",
            email="contato@servientrega.co",
            phone="+5781230000",
            operator_type="LOGISTICS",
            country="CO",
            active=False,
            commission_rate=0.01,
            currency="COP",        ),
        LockerOperator(
            id="OP-COL-MELI-001",
            name="Mercado Libre Colombia",
            document="CO987654321",
             email="contato@mercadolibre.co",
            phone="+5781230001",
            operator_type="ECOMMERCE",
            country="CO",
            active=False,
            commission_rate=0.01,
            currency="COP",            
        ),
        
        # ============================================================
        # OPERADORES ARGENTINA (FUTURO)
        # ============================================================
        LockerOperator(
            id="OP-ARG-001",
            name="Correo Argentino",
            document="AR123456789",
            email="contato@correo.ar",
            phone="+5433900900900",
            operator_type="LOGISTICS",
            country="AR",
            active=False,
            commission_rate=0.01,
            currency="ARS",
        ),
        LockerOperator(
            id="OP-ARG-MELI-001",
            name="Mercado Libre Argentina",
            document="AR987654321",
            email="contato@mercadolibre.ar",
            phone="+5433900900999",
            operator_type="ECOMMERCE",
            country="AR",
            active=False,
            commission_rate=0.01,
            currency="ARS",
        ),
    ]
    
    # Contadores para logging
    new_operators = 0
    updated_operators = 0
    
    for op_data in operators:
        existing = db.query(LockerOperator).filter(LockerOperator.id == op_data.id).first()
        if not existing:
            db.add(op_data)
            print(f"➕ Operador adicionado: {op_data.id} - {op_data.name} ({op_data.country})")
    
    db.commit()


def seed_lockers(db: Session):
    """Popula lockers com configurações de produtos - Versão completa e consistente"""
    
    # ============================================================
    # CONFIGURAÇÕES PADRÃO DE PRODUTOS (TODAS AS CATEGORIAS)
    # ============================================================
    default_product_configs = [
        # ==================== ELETRÔNICOS ====================
        {"category": "ELECTRONICS", "allowed": True, "max_value": 500000, "requires_id": True, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "ELECTRONICS_ACCESSORIES", "allowed": True, "max_value": 30000, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== MODA ====================
        {"category": "FASHION", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "FASHION_LUXURY", "allowed": True, "max_value": 500000, "requires_id": True, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "FOOTWEAR", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "ACCESSORIES", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== BELEZA ====================
        {"category": "BEAUTY", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "BEAUTY_PREMIUM", "allowed": True, "max_value": 100000, "requires_id": True, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "HYGIENE", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "ORAL_HYGIENE", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== SAÚDE ====================
        {"category": "PHARMACY_OTC_MEDS", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "PHARMACY_PRESCRIPTION_MEDS", "allowed": False, "max_value": None, "requires_id": True, "requires_signature": True, "temperature_zone": "REFRIGERATED"},
        {"category": "MEDICAL_SUPPLIES", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "VITAMINS_SUPPLEMENTS", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== ALIMENTOS ====================
        {"category": "FOOD_PERISHABLE", "allowed": False, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "REFRIGERATED"},
        {"category": "FOOD_FROZEN", "allowed": False, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "FROZEN"},
        {"category": "BAKED_GOODS", "allowed": True, "max_value": 20000, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "CAKES_TARTS", "allowed": False, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "REFRIGERATED"},
        {"category": "EMPADAS_PIES", "allowed": False, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "REFRIGERATED"},
        {"category": "FOOD_DRY", "allowed": True, "max_value": 15000, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "SNACKS", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== BEBIDAS ====================
        {"category": "BEVERAGES", "allowed": True, "max_value": 10000, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "BEVERAGES_ALCOHOLIC", "allowed": True, "max_value": 50000, "requires_id": True, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== DOCUMENTOS ====================
        {"category": "DOCUMENTS", "allowed": True, "max_value": None, "requires_id": True, "requires_signature": True, "temperature_zone": "AMBIENT"},
        {"category": "STATIONERY", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== CASA ====================
        {"category": "HOME_APPLIANCES", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "HOME_DECOR", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "CLEANING_SUPPLIES", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== BEBÊS ====================
        {"category": "BABY_PRODUCTS", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "BABY_FOOD", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "TOYS", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== ESPORTES ====================
        {"category": "SPORTS_EQUIPMENT", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "SUPPLEMENTS_SPORTS", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== PET ====================
        {"category": "PET_SUPPLIES", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "PET_FOOD", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== ALTO VALOR ====================
        {"category": "HIGH_VALUE", "allowed": False, "max_value": 1000000, "requires_id": True, "requires_signature": True, "temperature_zone": "AMBIENT"},
        {"category": "JEWELRY", "allowed": True, "max_value": 500000, "requires_id": True, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "WATCHES", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        
        # ==================== PRODUTOS ESPECIAIS ====================
        {"category": "HAZARDOUS", "allowed": False, "max_value": None, "requires_id": True, "requires_signature": True, "temperature_zone": "AMBIENT"},
        {"category": "MONEY", "allowed": False, "max_value": None, "requires_id": True, "requires_signature": True, "temperature_zone": "AMBIENT"},
        {"category": "ANIMALS_ALIVE", "allowed": False, "max_value": None, "requires_id": True, "requires_signature": True, "temperature_zone": "AMBIENT"},
        {"category": "WEAPONS", "allowed": False, "max_value": None, "requires_id": True, "requires_signature": True, "temperature_zone": "AMBIENT"},
        
        # ==================== SERVIÇOS ====================
        {"category": "GIFT_CARDS", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
        {"category": "TICKETS", "allowed": True, "max_value": None, "requires_id": False, "requires_signature": False, "temperature_zone": "AMBIENT"},
    ]
    
    # ==================== LOCKERS - SÃO PAULO ====================
    lockers_sp = [
        {
            "id": "SP-OSASCO-CENTRO-LK-001",
            "display_name": "Osasco Centro - Locker 001",
            "region": "SP",
            "city": "Osasco",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": True,
            "has_alarm": False,
            "active": True,
            "slots": [
                {"size": "P", "count": 8, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 8, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 6, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
                {"size": "XG", "count": 2, "width_cm": 50, "height_cm": 60, "depth_cm": 40, "max_weight_kg": 20},
            ],
            "product_overrides": [
                {"category": "FOOD_PERISHABLE", "allowed": False},
                {"category": "FOOD_FROZEN", "allowed": False},
            ]
        },
        {
            "id": "SP-CARAPICUIBA-JDMARILU-LK-001",
            "display_name": "Carapicuíba JD Marilu - Locker 001",
            "region": "SP",
            "city": "Carapicuíba",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": False,
            "has_alarm": False,
            "active": True,
            "slots": [
                {"size": "P", "count": 10, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 10, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 4, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
            ],
            "product_overrides": [
                {"category": "BAKED_GOODS", "allowed": True, "max_value": 20000},
                {"category": "FOOD_DRY", "allowed": True, "max_value": 15000},
                {"category": "SNACKS", "allowed": True},
            ]
        },
        {
            "id": "SP-CARAPICUIBA-JDMARILU-LK-002",
            "display_name": "Carapicuíba JD Marilu - Locker 002",
            "region": "SP",
            "city": "Carapicuíba",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": False,
            "has_alarm": False,
            "active": True,
            "slots": [
                {"size": "P", "count": 30, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 20, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 10, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
            ],
            "product_overrides": []
        },
        {
            "id": "SP-ALPHAVILLE-SHOP-LK-001",
            "display_name": "Alphaville Shopping - Locker Premium",
            "region": "SP",
            "city": "Barueri",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "HIGH",
            "has_camera": True,
            "has_alarm": True,
            "active": True,
            "slots": [
                {"size": "P", "count": 10, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 10, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 8, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
                {"size": "XG", "count": 4, "width_cm": 50, "height_cm": 60, "depth_cm": 40, "max_weight_kg": 20},
            ],
            "product_overrides": [
                {"category": "HIGH_VALUE", "allowed": True, "max_value": 2000000},
                {"category": "DOCUMENTS", "allowed": True, "requires_signature": True, "requires_id": True},
                {"category": "ELECTRONICS", "allowed": True, "max_value": 500000, "requires_id": True},
                {"category": "JEWELRY", "allowed": True, "max_value": 1000000, "requires_id": True},
            ]
        },
        {
            "id": "SP-VILAOLIMPIA-FOOD-LK-001",
            "display_name": "Vila Olímpia - Locker Refrigerado",
            "region": "SP",
            "city": "São Paulo",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "REFRIGERATED",
            "security_level": "STANDARD",
            "has_camera": True,
            "has_alarm": False,
            "active": True,
            "slots": [
                {"size": "P", "count": 12, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 3},
                {"size": "M", "count": 8, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
            ],
            "product_overrides": [
                {"category": "FOOD_PERISHABLE", "allowed": True},
                {"category": "PHARMACY_PRESCRIPTION_MEDS", "allowed": True},
                {"category": "CAKES_TARTS", "allowed": True},
                {"category": "EMPADAS_PIES", "allowed": True},
                {"category": "ELECTRONICS", "allowed": False},
                {"category": "BAKED_GOODS", "allowed": False},
                {"category": "FOOD_DRY", "allowed": False},
                {"category": "SNACKS", "allowed": False},
            ]
        },
    ]

    # ==================== LOCKERS - PORTUGAL ====================
    lockers_pt = [
        {
            "id": "PT-MAIA-CENTRO-LK-001",
            "display_name": "Maia Centro - Locker 001",
            "region": "PT",
            "city": "Maia",
            "state": "Porto",
            "country": "PT",
            "timezone": "Europe/Lisbon",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": True,
            "has_alarm": False,
            "active": True,
            "slots": [
                {"size": "P", "count": 8, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 8, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 6, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
                {"size": "XG", "count": 2, "width_cm": 50, "height_cm": 60, "depth_cm": 40, "max_weight_kg": 20},
            ],
            "product_overrides": []
        },
        {
            "id": "PT-GUIMARAES-AZUREM-LK-001",
            "display_name": "Guimarães Azurém - Locker Refrigerado",
            "region": "PT",
            "city": "Guimarães",
            "state": "Braga",
            "country": "PT",
            "timezone": "Europe/Lisbon",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "REFRIGERATED",
            "security_level": "STANDARD",
            "has_camera": False,
            "has_alarm": False,
            "active": True,
            "slots": [
                {"size": "P", "count": 10, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 10, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 4, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
            ],
            "product_overrides": [
                {"category": "FOOD_PERISHABLE", "allowed": True},
                {"category": "CAKES_TARTS", "allowed": True},
                {"category": "EMPADAS_PIES", "allowed": True},
                {"category": "BEVERAGES", "allowed": True, "max_value": 10000},
            ]
        },
        {
            "id": "PT-LISBOA-PHARMA-LK-001",
            "display_name": "Lisboa - Locker Farmácia",
            "region": "PT",
            "city": "Lisboa",
            "state": "Lisboa",
            "country": "PT",
            "timezone": "Europe/Lisbon",
            "operator_id": "OP-PHARMA-001",
            "temperature_zone": "AMBIENT",
            "security_level": "ENHANCED",
            "has_camera": True,
            "has_alarm": True,
            "active": True,
            "slots": [
                {"size": "P", "count": 15, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 5, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
            ],
            "product_overrides": [
                {"category": "PHARMACY_OTC_MEDS", "allowed": True},
                {"category": "PHARMACY_PRESCRIPTION_MEDS", "allowed": True, "requires_id": True, "requires_signature": True},
                {"category": "VITAMINS_SUPPLEMENTS", "allowed": True},
                {"category": "MEDICAL_SUPPLIES", "allowed": True},
                {"category": "ELECTRONICS", "allowed": False},
                {"category": "FASHION", "allowed": False},
                {"category": "BEAUTY", "allowed": False},
            ]
        },
    ]

    # ==================== LOCKERS FUTUROS (ES / RJ / PR) ====================
    lockers_future = [
        {
            "id": "ES-MADRID-CENTRO-LK-001",
            "display_name": "Madrid Centro - Locker 001",
            "region": "ES",
            "city": "Madrid",
            "state": None,
            "country": "ES",
            "timezone": "Europe/Madrid",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": True,
            "has_alarm": False,
            "active": False,
            "slots": [
                {"size": "P", "count": 8, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 8, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 6, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
            ],
            "product_overrides": []
        },
        {
            "id": "RJ-CAPITAL-CENTRO-LK-001",
            "display_name": "Rio Centro - Locker 001",
            "region": "RJ",
            "city": "Rio de Janeiro",
            "state": "RJ",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": True,
            "has_alarm": False,
            "active": False,
            "slots": [
                {"size": "P", "count": 16, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 8, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 6, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
            ],
            "product_overrides": []
        },
        {
            "id": "PR-CAPITAL-SANTAFELICIDADE-LK-001",
            "display_name": "Curitiba Santa Felicidade - Locker 001",
            "region": "PR",
            "city": "Curitiba",
            "state": "PR",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": False,
            "has_alarm": False,
            "active": False,
            "slots": [
                {"size": "P", "count": 10, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 10, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 10, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
            ],
            "product_overrides": []
        },
    ]

    # ==================== CRIAÇÃO DOS LOCKERS ====================
    all_lockers = lockers_sp + lockers_pt + lockers_future

    for locker_data in all_lockers:
        existing = db.query(Locker).filter(Locker.id == locker_data["id"]).first()
        if existing:
            print(f"Locker {locker_data['id']} já existe, pulando...")
            continue

        # Extrai slots e overrides
        slots_config = locker_data.pop("slots", [])
        product_overrides = locker_data.pop("product_overrides", [])
        
        # Cria o locker
        locker = Locker(
            **locker_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(locker)
        db.flush()

        # Cria configurações de slots
        for slot in slots_config:
            slot_config = LockerSlotConfig(
                locker_id=locker.id,
                slot_size=slot["size"],
                slot_count=slot["count"],
                width_cm=slot.get("width_cm"),
                height_cm=slot.get("height_cm"),
                depth_cm=slot.get("depth_cm"),
                max_weight_kg=slot.get("max_weight_kg"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(slot_config)

        # Cria configurações de produtos (default + overrides)
        for default_config in default_product_configs:
            # Verifica se há override para esta categoria
            override = next(
                (o for o in product_overrides if o["category"] == default_config["category"]), 
                {}
            )
            
            # Merge do default com override
            config = {**default_config, **override}
            
            # Validação de compatibilidade de temperatura
            if config["temperature_zone"] != "ANY":
                if locker.temperature_zone != config["temperature_zone"]:
                    # Se o locker não suporta a temperatura necessária, força allowed=False
                    if config["allowed"]:
                        print(f"AVISO: Locker {locker.id} não suporta {config['temperature_zone']} para categoria {config['category']}. Desabilitando.")
                    config["allowed"] = False
            
            product_config = ProductLockerConfig(
                locker_id=locker.id,
                category=config["category"],
                allowed=config["allowed"],
                temperature_zone=config.get("temperature_zone", locker.temperature_zone),
                # max_value=config.get("max_value"),
                # requires_signature=config.get("requires_signature", False),
                # requires_id=config.get("requires_id", False),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(product_config)
        
        print(f"Locker {locker.id} criado com {len(slots_config)} slots e {len(default_product_configs)} configurações de produto")

    db.commit()
    print(f"✅ Seed concluído: {len(all_lockers)} lockers processados")


def run_full_seed(db: Session):
    """Executa todo o seed na ordem correta."""
    seed_product_categories(db)
    seed_operators(db)
    seed_lockers(db)