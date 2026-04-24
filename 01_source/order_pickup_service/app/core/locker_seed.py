# 01_source/order_pickup_service/app/core/locker_seed.py
"""
Seed inicial completo: Lockers, Operadores, Categorias de Produtos, Configurações
e Capability Catalog (Bloco 12).

Este seed mantém todos os dados originais e adiciona suporte completo ao
Capability Catalog, incluindo:
- CapabilityProfileMethodInterface
- CapabilityProfileMethodRequirement
- CapabilityProfileTarget
- E todas as outras tabelas do Bloco 12

Data: 04/04/2026
"""

from sqlalchemy.orm import Session
from app.models.locker import Locker, LockerSlotConfig, LockerOperator
from app.models.product_locker_config import ProductLockerConfig, ProductCategory
from app.models.capability import (
    CapabilityRegion,
    CapabilityChannel,
    CapabilityContext,
    PaymentMethodCatalog,
    PaymentInterfaceCatalog,
    WalletProviderCatalog,
    CapabilityRequirementCatalog,
    CapabilityProfile,
    CapabilityProfileMethod,
    CapabilityProfileMethodInterface,
    CapabilityProfileMethodRequirement,
    CapabilityProfileAction,
    CapabilityProfileConstraint,
    CapabilityProfileTarget,
    CapabilityProfileSnapshot,
)
from datetime import datetime, timezone
import json
import hashlib


def _seed_cm_to_mm(value_cm: float | int | None) -> int | None:
    if value_cm is None:
        return None
    return int(round(float(value_cm) * 10))


def _seed_kg_to_g(value_kg: float | int | None) -> int | None:
    if value_kg is None:
        return None
    return int(round(float(value_kg) * 1000))


def log(msg: str):
    print(f"[SEED] {msg}")


# ============================================================
# 1. CATEGORIAS DE PRODUTOS (ORIGINAL COMPLETO)
# ============================================================

def seed_product_categories(db: Session):
    """Popula categorias mestre de produtos - Versão ampliada original"""
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="ELECTRONICS_ACCESSORIES",
            name="Acessórios Eletrônicos",
            description="Fones de ouvido, cabos, carregadores, capas",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="FASHION_LUXURY",
            name="Moda Luxo",
            description="Grife, designer, edições limitadas",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="FOOTWEAR",
            name="Calçados",
            description="Sapatos, tênis, sandálias, botas",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="ACCESSORIES",
            name="Acessórios",
            description="Bolsas, cintos, óculos, bijuterias",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="BEAUTY_PREMIUM",
            name="Beleza Premium",
            description="Perfumes importados, cosméticos de luxo",
            default_temperature_zone="AMBIENT",
            default_security_level="ENHANCED",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="HYGIENE",
            name="Higiene Pessoal",
            description="Sabonetes, shampoos, cremes, itens de banho",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="ORAL_HYGIENE",
            name="Higiene Bucal",
            description="Escovas de dente, pastas, fio dental, enxaguante",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="PHARMACY_PRESCRIPTION_MEDS",
            name="Medicamentos com Prescrição",
            description="Medicamentos que exigem receita médica",
            default_temperature_zone="REFRIGERATED",
            default_security_level="HIGH",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="MEDICAL_SUPPLIES",
            name="Suprimentos Médicos",
            description="Curativos, seringas, equipamentos médicos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="VITAMINS_SUPPLEMENTS",
            name="Vitaminas e Suplementos",
            description="Suplementos alimentares, vitaminas, minerais",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="FOOD_FROZEN",
            name="Alimentos Congelados",
            description="Pizzas congeladas, sorvetes, vegetais congelados",
            default_temperature_zone="FROZEN",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="BAKED_GOODS",
            name="Produtos de Panificação",
            description="Pães, biscoitos, bolos secos, cookies",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="CAKES_TARTS",
            name="Bolos e Tortas Cremosos",
            description="Bolos com recheio cremoso, tortas, sobremesas refrigeradas",
            default_temperature_zone="REFRIGERATED",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="EMPADAS_PIES",
            name="Empadas e Salgados Assados",
            description="Empadas, esfihas, salgados assados recheados",
            default_temperature_zone="REFRIGERATED",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="FOOD_DRY",
            name="Alimentos Não Perecíveis",
            description="Arroz, feijão, massas, enlatados, biscoitos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="SNACKS",
            name="Snacks e Petiscos",
            description="Salgadinhos, chocolates, balas, barras de cereal",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="BEVERAGES",
            name="Bebidas",
            description="Refrigerantes, sucos, águas, energéticos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="BEVERAGES_ALCOHOLIC",
            name="Bebidas Alcoólicas",
            description="Cervejas, vinhos, destilados",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=True,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="STATIONERY",
            name="Papelaria",
            description="Cadernos, canetas, material escolar",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="HOME_DECOR",
            name="Decoração",
            description="Quadros, velas, objetos decorativos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="CLEANING_SUPPLIES",
            name="Produtos de Limpeza",
            description="Detergentes, desinfetantes, produtos químicos domésticos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=True,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="BABY_FOOD",
            name="Alimentos Infantis",
            description="Papinhas, fórmulas infantis, comidas de bebê",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="TOYS",
            name="Brinquedos",
            description="Brinquedos e jogos infantis",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="SUPPLEMENTS_SPORTS",
            name="Suplementos Esportivos",
            description="Whey protein, creatina, pré-treino",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="PET_FOOD",
            name="Alimentos para Pets",
            description="Ração seca e úmida, petiscos",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="JEWELRY",
            name="Joias e Semijoias",
            description="Anéis, colares, pulseiras, brincos",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="WATCHES",
            name="Relógios",
            description="Relógios de pulso, smartwatches",
            default_temperature_zone="AMBIENT",
            default_security_level="ENHANCED",
            is_hazardous=False,
            requires_age_verification=False,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="MONEY",
            name="Dinheiro em Espécie",
            description="Cédulas, moedas, valores monetários",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="ANIMALS_ALIVE",
            name="Animais Vivos",
            description="Pets, animais de pequeno porte",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
            requires_age_verification=False,
        ),
        ProductCategory(
            id="WEAPONS",
            name="Armas e Munições",
            description="Armas de fogo, munições, armas brancas",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=True,
            requires_age_verification=True,
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
            requires_age_verification=False,
        ),
        ProductCategory(
            id="TICKETS",
            name="Ingressos",
            description="Ingressos para shows, eventos, viagens",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=False,
        ),
    ]
    
    new_count = 0
    for cat in categories:
        existing = db.query(ProductCategory).filter(ProductCategory.id == cat.id).first()
        if not existing:
            db.add(cat)
            new_count += 1
            log(f"Categoria adicionada: {cat.id} - {cat.name}")
    
    db.commit()
    log(f"Seed de categorias concluído: {new_count} novas categorias inseridas")


# ============================================================
# 2. OPERADORES DE LOCKERS (ORIGINAL COMPLETO)
# ============================================================

def seed_operators(db: Session):
    """Popula operadores de lockers - Versão ampliada original para múltiplos países"""
    
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=24,
            sla_return_hours=12,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
        ),
        LockerOperator(
            id="OP-ATACADAO-001",
            name="Atacadão Partner",
            document="44.444.444/0001-44",
            email="contato@atacadao.com.br",
            phone="+5511912340011",            
            operator_type="ECOMMERCE",
            country="BR",
            active=True,
            commission_rate=0.01,
            currency="BRL",
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=48,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=48,
            sla_return_hours=24,
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
            sla_pickup_hours=48,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=48,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=48,
            sla_return_hours=24,
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
            sla_pickup_hours=48,
            sla_return_hours=24,
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
            sla_pickup_hours=48,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
        ),
        
        # ============================================================
        # OPERADORES ESPANHA
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=48,
            sla_return_hours=24,
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
            sla_pickup_hours=48,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            currency="MXN",
            sla_pickup_hours=72,
            sla_return_hours=24,
        ),
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
            currency="MXN",
            sla_pickup_hours=72,
            sla_return_hours=24,
        ),
        
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
            currency="COP",
            sla_pickup_hours=72,
            sla_return_hours=24,
        ),
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
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
            sla_pickup_hours=72,
            sla_return_hours=24,
        ),
    ]
    
    new_count = 0
    for op in operators:
        existing = db.query(LockerOperator).filter(LockerOperator.id == op.id).first()
        if not existing:
            db.add(op)
            new_count += 1
            log(f"Operador adicionado: {op.id} - {op.name} ({op.country})")
    
    db.commit()
    log(f"Seed de operadores concluído: {new_count} novos operadores inseridos")


# ============================================================
# 3. CONFIGURAÇÕES PADRÃO DE PRODUTOS (ORIGINAL COMPLETO)
# ============================================================

DEFAULT_PRODUCT_CONFIGS = [
    # ==================== ELETRÔNICOS ====================
    {"category": "ELECTRONICS", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "ELECTRONICS_ACCESSORIES", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== MODA ====================
    {"category": "FASHION", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "FASHION_LUXURY", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "FOOTWEAR", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "ACCESSORIES", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== BELEZA ====================
    {"category": "BEAUTY", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "BEAUTY_PREMIUM", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "HYGIENE", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "ORAL_HYGIENE", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== SAÚDE ====================
    {"category": "PHARMACY_OTC_MEDS", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "PHARMACY_PRESCRIPTION_MEDS", "allowed": False, "temperature_zone": "REFRIGERATED"},
    {"category": "MEDICAL_SUPPLIES", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "VITAMINS_SUPPLEMENTS", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== ALIMENTOS ====================
    {"category": "FOOD_PERISHABLE", "allowed": False, "temperature_zone": "REFRIGERATED"},
    {"category": "FOOD_FROZEN", "allowed": False, "temperature_zone": "FROZEN"},
    {"category": "BAKED_GOODS", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "CAKES_TARTS", "allowed": False, "temperature_zone": "REFRIGERATED"},
    {"category": "EMPADAS_PIES", "allowed": False, "temperature_zone": "REFRIGERATED"},
    {"category": "FOOD_DRY", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "SNACKS", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== BEBIDAS ====================
    {"category": "BEVERAGES", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "BEVERAGES_ALCOHOLIC", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== DOCUMENTOS ====================
    {"category": "DOCUMENTS", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "STATIONERY", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== CASA ====================
    {"category": "HOME_APPLIANCES", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "HOME_DECOR", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "CLEANING_SUPPLIES", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== BEBÊS ====================
    {"category": "BABY_PRODUCTS", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "BABY_FOOD", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "TOYS", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== ESPORTES ====================
    {"category": "SPORTS_EQUIPMENT", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "SUPPLEMENTS_SPORTS", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== PET ====================
    {"category": "PET_SUPPLIES", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "PET_FOOD", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== ALTO VALOR ====================
    {"category": "HIGH_VALUE", "allowed": False, "temperature_zone": "AMBIENT"},
    {"category": "JEWELRY", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "WATCHES", "allowed": True, "temperature_zone": "AMBIENT"},
    
    # ==================== PRODUTOS ESPECIAIS ====================
    {"category": "HAZARDOUS", "allowed": False, "temperature_zone": "AMBIENT"},
    {"category": "MONEY", "allowed": False, "temperature_zone": "AMBIENT"},
    {"category": "ANIMALS_ALIVE", "allowed": False, "temperature_zone": "AMBIENT"},
    {"category": "WEAPONS", "allowed": False, "temperature_zone": "AMBIENT"},
    
    # ==================== SERVIÇOS ====================
    {"category": "GIFT_CARDS", "allowed": True, "temperature_zone": "AMBIENT"},
    {"category": "TICKETS", "allowed": True, "temperature_zone": "AMBIENT"},
]


# ============================================================
# 4. LOCKERS (ORIGINAL COMPLETO)
# ============================================================

def seed_lockers(db: Session):
    """Popula lockers com configurações de produtos - Versão original completa"""
    
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
            "has_kiosk": True,
            "has_printer": True,
            "has_card_reader": True,
            "has_nfc": True,
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
            "has_kiosk": True,
            "has_printer": False,
            "has_card_reader": True,
            "has_nfc": False,
            "active": True,
            "slots": [
                {"size": "P", "count": 10, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 10, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 4, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
            ],
            "product_overrides": [
                {"category": "BAKED_GOODS", "allowed": True},
                {"category": "FOOD_DRY", "allowed": True},
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
            "has_kiosk": True,
            "has_printer": False,
            "has_card_reader": True,
            "has_nfc": False,
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
            "has_kiosk": True,
            "has_printer": True,
            "has_card_reader": True,
            "has_nfc": True,
            "active": True,
            "slots": [
                {"size": "P", "count": 10, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 10, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 8, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
                {"size": "XG", "count": 4, "width_cm": 50, "height_cm": 60, "depth_cm": 40, "max_weight_kg": 20},
            ],
            "product_overrides": [
                {"category": "HIGH_VALUE", "allowed": True},
                {"category": "DOCUMENTS", "allowed": True},
                {"category": "ELECTRONICS", "allowed": True},
                {"category": "JEWELRY", "allowed": True},
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
            "operator_id": "OP-PHARMA-001",
            "temperature_zone": "REFRIGERATED",
            "security_level": "ENHANCED",
            "has_camera": True,
            "has_alarm": True,
            "has_kiosk": True,
            "has_printer": False,
            "has_card_reader": True,
            "has_nfc": False,
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
            "has_kiosk": True,
            "has_printer": True,
            "has_card_reader": True,
            "has_nfc": True,
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
            "has_kiosk": True,
            "has_printer": False,
            "has_card_reader": True,
            "has_nfc": False,
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
                {"category": "BEVERAGES", "allowed": True},
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
            "has_kiosk": True,
            "has_printer": True,
            "has_card_reader": True,
            "has_nfc": False,
            "active": True,
            "slots": [
                {"size": "P", "count": 15, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 5, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
            ],
            "product_overrides": [
                {"category": "PHARMACY_OTC_MEDS", "allowed": True},
                {"category": "PHARMACY_PRESCRIPTION_MEDS", "allowed": True},
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
            "state": "Madrid",
            "country": "ES",
            "timezone": "Europe/Madrid",
            "operator_id": "OP-CORREOS-ES-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": True,
            "has_alarm": False,
            "has_kiosk": True,
            "has_printer": True,
            "has_card_reader": True,
            "has_nfc": True,
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
            "has_kiosk": True,
            "has_printer": True,
            "has_card_reader": True,
            "has_nfc": True,
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
            "has_kiosk": True,
            "has_printer": False,
            "has_card_reader": True,
            "has_nfc": False,
            "active": False,
            "slots": [
                {"size": "P", "count": 10, "width_cm": 10, "height_cm": 10, "depth_cm": 40, "max_weight_kg": 2},
                {"size": "M", "count": 10, "width_cm": 20, "height_cm": 20, "depth_cm": 40, "max_weight_kg": 5},
                {"size": "G", "count": 10, "width_cm": 30, "height_cm": 40, "depth_cm": 40, "max_weight_kg": 10},
            ],
            "product_overrides": []
        },
    ]

    all_lockers = lockers_sp + lockers_pt + lockers_future

    new_count = 0
    for locker_data in all_lockers:
        existing = db.query(Locker).filter(Locker.id == locker_data["id"]).first()
        if existing:
            log(f"Locker {locker_data['id']} já existe, pulando...")
            continue

        slots_config = locker_data.pop("slots", [])
        product_overrides = locker_data.pop("product_overrides", [])
        
        locker = Locker(
            **locker_data,
            slots_count=sum(s["count"] for s in slots_config),
            slots_available=sum(s["count"] for s in slots_config),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(locker)
        db.flush()

        # Configurações de slots
        for slot in slots_config:
            slot_config = LockerSlotConfig(
                locker_id=locker.id,
                slot_size=slot["size"],
                slot_count=slot["count"],
                available_count=slot["count"],
                width_mm=_seed_cm_to_mm(slot.get("width_cm")),
                height_mm=_seed_cm_to_mm(slot.get("height_cm")),
                depth_mm=_seed_cm_to_mm(slot.get("depth_cm")),
                max_weight_g=_seed_kg_to_g(slot.get("max_weight_kg")),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(slot_config)

        # Configurações de produtos
        for default_config in DEFAULT_PRODUCT_CONFIGS:
            override = next(
                (o for o in product_overrides if o["category"] == default_config["category"]), 
                {}
            )
            
            config = {**default_config, **override}
            
            # Validação de temperatura
            if config["temperature_zone"] != "ANY":
                if locker.temperature_zone != config["temperature_zone"]:
                    if config["allowed"]:
                        log(f"AVISO: Locker {locker.id} não suporta {config['temperature_zone']} para categoria {config['category']}. Desabilitando.")
                    config["allowed"] = False
            
            product_config = ProductLockerConfig(
                locker_id=locker.id,
                category=config["category"],
                allowed=config["allowed"],
                temperature_zone=config.get("temperature_zone", locker.temperature_zone),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(product_config)
        
        new_count += 1
        log(f"Locker {locker.id} criado com {len(slots_config)} slots")

    db.commit()
    log(f"Seed de lockers concluído: {new_count} novos lockers inseridos")


# ============================================================
# 5. CAPABILITY CATALOG - REGIÕES
# ============================================================

def seed_capability_regions(db: Session):
    """Popula regiões do catálogo de capabilities"""
    
    regions = [
        CapabilityRegion(
            code="SP",
            name="São Paulo",
            country_code="BR",
            continent="América do Sul",
            default_currency="BRL",
            default_timezone="America/Sao_Paulo",
            default_locale="pt-BR",
            is_active=True,
        ),
        CapabilityRegion(
            code="RJ",
            name="Rio de Janeiro",
            country_code="BR",
            continent="América do Sul",
            default_currency="BRL",
            default_timezone="America/Sao_Paulo",
            default_locale="pt-BR",
            is_active=True,
        ),
        CapabilityRegion(
            code="PR",
            name="Paraná",
            country_code="BR",
            continent="América do Sul",
            default_currency="BRL",
            default_timezone="America/Sao_Paulo",
            default_locale="pt-BR",
            is_active=True,
        ),
        CapabilityRegion(
            code="PT",
            name="Portugal",
            country_code="PT",
            continent="Europa",
            default_currency="EUR",
            default_timezone="Europe/Lisbon",
            default_locale="pt-PT",
            is_active=True,
        ),
        CapabilityRegion(
            code="ES",
            name="Espanha",
            country_code="ES",
            continent="Europa",
            default_currency="EUR",
            default_timezone="Europe/Madrid",
            default_locale="es-ES",
            is_active=True,
        ),
        CapabilityRegion(
            code="MX",
            name="México",
            country_code="MX",
            continent="América do Norte",
            default_currency="MXN",
            default_timezone="America/Mexico_City",
            default_locale="es-MX",
            is_active=False,
        ),
        CapabilityRegion(
            code="CO",
            name="Colômbia",
            country_code="CO",
            continent="América do Sul",
            default_currency="COP",
            default_timezone="America/Bogota",
            default_locale="es-CO",
            is_active=False,
        ),
        CapabilityRegion(
            code="AR",
            name="Argentina",
            country_code="AR",
            continent="América do Sul",
            default_currency="ARS",
            default_timezone="America/Argentina/Buenos_Aires",
            default_locale="es-AR",
            is_active=False,
        ),
    ]
    
    new_count = 0
    for region in regions:
        existing = db.query(CapabilityRegion).filter(CapabilityRegion.code == region.code).first()
        if not existing:
            db.add(region)
            new_count += 1
            log(f"Região adicionada: {region.code} - {region.name}")
    
    db.commit()
    log(f"Seed de regiões concluído: {new_count} novas regiões inseridas")


# ============================================================
# 6. CAPABILITY CATALOG - CANAIS
# ============================================================

def seed_capability_channels(db: Session):
    """Popula canais do catálogo de capabilities"""
    
    channels = [
        CapabilityChannel(code="online", name="Online / Web / App", is_active=True),
        CapabilityChannel(code="kiosk", name="KIOSK / Totem físico", is_active=True),
        CapabilityChannel(code="api", name="API direta (parceiros B2B)", is_active=True),
        CapabilityChannel(code="partner", name="Parceiro integrado", is_active=True),
        CapabilityChannel(code="staff", name="Operação manual por staff", is_active=True),
    ]
    
    new_count = 0
    for channel in channels:
        existing = db.query(CapabilityChannel).filter(CapabilityChannel.code == channel.code).first()
        if not existing:
            db.add(channel)
            new_count += 1
            log(f"Canal adicionado: {channel.code} - {channel.name}")
    
    db.commit()
    log(f"Seed de canais concluído: {new_count} novos canais inseridos")


# ============================================================
# 7. CAPABILITY CATALOG - CONTEXTOS
# ============================================================

def seed_capability_contexts(db: Session):
    """Popula contextos do catálogo de capabilities"""
    
    channels = {c.code: c for c in db.query(CapabilityChannel).all()}
    
    contexts = [
        # Kiosk contexts
        CapabilityContext(
            channel_id=channels["kiosk"].id,
            code="purchase",
            name="Compra presencial",
            description="Compra com pagamento no KIOSK",
            is_active=True,
        ),
        CapabilityContext(
            channel_id=channels["kiosk"].id,
            code="pickup",
            name="Retirada de pedido",
            description="Retirada de pedido online no KIOSK",
            is_active=True,
        ),
        CapabilityContext(
            channel_id=channels["kiosk"].id,
            code="operator_pickup",
            name="Retirada assistida",
            description="Retirada assistida por operador",
            is_active=True,
        ),
        CapabilityContext(
            channel_id=channels["kiosk"].id,
            code="logistics_handover",
            name="Entrega de parceiro logístico",
            description="Depósito de encomenda por parceiro logístico",
            is_active=True,
        ),
        CapabilityContext(
            channel_id=channels["kiosk"].id,
            code="return_dropoff",
            name="Devolução de item",
            description="Devolução de produto no KIOSK",
            is_active=True,
        ),
        # Online contexts
        CapabilityContext(
            channel_id=channels["online"].id,
            code="checkout",
            name="Checkout online",
            description="Compra no e-commerce com pagamento online",
            is_active=True,
        ),
        CapabilityContext(
            channel_id=channels["online"].id,
            code="pickup_schedule",
            name="Agendamento de retirada",
            description="Agendamento de retirada de pedido",
            is_active=True,
        ),
        # Partner contexts
        CapabilityContext(
            channel_id=channels["partner"].id,
            code="webhook_payment",
            name="Pagamento via webhook",
            description="Notificação de pagamento via webhook",
            is_active=True,
        ),
        # Staff contexts
        CapabilityContext(
            channel_id=channels["staff"].id,
            code="manual_release",
            name="Liberação manual",
            description="Liberação manual de gaveta por staff",
            is_active=True,
        ),
    ]
    
    new_count = 0
    for context in contexts:
        existing = db.query(CapabilityContext).filter(
            CapabilityContext.channel_id == context.channel_id,
            CapabilityContext.code == context.code
        ).first()
        if not existing:
            db.add(context)
            new_count += 1
            log(f"Contexto adicionado: {context.code}")
    
    db.commit()
    log(f"Seed de contextos concluído: {new_count} novos contextos inseridos")


# ============================================================
# 8. CAPABILITY CATALOG - MÉTODOS DE PAGAMENTO
# ============================================================

def seed_payment_methods(db: Session):
    """Popula métodos de pagamento do catálogo"""
    
    methods = [
        PaymentMethodCatalog(
            code="pix",
            name="PIX",
            family="bank_transfer",
            is_wallet=False,
            is_card=False,
            is_bnpl=False,
            is_cash_like=False,
            is_bank_transfer=True,
            is_instant=True,
            requires_redirect=False,
            is_active=True,
        ),
        PaymentMethodCatalog(
            code="creditCard",
            name="Cartão de Crédito",
            family="card",
            is_wallet=False,
            is_card=True,
            is_bnpl=False,
            is_cash_like=False,
            is_bank_transfer=False,
            is_instant=False,
            requires_redirect=True,
            is_active=True,
        ),
        PaymentMethodCatalog(
            code="debitCard",
            name="Cartão de Débito",
            family="card",
            is_wallet=False,
            is_card=True,
            is_bnpl=False,
            is_cash_like=False,
            is_bank_transfer=False,
            is_instant=False,
            requires_redirect=True,
            is_active=True,
        ),
        PaymentMethodCatalog(
            code="boleto",
            name="Boleto Bancário",
            family="bank_transfer",
            is_wallet=False,
            is_card=False,
            is_bnpl=False,
            is_cash_like=False,
            is_bank_transfer=True,
            is_instant=False,
            requires_redirect=False,
            is_active=True,
        ),
        PaymentMethodCatalog(
            code="cash",
            name="Dinheiro",
            family="cash",
            is_wallet=False,
            is_card=False,
            is_bnpl=False,
            is_cash_like=True,
            is_bank_transfer=False,
            is_instant=False,
            requires_redirect=False,
            is_active=True,
        ),
        PaymentMethodCatalog(
            code="voucher",
            name="Voucher",
            family="voucher",
            is_wallet=False,
            is_card=False,
            is_bnpl=False,
            is_cash_like=False,
            is_bank_transfer=False,
            is_instant=False,
            requires_redirect=False,
            is_active=True,
        ),
        PaymentMethodCatalog(
            code="mbway",
            name="MB Way",
            family="digital_wallet",
            is_wallet=True,
            is_card=False,
            is_bnpl=False,
            is_cash_like=False,
            is_bank_transfer=False,
            is_instant=True,
            requires_redirect=False,
            is_active=True,
        ),
        PaymentMethodCatalog(
            code="apple_pay",
            name="Apple Pay",
            family="digital_wallet",
            is_wallet=True,
            is_card=True,
            is_bnpl=False,
            is_cash_like=False,
            is_bank_transfer=False,
            is_instant=False,
            requires_redirect=False,
            is_active=True,
        ),
        PaymentMethodCatalog(
            code="google_pay",
            name="Google Pay",
            family="digital_wallet",
            is_wallet=True,
            is_card=True,
            is_bnpl=False,
            is_cash_like=False,
            is_bank_transfer=False,
            is_instant=False,
            requires_redirect=False,
            is_active=True,
        ),
    ]
    
    new_count = 0
    for method in methods:
        existing = db.query(PaymentMethodCatalog).filter(PaymentMethodCatalog.code == method.code).first()
        if not existing:
            db.add(method)
            new_count += 1
            log(f"Método de pagamento adicionado: {method.code}")
    
    db.commit()
    log(f"Seed de métodos de pagamento concluído: {new_count} novos métodos inseridos")


# ============================================================
# 9. CAPABILITY CATALOG - INTERFACES DE PAGAMENTO
# ============================================================

def seed_payment_interfaces(db: Session):
    """Popula interfaces de pagamento do catálogo"""
    
    interfaces = [
        PaymentInterfaceCatalog(
            code="qr_code",
            name="QR Code",
            interface_type="digital",
            requires_hw=False,
            is_active=True,
        ),
        PaymentInterfaceCatalog(
            code="chip",
            name="Chip (EMV)",
            interface_type="physical",
            requires_hw=True,
            is_active=True,
        ),
        PaymentInterfaceCatalog(
            code="nfc",
            name="NFC / Contactless",
            interface_type="physical",
            requires_hw=True,
            is_active=True,
        ),
        PaymentInterfaceCatalog(
            code="magnetic",
            name="Trato magnético",
            interface_type="physical",
            requires_hw=True,
            is_active=True,
        ),
        PaymentInterfaceCatalog(
            code="deep_link",
            name="Deep Link (App)",
            interface_type="digital",
            requires_hw=False,
            is_active=True,
        ),
        PaymentInterfaceCatalog(
            code="web_token",
            name="Token Web",
            interface_type="digital",
            requires_hw=False,
            is_active=True,
        ),
        PaymentInterfaceCatalog(
            code="manual",
            name="Digitação manual",
            interface_type="physical",
            requires_hw=False,
            is_active=True,
        ),
        PaymentInterfaceCatalog(
            code="barcode",
            name="Código de barras",
            interface_type="physical",
            requires_hw=False,
            is_active=True,
        ),
        PaymentInterfaceCatalog(
            code="kiosk_pinpad",
            name="PinPad no KIOSK",
            interface_type="physical",
            requires_hw=True,
            is_active=True,
        ),
    ]
    
    new_count = 0
    for interface in interfaces:
        existing = db.query(PaymentInterfaceCatalog).filter(PaymentInterfaceCatalog.code == interface.code).first()
        if not existing:
            db.add(interface)
            new_count += 1
            log(f"Interface de pagamento adicionada: {interface.code}")
    
    db.commit()
    log(f"Seed de interfaces de pagamento concluído: {new_count} novas interfaces inseridas")


# ============================================================
# 10. CAPABILITY CATALOG - WALLET PROVIDERS
# ============================================================

def seed_wallet_providers(db: Session):
    """Popula wallet providers do catálogo"""
    
    providers = [
        WalletProviderCatalog(code="applePay", name="Apple Pay", is_active=True),
        WalletProviderCatalog(code="googlePay", name="Google Pay", is_active=True),
        WalletProviderCatalog(code="mercadoPago", name="Mercado Pago", is_active=True),
        WalletProviderCatalog(code="wechatPay", name="WeChat Pay", is_active=True),
        WalletProviderCatalog(code="alipay", name="Alipay", is_active=True),
        WalletProviderCatalog(code="mPesa", name="M-Pesa", is_active=True),
        WalletProviderCatalog(code="mbway", name="MB Way", is_active=True),
        WalletProviderCatalog(code="picpay", name="PicPay", is_active=True),
        WalletProviderCatalog(code="pagseguro", name="PagSeguro", is_active=True),
    ]
    
    new_count = 0
    for provider in providers:
        existing = db.query(WalletProviderCatalog).filter(WalletProviderCatalog.code == provider.code).first()
        if not existing:
            db.add(provider)
            new_count += 1
            log(f"Wallet provider adicionado: {provider.code}")
    
    db.commit()
    log(f"Seed de wallet providers concluído: {new_count} novos providers inseridos")


# ============================================================
# 11. CAPABILITY CATALOG - REQUISITOS
# ============================================================

def seed_capability_requirements(db: Session):
    """Popula requisitos do catálogo de capabilities"""
    
    requirements = [
        CapabilityRequirementCatalog(
            code="amount_cents",
            name="Valor em centavos",
            data_type="integer",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="customer_phone",
            name="Telefone do cliente",
            data_type="phone",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="customer_email",
            name="E-mail do cliente",
            data_type="email",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="customer_phone_or_email",
            name="Telefone OU e-mail",
            data_type="any_of",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="installments",
            name="Número de parcelas",
            data_type="integer",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="age_confirmation",
            name="Confirmação de maioridade",
            data_type="boolean",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="wallet_provider",
            name="Provider da wallet",
            data_type="enum",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="qr_code_content",
            name="Conteúdo do QR Code",
            data_type="string",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="device_id",
            name="ID do dispositivo",
            data_type="string",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="ip_address",
            name="Endereço IP do cliente",
            data_type="string",
            is_active=True,
        ),
        CapabilityRequirementCatalog(
            code="card_token",
            name="Token do cartão",
            data_type="string",
            is_active=True,
        ),
    ]
    
    new_count = 0
    for req in requirements:
        existing = db.query(CapabilityRequirementCatalog).filter(
            CapabilityRequirementCatalog.code == req.code
        ).first()
        if not existing:
            db.add(req)
            new_count += 1
            log(f"Requisito adicionado: {req.code}")
    
    db.commit()
    log(f"Seed de requisitos concluído: {new_count} novos requisitos inseridos")


# ============================================================
# 12. CAPABILITY CATALOG - PERFIS
# ============================================================

def seed_capability_profiles(db: Session):
    """Popula perfis do catálogo de capabilities"""
    
    regions = {r.code: r for r in db.query(CapabilityRegion).all()}
    channels = {c.code: c for c in db.query(CapabilityChannel).all()}
    
    # Build contexts map
    contexts = {}
    for ctx in db.query(CapabilityContext).all():
        channel = db.query(CapabilityChannel).filter(CapabilityChannel.id == ctx.channel_id).first()
        if channel:
            contexts[f"{channel.code}:{ctx.code}"] = ctx
    
    profiles = [
        # SP - Kiosk - Purchase
        CapabilityProfile(
            region_id=regions["SP"].id,
            channel_id=channels["kiosk"].id,
            context_id=contexts["kiosk:purchase"].id,
            profile_code="SP:kiosk:purchase",
            name="São Paulo - Kiosk Compra Presencial",
            priority=100,
            currency="BRL",
            is_active=True,
        ),
        # SP - Kiosk - Pickup
        CapabilityProfile(
            region_id=regions["SP"].id,
            channel_id=channels["kiosk"].id,
            context_id=contexts["kiosk:pickup"].id,
            profile_code="SP:kiosk:pickup",
            name="São Paulo - Kiosk Retirada",
            priority=100,
            currency="BRL",
            is_active=True,
        ),
        # SP - Online - Checkout
        CapabilityProfile(
            region_id=regions["SP"].id,
            channel_id=channels["online"].id,
            context_id=contexts["online:checkout"].id,
            profile_code="SP:online:checkout",
            name="São Paulo - Online Checkout",
            priority=100,
            currency="BRL",
            is_active=True,
        ),
        # PT - Kiosk - Purchase
        CapabilityProfile(
            region_id=regions["PT"].id,
            channel_id=channels["kiosk"].id,
            context_id=contexts["kiosk:purchase"].id,
            profile_code="PT:kiosk:purchase",
            name="Portugal - Kiosk Compra Presencial",
            priority=100,
            currency="EUR",
            is_active=True,
        ),
        # PT - Kiosk - Pickup
        CapabilityProfile(
            region_id=regions["PT"].id,
            channel_id=channels["kiosk"].id,
            context_id=contexts["kiosk:pickup"].id,
            profile_code="PT:kiosk:pickup",
            name="Portugal - Kiosk Retirada",
            priority=100,
            currency="EUR",
            is_active=True,
        ),
        # PT - Online - Checkout
        CapabilityProfile(
            region_id=regions["PT"].id,
            channel_id=channels["online"].id,
            context_id=contexts["online:checkout"].id,
            profile_code="PT:online:checkout",
            name="Portugal - Online Checkout",
            priority=100,
            currency="EUR",
            is_active=True,
        ),
        # ES - Kiosk - Purchase
        CapabilityProfile(
            region_id=regions["ES"].id,
            channel_id=channels["kiosk"].id,
            context_id=contexts["kiosk:purchase"].id,
            profile_code="ES:kiosk:purchase",
            name="Espanha - Kiosk Compra Presencial",
            priority=100,
            currency="EUR",
            is_active=False,
        ),
    ]
    
    new_count = 0
    for profile in profiles:
        existing = db.query(CapabilityProfile).filter(
            CapabilityProfile.profile_code == profile.profile_code
        ).first()
        if not existing:
            db.add(profile)
            new_count += 1
            log(f"Perfil adicionado: {profile.profile_code}")
    
    db.commit()
    log(f"Seed de perfis concluído: {new_count} novos perfis inseridos")


# ============================================================
# 13. CAPABILITY CATALOG - MÉTODOS POR PERFIL
# ============================================================

def seed_profile_methods(db: Session):
    """Popula métodos de pagamento por perfil"""
    
    profiles = {p.profile_code: p for p in db.query(CapabilityProfile).all()}
    methods = {m.code: m for m in db.query(PaymentMethodCatalog).all()}
    wallet_providers = {wp.code: wp for wp in db.query(WalletProviderCatalog).all()}
    
    profile_methods = [
        # SP:kiosk:purchase
        {"profile_code": "SP:kiosk:purchase", "method_code": "pix", "sort_order": 10, "is_default": True, "max_installments": 1},
        {"profile_code": "SP:kiosk:purchase", "method_code": "creditCard", "sort_order": 20, "is_default": False, "max_installments": 12},
        {"profile_code": "SP:kiosk:purchase", "method_code": "debitCard", "sort_order": 30, "is_default": False, "max_installments": 1},
        {"profile_code": "SP:kiosk:purchase", "method_code": "cash", "sort_order": 40, "is_default": False, "max_installments": 1},
        {"profile_code": "SP:kiosk:purchase", "method_code": "voucher", "sort_order": 50, "is_default": False, "max_installments": 1},
        
        # SP:kiosk:pickup
        {"profile_code": "SP:kiosk:pickup", "method_code": "pix", "sort_order": 10, "is_default": True, "max_installments": 1},
        
        # SP:online:checkout
        {"profile_code": "SP:online:checkout", "method_code": "pix", "sort_order": 10, "is_default": True, "max_installments": 1},
        {"profile_code": "SP:online:checkout", "method_code": "creditCard", "sort_order": 20, "is_default": False, "max_installments": 12},
        {"profile_code": "SP:online:checkout", "method_code": "boleto", "sort_order": 30, "is_default": False, "max_installments": 1},
        
        # PT:kiosk:purchase
        {"profile_code": "PT:kiosk:purchase", "method_code": "creditCard", "sort_order": 10, "is_default": True, "max_installments": 12},
        {"profile_code": "PT:kiosk:purchase", "method_code": "debitCard", "sort_order": 20, "is_default": False, "max_installments": 1},
        {"profile_code": "PT:kiosk:purchase", "method_code": "mbway", "sort_order": 30, "is_default": False, "max_installments": 1},
        {"profile_code": "PT:kiosk:purchase", "method_code": "cash", "sort_order": 40, "is_default": False, "max_installments": 1},
        
        # PT:online:checkout
        {"profile_code": "PT:online:checkout", "method_code": "creditCard", "sort_order": 10, "is_default": True, "max_installments": 12},
        {"profile_code": "PT:online:checkout", "method_code": "mbway", "sort_order": 20, "is_default": False, "max_installments": 1},
    ]
    
    new_count = 0
    for pm in profile_methods:
        profile = profiles.get(pm["profile_code"])
        method = methods.get(pm["method_code"])
        if not profile or not method:
            log(f"AVISO: Perfil {pm['profile_code']} ou método {pm['method_code']} não encontrado")
            continue
        
        existing = db.query(CapabilityProfileMethod).filter(
            CapabilityProfileMethod.profile_id == profile.id,
            CapabilityProfileMethod.payment_method_id == method.id
        ).first()
        
        if not existing:
            # Verifica se precisa de wallet provider
            wallet_provider_id = None
            if pm["method_code"] in ["apple_pay", "google_pay"]:
                wp_code = "applePay" if pm["method_code"] == "apple_pay" else "googlePay"
                wallet_provider = wallet_providers.get(wp_code)
                wallet_provider_id = wallet_provider.id if wallet_provider else None
            
            db.add(CapabilityProfileMethod(
                profile_id=profile.id,
                payment_method_id=method.id,
                sort_order=pm["sort_order"],
                is_default=pm["is_default"],
                is_active=True,
                max_installments=pm["max_installments"],
                wallet_provider_id=wallet_provider_id,
            ))
            new_count += 1
            log(f"Método {pm['method_code']} adicionado ao perfil {pm['profile_code']}")
    
    db.commit()
    log(f"Seed de métodos por perfil concluído: {new_count} novas associações inseridas")


# ============================================================
# 14. CAPABILITY CATALOG - INTERFACES POR MÉTODO
# ============================================================

def seed_profile_method_interfaces(db: Session):
    """Popula interfaces válidas para cada método por perfil"""
    
    profiles = {p.profile_code: p for p in db.query(CapabilityProfile).all()}
    methods = {m.code: m for m in db.query(PaymentMethodCatalog).all()}
    interfaces = {i.code: i for i in db.query(PaymentInterfaceCatalog).all()}
    
    # Get profile_method associations
    profile_methods = {}
    for pm in db.query(CapabilityProfileMethod).all():
        profile = db.query(CapabilityProfile).filter(CapabilityProfile.id == pm.profile_id).first()
        method = db.query(PaymentMethodCatalog).filter(PaymentMethodCatalog.id == pm.payment_method_id).first()
        if profile and method:
            key = f"{profile.profile_code}:{method.code}"
            profile_methods[key] = pm
    
    method_interfaces = [
        # Pix interfaces
        {"profile_code": "SP:kiosk:purchase", "method_code": "pix", "interface_code": "qr_code", "sort_order": 10, "is_default": True},
        {"profile_code": "SP:online:checkout", "method_code": "pix", "interface_code": "qr_code", "sort_order": 10, "is_default": True},
        {"profile_code": "SP:online:checkout", "method_code": "pix", "interface_code": "deep_link", "sort_order": 20, "is_default": False},
        
        # Credit Card interfaces
        {"profile_code": "SP:kiosk:purchase", "method_code": "creditCard", "interface_code": "chip", "sort_order": 10, "is_default": True},
        {"profile_code": "SP:kiosk:purchase", "method_code": "creditCard", "interface_code": "nfc", "sort_order": 20, "is_default": False},
        {"profile_code": "SP:kiosk:purchase", "method_code": "creditCard", "interface_code": "kiosk_pinpad", "sort_order": 30, "is_default": False},
        {"profile_code": "SP:online:checkout", "method_code": "creditCard", "interface_code": "web_token", "sort_order": 10, "is_default": True},
        
        # Debit Card interfaces
        {"profile_code": "SP:kiosk:purchase", "method_code": "debitCard", "interface_code": "chip", "sort_order": 10, "is_default": True},
        {"profile_code": "SP:kiosk:purchase", "method_code": "debitCard", "interface_code": "nfc", "sort_order": 20, "is_default": False},
        
        # Cash interfaces
        {"profile_code": "SP:kiosk:purchase", "method_code": "cash", "interface_code": "manual", "sort_order": 10, "is_default": True},
        {"profile_code": "SP:kiosk:purchase", "method_code": "cash", "interface_code": "barcode", "sort_order": 20, "is_default": False},
        
        # MB Way interfaces
        {"profile_code": "PT:kiosk:purchase", "method_code": "mbway", "interface_code": "qr_code", "sort_order": 10, "is_default": True},
        {"profile_code": "PT:online:checkout", "method_code": "mbway", "interface_code": "deep_link", "sort_order": 10, "is_default": True},
    ]
    
    new_count = 0
    for mi in method_interfaces:
        key = f"{mi['profile_code']}:{mi['method_code']}"
        profile_method = profile_methods.get(key)
        interface = interfaces.get(mi["interface_code"])
        
        if not profile_method or not interface:
            log(f"AVISO: ProfileMethod {key} ou interface {mi['interface_code']} não encontrado")
            continue
        
        existing = db.query(CapabilityProfileMethodInterface).filter(
            CapabilityProfileMethodInterface.profile_method_id == profile_method.id,
            CapabilityProfileMethodInterface.payment_interface_id == interface.id
        ).first()
        
        if not existing:
            db.add(CapabilityProfileMethodInterface(
                profile_method_id=profile_method.id,
                payment_interface_id=interface.id,
                sort_order=mi["sort_order"],
                is_default=mi["is_default"],
                is_active=True,
            ))
            new_count += 1
            log(f"Interface {mi['interface_code']} adicionada ao método {mi['method_code']} no perfil {mi['profile_code']}")
    
    db.commit()
    log(f"Seed de interfaces por método concluído: {new_count} novas associações inseridas")


# ============================================================
# 15. CAPABILITY CATALOG - REQUISITOS POR MÉTODO
# ============================================================

def seed_profile_method_requirements(db: Session):
    """Popula requisitos para cada método por perfil"""
    
    profiles = {p.profile_code: p for p in db.query(CapabilityProfile).all()}
    methods = {m.code: m for m in db.query(PaymentMethodCatalog).all()}
    requirements = {r.code: r for r in db.query(CapabilityRequirementCatalog).all()}
    
    # Get profile_method associations
    profile_methods = {}
    for pm in db.query(CapabilityProfileMethod).all():
        profile = db.query(CapabilityProfile).filter(CapabilityProfile.id == pm.profile_id).first()
        method = db.query(PaymentMethodCatalog).filter(PaymentMethodCatalog.id == pm.payment_method_id).first()
        if profile and method:
            key = f"{profile.profile_code}:{method.code}"
            profile_methods[key] = pm
    
    method_requirements = [
        # Pix requirements
        {"profile_code": "SP:kiosk:purchase", "method_code": "pix", "requirement_code": "amount_cents", "is_required": True, "scope": "request"},
        {"profile_code": "SP:kiosk:purchase", "method_code": "pix", "requirement_code": "qr_code_content", "is_required": True, "scope": "session"},
        {"profile_code": "SP:online:checkout", "method_code": "pix", "requirement_code": "amount_cents", "is_required": True, "scope": "request"},
        
        # Credit Card requirements
        {"profile_code": "SP:kiosk:purchase", "method_code": "creditCard", "requirement_code": "amount_cents", "is_required": True, "scope": "request"},
        {"profile_code": "SP:kiosk:purchase", "method_code": "creditCard", "requirement_code": "installments", "is_required": False, "scope": "request"},
        {"profile_code": "SP:online:checkout", "method_code": "creditCard", "requirement_code": "amount_cents", "is_required": True, "scope": "request"},
        {"profile_code": "SP:online:checkout", "method_code": "creditCard", "requirement_code": "card_token", "is_required": True, "scope": "session"},
        
        # Age verification for alcohol
        {"profile_code": "SP:kiosk:purchase", "method_code": "creditCard", "requirement_code": "age_confirmation", "is_required": False, "scope": "request"},
        
        # Cash requirements
        {"profile_code": "SP:kiosk:purchase", "method_code": "cash", "requirement_code": "amount_cents", "is_required": True, "scope": "request"},
    ]
    
    new_count = 0
    for mr in method_requirements:
        key = f"{mr['profile_code']}:{mr['method_code']}"
        profile_method = profile_methods.get(key)
        requirement = requirements.get(mr["requirement_code"])
        
        if not profile_method or not requirement:
            log(f"AVISO: ProfileMethod {key} ou requisito {mr['requirement_code']} não encontrado")
            continue
        
        existing = db.query(CapabilityProfileMethodRequirement).filter(
            CapabilityProfileMethodRequirement.profile_method_id == profile_method.id,
            CapabilityProfileMethodRequirement.requirement_id == requirement.id
        ).first()
        
        if not existing:
            db.add(CapabilityProfileMethodRequirement(
                profile_method_id=profile_method.id,
                requirement_id=requirement.id,
                is_required=mr["is_required"],
                requirement_scope=mr["scope"],
            ))
            new_count += 1
            log(f"Requisito {mr['requirement_code']} adicionado ao método {mr['method_code']} no perfil {mr['profile_code']}")
    
    db.commit()
    log(f"Seed de requisitos por método concluído: {new_count} novas associações inseridas")


# ============================================================
# 16. CAPABILITY CATALOG - AÇÕES POR PERFIL
# ============================================================

def seed_profile_actions(db: Session):
    """Popula ações por perfil"""
    
    profiles = {p.profile_code: p for p in db.query(CapabilityProfile).all()}
    
    profile_actions = [
        # Kiosk actions
        {"profile_code": "SP:kiosk:purchase", "action_code": "create_order", "label": "Iniciar pedido", "action_type": "NAVIGATION", "sort_order": 10},
        {"profile_code": "SP:kiosk:purchase", "action_code": "start_payment", "label": "Iniciar pagamento", "action_type": "PAYMENT", "sort_order": 20},
        {"profile_code": "SP:kiosk:purchase", "action_code": "identify_customer", "label": "Identificar cliente", "action_type": "IDENTIFICATION", "sort_order": 30},
        {"profile_code": "SP:kiosk:purchase", "action_code": "scan_product", "label": "Escanear produto", "action_type": "HARDWARE", "sort_order": 40},
        
        {"profile_code": "SP:kiosk:pickup", "action_code": "enter_pickup_code", "label": "Digitar código de retirada", "action_type": "IDENTIFICATION", "sort_order": 10},
        {"profile_code": "SP:kiosk:pickup", "action_code": "scan_pickup_qr", "label": "Escanear QR de retirada", "action_type": "IDENTIFICATION", "sort_order": 20},
        {"profile_code": "SP:kiosk:pickup", "action_code": "open_slot", "label": "Abrir gaveta", "action_type": "HARDWARE", "sort_order": 30},
        
        {"profile_code": "PT:kiosk:purchase", "action_code": "create_order", "label": "Iniciar pedido", "action_type": "NAVIGATION", "sort_order": 10},
        {"profile_code": "PT:kiosk:purchase", "action_code": "start_payment", "label": "Iniciar pagamento", "action_type": "PAYMENT", "sort_order": 20},
        
        {"profile_code": "PT:kiosk:pickup", "action_code": "enter_pickup_code", "label": "Digitar código de retirada", "action_type": "IDENTIFICATION", "sort_order": 10},
        {"profile_code": "PT:kiosk:pickup", "action_code": "scan_pickup_qr", "label": "Escanear QR de retirada", "action_type": "IDENTIFICATION", "sort_order": 20},
        
        # Online actions
        {"profile_code": "SP:online:checkout", "action_code": "checkout", "label": "Finalizar compra", "action_type": "PAYMENT", "sort_order": 10},
        {"profile_code": "SP:online:checkout", "action_code": "select_payment_method", "label": "Selecionar método de pagamento", "action_type": "PAYMENT", "sort_order": 20},
        {"profile_code": "SP:online:checkout", "action_code": "apply_voucher", "label": "Aplicar voucher", "action_type": "OPERATION", "sort_order": 30},
        
        {"profile_code": "PT:online:checkout", "action_code": "checkout", "label": "Finalizar compra", "action_type": "PAYMENT", "sort_order": 10},
        {"profile_code": "PT:online:checkout", "action_code": "select_payment_method", "label": "Selecionar método de pagamento", "action_type": "PAYMENT", "sort_order": 20},
    ]
    
    new_count = 0
    for pa in profile_actions:
        profile = profiles.get(pa["profile_code"])
        if not profile:
            log(f"AVISO: Perfil {pa['profile_code']} não encontrado")
            continue
        
        existing = db.query(CapabilityProfileAction).filter(
            CapabilityProfileAction.profile_id == profile.id,
            CapabilityProfileAction.action_code == pa["action_code"]
        ).first()
        
        if not existing:
            db.add(CapabilityProfileAction(
                profile_id=profile.id,
                action_code=pa["action_code"],
                label=pa["label"],
                action_type=pa["action_type"],
                sort_order=pa["sort_order"],
                is_active=True,
            ))
            new_count += 1
            log(f"Ação {pa['action_code']} adicionada ao perfil {pa['profile_code']}")
    
    db.commit()
    log(f"Seed de ações por perfil concluído: {new_count} novas ações inseridas")


# ============================================================
# 17. CAPABILITY CATALOG - CONSTRAINTS POR PERFIL
# ============================================================

def seed_profile_constraints(db: Session):
    """Popula constraints por perfil"""
    
    profiles = {p.profile_code: p for p in db.query(CapabilityProfile).all()}
    
    profile_constraints = [
        # Kiosk constraints
        {"profile_code": "SP:kiosk:purchase", "code": "prepayment_timeout_sec", "value_json": json.dumps(300)},
        {"profile_code": "SP:kiosk:purchase", "code": "max_amount_cents", "value_json": json.dumps(500000)},
        {"profile_code": "SP:kiosk:purchase", "code": "min_amount_cents", "value_json": json.dumps(100)},
        {"profile_code": "SP:kiosk:purchase", "code": "allow_guest_checkout", "value_json": json.dumps(True)},
        {"profile_code": "SP:kiosk:purchase", "code": "max_active_orders_per_user", "value_json": json.dumps(3)},
        
        {"profile_code": "SP:kiosk:pickup", "code": "pickup_window_sec", "value_json": json.dumps(86400)},  # 24 horas
        {"profile_code": "SP:kiosk:pickup", "code": "max_pickup_attempts", "value_json": json.dumps(5)},
        
        {"profile_code": "PT:kiosk:purchase", "code": "prepayment_timeout_sec", "value_json": json.dumps(300)},
        {"profile_code": "PT:kiosk:purchase", "code": "max_amount_cents", "value_json": json.dumps(500000)},
        {"profile_code": "PT:kiosk:purchase", "code": "allow_guest_checkout", "value_json": json.dumps(False)},
        
        {"profile_code": "PT:kiosk:pickup", "code": "pickup_window_sec", "value_json": json.dumps(172800)},  # 48 horas
        
        # Online constraints
        {"profile_code": "SP:online:checkout", "code": "max_amount_cents", "value_json": json.dumps(1000000)},
        {"profile_code": "SP:online:checkout", "code": "requires_identity_validation", "value_json": json.dumps(False)},
        {"profile_code": "SP:online:checkout", "code": "allow_guest_checkout", "value_json": json.dumps(True)},
        
        {"profile_code": "PT:online:checkout", "code": "max_amount_cents", "value_json": json.dumps(500000)},
        {"profile_code": "PT:online:checkout", "code": "allow_guest_checkout", "value_json": json.dumps(False)},
    ]
    
    new_count = 0
    for pc in profile_constraints:
        profile = profiles.get(pc["profile_code"])
        if not profile:
            log(f"AVISO: Perfil {pc['profile_code']} não encontrado")
            continue
        
        existing = db.query(CapabilityProfileConstraint).filter(
            CapabilityProfileConstraint.profile_id == profile.id,
            CapabilityProfileConstraint.code == pc["code"]
        ).first()
        
        if not existing:
            db.add(CapabilityProfileConstraint(
                profile_id=profile.id,
                code=pc["code"],
                value_json=pc["value_json"],
            ))
            new_count += 1
            log(f"Constraint {pc['code']} adicionada ao perfil {pc['profile_code']}")
    
    db.commit()
    log(f"Seed de constraints por perfil concluído: {new_count} novas constraints inseridas")


# ============================================================
# 18. CAPABILITY CATALOG - TARGETS POR PERFIL
# ============================================================

def seed_profile_targets(db: Session):
    """Popula targets (overrides) por perfil"""
    
    profiles = {p.profile_code: p for p in db.query(CapabilityProfile).all()}
    lockers = {l.id: l for l in db.query(Locker).all()}
    
    profile_targets = [
        # Override para locker refrigerado específico
        {
            "profile_code": "SP:kiosk:purchase",
            "target_type": "LOCKER",
            "target_key": "SP-VILAOLIMPIA-FOOD-LK-001",
            "locker_id": "SP-VILAOLIMPIA-FOOD-LK-001",
            "metadata": {"temperature_override": "REFRIGERATED"}
        },
        # Override para operador específico
        {
            "profile_code": "SP:kiosk:purchase",
            "target_type": "OPERATOR",
            "target_key": "OP-PHARMA-001",
            "locker_id": None,
            "metadata": {"special_rules": "pharmacy_only"}
        },
        # Override para tenant específico
        {
            "profile_code": "SP:online:checkout",
            "target_type": "TENANT",
            "target_key": "tenant_pharmacy_001",
            "locker_id": None,
            "metadata": {"requires_prescription": True}
        },
    ]
    
    new_count = 0
    for pt in profile_targets:
        profile = profiles.get(pt["profile_code"])
        locker = lockers.get(pt["locker_id"]) if pt["locker_id"] else None
        
        if not profile:
            log(f"AVISO: Perfil {pt['profile_code']} não encontrado")
            continue
        
        existing = db.query(CapabilityProfileTarget).filter(
            CapabilityProfileTarget.profile_id == profile.id,
            CapabilityProfileTarget.target_type == pt["target_type"],
            CapabilityProfileTarget.target_key == pt["target_key"]
        ).first()
        
        if not existing:
            db.add(CapabilityProfileTarget(
                profile_id=profile.id,
                target_type=pt["target_type"],
                target_key=pt["target_key"],
                locker_id=locker.id if locker else None,
                is_active=True,
                metadata_json=pt["metadata"],
            ))
            new_count += 1
            log(f"Target {pt['target_type']}:{pt['target_key']} adicionado ao perfil {pt['profile_code']}")
    
    db.commit()
    log(f"Seed de targets por perfil concluído: {new_count} novos targets inseridos")


# ============================================================
# 19. CAPABILITY CATALOG - SNAPSHOTS
# ============================================================

def seed_profile_snapshots(db: Session):
    """Popula snapshots de perfil (versão desnormalizada para KIOSK)"""
    
    profiles = {p.profile_code: p for p in db.query(CapabilityProfile).all()}
    
    new_count = 0
    for profile_code, profile in profiles.items():
        # Verifica se já existe um snapshot publicado
        existing = db.query(CapabilityProfileSnapshot).filter(
            CapabilityProfileSnapshot.profile_id == profile.id,
            CapabilityProfileSnapshot.status == "PUBLISHED"
        ).first()
        
        if not existing:
            # Busca ações ativas do perfil
            actions = db.query(CapabilityProfileAction).filter(
                CapabilityProfileAction.profile_id == profile.id,
                CapabilityProfileAction.is_active == True
            ).all()
            
            # Busca métodos ativos do perfil
            profile_methods = db.query(CapabilityProfileMethod).filter(
                CapabilityProfileMethod.profile_id == profile.id,
                CapabilityProfileMethod.is_active == True
            ).all()
            
            methods_data = []
            for pm in profile_methods:
                method = db.query(PaymentMethodCatalog).filter(
                    PaymentMethodCatalog.id == pm.payment_method_id
                ).first()
                if method:
                    # Busca interfaces para este método
                    interfaces = db.query(CapabilityProfileMethodInterface).filter(
                        CapabilityProfileMethodInterface.profile_method_id == pm.id,
                        CapabilityProfileMethodInterface.is_active == True
                    ).all()
                    
                    methods_data.append({
                        "code": method.code,
                        "name": method.name,
                        "family": method.family,
                        "is_default": pm.is_default,
                        "max_installments": pm.max_installments,
                        "interfaces": [{"code": pi.payment_interface.code} for pi in interfaces if pi.payment_interface],
                    })
            
            # Snapshot completo
            snapshot_json = {
                "profile_code": profile_code,
                "name": profile.name,
                "currency": profile.currency,
                "actions": [
                    {"code": a.action_code, "label": a.label, "type": a.action_type}
                    for a in actions
                ],
                "payment_methods": methods_data,
            }
            
            # Calcula hash do snapshot
            snapshot_str = json.dumps(snapshot_json, sort_keys=True)
            snapshot_hash = hashlib.sha256(snapshot_str.encode()).hexdigest()
            
            db.add(CapabilityProfileSnapshot(
                profile_id=profile.id,
                profile_code=profile_code,
                resolved_json=snapshot_json,
                snapshot_hash=snapshot_hash,
                version=1,
                status="PUBLISHED",
                published_at=datetime.now(timezone.utc),
                generated_by="seed_script",
            ))
            new_count += 1
            log(f"Snapshot criado para perfil {profile_code}")
    
    db.commit()
    log(f"Seed de snapshots concluído: {new_count} novos snapshots inseridos")


# ============================================================
# 20. FUNÇÃO PRINCIPAL
# ============================================================

def run_full_seed(db: Session):
    """Executa todo o seed na ordem correta"""
    
    log("🚀 Iniciando seed completo do banco de dados...")
    log("=" * 60)
    
    # 1. Tabelas base (ordem respeitando FKs)
    log("\n📦 1. Seed de Categorias de Produtos")
    seed_product_categories(db)
    
    log("\n🏢 2. Seed de Operadores")
    seed_operators(db)
    
    log("\n📬 3. Seed de Lockers e Configurações")
    seed_lockers(db)
    
    # 2. Capability Catalog - Tabelas base
    log("\n🌍 4. Seed de Regiões")
    seed_capability_regions(db)
    
    log("\n📡 5. Seed de Canais")
    seed_capability_channels(db)
    
    log("\n🎯 6. Seed de Contextos")
    seed_capability_contexts(db)
    
    log("\n💳 7. Seed de Métodos de Pagamento")
    seed_payment_methods(db)
    
    log("\n🖥️ 8. Seed de Interfaces de Pagamento")
    seed_payment_interfaces(db)
    
    log("\n👛 9. Seed de Wallet Providers")
    seed_wallet_providers(db)
    
    log("\n📋 10. Seed de Requisitos")
    seed_capability_requirements(db)
    
    # 3. Capability Catalog - Tabelas de relacionamento
    log("\n📁 11. Seed de Perfis")
    seed_capability_profiles(db)
    
    log("\n🔗 12. Seed de Métodos por Perfil")
    seed_profile_methods(db)
    
    log("\n🔌 13. Seed de Interfaces por Método")
    seed_profile_method_interfaces(db)
    
    log("\n⚠️ 14. Seed de Requisitos por Método")
    seed_profile_method_requirements(db)
    
    log("\n⚡ 15. Seed de Ações por Perfil")
    seed_profile_actions(db)
    
    log("\n🚧 16. Seed de Constraints por Perfil")
    seed_profile_constraints(db)
    
    log("\n🎯 17. Seed de Targets por Perfil")
    seed_profile_targets(db)
    
    log("\n📸 18. Seed de Snapshots")
    seed_profile_snapshots(db)
    
    log("\n" + "=" * 60)
    log("✅ Seed completo finalizado com sucesso!")


# ============================================================
# EXECUÇÃO DIRETA (para testes)
# ============================================================

if __name__ == "__main__":
    import sys
    import os
    
    # Adiciona o caminho do projeto ao sys.path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from app.core.db import SessionLocal
    
    db = SessionLocal()
    try:
        run_full_seed(db)
    finally:
        db.close()